from __future__ import annotations

import json
import time

from groq import Groq

from app.config import get_settings


class LLMCallError(RuntimeError):
    pass


def _client() -> Groq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY must be set")
    return Groq(api_key=settings.groq_api_key)


def call_text(prompt: str, temperature: float = 0.3) -> str:
    settings = get_settings()
    res = _client().chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return (res.choices[0].message.content or "").strip()


def call(prompt: str, retries: int = 2) -> str:
    settings = get_settings()
    last_err: Exception | None = None

    for attempt in range(retries + 1):
        try:
            res = _client().chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "Return valid JSON only. No markdown."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            text = res.choices[0].message.content or ""

            # 빠른 JSON 검증(문서 스펙: JSON만 반환)
            json.loads(text)
            return text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            raise LLMCallError(str(last_err)) from last_err

