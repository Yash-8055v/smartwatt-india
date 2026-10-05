"""
SmartWatt India — Exploratory Data Analysis (T005)
===================================================
Purpose:
  - Understand the statistical properties of the hourly electricity dataset
  - Identify patterns: time-of-day, day-of-week, seasonal, per-household
  - Characterise the distribution of energy_kwh
  - Examine temperature correlation with energy
  - Document gap structure (missing hours)
  - Determine which statistical methods are appropriate
  - Save findings to data/processed/eda_report.json

What this script does NOT do:
  - Does not train a model
  - Does not score anomalies
  - Does not remove or transform outliers
  - Does not create ML features

Run from project root:
    python ml/eda.py
"""

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
INPUT_CSV = PROCESSED_DIR / "hourly_energy.csv"
OUTPUT_REPORT = PROCESSED_DIR / "eda_report.json"


def log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def load_data() -> pd.DataFrame:
    log(f"Loading: {INPUT_CSV.name}")
    df = pd.read_csv(INPUT_CSV, parse_dates=["timestamp"])
    df = df.sort_values(["apt", "timestamp"]).reset_index(drop=True)
    # Derive time features for EDA
    df["month"] = df["timestamp"].dt.month
    df["week_of_year"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["dayofweek"].isin([6, 7]).astype(int)
    df["date"] = df["timestamp"].dt.date
    log(f"Loaded: {len(df):,} rows, {df['apt'].nunique()} households")
    return df


# ── Section 1: Overall distribution ──────────────────────────────────────────
def energy_distribution(df: pd.DataFrame) -> dict:
    log("Section 1: Overall energy distribution")
    e = df["energy_kwh"]

    # Shapiro-Wilk on a sample (max 5000 for speed)
    sample = e.sample(min(5000, len(e)), random_state=42)
    _, shapiro_p = scipy_stats.shapiro(sample)

    # Skewness and kurtosis
    skew = float(e.skew())
    kurt = float(e.kurtosis())

    # Log-normal check: skewness of log(energy)
    log_e = np.log(e.clip(lower=1e-9))
    log_skew = float(log_e.skew())
    _, shapiro_log_p = scipy_stats.shapiro(log_e.sample(min(5000, len(log_e)), random_state=42))

    iqr = float(e.quantile(0.75) - e.quantile(0.25))
    # Tukey fence outliers (1.5×IQR rule)
    lower_fence = float(e.quantile(0.25) - 1.5 * iqr)
    upper_fence = float(e.quantile(0.75) + 1.5 * iqr)
    n_tukey_high = int((e > upper_fence).sum())
    n_tukey_low = int((e < lower_fence).sum())

    result = {
        "count": int(len(e)),
        "min": float(e.min()),
        "max": float(e.max()),
        "mean": float(e.mean()),
        "median": float(e.median()),
        "std": float(e.std()),
        "p5": float(e.quantile(0.05)),
        "p10": float(e.quantile(0.10)),
        "p25": float(e.quantile(0.25)),
        "p75": float(e.quantile(0.75)),
        "p90": float(e.quantile(0.90)),
        "p95": float(e.quantile(0.95)),
        "p99": float(e.quantile(0.99)),
        "iqr": iqr,
        "skewness": skew,
        "kurtosis": kurt,
        "shapiro_p_raw": float(shapiro_p),
        "normally_distributed_raw": shapiro_p > 0.05,
        "log_skewness": log_skew,
        "shapiro_p_log": float(shapiro_log_p),
        "log_normally_distributed": shapiro_log_p > 0.05,
        "tukey_upper_fence": upper_fence,
        "tukey_lower_fence": lower_fence,
        "n_tukey_high_outliers": n_tukey_high,
        "n_tukey_low_outliers": n_tukey_low,
        "pct_tukey_high": round(n_tukey_high / len(e) * 100, 2),
    }
    log(f"  mean={result['mean']:.4f} kWh, median={result['median']:.4f}, std={result['std']:.4f}")
    log(f"  skewness={skew:.3f}, kurtosis={kurt:.3f}")
    log(f"  Log-scale skewness={log_skew:.3f} (log-normal check)")
    log(f"  Tukey high-outliers: {n_tukey_high} ({result['pct_tukey_high']:.1f}%)")
    return result


# ── Section 2: Per-household baseline statistics ──────────────────────────────
def per_household_stats(df: pd.DataFrame) -> dict:
    log("Section 2: Per-household baseline statistics")
    result = {}
    for apt_id, grp in df.groupby("apt"):
        e = grp["energy_kwh"]
        iqr = float(e.quantile(0.75) - e.quantile(0.25))
        result[str(apt_id)] = {
            "n_obs": int(len(grp)),
            "mean_kwh": float(e.mean()),
            "median_kwh": float(e.median()),
            "std_kwh": float(e.std()),
            "min_kwh": float(e.min()),
            "max_kwh": float(e.max()),
            "p25_kwh": float(e.quantile(0.25)),
            "p75_kwh": float(e.quantile(0.75)),
            "iqr_kwh": iqr,
            "cv_pct": float(e.std() / e.mean() * 100),  # coefficient of variation
        }
        log(f"  apt={apt_id:2d}: n={len(grp):5d}  mean={e.mean():.4f}  std={e.std():.4f}  CV={e.std()/e.mean()*100:.0f}%")
    return result


# ── Section 3: Time-of-day pattern ────────────────────────────────────────────
def hourly_pattern(df: pd.DataFrame) -> dict:
    log("Section 3: Time-of-day (hour-of-day) pattern")
    hourly = df.groupby("hour")["energy_kwh"].agg(["mean", "median", "std"]).reset_index()
    result = {}
    for _, row in hourly.iterrows():
        result[str(int(row["hour"]))] = {
            "mean_kwh": float(row["mean"]),
            "median_kwh": float(row["median"]),
            "std_kwh": float(row["std"]),
        }
    peak_hour = hourly.loc[hourly["mean"].idxmax(), "hour"]
    trough_hour = hourly.loc[hourly["mean"].idxmin(), "hour"]
    log(f"  Peak hour: {int(peak_hour)}:00  ({hourly['mean'].max():.4f} kWh mean)")
    log(f"  Trough hour: {int(trough_hour)}:00  ({hourly['mean'].min():.4f} kWh mean)")
    return {
        "by_hour": result,
        "peak_hour": int(peak_hour),
        "trough_hour": int(trough_hour),
        "peak_mean_kwh": float(hourly["mean"].max()),
        "trough_mean_kwh": float(hourly["mean"].min()),
        "peak_to_trough_ratio": float(hourly["mean"].max() / hourly["mean"].min()),
    }


# ── Section 4: Day-of-week pattern ────────────────────────────────────────────
def dow_pattern(df: pd.DataFrame) -> dict:
    log("Section 4: Day-of-week pattern")
    DOW_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    dow = df.groupby("dayofweek")["energy_kwh"].agg(["mean", "median", "std"]).reset_index()
    result = {}
    for _, row in dow.iterrows():
        d = int(row["dayofweek"])
        result[str(d)] = {
            "day_name": DOW_NAMES.get(d, str(d)),
            "mean_kwh": float(row["mean"]),
            "median_kwh": float(row["median"]),
            "std_kwh": float(row["std"]),
        }
    weekday_mean = float(df[df["is_weekend"] == 0]["energy_kwh"].mean())
    weekend_mean = float(df[df["is_weekend"] == 1]["energy_kwh"].mean())
    # Kruskal-Wallis test across days of week (non-parametric)
    groups = [df[df["dayofweek"] == d]["energy_kwh"].values for d in sorted(df["dayofweek"].unique())]
    kw_stat, kw_p = scipy_stats.kruskal(*groups)
    log(f"  Weekday mean: {weekday_mean:.4f} kWh,  Weekend mean: {weekend_mean:.4f} kWh")
    log(f"  Kruskal-Wallis across days: stat={kw_stat:.2f}, p={kw_p:.4f}")
    return {
        "by_dayofweek": result,
        "weekday_mean_kwh": weekday_mean,
        "weekend_mean_kwh": weekend_mean,
        "weekend_vs_weekday_pct": float((weekend_mean - weekday_mean) / weekday_mean * 100),
        "kruskal_wallis_stat": float(kw_stat),
        "kruskal_wallis_p": float(kw_p),
        "significant_dow_effect": kw_p < 0.05,
    }


# ── Section 5: Monthly / seasonal pattern ─────────────────────────────────────
def monthly_pattern(df: pd.DataFrame) -> dict:
    log("Section 5: Monthly / seasonal pattern")
    MONTH_NAMES = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May",
        6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct",
        11: "Nov", 12: "Dec",
    }
    monthly = df.groupby("month")["energy_kwh"].agg(["mean", "median", "std", "count"]).reset_index()
    result = {}
    for _, row in monthly.iterrows():
        m = int(row["month"])
        result[str(m)] = {
            "month_name": MONTH_NAMES[m],
            "mean_kwh": float(row["mean"]),
            "median_kwh": float(row["median"]),
            "std_kwh": float(row["std"]),
            "n_obs": int(row["count"]),
        }
    peak_month = monthly.loc[monthly["mean"].idxmax(), "month"]
    trough_month = monthly.loc[monthly["mean"].idxmin(), "month"]
    log(f"  Peak month: {MONTH_NAMES[int(peak_month)]}  ({monthly['mean'].max():.4f} kWh)")
    log(f"  Trough month: {MONTH_NAMES[int(trough_month)]}  ({monthly['mean'].min():.4f} kWh)")
    return {
        "by_month": result,
        "peak_month": int(peak_month),
        "trough_month": int(trough_month),
        "peak_mean_kwh": float(monthly["mean"].max()),
        "trough_mean_kwh": float(monthly["mean"].min()),
    }


