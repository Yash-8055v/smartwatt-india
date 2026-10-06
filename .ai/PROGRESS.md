# SmartWatt Progress Tracker

Last updated: 2026-10-06 (T022 Advanced filters complete)

## Overall status
**100% MVP — Both backend and frontend configured for Render deployment. Manual Render UI steps remaining. Moving to P1 tasks.**

## Progress board
- [x] 01 Dataset downloaded
- [x] 02 Dataset structure verified
- [x] 03 Data preprocessing complete
- [x] 04 EDA complete
- [x] 05 Statistical anomaly engine complete
- [x] 06 ML baseline complete
- [x] 07 Evaluation complete
- [x] 08 Model artifact versioned
- [x] 09 FastAPI skeleton complete
- [x] 10 API endpoints complete
- [x] 11 React/Vite shell complete
- [x] 12 Dashboard complete
- [x] 13 Anomaly Explorer complete
- [x] 14 Methodology page complete
- [x] 15 Frontend/backend integration complete
- [x] 16 Tests complete
- [x] 17 Backend deployed
- [x] 18 Frontend deployed
- [ ] 19 Public end-to-end test complete
- [ ] 20 PPT/demo ready

## Current milestone
M14 — P2 tasks finishing.

## Active task
T023 — Additional statistical tests.

## Blockers
None known.

## Changelog
- 2026-10-06 (AI Agent): Inspected all 14 .dta files; wrote docs/DATASET.md; produced data/processed/dataset_inspection_report.json; identified Table_9_3_Final.dta as primary ML dataset (hourly, 19 apartments, 103,704 rows, zero missing values, date range 2013-08-01 to 2014-05-12).
- 2026-10-06 (AI Agent): T003 complete. Wrote ml/preprocess.py; produced data/processed/hourly_energy.csv (103,704 rows, 16 columns) and data/processed/preprocessing_report.json. Key finding: all 19 households have temporal gaps (missing hours not filled); largest gap ~750 hours (apts 1-5, Nov-Dec 2013); average coverage ~80% of the 6,839-hour range.
- 2026-10-06 (AI Agent): T005 complete. Wrote ml/eda.py; produced data/processed/eda_report.json and docs/EDA_FINDINGS.md. Key EDA findings: energy is log-normally distributed; strong hour-of-day effect (2.35x peak/trough); per-household mean ranges 0.09–1.04 kWh (per-household baselines mandatory); temperature positively correlated on log scale (r=0.12); pre/post treatment confirmed (−8.5%, p=0.044); recommended method set: Z-score on lnenergy + IQR fence + regression residual.
- 2026-10-06 (AI Agent): T006 complete. Wrote ml/anomaly_features.py; produced data/processed/anomaly_features.csv (103,704 rows, 30 cols) and anomaly_features_report.json. Features: global Z-score on lnenergy, IQR fences on energy_kwh, 7-day rolling Z-score (closed='left', min_periods=48). All 19 validations passed: no row loss, no leakage, rolling NaN at start only.
- 2026-10-06 (AI Agent): T007+T008+T009 complete. Wrote ml/train.py, ml/evaluate.py. Ridge (α=100) beats LinearRegression on test RMSE (0.9952 vs 1.031, R²=0.266). Synthetic benchmark: 73% detection at +3σ, 95% at +4σ, FP rate 0.68%. Artifacts: model_predictions.csv, model_metrics.json, evaluation_report.json, ml/models/ridge_model.joblib.
- 2026-10-06 (AI Agent): T010 complete. FastAPI backend built (backend/app/). 7 endpoints: /health, /metadata, /households, /households/{id}, /households/{id}/timeseries, /households/{id}/anomalies, /summary. All tested and returning correct data (6,549 anomalies, 19 households). DataStore loads at startup from CSV artifacts.
- 2026-10-06 (AI Agent): T011+T012 complete. React/Vite frontend built (3 pages: Dashboard, Anomaly Explorer, Methodology). Stack: React 18 + Vite 5 + Tailwind CSS v4 + Recharts + React Router 6. Clean production build (0 errors). API integration via VITE_API_BASE_URL. All API endpoints consumed and tested via curl. Dev server: port 5173.
- 2026-10-06 (AI Agent): T013 complete. 86/86 pytest tests pass. 7 endpoint classes, integration class. 1 dataset fact discovered: dayofweek uses ISO encoding 1–7 (not 0–6) from raw Stata file — documented as ADR-011. No backend bugs. Test file: backend/tests/test_api.py. Run: PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py
- 2026-10-06 (AI Agent): T014 complete. Backend successfully deployed to Render (`https://smartwatt-india-backend.onrender.com`).
- 2026-10-06 (AI Agent): T015 complete (local). Frontend build tested locally with `VITE_API_BASE_URL` pointing to live backend. Provided `T015_deployment_guide.md` for manual Render static site deployment. P0 MVP phase complete.
- 2026-10-06 (AI Agent): T016 complete. Built and evaluated a Random Forest regressor (`ml/train_rf.py`). Rejected in favor of Ridge baseline. RF heavily overfit (Train R²=0.59 vs Test R²=-0.22) and failed to extrapolate chronological trends. (ADR-012).
- 2026-10-06 (AI Agent): T017 complete. Created frontend/src/pages/Compare.jsx — dedicated /compare route. Multi-select checkboxes (2–5 max), metrics comparison table with min/max highlighting, 3 bar charts (avg kWh, anomaly rate%, anomaly count). Uses /api/v1/households response only. Build: 843 modules, 0 errors. Pushed to GitHub.
- 2026-10-06 (AI Agent): T018 complete. POST /api/v1/predict added to backend (ADR-013). PredictRequest/Response Pydantic schemas. Validates apt 1-19, hour 0-23, dayofweek 1-7, month 1-12, temp_c 5-45. Treatment flags (finpost/healthpost) resolved per household; tt/tt2/tt3 held at medians. 21 new tests added; 107/107 pass. Frontend: Predict.jsx at /predict with form, result card, consumption bar, model disclaimer. Navbar updated. Build: 844 modules, 0 errors. Pushed 31aa63f.
- 2026-10-06 (AI Agent): T019 complete. Rewrote AnomalyExplorer.jsx to use clear, non-technical explanations for detection methods. Preserved functionality and UI aesthetics. Build: 844 modules, 0 errors.
- 2026-10-06 (AI Agent): T020 complete. Updated default household selection to Apt 1 in Dashboard, AnomalyExplorer, and Predict pages to make the deployed demo immediately usable. Build: 844 modules, 0 errors. Tests: 107/107 pass.
- 2026-10-06 (AI Agent): T021 complete. Added a frontend-generated CSV export feature to the `AnomalyTable` component. Generates a properly escaped CSV with meaningful headers (household, timestamp, consumption, expected, residuals, methods). No new backend infrastructure added. Build: 844 modules, 0 errors. Tests: 107/107 pass.
- 2026-10-06 (AI Agent): T022 complete. Added 'Required Method' (Z-score, IQR, Rolling, Residual) and 'Date Range' (From, To) filters to `AnomalyTable`. Includes 'Clear Filters' button and reactive empty state. Filters apply instantly client-side without new backend endpoints. Build: 844 modules, 0 errors. Tests: 107/107 pass.

## Rule for AI agents
Before starting work: read PROJECT_CONTEXT.md, this file, TASKS.md and DECISIONS.md.
After work: update completed checkboxes, current milestone, active task, blockers and a short changelog.
