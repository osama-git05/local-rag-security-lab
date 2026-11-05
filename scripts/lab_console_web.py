"""Separate loopback operator UI; no arbitrary shell commands or file endpoints."""
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.auth import Principal, get_principal
from app.paths import ROOT
from scripts.lab_workflow import WorkflowBusy, list_reports, public_report, read_report, readiness, start_background

ORIGIN = "http://127.0.0.1:8010"
STATIC = ROOT / "scripts" / "console_static"
app = FastAPI(title="ExampleCo Lab Console", docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def browser_boundary(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if origin not in (None, ORIGIN) or request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-origin console access denied."}, status_code=403)
        if request.method == "POST" and (origin != ORIGIN or request.headers.get("x-lab-console") != "1" or request.headers.get("content-type", "").split(";")[0] != "application/json"):
            return JSONResponse({"detail": "Same-origin JSON action required."}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    return response


app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"])


def operator(principal: Principal = Depends(get_principal)):
    if principal.role != "admin":
        raise HTTPException(403, "Administrator account required for operator tools.")
    return principal


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suite: Literal["isolated", "chroma", "regression", "extended"]


@app.get("/")
def page():
    return FileResponse(STATIC / "index.html")


@app.get("/assets/console.css")
def css():
    return FileResponse(STATIC / "console.css")


@app.get("/assets/console.js")
def js():
    return FileResponse(STATIC / "console.js", media_type="text/javascript")


@app.get("/api/session")
def session(principal=Depends(operator)):
    return {"user_id": principal.user_id, "role": principal.role}


@app.get("/api/readiness", dependencies=[Depends(operator)])
def prerequisites():
    return {"checks": readiness()}


@app.get("/api/runs", dependencies=[Depends(operator)])
def runs():
    return {"runs": list_reports()}


@app.post("/api/runs", dependencies=[Depends(operator)], status_code=202)
def start(body: RunRequest):
    try:
        return {"run_id": start_background(body.suite)}
    except WorkflowBusy:
        raise HTTPException(409, "Another workflow is running. Wait for it to finish.") from None


@app.get("/api/runs/{run_id}", dependencies=[Depends(operator)])
def run(run_id: str):
    try:
        return public_report(read_report(run_id))
    except (FileNotFoundError, ValueError, OSError):
        raise HTTPException(404, "Workflow report not found.") from None


@app.get("/api/runs/{run_id}/download", dependencies=[Depends(operator)])
def download(run_id: str):
    report = run(run_id)
    return JSONResponse(report, headers={"Content-Disposition": f'attachment; filename="lab-summary-{run_id}.json"'})
