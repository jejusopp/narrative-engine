from __future__ import annotations

from app.llm.groq_client import call_text


def generate(scene_summary: str, characters: list[dict]) -> str:
    # 씬 요약 → 짧은 영어 한 줄로 번역
    scene_en = call_text(
        f"Translate the following Korean scene summary into one concise English sentence. Return only the sentence.\n\n{scene_summary}",
        temperature=0.1,
    )

    # 캐릭터 블록 조립
    character_lines = []
    for c in characters:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        raw = c.get("appearance") or ""
        if isinstance(raw, list):
            raw = ", ".join(str(x) for x in raw if x)
        appearance = raw.strip()
        if appearance:
            character_lines.append(f"{name}:\n{appearance}")
        else:
            character_lines.append(name)

    characters_block = "\n\n".join(character_lines) if character_lines else "None"

    return f"Scene:\n{scene_en}\n\nCharacters:\n{characters_block}"
