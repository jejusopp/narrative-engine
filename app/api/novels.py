from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.repositories.novel_repository import NovelRepository
from app.services.scene_chunker import split_into_scenes
from app.services.novel_processor import process_novel


router = APIRouter()


class CreateNovelRequest(BaseModel):
    title: str
    author: str | None = None
    description: str | None = None


class ProcessNovelRequest(BaseModel):
    text: str


@router.post("/novels")
def create_novel(body: CreateNovelRequest):
    repo = NovelRepository()
    novel = repo.create_novel(title=body.title, author=body.author, description=body.description)
    return {"novel_id": novel["id"], "title": novel["title"], "status": novel.get("status", "pending")}


@router.post("/novels/{novel_id}/process")
def process_novel_endpoint(novel_id: str, body: ProcessNovelRequest, background_tasks: BackgroundTasks):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    chunks = split_into_scenes(body.text)

    repo = NovelRepository()
    repo.update_status(novel_id, "processing")
    background_tasks.add_task(process_novel, novel_id, body.text)

    return {"novel_id": novel_id, "status": "processing", "total_scenes": len(chunks)}

