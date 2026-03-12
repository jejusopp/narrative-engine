from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Any

from app.config import get_settings
from app.llm.comfy_client import ComfyClient
from app.repositories.image_repository import ImageRepository

logger = logging.getLogger("ImageService")

class ImageService:
    def __init__(self):
        self.settings = get_settings()
        self.repo = ImageRepository()
        self.comfy_client = ComfyClient(
            host=self.settings.comfyui_host,
            client_id=self.settings.comfyui_client_id
        )
        # 워크플로우 템플릿 로드
        workflow_path = os.path.join(os.path.dirname(__file__), "..", "llm", "workflows", "sdxl_base.json")
        with open(workflow_path, 'r') as f:
            self.workflow_template = json.load(f)

    def _enrich_prompt(self, base_prompt: str) -> str:
        """지브리 스타일의 고품질 삽화를 위해 프롬프트 강화"""
        style_suffix = (
            ", Studio Ghibli art style, anime style, "
            "vibrant colors, detailed background, hand-drawn, "
            "soft lighting, cinematic composition, high quality, "
            "masterpiece, beautiful scenery"
        )
        return base_prompt + style_suffix

    def generate_image_for_scene(self, scene_id: str, prompt: str) -> Dict[str, Any]:
        """특정 씬에 대해 이미지를 생성하고 저장 (BackgroundTasks에서 호출 권장)"""
        # 1. Job 생성 (또는 기존 Job 확인)
        # 우선 항상 새로운 Job을 생성하는 방식으로 구현 (기존 create_image_job 활용)
        job = self.repo.create_image_job(scene_id, prompt)
        job_id = job["id"]

        logger.info(f"Starting image generation for scene {scene_id}, job {job_id}")
        
        try:
            # 상태를 processing으로 변경
            self.repo.update_job_status(job_id, "processing")

            # 2. 프롬프트 강화
            enriched_prompt = self._enrich_prompt(prompt)

            # 3. 워크플로우 주입
            workflow = self.workflow_template.copy()
            # sdxl_base.json의 구조에 따라 노드 ID 6번이 Positive Prompt라고 가정
            if "6" in workflow and "inputs" in workflow["6"]:
                workflow["6"]["inputs"]["text"] = enriched_prompt
            else:
                # 템플릿 구조가 다를 경우를 대비해 로그 남김 (실제 운영 시 확인 필요)
                logger.warning("Node 6 not found in workflow template, check node IDs")

            # 4. ComfyUI 호출
            logger.info(f"Sending prompt to ComfyUI for job {job_id}")
            image_binary = self.comfy_client.generate_image(workflow)

            if not image_binary:
                raise Exception("Failed to get image from ComfyUI")

            # 5. 이미지 업로드
            file_name = f"{scene_id}_{int(time.time())}.png"
            file_path = f"generated/{file_name}"
            
            logger.info(f"Uploading image to storage: {file_path}")
            image_url = self.repo.upload_image_to_storage(file_path, image_binary)

            # 6. DB 기록
            self.repo.save_image(scene_id, job_id, image_url)
            self.repo.update_job_status(job_id, "completed")

            logger.info(f"Successfully completed image generation for scene {scene_id}")
            return {"status": "success", "image_url": image_url}

        except Exception as e:
            logger.error(f"Error generating image for job {job_id}: {str(e)}")
            self.repo.update_job_status(job_id, "failed")
            return {"status": "failed", "error": str(e)}
