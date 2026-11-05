"""Run existing checks, or serve the administrator's local test console."""
import argparse
from contextlib import contextmanager, nullcontext
import socket
import threading
import time

from scripts.lab_workflow import SUITES, Workflow, WorkflowBusy


@contextmanager
def application_server():
    """Start a companion API only when port 8001 is unoccupied; stop only ours."""
    try:
        connection = socket.create_connection(("127.0.0.1", 8001), timeout=1)
    except ConnectionRefusedError:
        connection = None
    if connection is not None:
        connection.close()
        yield
        return
    import uvicorn
    server = uvicorn.Server(uvicorn.Config("app.main:app", host="127.0.0.1", port=8001, log_level="warning"))
    worker = threading.Thread(target=server.run, name="companion-api", daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 20
        while not server.started:
            if not worker.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError("Could not start the companion API. Check port 8001.")
            time.sleep(.1)
        print("Started companion API on http://127.0.0.1:8001/", flush=True)
        yield
    finally:
        server.should_exit = True
        worker.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--serve", action="store_true", help="Open the local administrator console on port 8010.")
    mode.add_argument("--suite", choices=SUITES, default="extended")
    args = parser.parse_args()
    try:
        if args.serve:
            import uvicorn
            print("Test console: http://127.0.0.1:8010/ (existing administrator token required)", flush=True)
            with application_server():
                uvicorn.run("scripts.lab_console_web:app", host="127.0.0.1", port=8010, log_level="warning")
            return 0
        workflow = Workflow(args.suite, emit=print)
        workflow.acquire()
        try:
            with application_server() if args.suite in ("regression", "extended") else nullcontext():
                return workflow.execute()
        finally:
            if workflow.report["status"] == "running":
                workflow.report.update(status="error", exit_code=2, message="Companion API startup failed; no workflow was executed.")
                workflow.save()
            workflow.lock.release()
    except WorkflowBusy:
        print("Another test workflow is running. Wait for it to finish.")
        return 2
    except (OSError, RuntimeError):
        print("Local service startup failed. Check the existing listeners and local account configuration.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
