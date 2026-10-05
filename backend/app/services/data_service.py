"""
SmartWatt India — Data & Model Service
Loads all processed data and the trained model ONCE at startup.
All API endpoints read from these in-memory objects (read-only).

No database. No auth. Consistent with ADR-003.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from app.core.config import (
    ANOMALY_FEATURES_CSV,
    EVALUATION_REPORT_JSON,
    MODEL_METRICS_JSON,
    MODEL_PATH,
    MODEL_PREDICTIONS_CSV,
)

log = logging.getLogger(__name__)


class DataStore:
    """
    In-memory store for all processed data.
    Loaded once at application startup via the lifespan context manager.
    All DataFrames are read-only after load.
    """

    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None          # merged timeseries + anomaly flags
        self._model = None
        self._metrics: Optional[dict] = None
        self._eval_report: Optional[dict] = None

    # ── Load ──────────────────────────────────────────────────────────────────
    def load(self) -> None:
        log.info("Loading anomaly features CSV...")
        feats = pd.read_csv(ANOMALY_FEATURES_CSV, parse_dates=["timestamp"])

        log.info("Loading model predictions CSV...")
        preds = pd.read_csv(MODEL_PREDICTIONS_CSV, parse_dates=["timestamp"])

        # Merge predictions into features (join on apt + timestamp)
        # Keep all original columns from feats; add predictions/residuals from preds.
        preds_cols = [
            "apt", "timestamp", "split",
            "lnenergy_predicted", "residual", "abs_residual",
            "residual_zscore", "energy_kwh_predicted",
        ]
        df = feats.merge(preds[preds_cols], on=["apt", "timestamp"], how="left")

        # Composite anomaly flag: flagged by ≥1 method
        df["is_anomaly"] = (
            df["flag_zscore_hi"].fillna(False) |
            df["flag_iqr_extreme"].fillna(False) |
            df["flag_rolling_spike"].fillna(False) |
            (df["residual_zscore"].fillna(0) > 3)
        )

        # Anomaly severity (0-3, counts how many methods flag this row)
        df["anomaly_method_count"] = (
            df["flag_zscore_hi"].fillna(False).astype(int) +
            df["flag_iqr_extreme"].fillna(False).astype(int) +
            df["flag_rolling_spike"].fillna(False).astype(int) +
            (df["residual_zscore"].fillna(0) > 3).astype(int)
        )

        # Ensure chronological sort
        df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)
        self._df = df

        log.info("Loading model artifact...")
        self._model = joblib.load(MODEL_PATH)

        log.info("Loading model metrics JSON...")
        with open(MODEL_METRICS_JSON) as f:
            self._metrics = json.load(f)

        log.info("Loading evaluation report JSON...")
        with open(EVALUATION_REPORT_JSON) as f:
            self._eval_report = json.load(f)

        log.info(
            f"DataStore loaded: {len(df):,} rows, "
            f"{df['apt'].nunique()} households, "
            f"{df['is_anomaly'].sum():,} anomalies ({df['is_anomaly'].mean()*100:.2f}%)"
        )

    # ── Accessors ─────────────────────────────────────────────────────────────
    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            raise RuntimeError("DataStore not loaded. Call load() first.")
        return self._df

    @property
    def model(self):
        return self._model

    @property
    def metrics(self) -> dict:
        return self._metrics or {}

    @property
    def eval_report(self) -> dict:
        return self._eval_report or {}

    def household_df(self, apt_id: int) -> pd.DataFrame:
        return self.df[self.df["apt"] == apt_id].copy()

    def all_households(self) -> list[int]:
        return sorted(self.df["apt"].unique().tolist())


# Singleton — injected via FastAPI dependency
_store = DataStore()


def get_store() -> DataStore:
    return _store
