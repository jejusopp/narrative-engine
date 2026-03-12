from __future__ import annotations

from app.db.supabase import get_supabase


class ImageRepository:
    def __init__(self):
        self.sb = get_supabase()

    def create_image_job(self, scene_id: str, prompt: str) -> dict:
        payload = {"scene_id": scene_id, "prompt": prompt, "status": "pending"}
        res = self.sb.table("image_jobs").insert(payload).execute()
        return res.data[0]

    def fetch_pending_job(self) -> dict | None:
        """가장 오래된 pending 작업을 하나 가져와 processing으로 업데이트"""
        # 1. pending 상태인 작업을 하나 조회
        res = self.sb.table("image_jobs") \
            .select("*") \
            .eq("status", "pending") \
            .order("created_at", desc=False) \
            .limit(1) \
            .execute()
        
        if not res.data:
            return None
        
        job = res.data[0]
        job_id = job["id"]

        # 2. 상태를 processing으로 업데이트 (동시성 방지를 위해 update 성공 여부 확인이 좋으나 일단 단순 구현)
        update_res = self.sb.table("image_jobs") \
            .update({"status": "processing", "updated_at": "now()"}) \
            .eq("id", job_id) \
            .execute()
        
        return update_res.data[0]

    def update_job_status(self, job_id: str, status: str) -> dict:
        res = self.sb.table("image_jobs") \
            .update({"status": status, "updated_at": "now()"}) \
            .eq("id", job_id) \
            .execute()
        return res.data[0]

    def save_image(self, scene_id: str, job_id: str, image_url: str) -> dict:
        payload = {
            "scene_id": scene_id,
            "job_id": job_id,
            "image_url": image_url
        }
        res = self.sb.table("images").insert(payload).execute()
        return res.data[0]

    def upload_image_to_storage(self, file_path: str, binary_data: bytes) -> str:
        """Supabase Storage에 업로드하고 공용 URL 반환"""
        # 'images' 버킷이 미리 생성되어 있어야 함
        self.sb.storage.from_("images").upload(
            path=file_path,
            file=binary_data,
            file_options={"content-type": "image/png"}
        )
        return self.sb.storage.from_("images").get_public_url(file_path)

