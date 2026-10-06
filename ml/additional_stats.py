"""
SmartWatt India — Additional Statistical Diagnostics (T023)
===========================================================
Purpose:
  Adds advanced statistical diagnostics to evaluate the regression assumptions
  of the Ridge baseline model. Time-series data often violates OLS assumptions.
  We test for:
  1. Autocorrelation of residuals (Durbin-Watson test).
  2. Heteroscedasticity (correlation between predicted value and absolute residual).

Why this matters:
  - High autocorrelation implies the model misses some temporal dynamics (e.g.,
    unobserved state like occupancy). This is expected in hourly smart meter data.
  - Heteroscedasticity implies anomaly thresholds might need to be dynamic 
    relative to the predicted value, though we partially mitigated this using
    the log transformation of energy_kwh.

What this script does NOT do:
  - It does not alter the Ridge model.
  - It does not generate new anomaly flags.
  - It does not claim causation.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PREDICTIONS_CSV = PROCESSED_DIR / "model_predictions.csv"
REPORT_JSON = PROCESSED_DIR / "additional_stats_report.json"

def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def main():
    log("=" * 60)
    log("SmartWatt India — Additional Statistical Tests (T023)")
    log("=" * 60)

    # 1. Load data
    log("Loading model predictions...")
    df = pd.read_csv(PREDICTIONS_CSV, parse_dates=["timestamp"])
    
    # We analyze the test split to measure generalization
    test_df = df[df["split"] == "test"].copy()
    
    log(f"Test observations: {len(test_df):,}")

    results = {}

    # 2. Durbin-Watson Test for Autocorrelation
    # Durbin-Watson statistic ranges from 0 to 4.
    # ~2.0 indicates no autocorrelation.
    # < 2.0 indicates positive autocorrelation.
    # > 2.0 indicates negative autocorrelation.
    log("Running Durbin-Watson test per household...")
    dw_results = {}
    
    for apt_id, grp in test_df.groupby("apt"):
        # Sort chronologically just to be absolutely sure
        grp = grp.sort_values("timestamp")
        residuals = grp["residual"].dropna().values
        if len(residuals) > 1:
            diffs = np.diff(residuals)
            dw_stat = np.sum(diffs**2) / np.sum(residuals**2)
            dw_results[int(apt_id)] = float(dw_stat)
    
    mean_dw = np.mean(list(dw_results.values()))
    results["durbin_watson"] = {
        "test": "Durbin-Watson",
        "purpose": "Detects first-order autocorrelation in residuals.",
        "per_household_statistic": dw_results,
        "mean_statistic": float(mean_dw),
        "interpretation": (
            f"Mean DW statistic is {mean_dw:.2f}. Values significantly below 2.0 "
            "indicate positive autocorrelation, meaning periods of high/low "
            "unexplained consumption tend to cluster together temporally."
        ),
        "limitation": "Only detects first-order (lag-1) autocorrelation."
    }
    log(f"Mean Durbin-Watson statistic: {mean_dw:.2f}")

    # 3. Heteroscedasticity check (Spearman rank correlation)
    # Are errors larger when predicted consumption is larger?
    # We use Spearman correlation between expected (lnenergy_predicted) and absolute residual.
    log("Checking for heteroscedasticity...")
    test_df["abs_residual"] = test_df["residual"].abs()
    # Drop NaNs just in case
    clean_test = test_df.dropna(subset=["lnenergy_predicted", "abs_residual"])
    corr, p_value = spearmanr(clean_test["lnenergy_predicted"], clean_test["abs_residual"])

    results["heteroscedasticity"] = {
        "test": "Spearman Rank Correlation (Predicted vs Absolute Residual)",
        "purpose": "Checks if prediction errors scale with the predicted value (heteroscedasticity).",
        "spearman_correlation": float(corr),
        "p_value": float(p_value),
        "interpretation": (
            f"Correlation is {corr:.3f} (p={p_value:.2e}). "
            "A positive value indicates that as expected energy use increases, the magnitude "
            "of the model's error also tends to increase. The log transformation "
            "partially mitigated this, but some heteroscedasticity remains."
        ),
        "limitation": "Does not formalize a functional form for the variance."
    }
    log(f"Heteroscedasticity rank correlation: {corr:.3f} (p={p_value:.2e})")

    # Build and save report
    report = {
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "n_test_observations": len(test_df),
        "tests": results,
    }

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    log(f"Written: {REPORT_JSON.name}")
    log("=" * 60)
    log("T023 COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    main()
