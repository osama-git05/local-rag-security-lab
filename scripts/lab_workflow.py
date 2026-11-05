"""Shared, allowlisted orchestration for the CLI and local operator console."""
import json
import os
import re
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
from dotenv import dotenv_values

from app.paths import ROOT

RESULTS = ROOT / "results"
BASE_URL = "http://127.0.0.1:8001"
SUITES = ("isolated", "chroma", "regression", "extended")
EVALUATORS = {"regression": "evaluation.run_regression", "extended": "evaluation.run_extended_regression"}
RUN_ID = re.compile(r"\d{8}T\d{12}Z-[a-f0-9]{8}")


class WorkflowBusy(Exception):
    pass


class WorkflowError(Exception):
    pass


class RunLock:
    """OS lock released even after a process crash; keep its inode/file stable."""
    def __init__(self, directory):
        self.path = Path(directory) / ".lab-console.lock"
        self.handle = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise WorkflowBusy("Another workflow is running.") from None
        self.handle = handle

    def release(self):
        if self.handle is None:
            return
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


def readiness():
    """Return safe, separate prerequisite decisions; never return configuration values."""
    checks = []

    def add(key, label, status, message):
        checks.append(dict(id=key, label=label, status=status, message=message))

    values = dotenv_values(ROOT / ".env")
    tokens = [values.get(key) for key in ("EMPLOYEE_TOKEN", "ADMIN_TOKEN")]
    valid = all(isinstance(t, str) and len(t) >= 32 for t in tokens) and tokens[0] != tokens[1]
    add("credentials", "Local credentials", "ready" if valid else "error",
        "Two distinct account tokens are configured." if valid else "Check the existing employee/admin token configuration.")
    index = ROOT / ".chroma" / "chroma.sqlite3"
    add("index", "Existing Chroma index", "ready" if index.is_file() else "error",
        "Index file exists; the Chroma suite checks its collection." if index.is_file() else "Existing Chroma index is unavailable. No rebuild was attempted.")
    try:
        manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8-sig"))
        corpus = (ROOT / "data" / "corpus").resolve()
        entries = manifest["documents"]
        corpus_ok = bool(entries) and all((corpus / item["file"]).resolve().parent == corpus and (corpus / item["file"]).is_file() for item in entries)
    except (ValueError, OSError, KeyError, TypeError):
        corpus_ok = False
    add("corpus", "Corpus and manifest", "ready" if corpus_ok else "error",
        "Manifest files are present." if corpus_ok else "Review the existing manifest and corpus paths.")

    with httpx.Client(timeout=5.0, trust_env=False) as client:
        try:
            response = client.get(BASE_URL + "/health")
            response.raise_for_status()
            api_ok = response.json().get("status") == "ok"
        except (httpx.HTTPError, ValueError, AttributeError):
            api_ok = False
        add("api", "Company assistant API", "ready" if api_ok else "error",
            "API responds on port 8001." if api_ok else "API unavailable on port 8001. Check its existing process before starting another.")
        identity_ok = api_ok and valid
        if identity_ok:
            try:
                for token, role in zip(tokens, ("employee", "admin")):
                    response = client.get(BASE_URL + "/whoami", headers={"Authorization": f"Bearer {token}"})
                    response.raise_for_status()
                    identity_ok &= response.json().get("role") == role
            except (httpx.HTTPError, ValueError, AttributeError):
                identity_ok = False
        add("identity", "Server account mappings", "ready" if identity_ok else "error",
            "Both roles match their server-verified identities." if identity_ok else "Could not verify both accounts against the running API.")
        try:
            from app.ingest import EMBEDDING_MODEL
            # auth loads validated settings before rag can be imported.
            if not valid:
                raise WorkflowError()
            from app.rag import MODEL, OLLAMA_URL
            base = OLLAMA_URL.rsplit("/api/", 1)[0]
            response = client.get(base + "/api/tags")
            response.raise_for_status()
            installed = {item["name"] for item in response.json()["models"]}
            models_ok = all(name in installed or name + ":latest" in installed for name in (MODEL, EMBEDDING_MODEL))
            add("ollama", "Ollama and models", "ready" if models_ok else "error",
                "Both configured models are installed." if models_ok else "A configured model is missing. No download was attempted.")
        except (httpx.HTTPError, ValueError, OSError, KeyError, TypeError, RuntimeError, WorkflowError):
            add("ollama", "Ollama and models", "error", "Could not verify Ollama/model configuration. No download was attempted.")
    try:
        from evaluation.run_regression import load_environment_snapshot
        snapshot = load_environment_snapshot()
        add("snapshot", "Environment snapshot", "ready", "Latest snapshot matches current source, assets and active payment dataset: " + snapshot.name)
    except (ValueError, RuntimeError, OSError, KeyError, TypeError):
        add("snapshot", "Environment snapshot", "recapture", "The live workflow will capture the current source before evaluation.")
    return checks


