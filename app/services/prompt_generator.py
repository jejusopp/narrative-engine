from __future__ import annotations

from app.llm.groq_client import call_text


def generate(scene_summary: str, characters: list[dict]) -> str:
    character_names = [c.get("name") for c in characters if c.get("name")]
    prompt = f"""
You are a professional AI image prompt engineer.

Create a high quality prompt for an AI image generation model based on the given scene details.
The inputs are in Korean, but your output (the prompt) MUST be in English.

Scene Summary (Korean):
{scene_summary}

Characters (Korean):
{", ".join(character_names)}

Style requirements:
- fantasy illustration, cinematic lighting, dramatic composition, high detail, epic atmosphere
- masterpiece, beautiful scenery, Studio Ghibli art style

Output Rules:
- Return ONLY the English prompt sentence. 
- No Korean in the output.
- No explanation.
""".strip()

    return call_text(prompt, temperature=0.3)

