from __future__ import annotations

import json
import logging
import re
import time

from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMCallError(RuntimeError):
    pass


def _client() -> Groq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY must be set")
    return Groq(api_key=settings.groq_api_key)


def call_text(prompt: str, temperature: float = 0.3) -> str:
    settings = get_settings()
    messages = [{"role": "user", "content": prompt}]
#     logger.info(
#         "[LLM call_text] model=%s temperature=%s\n--- PROMPT ---\n%s\n--------------",
#         settings.llm_model, temperature, prompt,
#     )
    res = _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
    )
    result = (res.choices[0].message.content or "").strip()
#     logger.info("[LLM call_text] --- RESPONSE ---\n%s\n--------------", result)
    return result


def call(prompt: str, retries: int = 2) -> str:
    settings = get_settings()
    last_err: Exception | None = None

    messages = [
        {"role": "system", "content": "Return valid JSON only. No markdown."},
        {"role": "user", "content": prompt},
    ]
#     logger.info(
#         "[LLM call] model=%s temperature=0.2\n--- PROMPT ---\n%s\n--------------",
#         settings.llm_model, prompt,
#     )

    for attempt in range(retries + 1):
        try:
            res = _client().chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.2,
            )
            text = res.choices[0].message.content or ""
#             logger.info("[LLM call] attempt=%d --- RESPONSE ---\n%s\n--------------", attempt, text)

            # 마크다운 코드블록 제거 후 JSON 추출
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError(f"No JSON found in response: {text[:200]}")
            json.loads(match.group())
            return match.group()
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            raise LLMCallError(str(last_err)) from last_err

