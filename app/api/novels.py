from __future__ import annotations
import re
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Request

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


def _preprocess_text(text: str) -> str:
    """
    텍스트 전처리: 불필요한 공백 제거 및 줄바꿈 정규화
    """
    # 1. 3개 이상의 줄바꿈을 2개로 통일 (\n\n\n+ -> \n\n)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 2. 문장 앞뒤 공백 제거 및 탭 등 특수 공백 문자를 일반 공백으로
    lines = [line.strip() for line in text.split('\n')]
    
    # 3. 빈 줄이 연속으로 나오는 것을 방지하며 재결합
    processed_text = '\n'.join(lines)
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)
    
    return processed_text.strip()


@router.post("/novels/{novel_id}/process")
async def process_novel_endpoint(
    novel_id: str, 
    background_tasks: BackgroundTasks,
    request: Request,
    text: str | None = Form(None),
    file: UploadFile | None = File(None)
):
    print(f"DEBUG: novel_id={novel_id}, text_len={len(text) if text else 0}, file={file.filename if file else 'None'}")
    
    # 더 자세한 디버깅을 위해 폼 데이터 직접 확인
    try:
        form_data = await request.form()
        print(f"DEBUG: Form keys: {list(form_data.keys())}")
    except Exception as e:
        print(f"DEBUG: Error reading form: {str(e)}")

    raw_text = ""
    
    # 1. 파일 업로드 우선
    if file and file.filename:
        content = await file.read()
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("cp949", errors="ignore")
    # 2. Form 데이터의 text 필드 확인
    elif text:
        raw_text = text
    
    if not raw_text or not raw_text.strip():
        print("DEBUG: raw_text is empty!")
        raise HTTPException(status_code=400, detail="text or file is required via form-data")

    # 텍스트 전처리 적용
    final_text = _preprocess_text(raw_text)
    print(f"DEBUG: Preprocessed text_len: {len(raw_text)} -> {len(final_text)}")
    print(f"DEBUG: final_text sample: {final_text[:100]}...")
    
    try:
        chunks = split_into_scenes(final_text)
        print(f"DEBUG: total_scenes={len(chunks)}")
    except Exception as e:
        print(f"DEBUG: split_into_scenes error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scene chunking failed: {str(e)}")

    repo = NovelRepository()
    repo.update_status(novel_id, "processing")
    repo.update_content(novel_id, final_text)
    background_tasks.add_task(process_novel, novel_id, final_text, background_tasks)

    return {"novel_id": novel_id, "status": "processing", "total_scenes": len(chunks)}


@router.get("/novels/{novel_id}/content")
def get_novel_content_endpoint(novel_id: str):
    repo = NovelRepository()
    content = repo.get_novel_content(novel_id)
    return {"novel_id": novel_id, "content": content}


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

