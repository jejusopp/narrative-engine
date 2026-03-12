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
        # appearance_count 증가는 MVP에서는 단순 update로 처리 (정확한 카운트는 추후 appearances 테이블 기반으로 계산 가능)
        self.sb.table("characters").update({"appearance_count": (row.get("appearance_count") or 0) + 1}).eq("id", row["id"]).execute()
        return row

    def list_characters(self, novel_id: str) -> list[dict]:
        res = self.sb.table("characters").select("id,name,description,appearance_count").eq("novel_id", novel_id).execute()
        return res.data or []

