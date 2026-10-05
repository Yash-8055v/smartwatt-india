"""
SmartWatt India — API Routes
Endpoints:
  GET /health
  GET /metadata
  GET /households
  GET /households/{apt_id}
  GET /households/{apt_id}/timeseries
  GET /households/{apt_id}/anomalies
  GET /summary
"""

import math
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import DATA_VERSION, MODEL_VERSION
from app.schemas.responses import (
    AnomaliesResponse,
    AnomalyPoint,
    GlobalSummaryResponse,
    HealthResponse,
    HouseholdSummary,
    HouseholdsResponse,
    MetadataResponse,
    TimeseriesPoint,
    TimeseriesResponse,
)
from app.services.data_service import DataStore, get_store

router = APIRouter()


def _safe_float(val) -> Optional[float]:
    """Convert to float, returning None for NaN/Inf."""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _safe_bool(val) -> bool:
    try:
        return bool(val)
    except Exception:
        return False


# ── /health ───────────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(store: DataStore = Depends(get_store)):
    return HealthResponse(status="ok", version=MODEL_VERSION)


# ── /metadata ─────────────────────────────────────────────────────────────────
@router.get("/metadata", response_model=MetadataResponse, tags=["system"])
def metadata(store: DataStore = Depends(get_store)):
    df = store.df
    m = store.metrics
    selected = m.get("selected_model", "Ridge")
    test_m = m.get("models", {}).get(selected, {}).get("test_metrics", {})
    return MetadataResponse(
        model_version=MODEL_VERSION,
        data_version=DATA_VERSION,
        n_households=int(df["apt"].nunique()),
        n_observations=int(len(df)),
        date_start=str(df["timestamp"].min()),
        date_end=str(df["timestamp"].max()),
        selected_model=selected,
        model_test_r2=float(test_m.get("r2", 0)),
        model_test_rmse=float(test_m.get("rmse", 0)),
        model_test_mae=float(test_m.get("mae", 0)),
        n_anomalies=int(df["is_anomaly"].sum()),
        anomaly_rate_pct=round(float(df["is_anomaly"].mean() * 100), 2),
    )


# ── /households ───────────────────────────────────────────────────────────────
@router.get("/households", response_model=HouseholdsResponse, tags=["households"])
def list_households(store: DataStore = Depends(get_store)):
    df = store.df
    result = []
    for apt_id in store.all_households():
        grp = store.household_df(apt_id)
        result.append(HouseholdSummary(
            apt_id=apt_id,
            n_observations=int(len(grp)),
            mean_kwh=round(float(grp["energy_kwh"].mean()), 4),
            median_kwh=round(float(grp["energy_kwh"].median()), 4),
            std_kwh=round(float(grp["energy_kwh"].std()), 4),
            n_anomalies=int(grp["is_anomaly"].sum()),
            anomaly_rate_pct=round(float(grp["is_anomaly"].mean() * 100), 2),
            date_start=str(grp["timestamp"].min()),
            date_end=str(grp["timestamp"].max()),
        ))
    return HouseholdsResponse(households=result)


# ── /households/{apt_id} ─────────────────────────────────────────────────────
@router.get("/households/{apt_id}", response_model=HouseholdSummary, tags=["households"])
def get_household(apt_id: int, store: DataStore = Depends(get_store)):
    if apt_id not in store.all_households():
        raise HTTPException(status_code=404, detail=f"Household {apt_id} not found")
    grp = store.household_df(apt_id)
    return HouseholdSummary(
        apt_id=apt_id,
        n_observations=int(len(grp)),
        mean_kwh=round(float(grp["energy_kwh"].mean()), 4),
        median_kwh=round(float(grp["energy_kwh"].median()), 4),
        std_kwh=round(float(grp["energy_kwh"].std()), 4),
        n_anomalies=int(grp["is_anomaly"].sum()),
        anomaly_rate_pct=round(float(grp["is_anomaly"].mean() * 100), 2),
        date_start=str(grp["timestamp"].min()),
        date_end=str(grp["timestamp"].max()),
    )


