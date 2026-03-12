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

Analyze the given scene and extract all information in one response.

Previous Scene Summary:
{previous_summary or "None"}

Known Characters (use these names if the same character appears):
{json.dumps(known_characters, ensure_ascii=False)}

Relevant past scenes from this novel (use for consistency):
{_format_retrieved_context(retrieved_context)}

Rules:
- Return valid JSON only, no markdown
- Use known character names when possible to avoid duplicates
- In first-person narratives, identify the real name of "I" (나/내) if mentioned and use it as the character name.
- Ignore generic background characters (man, woman, soldier, stranger)
- Characters list must include ONLY named or clearly identified characters
- Each character in the 'characters' list MUST be an object: {{"name": "...", "description": "..."}}

Expected JSON Structure (Strictly follow this structure):
{{
  "summary": "Short scene summary",
  "location": "Where this scene happens",
  "tone": "Emotional tone",
  "characters": [
    {{"name": "CHARACTER_NAME", "description": "CHARACTER_DESCRIPTION"}}
  ],
  "relationships": [
    {{"character_a": "NAME_A", "character_b": "NAME_B", "relationship": "RELATIONSHIP_TYPE", "confidence": 0.9}}
  ]
}}

Scene Text:
{scene_text}
""".strip()

    raw = call(prompt)
    return json.loads(raw)

