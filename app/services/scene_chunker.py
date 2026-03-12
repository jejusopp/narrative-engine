from __future__ import annotations

import re
from typing import Any

import tiktoken


_CHAPTER_SPLIT_RE = re.compile(r"(?i)(chapter\s+\d+|제\s*\d+\s*장|\*{3}|---)")


def _token_count(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def split_into_scenes(text: str) -> list[dict[str, Any]]:
    # Step 1. 전처리
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # Step 2. 1차 분리
    parts = [p.strip() for p in _CHAPTER_SPLIT_RE.split(cleaned) if p and p.strip()]

    # split()이 구분자도 포함할 수 있으니, 구분자 단독 조각 제거
    chunks: list[str] = []
    for p in parts:
        if _CHAPTER_SPLIT_RE.fullmatch(p):
            continue
        chunks.append(p)

    # Step 3. token 초과 시 문단 재분리
    refined: list[str] = []
    for ch in chunks:
        if _token_count(ch) <= 1200:
            refined.append(ch)
            continue
        paragraphs = [pp.strip() for pp in ch.split("\n\n") if pp.strip()]
        buf: list[str] = []
        buf_tokens = 0
        for pp in paragraphs:
            pp_tokens = _token_count(pp)
            if buf and (buf_tokens + pp_tokens) > 1200:
                refined.append("\n\n".join(buf).strip())
                buf = [pp]
                buf_tokens = pp_tokens
            else:
                buf.append(pp)
                buf_tokens += pp_tokens
        if buf:
            refined.append("\n\n".join(buf).strip())

    # Step 4. 짧은 chunk 병합
    merged: list[str] = []
    i = 0
    while i < len(refined):
        cur = refined[i]
        if _token_count(cur) < 200 and (i + 1) < len(refined):
            nxt = refined[i + 1]
            merged.append((cur + "\n\n" + nxt).strip())
            i += 2
        else:
            merged.append(cur)
            i += 1

    # Step 5. scene_index
    return [{"scene_index": idx + 1, "text": ch} for idx, ch in enumerate(merged) if ch.strip()]

