from __future__ import annotations

from fastapi import FastAPI

from app.api import health, novels, scenes


def create_app() -> FastAPI:
    app = FastAPI(title="Narrative Engine", version="0.1.0")
    app.include_router(health.router)
    app.include_router(novels.router)
    app.include_router(scenes.router)
    return app


app = create_app()

