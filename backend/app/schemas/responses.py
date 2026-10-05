"""
SmartWatt India — Pydantic response schemas
All API responses are typed here.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Health ────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


# ── Metadata ──────────────────────────────────────────────────────────────────
class MetadataResponse(BaseModel):
    model_version: str
    data_version: str
    n_households: int
    n_observations: int
    date_start: str
    date_end: str
    selected_model: str
    model_test_r2: float
    model_test_rmse: float
    model_test_mae: float
    n_anomalies: int
    anomaly_rate_pct: float


# ── Household list ─────────────────────────────────────────────────────────────
class HouseholdSummary(BaseModel):
    apt_id: int
    n_observations: int
    mean_kwh: float
    median_kwh: float
    std_kwh: float
    n_anomalies: int
    anomaly_rate_pct: float
    date_start: str
    date_end: str


class HouseholdsResponse(BaseModel):
    households: list[HouseholdSummary]


# ── Timeseries ────────────────────────────────────────────────────────────────
class TimeseriesPoint(BaseModel):
    timestamp: str
    hour: int
    dayofweek: int
    energy_kwh: float
    lnenergy: float
    temp_c: float
    lnenergy_predicted: Optional[float] = None
    energy_kwh_predicted: Optional[float] = None
    residual: Optional[float] = None
    residual_zscore: Optional[float] = None
    feat_zscore_global: Optional[float] = None
    feat_rolling_mean_7d: Optional[float] = None
    feat_rolling_zscore: Optional[float] = None
    is_anomaly: bool
    anomaly_method_count: int
    flag_zscore_hi: bool
    flag_zscore_lo: bool
    flag_iqr_mild: bool
    flag_iqr_extreme: bool
    flag_rolling_spike: bool
    flag_rolling_low: bool
    split: Optional[str] = None


class TimeseriesResponse(BaseModel):
    apt_id: int
    n_points: int
    data: list[TimeseriesPoint]


# ── Anomalies ─────────────────────────────────────────────────────────────────
class AnomalyPoint(BaseModel):
    timestamp: str
    energy_kwh: float
    lnenergy_predicted: Optional[float] = None
    residual_zscore: Optional[float] = None
    feat_zscore_global: Optional[float] = None
    feat_rolling_zscore: Optional[float] = None
    is_anomaly: bool
    anomaly_method_count: int
    flag_zscore_hi: bool
    flag_iqr_extreme: bool
    flag_rolling_spike: bool
    residual_z_flagged: bool


class AnomaliesResponse(BaseModel):
    apt_id: int
    n_anomalies: int
    data: list[AnomalyPoint]


# ── Summary ────────────────────────────────────────────────────────────────────
class GlobalSummaryResponse(BaseModel):
    n_households: int
    n_observations: int
    n_anomalies: int
    anomaly_rate_pct: float
    by_method: dict[str, int]
    date_start: str
    date_end: str
    model_metrics: dict[str, Any]
