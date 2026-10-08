from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, Request as _Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse as _JSONResponse
from fastapi.staticfiles import StaticFiles

from app.chat.router import router as chat_router
from app.rag.search import load_knowledge
from app.services.db_service import init_db

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

app = FastAPI(title="Latissa AI", version="1.0.0", docs_url=None, redoc_url=None)


@app.middleware("http")
async def _admin_auth(request: _Request, call_next):
    if request.url.path.startswith("/api/admin"):
        token = os.getenv("ADMIN_TOKEN", "").strip()
        if not token:
            return _JSONResponse({"detail": "Admin token ni nastavljen"}, status_code=503)
        provided = (
            request.headers.get("X-Admin-Token")
            or request.query_params.get("t")
            or request.cookies.get("admin_token")
        )
        if provided != token:
            return _JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


@app.middleware("http")
async def _set_admin_cookie(request: _Request, call_next):
    response = await call_next(request)
    t = request.query_params.get("t")
    if t and ADMIN_TOKEN and t == ADMIN_TOKEN:
        response.set_cookie(
            key="admin_token", value=t,
            httponly=True, secure=True, samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )
    return response


@app.middleware("http")
async def _widget_cache(request: _Request, call_next):
    response = await call_next(request)
    if request.url.path == "/static/widget.js":
        response.headers["Cache-Control"] = "no-cache"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://latissa.si",
        "https://www.latissa.si",
        "https://latissa.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def startup():
    init_db()
    kb_path = Path(__file__).parent / "knowledge.jsonl"
    count = load_knowledge(kb_path)
    print(f"[startup] Latissa AI ready — {count} knowledge chunks")


@app.get("/health")
def health():
    return {"status": "ok", "service": "latissa-ai", "version": "1.0"}


@app.get("/", response_class=HTMLResponse)
def home():
    widget_html = Path("static/widget.html")
    if widget_html.exists():
        return HTMLResponse(content=widget_html.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Latissa AI</h1><p>Widget se nalaga...</p>")


@app.get("/api/admin/conversations")
def admin_conversations():
    from app.services.db_service import get_conversations
    return get_conversations(limit=200)


@app.get("/api/admin/inquiries")
def admin_inquiries():
    from app.services.db_service import get_inquiries
    return get_inquiries(limit=200)


app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
