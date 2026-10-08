from __future__ import annotations

import os
from pathlib import Path
from openai import OpenAI

from app.rag.search import get_context
from app.guard import check_reply as _guard_check


_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.txt"
_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()


def _load_system_prompt() -> str:
    if _SYSTEM_PROMPT_PATH.exists():
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "Si pomočnik spletne prodajalne Latissa home&decor."


def chat(
    message: str,
    history: list[dict[str, str]] | None = None,
    client: OpenAI | None = None,
    model: str | None = None,
) -> dict[str, str]:
    if model is None:
        model = _DEFAULT_MODEL

    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    rag_context = get_context(message, top_k=3)
    system_prompt = _load_system_prompt()

    if rag_context:
        system_prompt += f"\n\n## Dodatni kontekst iz baze znanja:\n{rag_context}"

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for msg in history[-20:]:
            messages.append(msg)

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=450,
    )

    reply = (response.choices[0].message.content or "").strip()

    if not reply:
        reply = "Oprostite, nisem razumel vprašanja. Pokličite nas: 070 733 390"

    _, reply = _guard_check(reply)
    return {"reply": reply}
