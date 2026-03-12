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

    def list_character_relationships(self, character_id: str) -> list[dict]:
        # 특정 캐릭터가 연관된 모든 관계 조회
        # character_a 가 해당 캐릭터인 경우
        res_a = (
            self.sb.table("relationships")
            .select("relationship, confidence, scene_id, target:characters!character_b(id, name)")
            .eq("character_a", character_id)
            .execute()
        )
        # character_b 가 해당 캐릭터인 경우
        res_b = (
            self.sb.table("relationships")
            .select("relationship, confidence, scene_id, target:characters!character_a(id, name)")
            .eq("character_b", character_id)
            .execute()
        )
        
        results = []
        for r in (res_a.data or []):
            results.append({
                "relationship": r["relationship"],
                "confidence": r["confidence"],
                "scene_id": r["scene_id"],
                "other_character": r["target"]
            })
        for r in (res_b.data or []):
            results.append({
                "relationship": r["relationship"],
                "confidence": r["confidence"],
                "scene_id": r["scene_id"],
                "other_character": r["target"]
            })
            
        return results

