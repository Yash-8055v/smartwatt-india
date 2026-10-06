# Antigravity Agent Handoff Prompt

You are working on SmartWatt India. Before changing code, read:
1. `.ai/PROJECT_CONTEXT.md`
2. `.ai/PROGRESS.md`
3. `.ai/TASKS.md`
4. `.ai/DECISIONS.md`
5. Relevant files in `docs/`

Work only on the requested task. Do not redesign the architecture without documenting a decision. Do not invent dataset columns. Inspect the downloaded dataset before implementing preprocessing.

After completing work:
- run relevant tests/checks;
- update `.ai/PROGRESS.md`;
- update `.ai/TASKS.md`;
- update `.ai/DECISIONS.md` only if a decision changed;
- summarize files changed, tests run, current status and next task.

If blocked by missing data, dependency, deployment credential or ambiguous requirement, do not fabricate a solution. Record the blocker and ask for the minimum required input.

## Current state (updated 2026-10-06 — T019 complete)

**Milestone:** M13 — P1 tasks finishing up.

**GitHub:** `(Pending commit)`

**New endpoint: POST /api/v1/predict**
- Request: `{ apt, hour, dayofweek, month, temp_c }`
- Response: `{ apt, hour, dayofweek, month, temp_c, predicted_lnenergy, predicted_kwh, model_version, note }`
- Validation: apt 1–19 → 404; field bounds → 422
- Treatment flags resolved per household from dataset; tt/tt2/tt3 at medians (ADR-013)
- Uses `store.model.predict()` — no model reload

**New page: `/predict` (Predict.jsx)**
- Form: Household dropdown, Hour, Day of Week, Month, Temperature (°C)
- Result: kWh value, consumption level bar, scenario summary, model disclaimer
- Loading / error / empty states; mobile-responsive grid layout

**Tests: 107/107 passed** (21 new TestPredict cases added to test_api.py)

**Navbar:** Dashboard | Anomaly Explorer | Compare | **Predict** | Methodology

**Next task: T020 — Demo seed/default household**
- Make the deployed demo immediately usable.
- Use an actual household from the existing API/data (prefer Apt 1 as default).
- Apply sensible defaults where household selection is required (Dashboard, Anomaly Explorer, Predict, Compare).
- Handle asynchronous API loading correctly and preserve loading/error states.
- Do NOT fabricate data, add a database, or add a backend endpoint.

**Dev commands:**
```bash
# Backend
cd backend && PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev    # → http://localhost:5173

# Tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v

# Quick predict test
curl -s -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -d '{"apt":7,"hour":18,"dayofweek":3,"month":10,"temp_c":25}' | python3 -m json.tool
```
