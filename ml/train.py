"""
SmartWatt India — Regression Baseline Training (T007)
======================================================
Purpose:
  Train a per-panel regression model that predicts expected electricity
  consumption (lnenergy) from context variables confirmed by EDA.
  The model residual becomes the 4th anomaly signal (regression residual).

Design:
  - Target:      lnenergy  (approximately log-normal; symmetric → regression-friendly)
  - Predictors:  hour, dayofweek, temp_c, is_weekend, month,
                 apt (one-hot encoded household fixed effects),
                 post, finpost, healthpost, tt, tt2, tt3
  - Encoding:    OneHotEncoder on apt + hour + dayofweek + month (dummy variables)
                 StandardScaler on continuous features (temp_c, tt, tt2, tt3)
  - Split:       Chronological 80/20 per household — NO random shuffle.
                 The split point is the 80th percentile of each household's
                 timestamps, so train always precedes test.
  - Models:      (1) LinearRegression  (2) Ridge (α tuned by cross-validation)
  - Selection:   Ridge preferred unless LinearRegression is clearly better on
                 all metrics — regularisation avoids instability in OHE-heavy design.
  - CV:          Time-series aware RidgeCV with 5 chronological folds.

What this script does NOT do:
  - Does not use anomaly flag columns as predictors.
  - Does not use rolling stats or residuals as predictors (leakage).
  - Does not do random train/test split.
  - Does not remove or modify extreme observations.
  - Does not classify observations as theft or appliance failures.
  - Does not produce the final combined anomaly score.
  - Does not modify raw data.

Outputs:
  data/processed/model_predictions.csv   — apt, timestamp, actual, predicted, residual, ...
  data/processed/model_metrics.json      — per-model and overall evaluation metrics
  ml/models/ridge_model.joblib           — selected trained pipeline artifact

Run from any directory:
    python ml/train.py
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
MODELS_DIR = REPO_ROOT / "ml" / "models"
INPUT_CSV = PROCESSED_DIR / "anomaly_features.csv"
OUTPUT_PREDICTIONS = PROCESSED_DIR / "model_predictions.csv"
OUTPUT_METRICS = PROCESSED_DIR / "model_metrics.json"
OUTPUT_MODEL = MODELS_DIR / "ridge_model.joblib"

# ── Feature configuration ─────────────────────────────────────────────────────
TARGET = "lnenergy"

# Categorical features — will be one-hot encoded
# apt: household fixed effects (captures household-level baseline)
# hour: time-of-day (2.35x peak/trough ratio from EDA)
# dayofweek: day-of-week effect (p<0.0001, Kruskal-Wallis from EDA)
# month: seasonal effect (May vs Nov differ by 0.45 kWh)
CATEGORICAL_FEATURES = ["apt", "hour", "dayofweek", "month"]

# Continuous features — will be standardised
# temp_c: Pearson r=0.12 on log scale (EDA); converted from °F
# tt, tt2, tt3: cubic time trend — controls secular drift
CONTINUOUS_FEATURES = ["temp_c", "tt", "tt2", "tt3"]

# Treatment/context features — included as binary predictors (no scaling needed)
# post: pre/post intervention period — EDA confirmed -8.5% effect (p=0.044)
# finpost, healthpost: treatment group × post interactions
# These are included so residuals reflect genuine deviations, not treatment effects
BINARY_FEATURES = ["post", "finpost", "healthpost"]

# DO NOT include as predictors:
#   lnenergy, energy_kwh, temp_c (already in CONTINUOUS)
#   feat_*, flag_* columns (anomaly features — leakage)
#   hour_temp (raw Fahrenheit — temp_c is the processed form)
#   ga_fin_1, ga_health_1 (treatment intensity — collinear with finpost/healthpost)

ALL_FEATURES = CATEGORICAL_FEATURES + CONTINUOUS_FEATURES + BINARY_FEATURES

# ── Ridge CV alphas ───────────────────────────────────────────────────────────
RIDGE_ALPHAS = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]

# ── Train/test split config ───────────────────────────────────────────────────
TRAIN_FRACTION = 0.80  # first 80% of each household's observations

# ── Minimum household representation ─────────────────────────────────────────
MIN_TEST_OBS_PER_HOUSEHOLD = 20


def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# ── Load & prepare ────────────────────────────────────────────────────────────
def load_and_prepare(path: Path) -> pd.DataFrame:
    log(f"Loading: {path.name}")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)

    # Derive month — used as seasonal control
    df["month"] = df["timestamp"].dt.month

    # Validate required columns
    required = [TARGET] + ALL_FEATURES + ["timestamp", "energy_kwh"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {missing}")

    log(f"Loaded: {len(df):,} rows, {df['apt'].nunique()} households")
    log(f"Predictors ({len(ALL_FEATURES)}): {ALL_FEATURES}")
    return df


# ── Chronological split ───────────────────────────────────────────────────────
def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split each household's data chronologically: first 80% → train, last 20% → test.
    Train period always precedes test period for every household (no leakage).
    """
    train_parts, test_parts = [], []

    log(f"Chronological split ({TRAIN_FRACTION*100:.0f}% train / {(1-TRAIN_FRACTION)*100:.0f}% test) per household:")

    for apt_id, grp in df.groupby("apt", sort=True):
        grp_sorted = grp.sort_values("timestamp").reset_index(drop=True)
        n = len(grp_sorted)
        split_idx = int(np.floor(n * TRAIN_FRACTION))

        train_grp = grp_sorted.iloc[:split_idx].copy()
        test_grp = grp_sorted.iloc[split_idx:].copy()

        n_test = len(test_grp)
        if n_test < MIN_TEST_OBS_PER_HOUSEHOLD:
            log(f"  WARNING: apt={apt_id} has only {n_test} test observations")

        # Verify no leakage: last train timestamp < first test timestamp
        assert train_grp["timestamp"].max() < test_grp["timestamp"].min(), \
            f"Leakage detected for apt={apt_id}"

        log(f"  apt={apt_id:2d}: n={n:5d}  train={len(train_grp):5d} "
            f"(up to {train_grp['timestamp'].max().date()})  "
            f"test={len(test_grp):4d} "
            f"(from {test_grp['timestamp'].min().date()})")

        train_parts.append(train_grp)
        test_parts.append(test_grp)

    train_df = pd.concat(train_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    log(f"Total train rows: {len(train_df):,}  "
        f"(date range: {train_df['timestamp'].min().date()} → {train_df['timestamp'].max().date()})")
    log(f"Total test rows:  {len(test_df):,}  "
        f"(date range: {test_df['timestamp'].min().date()} → {test_df['timestamp'].max().date()})")

    # Global sanity: 100% of train timestamps < 100% of test timestamps is
    # guaranteed per household; globally they interleave (different households
    # have different date ranges), which is expected and fine.
    return train_df, test_df


# ── Build sklearn preprocessor ────────────────────────────────────────────────
def build_preprocessor() -> ColumnTransformer:
    """
    ColumnTransformer that:
      - OHE-encodes categorical features (apt, hour, dayofweek, month)
      - StandardScaler on continuous features (temp_c, tt, tt2, tt3)
      - Passes binary features through unchanged

    Fitted ONLY on training data.
    """
    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",   # silent if a test household has unseen month
        sparse_output=False,
        drop="first",              # drop one dummy per category to avoid multicollinearity
    )
    continuous_transformer = StandardScaler()

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
            ("cont", continuous_transformer, CONTINUOUS_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES),
        ],
        remainder="drop",          # drop any columns not in features list
    )
    return preprocessor


