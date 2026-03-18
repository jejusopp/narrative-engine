from __future__ import annotations

from app.llm.groq_client import call_text

_DEFAULT_APPEARANCE = "a person"


def generate(scene_summary: str, characters: list[dict], tone: str = "") -> str:
    # 캐릭터 이름 → 외모 묘사로 치환
    replaced = scene_summary
    for c in characters:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        raw = c.get("appearance")
        if isinstance(raw, list):
            raw = ", ".join(str(x) for x in raw if x)
        appearance = (raw or "").strip() or _DEFAULT_APPEARANCE
        replaced = replaced.replace(name, f"({appearance})")

    tone_line = f"Mood: {tone}\n" if tone else ""

    prompt = f"""Translate the following Korean scene into one concise English sentence for image generation.
Rules:
- Describe the overall situation, not individual characters in isolation.
- Write as a wide-shot scene illustration (full-body characters, not close-up portraits).
- Include background/setting ONLY if the scene clearly implies a specific location. If not, omit background entirely.
- Return only the final sentence.

{tone_line}Scene:
{replaced}"""

    return call_text(prompt, temperature=0.1)
