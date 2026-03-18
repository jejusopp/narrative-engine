from __future__ import annotations

import json

from app.llm.groq_client import call


def _format_retrieved_context(retrieved_context: list[dict] | None) -> str:
    if not retrieved_context:
        return ""
    lines: list[str] = []
    for item in retrieved_context:
        content = (item.get("content") or "").strip()
        sim = item.get("similarity")
        if content:
            if sim is None:
                lines.append(content)
            else:
                lines.append(f"[similarity={sim:.3f}]\n{content}")
    return "\n\n---\n\n".join(lines)


def process(
    scene_text: str,
    previous_summary: str | None,
    known_characters: list[dict],
    retrieved_context: list[dict] | None = None,
) -> dict:
    prompt = f"""
You are an expert novel scene analyzer.

Analyze the following scene and extract all information in one response.
The summary MUST reflect ONLY what happens in the Scene Text. Do NOT summarize past references.

Scene Text:
{scene_text}

---

Known Characters (use these names if the same character appears):
{json.dumps(known_characters, ensure_ascii=False)}

Past scene references (for name/relationship consistency ONLY — do NOT summarize these):
{_format_retrieved_context(retrieved_context)}

---

Rules:
- Return valid JSON only, no markdown
- summary, location, tone MUST be derived from the Scene Text above, not from past references
- "summary" must capture ONE visual moment suitable for a single illustration. For each action, clearly specify: WHO does WHAT, to WHOM, and HOW. If an object is involved, specify who owns or uses it. Describe posture and reaction between characters. Write as a plain present-tense statement. Do NOT use meta words that describe the scene as a scene. Keep it to 1-2 sentences.
- Use known character names when possible to avoid duplicates
- In first-person narratives, the narrator ("나"/"내") should be listed as "주인공" unless their real name is explicitly mentioned in the scene.
- If the narrator's real name is revealed in the scene, set "narrator_real_name" to that name AND use the real name in the characters list instead of "주인공".
- Ignore generic background characters (man, woman, soldier, stranger)
- When a character is referred to only by a role or title (e.g. father, teacher, captain), check Known Characters and past references to find if this role matches an already-known character. If matched, use the known character's name — do NOT create a duplicate.
- If a role-based reference cannot be matched to any known character AND no real name is given in this scene, skip that character entirely.
- Characters list must include ONLY named or clearly identified characters
- Each character in the 'characters' list MUST be an object: {{"name": "...", "description": "...", "appearance": "..."}}
- "appearance": STRICTLY physical and visible traits only. Always include gender and estimated age group (child / teenager / young adult / middle-aged / elderly) first — infer from context if not explicitly stated. Then add up to 2 more visual traits (hair, eyes, build, etc.). EXCLUDE anything that cannot be drawn: voice, sound, smell, emotion, action, personality. Max 3 items total.
- IMPORTANT: All values in the JSON MUST be written in Korean.

Expected JSON Structure (Strictly follow this structure):
{{
  "summary": "one key visual moment (Korean, 1-2 sentences)",
  "location": "place where the scene occurs (Korean)",
  "tone": "mood or atmosphere of the scene (Korean)",
  "narrator_real_name": null,
  "characters": [
    {{"name": "character name (Korean)", "description": "brief character description (Korean)", "appearance": "visual traits only, or null"}}
  ],
  "relationships": [
    {{"character_a": "name A", "character_b": "name B", "relationship": "relationship description (Korean)", "confidence": 0.9}}
  ]
}}
""".strip()

    raw = call(prompt)
    return json.loads(raw)
