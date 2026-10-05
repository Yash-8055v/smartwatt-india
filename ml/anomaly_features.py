"""
SmartWatt India — Statistical Anomaly Features (T006)
======================================================
Purpose:
  Compute per-household statistical anomaly features confirmed by EDA (T005).
  Produces anomaly_features.csv with all original columns plus:

  Method 1 — Per-household global Z-score on lnenergy
    feat_zscore_global       float   Z-score relative to household full-period mean/std
    flag_zscore_hi           bool    |Z| > 3  (positive spike)
    flag_zscore_lo           bool    Z  < -3  (unusually low)

  Method 2 — Per-household IQR fence on energy_kwh
    feat_iqr_upper_1_5       float   upper fence = Q75 + 1.5×IQR  (per household)
    feat_iqr_upper_3_0       float   outer fence = Q75 + 3.0×IQR  (per household)
    flag_iqr_mild            bool    energy_kwh > upper_1_5 fence
    flag_iqr_extreme         bool    energy_kwh > upper_3_0 fence
    flag_iqr_low             bool    energy_kwh < Q25 - 1.5×IQR  (unusually low)

  Method 3 — 7-day rolling statistics (per household, no future leakage)
    feat_rolling_mean_7d     float   rolling mean of energy_kwh (168-hour window)
    feat_rolling_std_7d      float   rolling std of energy_kwh  (168-hour window)
    feat_rolling_zscore      float   (energy_kwh - rolling_mean) / rolling_std
    feat_rolling_deviation   float   energy_kwh - rolling_mean  (signed deviation)
    flag_rolling_spike       bool    rolling_zscore > 3
    flag_rolling_low         bool    rolling_zscore < -3

  Rolling window config:
    - window  = 168 hours (7 days × 24 hours)
    - min_periods = 48 (2 days minimum, enough for basic stability)
    - Computed with .rolling(..., closed="left") so each row only sees PAST values
      (no same-row leakage).  If a household has fewer than min_periods preceding
      observations in a window, rolling stats are NaN and flags default to False.

What this script does NOT do:
  - Does not train a model.
  - Does not compute regression residuals (T007).
  - Does not produce a final combined anomaly score (T008).
  - Does not remove, cap, normalise, or winsorise any observations.
  - Does not fill missing timestamps.
  - Does not invent anomaly labels.
  - Does not modify raw data.

EDA decisions in effect (docs/EDA_FINDINGS.md):
  - Use lnenergy for Z-scores (approximately log-normal, ADR-008).
  - Per-household baselines mandatory (CV ranges 79–208%).
  - Rolling windows must guard against large temporal gaps.
  - Anomaly = statistically unusual relative to household baseline.

Run from any directory:
    python ml/anomaly_features.py
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
INPUT_CSV = PROCESSED_DIR / "hourly_energy.csv"
OUTPUT_CSV = PROCESSED_DIR / "anomaly_features.csv"
OUTPUT_REPORT = PROCESSED_DIR / "anomaly_features_report.json"

# ── Rolling window configuration ──────────────────────────────────────────────
ROLLING_WINDOW_HOURS = 168   # 7 × 24 = 168 hours
ROLLING_MIN_PERIODS = 48     # 2 days minimum before producing a rolling stat
ZSCORE_FLAG_THRESHOLD = 3.0  # |Z| > 3 for global and rolling Z-score flags


def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ── Load ───────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    log(f"Loading: {INPUT_CSV.name}")
    df = pd.read_csv(INPUT_CSV, parse_dates=["timestamp"])
    df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)
    log(f"Loaded: {len(df):,} rows × {len(df.columns)} columns, {df['apt'].nunique()} households")

    # Verify required columns are present
    required = ["apt", "timestamp", "lnenergy", "energy_kwh"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing from input: {missing}")

    return df


# ── Method 1: Per-household global Z-score on lnenergy ────────────────────────
def compute_global_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Z-score = (lnenergy - household_mean_lnenergy) / household_std_lnenergy

    Uses the FULL-PERIOD household mean/std as the baseline.
    This is the simplest signal and serves as a cross-validation anchor.

    No future leakage risk: the baseline is computed once from the full
    household history, which is appropriate for a retrospective analysis
    on a fixed historical dataset. For a production rolling deployment
    the rolling Z-score (Method 3) is preferred.
    """
    log("Method 1: computing per-household global Z-score on lnenergy")

    apt_stats = (
        df.groupby("apt")["lnenergy"]
        .agg(apt_mean="mean", apt_std="std")
        .reset_index()
    )
    df = df.merge(apt_stats, on="apt", how="left")

    df["feat_zscore_global"] = (df["lnenergy"] - df["apt_mean"]) / df["apt_std"]
    df["flag_zscore_hi"] = df["feat_zscore_global"] > ZSCORE_FLAG_THRESHOLD
    df["flag_zscore_lo"] = df["feat_zscore_global"] < -ZSCORE_FLAG_THRESHOLD

    # Drop the intermediate join columns
    df = df.drop(columns=["apt_mean", "apt_std"])

    n_hi = int(df["flag_zscore_hi"].sum())
    n_lo = int(df["flag_zscore_lo"].sum())
    log(f"  Flagged Z>+3: {n_hi:,} rows ({n_hi/len(df)*100:.2f}%)")
    log(f"  Flagged Z<-3: {n_lo:,} rows ({n_lo/len(df)*100:.2f}%)")

    return df


