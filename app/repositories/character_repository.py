from __future__ import annotations

from app.db.supabase import get_supabase


class CharacterRepository:
    def __init__(self):
        self.sb = get_supabase()

    def upsert_character(self, novel_id: str, name: str, description: str | None = None) -> dict:
        payload = {
            "novel_id": novel_id,
            "name": name,
            "description": description,
        }
        res = self.sb.table("characters").upsert(payload, on_conflict="novel_id,name").execute()
        row = res.data[0]
        # appearance_count 증가는 MVP에서는 단순 update로 처리
        self.sb.table("characters").update({"appearance_count": (row.get("appearance_count") or 0) + 1}).eq("id", row["id"]).execute()
        return row

    def add_appearance(self, character_id: str, scene_id: str) -> dict:
        payload = {
            "character_id": character_id,
            "scene_id": scene_id,
        }
        res = self.sb.table("character_appearances").insert(payload).execute()
        return res.data[0]

    def list_characters(self, novel_id: str) -> list[dict]:
        res = self.sb.table("characters").select("id,name,description,appearance_count").eq("novel_id", novel_id).execute()
        return res.data or []

    def get_character_detail(self, character_id: str) -> dict | None:
        # 캐릭터 기본 정보 조회
        res = self.sb.table("characters").select("*").eq("id", character_id).execute()
        if not res.data:
            return None
        char = res.data[0]

        # character_appearances 를 통해 등장한 scene 목록 조회 (scene_index 순)
        appearances_res = (
            self.sb.table("character_appearances")
            .select("scene:scenes(id, scene_index, summary, location, tone)")
            .eq("character_id", character_id)
            .execute()
        )
        
        # 중복 제거 및 정렬 (Supabase select join 시 리스트로 옴)
        scenes = [a["scene"] for a in appearances_res.data if a.get("scene")]
        scenes.sort(key=lambda x: x["scene_index"])
        
        char["scenes"] = scenes
        return char

