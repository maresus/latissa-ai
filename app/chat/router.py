from __future__ import annotations

import json
import os
import uuid
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from openai import OpenAI

from app.chat.llm_chat import chat
from app.services.db_service import log_conversation, save_inquiry


router = APIRouter(prefix="/chat", tags=["chat"])

_sessions: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


def _get_session(session_id: str | None) -> tuple[str, dict]:
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id]
    sid = session_id or str(uuid.uuid4())
    _sessions[sid] = {"history": [], "auto_saved": False}
    return sid, _sessions[sid]


@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    session_id, session = _get_session(payload.session_id)
    message = payload.message.strip()

    result = chat(message=message, history=session["history"])
    reply = result["reply"]

    session["history"].append({"role": "user", "content": message})
    session["history"].append({"role": "assistant", "content": reply})
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]

    background_tasks.add_task(_try_auto_save_inquiry, session_id, session)

    log_conversation(session_id=session_id, user_message=message, bot_response=reply)

    return ChatResponse(reply=reply, session_id=session_id)


def _try_auto_save_inquiry(session_id: str, session: dict):
    if session.get("auto_saved"):
        return
    history = session.get("history", [])
    if len(history) < 4:
        return

    conversation_text = ""
    for msg in history[-16:]:
        role = "Obiskovalec" if msg["role"] == "user" else "Bot"
        conversation_text += f"{role}: {msg['content']}\n"

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    extraction_prompt = """Iz spodnjega pogovora izvleci kontaktne podatke in namen povpraševanja.
Vrni SAMO JSON brez razlage. Če podatki manjkajo, daj null.
Zahtevano: ime in vsaj en kontakt (email ali telefon).
Če manjka ime ALI kontakt → vrni: {"complete": false}

Format:
{
  "complete": true,
  "name": "...",
  "email": "..." ali null,
  "phone": "..." ali null,
  "message": "kratki opis namena (max 100 znakov)"
}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": conversation_text},
            ],
            max_tokens=200,
        )
        raw = (resp.choices[0].message.content or "").strip().strip("```json").strip("```").strip()
        data = json.loads(raw)
    except Exception:
        return

    if not data.get("complete"):
        return

    inquiry_id = save_inquiry(
        session_id=session_id,
        name=data.get("name", ""),
        email=data.get("email") or "",
        phone=data.get("phone") or "",
        message=data.get("message") or "Povpraševanje iz klepeta.",
    )
    if inquiry_id:
        session["auto_saved"] = True
        log_conversation(
            session_id=session_id,
            user_message="[AUTO] Sistem je zaznal in shranil povpraševanje.",
            bot_response=f"Povpraševanje #{inquiry_id} shranjeno.",
            intent="auto_extracted_inquiry",
        )
