from __future__ import annotations
import numpy as np
from typing import Any
from app.llm import embedding_client

def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def split_into_scenes(
    text: str,
    window_size: int = 2,    # 웹소설의 빠른 전환을 잡기 위해 2로 축소
    drop_threshold: float = 0.15, # 유사도가 이전보다 얼마나 급락했는가 (변화율)
    min_scene_chars: int = 300
) -> list[dict[str, Any]]:
    # Step 1. 문단 분리 (단순 공백 제거)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    if len(paragraphs) < window_size:
        return [{"scene_index": 1, "text": "\n\n".join(paragraphs)}]

    # Step 2. 슬라이딩 윈도우 임베딩 (문맥 응집도 확보)
    windows = [" ".join(paragraphs[i : i + window_size]) for i in range(len(paragraphs) - window_size + 1)]
    embeddings = embedding_client.embed_batch(windows)

    # Step 3. 유사도 및 변화율(Gradient) 계산
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = _cosine_similarity(embeddings[i], embeddings[i + 1])
        similarities.append(sim)

    # Step 4. 경계 감지 (상대적 낙폭 지점 찾기)
    # 지엽적인 키워드 대신, 앞 문맥과 뒤 문맥의 '의미적 단절'이 발생하는 순간을 포착
    boundaries = []
    for i in range(1, len(similarities)):
        # 이전 유사도 대비 현재 유사도가 급격히 떨어지는 '절벽' 탐지
        prev_sim = similarities[i-1]
        curr_sim = similarities[i]

        if prev_sim - curr_sim > drop_threshold:
            # 낙폭이 크면 새로운 장면의 시작점으로 간주
            boundaries.append(i + window_size)

    # Step 5. 장면 구성 및 최소 길이 보장
    scenes: list[str] = []
    start = 0

    # 중복 제거 및 정렬
    sorted_boundaries = sorted(list(set(boundaries)))

    for b in sorted_boundaries:
        current_scene_text = "\n\n".join(paragraphs[start:b])

        if len(current_scene_text) >= min_scene_chars or not scenes:
            scenes.append(current_scene_text)
            start = b
        else:
            # 너무 짧으면 이전 장면에 병합
            scenes[-1] += "\n\n" + current_scene_text
            start = b

    # 마지막 남은 문단 처리
    remaining_text = "\n\n".join(paragraphs[start:])
    if remaining_text:
        if len(remaining_text) < min_scene_chars and scenes:
            scenes[-1] += "\n\n" + remaining_text
        else:
            scenes.append(remaining_text)

    return [{"scene_index": i + 1, "text": s.strip()} for i, s in enumerate(scenes)]