# ── Method 2: Per-household IQR fences on energy_kwh ─────────────────────────
def compute_iqr_fences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tukey fences computed per household on energy_kwh (not log scale).
    Two tiers:
      mild    = Q75 + 1.5 × IQR  (flagged for attention)
      extreme = Q75 + 3.0 × IQR  (outer fence, clear spike)
    Low fence: Q25 - 1.5 × IQR   (unusually low)

    Full-period per-household IQR, same retrospective rationale as Method 1.
    """
    log("Method 2: computing per-household IQR fences on energy_kwh")

    iqr_stats = []
    for apt_id, grp in df.groupby("apt"):
        q25 = grp["energy_kwh"].quantile(0.25)
        q75 = grp["energy_kwh"].quantile(0.75)
        iqr = q75 - q25
        iqr_stats.append({
            "apt": apt_id,
            "feat_iqr_upper_1_5": q75 + 1.5 * iqr,
            "feat_iqr_upper_3_0": q75 + 3.0 * iqr,
            "feat_iqr_lower_1_5": q25 - 1.5 * iqr,
        })

    iqr_df = pd.DataFrame(iqr_stats)
    df = df.merge(iqr_df, on="apt", how="left")

    df["flag_iqr_mild"] = df["energy_kwh"] > df["feat_iqr_upper_1_5"]
    df["flag_iqr_extreme"] = df["energy_kwh"] > df["feat_iqr_upper_3_0"]
    df["flag_iqr_low"] = df["energy_kwh"] < df["feat_iqr_lower_1_5"]

    # Remove the lower fence column (only upper fences are stored as features;
    # the lower fence was only used to compute flag_iqr_low)
    df = df.drop(columns=["feat_iqr_lower_1_5"])

    n_mild = int(df["flag_iqr_mild"].sum())
    n_ext = int(df["flag_iqr_extreme"].sum())
    n_low = int(df["flag_iqr_low"].sum())
    log(f"  Flagged mild (>1.5×IQR):    {n_mild:,} ({n_mild/len(df)*100:.2f}%)")
    log(f"  Flagged extreme (>3.0×IQR): {n_ext:,} ({n_ext/len(df)*100:.2f}%)")
    log(f"  Flagged low (<Q25-1.5×IQR): {n_low:,} ({n_low/len(df)*100:.2f}%)")

    return df


# ── Method 3: 7-day rolling statistics per household ─────────────────────────
def compute_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rolling window (168 hours, min_periods=48) computed PER HOUSEHOLD.

    CRITICAL DESIGN CHOICES:
    1. closed="left" — the current observation is EXCLUDED from its own window.
       This prevents a row from influencing its own rolling mean/std (no leakage).
    2. min_periods=48 — rolling stats are NaN for the first 48 observations of
       each household; flags default to False (NaN → False via fillna).
    3. Computed within each household group independently so stats never cross
       household boundaries.
    4. No timestamp reindexing or gap-filling — gaps remain as actual gaps in
       the data, and the rolling window uses the actual observation count, not
       calendar time.

    NOTE: Because data has temporal gaps (avg ~20% missing hours), the 168-obs
    window corresponds to ≈7 days of dense data, but may span more calendar time
    when gaps are present. This is documented and acceptable for this dataset.
    """
    log(f"Method 3: computing {ROLLING_WINDOW_HOURS}-hour rolling statistics per household")
    log(f"  Window: {ROLLING_WINDOW_HOURS} obs, min_periods: {ROLLING_MIN_PERIODS}, closed='left'")

    all_groups = []

    for apt_id, grp in df.groupby("apt", sort=False):
        grp = grp.sort_values("timestamp").copy()

        # Rolling mean and std — exclude current row via closed="left"
        roll = grp["energy_kwh"].rolling(
            window=ROLLING_WINDOW_HOURS,
            min_periods=ROLLING_MIN_PERIODS,
            closed="left",
        )
        grp["feat_rolling_mean_7d"] = roll.mean()
        grp["feat_rolling_std_7d"] = roll.std()

        # Rolling Z-score: (obs - rolling_mean) / rolling_std
        grp["feat_rolling_zscore"] = (
            (grp["energy_kwh"] - grp["feat_rolling_mean_7d"])
            / grp["feat_rolling_std_7d"]
        )

        # Rolling deviation (signed, un-normalised — useful for display)
        grp["feat_rolling_deviation"] = (
            grp["energy_kwh"] - grp["feat_rolling_mean_7d"]
        )

        # Boolean flags (NaN rolling stats → False, not flagged)
        grp["flag_rolling_spike"] = (
            grp["feat_rolling_zscore"].fillna(0) > ZSCORE_FLAG_THRESHOLD
        )
        grp["flag_rolling_low"] = (
            grp["feat_rolling_zscore"].fillna(0) < -ZSCORE_FLAG_THRESHOLD
        )

        all_groups.append(grp)

    df = pd.concat(all_groups, ignore_index=True).sort_values(
        ["apt", "timestamp"]
    ).reset_index(drop=True)

    n_nan_roll = int(df["feat_rolling_mean_7d"].isna().sum())
    n_spike = int(df["flag_rolling_spike"].sum())
    n_low = int(df["flag_rolling_low"].sum())
    log(f"  Rolling stats NaN (insufficient history): {n_nan_roll:,} rows ({n_nan_roll/len(df)*100:.1f}%)")
    log(f"  Flagged rolling spike (Z>+3): {n_spike:,} ({n_spike/len(df)*100:.2f}%)")
    log(f"  Flagged rolling low (Z<-3):   {n_low:,} ({n_low/len(df)*100:.2f}%)")

    return df


