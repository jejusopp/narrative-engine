from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, novels, scenes, characters


def create_app() -> FastAPI:
    app = FastAPI(title="Narrative Engine", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(novels.router)
    app.include_router(scenes.router)
    app.include_router(characters.router)
    return app


app = create_app()

