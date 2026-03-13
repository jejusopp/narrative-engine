from __future__ import annotations

from app.db.supabase import get_supabase


class NovelRepository:
    def __init__(self):
        self.sb = get_supabase()

    def create_novel(self, title: str, author: str | None = None, description: str | None = None) -> dict:
        payload = {"title": title, "author": author, "description": description, "status": "pending"}
        res = self.sb.table("novels").insert(payload).execute()
        return res.data[0]

    def update_status(self, novel_id: str, status: str) -> None:
        self.sb.table("novels").update({"status": status}).eq("id", novel_id).execute()

    def get_novel(self, novel_id: str) -> dict:
        res = self.sb.table("novels").select("*").eq("id", novel_id).limit(1).execute()
        if not res.data:
            raise KeyError("novel not found")
        return res.data[0]

    def list_novels(self) -> list[dict]:
        res = self.sb.table("novels").select("*").order("created_at", desc=True).execute()
        return res.data or []

    def delete_novel(self, novel_id: str) -> None:
        self.sb.table("novels").delete().eq("id", novel_id).execute()

