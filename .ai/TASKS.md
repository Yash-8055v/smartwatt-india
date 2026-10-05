# AI Task Queue

## Priority P0 — must complete
- [ ] T001 Download dataset from official Harvard Dataverse source.
- [ ] T002 Inspect all `.dta` files and identify best hourly electricity table.
- [ ] T003 Create reproducible preprocessing script.
- [ ] T004 Produce `data/processed/hourly_energy.csv`.
- [ ] T005 Build EDA notebook/script and save key findings.
- [ ] T006 Implement statistical anomaly features.
- [ ] T007 Train chronological Linear/Ridge Regression baseline.
- [ ] T008 Evaluate MAE/RMSE/R2.
- [ ] T009 Implement controlled synthetic anomaly benchmark.
- [ ] T010 Build FastAPI backend.
- [ ] T011 Build React frontend.
- [ ] T012 Integrate frontend/backend.
- [ ] T013 Test.
- [ ] T014 Deploy backend.
- [ ] T015 Deploy frontend.

## Priority P1 — should complete
- [ ] T016 Random Forest comparison.
- [ ] T017 Household comparison view.
- [ ] T018 Prediction scenario form.
- [ ] T019 Improved anomaly explanation.
- [ ] T020 Demo seed/default household.

## Priority P2 — only if time remains
- [ ] T021 CSV export.
- [ ] T022 Advanced filters.
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
