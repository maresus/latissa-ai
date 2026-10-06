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

app = FastAPI(title="Latissa AI", version="1.0.0")


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://latissa.si",
        "https://www.latissa.si",
        "https://latissa-ai-production.up.railway.app",
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
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Latissa AI</title>
<style>body{font-family:system-ui;max-width:600px;margin:50px auto;padding:20px;background:#f6ece4;}
h1{color:#3a322e;}#chat{border:1px solid #d2b9a8;height:400px;overflow-y:auto;padding:10px;margin-bottom:10px;background:#fff;border-radius:8px;}
.user{color:#3a322e;margin:5px 0;font-weight:600;}.bot{color:#5a4a3a;margin:5px 0;white-space:pre-wrap;}
#input{width:80%;padding:10px;border:1px solid #b9a89c;border-radius:6px;}
button{padding:10px 20px;background:#3a322e;color:#fff;border:none;border-radius:6px;cursor:pointer;}
</style></head><body>
<h1>Latissa AI</h1>
<div id="chat"></div>
<input type="text" id="input" placeholder="Vprašajte karkoli..." onkeypress="if(event.key==='Enter')send()">
<button onclick="send()">Pošlji</button>
<script>
let sid=null;const chat=document.getElementById('chat'),inp=document.getElementById('input');
async function send(){const msg=inp.value.trim();if(!msg)return;
chat.innerHTML+=`<div class="user">Vi: ${msg}</div>`;inp.value='';
const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,session_id:sid})});
const d=await r.json();sid=d.session_id;
chat.innerHTML+=`<div class="bot">Bot: ${d.reply}</div>`;chat.scrollTop=chat.scrollHeight;}
</script></body></html>"""


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