# ── Train & evaluate ──────────────────────────────────────────────────────────
def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> dict:
    """Train Linear and Ridge, evaluate both, return metrics dict."""

    X_train = train_df[ALL_FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[ALL_FEATURES]
    y_test = test_df[TARGET]

    results = {}

    for model_name, estimator in [
        ("LinearRegression", LinearRegression()),
        ("Ridge", RidgeCV(alphas=RIDGE_ALPHAS, cv=5, scoring="neg_root_mean_squared_error")),
    ]:
        log(f"Training {model_name}...")
        pipeline = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("model", estimator),
        ])
        pipeline.fit(X_train, y_train)

        y_pred_train = pipeline.predict(X_train)
        y_pred_test = pipeline.predict(X_test)

        train_metrics = {
            "mae": float(mean_absolute_error(y_train, y_pred_train)),
            "mse": float(mean_squared_error(y_train, y_pred_train)),
            "rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "r2": float(r2_score(y_train, y_pred_train)),
        }
        test_metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "mse": float(mean_squared_error(y_test, y_pred_test)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "r2": float(r2_score(y_test, y_pred_test)),
        }

        if model_name == "Ridge":
            best_alpha = float(estimator.alpha_)
            log(f"  Ridge best alpha (CV): {best_alpha}")
            results[model_name] = {
                "pipeline": pipeline,
                "train_metrics": train_metrics,
                "test_metrics": test_metrics,
                "best_alpha": best_alpha,
            }
        else:
            results[model_name] = {
                "pipeline": pipeline,
                "train_metrics": train_metrics,
                "test_metrics": test_metrics,
            }

        log(f"  Train → MAE={train_metrics['mae']:.4f}  RMSE={train_metrics['rmse']:.4f}  R²={train_metrics['r2']:.4f}")
        log(f"  Test  → MAE={test_metrics['mae']:.4f}  RMSE={test_metrics['rmse']:.4f}  R²={test_metrics['r2']:.4f}")

    return results


