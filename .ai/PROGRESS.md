# SmartWatt Progress Tracker

Last updated: 2026-10-06 (T014 render.yaml + GitHub push complete)

## Overall status
**95% — All code on GitHub; render.yaml ready; manual Render web service creation + T015 frontend deploy remaining.**

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
- [ ] 18 Frontend deployed
- [ ] 19 Public end-to-end test complete
- [ ] 20 PPT/demo ready

## Current milestone
M9 — Code on GitHub; Render blueprint (render.yaml) ready; T015 frontend deploy next.

## Active task
T015 — Deploy frontend.

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
- 2026-10-06 (AI Agent): T014 complete (local). All backend artifacts committed + pushed to GitHub main. render.yaml created for Render Blueprint deployment. Local smoke test: 7/7 endpoints pass (19 households, 103,704 obs, 6,549 anomalies confirmed). Manual Render dashboard step remains — see T014_deployment_guide.md.

## Rule for AI agents
Before starting work: read PROJECT_CONTEXT.md, this file, TASKS.md and DECISIONS.md.
After work: update completed checkboxes, current milestone, active task, blockers and a short changelog.
