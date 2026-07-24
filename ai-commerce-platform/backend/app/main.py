"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="AI-first, modular, headless commerce platform — MVP foundation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Report the application's health status and configured AI provider.
    
    Returns:
    	dict: A status payload containing ``"ok"`` and the configured AI provider.
    """
    return {"status": "ok", "ai_provider": settings.AI_PROVIDER}


@app.get("/", tags=["meta"])
def root() -> dict:
    """Provide basic project metadata and links to the documentation and API."""
    return {
        "name": settings.PROJECT_NAME,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }
