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

## Current state (updated 2026-10-06 — T017 complete)

**Milestone:** M11 — Compare page live on GitHub; continuing P1 tasks.

**New page: `/compare` (Compare.jsx)**
- Multi-select checkboxes for all 19 households (2–5 max enforced)
- "Select first 5" / "Clear all" shortcuts
- Metrics table: n_obs, mean kWh, median kWh, std kWh, n_anomalies, anomaly rate
- Min/max row highlighting (orange=highest, green=lowest)
- Bar charts: avg consumption (kWh/hr), anomaly rate (%), anomaly count
- Custom dark tooltips matching site style
- Loading / error / empty states
- Data source: `/api/v1/households` response fields only (no new API calls)
- Navbar: Dashboard | Anomaly Explorer | **Compare** | Methodology

**GitHub:** `7ac1e2f main` — pushed

**Next task: T018 — Prediction scenario form**
- A form UI to let users input values (household, hour, temp, day) and call the backend
- NOTE: Current backend has no `/predict` endpoint. A new endpoint may be required.
- Decide: (a) add `/api/v1/predict` to backend, or (b) skip T018 if it conflicts with the "no API contract changes" rule.
- Check if sklearn pipeline can serve predictions without reloading model artifacts.

**Dev commands:**
```bash
# Backend
cd backend && PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev    # → http://localhost:5173

# Tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v
```

