from __future__ import annotations

from app.llm.groq_client import call_text

_DEFAULT_APPEARANCE = "a person"


def generate(scene_summary: str, characters: list[dict]) -> str:
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

    # 치환된 한국어 문장을 영어로 번역
    return call_text(
        f"Translate the following into one concise English sentence for image generation. Return only the sentence.\n\n{replaced}",
        temperature=0.1,
    )
