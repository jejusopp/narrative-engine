from __future__ import annotations

import re
from typing import Any
import numpy as np

from app.llm import embedding_client


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def split_into_scenes(
    text: str, 
    window_size: int = 4, 
    threshold: float = 0.65, 
    min_paragraphs: int = 2,
    min_scene_chars: int = 300
) -> list[dict[str, Any]]:
    """
    임베딩 기반 시맨틱 장면 분리 알고리즘 (chunking.md 참조)
    웹 소설 특성을 고려하여 짧은 문단들을 묶어 분석 단위를 최적화함.
    """
    # Step 1. 문단 분리 및 짧은 문단 묶기 (Semantic Chunks 생성)
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paragraphs:
        return []
    
    # 너무 짧은 문단들이 많으면 임베딩이 불안정하므로 일정 길이(예: 200자)까지 묶음
    paragraphs: list[str] = []
    current_chunk = []
    current_len = 0
    for p in raw_paragraphs:
        current_chunk.append(p)
        current_len += len(p)
        if current_len >= 200:
            paragraphs.append("\n\n".join(current_chunk))
            current_chunk = []
            current_len = 0
    if current_chunk:
        if paragraphs:
            paragraphs[-1] += "\n\n" + "\n\n".join(current_chunk)
        else:
            paragraphs.append("\n\n".join(current_chunk))

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
    # 유사도 변화의 골짜기(Local Minima)를 찾는 방식이 더 정확할 수 있으나, 
    # 일단은 단순 threshold 방식을 유지하되 민감도를 조절함.
    boundaries: list[int] = []
    for i in range(len(embeddings) - 1):
        sim = _cosine_similarity(embeddings[i], embeddings[i + 1])
        if sim < threshold:
            # 경계 지점: i + window_size 문단 이전
            boundaries.append(i + window_size)

    # Step 5. 장면 구성 및 최소 길이(문단 수 & 글자 수) 보장
    scenes: list[list[str]] = []
    start = 0
    for b in boundaries:
        current_scene_paras = paragraphs[start:b]
        scene_text = "\n\n".join(current_scene_paras)
        
        # 문단 수뿐만 아니라 글자 수(min_scene_chars)도 체크하여 너무 짧은 씬 방지
        if (len(current_scene_paras) >= min_paragraphs and len(scene_text) >= min_scene_chars) or not scenes:
            scenes.append(current_scene_paras)
            start = b
        else:
            # 너무 짧으면 이전 장면에 병합 (이미 장면이 있을 경우에만)
            if scenes:
                scenes[-1].extend(current_scene_paras)
                start = b
            else:
                scenes.append(current_scene_paras)
                start = b

    # 남은 문단 처리
    remaining = paragraphs[start:]
    if remaining:
        remaining_text = "\n\n".join(remaining)
        if not scenes:
            scenes.append(remaining)
        elif len(remaining) < min_paragraphs or len(remaining_text) < min_scene_chars:
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

