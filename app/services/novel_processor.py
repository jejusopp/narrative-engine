from __future__ import annotations

from fastapi import BackgroundTasks

from app.repositories.character_repository import CharacterRepository
from app.repositories.novel_repository import NovelRepository
from app.services.scene_chunker import split_into_scenes
from app.services.scene_pipeline import analyze_scene


def process_novel(novel_id: str, full_text: str, background_tasks: BackgroundTasks | None = None) -> None:
    novel_repo = NovelRepository()
    char_repo = CharacterRepository()

    chunks = split_into_scenes(full_text)
    previous_summary: str | None = None

    for ch in chunks:
        # MVP: scene_pipeline이 previous_summary를 아직 쓰지 않으므로, 추후 확장 포인트로 유지
        _ = char_repo.list_characters(novel_id)
        result = analyze_scene(
            novel_id=novel_id,
            scene_index=ch["scene_index"],
            scene_text=ch["text"],
            background_tasks=background_tasks,
        )
        previous_summary = result.get("summary") or previous_summary

    novel_repo.update_status(novel_id, "completed")

