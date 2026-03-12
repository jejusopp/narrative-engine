from __future__ import annotations

from app.llm.embedding_client import embed
from app.repositories.character_repository import CharacterRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.scene_embedding_repository import SceneEmbeddingRepository
from app.repositories.scene_repository import SceneRepository
from app.services import scene_context_retriever
from app.services.character_resolver import resolve_all
from app.services.prompt_generator import generate as generate_image_prompt
from app.services.scene_processor import process as process_scene
from app.services.image_job_service import create_job as create_image_job


def _build_embedding_content(summary: str, location: str, tone: str, characters: list[dict]) -> str:
    names = [c.get("name") for c in characters if c.get("name")]
    return (
        f"Summary: {summary}\n"
        f"Location: {location}\n"
        f"Tone: {tone}\n"
        f"Characters: {', '.join(names)}"
    )


def analyze_scene(novel_id: str, scene_index: int, scene_text: str) -> dict:
    char_repo = CharacterRepository()
    known_characters = char_repo.list_characters(novel_id)

    retrieved = scene_context_retriever.retrieve(novel_id=novel_id, scene_text=scene_text, top_k=5)

    result = process_scene(
        scene_text=scene_text,
        previous_summary=None,
        known_characters=known_characters,
        retrieved_context=retrieved,
    )

    resolved_characters = resolve_all(result.get("characters", []), novel_id=novel_id, known_characters=known_characters)

    scene_repo = SceneRepository()
    scene_row = scene_repo.save_scene(
        novel_id=novel_id,
        scene_index=scene_index,
        text=scene_text,
        summary=result.get("summary", ""),
        location=result.get("location", ""),
        tone=result.get("tone", ""),
        status="completed",
    )

    # upsert characters (resolve된 이름 기준)
    name_to_id: dict[str, str] = {}
    for ch in resolved_characters:
        row = char_repo.upsert_character(novel_id=novel_id, name=ch["name"], description=ch.get("description"))
        name_to_id[row["name"]] = row["id"]

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

    # RAG 임베딩 저장
    content = _build_embedding_content(
        summary=result.get("summary", ""),
        location=result.get("location", ""),
        tone=result.get("tone", ""),
        characters=resolved_characters,
    )
    emb = embed(content)
    SceneEmbeddingRepository().upsert(scene_id=scene_row["id"], novel_id=novel_id, content=content, embedding=emb)

    # 이미지 프롬프트 및 job 생성
    image_prompt = generate_image_prompt(scene_summary=result.get("summary", ""), characters=resolved_characters)
    create_image_job(scene_id=scene_row["id"], prompt=image_prompt)

    return {
        "scene_id": scene_row["id"],
        "summary": result.get("summary", ""),
        "location": result.get("location", ""),
        "tone": result.get("tone", ""),
        "characters": resolved_characters,
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

