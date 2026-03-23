from __future__ import annotations

import logging

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

from app.llm.embedding_client import embed
from app.repositories.character_repository import CharacterRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.scene_embedding_repository import SceneEmbeddingRepository
from app.repositories.scene_repository import SceneRepository
from app.services import scene_context_retriever
from app.services.character_resolver import resolve_all
from app.services.prompt_generator import generate as generate_image_prompt
from app.services.scene_processor import process as process_scene
from app.services.image_service import ImageService


def _build_scene_context_embedding_content(
    characters: list[dict],
    relationships: list[dict] | None,
    summary_fallback: str = "",
) -> str:
    """RAG·중복 판별용: 요약 대신 등장 인물(설명·외형)과 씬 관계를 임베딩한다."""
    lines: list[str] = []

    char_lines: list[str] = []
    for ch in characters or []:
        name = (ch.get("name") or "").strip()
        if not name:
            continue
        desc = (ch.get("description") or "").strip()
        app = ch.get("appearance")
        if isinstance(app, list):
            app = ", ".join(str(x) for x in app if x)
        app = (str(app).strip() if app else "").strip()
        if app.lower() == "null":
            app = ""
        block = [f"- {name}"]
        if desc:
            block.append(f"  설명: {desc}")
        if app:
            block.append(f"  외형: {app}")
        char_lines.append("\n".join(block))

    if char_lines:
        lines.append("등장 인물:")
        lines.extend(char_lines)

    rel_lines: list[str] = []
    for r in relationships or []:
        a = (r.get("character_a") or "").strip()
        b = (r.get("character_b") or "").strip()
        rel = (r.get("relationship") or "").strip()
        if not a or not b:
            continue
        if rel:
            rel_lines.append(f"- {a} — {rel} — {b}")
        else:
            rel_lines.append(f"- {a}, {b}")

    if rel_lines:
        if lines:
            lines.append("")
        lines.append("관계:")
        lines.extend(rel_lines)

    text = "\n".join(lines).strip()
    if text:
        return text
    fb = (summary_fallback or "").strip()
    return fb if fb else "(등장 인물·관계 없음)"


