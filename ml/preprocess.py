"""
SmartWatt India — Preprocessing Script
Task: T003 — Produce data/processed/hourly_energy.csv

What this script does
---------------------
1. Loads Table_9_3_Final.dta (hourly, 19 apartments).
2. Validates that all expected columns are present.
3. Converts the timestamp column to pandas datetime.
4. Sorts the dataset chronologically per apartment.
5. Derives energy_kwh = exp(lnenergy).
6. Derives temp_c = (hour_temp - 32) * 5/9.
7. Validates the output dataset.
8. Writes data/processed/hourly_energy.csv.
9. Writes data/processed/preprocessing_report.json.

What this script does NOT do
-----------------------------
- Does not train a model.
- Does not perform anomaly detection.
- Does not remove or winsorise any observations.
- Does not normalise or standardise values.
- Does not create arbitrary ML features.
- Does not modify the raw input file.
- Does not aggregate to daily or any other frequency.

Architecture decisions in effect
---------------------------------
- ADR-002: hourly is the primary resolution
- ADR-007: Table_9_3_Final.dta is the primary ML dataset
- ADR-008: energy_kwh = exp(lnenergy); temp_c from Fahrenheit

Run from any directory:
    python /path/to/ml/preprocess.py
Or from project root:
    python ml/preprocess.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── Path resolution (works regardless of working directory) ───────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RAW_FILE = (
    REPO_ROOT
    / "data"
    / "raw"
    / "Data_Do_Files_For_Data_Brief_09-15-2017"
    / "Data"
    / "Table_9_3_Final.dta"
)
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "hourly_energy.csv"
OUTPUT_REPORT = PROCESSED_DIR / "preprocessing_report.json"

# ── Expected columns from dataset inspection ──────────────────────────────────
EXPECTED_COLUMNS = [
    "apt",
    "timestamp",
    "hour",
    "dayofweek",
    "post",
    "finpost",
    "healthpost",
    "ga_fin_1",
    "ga_health_1",
    "hour_temp",
    "tt",
    "tt2",
    "tt3",
    "lnenergy",
]

# ── Minimum required columns for the processed dataset ────────────────────────
MINIMUM_REQUIRED_COLUMNS = [
    "apt",
    "timestamp",
    "lnenergy",
    "hour_temp",
    "hour",
    "dayofweek",
]


def log(msg: str) -> None:
    """Print a timestamped log line."""
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def load_raw_data(path: Path) -> pd.DataFrame:
    """Load the Stata file. Raises SystemExit on file-not-found."""
    if not path.exists():
        log(f"ERROR: Raw input file not found: {path}")
        log("  Expected location: data/raw/Data_Do_Files_For_Data_Brief_09-15-2017/Data/Table_9_3_Final.dta")
        log("  Do not modify data/raw/. Check the dataset was downloaded correctly.")
        sys.exit(1)

    log(f"Loading: {path.name} ({path.stat().st_size / 1_048_576:.2f} MB)")
    df = pd.read_stata(path, convert_categoricals=False)
    log(f"Loaded: {len(df):,} rows × {len(df.columns)} columns")
    return df


def validate_columns(df: pd.DataFrame) -> None:
    """Confirm all expected columns are present. Exits on failure."""
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        log("FATAL: The following expected columns are MISSING from the dataset:")
        for col in missing:
            log(f"  - {col}")
        log("Preprocessing cannot continue. Investigate the raw file.")
        log("Do not invent column names or attempt to work around this.")
        sys.exit(1)

    log("Column validation: PASSED — all 14 expected columns present.")


def prepare_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure timestamp is pandas datetime and sort chronologically."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        log("timestamp: converted to datetime64.")
    else:
        log("timestamp: already datetime64, no conversion needed.")

    # Chronological sort per apartment — project rule: no random shuffling
    df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)
    log("Sorted by ['apt', 'timestamp'] (chronological, no shuffle).")
    return df


def compute_energy_kwh(df: pd.DataFrame) -> pd.DataFrame:
    """Derive energy_kwh = exp(lnenergy). No values are dropped."""
    df["energy_kwh"] = np.exp(df["lnenergy"])
    n_negative = (df["energy_kwh"] <= 0).sum()
    if n_negative > 0:
        log(f"WARNING: {n_negative} rows have energy_kwh <= 0 (unexpected — keep all for analysis).")
    else:
        log("energy_kwh: computed from exp(lnenergy). All values > 0.")
    return df


def compute_temp_celsius(df: pd.DataFrame) -> pd.DataFrame:
    """Derive temp_c = (hour_temp - 32) * 5/9. Original hour_temp is kept."""
    df["temp_c"] = (df["hour_temp"] - 32) * 5.0 / 9.0
    log(f"temp_c: computed from hour_temp (°F). Range: {df['temp_c'].min():.1f}°C — {df['temp_c'].max():.1f}°C.")
    return df


def validate_output(df: pd.DataFrame) -> dict:
    """Run all validation checks and return a structured report dict."""
    log("Running output validation...")

    # ── Basic counts ──────────────────────────────────────────────────────────
    n_rows = len(df)
    households = sorted(df["apt"].unique().tolist())
    n_households = len(households)
    rows_per_apt = df.groupby("apt").size().to_dict()

    # ── Missing values ────────────────────────────────────────────────────────
    missing_counts = df.isnull().sum()
    total_missing = int(missing_counts.sum())
    missing_by_col = {col: int(v) for col, v in missing_counts.items() if v > 0}

    # ── Duplicates ────────────────────────────────────────────────────────────
    n_duplicates = int(df.duplicated().sum())

    # ── Date range ────────────────────────────────────────────────────────────
    ts_min = df["timestamp"].min()
    ts_max = df["timestamp"].max()

    # ── Energy statistics ─────────────────────────────────────────────────────
    energy_stats = {
        "min_kwh": float(df["energy_kwh"].min()),
        "max_kwh": float(df["energy_kwh"].max()),
        "mean_kwh": float(df["energy_kwh"].mean()),
        "median_kwh": float(df["energy_kwh"].median()),
        "std_kwh": float(df["energy_kwh"].std()),
        "p25_kwh": float(df["energy_kwh"].quantile(0.25)),
        "p75_kwh": float(df["energy_kwh"].quantile(0.75)),
    }

    # ── Temperature statistics ────────────────────────────────────────────────
    temp_stats = {
        "min_temp_c": float(df["temp_c"].min()),
        "max_temp_c": float(df["temp_c"].max()),
        "mean_temp_c": float(df["temp_c"].mean()),
    }

    # ── Temporal validation — per household ──────────────────────────────────
    temporal = {}
    all_gap_issues = []
    for apt_id, grp in df.groupby("apt"):
        grp_sorted = grp.sort_values("timestamp")
        gaps = grp_sorted["timestamp"].diff().dropna()

        if len(gaps) == 0:
            temporal[str(apt_id)] = {"note": "only 1 observation, no gaps to check"}
            continue

        median_gap = gaps.median()
        median_gap_min = median_gap.total_seconds() / 60.0

        # Flag any gap that is not exactly 60 minutes
        non_hourly = gaps[gaps != pd.Timedelta(hours=1)]
        n_non_hourly = len(non_hourly)

        gap_detail = {
            "n_observations": int(len(grp_sorted)),
            "median_gap_minutes": round(median_gap_min, 1),
            "n_non_hourly_gaps": n_non_hourly,
        }

        if n_non_hourly > 0:
            gap_examples = non_hourly.head(5)
            gap_detail["example_non_hourly_gaps_minutes"] = [
                round(g.total_seconds() / 60.0, 1)
                for g in gap_examples
            ]
            all_gap_issues.append(f"apt={apt_id}: {n_non_hourly} non-hourly gaps")

        temporal[str(apt_id)] = gap_detail

    if all_gap_issues:
        log(f"WARNING: Non-hourly time gaps detected:")
        for issue in all_gap_issues:
            log(f"  {issue}")
        log("  These gaps are documented. No filling was applied.")
    else:
        log("Temporal validation: all households have consistent hourly gaps.")

    # ── Print summary ─────────────────────────────────────────────────────────
    log(f"Rows:              {n_rows:,}")
    log(f"Households:        {n_households}")
    log(f"Date range:        {ts_min} → {ts_max}")
    log(f"Missing values:    {total_missing}")
    log(f"Duplicate rows:    {n_duplicates}")
    log(f"energy_kwh min:    {energy_stats['min_kwh']:.6f} kWh")
    log(f"energy_kwh max:    {energy_stats['max_kwh']:.4f} kWh")
    log(f"energy_kwh mean:   {energy_stats['mean_kwh']:.4f} kWh")
    log(f"energy_kwh median: {energy_stats['median_kwh']:.4f} kWh")
    log(f"temp_c range:      {temp_stats['min_temp_c']:.1f}°C — {temp_stats['max_temp_c']:.1f}°C")

    return {
        "n_rows": n_rows,
        "n_households": n_households,
        "households": households,
        "rows_per_household": {str(k): int(v) for k, v in rows_per_apt.items()},
        "date_start": str(ts_min),
        "date_end": str(ts_max),
        "total_missing_values": total_missing,
        "missing_by_column": missing_by_col,
        "duplicate_rows": n_duplicates,
        "energy_statistics": energy_stats,
        "temperature_statistics": temp_stats,
        "temporal_validation": temporal,
        "temporal_gap_issues": all_gap_issues,
    }


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write the processed dataset to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    size_kb = path.stat().st_size / 1024
    log(f"Written: {path.name}  ({size_kb:.0f} KB)")


def write_report(report: dict, path: Path) -> None:
    """Write the preprocessing report to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    log(f"Written: {path.name}")


