from fastapi import Request
import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en","hi","fr","zh"} 
DEFAULT_LANGUAGE = "en"

def _parse_accept_language(header: str) -> str | None:
    if not header:
        return None
    candidates = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q.strip())
            except ValueError:
                quality = 0.0
        else:
            lang = part
            quality = 1.0
        candidates.append((lang.strip().lower(), quality))
    candidates.sort(key=lambda x: x[1], reverse=True)
    for lang, _ in candidates:
        if lang in {l.lower() for l in SUPPORTED_LANGUAGES}:
            return lang
        base = lang.split("-")[0]
        if base in {l.lower() for l in SUPPORTED_LANGUAGES}:
            return base
    return None

def resolve_language(request: Request,profile_language: str | None = None,) -> str:
    accept_lang_header = request.headers.get("Accept-Language", "")
    header_lang = _parse_accept_language(accept_lang_header)
    if header_lang:
        return header_lang
    if profile_language and profile_language.lower() in {l.lower() for l in SUPPORTED_LANGUAGES}:
        return profile_language.lower()
    return DEFAULT_LANGUAGE