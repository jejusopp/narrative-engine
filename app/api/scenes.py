from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.scene_pipeline import analyze_scene


router = APIRouter()


class AnalyzeSceneRequest(BaseModel):
    novel_id: str
    scene_index: int
    text: str


@router.post("/analyze-scene")
def analyze_scene_endpoint(body: AnalyzeSceneRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    return analyze_scene(novel_id=body.novel_id, scene_index=body.scene_index, scene_text=body.text)

