# AI Task Queue

## Priority P0 — must complete
- [x] T001 Download dataset from official Harvard Dataverse source. DONE
- [x] T002 Inspect all `.dta` files and identify best hourly electricity table. DONE — primary table: Table_9_3_Final.dta
- [x] T003 Create reproducible preprocessing script. DONE — ml/preprocess.py; outputs: hourly_energy.csv, preprocessing_report.json
- [x] T004 Produce `data/processed/hourly_energy.csv`. DONE — produced by ml/preprocess.py (103,704 rows, 16 columns)
- [x] T005 Build EDA notebook/script and save key findings. DONE — ml/eda.py; outputs: eda_report.json, docs/EDA_FINDINGS.md
- [x] T006 Implement statistical anomaly features. DONE — ml/anomaly_features.py; outputs: anomaly_features.csv (30 cols), anomaly_features_report.json
- [x] T007 Train chronological Linear/Ridge Regression baseline. DONE — ml/train.py; Ridge α=100, test RMSE=0.9952, R²=0.266
- [x] T008 Evaluate MAE/RMSE/R2. DONE — ml/evaluate.py; evaluation_report.json; per-household metrics documented
- [x] T009 Implement controlled synthetic anomaly benchmark. DONE — 73% detection at +3σ, 95% at +4σ, FP rate 0.68%
- [x] T010 Build FastAPI backend. DONE — backend/app/{main.py,api/routes.py,services/data_service.py,schemas/responses.py,core/config.py}; 7 endpoints tested
- [x] T011 Build React frontend. DONE — frontend/src/ (App.jsx, 3 pages, 5 components); Vite 5+React 18+Tailwind v4+Recharts+React Router 6; clean build
- [x] T012 Integrate frontend/backend. DONE — src/services/api.js consumes all 7 backend endpoints via VITE_API_BASE_URL
- [x] T013 Test. DONE — 86/86 pytest; backend/tests/test_api.py; 1 dataset fact (ADR-011: dayofweek=1–7 ISO encoding)
- [x] T014 Deploy backend. DONE — deployed to Render (smartwatt-india-backend.onrender.com)
- [x] T015 Deploy frontend. DONE (local) — build passed, deployment guide (T015_deployment_guide.md) provided for Render.

## Priority P1 — should complete
- [x] T016 Random Forest comparison. DONE — RF struggled with temporal extrapolation (Test R²=-0.2259); Ridge baseline retained.
- [x] T017 Household comparison view. DONE — frontend/src/pages/Compare.jsx; /compare route; multi-select (2–5); metrics table + 3 bar charts; 843-module build passes.
- [x] T018 Prediction scenario form. DONE — POST /api/v1/predict + Predict.jsx; 107/107 pytest; ADR-013.
- [x] T019 Improved anomaly explanation. DONE — Rewrote AnomalyExplorer with expandable plain-language tooltips for methods.
- [x] T020 Demo seed/default household. DONE — Changed default apt selection to 1 in Dashboard, AnomalyExplorer, and Predict.
- [x] T021 CSV export. DONE — Added 'Export CSV' button to AnomalyTable (frontend-generated).
- [ ] T022 Advanced filters. IN PROGRESS
- [ ] T023 Additional statistical tests.

## Agent execution protocol
When an agent takes a task:
1. Mark task `IN PROGRESS` in this file.
2. Read relevant docs.
3. Implement only the task scope.
4. Run tests/validation.
5. Mark `DONE` or record blocker.
6. Update `.ai/PROGRESS.md`.
7. Add architecture changes to `.ai/DECISIONS.md`.
