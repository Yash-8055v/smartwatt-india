"""
SmartWatt India — Random Forest Regressor Comparison (T016)
============================================================
Purpose:
  Train a Random Forest model on the same context variables as the Ridge baseline
  to see if non-linear interactions improve R² and RMSE for expected electricity
  consumption.

Outputs:
  data/processed/rf_metrics.json
  ml/models/rf_model.joblib
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
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
OUTPUT_METRICS = PROCESSED_DIR / "rf_metrics.json"
OUTPUT_MODEL = MODELS_DIR / "rf_model.joblib"

# ── Feature configuration ─────────────────────────────────────────────────────
TARGET = "lnenergy"
CATEGORICAL_FEATURES = ["apt", "hour", "dayofweek", "month"]
CONTINUOUS_FEATURES = ["temp_c", "tt", "tt2", "tt3"]
BINARY_FEATURES = ["post", "finpost", "healthpost"]
ALL_FEATURES = CATEGORICAL_FEATURES + CONTINUOUS_FEATURES + BINARY_FEATURES

TRAIN_FRACTION = 0.80

def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def load_and_prepare(path: Path) -> pd.DataFrame:
    log(f"Loading: {path.name}")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)
    df["month"] = df["timestamp"].dt.month
    return df

def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_parts, test_parts = [], []
    for apt_id, grp in df.groupby("apt", sort=True):
        grp_sorted = grp.sort_values("timestamp").reset_index(drop=True)
        n = len(grp_sorted)
        split_idx = int(np.floor(n * TRAIN_FRACTION))
        train_parts.append(grp_sorted.iloc[:split_idx].copy())
        test_parts.append(grp_sorted.iloc[split_idx:].copy())
    return pd.concat(train_parts, ignore_index=True), pd.concat(test_parts, ignore_index=True)

def build_preprocessor() -> ColumnTransformer:
    categorical_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop="first")
    continuous_transformer = StandardScaler()
    return ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
            ("cont", continuous_transformer, CONTINUOUS_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES),
        ],
        remainder="drop",
    )

def main() -> None:
    log("=" * 60)
    log("SmartWatt India — Random Forest Comparison (T016)")
    log("=" * 60)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_and_prepare(INPUT_CSV)
    train_df, test_df = chronological_split(df)

    X_train = train_df[ALL_FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[ALL_FEATURES]
    y_test = test_df[TARGET]

    # RandomForest configuration
    # Max depth limited to prevent extreme overfitting and control training time
    # n_estimators=100 is standard
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15, 
        n_jobs=-1,
        random_state=42
    )

    pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", rf_model),
    ])

    log("Training Random Forest Regressor...")
    pipeline.fit(X_train, y_train)

    log("Generating predictions...")
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

    log(f"  Train → MAE={train_metrics['mae']:.4f}  RMSE={train_metrics['rmse']:.4f}  R²={train_metrics['r2']:.4f}")
    log(f"  Test  → MAE={test_metrics['mae']:.4f}  RMSE={test_metrics['rmse']:.4f}  R²={test_metrics['r2']:.4f}")

    metrics_out = {
        "run_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "model": "RandomForestRegressor",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 15,
        },
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
    }

    with open(OUTPUT_METRICS, "w") as f:
        json.dump(metrics_out, f, indent=2)
    log(f"Written: {OUTPUT_METRICS.name}")

    joblib.dump(pipeline, OUTPUT_MODEL)
    log(f"Written: {OUTPUT_MODEL.name} ({OUTPUT_MODEL.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # Load Ridge metrics to compare
    ridge_metrics_file = PROCESSED_DIR / "model_metrics.json"
    if ridge_metrics_file.exists():
        with open(ridge_metrics_file) as f:
            ridge_data = json.load(f)
            ridge_test = ridge_data["models"]["Ridge"]["test_metrics"]
            
        log("=" * 60)
        log("COMPARISON: Random Forest vs Ridge Baseline")
        log(f"  Ridge        Test RMSE: {ridge_test['rmse']:.4f} | Test R²: {ridge_test['r2']:.4f}")
        log(f"  RandomForest Test RMSE: {test_metrics['rmse']:.4f} | Test R²: {test_metrics['r2']:.4f}")
        
        diff_rmse = ridge_test['rmse'] - test_metrics['rmse']
        diff_r2 = test_metrics['r2'] - ridge_test['r2']
        if diff_rmse > 0:
            log(f"  RandomForest is BETTER by {diff_rmse:.4f} RMSE and {diff_r2:.4f} R²")
        else:
            log(f"  RandomForest is WORSE by {-diff_rmse:.4f} RMSE and {-diff_r2:.4f} R²")
    log("=" * 60)

if __name__ == "__main__":
    main()
