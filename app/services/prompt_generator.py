from __future__ import annotations

import logging

from app.llm.groq_client import call_text

logger = logging.getLogger(__name__)

_DEFAULT_APPEARANCE = "a person"


def generate(scene_summary: str, characters: list[dict], tone: str = "", events: list[str] | None = None) -> str:
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
    events_block = "\n".join(f"- {e}" for e in events) if events else f"- {scene_summary}"

    logger.info("[prompt_generator] scene_summary: %s", scene_summary)
    logger.info("[prompt_generator] events: %s", events)
    logger.info("[prompt_generator] tone: %s", tone)
    logger.info("[prompt_generator] characters:\n%s", chars_block)

    prompt = f"""You are a visual director writing a scene description for an AI image generation model.

Scene summary (Korean):
{scene_summary}

Key events (Korean):
{events_block}

{tone_line}Characters:
{chars_block}

Task:
Pick the single most visually compelling event from the list above, then write ONE English sentence describing it.

Rules:
- Structure: Subject → Action → Object → Result.
- The action must be happening now, not about to happen.
- Both characters must be visible in the same frame — describe them together, not one acting off-screen.
- Focus on the interaction between characters — describe what one does to another.
- Do NOT describe characters independently or list them.
- Always include the visible result or reaction of the action.
- Integrate character appearances naturally into the sentence — do not list them separately.
- Do NOT include framing, style, or composition words — those will be added separately.
- No dialogue, no narration, no explanation.
- Return only the sentence."""

    return call_text(prompt, temperature=0.1)
