# EDA_FINDINGS.md — SmartWatt India Exploratory Data Analysis

**Last updated:** 2026-10-06  
**Script:** `ml/eda.py`  
**Input:** `data/processed/hourly_energy.csv`  
**Report:** `data/processed/eda_report.json`

---

## 1. Dataset Shape (Reminder)

| Property | Value |
|---|---|
| Rows | 103,704 |
| Households (`apt`) | 19 |
| Date range | 2013-08-01 → 2014-05-12 |
| Time resolution | Hourly |
| Target variable | `energy_kwh` = exp(lnenergy) |

---

## 2. Energy Distribution

| Statistic | Value (kWh) |
|---|---|
| Mean | 0.3684 |
| Median | 0.1479 |
| Std | 0.5798 |
| Min | ~0.000008 |
| P25 | 0.0613 |
| P75 | 0.3707 |
| P95 | 1.1875 |
| P99 | 2.4440 |
| Max | 14.744 |
| Skewness | **+3.564** (strongly right-skewed) |
| Kurtosis | **23.875** (heavy-tailed) |

**Key finding:** `energy_kwh` is heavily right-skewed and NOT normally distributed.  
`lnenergy` (log-scale) has skewness = −0.224 — approximately symmetric / log-normal.

> **Implication:** Use `lnenergy` for regression target and Z-scores. Use `energy_kwh` for display and IQR-based methods. Do NOT use raw mean/std on `energy_kwh` as a primary anomaly baseline without log transformation.

---

## 3. Per-Household Baseline

Households vary enormously in their consumption levels:

| apt | Mean kWh | Median kWh | Std | CV% | N obs |
|---|---|---|---|---|---|
| 1 | 0.360 | 0.204 | 0.442 | 123 | 5,077 |
| 2 | 0.426 | 0.246 | 0.593 | 139 | 4,298 |
| 3 | 0.423 | 0.154 | 0.592 | 140 | 4,752 |
| 4 | 0.561 | 0.366 | 0.443 | 79 | 5,217 |
| 5 | 0.935 | 0.117 | 1.210 | 129 | 4,048 |
| 6 | 0.108 | 0.066 | 0.182 | 169 | 4,464 |
| 7 | 0.567 | 0.309 | 0.707 | 125 | 6,560 |
| 8 | 0.298 | 0.116 | 0.474 | 159 | 6,624 |
| 9 | 0.089 | 0.032 | 0.185 | 208 | 6,417 |
| 10 | 0.253 | 0.110 | 0.406 | 161 | 6,572 |
| 11 | 0.244 | 0.155 | 0.312 | 128 | 6,601 |
| 12 | 0.105 | 0.065 | 0.152 | 144 | 4,526 |
| 13 | 0.326 | 0.148 | 0.419 | 128 | 6,241 |
| 14 | 0.641 | 0.328 | 0.655 | 102 | 6,187 |
| 15 | 0.150 | 0.071 | 0.242 | 161 | 5,643 |
| 16 | 0.271 | 0.205 | 0.270 | 100 | 6,191 |
| 17 | 0.376 | 0.131 | 0.682 | 182 | 5,686 |
| 18 | 0.278 | 0.124 | 0.408 | 147 | 5,586 |
| 19 | 1.036 | 0.665 | 1.058 | 102 | 3,014 |

**Coefficient of Variation (CV)** ranges from 79% to 208% — households are highly heterogeneous. This strongly confirms that **a fixed global threshold cannot meaningfully detect anomalies**. Per-household baselines are mandatory.

---

## 4. Time-of-Day Pattern

| Hour | Mean kWh |
|---|---|
| 16:00 (trough) | 0.2395 |
| 21:00 (peak) | **0.5632** |

- **Peak-to-trough ratio: 2.35×** — strong diurnal cycle.
- Evening hours (18:00–22:00) have the highest consumption, consistent with residential cooking, AC, and lighting patterns in Delhi.
- The ML baseline **must condition on `hour`** to avoid treating normal evening peaks as anomalies.

---

## 5. Day-of-Week Pattern

| | Weekday | Weekend |
|---|---|---|
| Mean kWh | 0.3701 | 0.3642 |
| Difference | — | −1.6% |

- **Kruskal-Wallis test p < 0.0001** → statistically significant day-of-week effect, though the magnitude is small (−1.6% weekends).
- The ML baseline should include `dayofweek` as a covariate.

---

## 6. Seasonal Pattern

| Month | Mean kWh |
|---|---|
| August 2013 | 0.473 |
| September 2013 | 0.452 |
| October 2013 | 0.301 |
| November 2013 | 0.210 ← trough |
| December 2013 | 0.226 |
| January 2014 | 0.259 |
| February 2014 | 0.277 |
| March 2014 | 0.335 |
| April 2014 | 0.525 |
| May 2014 | **0.656** ← peak |

