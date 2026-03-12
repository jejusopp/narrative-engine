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

    return char
