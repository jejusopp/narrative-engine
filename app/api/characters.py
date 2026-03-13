from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.repositories.character_repository import CharacterRepository
from app.repositories.relationship_repository import RelationshipRepository

router = APIRouter()

@router.get("/characters/{character_id}")
def get_character_detail_endpoint(character_id: str):
    char_repo = CharacterRepository()
    rel_repo = RelationshipRepository()

    char = char_repo.get_character_detail(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    relationships = rel_repo.list_character_relationships(character_id)
    char["relationships"] = relationships

    # id -> character_id 매핑
    char["character_id"] = char["id"]
    return char


@router.get("/characters/{character_id}/relationships")
def get_character_relationships_endpoint(character_id: str):
    rel_repo = RelationshipRepository()
    return rel_repo.list_character_relationships(character_id)
