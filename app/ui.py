"""Local company assistant interface; document access stays in the API."""
from hashlib import sha256

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from app.paths import ROOT

router = APIRouter(include_in_schema=False)
STATIC = ROOT / "app" / "static"


@router.get("/")
def assistant_page():
    content = (STATIC / "index.html").read_text(encoding="utf-8")
    for filename in ("assistant.css", "assistant.js"):
        version = sha256((STATIC / filename).read_bytes()).hexdigest()[:16]
        url = f"/assets/{filename}"
        content = content.replace(f'"{url}"', f'"{url}?v={version}"')
    return HTMLResponse(content, headers={"Cache-Control": "no-store"})


@router.get("/assets/assistant.css")
def assistant_styles():
    return FileResponse(STATIC / "assistant.css", headers={"Cache-Control": "no-store"})


@router.get("/assets/assistant.js")
def assistant_script():
    return FileResponse(STATIC / "assistant.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})