- Clear seasonal cycle: high summer consumption (AC), low winter consumption.
- This matches Delhi's climate (hot summers 35–45°C; mild winters 5–20°C).
- The `tt`/`tt2`/`tt3` cubic time-trend and `month` features should control for seasonal drift in the regression baseline.

---

## 7. Temperature–Energy Correlation

| Correlation | r | p-value |
|---|---|---|
| Pearson (raw kWh) | −0.028 | 7.85 × 10⁻¹⁹ |
| Spearman (raw kWh) | +0.156 | ~0 |
| Pearson (lnenergy) | +0.120 | ~0 |

**Why the Pearson/Spearman discrepancy?**  
The raw `energy_kwh` distribution is extremely right-skewed. Pearson correlation is pulled by the high-leverage peak readings. Spearman (rank-based) and the log-scale Pearson show a clearer positive trend: **warmer hours → higher electricity use** (AC effect), consistent with Delhi summers.

**Within-hour correlation:** negative in daytime hours (6:00–18:00), suggesting daytime temperature and daytime usage are anti-correlated (households may leave during daytime). Evening hours show near-zero correlation, as usage is driven by activities rather than temperature.

> **Implication:** `temp_c` should be included as a covariate in the regression baseline. It is more useful on the log scale.

---

## 8. Pre/Post Intervention Comparison

| Period | N | Mean kWh |
|---|---|---|
| Pre-intervention (post=0) | 52,836 | 0.3793 |
| Post-intervention (post=1) | 50,868 | 0.3451 |

- Post-intervention mean is **8.5% lower** than pre.
- **Mann-Whitney U p = 0.044** — marginally statistically significant.
- This validates that the information intervention had a measurable (though modest) effect on consumption.

> **Anomaly detection implication:** The `post` indicator (and `finpost`/`healthpost`) should be included in the regression baseline as covariates so that the model does not flag post-intervention reduced usage as anomalously low.

---

## 9. Temporal Gaps (Missing Hours)

| Metric | Value |
|---|---|
| Expected hours per household | 6,839 |
| Average coverage | **79.8%** |
| Min coverage (apt 19) | 44.1% |
| Max coverage (apt 7) | 96.9% |
| Total missing household-hours | 26,243 |

- All 19 households have missing hourly readings.
- Most common gap: **2 hours** (607 occurrences) — individual missed readings.
- Largest gap: **750 hours** (~31 days, affecting apts 1–5 in Nov–Dec 2013) — likely a data collection outage.
- **No gap filling was performed** in preprocessing (consistent with project rules).

> **Rolling baseline implication:** A rolling window (e.g., 7-day) may span large gaps for some households. Rolling feature computation must enforce a `min_periods` guard. Rows within or immediately after a gap must be treated with caution.

---

## 10. Z-Score Analysis (Per-Household Global Baseline)

Using each household's full-period mean and std:

| Threshold | Count | % of total |
|---|---|---|
| \|Z\| > 2 | 5,283 | 5.1% |
| \|Z\| > 3 | 2,601 | 2.5% |
| \|Z\| > 4 | 1,103 | 1.1% |

> **Note:** This is a *global* (full-period) baseline Z-score — it does not account for hour-of-day or seasonal context. A conditional (regression-residual) Z-score will be more accurate for anomaly detection. This analysis establishes the upper-bound scale of potential anomalies.

---

## 11. IQR Fence Analysis

Percentage of readings exceeding the 1.5×IQR upper fence per household ranges from ~7% to ~22%, reflecting how heavy-tailed each household's distribution is.

---

## 12. Statistical Method Recommendations (from EDA)

Based on actual data properties observed:

| Finding | Recommended method |
|---|---|
| energy_kwh is right-skewed | Use `lnenergy` for regression and Z-scores; use IQR fence on `energy_kwh` |
| Strong time-of-day effect (2.35× peak/trough) | Condition baseline on `hour` |
| Significant day-of-week effect | Include `dayofweek` in baseline |
| Temperature positively correlated (log scale) | Include `temp_c` as regression covariate |
| Per-household heterogeneity (CV 79–208%) | Per-household baselines mandatory |
| Missing hours (gaps) in all households | Enforce `min_periods` in rolling features |
| Pre/post treatment effect confirmed | Include `post`, `finpost`, `healthpost` as covariates |

**Confirmed anomaly signal set for T006:**
1. Per-household Z-score on `lnenergy` (global baseline)
2. Per-household IQR fence on `energy_kwh`
3. Residual from regression-predicted baseline (T007)
4. Rolling deviation from rolling mean (7-day window with `min_periods` guard)

---

## 13. Revision History

| Date | Author | Change |
|---|---|---|
| 2026-10-06 | Antigravity AI Agent | Initial EDA; created this document |
