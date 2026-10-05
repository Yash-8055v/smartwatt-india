"""
SmartWatt India — Backend Configuration
Reads environment variables from .env file (development) or system env (production/Render).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env only in development — production env vars come from Render dashboard
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

APP_ENV: str = os.getenv("APP_ENV", "production")
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
MODEL_VERSION: str = os.getenv("MODEL_VERSION", "v0.1.0")
DATA_VERSION: str = os.getenv("DATA_VERSION", "v0.1.0")

# ── Data / model paths ─────────────────────────────────────────────────────────
# These resolve relative to the repo root regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PROCESSED_DIR: Path = _REPO_ROOT / "data" / "processed"
MODEL_PATH: Path = _REPO_ROOT / "ml" / "models" / "ridge_model.joblib"

ANOMALY_FEATURES_CSV: Path = PROCESSED_DIR / "anomaly_features.csv"
MODEL_PREDICTIONS_CSV: Path = PROCESSED_DIR / "model_predictions.csv"
MODEL_METRICS_JSON: Path = PROCESSED_DIR / "model_metrics.json"
EVALUATION_REPORT_JSON: Path = PROCESSED_DIR / "evaluation_report.json"
