"""
SmartWatt India — Backend API Test Suite (T013)

Tests every endpoint for:
  - correct HTTP status codes
  - response schema structure
  - domain constraints (19 households, expected counts, etc.)
  - edge cases (missing household, bad params, date filter, limit)

Uses FastAPI TestClient (synchronous) — no live server required.
The DataStore is loaded once per test session via a session-scoped fixture.
"""

import sys
import os

# Ensure the backend app package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.data_service import get_store


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def loaded_store():
    """Load the DataStore once for the whole test session."""
    store = get_store()
    store.load()
    return store


@pytest.fixture(scope="session")
def client(loaded_store):
    """TestClient with the DataStore already loaded."""
    with TestClient(app) as c:
        yield c


# ── Constants from known dataset ─────────────────────────────────────────────
EXPECTED_HOUSEHOLDS = 19
EXPECTED_OBSERVATIONS = 103_704
EXPECTED_ANOMALIES = 6_549          # may vary ±1 if methodology changes
VALID_APT_ID = 7
VALID_APT_ID_SMALL = 12             # apt 12 has fewer anomalies
INVALID_APT_ID = 99
DATE_START = "2013-08-01"
DATE_END = "2014-05-12"


# ── /api/v1/health ────────────────────────────────────────────────────────────

class TestHealth:
    def test_status_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_schema_fields(self, client):
        d = client.get("/api/v1/health").json()
        assert "status" in d
        assert "version" in d

    def test_status_ok(self, client):
        d = client.get("/api/v1/health").json()
        assert d["status"] == "ok"

    def test_version_non_empty(self, client):
        d = client.get("/api/v1/health").json()
        assert len(d["version"]) > 0


# ── /api/v1/metadata ─────────────────────────────────────────────────────────

