"""FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gmle.app.api.rest.errors import api_exception_handler
from gmle.app.infra.errors import AnkiError, ConfigError, InfraError, SOTError
from .routes import config, global_config, ingest, items, llm_config, prompts_config, runs, spaces, system

app = FastAPI(
    title="GMLE Light REST API",
    description="GMLE Light - Lightweight MCQ Generator with Local Anki Integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ConfigError, api_exception_handler)
app.add_exception_handler(InfraError, api_exception_handler)
app.add_exception_handler(AnkiError, api_exception_handler)
app.add_exception_handler(SOTError, api_exception_handler)
app.add_exception_handler(Exception, api_exception_handler)

# Include routers
app.include_router(spaces.router, prefix="/api/v1", tags=["spaces"])
app.include_router(runs.router, prefix="/api/v1", tags=["runs"])
app.include_router(items.router, prefix="/api/v1", tags=["items"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(global_config.router, prefix="/api/v1", tags=["global_config"])
app.include_router(llm_config.router, prefix="/api/v1", tags=["llm_config"])
app.include_router(prompts_config.router, prefix="/api/v1", tags=["prompts_config"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "GMLE Light REST API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