def _dedupe_event_sentences(events: list[str] | None) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for e in events or []:
        text = str(e).strip()
        if not text:
            continue
        key = " ".join(text.split()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(text)
    return unique


def analyze_scene(novel_id: str, scene_index: int, scene_text: str, background_tasks: BackgroundTasks | None = None) -> dict:
    char_repo = CharacterRepository()
    known_characters = char_repo.list_characters(novel_id)

    # 관계 정보를 known_characters에 병합
    rel_repo = RelationshipRepository()
    all_rels = rel_repo.list_novel_relationships(novel_id)
    id_to_name = {c["id"]: c["name"] for c in known_characters}
    rel_map: dict[str, list[str]] = {}
    for r in all_rels:
        a_name = id_to_name.get(r["character_a"])
        b_name = id_to_name.get(r["character_b"])
        if a_name and b_name:
            rel_map.setdefault(a_name, []).append(f"{r['relationship']} ({b_name})")
            rel_map.setdefault(b_name, []).append(f"{r['relationship']} ({a_name})")
    for c in known_characters:
        rels = rel_map.get(c["name"], [])
        if rels:
            c["relationships"] = rels

    retrieved = scene_context_retriever.retrieve(novel_id=novel_id, scene_text=scene_text, top_k=2)

    result = process_scene(
        scene_text=scene_text,
        known_characters=known_characters,
        retrieved_context=retrieved,
    )
    cleaned_events = _dedupe_event_sentences(result.get("events"))

    resolved_characters = resolve_all(result.get("characters", []), novel_id=novel_id, known_characters=known_characters)
    logger.info("[scene_pipeline] extracted characters: %s", result.get("characters", []))
    logger.info("[scene_pipeline] resolved characters: %s", resolved_characters)

    scene_repo = SceneRepository()
    scene_row = scene_repo.save_scene(
        novel_id=novel_id,
        scene_index=scene_index,
        text=scene_text,
        summary=result.get("summary", ""),
        location=result.get("location", ""),
        tone=result.get("tone", ""),
        events=cleaned_events,
        status="completed",
    )

    # upsert characters (resolve된 이름 기준)
    name_to_id: dict[str, str] = {}
    for ch in resolved_characters:
        raw_appearance = ch.get("appearance")
        if raw_appearance:
            # LLM이 배열로 반환한 경우 → 문자열로 합치기
            if isinstance(raw_appearance, list):
                raw_appearance = ", ".join(str(x) for x in raw_appearance if x)
            # "남성, null" / "null, 은발" 등 null 토큰 제거 후 빈 값이면 None 처리
            parts = [p.strip() for p in str(raw_appearance).split(",") if p.strip().lower() != "null" and p.strip()]
            raw_appearance = ", ".join(parts) if parts else None
        row = char_repo.upsert_character(novel_id=novel_id, name=ch["name"], description=ch.get("description"), appearance=raw_appearance)
        name_to_id[row["name"]] = row["id"]
        # character_appearances 테이블에 등장 기록 추가
        char_repo.add_appearance(character_id=row["id"], scene_id=scene_row["id"])

    # relationships 저장 (캐릭터 id가 없으면 스킵)
    rel_repo = RelationshipRepository()
    saved_relationships: list[dict] = []
    for rel in result.get("relationships", []) or []:
        a = rel.get("character_a")
        b = rel.get("character_b")
        if not a or not b:
            continue
        a_id = name_to_id.get(a) or next((c["id"] for c in known_characters if c.get("name") == a), None)
        b_id = name_to_id.get(b) or next((c["id"] for c in known_characters if c.get("name") == b), None)
        if not a_id or not b_id:
            continue
        saved_relationships.append(
            rel_repo.save_relationship(
                novel_id=novel_id,
                scene_id=scene_row["id"],
                char_a_id=a_id,
                char_b_id=b_id,
                relationship=rel.get("relationship", ""),
                confidence=float(rel.get("confidence", 0.0) or 0.0),
            )
        )

    # RAG 임베딩 저장 (과거 씬 검색 시 캐릭터 정체·관계·중복 판별 맥락용)
    content = _build_scene_context_embedding_content(
        characters=resolved_characters,
        relationships=result.get("relationships") or [],
        summary_fallback=result.get("summary") or "",
    )
    emb = embed(content)
    SceneEmbeddingRepository().upsert(scene_id=scene_row["id"], novel_id=novel_id, content=content, embedding=emb)

    # 이미지 프롬프트 생성 — DB에 저장된 appearance를 fallback으로 사용
    db_appearance = {kc["name"]: kc.get("appearance") for kc in char_repo.list_characters(novel_id)}
    logger.info("[scene_pipeline] db_appearance: %s", db_appearance)
    chars_for_prompt = [
        {**ch, "appearance": ch.get("appearance") or db_appearance.get(ch.get("name"))}
        for ch in resolved_characters
    ]
    logger.info("[scene_pipeline] chars_for_prompt: %s", chars_for_prompt)
    events = cleaned_events
    image_prompt = generate_image_prompt(scene_summary=result.get("summary", ""), characters=chars_for_prompt, tone=result.get("tone", ""), events=events)
    
    # 2024-03-13 수정: 소설 분석 시 이미지를 자동으로 생성하지 않도록 변경. 
    # 사용자가 직접 생성 버튼을 누를 때만 (POST /scenes/{scene_id}/generate-image) 생성하도록 함.
    # if background_tasks:
    #     image_service = ImageService()
    #     background_tasks.add_task(image_service.generate_image_for_scene, scene_row["id"], image_prompt)

    return {
        "scene_id": scene_row["id"],
        "summary": result.get("summary", ""),
        "location": result.get("location", ""),
        "tone": result.get("tone", ""),
        "characters": resolved_characters,
        "events": cleaned_events,
        "relationships": [
            {
                "character_a": r.get("character_a"),
                "character_b": r.get("character_b"),
                "relationship": r.get("relationship"),
                "confidence": r.get("confidence"),
            }
            for r in (result.get("relationships", []) or [])
        ],
        "image_prompt": image_prompt,
        "retrieved_context": retrieved,
        "saved_relationships_count": len(saved_relationships),
    }

