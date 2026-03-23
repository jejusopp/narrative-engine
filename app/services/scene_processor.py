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
- "summary": 1-4 concise sentences joined by \n. Keep total length under 320 Korean characters. Capture only the most important outcome-level facts from Scene Text; no flashback/background summary.
- Do NOT copy long narrative wording or quotes from Scene Text. Use compressed paraphrase.
- "events": 1-6 sentences about direct narrator-experienced actions (who does what to whom).
- Character dedupe rule: cross-check BOTH Known Characters and Past scene references (retrieved_context). If matched (including role/title mentions), reuse existing name; if unmatched but directly involved in key action/dialogue, add as NEW; skip incidental background mentions.
- In first-person narratives, narrator ("나"/"내") must be "주인공". If real name appears in this scene, include it in description.
- Extract only human, named/clearly identified characters (ignore animals/objects and generic background roles like man/woman/soldier/stranger).
- Each character in the 'characters' list MUST be an object: {{"name": "...", "description": "...", "appearance": "..."}}
- "description": role/title/occupation/relationship only (no visual traits).
- "appearance": visual traits only (gender/age + up to 2 visible traits); no voice/emotion/personality; null if unknown.
- IMPORTANT: All values in the JSON MUST be written in Korean.

Expected JSON Structure (Strictly follow this structure):
{{
  "summary": "overall scene summary (Korean, 1-4 concise sentences separated by \\n, under 320 chars total)",
  "events": ["key event 1 (Korean)", "key event 2 (Korean)", ...],
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