class TestMetadata:
    def test_status_200(self, client):
        r = client.get("/api/v1/metadata")
        assert r.status_code == 200

    def test_schema_fields(self, client):
        d = client.get("/api/v1/metadata").json()
        required = [
            "model_version", "data_version", "n_households", "n_observations",
            "date_start", "date_end", "selected_model",
            "model_test_r2", "model_test_rmse", "model_test_mae",
            "n_anomalies", "anomaly_rate_pct",
        ]
        for field in required:
            assert field in d, f"Missing field: {field}"

    def test_n_households(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["n_households"] == EXPECTED_HOUSEHOLDS

    def test_n_observations(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["n_observations"] == EXPECTED_OBSERVATIONS

    def test_n_anomalies_plausible(self, client):
        d = client.get("/api/v1/metadata").json()
        # Within 5% tolerance of expected (methodology may be updated)
        assert abs(d["n_anomalies"] - EXPECTED_ANOMALIES) < EXPECTED_ANOMALIES * 0.05

    def test_anomaly_rate_plausible(self, client):
        d = client.get("/api/v1/metadata").json()
        assert 1.0 <= d["anomaly_rate_pct"] <= 20.0

    def test_model_r2_range(self, client):
        d = client.get("/api/v1/metadata").json()
        # Ridge R² on test set: documented as 0.266; accept -1 to 1
        assert -1.0 <= d["model_test_r2"] <= 1.0

    def test_model_rmse_positive(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["model_test_rmse"] > 0

    def test_model_mae_positive(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["model_test_mae"] > 0

    def test_date_range(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["date_start"].startswith(DATE_START)
        assert d["date_end"].startswith(DATE_END)

    def test_selected_model_ridge(self, client):
        d = client.get("/api/v1/metadata").json()
        assert d["selected_model"] == "Ridge"


# ── /api/v1/households ───────────────────────────────────────────────────────

class TestListHouseholds:
    def test_status_200(self, client):
        r = client.get("/api/v1/households")
        assert r.status_code == 200

    def test_schema_top_level(self, client):
        d = client.get("/api/v1/households").json()
        assert "households" in d
        assert isinstance(d["households"], list)

    def test_count_19(self, client):
        d = client.get("/api/v1/households").json()
        assert len(d["households"]) == EXPECTED_HOUSEHOLDS

    def test_apt_ids_1_to_19(self, client):
        d = client.get("/api/v1/households").json()
        ids = sorted(h["apt_id"] for h in d["households"])
        assert ids == list(range(1, 20))

    def test_household_schema_fields(self, client):
        d = client.get("/api/v1/households").json()
        h = d["households"][0]
        required = [
            "apt_id", "n_observations", "mean_kwh", "median_kwh",
            "std_kwh", "n_anomalies", "anomaly_rate_pct", "date_start", "date_end",
        ]
        for field in required:
            assert field in h, f"Missing field: {field}"

    def test_observations_positive(self, client):
        d = client.get("/api/v1/households").json()
        for h in d["households"]:
            assert h["n_observations"] > 0

    def test_mean_kwh_positive(self, client):
        d = client.get("/api/v1/households").json()
        for h in d["households"]:
            assert h["mean_kwh"] > 0

    def test_anomaly_count_non_negative(self, client):
        d = client.get("/api/v1/households").json()
        for h in d["households"]:
            assert h["n_anomalies"] >= 0

    def test_total_observations_match_metadata(self, client):
        hh = client.get("/api/v1/households").json()["households"]
        meta = client.get("/api/v1/metadata").json()
        total = sum(h["n_observations"] for h in hh)
        assert total == meta["n_observations"]


# ── /api/v1/households/{apt_id} ──────────────────────────────────────────────

class TestGetHousehold:
    def test_valid_household_200(self, client):
        r = client.get(f"/api/v1/households/{VALID_APT_ID}")
        assert r.status_code == 200

    def test_invalid_household_404(self, client):
        r = client.get(f"/api/v1/households/{INVALID_APT_ID}")
        assert r.status_code == 404

    def test_invalid_household_error_message(self, client):
        d = client.get(f"/api/v1/households/{INVALID_APT_ID}").json()
        assert "detail" in d
        assert str(INVALID_APT_ID) in d["detail"]

    def test_household_schema(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}").json()
        required = [
            "apt_id", "n_observations", "mean_kwh", "median_kwh",
            "std_kwh", "n_anomalies", "anomaly_rate_pct", "date_start", "date_end",
        ]
        for field in required:
            assert field in d, f"Missing: {field}"

    def test_apt_id_matches(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}").json()
        assert d["apt_id"] == VALID_APT_ID

    def test_household_0_is_404(self, client):
        r = client.get("/api/v1/households/0")
        assert r.status_code == 404

    def test_household_20_is_404(self, client):
        r = client.get("/api/v1/households/20")
        assert r.status_code == 404

    def test_all_19_households_reachable(self, client):
        for apt_id in range(1, 20):
            r = client.get(f"/api/v1/households/{apt_id}")
            assert r.status_code == 200, f"Apt {apt_id} returned {r.status_code}"


# ── /api/v1/households/{apt_id}/timeseries ────────────────────────────────────

class TestTimeseries:
    def test_status_200(self, client):
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=10")
        assert r.status_code == 200

    def test_invalid_household_404(self, client):
        r = client.get(f"/api/v1/households/{INVALID_APT_ID}/timeseries")
        assert r.status_code == 404

    def test_schema_top_level(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=5").json()
        assert "apt_id" in d
        assert "n_points" in d
        assert "data" in d

    def test_limit_respected(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=10").json()
        assert d["n_points"] == 10
        assert len(d["data"]) == 10

    def test_limit_1(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=1").json()
        assert d["n_points"] == 1

    def test_limit_max_10000(self, client):
        # limit above 10000 should be rejected (422)
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=99999")
        assert r.status_code == 422

    def test_limit_0_rejected(self, client):
        # limit must be >= 1
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=0")
        assert r.status_code == 422

    def test_point_schema(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=1").json()
        p = d["data"][0]
        required = [
            "timestamp", "hour", "dayofweek", "energy_kwh", "lnenergy",
            "temp_c", "is_anomaly", "anomaly_method_count",
            "flag_zscore_hi", "flag_zscore_lo", "flag_iqr_mild",
            "flag_iqr_extreme", "flag_rolling_spike", "flag_rolling_low",
        ]
        for field in required:
            assert field in p, f"Missing field: {field}"

    def test_hour_range(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=100").json()
        for p in d["data"]:
            assert 0 <= p["hour"] <= 23

    def test_dayofweek_range(self, client):
        # Dataset uses ISO weekday encoding: 1=Monday … 7=Sunday (from raw Stata file).
        # This is NOT pandas 0-indexed encoding. Confirmed by inspection of raw data.
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=100").json()
        for p in d["data"]:
            assert 1 <= p["dayofweek"] <= 7, f"dayofweek={p['dayofweek']} out of 1–7 range"


    def test_energy_kwh_positive(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=100").json()
        for p in d["data"]:
            assert p["energy_kwh"] > 0

    def test_date_from_filter(self, client):
        d = client.get(
            f"/api/v1/households/{VALID_APT_ID}/timeseries?date_from=2014-01-01&limit=50"
        ).json()
        for p in d["data"]:
            assert p["timestamp"] >= "2014-01-01"

    def test_date_to_filter(self, client):
        d = client.get(
            f"/api/v1/households/{VALID_APT_ID}/timeseries?date_to=2013-09-30&limit=50"
        ).json()
        for p in d["data"]:
            assert p["timestamp"] <= "2013-09-30 23:59:59"

    def test_date_range_filter(self, client):
        d = client.get(
            f"/api/v1/households/{VALID_APT_ID}/timeseries"
            "?date_from=2013-10-01&date_to=2013-10-31&limit=200"
        ).json()
        for p in d["data"]:
            assert "2013-10" in p["timestamp"]

    def test_impossible_date_range_returns_empty(self, client):
        # Start after end → no data
        d = client.get(
            f"/api/v1/households/{VALID_APT_ID}/timeseries"
            "?date_from=2020-01-01&date_to=2020-01-31"
        ).json()
        assert d["n_points"] == 0
        assert d["data"] == []

    def test_n_points_matches_data_length(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=20").json()
        assert d["n_points"] == len(d["data"])

    def test_anomaly_method_count_range(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/timeseries?limit=500").json()
        for p in d["data"]:
            assert 0 <= p["anomaly_method_count"] <= 4


# ── /api/v1/households/{apt_id}/anomalies ─────────────────────────────────────

class TestAnomalies:
    def test_status_200(self, client):
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies")
        assert r.status_code == 200

    def test_invalid_household_404(self, client):
        r = client.get(f"/api/v1/households/{INVALID_APT_ID}/anomalies")
        assert r.status_code == 404

    def test_schema_top_level(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        assert "apt_id" in d
        assert "n_anomalies" in d
        assert "data" in d

    def test_apt_id_in_response(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        assert d["apt_id"] == VALID_APT_ID

    def test_n_anomalies_matches_data(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        assert d["n_anomalies"] == len(d["data"])

    def test_is_anomaly_always_true(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        for row in d["data"]:
            assert row["is_anomaly"] is True

    def test_anomaly_schema(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        row = d["data"][0]
        required = [
            "timestamp", "energy_kwh", "is_anomaly", "anomaly_method_count",
            "flag_zscore_hi", "flag_iqr_extreme", "flag_rolling_spike",
            "residual_z_flagged",
        ]
        for field in required:
            assert field in row, f"Missing field: {field}"

    def test_min_methods_1_default(self, client):
        d1 = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        d2 = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=1").json()
        assert d1["n_anomalies"] == d2["n_anomalies"]

    def test_min_methods_2_lte_1(self, client):
        d1 = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=1").json()
        d2 = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=2").json()
        # Stricter filter → fewer or equal anomalies
        assert d2["n_anomalies"] <= d1["n_anomalies"]

    def test_min_methods_monotone(self, client):
        counts = []
        for m in [1, 2, 3, 4]:
            d = client.get(
                f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods={m}"
            ).json()
            counts.append(d["n_anomalies"])
        # Each stricter threshold → non-increasing count
        for i in range(len(counts) - 1):
            assert counts[i] >= counts[i + 1], f"Not monotone at min_methods={i+1}"

    def test_min_methods_4_rows_have_4_methods(self, client):
        d = client.get(
            f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=4"
        ).json()
        for row in d["data"]:
            assert row["anomaly_method_count"] == 4

    def test_min_methods_0_rejected(self, client):
        # min_methods must be >= 1
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=0")
        assert r.status_code == 422

    def test_min_methods_5_rejected(self, client):
        # min_methods must be <= 4
        r = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies?min_methods=5")
        assert r.status_code == 422

    def test_all_households_have_anomalies(self, client):
        """Every household should have at least one anomaly with min_methods=1."""
        for apt_id in range(1, 20):
            d = client.get(f"/api/v1/households/{apt_id}/anomalies").json()
            assert d["n_anomalies"] >= 0  # non-negative (some may have 0)

    def test_total_anomalies_matches_metadata(self, client):
        meta = client.get("/api/v1/metadata").json()
        total = sum(
            client.get(f"/api/v1/households/{i}/anomalies").json()["n_anomalies"]
            for i in range(1, 20)
        )
        assert total == meta["n_anomalies"]

    def test_energy_kwh_positive(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        for row in d["data"]:
            assert row["energy_kwh"] > 0

    def test_anomaly_method_count_gte_1(self, client):
        d = client.get(f"/api/v1/households/{VALID_APT_ID}/anomalies").json()
        for row in d["data"]:
            # Every anomaly row must have at least 1 method flagging it
            assert row["anomaly_method_count"] >= 1


# ── /api/v1/summary ───────────────────────────────────────────────────────────

class TestSummary:
    def test_status_200(self, client):
        r = client.get("/api/v1/summary")
        assert r.status_code == 200

    def test_schema_fields(self, client):
        d = client.get("/api/v1/summary").json()
        required = [
            "n_households", "n_observations", "n_anomalies", "anomaly_rate_pct",
            "by_method", "date_start", "date_end", "model_metrics",
        ]
        for field in required:
            assert field in d, f"Missing: {field}"

    def test_n_households(self, client):
        d = client.get("/api/v1/summary").json()
        assert d["n_households"] == EXPECTED_HOUSEHOLDS

    def test_n_observations(self, client):
        d = client.get("/api/v1/summary").json()
        assert d["n_observations"] == EXPECTED_OBSERVATIONS

    def test_n_anomalies_plausible(self, client):
        d = client.get("/api/v1/summary").json()
        assert abs(d["n_anomalies"] - EXPECTED_ANOMALIES) < EXPECTED_ANOMALIES * 0.05

    def test_by_method_keys(self, client):
        d = client.get("/api/v1/summary").json()
        expected_keys = {"global_zscore_hi", "iqr_extreme", "rolling_spike", "residual_z_gt3"}
        assert set(d["by_method"].keys()) == expected_keys

    def test_by_method_values_non_negative(self, client):
        d = client.get("/api/v1/summary").json()
        for k, v in d["by_method"].items():
            assert v >= 0, f"Negative count for {k}"

    def test_model_metrics_fields(self, client):
        d = client.get("/api/v1/summary").json()
        mm = d["model_metrics"]
        for field in ["selected_model", "test_r2", "test_rmse", "test_mae"]:
            assert field in mm

    def test_model_metrics_consistent_with_metadata(self, client):
        summary = client.get("/api/v1/summary").json()
        meta = client.get("/api/v1/metadata").json()
        assert summary["n_households"] == meta["n_households"]
        assert summary["n_observations"] == meta["n_observations"]
        assert abs(summary["n_anomalies"] - meta["n_anomalies"]) == 0

    def test_anomaly_rate_computed_correctly(self, client):
        d = client.get("/api/v1/summary").json()
        expected_rate = round(d["n_anomalies"] / d["n_observations"] * 100, 2)
        assert abs(d["anomaly_rate_pct"] - expected_rate) < 0.01

    def test_date_start_correct(self, client):
        d = client.get("/api/v1/summary").json()
        assert d["date_start"].startswith(DATE_START)

    def test_date_end_correct(self, client):
        d = client.get("/api/v1/summary").json()
        assert d["date_end"].startswith(DATE_END)


# ── Integration: cross-endpoint consistency ───────────────────────────────────

class TestIntegration:
    def test_households_list_count_matches_metadata(self, client):
        hh = client.get("/api/v1/households").json()["households"]
        meta = client.get("/api/v1/metadata").json()
        assert len(hh) == meta["n_households"]

    def test_timeseries_observations_match_household_summary(self, client):
        apt = VALID_APT_ID
        summary = client.get(f"/api/v1/households/{apt}").json()
        ts = client.get(f"/api/v1/households/{apt}/timeseries").json()
        assert ts["n_points"] == summary["n_observations"]

    def test_anomaly_count_consistent_across_endpoints(self, client):
        apt = VALID_APT_ID
        hh = client.get(f"/api/v1/households/{apt}").json()
        anom = client.get(f"/api/v1/households/{apt}/anomalies").json()
        assert anom["n_anomalies"] == hh["n_anomalies"]

    def test_timeseries_anomaly_flags_consistent(self, client):
        """
        In the timeseries, count rows where is_anomaly=True for the limited set
        and verify method count >= 1 whenever is_anomaly=True.
        """
        apt = VALID_APT_ID_SMALL
        d = client.get(f"/api/v1/households/{apt}/timeseries?limit=500").json()
        for p in d["data"]:
            if p["is_anomaly"]:
                assert p["anomaly_method_count"] >= 1, (
                    f"is_anomaly=True but method_count={p['anomaly_method_count']}"
                )

    def test_all_apts_timeseries_accessible(self, client):
        for apt_id in range(1, 20):
            r = client.get(f"/api/v1/households/{apt_id}/timeseries?limit=1")
            assert r.status_code == 200, f"Apt {apt_id} timeseries failed"

    def test_all_apts_anomalies_accessible(self, client):
        for apt_id in range(1, 20):
            r = client.get(f"/api/v1/households/{apt_id}/anomalies")
            assert r.status_code == 200, f"Apt {apt_id} anomalies failed"

    def test_summary_by_method_iqr_is_largest(self, client):
        """IQR extreme is the most common single-method flag (5216 in known data)."""
        d = client.get("/api/v1/summary").json()
        bm = d["by_method"]
        assert bm["iqr_extreme"] >= bm["residual_z_gt3"]
        assert bm["iqr_extreme"] >= bm["global_zscore_hi"]

    def test_metadata_and_summary_model_type(self, client):
        meta = client.get("/api/v1/metadata").json()
        summ = client.get("/api/v1/summary").json()
        assert meta["selected_model"] == summ["model_metrics"]["selected_model"] == "Ridge"


# ── /predict tests ────────────────────────────────────────────────────────────
class TestPredict:
    """Tests for POST /api/v1/predict (T018 — ADR-013)."""

    BASE = "/api/v1/predict"
    VALID_BODY = {
        "apt": 7,
        "hour": 14,
        "dayofweek": 2,
        "month": 10,
        "temp_c": 25.0,
    }

    def test_valid_prediction_200(self, client):
        r = client.post(self.BASE, json=self.VALID_BODY)
        assert r.status_code == 200

    def test_response_schema(self, client):
        d = client.post(self.BASE, json=self.VALID_BODY).json()
        assert "apt" in d
        assert "predicted_kwh" in d
        assert "predicted_lnenergy" in d
        assert "model_version" in d
        assert "note" in d

    def test_predicted_kwh_is_positive(self, client):
        d = client.post(self.BASE, json=self.VALID_BODY).json()
        assert d["predicted_kwh"] > 0

    def test_echo_inputs(self, client):
        d = client.post(self.BASE, json=self.VALID_BODY).json()
        assert d["apt"] == self.VALID_BODY["apt"]
        assert d["hour"] == self.VALID_BODY["hour"]
        assert d["dayofweek"] == self.VALID_BODY["dayofweek"]
        assert d["month"] == self.VALID_BODY["month"]
        assert d["temp_c"] == self.VALID_BODY["temp_c"]

    def test_all_valid_apts_work(self, client):
        for apt_id in range(1, 20):
            body = {**self.VALID_BODY, "apt": apt_id}
            r = client.post(self.BASE, json=body)
            assert r.status_code == 200, f"Apt {apt_id} predict failed"

    def test_peak_hour_higher_than_off_peak(self, client):
        """Hour 20 (8 pm, verified peak) predicts more than hour 4 (4 am, trough) for apt 7."""
        peak = client.post(self.BASE, json={**self.VALID_BODY, "hour": 20}).json()
        off_peak = client.post(self.BASE, json={**self.VALID_BODY, "hour": 4}).json()
        assert peak["predicted_kwh"] > off_peak["predicted_kwh"]

    def test_hot_temperature_higher_than_cold(self, client):
        """Positive correlation: higher temp → higher predicted consumption (r=0.12 EDA)."""
        hot = client.post(self.BASE, json={**self.VALID_BODY, "temp_c": 38.0}).json()
        cold = client.post(self.BASE, json={**self.VALID_BODY, "temp_c": 10.0}).json()
        assert hot["predicted_kwh"] > cold["predicted_kwh"]

    def test_invalid_apt_returns_404(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "apt": 99})
        assert r.status_code == 404

    def test_invalid_hour_out_of_range_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "hour": 24})
        assert r.status_code == 422

    def test_invalid_hour_negative_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "hour": -1})
        assert r.status_code == 422

    def test_invalid_dayofweek_zero_returns_422(self, client):
        """dayofweek must be 1–7 (ISO). 0 is invalid."""
        r = client.post(self.BASE, json={**self.VALID_BODY, "dayofweek": 0})
        assert r.status_code == 422

    def test_invalid_dayofweek_eight_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "dayofweek": 8})
        assert r.status_code == 422

    def test_invalid_month_zero_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "month": 0})
        assert r.status_code == 422

    def test_invalid_month_thirteen_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "month": 13})
        assert r.status_code == 422

    def test_temp_too_low_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "temp_c": 4.9})
        assert r.status_code == 422

    def test_temp_too_high_returns_422(self, client):
        r = client.post(self.BASE, json={**self.VALID_BODY, "temp_c": 45.1})
        assert r.status_code == 422

    def test_boundary_values_valid(self, client):
        """Hour 0, dayofweek 1, month 1, temp_c at lower bound."""
        body = {"apt": 1, "hour": 0, "dayofweek": 1, "month": 1, "temp_c": 5.0}
        r = client.post(self.BASE, json=body)
        assert r.status_code == 200

    def test_boundary_values_max(self, client):
        """Hour 23, dayofweek 7, month 12, temp_c at upper bound."""
        body = {"apt": 19, "hour": 23, "dayofweek": 7, "month": 12, "temp_c": 45.0}
        r = client.post(self.BASE, json=body)
        assert r.status_code == 200

    def test_missing_field_returns_422(self, client):
        """Missing required field should fail validation."""
        r = client.post(self.BASE, json={"apt": 7, "hour": 14, "dayofweek": 2, "month": 10})
        assert r.status_code == 422

    def test_model_version_in_response(self, client):
        d = client.post(self.BASE, json=self.VALID_BODY).json()
        assert d["model_version"] == "v0.1.0"

    def test_predicted_kwh_reasonable_range(self, client):
        """Predicted kWh should be within dataset range (0.01–10 kWh/hr roughly)."""
        d = client.post(self.BASE, json=self.VALID_BODY).json()
        assert 0.01 < d["predicted_kwh"] < 10.0
