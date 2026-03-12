from __future__ import annotations

from app.db.supabase import get_supabase


class SceneEmbeddingRepository:
    def __init__(self):
        self.sb = get_supabase()

    def upsert(self, scene_id: str, novel_id: str, content: str, embedding: list[float]) -> None:
        payload = {"scene_id": scene_id, "novel_id": novel_id, "content": content, "embedding": embedding}
        self.sb.table("scene_context_embeddings").upsert(payload, on_conflict="scene_id").execute()

    def search_by_vector(
        self,
        novel_id: str,
        embedding: list[float],
        top_k: int = 5,
        exclude_scene_ids: list[str] | None = None,
    ) -> list[dict]:
        payload = {
            "p_novel_id": novel_id,
            "query_embedding": embedding,
            "match_count": top_k,
            "exclude_scene_ids": exclude_scene_ids or [],
        }
        res = self.sb.rpc("match_scene_context_embeddings", payload).execute()
        return res.data or []