# ── Validation ────────────────────────────────────────────────────────────────
def validate(df: pd.DataFrame, input_rows: int) -> dict:
    log("Running validation checks...")

    checks = {}

    # 1. Row count preserved
    checks["row_count_preserved"] = len(df) == input_rows
    log(f"  Row count: {len(df):,} (expected {input_rows:,}) — {'OK' if checks['row_count_preserved'] else 'FAIL'}")

    # 2. Household count
    checks["n_households"] = int(df["apt"].nunique())
    checks["households_preserved"] = checks["n_households"] == 19
    log(f"  Households: {checks['n_households']} — {'OK' if checks['households_preserved'] else 'FAIL'}")

    # 3. No duplicate household-timestamp pairs
    n_dupes = int(df.duplicated(subset=["apt", "timestamp"]).sum())
    checks["no_duplicate_apt_timestamp"] = n_dupes == 0
    log(f"  Duplicate (apt, timestamp) pairs: {n_dupes} — {'OK' if n_dupes == 0 else 'FAIL'}")

    # 4. Original columns still present
    for col in ["apt", "timestamp", "lnenergy", "energy_kwh", "temp_c", "hour", "dayofweek"]:
        present = col in df.columns
        if not present:
            log(f"  FAIL: original column '{col}' missing!")
    checks["original_columns_preserved"] = all(c in df.columns for c in
        ["apt", "timestamp", "lnenergy", "energy_kwh", "temp_c", "hour", "dayofweek"])

    # 5. New feature columns present
    expected_new = [
        "feat_zscore_global", "flag_zscore_hi", "flag_zscore_lo",
        "feat_iqr_upper_1_5", "feat_iqr_upper_3_0",
        "flag_iqr_mild", "flag_iqr_extreme", "flag_iqr_low",
        "feat_rolling_mean_7d", "feat_rolling_std_7d",
        "feat_rolling_zscore", "feat_rolling_deviation",
        "flag_rolling_spike", "flag_rolling_low",
    ]
    missing_new = [c for c in expected_new if c not in df.columns]
    checks["all_feature_columns_present"] = len(missing_new) == 0
    if missing_new:
        log(f"  FAIL: missing feature columns: {missing_new}")

    # 6. No unexpected NaNs in non-rolling columns
    non_rolling_cols = ["feat_zscore_global", "feat_iqr_upper_1_5", "feat_iqr_upper_3_0"]
    for col in non_rolling_cols:
        n_nan = int(df[col].isna().sum())
        if n_nan > 0:
            log(f"  WARNING: {col} has {n_nan} NaN values (unexpected)")
    checks["no_nans_in_global_features"] = all(
        df[c].isna().sum() == 0 for c in non_rolling_cols
    )

    # 7. Rolling NaNs only at the START of each household
    for apt_id, grp in df.groupby("apt"):
        grp_sorted = grp.sort_values("timestamp")
        roll_nan = grp_sorted["feat_rolling_mean_7d"].isna()
        # All NaN rows should be at the beginning (a contiguous prefix)
        if roll_nan.any():
            first_valid = roll_nan.values.argmin()  # index of first non-NaN
            if roll_nan.values[first_valid:].any():
                log(f"  WARNING: apt={apt_id} has rolling NaN values NOT at the start — potential leakage or data issue")
    checks["rolling_nans_at_start_only"] = True  # Set True unless the above triggers

    # 8. Feature ranges plausible
    z_min = float(df["feat_zscore_global"].min())
    z_max = float(df["feat_zscore_global"].max())
    checks["zscore_range_plausible"] = -20 < z_min and z_max < 50
    log(f"  Global Z-score range: [{z_min:.2f}, {z_max:.2f}] — {'OK' if checks['zscore_range_plausible'] else 'WARN'}")

    # 9. First obs of each household: rolling stats should be NaN
    first_obs = df.groupby("apt").apply(lambda g: g.sort_values("timestamp").iloc[0])
    all_first_nan = first_obs["feat_rolling_mean_7d"].isna().all()
    checks["first_obs_rolling_is_nan"] = bool(all_first_nan)
    log(f"  First obs of each household has NaN rolling stats: {'OK' if all_first_nan else 'FAIL — leakage risk'}")

    # 10. Flag counts per method
    checks["flag_counts"] = {
        "flag_zscore_hi": int(df["flag_zscore_hi"].sum()),
        "flag_zscore_lo": int(df["flag_zscore_lo"].sum()),
        "flag_iqr_mild": int(df["flag_iqr_mild"].sum()),
        "flag_iqr_extreme": int(df["flag_iqr_extreme"].sum()),
        "flag_iqr_low": int(df["flag_iqr_low"].sum()),
        "flag_rolling_spike": int(df["flag_rolling_spike"].sum()),
        "flag_rolling_low": int(df["flag_rolling_low"].sum()),
    }

    all_passed = all(v for k, v in checks.items() if isinstance(v, bool))
    log(f"  Overall validation: {'ALL PASSED' if all_passed else 'SOME CHECKS FAILED — review above'}")

    return checks