def public_report(report):
    """Only curated metadata crosses the operator HTTP boundary."""
    keys = ("run_id", "suite", "status", "started_at_utc", "finished_at_utc", "elapsed_ms", "exit_code",
            "environment_snapshot", "evaluation_report", "case_counts", "cases", "message", "readiness")
    result = {key: report[key] for key in keys if key in report}
    result["stages"] = [{k: s[k] for k in ("name", "status", "elapsed_ms", "returncode", "message") if k in s}
                        for s in report.get("stages", [])]
    return result


def read_report(run_id, directory=RESULTS):
    if not RUN_ID.fullmatch(run_id):
        raise FileNotFoundError()
    path = Path(directory) / f"lab-workflow-{run_id}.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") == "running":
        lock = RunLock(directory)
        try:
            lock.acquire()
        except WorkflowBusy:
            return report
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if report.get("status") == "running":
                report.update(status="interrupted", exit_code=130,
                              message="Previous process stopped without completing this run; completed evidence is retained.")
                temporary = path.with_suffix(".tmp")
                temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                temporary.replace(path)
        finally:
            lock.release()
    return report


def list_reports(directory=RESULTS):
    reports = []
    for path in sorted(Path(directory).glob("lab-workflow-*.json"), reverse=True)[:30]:
        try:
            reports.append(public_report(read_report(path.stem.removeprefix("lab-workflow-"), directory)))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return reports