# ── Section 6: Temperature–energy correlation ─────────────────────────────────
def temperature_correlation(df: pd.DataFrame) -> dict:
    log("Section 6: Temperature–energy correlation")
    # Overall Pearson and Spearman
    pearson_r, pearson_p = scipy_stats.pearsonr(df["temp_c"], df["energy_kwh"])
    spearman_r, spearman_p = scipy_stats.spearmanr(df["temp_c"], df["energy_kwh"])

    # Per-household correlations
    per_apt = {}
    for apt_id, grp in df.groupby("apt"):
        r, p = scipy_stats.pearsonr(grp["temp_c"], grp["energy_kwh"])
        per_apt[str(apt_id)] = {"pearson_r": float(r), "pearson_p": float(p)}

    log(f"  Overall Pearson r={pearson_r:.4f} (p={pearson_p:.2e})")
    log(f"  Overall Spearman r={spearman_r:.4f} (p={spearman_p:.2e})")

    return {
        "overall_pearson_r": float(pearson_r),
        "overall_pearson_p": float(pearson_p),
        "overall_spearman_r": float(spearman_r),
        "overall_spearman_p": float(spearman_p),
        "significant_correlation": pearson_p < 0.05,
        "per_household_pearson": per_apt,
    }


# ── Section 7: Pre/post-intervention energy comparison ────────────────────────
def pre_post_analysis(df: pd.DataFrame) -> dict:
    log("Section 7: Pre/post-intervention comparison")
    pre = df[df["post"] == 0]["energy_kwh"]
    post = df[df["post"] == 1]["energy_kwh"]
    mw_stat, mw_p = scipy_stats.mannwhitneyu(pre, post, alternative="two-sided")
    log(f"  Pre mean: {pre.mean():.4f}  Post mean: {post.mean():.4f}")
    log(f"  Mann-Whitney U: stat={mw_stat:.1f}, p={mw_p:.4f}")
    return {
        "pre_n": int(len(pre)),
        "post_n": int(len(post)),
        "pre_mean_kwh": float(pre.mean()),
        "post_mean_kwh": float(post.mean()),
        "post_vs_pre_pct": float((post.mean() - pre.mean()) / pre.mean() * 100),
        "mannwhitney_u_stat": float(mw_stat),
        "mannwhitney_p": float(mw_p),
        "significant_change": mw_p < 0.05,
    }


