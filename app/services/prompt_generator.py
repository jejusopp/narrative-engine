from __future__ import annotations

from app.llm.groq_client import call_text

_DEFAULT_APPEARANCE = "a person"


def generate(scene_summary: str, characters: list[dict], tone: str = "") -> str:
    # 캐릭터 블록 구성 (이름: 외모)
    char_lines = []
    for c in characters:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        raw = c.get("appearance")
        if isinstance(raw, list):
            raw = ", ".join(str(x) for x in raw if x)
        appearance = (raw or "").strip() or _DEFAULT_APPEARANCE
        char_lines.append(f"{name}: {appearance}")

    chars_block = "\n".join(char_lines) if char_lines else "None"
    tone_line = f"Mood: {tone}\n" if tone else ""

    prompt = f"""You are a visual director writing a scene description for an AI image generation model.

Scene (Korean):
{scene_summary}

{tone_line}Characters:
{chars_block}

Task:
Write ONE English sentence describing the key action of this scene.

Rules:
- Structure: Subject → Action → Object → Result.
- The action must be happening now, not about to happen.
- Clearly identify who does what to whom.
- Integrate character appearances naturally into the sentence — do not list them separately.
- Do NOT include framing, style, or composition words — those will be added separately.
- No dialogue, no narration, no explanation.
- Return only the sentence."""

    return call_text(prompt, temperature=0.1)