# ── /households/{apt_id}/timeseries ──────────────────────────────────────────
@router.get(
    "/households/{apt_id}/timeseries",
    response_model=TimeseriesResponse,
    tags=["households"],
)
def get_timeseries(
    apt_id: int,
    date_from: Optional[str] = Query(None, description="ISO date filter start (inclusive), e.g. 2013-10-01"),
    date_to: Optional[str] = Query(None, description="ISO date filter end (inclusive), e.g. 2013-11-30"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Max rows returned"),
    store: DataStore = Depends(get_store),
):
    if apt_id not in store.all_households():
        raise HTTPException(status_code=404, detail=f"Household {apt_id} not found")

    grp = store.household_df(apt_id).sort_values("timestamp")

    if date_from:
        grp = grp[grp["timestamp"] >= date_from]
    if date_to:
        grp = grp[grp["timestamp"] <= date_to + " 23:59:59"]
    if limit:
        grp = grp.head(limit)

    points = []
    for _, row in grp.iterrows():
        points.append(TimeseriesPoint(
            timestamp=str(row["timestamp"]),
            hour=int(row["hour"]),
            dayofweek=int(row["dayofweek"]),
            energy_kwh=round(float(row["energy_kwh"]), 6),
            lnenergy=round(float(row["lnenergy"]), 6),
            temp_c=round(float(row["temp_c"]), 2),
            lnenergy_predicted=_safe_float(row.get("lnenergy_predicted")),
            energy_kwh_predicted=_safe_float(row.get("energy_kwh_predicted")),
            residual=_safe_float(row.get("residual")),
            residual_zscore=_safe_float(row.get("residual_zscore")),
            feat_zscore_global=_safe_float(row.get("feat_zscore_global")),
            feat_rolling_mean_7d=_safe_float(row.get("feat_rolling_mean_7d")),
            feat_rolling_zscore=_safe_float(row.get("feat_rolling_zscore")),
            is_anomaly=_safe_bool(row["is_anomaly"]),
            anomaly_method_count=int(row["anomaly_method_count"]),
            flag_zscore_hi=_safe_bool(row["flag_zscore_hi"]),
            flag_zscore_lo=_safe_bool(row["flag_zscore_lo"]),
            flag_iqr_mild=_safe_bool(row["flag_iqr_mild"]),
            flag_iqr_extreme=_safe_bool(row["flag_iqr_extreme"]),
            flag_rolling_spike=_safe_bool(row["flag_rolling_spike"]),
            flag_rolling_low=_safe_bool(row["flag_rolling_low"]),
            split=str(row["split"]) if "split" in row.index and row["split"] is not None else None,
        ))

    return TimeseriesResponse(apt_id=apt_id, n_points=len(points), data=points)


# ── /households/{apt_id}/anomalies ────────────────────────────────────────────
@router.get(
    "/households/{apt_id}/anomalies",
    response_model=AnomaliesResponse,
    tags=["households"],
)
def get_anomalies(
    apt_id: int,
    min_methods: int = Query(1, ge=1, le=4, description="Min anomaly methods that must flag a row"),
    store: DataStore = Depends(get_store),
):
    if apt_id not in store.all_households():
        raise HTTPException(status_code=404, detail=f"Household {apt_id} not found")

    grp = store.household_df(apt_id)
    anomalies = grp[grp["anomaly_method_count"] >= min_methods].sort_values("timestamp")

    points = []
    for _, row in anomalies.iterrows():
        points.append(AnomalyPoint(
            timestamp=str(row["timestamp"]),
            energy_kwh=round(float(row["energy_kwh"]), 6),
            lnenergy_predicted=_safe_float(row.get("lnenergy_predicted")),
            residual_zscore=_safe_float(row.get("residual_zscore")),
            feat_zscore_global=_safe_float(row.get("feat_zscore_global")),
            feat_rolling_zscore=_safe_float(row.get("feat_rolling_zscore")),
            is_anomaly=True,
            anomaly_method_count=int(row["anomaly_method_count"]),
            flag_zscore_hi=_safe_bool(row["flag_zscore_hi"]),
            flag_iqr_extreme=_safe_bool(row["flag_iqr_extreme"]),
            flag_rolling_spike=_safe_bool(row["flag_rolling_spike"]),
            residual_z_flagged=(_safe_float(row.get("residual_zscore")) or 0) > 3,
        ))

    return AnomaliesResponse(apt_id=apt_id, n_anomalies=len(points), data=points)


# ── /summary ─────────────────────────────────────────────────────────────────
@router.get("/summary", response_model=GlobalSummaryResponse, tags=["analysis"])
def summary(store: DataStore = Depends(get_store)):
    df = store.df
    m = store.metrics
    selected = m.get("selected_model", "Ridge")
    test_m = m.get("models", {}).get(selected, {}).get("test_metrics", {})
    return GlobalSummaryResponse(
        n_households=int(df["apt"].nunique()),
        n_observations=int(len(df)),
        n_anomalies=int(df["is_anomaly"].sum()),
        anomaly_rate_pct=round(float(df["is_anomaly"].mean() * 100), 2),
        by_method={
            "global_zscore_hi": int(df["flag_zscore_hi"].sum()),
            "iqr_extreme": int(df["flag_iqr_extreme"].sum()),
            "rolling_spike": int(df["flag_rolling_spike"].sum()),
            "residual_z_gt3": int((df["residual_zscore"].fillna(0) > 3).sum()),
        },
        date_start=str(df["timestamp"].min()),
        date_end=str(df["timestamp"].max()),
        model_metrics={
            "selected_model": selected,
            "test_r2": float(test_m.get("r2", 0)),
            "test_rmse": float(test_m.get("rmse", 0)),
            "test_mae": float(test_m.get("mae", 0)),
        },
    )
