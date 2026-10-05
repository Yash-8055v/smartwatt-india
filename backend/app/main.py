"""
SmartWatt India — FastAPI Application Entry Point

Architecture decisions in effect:
  - ADR-004: FastAPI backend
  - ADR-003: No database; data loaded from CSV/JSON artifacts at startup
  - ADR-005: Render deployment (CORS origin from env var FRONTEND_ORIGIN)

Startup:
  1. Load DataStore (all processed CSVs + model artifact) into memory.
  2. Register API routes.
  3. Configure CORS.

Run locally:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import APP_ENV, FRONTEND_ORIGIN, MODEL_VERSION
from app.services.data_service import get_store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data once at startup; nothing to teardown (read-only)."""
    log.info(f"SmartWatt India API starting (env={APP_ENV}, version={MODEL_VERSION})")
    store = get_store()
    store.load()
    log.info("DataStore ready.")
    yield
    log.info("SmartWatt India API shutting down.")


app = FastAPI(
    title="SmartWatt India API",
    description=(
        "Context-aware electricity consumption anomaly detection for Indian households. "
        "Statistical and ML-based anomaly signals on the IIIT-Delhi residential dataset."
    ),
    version=MODEL_VERSION,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In production the FRONTEND_ORIGIN env var is set in the Render dashboard.
# Never hardcode localhost in production paths — reads from env.
origins = [
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")
