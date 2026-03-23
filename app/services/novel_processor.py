from __future__ import annotations

import time

from fastapi import BackgroundTasks

from app.repositories.character_repository import CharacterRepository
from app.repositories.novel_repository import NovelRepository
from app.services.scene_chunker import split_into_scenes
from app.services.scene_pipeline import analyze_scene


def process_novel(novel_id: str, full_text: str, background_tasks: BackgroundTasks | None = None) -> None:
    novel_repo = NovelRepository()
    char_repo = CharacterRepository()

    chunks = split_into_scenes(full_text)
    for ch in chunks:
        _ = char_repo.list_characters(novel_id)
        analyze_scene(
            novel_id=novel_id,
            scene_index=ch["scene_index"],
            scene_text=ch["text"],
            background_tasks=background_tasks,
        )
        time.sleep(1)

    novel_repo.update_status(novel_id, "completed")

