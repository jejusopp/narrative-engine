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

    def list_scenes_by_novel(self, novel_id: str) -> list[dict]:
        # 씬 정보와 해당 씬의 가장 최신 이미지 URL을 함께 조회
        res = self.sb.table("scenes") \
            .select("id, novel_id, scene_index, summary, location, tone, status, images(image_url)") \
            .eq("novel_id", novel_id) \
            .order("scene_index") \
            .execute()
        
        scenes = []
        for s in (res.data or []):
            # images는 리스트로 반환되므로 가장 최근 것 하나만 선택
            image_url = None
            if s.get("images") and len(s["images"]) > 0:
                # images 테이블에 order를 넣기 어려우므로 일단 첫 번째 요소 사용
                image_url = s["images"][0]["image_url"]
            
            scene_data = {
                "id": s["id"],
                "novel_id": s["novel_id"],
                "scene_index": s["scene_index"],
                "summary": s["summary"],
                "location": s["location"],
                "tone": s["tone"],
                "image_status": s["status"],
                "image_url": image_url
            }
            scenes.append(scene_data)
        return scenes

    def get_scene_by_id(self, scene_id: str) -> dict | None:
        res = self.sb.table("scenes").select("*, images(image_url)").eq("id", scene_id).execute()
        if not res.data:
            return None
        
        scene = res.data[0]
        image_url = None
        if scene.get("images") and len(scene["images"]) > 0:
            image_url = scene["images"][0]["image_url"]
        
        scene["image_status"] = scene["status"]
        scene["image_url"] = image_url
        return scene

