from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.services.scene_pipeline import analyze_scene
from app.services.image_service import ImageService
from app.repositories.scene_repository import SceneRepository
from app.db.supabase import get_supabase


router = APIRouter()


class AnalyzeSceneRequest(BaseModel):
    novel_id: str
    scene_index: int
    text: str


@router.post("/analyze-scene")
def analyze_scene_endpoint(body: AnalyzeSceneRequest, background_tasks: BackgroundTasks):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    return analyze_scene(
        novel_id=body.novel_id, 
        scene_index=body.scene_index, 
        scene_text=body.text,
        background_tasks=background_tasks
    )


@router.get("/novels/{novel_id}/scenes")
def list_novel_scenes_endpoint(novel_id: str):
    repo = SceneRepository()
    scenes = repo.list_scenes_by_novel(novel_id)
    # id -> scene_id 매핑, image_url 포함
    return [{**s, "scene_id": s["id"]} for s in scenes]


@router.get("/scenes/{scene_id}")
def get_scene_endpoint(scene_id: str):
    repo = SceneRepository()
    scene = repo.get_scene_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # id -> scene_id 매핑
    return {**scene, "scene_id": scene["id"]}


@router.post("/scenes/{scene_id}/generate-image")
def generate_image_endpoint(scene_id: str, background_tasks: BackgroundTasks):
    sb = get_supabase()
    # 씬 정보 확인 및 이미지 생성용 프롬프트 가져오기
    res = sb.table("scenes").select("id, summary").eq("id", scene_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    scene = res.data[0]
    summary = scene["summary"]
    
    # 등장인물 목록 가져오기 (더 나은 프롬프트를 위해)
    char_res = sb.table("character_appearances").select("characters(name)").eq("scene_id", scene_id).execute()
    characters = [c["characters"] for c in char_res.data if c.get("characters")]
    
    # 1. 이미지 서비스 초기화
    image_service = ImageService()
    
    # 2. 이미지 프롬프트 생성 (기존 prompt_generator 활용하거나 직접 호출)
    from app.services.prompt_generator import generate as generate_image_prompt
    image_prompt = generate_image_prompt(scene_summary=summary, characters=characters)
    
    # 3. 백그라운드 작업으로 이미지 생성 실행
    sb.table("scenes").update({"status": "processing"}).eq("id", scene_id).execute()
    background_tasks.add_task(image_service.generate_image_for_scene, scene_id, image_prompt)
    
    return {"scene_id": scene_id, "image_status": "processing", "message": "Image generation started in background"}