# ── Section 8: Temporal gap characterisation ──────────────────────────────────
def gap_analysis(df: pd.DataFrame) -> dict:
    log("Section 8: Temporal gap analysis")
    expected_hours = 6839  # from preprocessing report
    gap_summary = {}
    total_missing = 0

    for apt_id, grp in df.groupby("apt"):
        grp_sorted = grp.sort_values("timestamp")
        gaps = grp_sorted["timestamp"].diff().dropna()
        gap_hours = gaps.dt.total_seconds() / 3600

        n_obs = int(len(grp_sorted))
        missing_hrs = expected_hours - n_obs
        total_missing += missing_hrs

        non_hourly = gap_hours[gap_hours != 1.0]
        gap_summary[str(apt_id)] = {
            "n_obs": n_obs,
            "expected_obs": expected_hours,
            "missing_hours": int(missing_hrs),
            "coverage_pct": round(n_obs / expected_hours * 100, 1),
            "n_gap_events": int(len(non_hourly)),
            "max_gap_hours": float(gap_hours.max()) if len(gap_hours) else 0,
        }

    coverages = [v["coverage_pct"] for v in gap_summary.values()]
    log(f"  Average coverage: {np.mean(coverages):.1f}%  Range: {min(coverages):.1f}%–{max(coverages):.1f}%")
    return {
        "expected_hours_per_household": expected_hours,
        "total_missing_household_hours": int(total_missing),
        "avg_coverage_pct": float(np.mean(coverages)),
        "min_coverage_pct": float(min(coverages)),
        "max_coverage_pct": float(max(coverages)),
        "by_household": gap_summary,
    }


