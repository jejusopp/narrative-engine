from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    settings = get_settings()
    if settings.embedding_provider != "local":
        raise RuntimeError("Only EMBEDDING_PROVIDER=local is supported in this project setup")
    return SentenceTransformer(settings.embedding_model)


def embed(text: str) -> list[float]:
    model = _get_model()
    vec = model.encode([text], normalize_embeddings=True)
    return vec[0].tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]

