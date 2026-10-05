"""
SmartWatt India — Dataset Inspection Script
Task: T002 — Inspect all .dta files and identify best hourly electricity table.

RULES:
- Do NOT modify anything under data/raw/.
- Do NOT begin ML training.
- Do NOT invent missing information.
"""

import os
import json
import warnings
from pathlib import Path

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "Data_Do_Files_For_Data_Brief_09-15-2017" / "Data"
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DTA_FILES = sorted(RAW_DIR.glob("*.dta"))

print(f"Repository root : {REPO_ROOT}")
print(f"Raw data dir    : {RAW_DIR}")
print(f"Files found     : {len(DTA_FILES)}\n")
for f in DTA_FILES:
    print(f"  {f.name}  ({f.stat().st_size / 1_048_576:.2f} MB)")

print()

# ── Per-file inspection ───────────────────────────────────────────────────────
reports = {}

for dta_path in DTA_FILES:
    name = dta_path.stem
    print("=" * 70)
    print(f"FILE: {dta_path.name}  ({dta_path.stat().st_size / 1_048_576:.2f} MB)")
    print("=" * 70)

    try:
        df = pd.read_stata(dta_path, convert_categoricals=False)
    except Exception as e:
        print(f"  ERROR reading file: {e}\n")
        reports[name] = {"error": str(e)}
        continue

    nrows, ncols = df.shape
    print(f"  Rows      : {nrows:,}")
    print(f"  Columns   : {ncols}")

    # ── Column inventory ──────────────────────────────────────────────────────
    print("\n  Column inventory:")
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_missing = int(df[col].isna().sum())
        pct_missing = round(n_missing / nrows * 100, 2)
        n_unique = int(df[col].nunique(dropna=True))

        # sample values (first 5 non-null)
        sample_vals = df[col].dropna().head(5).tolist()
        sample_str = str(sample_vals)[:120]

        col_info.append({
            "column": col,
            "dtype": dtype,
            "n_missing": n_missing,
            "pct_missing": pct_missing,
            "n_unique": n_unique,
            "sample": sample_vals,
        })
        flag = "  *** MISSING" if pct_missing > 20 else ""
        print(f"    {col:<35} {dtype:<12} missing={pct_missing:5.1f}%  unique={n_unique:>7,}{flag}")

    # ── Numeric summary of likely consumption column ──────────────────────────
    energy_cols = [c for c in df.columns if "energy" in c.lower() or "kwh" in c.lower()
                   or "kw" in c.lower() or "consumption" in c.lower() or "elec" in c.lower()]
    if energy_cols:
        print(f"\n  Potential energy/consumption columns: {energy_cols}")
        for ec in energy_cols:
            if pd.api.types.is_numeric_dtype(df[ec]):
                desc = df[ec].describe()
                print(f"\n  describe({ec}):")
                print(desc.to_string(float_format=lambda x: f"{x:.4f}"))

    # ── Household / panel identifier ──────────────────────────────────────────
    id_candidates = [c for c in df.columns if c.lower() in ("apt", "id", "hhid", "hh_id",
                                                              "household", "household_id", "id1", "flat")]
    if id_candidates:
        print(f"\n  Household/panel ID candidates: {id_candidates}")
        for ic in id_candidates:
            n_hh = df[ic].nunique()
            print(f"    {ic}: {n_hh} unique values")

    # ── Timestamp column ──────────────────────────────────────────────────────
    ts_candidates = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()
                     or c.lower() in ("ts", "t", "timestamp", "period")]
    print(f"\n  Timestamp/time candidates: {ts_candidates}")

    # ── Duplicate check ───────────────────────────────────────────────────────
    n_dups = int(df.duplicated().sum())
    print(f"\n  Duplicate rows: {n_dups}")

    # ── Date range (if timestamp column present) ──────────────────────────────
    if "timestamp" in df.columns:
        ts_col = df["timestamp"]
        print(f"\n  timestamp raw range: min={ts_col.min()}  max={ts_col.max()}")
        if pd.api.types.is_numeric_dtype(ts_col):
            # Stata timestamps are ms since 01-Jan-1960
            try:
                ts_dt = pd.to_datetime(ts_col, unit="ms", origin="1960-01-01")
                print(f"  timestamp (datetime): min={ts_dt.min()}  max={ts_dt.max()}")
            except Exception:
                pass

    # ── Treatment/context columns ─────────────────────────────────────────────
    treatment_cols = [c for c in df.columns if any(k in c.lower() for k in
                      ("post", "treat", "fin", "health", "ga_", "subsample", "group"))]
    if treatment_cols:
        print(f"\n  Treatment/context columns: {treatment_cols}")

    # ── Temperature columns ───────────────────────────────────────────────────
    temp_cols = [c for c in df.columns if "temp" in c.lower()]
    if temp_cols:
        print(f"  Temperature columns: {temp_cols}")
        for tc in temp_cols:
            if pd.api.types.is_numeric_dtype(df[tc]):
                print(f"    {tc}: min={df[tc].min():.2f}  max={df[tc].max():.2f}  "
                      f"mean={df[tc].mean():.2f}")

    # ── Time resolution (for panel datasets) ─────────────────────────────────
    if "apt" in df.columns and "timestamp" in df.columns:
        # check median gap per household
        sample_apt = df["apt"].value_counts().index[0]
        apt_df = df[df["apt"] == sample_apt].sort_values("timestamp")
        if len(apt_df) > 1:
            gaps = apt_df["timestamp"].diff().dropna()
            median_gap = gaps.median()
            if hasattr(median_gap, "total_seconds"):
                median_gap_min = median_gap.total_seconds() / 60
            else:
                median_gap_min = float(median_gap) / 60_000
            print(f"\n  Time resolution (sample apt={sample_apt}): median gap = {median_gap_min:.1f} minutes")

    print()

    # ── Build compact report dict ─────────────────────────────────────────────
    reports[name] = {
        "file": dta_path.name,
        "size_mb": round(dta_path.stat().st_size / 1_048_576, 2),
        "nrows": nrows,
        "ncols": ncols,
        "columns": col_info,
        "energy_cols": energy_cols,
        "id_candidates": id_candidates,
        "timestamp_candidates": ts_candidates,
        "treatment_cols": treatment_cols,
        "temp_cols": temp_cols,
        "n_duplicates": n_dups,
    }

# ── Save compact JSON report ──────────────────────────────────────────────────
report_path = OUTPUT_DIR / "dataset_inspection_report.json"

def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)

with open(report_path, "w") as f:
    json.dump(reports, f, indent=2, default=_default)

print(f"\nCompact inspection report saved -> {report_path}")
print("\n=== INSPECTION COMPLETE ===")
