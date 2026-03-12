from __future__ import annotations

import re
from typing import Any
import numpy as np

from app.llm import embedding_client


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def split_into_scenes(text: str, window_size: int = 3, threshold: float = 0.65, min_paragraphs: int = 2) -> list[dict[str, Any]]:
    """
    임베딩 기반 시맨틱 장면 분리 알고리즘 (chunking.md 참조)
    """
    # Step 1. 문단 분리
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []
    
    if len(paragraphs) < window_size:
        return [{"scene_index": 1, "text": "\n\n".join(paragraphs)}]

    # Step 2. 슬라이딩 윈도우 생성
    windows: list[str] = []
    for i in range(len(paragraphs) - window_size + 1):
        window_text = " ".join(paragraphs[i : i + window_size])
        windows.append(window_text)

    # Step 3. 임베딩 생성
    embeddings = embedding_client.embed_batch(windows)

    # Step 4. 유사도 계산 및 경계 감지
    boundaries: list[int] = []
    for i in range(len(embeddings) - 1):
        sim = _cosine_similarity(embeddings[i], embeddings[i + 1])
        if sim < threshold:
            # 경계 지점: i + window_size 문단 이전
            boundaries.append(i + window_size)

    # Step 5. 장면 구성 및 최소 길이 보장
    scenes: list[list[str]] = []
    start = 0
    for b in boundaries:
        current_scene_paras = paragraphs[start:b]
        if len(current_scene_paras) >= min_paragraphs or not scenes:
            scenes.append(current_scene_paras)
            start = b
        else:
            # 너무 짧으면 이전 장면에 병합
            scenes[-1].extend(current_scene_paras)
            start = b

    # 남은 문단 처리
    remaining = paragraphs[start:]
    if remaining:
        if not scenes:
            scenes.append(remaining)
        elif len(remaining) < min_paragraphs:
            scenes[-1].extend(remaining)
        else:
            scenes.append(remaining)

    # Step 6. 최종 결과 반환
    result = []
    for idx, scene_paras in enumerate(scenes):
        result.append({
            "scene_index": idx + 1,
            "text": "\n\n".join(scene_paras).strip()
        })

    return result

