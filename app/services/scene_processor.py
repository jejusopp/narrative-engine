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
- "summary" must describe ONE key visual moment from the scene as if capturing a single illustration frame — who is doing what, who is facing whom, what is happening at that instant. Keep it concise (1-2 sentences).
- Use known character names when possible to avoid duplicates
- In first-person narratives, the narrator ("나"/"내") should be listed as "주인공" unless their real name is explicitly mentioned in the scene.
- If the narrator's real name is revealed in the scene, set "narrator_real_name" to that name AND use the real name in the characters list instead of "주인공".
- Ignore generic background characters (man, woman, soldier, stranger)
- When a character is referred to only by a role or title (e.g. father, teacher, captain), check Known Characters and past references to find if this role matches an already-known character. If matched, use the known character's name — do NOT create a duplicate.
- If a role-based reference cannot be matched to any known character AND no real name is given in this scene, skip that character entirely.
- Characters list must include ONLY named or clearly identified characters
- Each character in the 'characters' list MUST be an object: {{"name": "...", "description": "...", "appearance": "..."}}
- "appearance": STRICTLY physical and visible traits only — gender, hair, eyes, skin, body build. EXCLUDE anything that cannot be drawn: voice, sound, smell, emotion, action, personality. Always list gender first if determinable, followed by other physical traits. Max 3 items. If no physical traits are described at all, set to null.
- IMPORTANT: All values in the JSON (summary, location, tone, description, relationship, appearance) MUST be written in Korean (한국어).

Expected JSON Structure (Strictly follow this structure):
{{
  "summary": "한 장면의 핵심 순간 묘사 (한국어, 1-2문장)",
  "location": "장면의 장소 (한국어)",
  "tone": "장면의 분위기 (한국어)",
  "narrator_real_name": null,
  "characters": [
    {{"name": "character name", "description": "brief character description (Korean)", "appearance": "visual traits only, or null"}}
  ],
  "relationships": [
    {{"character_a": "이름_A", "character_b": "이름_B", "relationship": "관계 내용 (한국어)", "confidence": 0.9}}
  ]
}}
""".strip()

    raw = call(prompt)
    return json.loads(raw)
