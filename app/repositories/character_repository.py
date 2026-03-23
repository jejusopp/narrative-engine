from __future__ import annotations

import re

from app.db.supabase import get_supabase


def _split_description_parts(text: str) -> list[str]:
    parts = re.split(r"[/,]", text)
    return [p.strip() for p in parts if p and p.strip()]


def _merge_description(existing_desc: str, new_desc: str) -> str:
    """Merge character descriptions without duplicate phrases."""
    existing_parts = _split_description_parts(existing_desc)
    new_parts = _split_description_parts(new_desc)
    merged: list[str] = []
    seen: set[str] = set()
    for part in [*existing_parts, *new_parts]:
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(part)
    return ", ".join(merged)


class CharacterRepository:
    def __init__(self):
        self.sb = get_supabase()

    def upsert_character(self, novel_id: str, name: str, description: str | None = None, appearance: str | None = None) -> dict:
        # 기존 캐릭터 조회
        existing = self.sb.table("characters").select("*").eq("novel_id", novel_id).eq("name", name).execute()

        if existing.data:
            row = existing.data[0]
            update_payload: dict = {
                "appearance_count": (row.get("appearance_count") or 0) + 1,
            }
            # description은 토큰 단위로 병합하여 중복 문구 누적을 방지
            existing_desc = (row.get("description") or "").strip()
            new_desc = (description or "").strip()
            if new_desc:
                merged_desc = _merge_description(existing_desc, new_desc) if existing_desc else ", ".join(_split_description_parts(new_desc))
                if merged_desc and merged_desc != existing_desc:
                    update_payload["description"] = merged_desc
            # appearance는 기존 값이 없을 때만 저장
            if appearance and not row.get("appearance"):
                update_payload["appearance"] = appearance
            self.sb.table("characters").update(update_payload).eq("id", row["id"]).execute()
            row.update(update_payload)
            return row
        else:
            payload = {
                "novel_id": novel_id,
                "name": name,
                "description": description,
                "appearance": appearance,
                "appearance_count": 1,
            }
            res = self.sb.table("characters").insert(payload).execute()
            return res.data[0]

    def add_appearance(self, character_id: str, scene_id: str) -> dict:
        payload = {
            "character_id": character_id,
            "scene_id": scene_id,
        }
        res = self.sb.table("character_appearances").insert(payload).execute()
        return res.data[0]

    def list_characters(self, novel_id: str) -> list[dict]:
        res = self.sb.table("characters").select("id,name,description,appearance,appearance_count").eq("novel_id", novel_id).execute()
        return res.data or []

    def rename_character(self, novel_id: str, old_name: str, new_name: str) -> dict | None:
        res = self.sb.table("characters").select("id").eq("novel_id", novel_id).eq("name", old_name).execute()
        if not res.data:
            return None
        char_id = res.data[0]["id"]
        updated = self.sb.table("characters").update({"name": new_name}).eq("id", char_id).execute()
        return updated.data[0] if updated.data else None

    def get_character_detail(self, character_id: str) -> dict | None:
        # 캐릭터 기본 정보 조회
        res = self.sb.table("characters").select("*").eq("id", character_id).execute()
        if not res.data:
            return None
        char = res.data[0]

        # character_appearances 를 통해 등장한 scene 목록 조회 (scene_index 순), 이미지 포함
        appearances_res = (
            self.sb.table("character_appearances")
            .select("scene:scenes(id, scene_index, summary, location, tone, images(image_url))")
            .eq("character_id", character_id)
            .execute()
        )
        
        # 중복 제거 및 정렬 (Supabase select join 시 리스트로 옴)
        scenes = []
        for a in appearances_res.data:
            if not a.get("scene"):
                continue
            s = a["scene"]
            image_url = None
            if s.get("images") and len(s["images"]) > 0:
                image_url = s["images"][0]["image_url"]
            
            scenes.append({
                "id": s["id"],
                "scene_index": s["scene_index"],
                "summary": s["summary"],
                "location": s["location"],
                "tone": s["tone"],
                "image_url": image_url
            })
        
        scenes.sort(key=lambda x: x["scene_index"])
        
        char["scenes"] = scenes
        return char