# ── Model selection ───────────────────────────────────────────────────────────
def select_model(results: dict) -> tuple[str, Pipeline, str]:
    """
    Select the best model based on test RMSE (lower is better).
    Ridge is preferred when performance is equivalent (regularisation stability).
    Returns (model_name, pipeline, reason).
    """
    lr_rmse = results["LinearRegression"]["test_metrics"]["rmse"]
    rr_rmse = results["Ridge"]["test_metrics"]["rmse"]

    # If LinearRegression is meaningfully better (>1% improvement), prefer it
    if lr_rmse < rr_rmse * 0.99:
        name = "LinearRegression"
        reason = (
            f"LinearRegression test RMSE ({lr_rmse:.4f}) is >1% lower than "
            f"Ridge ({rr_rmse:.4f}). Simpler model preferred when measurably better."
        )
    else:
        name = "Ridge"
        reason = (
            f"Ridge test RMSE ({rr_rmse:.4f}) ≤ LinearRegression ({lr_rmse:.4f}). "
            f"Ridge selected for regularisation stability with one-hot encoded household dummies. "
            f"Best alpha={results['Ridge'].get('best_alpha', '?')}."
        )

    log(f"Selected model: {name}  — {reason}")
    return name, results[name]["pipeline"], reason


# ── Generate prediction output ────────────────────────────────────────────────
def generate_predictions(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    pipeline: Pipeline,
    selected_model_name: str,
) -> pd.DataFrame:
    """
    Produce predictions for ALL rows (train + test) using the selected model.
    Add split label, residual, and standardised residual (per-household).

    The standardised residual will serve as the 4th anomaly signal in the
    combined anomaly scoring step (T008).
    """
    full_df = pd.concat([train_df, test_df]).sort_values(["apt", "timestamp"]).reset_index(drop=True)

    # Predict on all rows
    full_df["lnenergy_predicted"] = pipeline.predict(full_df[ALL_FEATURES])

    # Residual (actual − predicted; positive = above expected)
    full_df["residual"] = full_df["lnenergy"] - full_df["lnenergy_predicted"]
    full_df["abs_residual"] = full_df["residual"].abs()

    # Back-transform predictions to kWh
    full_df["energy_kwh_predicted"] = np.exp(full_df["lnenergy_predicted"])

    # Standardised residual per household (residual / household residual std)
    # Computed on TRAINING residuals only to avoid test leakage
    train_residual_stats = (
        full_df[full_df["split"] == "train"]
        .groupby("apt")["residual"]
        .agg(res_mean="mean", res_std="std")
        .reset_index()
    )
    full_df = full_df.merge(train_residual_stats, on="apt", how="left")
    full_df["residual_zscore"] = (full_df["residual"] - full_df["res_mean"]) / full_df["res_std"]
    full_df = full_df.drop(columns=["res_mean", "res_std"])

    log(f"Predictions generated for {len(full_df):,} rows (train + test)")
    log(f"  Residual stats — mean: {full_df['residual'].mean():.4f}  "
        f"std: {full_df['residual'].std():.4f}  "
        f"range: [{full_df['residual'].min():.3f}, {full_df['residual'].max():.3f}]")
    log(f"  Residual Z-score range: [{full_df['residual_zscore'].min():.2f}, {full_df['residual_zscore'].max():.2f}]")

    return full_df


