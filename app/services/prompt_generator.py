from __future__ import annotations

from app.llm.groq_client import call_text


def generate(scene_summary: str, characters: list[dict]) -> str:
    character_names = [c.get("name") for c in characters if c.get("name")]
    prompt = f"""
You are a professional AI image prompt engineer.

Create a high quality prompt for an AI image generation model.

Scene Summary:
{scene_summary}

Characters:
{", ".join(character_names)}

Style requirements:
fantasy illustration
cinematic lighting
dramatic composition
high detail
epic atmosphere

Return a single prompt sentence only. No explanation.
""".strip()

    return call_text(prompt, temperature=0.3)

