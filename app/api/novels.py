from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.repositories.novel_repository import NovelRepository
from app.repositories.character_repository import CharacterRepository
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


@router.get("/novels")
def list_novels_endpoint():
    repo = NovelRepository()
    novels = repo.list_novels()
    # 프론트엔드 기대 형식에 맞게 필드명 매핑 (id -> novel_id)
    return [{"novel_id": n["id"], "title": n["title"], "author": n.get("author"), "status": n.get("status"), "created_at": n.get("created_at")} for n in novels]


@router.get("/novels/{novel_id}")
def get_novel_endpoint(novel_id: str):
    repo = NovelRepository()
    try:
        novel = repo.get_novel(novel_id)
        return {"novel_id": novel["id"], "title": novel["title"], "author": novel.get("author"), "status": novel.get("status"), "created_at": novel.get("created_at")}
    except KeyError:
        raise HTTPException(status_code=404, detail="Novel not found")


@router.post("/novels/{novel_id}/process")
def process_novel_endpoint(novel_id: str, body: ProcessNovelRequest, background_tasks: BackgroundTasks):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    chunks = split_into_scenes(body.text)

    repo = NovelRepository()
    repo.update_status(novel_id, "processing")
    background_tasks.add_task(process_novel, novel_id, body.text, background_tasks)

    return {"novel_id": novel_id, "status": "processing", "total_scenes": len(chunks)}


@router.get("/novels/{novel_id}/characters")
def list_characters_endpoint(novel_id: str):
    repo = CharacterRepository()
    characters = repo.list_characters(novel_id)
    # id -> character_id 매핑
    return [{**c, "character_id": c["id"]} for c in characters]


@router.delete("/novels/{novel_id}")
def delete_novel_endpoint(novel_id: str):
    repo = NovelRepository()
    try:
        repo.get_novel(novel_id)
        repo.delete_novel(novel_id)
        return {"novel_id": novel_id, "status": "deleted"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Novel not found")

