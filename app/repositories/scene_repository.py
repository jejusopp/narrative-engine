from __future__ import annotations

from app.db.supabase import get_supabase


class SceneRepository:
    def __init__(self):
        self.sb = get_supabase()

    def save_scene(
        self,
        novel_id: str,
        scene_index: int,
        text: str,
        summary: str,
        location: str,
        tone: str,
        status: str = "completed",
    ) -> dict:
        payload = {
            "novel_id": novel_id,
            "scene_index": scene_index,
            "text": text,
            "summary": summary,
            "location": location,
            "tone": tone,
            "status": status,
        }
        res = self.sb.table("scenes").insert(payload).execute()
        return res.data[0]

