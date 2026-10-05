# Architecture Decisions

## ADR-001: Use Indian household dataset
Decision: Use the IIIT-Delhi/New Delhi residential electricity field-experiment dataset.
Reason: It provides actual kWh consumption, weather and household context, unlike the RESIDE-AC dataset whose core electrical measurements are current rather than direct kWh.

## ADR-002: Hourly modeling
Decision: Use hourly observations for the main ML pipeline.
Reason: Smaller, compatible with hourly weather, and sufficient for a 2–3 day project while preserving meaningful daily patterns.

## ADR-003: No database in MVP
Decision: Bundle processed data/model artifacts with backend.
Reason: Read-only academic demo; avoids unnecessary database deployment and free-tier persistence issues.

## ADR-004: FastAPI backend
Decision: Use FastAPI rather than Node/Express.
Reason: ML/data processing is Python-native, avoiding a second ML runtime/service.

## ADR-005: Render for deployment
Decision: Render static frontend + Render backend web service.
Reason: Both service types are supported on free plans and can be deployed from one repository. Free backend cold starts must be handled in UX.

## ADR-006: Statistical evidence before ML complexity
Decision: Statistical anomaly methods are first-class; ML is used for expected-usage prediction.
Reason: Course objective is Statistics for ML and DS, and the project must remain explainable.

## ADR-007: Primary dataset confirmed as Table_9_3_Final.dta (hourly)
Decision: Use Table_9_3_Final.dta as the primary ML dataset.
Reason: Post-inspection finding. It is the hourly-resolution panel (103,704 rows, 19 apartments, 2013-08-01 to 2014-05-12, zero missing values). It is the smallest file that covers the full period at a meaningful resolution, and it is the table used in the paper's primary Table 9 regression. The 15-min table (Table_A2_Final.dta) is designated secondary.
Date: 2026-10-06

## ADR-008: Energy variable is lnenergy = ln(kWh); work in kWh space for anomaly detection
Decision: Preprocessing will compute energy_kwh = exp(lnenergy) for anomaly scoring, and convert hour_temp from Fahrenheit to Celsius.
Reason: Raw kWh is interpretable to users; log form is appropriate for regression targets. Temperature °F is not standard in India — convert to °C for interpretability.
Date: 2026-10-06

## ADR-009: Ridge Regression selected as production baseline model
Decision: Use Ridge Regression (α=100, RidgeCV-selected) as the baseline model artifact bundled with the backend.
Reason: Ridge achieves test RMSE=0.9952 and R²=0.266 vs LinearRegression RMSE=1.031 and R²=0.212. Ridge is 3.5% lower RMSE and more stable with the OHE-heavy design matrix (household dummies + hour dummies + day dummies). Predictors: apt (OHE), hour (OHE), dayofweek (OHE), month (OHE), temp_c (scaled), tt/tt2/tt3 (scaled), post/finpost/healthpost (binary passthrough). Target: lnenergy. Split: chronological 80/20 per household.
Date: 2026-10-06

## ADR-010: Residual Z-score (training-stats standardised) is the 4th anomaly signal
Decision: residual_zscore = (residual − household_train_residual_mean) / household_train_residual_std. Stored in model_predictions.csv. Used as the regression-based anomaly signal alongside global Z-score, IQR fence, and rolling Z-score.
Reason: Training residual stats avoid test-set leakage into the anomaly score. Synthetic benchmark shows 73% detection at +3σ and 95% at +4σ with FP rate 0.68%.
Date: 2026-10-06


## ADR-011: dayofweek column uses ISO encoding (1=Monday … 7=Sunday)
Decision: Do NOT recode the dayofweek column; leave it as-is from the raw Stata dataset.
Reason: Discovered during T013 testing. The raw dataset (Table_9_3_Final.dta) encodes day-of-week as ISO weekday (1=Mon, 7=Sun), not pandas 0-indexed (0=Mon, 6=Sun). The model was trained with this encoding and all downstream code uses it consistently. Recoding would require re-running the full ML pipeline. Clients and tests must expect 1–7.
Date: 2026-10-06
