from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    llm_model: str

    supabase_url: str
    supabase_service_key: str

    embedding_provider: str
    embedding_model: str

    comfyui_host: str
    comfyui_client_id: str


def get_settings() -> Settings:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "local").strip()
    embedding_model = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2").strip()

    comfyui_host = os.getenv("COMFYUI_HOST", "localhost:8188").strip()
    comfyui_client_id = os.getenv("COMFYUI_CLIENT_ID", "story_lens_engine").strip()

    return Settings(
        groq_api_key=groq_api_key,
        llm_model=llm_model,
        supabase_url=supabase_url,
        supabase_service_key=supabase_service_key,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        comfyui_host=comfyui_host,
        comfyui_client_id=comfyui_client_id,
    )
