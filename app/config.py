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


def get_settings() -> Settings:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "local").strip()
    embedding_model = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2").strip()

    return Settings(
        groq_api_key=groq_api_key,
        llm_model=llm_model,
        supabase_url=supabase_url,
        supabase_service_key=supabase_service_key,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
    )
