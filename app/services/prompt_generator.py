from __future__ import annotations

from app.llm.groq_client import call_text

_DEFAULT_APPEARANCE = "a person"


def generate(scene_summary: str, characters: list[dict]) -> str:
    char_map = {}
    for c in characters:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        raw = c.get("appearance")
        if isinstance(raw, list):
            raw = ", ".join(str(x) for x in raw if x)
        appearance = (raw or "").strip()
        char_map[name] = appearance if appearance else _DEFAULT_APPEARANCE

    char_map_lines = "\n".join(f'- "{k}" → "{v}"' for k, v in char_map.items())

    prompt = f"""Translate the following Korean scene summary into one concise English sentence for image generation.
Replace each character name with their appearance description using the mapping below.
Return only the final English sentence.

Character mapping:
{char_map_lines if char_map_lines else "None"}

Scene summary (Korean):
{scene_summary}"""

    return call_text(prompt, temperature=0.1)
