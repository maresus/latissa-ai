"""
Guard za Latissa AI — blokira kode/kupone, neodobrene odstotke in napačne URL-je.
GUARD_BLOKIRAJ=0 → samo logira (faza A)
GUARD_BLOKIRAJ=1 → blokira coupon/pct z varnim sporočilom (faza B)
URL filter je vedno aktiven (zamenja napačen URL s https://latissa.si).
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

# Veljavni latissa.si poti (točno ali kot predpona za globlje produktne strani)
_APPROVED_LATISSA_PATHS: frozenset[str] = frozenset({
    # pohištvo
    '/produkti/pohistvo/',
    '/produkti/pohistvo/postelje/',
    '/produkti/pohistvo/oblazinjeno_pohistvo/',
    '/produkti/pohistvo/mize/',
    '/produkti/pohistvo/stoli/',
    '/produkti/pohistvo/omare_in_komode/',
    '/produkti/pohistvo/kolekcije/',
    '/produkti/pohistvo/pisarnisko_pohistvo/',
    '/produkti/pohistvo/vrtno_pohistvo/',
    # kopalnički program
    '/produkti/kopalniski_program/',
    '/produkti/kopalniski_program/kopalne_kadi/',
    '/produkti/kopalniski_program/kopalniske_armature/',
    '/produkti/kopalniski_program/kopalniske_omarice/',
    '/produkti/kopalniski_program/kopalniski_dodatki/',
    '/produkti/kopalniski_program/kopalniski_radiatorji/',
    '/produkti/kopalniski_program/tus_kabine_in_stene/',
    '/produkti/kopalniski_program/tus_kadi_in_kanalete/',
    '/produkti/kopalniski_program/umivalniki/',
    '/produkti/kopalniski_program/wc_skoljke/',
    # svetila
    '/produkti/svetila/',
    '/produkti/svetila/stropna_svetila/',
    '/produkti/svetila/stenska_svetila/',
    '/produkti/svetila/viseca_svetila/',
    '/produkti/svetila/talna_in_namizna_svetila/',
    '/produkti/svetila/vgradna_svetila/',
    '/produkti/svetila/tracna_svetila/',
    '/produkti/svetila/zunanja_svetila/',
    '/produkti/svetila/dodatki_za_svetila/',
    # home decor
    '/produkti/home_decor/',
    '/produkti/home_decor/vaze/',
    '/produkti/home_decor/ogledala/',
    '/produkti/home_decor/preproge/',
    '/produkti/home_decor/umetniske_slike/',
    '/produkti/home_decor/umetne_rastline/',
    '/produkti/home_decor/tekstil_za_dom/',
    '/produkti/home_decor/stenski_paneli/',
    '/produkti/home_decor/obesalniki/',
    '/produkti/home_decor/dodatki_za_dom/',
    # otroška soba
    '/produkti/otroska_soba/',
    '/produkti/otroska_soba/otroske_in_mladinske_postelje/',
    '/produkti/otroska_soba/otroski_stoli/',
    # strani
    '/akcija/',
    '/aktualno/',
    '/inspiracija/',
    '/blagovne_znamke/',
    '/o_latissi/kontakt/',
    '/o_latissi/nasa_zgodba/',
    '/o_latissi/zakaj_izbrati_latisso/',
    '/partnerstvo/b2b/',
    '/partnerstvo/arhitekti_in_oblikovalci/',
    '/za_vas/kontaktni_obrazec/',
    '/za_vas/nacini_placila_in_dostava/',
    '/za_vas/nakup_na_obroke/',
    '/za_vas/pogosta_vprasanja/',
    '/za_vas/reklamacije_in_vracilo_blaga/',
    '/za_vas/splosni_pogoji_poslovanja/',
    '/pravilnik_zasebnosti/',
    '/piskotki/',
    '/',
})

_LATISSA_URL_RE = re.compile(
    r'https?://(?:www\.)?latissa\.si(/[^\s<>"\')\]]*)',
    re.IGNORECASE,
)


def _path_approved(raw_path: str) -> bool:
    path = raw_path if raw_path.endswith('/') else raw_path + '/'
    # točno ujemanje
    if path in _APPROVED_LATISSA_PATHS:
        return True
    # predpona (dovoli globlje produktne strani, npr. /produkti/pohistvo/postelje/xyz/)
    return any(path.startswith(p) for p in _APPROVED_LATISSA_PATHS)


def _filter_latissa_urls(reply: str, session_id: str = "") -> tuple[bool, str]:
    """Zamenja vsak napačen latissa.si URL s https://latissa.si. Vedno aktiven."""
    found_bad = False

    def _sub(m: re.Match) -> str:
        nonlocal found_bad
        path = m.group(1) or '/'
        if _path_approved(path):
            return m.group(0)
        found_bad = True
        logger.warning("[guard] bad_url session=%s url=%s", session_id, m.group(0))
        return 'https://latissa.si'

    return found_bad, _LATISSA_URL_RE.sub(_sub, reply)


def check_reply(reply: str, session_id: str = "") -> tuple[bool, str]:
    """
    Vrne (ok, reply).
    URL filter: vedno zamenja napačne URL-je (ne blokira celotnega odgovora).
    Coupon/pct: faza A (log) ali B (blokira) glede na GUARD_BLOKIRAJ.
    """
    blokiraj = os.getenv("GUARD_BLOKIRAJ", "0").strip() == "1"

    # URL filter — vedno aktiven, zamenja napačne URL-je
    bad_url, reply = _filter_latissa_urls(reply, session_id)

    violations: list[str] = []
    if bad_url:
        violations.append("bad_latissa_url")

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

    # samo coupon/pct kršitve sprožijo _SAFE_MESSAGE (URL kršitve so že popravljene)
    hard = [v for v in violations if not v.startswith("bad_latissa_url")]
    if hard and blokiraj:
        return False, _SAFE_MESSAGE
    return True, reply
