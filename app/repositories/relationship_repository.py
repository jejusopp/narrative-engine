from __future__ import annotations

from app.db.supabase import get_supabase


class RelationshipRepository:
    def __init__(self):
        self.sb = get_supabase()

    def save_relationship(
        self,
        novel_id: str,
        scene_id: str,
        char_a_id: str,
        char_b_id: str,
        relationship: str,
        confidence: float,
    ) -> dict:
        payload = {
            "novel_id": novel_id,
            "scene_id": scene_id,
            "character_a": char_a_id,
            "character_b": char_b_id,
            "relationship": relationship,
            "confidence": confidence,
        }
        res = self.sb.table("relationships").insert(payload).execute()
        return res.data[0]

