# DATASET.md — SmartWatt India Dataset Documentation

**Last updated:** 2026-10-06  
**Inspection performed by:** Antigravity AI Agent (automated Python inspection)  
**Source:** Harvard Dataverse — DOI [10.7910/DVN/7MEXN4](https://doi.org/10.7910/DVN/7MEXN4)  
**Full citation:** "Dataset on Information Strategies for Energy Conservation: A Field Experiment in India"  
**Raw data location:** `data/raw/Data_Do_Files_For_Data_Brief_09-15-2017/Data/`  
**⚠ CRITICAL: The raw data files must NEVER be modified.**

---

## 1. Study Background

This dataset comes from a randomised controlled field experiment on Indian residential households (apartments) in Delhi. Households received either a **financial** or **health-framing** information intervention about electricity conservation. The study measured electricity consumption before and after the intervention at sub-hourly resolution.

The dataset is **not** a general-purpose electricity monitoring dataset — it is a **panel experiment dataset** with treatment indicators baked in. For anomaly detection, we use the meter readings as household-level time series and treat the treatment variables as contextual covariates.

---

## 2. File Inventory

All 14 `.dta` (Stata) files confirmed present under `Data/`.

| File | Size (MB) | Rows | Cols | Resolution | Households | Notes |
|---|---|---|---|---|---|---|
| `Table_9_2_Final.dta` | 7.04 | 199,379 | 14 | 30-min | 19 | 30-min panel (robustness) |
| `Table_9_3_Final.dta` | 3.66 | 103,704 | 14 | **Hourly** | 19 | **✅ PRIMARY ML TABLE** |
| `Table_9_4_Final.dta` | 0.20 | 4,802 | 13 | **Daily** | 19 | Daily aggregation |
| `Table_A1_Final.dta` | 0.28 | 1,820 | 12 | Survey | — | Survey/behavioral data |
| `Table_A2_Final.dta` | 15.77 | 375,805 | 14 | 15-min | 19 | Full 15-min panel |
| `Table_A3_1_Final.dta` | 12.55 | 375,805 | 12 | 15-min | 19 | Full sample subset |
| `Table_A3_2_Final.dta` | 11.95 | 357,893 | 12 | 15-min | 18 | Dropped 0-email apt |
| `Table_A3_3_Final.dta` | 12.14 | 363,530 | 12 | 15-min | 18 | Dropped double-apt |
| `Table_A4_1_Final.dta` | 13.26 | 375,805 | 14 | 15-min | 19 | Full sample |
| `Table_A4_2_Final.dta` | 12.63 | 357,893 | 14 | 15-min | 18 | Dropped 0-email apt |
| `Table_A4_3_Final.dta` | 12.83 | 363,530 | 14 | 15-min | 18 | Dropped double-apt |
| `Table_A5_1_Final.dta` | 13.26 | 375,805 | 14 | 15-min | 19 | Full sample |
| `Table_A5_2_Final.dta` | 12.63 | 357,893 | 14 | 15-min | 18 | Dropped 0-email apt |
| `Table_A5_3_Final.dta` | 12.83 | 363,530 | 14 | 15-min | 18 | Dropped double-apt |

> **Note:** No `Table_9_1_Final.dta` exists (referenced in the original `Table_9.do` do-file but not present in the Dataverse release). This is a pre-analysis dataset limitation and does not affect the project.

---

## 3. Primary Table: `Table_9_3_Final.dta` (Hourly)

Recommended primary table for the ML pipeline.

### 3.1 Column Schema

| Column | Type | Missing | Unique values | Description |
|---|---|---|---|---|
| `apt` | int16 | 0% | 19 | Household/apartment identifier (panel key) |
| `timestamp` | datetime64[ms] | 0% | 6,805 | Hourly timestamp (parsed automatically by pandas) |
| `hour` | int8 | 0% | 24 | Hour of day (0–23) |
| `dayofweek` | int8 | 0% | 7 | Day of week |
| `post` | int8 | 0% | 2 | 1 = post-intervention period |
| `finpost` | int8 | 0% | 2 | 1 = financial treatment group × post period |
| `healthpost` | int8 | 0% | 2 | 1 = health treatment group × post period |
| `ga_fin_1` | int8 | 0% | 5 | Graduated financial treatment intensity (0–4) |
| `ga_health_1` | int8 | 0% | 5 | Graduated health treatment intensity (0–4) |
| `hour_temp` | int16 | 0% | 67 | Hourly temperature (°F, range 41–107°F) |
| `tt` | int16 | 0% | 285 | Linear time trend counter |
| `tt2` | int32 | 0% | 285 | Quadratic time trend (tt²) |
| `tt3` | int32 | 0% | 285 | Cubic time trend (tt³) |
| `lnenergy` | float64 | 0% | 64,617 | **ln(hourly kWh)** — primary energy variable |

### 3.2 Key Statistics

```
Shape:              103,704 rows × 14 columns
Households:         19 apartments (apt = 1 to 19)
Date range:         2013-08-01 01:00:00  →  2014-05-12 23:00:00
Time resolution:    Hourly (1-hour median gap, confirmed)
Obs per household:  ~5,458
Missing values:     NONE (0 in every column)
Duplicate rows:     NONE (0)
```

### 3.3 Energy Variable — `lnenergy`

`lnenergy` = natural logarithm of hourly kWh consumption.

**lnenergy statistics:**

| Stat | Value |
|---|---|
| count | 103,704 |
| mean | −1.862 |
| std | 1.361 |
| min | −11.760 |
| 25th pct | −2.791 |
| median | −1.911 |
| 75th pct | −0.992 |
| max | 2.691 |

**Back-calculated kWh = exp(lnenergy):**

| Stat | kWh |
|---|---|
| mean | 0.368 |
| std | 0.580 |
| min | ~0.000008 |
| 25th pct | 0.061 |
| median | 0.148 |
| 75th pct | 0.371 |
| max | 14.744 |

> Preprocessing will compute `energy_kwh = np.exp(df['lnenergy'])` and work in kWh units. Log-scale may be reapplied for regression targets.

### 3.4 Temperature Variable — `hour_temp`

- Unit: **Fahrenheit** (integer)
- Range: 41–107°F (~5–42°C)
- Represents hourly ambient temperature in Delhi.
- Preprocessing: convert to Celsius via `(hour_temp - 32) × 5/9`.

### 3.5 Time Coverage

- **Start:** 2013-08-01 (August — late monsoon, Delhi)
- **End:** 2014-05-12 (May — pre-monsoon / early summer, Delhi)
- **Span:** ~9.5 months
- **Seasons:** Late monsoon → winter → spring → early summer

---

## 4. Secondary Table: `Table_A2_Final.dta` (15-Minute, Full Sample)

Finest available time resolution.

| Property | Value |
|---|---|
| Shape | 375,805 × 14 |
| Households | 19 |
| Time resolution | **15 minutes** |
| Date range | 2013-08-01 00:15 → 2014-05-12 23:45 |
| Extra column | `pctmissing` — % of 15-min slots imputed per hour (values: 0, 25, 50, 75) |
| `week` | Week-number column (1–41) |
| Missing values | 0 |

> Use this table if 15-min granularity is needed. The `pctmissing` field is the only available data quality signal; rows with `pctmissing > 0` should be flagged in processing.

---

## 5. Daily Table: `Table_9_4_Final.dta`

| Property | Value |
|---|---|
| Shape | 4,802 × 13 |
| Households | 19 |
| Resolution | **Daily** |
| Date range | 2013-08-02 → 2014-05-12 |
| Temperature | `mean_daily_temp` (daily mean °F) |
| Missing | 0 |

`lnenergy` here = ln(daily total kWh). Useful for daily-level EDA and daily anomaly scoring.

---

## 6. Survey / Behavioral Table: `Table_A1_Final.dta`

| Property | Value |
|---|---|
| Shape | 1,820 × 12 |
| Key | `id1` (string respondent ID) |
| Time | None — cross-sectional survey |

**Columns:** `id1`, `unplug_appliances`, `buy_energy_efficient`, `turnoff_ac`, `switchoff_lights`, `change_appliance_setting`, `mot_*` (motivation codes), `subsample`.

> No meter readings. No `apt` column. Cannot be joined to the energy panel tables without an `apt` ↔ `id1` crosswalk (not publicly released). This table is **not usable** in the ML pipeline.

---

## 7. Robustness Variant Tables (A3, A4, A5)

All six `Table_A3_*`, `Table_A4_*`, `Table_A5_*` tables are **15-minute** panel data differing only in sample composition:

| Suffix | Sample |
|---|---|
| `_1` | Full sample — 19 apartments |
| `_2` | Dropped 1 apartment with 0 emails opened — 18 apartments |
| `_3` | Dropped 1 "double apartment" — 18 apartments |

Treatment variable encoding differs slightly between A3, A4, A5 (`ga_fin_1`/`ga_health_1` vs `mc_fin`/`mc_health`).

> For MVP: use `Table_A3_1_Final.dta` as the secondary 15-min reference if sub-hourly granularity is required.

---

## 8. Household Identifier

| Property | Value |
|---|---|
| Column | `apt` |
| Type | int16 |
| Range | 1–19 |
| Count | 19 unique apartments |
| Missing | 0 |

---

## 9. Timestamp Details

| Property | Value |
|---|---|
| Column | `timestamp` |
| Parsed type | `datetime64[ms]` (auto-parsed by `pd.read_stata`) |
| Timezone | Not encoded; assumed IST (UTC+5:30) |

Feature engineering will extract: `month`, `week_of_year`, `is_weekend` from `timestamp`.

---

## 10. Treatment and Context Variables

| Column | Description |
|---|---|
| `post` | 1 = post-treatment period, 0 = baseline |
| `finpost` | Financial treatment group × post period interaction |
| `healthpost` | Health treatment group × post period interaction |
| `ga_fin_1` | Graduated financial treatment (5 levels: 0–4) |
| `ga_health_1` | Graduated health treatment (5 levels: 0–4) |
| `tt`, `tt2`, `tt3` | Time trend polynomial (controls secular drift) |

> **ML note:** Treatment variables should be included as covariates in the regression baseline so that model residuals reflect genuine consumption anomalies rather than intervention effects.

---

## 11. Data Quality

| Table group | Missing | Duplicates | `pctmissing` available |
|---|---|---|---|
| All energy panel tables | **0** | **0** | Only Table_A2 |

The original authors pre-imputed the data before Dataverse release. Zero missing values reflects this. The `pctmissing` column (Table_A2 only) shows the degree of imputation per record.

---

## 12. Target Variable Summary

| Use case | Variable | Notes |
|---|---|---|
| ML regression target | `lnenergy` | Log-normal; standard in original study |
| Anomaly scoring | `energy_kwh = exp(lnenergy)` | Interpretable kWh units |
| Statistical features | `energy_kwh` | Z-score, IQR, rolling stats on kWh scale |

**Recommended target for modelling: `lnenergy`** (back-transform predictions to kWh for display).

---

## 13. Recommended Primary Dataset

> **✅ Primary: `Table_9_3_Final.dta` (hourly, 19 apartments)**

Reasons:
1. Hourly resolution — good balance of granularity and tractability
2. Smallest useful file (103K rows vs 375K for 15-min)
3. No missing values
4. All required features present: `apt`, `timestamp`, `hour`, `dayofweek`, `hour_temp`, treatment vars, time trend
5. Used in the original paper's primary Table 9 regression

> **Secondary: `Table_A2_Final.dta`** if 15-min granularity is needed.

---

## 14. Required Preprocessing Steps

Based on this inspection, `ml/preprocess.py` must:

1. Load `Table_9_3_Final.dta` with `pd.read_stata(..., convert_categoricals=False)`.
2. Compute `energy_kwh = np.exp(df['lnenergy'])`.
3. Convert temperature: `temp_c = (df['hour_temp'] - 32) * 5/9`.
4. Sort by `['apt', 'timestamp']` (no random shuffle — chronological only).
5. Extract: `month`, `week_of_year`, `is_weekend` from `timestamp`.
6. Save to `data/processed/hourly_energy.csv`.
7. Optionally join `pctmissing` from `Table_A2` as a quality flag.

---

## 15. Anomaly Detection Implications

| Finding | Implication |
|---|---|
| 19 apartments only | Per-household baselines are computationally trivial |
| ~5,458 hourly obs/apt | Sufficient for rolling stats (e.g. 7-day window = 168 points) |
| Zero missing values | No imputation step needed |
| `hour_temp` in °F | Must convert to °C in preprocessing |
| `lnenergy` is log-scale | Z-scores can be computed on log or kWh scale |
| Treatment vars present | Include as covariates so model residuals ≈ genuine anomalies |
| `tt`, `tt2`, `tt3` | Include in regression to control seasonal secular drift |

---

## 16. What Is NOT in the Dataset

- No appliance-level sub-metering
- No voltage / current / power factor readings
- No household demographic data (floor area, occupant count, income)
- No `apt` ↔ respondent crosswalk (Table_A1 cannot be merged to energy tables)
- No real-time streaming or IoT component
- No geographic metadata beyond "Delhi residential"

---

## 17. Revision History

| Date | Author | Change |
|---|---|---|
| 2026-10-06 | Antigravity AI Agent | Initial dataset inspection; created this document |
