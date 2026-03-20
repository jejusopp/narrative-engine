from __future__ import annotations

import json
import re

from app.llm.groq_client import call


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON found in response:\n{text}")


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
- "summary" must be 1-3 short sentences, each describing one key event, joined by \n. Focus on what the narrator directly experiences or does — ignore background exposition, historical context, and flashbacks. Each sentence covers one independent event — do not chain events with conjunctions. Use exact character names — never replace with titles or roles. Carefully identify who does what — do not misattribute actions to the wrong character.
- "events" must be a list of 1–3 key actions the narrator directly experiences, each as one sentence with enough detail to visualize (who does what to whom). Use exact character names — never replace with titles or roles.
- Use known character names when possible to avoid duplicates
- In first-person narratives, the narrator ("나"/"내") should be listed as "주인공". If the narrator's real name is mentioned in the scene, include it in the description field.
- Extract ONLY human characters. Ignore animals, creatures, and objects even if they appear in the scene.
- Ignore generic background characters (man, woman, soldier, stranger)
- When a character is referred to only by a role or title (e.g. father, teacher, captain), check Known Characters and past references to find if this role matches an already-known character. If matched, use the known character's name — do NOT create a duplicate.
- If a role-based reference cannot be matched to any known character AND no real name is given in this scene, skip that character entirely.
- Characters list must include ONLY named or clearly identified characters
- Each character in the 'characters' list MUST be an object: {{"name": "...", "description": "...", "appearance": "..."}}
- "description": WHO the character is — role, title, occupation, or relationship to others only. Never include visual traits here.
- "appearance": What you would see if you took a photo of this character — gender, age group, and visible physical traits. Infer gender and age from context (names, titles, pronouns). Add up to 2 explicitly described visual traits (hair, eyes, build, clothing). Voice, sound, emotions, and personality are NOT visible in a photo — never include them. Max 3 items. Set null only if nothing at all can be seen or inferred.
- IMPORTANT: All values in the JSON MUST be written in Korean.

Expected JSON Structure (Strictly follow this structure):
{{
  "summary": "overall scene summary (Korean, 1 sentence)",
  "events": ["key event 1 (Korean)", "key event 2 (Korean)"],
  "location": "place where the scene occurs (Korean)",
  "tone": "mood or atmosphere of the scene (Korean)",
  "characters": [
    {{"name": "character name (Korean)", "description": "role, background, title, or relationship to others (Korean) — no physical traits", "appearance": "visual traits only, or null"}}
  ],
  "relationships": [
    {{"character_a": "name A", "character_b": "name B", "relationship": "relationship description (Korean)", "confidence": 0.9}}
  ]
}}
""".strip()

    raw = call(prompt)
    return _extract_json(raw)
