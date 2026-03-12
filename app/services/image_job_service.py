from __future__ import annotations

from app.repositories.image_repository import ImageRepository


def create_job(scene_id: str, prompt: str) -> dict:
    repo = ImageRepository()
    return repo.create_image_job(scene_id=scene_id, prompt=prompt)

