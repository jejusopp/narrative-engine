from __future__ import annotations

from app.llm.embedding_client import embed
from app.repositories.scene_embedding_repository import SceneEmbeddingRepository


def retrieve(
    novel_id: str,
    scene_text: str,
    top_k: int = 5,
    exclude_scene_ids: list[str] | None = None,
) -> list[dict]:
    # 너무 긴 텍스트는 앞부분만 사용 (임베딩 비용/시간 절감)
    vector = embed(scene_text[:2000])
    repo = SceneEmbeddingRepository()
    return repo.search_by_vector(novel_id=novel_id, embedding=vector, top_k=top_k, exclude_scene_ids=exclude_scene_ids)