def main() -> None:
    log("=" * 60)
    log("SmartWatt India — Preprocessing (T003)")
    log("=" * 60)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load raw data
    df = load_raw_data(RAW_FILE)
    input_rows = len(df)

    # 2. Validate columns — exit immediately if any expected column is missing
    validate_columns(df)

    # 3. Prepare timestamp and sort chronologically
    df = prepare_timestamp(df)

    # 4. Compute energy_kwh = exp(lnenergy) — no rows removed
    df = compute_energy_kwh(df)

    # 5. Compute temp_c — original hour_temp is preserved
    df = compute_temp_celsius(df)

    # 6. Validate output dataset
    validation = validate_output(df)
    output_rows = validation["n_rows"]

    # 7. Write CSV
    write_csv(df, OUTPUT_CSV)

    # 8. Build and write preprocessing report
    report = {
        "script": str(Path(__file__).name),
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "input_file": str(RAW_FILE.relative_to(REPO_ROOT)),
        "output_file": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        "input_rows": input_rows,
        "output_rows": output_rows,
        "households": validation["n_households"],
        "date_start": validation["date_start"],
        "date_end": validation["date_end"],
        "transformations": [
            "timestamp converted to datetime64 and sorted chronologically per apt",
            "energy_kwh = np.exp(lnenergy)  — no rows removed",
            "temp_c = (hour_temp - 32) * 5/9  — original hour_temp preserved",
        ],
        "columns": list(df.columns),
        "missing_values": validation["total_missing_values"],
        "missing_by_column": validation["missing_by_column"],
        "duplicate_rows": validation["duplicate_rows"],
        "rows_per_household": validation["rows_per_household"],
        "energy_statistics": validation["energy_statistics"],
        "temperature_statistics": validation["temperature_statistics"],
        "temporal_validation": validation["temporal_validation"],
        "temporal_gap_issues": validation["temporal_gap_issues"],
    }
    write_report(report, OUTPUT_REPORT)

    # 9. Final summary
    log("=" * 60)
    log("T003 COMPLETE")
    log(f"Input rows:   {input_rows:,}")
    log(f"Output rows:  {output_rows:,}")
    log(f"Households:   {validation['n_households']}")
    log(f"Date range:   {validation['date_start']} → {validation['date_end']}")
    log(f"Missing:      {validation['total_missing_values']}")
    log(f"Duplicates:   {validation['duplicate_rows']}")
    if validation["temporal_gap_issues"]:
        log(f"Gap issues:   {len(validation['temporal_gap_issues'])} household(s) — see report")
    else:
        log("Gap issues:   None")
    log(f"Output CSV:   {OUTPUT_CSV}")
    log(f"Report JSON:  {OUTPUT_REPORT}")
    log("=" * 60)


if __name__ == "__main__":
    main()
