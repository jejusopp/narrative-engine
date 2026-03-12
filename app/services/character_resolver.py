from __future__ import annotations

import re


_TITLE_RE = re.compile(r"^(mr|mrs|ms|dr|professor|lord|captain)\.?\s+", re.IGNORECASE)
_IGNORE = {"man", "woman", "boy", "girl", "soldier", "stranger", "person"}


def normalize_name(name: str) -> str:
    n = name.strip()
    n = _TITLE_RE.sub("", n)
    return n.strip().lower()


def resolve(extracted: dict | str, known_characters: list[dict]) -> dict:
    if isinstance(extracted, str):
        extracted = {"name": extracted, "description": ""}

    raw = (extracted.get("name") or "").strip()
    if not raw:
        return {**extracted, "is_new": False}

    norm = normalize_name(raw)
    if norm in _IGNORE or len(norm) < 2:
        return {**extracted, "ignore": True, "is_new": False}

    for kc in known_characters:
        if normalize_name(kc.get("name", "")) == norm:
            return {"name": kc.get("name"), "description": extracted.get("description", ""), "is_new": False}

    if len(norm) >= 3:
        for kc in known_characters:
            if norm in normalize_name(kc.get("name", "")):
                return {"name": kc.get("name"), "description": extracted.get("description", ""), "is_new": False}

    return {"name": raw, "description": extracted.get("description", ""), "is_new": True}


def resolve_all(extracted_characters: list[dict | str], novel_id: str, known_characters: list[dict]) -> list[dict]:
    resolved: list[dict] = []
    for ch in extracted_characters or []:
        r = resolve(ch, known_characters)
        if r.get("ignore"):
            continue
        resolved.append(r)
    return resolved

