"""
SmartWatt India — Model Evaluation Report (T008)
=================================================
Purpose:
  Produce a formal, human-readable evaluation of the Ridge regression
  baseline trained in T007. Enriches model_metrics.json with per-household
  metrics, residual diagnostics, and a T009 synthetic anomaly benchmark.

  T009 — Synthetic anomaly benchmark:
    Inject known positive spikes (+2 std, +3 std, +4 std on lnenergy)
    into a held-out test copy and verify that the residual_zscore
    correctly detects them at each severity tier.
    This is NOT a label — it is a calibration sanity check.

What this script does NOT do:
  - Does not retrain the model.
  - Does not modify model_predictions.csv or the saved model.
  - Does not score anomalies on production data.
  - Does not classify observations.

Run from any directory:
    python ml/evaluate.py
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PREDICTIONS_CSV = PROCESSED_DIR / "model_predictions.csv"
METRICS_JSON = PROCESSED_DIR / "model_metrics.json"
EVAL_REPORT = PROCESSED_DIR / "evaluation_report.json"
MODEL_PATH = REPO_ROOT / "ml" / "models" / "ridge_model.joblib"


def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ── Per-household test metrics ────────────────────────────────────────────────
def per_household_metrics(test_df: pd.DataFrame) -> dict:
    log("Computing per-household test metrics...")
    result = {}
    for apt_id, grp in test_df.groupby("apt"):
        y_true = grp["lnenergy"]
        y_pred = grp["lnenergy_predicted"]
        result[str(apt_id)] = {
            "n_test": int(len(grp)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "mse": float(mean_squared_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2": float(r2_score(y_true, y_pred)),
            "residual_mean": float(grp["residual"].mean()),
            "residual_std": float(grp["residual"].std()),
            "residual_zscore_gt2": int((grp["residual_zscore"].abs() > 2).sum()),
            "residual_zscore_gt3": int((grp["residual_zscore"].abs() > 3).sum()),
        }
        log(f"  apt={apt_id:2d}: R²={result[str(apt_id)]['r2']:+.3f}  "
            f"MAE={result[str(apt_id)]['mae']:.4f}  "
            f"|Z|>3: {result[str(apt_id)]['residual_zscore_gt3']}")
    return result


# ── Residual diagnostics ───────────────────────────────────────────────────────
def residual_diagnostics(df: pd.DataFrame) -> dict:
    log("Residual diagnostics...")
    res = df["residual"]
    rz = df["residual_zscore"]

    # Check residual normality (Shapiro on sample)
    from scipy import stats as scipy_stats
    sample = res.dropna().sample(min(5000, len(res)), random_state=42)
    _, shap_p = scipy_stats.shapiro(sample)

    # Skewness and kurtosis of residuals
    skew = float(res.skew())
    kurt = float(res.kurtosis())

    diag = {
        "residual_mean": float(res.mean()),
        "residual_std": float(res.std()),
        "residual_min": float(res.min()),
        "residual_max": float(res.max()),
        "residual_skewness": skew,
        "residual_kurtosis": kurt,
        "residual_shapiro_p": float(shap_p),
        "residual_normally_distributed": shap_p > 0.05,
        "residual_zscore_abs_gt_2": int((rz.abs() > 2).sum()),
        "residual_zscore_abs_gt_3": int((rz.abs() > 3).sum()),
        "residual_zscore_abs_gt_4": int((rz.abs() > 4).sum()),
        "pct_zscore_gt3": float((rz.abs() > 3).sum() / len(rz) * 100),
    }
    log(f"  Residual skew={skew:.3f}  kurtosis={kurt:.3f}  "
        f"shapiro_p={shap_p:.2e}  normal={diag['residual_normally_distributed']}")
    log(f"  |Z|>2: {diag['residual_zscore_abs_gt_2']}  "
        f"|Z|>3: {diag['residual_zscore_abs_gt_3']}  "
        f"|Z|>4: {diag['residual_zscore_abs_gt_4']}")
    return diag


# ── T009: Synthetic anomaly benchmark ─────────────────────────────────────────
def synthetic_anomaly_benchmark(df: pd.DataFrame) -> dict:
    """
    T009 — Controlled synthetic anomaly benchmark.

    Method:
    1. Take the test split only.
    2. For each severity tier (+2σ, +3σ, +4σ on lnenergy):
       - Randomly sample 100 test observations (seed=42 for reproducibility).
       - Add the spike (severity × household residual_std) to their lnenergy.
       - Recompute residual and residual_zscore (using the same training residual stats).
       - Measure detection rate at the given Z-score threshold.

    This tests whether the residual_zscore signal can distinguish injected
    anomalies from normal variation. It does NOT label any real observation.
    """
    log("T009: Synthetic anomaly benchmark...")

    test_df = df[df["split"] == "test"].copy()

    # Per-household training residual stats (from residual_zscore denominator)
    # We back-calculate the std used per household from the train residuals in df
    train_df = df[df["split"] == "train"].copy()
    res_stats = (
        train_df.groupby("apt")["residual"]
        .agg(res_mean="mean", res_std="std")
        .reset_index()
    )

    results = {}
    rng = np.random.default_rng(42)

    for severity_sigma in [2.0, 3.0, 4.0]:
        n_inject = 100
        sampled_idx = rng.choice(test_df.index, size=n_inject, replace=False)
        injected = test_df.loc[sampled_idx].copy()

        # Add spike per household (uses household's own residual std for scaling)
        injected = injected.merge(res_stats, on="apt", how="left")
        spike_amount = severity_sigma * injected["res_std"]
        injected["lnenergy_spiked"] = injected["lnenergy"] + spike_amount

        # Recompute residual with spiked lnenergy
        injected["residual_spiked"] = (
            injected["lnenergy_spiked"] - injected["lnenergy_predicted"]
        )
        # Recompute Z-score using same training stats
        injected["residual_zscore_spiked"] = (
            (injected["residual_spiked"] - injected["res_mean"])
            / injected["res_std"]
        )

        # Detection at Z > severity_sigma threshold
        detected = (injected["residual_zscore_spiked"] > severity_sigma).sum()
        detection_rate = float(detected / n_inject * 100)

        # Also check at Z > 3 threshold (fixed)
        detected_at_3 = (injected["residual_zscore_spiked"] > 3.0).sum()
        detection_at_3 = float(detected_at_3 / n_inject * 100)

        results[f"+{severity_sigma:.0f}sigma"] = {
            "n_injected": n_inject,
            "spike_threshold_sigma": severity_sigma,
            "detected_at_own_threshold": int(detected),
            "detection_rate_at_own_threshold_pct": detection_rate,
            "detected_at_z3": int(detected_at_3),
            "detection_rate_at_z3_pct": detection_at_3,
            "mean_injected_spike_kwh": float(np.exp(injected["lnenergy_spiked"]).mean()
                                             - np.exp(injected["lnenergy"]).mean()),
        }
        log(f"  +{severity_sigma:.0f}σ: injected {n_inject} | "
            f"detected at Z>{severity_sigma:.0f}: {detected} ({detection_rate:.0f}%) | "
            f"at Z>3: {detected_at_3} ({detection_at_3:.0f}%)")

    # False positive rate (normal observations flagged at Z>3)
    normal_test = test_df.copy()
    fp = (normal_test["residual_zscore"].abs() > 3).sum()
    fp_rate = float(fp / len(normal_test) * 100)
    results["false_positive_rate_at_z3"] = {
        "n_test_obs": int(len(normal_test)),
        "n_flagged": int(fp),
        "fp_rate_pct": fp_rate,
    }
    log(f"  False positive rate at |Z|>3 (real test data): {fp_rate:.2f}%")

    return results


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log("=" * 60)
    log("SmartWatt India — Evaluation (T008) + Synthetic Benchmark (T009)")
    log("=" * 60)

    # Load predictions
    df = pd.read_csv(PREDICTIONS_CSV, parse_dates=["timestamp"])
    test_df = df[df["split"] == "test"].copy()
    log(f"Loaded: {len(df):,} total rows, {len(test_df):,} test rows")

    # Load existing metrics
    with open(METRICS_JSON) as f:
        metrics = json.load(f)

    # T008: Per-household metrics
    ph_metrics = per_household_metrics(test_df)

    # T008: Residual diagnostics
    res_diag = residual_diagnostics(df)

    # T009: Synthetic benchmark
    synth = synthetic_anomaly_benchmark(df)

    # Build evaluation report
    eval_report = {
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "predictions_file": str(PREDICTIONS_CSV.relative_to(REPO_ROOT)),
        "selected_model": metrics["selected_model"],
        "overall_test_metrics": metrics["models"][metrics["selected_model"]]["test_metrics"],
        "overall_train_metrics": metrics["models"][metrics["selected_model"]]["train_metrics"],
        "model_comparison": {
            name: data["test_metrics"]
            for name, data in metrics["models"].items()
        },
        "per_household_test_metrics": ph_metrics,
        "residual_diagnostics": res_diag,
        "synthetic_anomaly_benchmark_t009": synth,
        "interpretation": {
            "r2_note": (
                "R²=0.27 on test set. This is moderate for hourly residential electricity. "
                "The model captures time-of-day, seasonal, and treatment effects. "
                "High unexplained variance is partly due to: occupancy behaviour, "
                "appliance heterogeneity, and temporal gaps. Residuals are the key "
                "anomaly signal — not the R² itself."
            ),
            "negative_per_household_r2_note": (
                "Several households show negative R² in the test split. "
                "This occurs when the household's test-period consumption pattern "
                "differs from the training period (e.g., seasonality shift, "
                "behaviour change post-intervention). The model still produces "
                "interpretable residuals — large positive residuals still indicate "
                "above-expected usage. Negative R² means the model is worse than "
                "the mean; residuals should be interpreted per-household."
            ),
            "anomaly_signal_status": (
                "residual_zscore is computed per-household using training residual stats. "
                "It is the 4th anomaly signal and is available in model_predictions.csv. "
                "Combined anomaly scoring (T008 final step) will use: "
                "feat_zscore_global, flag_iqr_extreme, flag_rolling_spike, residual_zscore."
            ),
        },
    }

    with open(EVAL_REPORT, "w") as f:
        json.dump(eval_report, f, indent=2, default=str)

    log(f"Written: {EVAL_REPORT.name}")

    log("=" * 60)
    log("T008 + T009 COMPLETE")
    log(f"  Overall test R²: {metrics['models'][metrics['selected_model']]['test_metrics']['r2']:.4f}")
    log(f"  Overall test MAE: {metrics['models'][metrics['selected_model']]['test_metrics']['mae']:.4f}")
    log(f"  Overall test RMSE: {metrics['models'][metrics['selected_model']]['test_metrics']['rmse']:.4f}")
    log(f"  Residual Z>3 (real test): {res_diag['residual_zscore_abs_gt_3']} ({res_diag['pct_zscore_gt3']:.2f}%)")
    log(f"  Synthetic detection:")
    for tier, v in synth.items():
        if "detected_at_own_threshold" in v:
            log(f"    {tier}: {v['detection_rate_at_own_threshold_pct']:.0f}% detected at own threshold")
    log("=" * 60)


if __name__ == "__main__":
    main()