# ── Section 9: Z-score distribution (global baseline) ────────────────────────
def zscore_analysis(df: pd.DataFrame) -> dict:
    """
    Compute Z-scores using per-household mean and std.
    This is the simplest anomaly signal; EDA characterises its distribution.
    No anomaly labels are assigned here — that is T006 work.
    """
    log("Section 9: Z-score distribution (per-household, global baseline)")
    df = df.copy()

    apt_stats = df.groupby("apt")["energy_kwh"].agg(["mean", "std"]).rename(
        columns={"mean": "apt_mean", "std": "apt_std"}
    )
    df = df.join(apt_stats, on="apt")
    df["zscore_global"] = (df["energy_kwh"] - df["apt_mean"]) / df["apt_std"]

    z = df["zscore_global"].dropna()
    n_above_2 = int((z.abs() > 2).sum())
    n_above_3 = int((z.abs() > 3).sum())
    n_above_4 = int((z.abs() > 4).sum())

    log(f"  Z>2: {n_above_2} ({n_above_2/len(z)*100:.1f}%)  Z>3: {n_above_3}  Z>4: {n_above_4}")

    # Per-household z-score stats
    per_apt = {}
    for apt_id, grp in df.groupby("apt"):
        zz = grp["zscore_global"].dropna()
        per_apt[str(apt_id)] = {
            "n_z_above_2": int((zz.abs() > 2).sum()),
            "n_z_above_3": int((zz.abs() > 3).sum()),
            "max_z": float(zz.max()),
            "min_z": float(zz.min()),
        }

    return {
        "note": "Z-scores use per-household mean and std. This is the global (full-period) baseline, not a rolling baseline.",
        "total_obs": int(len(z)),
        "n_z_above_2": n_above_2,
        "pct_z_above_2": float(n_above_2 / len(z) * 100),
        "n_z_above_3": n_above_3,
        "pct_z_above_3": float(n_above_3 / len(z) * 100),
        "n_z_above_4": n_above_4,
        "pct_z_above_4": float(n_above_4 / len(z) * 100),
        "per_household": per_apt,
    }


# ── Section 10: IQR fence counts (per-household) ──────────────────────────────
def iqr_analysis(df: pd.DataFrame) -> dict:
    log("Section 10: IQR fence analysis (per-household)")
    per_apt = {}
    for apt_id, grp in df.groupby("apt"):
        e = grp["energy_kwh"]
        q25, q75 = e.quantile(0.25), e.quantile(0.75)
        iqr = q75 - q25
        upper_15 = q75 + 1.5 * iqr
        upper_30 = q75 + 3.0 * iqr
        per_apt[str(apt_id)] = {
            "q25": float(q25),
            "q75": float(q75),
            "iqr": float(iqr),
            "upper_fence_1_5": float(upper_15),
            "upper_fence_3_0": float(upper_30),
            "n_above_1_5_iqr": int((e > upper_15).sum()),
            "n_above_3_0_iqr": int((e > upper_30).sum()),
            "pct_above_1_5_iqr": float((e > upper_15).sum() / len(e) * 100),
        }
    log(f"  IQR fence analysis complete for {len(per_apt)} households.")
    return {"per_household": per_apt}