def run_module(module, timeout):
    """Bound each stage and clean up only the subprocess tree we created."""
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen([sys.executable, "-u", "-m", module], cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"), **options)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    except BaseException:
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            if process.poll() is None:
                process.kill()
        process.communicate()
        raise


class Workflow:
    def __init__(self, suite, directory=RESULTS, emit=None):
        if suite not in SUITES:
            raise ValueError("Unsupported suite.")
        self.directory = Path(directory)
        self.lock = RunLock(directory)
        self.emit = emit or (lambda text: None)
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:8]
        self.path = self.directory / f"lab-workflow-{self.run_id}.json"
        self.report = dict(run_type="lab_workflow", run_id=self.run_id, suite=suite, status="running",
                           started_at_utc=datetime.now(timezone.utc).isoformat(), stages=[],
                           limitations=["Stage outcomes are not independent test-case counts.",
                                        "Snapshots hash saved files, not the running API process.",
                                        "Direct evaluation commands do not share this orchestration lock."])

    def save(self):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.report, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def acquire(self):
        self.lock.acquire()
        try:
            self.save()
        except BaseException:
            self.lock.release()
            raise

    def stage(self, name, module, timeout):
        stage = dict(name=name, module=module, status="running")
        self.report["stages"].append(stage)
        self.save()
        self.emit(name + " ...")
        timer = perf_counter()
        try:
            result = run_module(module, timeout)
            output = result.stdout + "\n" + result.stderr
            # Keep diagnostics locally, with account tokens and personal paths removed.
            for token in dotenv_values(ROOT / ".env").values():
                if isinstance(token, str) and token:
                    output = output.replace(token, "[REDACTED]")
            output = output.replace(str(ROOT), "<repository>").replace(str(Path.home()), "<user>")
            log = self.directory / f"lab-diagnostic-{self.run_id}-{len(self.report['stages'])}.log"
            log.write_text(output, encoding="utf-8")
            stage.update(returncode=result.returncode, status="pass" if result.returncode == 0 else "fail", diagnostic_log=log.name)
            summaries = re.findall(r"Passed:\s*\d+/\d+|Ran \d+ tests?", output)
            stage["message"] = "; ".join(summaries) or ("Completed." if result.returncode == 0 else "Check the local diagnostic log.")
            self.emit(stage["status"].upper() + " | " + name + " | " + stage["message"])
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            stage.update(status="error", message="Stage exceeded its time limit.")
            raise WorkflowError("Stage timed out.") from None
        except BaseException:
            stage.update(status="error", message="Stage interrupted or unavailable.")
            raise
        finally:
            stage["elapsed_ms"] = round((perf_counter() - timer) * 1000, 2)
            self.save()

    def artifact(self, output, prefix):
        matches = re.findall(r"^Saved: results/(" + re.escape(prefix) + r"-\d{8}T\d{12}Z\.json)\s*$", output, re.MULTILINE)
        if len(matches) != 1 or not (self.directory / matches[0]).is_file():
            raise WorkflowError("Could not identify the generated artifact.")
        return matches[0]

    def execute(self):
        """Caller must acquire before running or dispatching a worker."""
        timer = perf_counter()
        exit_code = 2
        try:
            suite = self.report["suite"]
            passed = True
            if suite != "chroma":
                passed, _ = self.stage("Isolated checks", "tests.run_isolated", 300)
            if passed and suite != "isolated":
                passed, _ = self.stage("Existing Chroma index", "tests.live.check_chroma_authorization", 90)
            if passed and suite in EVALUATORS:
                self.report["readiness"] = readiness()
                if any(c["status"] == "error" for c in self.report["readiness"]):
                    raise WorkflowError("A live prerequisite is unavailable. Review readiness checks.")
                passed, output = self.stage("Environment capture", "scripts.capture_environment", 90)
                if passed:
                    self.report["environment_snapshot"] = self.artifact(output, "environment")
                    self.save()
                    previous_reports = set(self.directory.glob("development-regression-*.json"))
                    passed, output = self.stage("Live development evaluation", EVALUATORS[suite], 5400)
                    # A failed or interrupted evaluator may still save a partial case report.
                    if "Saved: results/development-regression-" in output:
                        filename = self.artifact(output, "development-regression")
                    else:
                        new_reports = set(self.directory.glob("development-regression-*.json")) - previous_reports
                        filename = next(iter(new_reports)).name if len(new_reports) == 1 else None
                    if filename:
                        detail = json.loads((self.directory / filename).read_text(encoding="utf-8"))
                        if detail.get("environment_snapshot") != self.report["environment_snapshot"]:
                            raise WorkflowError("Evaluation snapshot differs from this run. Check concurrent direct commands.")
                        self.report["evaluation_report"] = filename
                        self.report["case_counts"] = detail.get("counts")
                        self.report["cases"] = [dict(case_id=c.get("case_id"), outcome=c.get("outcome"),
                            status=c.get("status"), elapsed_ms=c.get("elapsed_ms"), error_type=c.get("error_type"),
                            failed_checks=[name for name, value in c.get("checks", {}).items() if not value])
                            for c in detail.get("results", [])]
                        if detail.get("counts") is None:
                            self.report["message"] = "Evaluator stopped before final counts; linked case report is incomplete."
                        compatibility = detail.get("payment_dataset_compatibility")
                        if compatibility:
                            self.report["payment_dataset_compatibility"] = compatibility
                            if compatibility["status"] == "error":
                                self.report["message"] = compatibility["message"]
                    elif passed:
                        raise WorkflowError("Evaluator did not identify its saved report.")
            exit_code = 0 if passed else 1
            self.report["status"] = "pass" if passed else "fail"
        except KeyboardInterrupt:
            exit_code = 130
            self.report.update(status="interrupted", message="Run interrupted; completed evidence is retained.")
        except Exception as error:
            self.report.update(status="error", message=str(error) if isinstance(error, WorkflowError) else "Workflow stopped. Review local diagnostics.")
        finally:
            self.report.update(exit_code=exit_code, finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_ms=round((perf_counter() - timer) * 1000, 2))
            try:
                self.save()
            finally:
                self.lock.release()
            self.emit("Workflow " + self.report["status"].upper() + " | " + self.path.name)
            if self.report.get("case_counts") is not None:
                self.emit("Live case counts: " + json.dumps(self.report["case_counts"]))
        return exit_code


def start_background(suite, directory=RESULTS):
    workflow = Workflow(suite, directory)
    workflow.acquire()
    worker = threading.Thread(target=workflow.execute, name="lab-workflow", daemon=False)
    try:
        worker.start()
    except BaseException:
        workflow.lock.release()
        raise
    return workflow.run_id
