"""
Guard za Latissa AI — blokira kode/kupone in neodobrene odstotke.
GUARD_BLOKIRAJ=0 → samo logira (faza A)
GUARD_BLOKIRAJ=1 → blokira in vrne varno sporočilo (faza B)
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

_SAFE_MESSAGE = (
    "Tega ne morem potrditi. Za natančne informacije obiščite latissa.si "
    "ali pišite na info@latissa.si."
)

# Kupon/koda: alfanumerična beseda 4+ znakov z vsaj eno VELIKO + vsaj eno cifro
_COUPON_RE = re.compile(r'\b(?=[A-Z0-9]{4,})(?=[^a-z]*[A-Z])(?=[^a-z]*[0-9])[A-Z0-9]{4,}\b')

# Odstotek v odgovoru bota
_PCT_RE = re.compile(r'(\d+(?:[.,]\d+)?)\s*%')

# Odobreni odstotki (kot float, zaokroženi na 2 decimali)
_APPROVED_PCTS = {4.0, 8.25, 6.95}


def check_reply(reply: str, session_id: str = "") -> tuple[bool, str]:
    """
    Vrne (ok, reply). Če ok=False, je reply varno nadomestno sporočilo.
    Faza A (GUARD_BLOKIRAJ=0): log, vrni original.
    Faza B (GUARD_BLOKIRAJ=1): log, vrni _SAFE_MESSAGE.
    """
    blokiraj = os.getenv("GUARD_BLOKIRAJ", "0").strip() == "1"
    violations: list[str] = []

    # Kupon/koda
    for m in _COUPON_RE.finditer(reply):
        violations.append(f"coupon_code:{m.group()}")

    # Neodobreni odstotki
    for m in _PCT_RE.finditer(reply):
        raw = m.group(1).replace(",", ".")
        try:
            val = round(float(raw), 2)
        except ValueError:
            continue
        if val not in _APPROVED_PCTS:
            violations.append(f"pct_not_approved:{val}%")

    if not violations:
        return True, reply

    logger.warning(
        "[guard] session=%s violations=%s reply_preview=%s",
        session_id, violations, reply[:120],
    )

    if blokiraj:
        return False, _SAFE_MESSAGE
    return True, reply