# ── Section 11: Statistical method recommendations ────────────────────────────
def method_recommendations(
    dist: dict, hourly: dict, dow: dict, temp_corr: dict
) -> dict:
    log("Section 11: Statistical method recommendations")
    recs = []

    # Distribution shape
    if not dist["normally_distributed_raw"]:
        recs.append("energy_kwh is NOT normally distributed (heavy-tailed, right-skewed). Use median/IQR rather than mean/std for robust baselines.")
    if dist["log_normally_distributed"] or abs(dist["log_skewness"]) < 0.5:
        recs.append("lnenergy (log-kWh) is approximately log-normally distributed. Regression and Z-scores on log scale are appropriate.")

    # Hourly pattern
    if hourly["peak_to_trough_ratio"] > 1.5:
        recs.append(f"Strong time-of-day effect (peak/trough ratio={hourly['peak_to_trough_ratio']:.2f}x). Baseline model must condition on hour-of-day.")

    # Day-of-week
    if dow["significant_dow_effect"]:
        recs.append("Significant day-of-week effect (Kruskal-Wallis p<0.05). Baseline must include day-of-week.")

    # Temperature
    if abs(temp_corr["overall_pearson_r"]) > 0.1:
        recs.append(f"Temperature is correlated with energy (Pearson r={temp_corr['overall_pearson_r']:.3f}). Include temp_c as a predictor in the regression baseline.")

    # Gaps
    recs.append("Temporal gaps (missing hours) are present in all households. Rolling features must use a minimum-observations guard to avoid misleading baselines over gaps.")

    # Anomaly method set
    recs.append("Recommended anomaly signals: (1) per-household Z-score on lnenergy, (2) IQR fence on energy_kwh, (3) residual from rolling-window or regression-predicted baseline.")

    log(f"  Generated {len(recs)} method recommendations.")
    return {"recommendations": recs}


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log("=" * 60)
    log("SmartWatt India — EDA (T005)")
    log("=" * 60)

    df = load_data()

    report = {}
    report["run_at_utc"] = datetime.now(tz=timezone.utc).isoformat()
    report["input_file"] = str(INPUT_CSV.relative_to(REPO_ROOT))
    report["n_rows"] = int(len(df))
    report["n_households"] = int(df["apt"].nunique())

    report["energy_distribution"] = energy_distribution(df)
    report["per_household_stats"] = per_household_stats(df)
    report["hourly_pattern"] = hourly_pattern(df)
    report["dow_pattern"] = dow_pattern(df)
    report["monthly_pattern"] = monthly_pattern(df)
    report["temperature_correlation"] = temperature_correlation(df)
    report["pre_post_analysis"] = pre_post_analysis(df)
    report["gap_analysis"] = gap_analysis(df)
    report["zscore_analysis"] = zscore_analysis(df)
    report["iqr_analysis"] = iqr_analysis(df)
    report["method_recommendations"] = method_recommendations(
        report["energy_distribution"],
        report["hourly_pattern"],
        report["dow_pattern"],
        report["temperature_correlation"],
    )

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report, f, indent=2, default=str)

    log("=" * 60)
    log(f"EDA report written → {OUTPUT_REPORT}")
    log("T005 COMPLETE")
    log("=" * 60)

    # Print key findings for immediate review
    print("\n=== KEY EDA FINDINGS ===")
    e = report["energy_distribution"]
    h = report["hourly_pattern"]
    d = report["dow_pattern"]
    tc = report["temperature_correlation"]
    z = report["zscore_analysis"]
    print(f"Energy distribution: mean={e['mean']:.4f} kWh, median={e['median']:.4f} kWh, std={e['std']:.4f}")
    print(f"  Skewness: {e['skewness']:.3f}  (log-scale skewness: {e['log_skewness']:.3f})")
    print(f"  Log-normally distributed: {e['log_normally_distributed']}")
    print(f"  Tukey high-outliers (1.5×IQR): {e['n_tukey_high_outliers']} ({e['pct_tukey_high']:.1f}%)")
    print(f"Hour-of-day: peak={h['peak_hour']}:00 ({h['peak_mean_kwh']:.4f} kWh), trough={h['trough_hour']}:00 ({h['trough_mean_kwh']:.4f} kWh)")
    print(f"Day-of-week: significant={d['significant_dow_effect']}  weekend vs weekday: {d['weekend_vs_weekday_pct']:+.1f}%")
    print(f"Temperature Pearson r={tc['overall_pearson_r']:.4f}  p={tc['overall_pearson_p']:.2e}")
    print(f"Z-score >2 (per-household): {z['n_z_above_2']} ({z['pct_z_above_2']:.1f}%)")
    print(f"Z-score >3: {z['n_z_above_3']} ({z['pct_z_above_3']:.1f}%)")
    print("\nMethod recommendations:")
    for r in report["method_recommendations"]["recommendations"]:
        print(f"  • {r}")


if __name__ == "__main__":
    main()