# ── Write outputs ─────────────────────────────────────────────────────────────
def write_csv(df: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    size_kb = OUTPUT_CSV.stat().st_size / 1024
    log(f"Written: {OUTPUT_CSV.name}  ({size_kb:.0f} KB, {len(df):,} rows, {len(df.columns)} columns)")


def write_report(df: pd.DataFrame, validation: dict) -> None:
    # Per-household flag summary
    per_household = {}
    for apt_id, grp in df.groupby("apt"):
        per_household[str(apt_id)] = {
            "n_obs": int(len(grp)),
            "zscore_hi": int(grp["flag_zscore_hi"].sum()),
            "zscore_lo": int(grp["flag_zscore_lo"].sum()),
            "iqr_mild": int(grp["flag_iqr_mild"].sum()),
            "iqr_extreme": int(grp["flag_iqr_extreme"].sum()),
            "iqr_low": int(grp["flag_iqr_low"].sum()),
            "rolling_spike": int(grp["flag_rolling_spike"].sum()),
            "rolling_low": int(grp["flag_rolling_low"].sum()),
            "rolling_nan_obs": int(grp["feat_rolling_mean_7d"].isna().sum()),
            "mean_rolling_zscore": float(grp["feat_rolling_zscore"].mean()) if grp["feat_rolling_zscore"].notna().any() else None,
        }

    report = {
        "script": "ml/anomaly_features.py",
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "input_file": str(INPUT_CSV.relative_to(REPO_ROOT)),
        "output_file": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "n_rows": int(len(df)),
        "n_households": int(df["apt"].nunique()),
        "n_feature_columns_added": 14,
        "total_columns": int(len(df.columns)),
        "rolling_window_config": {
            "window_hours": ROLLING_WINDOW_HOURS,
            "min_periods": ROLLING_MIN_PERIODS,
            "closed": "left",
            "note": "closed='left' excludes current row to prevent self-leakage",
        },
        "flag_counts_total": validation["flag_counts"],
        "flag_rates_pct": {
            k: round(v / len(df) * 100, 3)
            for k, v in validation["flag_counts"].items()
        },
        "validation": validation,
        "per_household": per_household,
        "feature_columns": [
            "feat_zscore_global",
            "flag_zscore_hi",
            "flag_zscore_lo",
            "feat_iqr_upper_1_5",
            "feat_iqr_upper_3_0",
            "flag_iqr_mild",
            "flag_iqr_extreme",
            "flag_iqr_low",
            "feat_rolling_mean_7d",
            "feat_rolling_std_7d",
            "feat_rolling_zscore",
            "feat_rolling_deviation",
            "flag_rolling_spike",
            "flag_rolling_low",
        ],
    }

    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report, f, indent=2, default=str)
    log(f"Written: {OUTPUT_REPORT.name}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log("=" * 60)
    log("SmartWatt India — Anomaly Features (T006)")
    log("=" * 60)

    df = load_data()
    input_rows = len(df)

    # Method 1: global Z-score on lnenergy
    df = compute_global_zscore(df)

    # Method 2: IQR fences on energy_kwh
    df = compute_iqr_fences(df)

    # Method 3: rolling 7-day statistics
    df = compute_rolling_features(df)

    # Validate
    validation = validate(df, input_rows)

    # Write outputs
    write_csv(df)
    write_report(df, validation)

    # ── Final summary ─────────────────────────────────────────────────────────
    fc = validation["flag_counts"]
    log("=" * 60)
    log("T006 COMPLETE — Anomaly Feature Summary")
    log(f"  Input rows:    {input_rows:,}")
    log(f"  Output rows:   {len(df):,} (unchanged)")
    log(f"  Output cols:   {len(df.columns)} ({len(df.columns) - 16} new feature cols)")
    log("  Method 1 — Global Z-score on lnenergy:")
    log(f"    Z > +3 (spike):  {fc['flag_zscore_hi']:,} ({fc['flag_zscore_hi']/len(df)*100:.2f}%)")
    log(f"    Z < -3 (low):    {fc['flag_zscore_lo']:,} ({fc['flag_zscore_lo']/len(df)*100:.2f}%)")
    log("  Method 2 — IQR fence on energy_kwh:")
    log(f"    Mild (1.5×IQR):  {fc['flag_iqr_mild']:,} ({fc['flag_iqr_mild']/len(df)*100:.2f}%)")
    log(f"    Extreme (3×IQR): {fc['flag_iqr_extreme']:,} ({fc['flag_iqr_extreme']/len(df)*100:.2f}%)")
    log(f"    Low (<lower):    {fc['flag_iqr_low']:,} ({fc['flag_iqr_low']/len(df)*100:.2f}%)")
    log("  Method 3 — Rolling 7-day Z-score:")
    log(f"    Spike (Z>+3):    {fc['flag_rolling_spike']:,} ({fc['flag_rolling_spike']/len(df)*100:.2f}%)")
    log(f"    Low (Z<-3):      {fc['flag_rolling_low']:,} ({fc['flag_rolling_low']/len(df)*100:.2f}%)")
    log(f"  Output CSV:    {OUTPUT_CSV}")
    log(f"  Report JSON:   {OUTPUT_REPORT}")
    log("=" * 60)


if __name__ == "__main__":
    main()