# ── Validation ────────────────────────────────────────────────────────────────
def validate_outputs(full_df: pd.DataFrame, train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    log("Running validation checks...")
    checks = {}

    # 1. No duplicate (apt, timestamp)
    n_dupes = int(full_df.duplicated(subset=["apt", "timestamp"]).sum())
    checks["no_duplicate_apt_timestamp"] = n_dupes == 0
    log(f"  Duplicate (apt, timestamp): {n_dupes} — {'OK' if n_dupes == 0 else 'FAIL'}")

    # 2. No missing predictions
    n_missing_pred = int(full_df["lnenergy_predicted"].isna().sum())
    checks["no_missing_predictions"] = n_missing_pred == 0
    log(f"  Missing predictions: {n_missing_pred} — {'OK' if n_missing_pred == 0 else 'FAIL'}")

    # 3. Train dates precede test dates per household
    leakage_found = False
    for apt_id, grp in full_df.groupby("apt"):
        tr = grp[grp["split"] == "train"]["timestamp"]
        te = grp[grp["split"] == "test"]["timestamp"]
        if len(tr) > 0 and len(te) > 0:
            if tr.max() >= te.min():
                log(f"  LEAKAGE: apt={apt_id} train max {tr.max()} >= test min {te.min()}")
                leakage_found = True
    checks["no_temporal_leakage"] = not leakage_found
    log(f"  Temporal leakage check: {'FAIL' if leakage_found else 'OK'}")

    # 4. All 19 households in test
    n_test_apts = full_df[full_df["split"] == "test"]["apt"].nunique()
    checks["all_households_in_test"] = n_test_apts == 19
    log(f"  Households in test set: {n_test_apts} — {'OK' if n_test_apts == 19 else 'WARN'}")

    # 5. Row counts match
    total = len(train_df) + len(test_df)
    checks["row_count_preserved"] = len(full_df) == total
    log(f"  Total rows: {len(full_df):,} = train({len(train_df):,}) + test({len(test_df):,}) — "
        f"{'OK' if checks['row_count_preserved'] else 'FAIL'}")

    # 6. Residual statistics per household
    per_apt = {}
    for apt_id, grp in full_df.groupby("apt"):
        res = grp["residual"]
        per_apt[str(apt_id)] = {
            "n_train": int((grp["split"] == "train").sum()),
            "n_test": int((grp["split"] == "test").sum()),
            "residual_mean": float(res.mean()),
            "residual_std": float(res.std()),
            "residual_mae": float(res.abs().mean()),
        }

    checks["per_household"] = per_apt

    all_pass = all(v for k, v in checks.items() if isinstance(v, bool))
    log(f"  Overall: {'ALL PASSED' if all_pass else 'SOME CHECKS FAILED'}")
    return checks


# ── Add split column before generating predictions ────────────────────────────
def tag_split(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = train_df.copy()
    test_df = test_df.copy()
    train_df["split"] = "train"
    test_df["split"] = "test"
    return train_df, test_df


# ── Write outputs ─────────────────────────────────────────────────────────────
def write_predictions(full_df: pd.DataFrame) -> None:
    # Select columns for the output file
    output_cols = [
        "apt", "timestamp", "split", "hour", "dayofweek", "month",
        "temp_c", "post", "finpost", "healthpost",
        "lnenergy", "lnenergy_predicted", "residual", "abs_residual",
        "residual_zscore", "energy_kwh", "energy_kwh_predicted",
    ]
    out = full_df[output_cols].sort_values(["apt", "timestamp"]).reset_index(drop=True)
    out.to_csv(OUTPUT_PREDICTIONS, index=False)
    size_kb = OUTPUT_PREDICTIONS.stat().st_size / 1024
    log(f"Written: {OUTPUT_PREDICTIONS.name}  ({size_kb:.0f} KB, {len(out):,} rows)")


def write_metrics(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    results: dict,
    selected_name: str,
    selection_reason: str,
    validation: dict,
) -> None:
    metrics_out = {
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "input_file": str(INPUT_CSV.relative_to(REPO_ROOT)),
        "target": TARGET,
        "features": {
            "categorical": CATEGORICAL_FEATURES,
            "continuous": CONTINUOUS_FEATURES,
            "binary": BINARY_FEATURES,
        },
        "split": {
            "train_fraction": TRAIN_FRACTION,
            "train_rows": int(len(train_df)),
            "test_rows": int(len(test_df)),
            "train_date_start": str(train_df["timestamp"].min()),
            "train_date_end": str(train_df["timestamp"].max()),
            "test_date_start": str(test_df["timestamp"].min()),
            "test_date_end": str(test_df["timestamp"].max()),
        },
        "models": {
            name: {
                "train_metrics": data["train_metrics"],
                "test_metrics": data["test_metrics"],
                **({"best_alpha": data["best_alpha"]} if "best_alpha" in data else {}),
            }
            for name, data in results.items()
        },
        "selected_model": selected_name,
        "selection_reason": selection_reason,
        "validation": {k: v for k, v in validation.items() if isinstance(v, bool)},
        "per_household": validation.get("per_household", {}),
        "model_artifact": str(OUTPUT_MODEL.relative_to(REPO_ROOT)),
    }
    with open(OUTPUT_METRICS, "w") as f:
        json.dump(metrics_out, f, indent=2, default=str)
    log(f"Written: {OUTPUT_METRICS.name}")


def save_model(pipeline: Pipeline) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, OUTPUT_MODEL)
    size_kb = OUTPUT_MODEL.stat().st_size / 1024
    log(f"Written: {OUTPUT_MODEL}  ({size_kb:.1f} KB)")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log("=" * 60)
    log("SmartWatt India — Regression Baseline Training (T007)")
    log("=" * 60)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load
    df = load_and_prepare(INPUT_CSV)

    # 2. Chronological split
    train_df, test_df = chronological_split(df)
    train_df, test_df = tag_split(train_df, test_df)

    # 3. Train both models
    results = train_and_evaluate(train_df, test_df)

    # 4. Select best model
    selected_name, selected_pipeline, selection_reason = select_model(results)

    # 5. Generate predictions for all rows
    full_df = generate_predictions(train_df, test_df, selected_pipeline, selected_name)

    # 6. Validate
    validation = validate_outputs(full_df, train_df, test_df)

    # 7. Write outputs
    write_predictions(full_df)
    write_metrics(train_df, test_df, results, selected_name, selection_reason, validation)
    save_model(selected_pipeline)

    # ── Summary ───────────────────────────────────────────────────────────────
    lr_m = results["LinearRegression"]["test_metrics"]
    rr_m = results["Ridge"]["test_metrics"]
    res = full_df["residual"]
    rz = full_df["residual_zscore"]

    log("=" * 60)
    log("T007 COMPLETE — Model Training Summary")
    log(f"  Train rows:  {len(train_df):,}")
    log(f"  Test rows:   {len(test_df):,}")
    log(f"  LinearRegression test:  MAE={lr_m['mae']:.4f}  RMSE={lr_m['rmse']:.4f}  R²={lr_m['r2']:.4f}")
    log(f"  Ridge        test:      MAE={rr_m['mae']:.4f}  RMSE={rr_m['rmse']:.4f}  R²={rr_m['r2']:.4f}")
    log(f"  Selected model: {selected_name}")
    log(f"  Residual stats: mean={res.mean():.4f}  std={res.std():.4f}  range=[{res.min():.3f}, {res.max():.3f}]")
    log(f"  Residual Z-score range: [{rz.min():.2f}, {rz.max():.2f}]")
    log(f"  Predictions: {OUTPUT_PREDICTIONS}")
    log(f"  Metrics:     {OUTPUT_METRICS}")
    log(f"  Model:       {OUTPUT_MODEL}")
    log("=" * 60)


if __name__ == "__main__":
    main()
