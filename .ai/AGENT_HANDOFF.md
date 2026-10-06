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

## Current state (updated 2026-10-06 — T015 complete)

**Milestone:** M10 — P0 MVP Complete! Starting Priority P1 Tasks.

**Backend URL:** `https://smartwatt-india-backend.onrender.com` (Live)
**Frontend URL:** Not live yet (Manual Render step required, see `T015_deployment_guide.md`)

**Remaining manual step for T015 (frontend live on Render):**
1. Go to https://dashboard.render.com
2. New → Static Site → connect `Yash-8055v/smartwatt-india`
3. Name: `smartwatt-india-frontend`
4. Build Command: `npm ci && npm run build`
5. Publish Directory: `dist`
6. Add Environment Variable: `VITE_API_BASE_URL` = `https://smartwatt-india-backend.onrender.com`

**Next task: T017 — Household comparison view.**
- Create a new frontend view/page or add a section to the Dashboard to compare multiple households side-by-side.
- Compare metrics like average consumption, peak consumption, and anomaly counts.
- It will likely require hitting `/api/v1/households/{id}` and `/api/v1/households/{id}/anomalies` for multiple households and plotting them together.

**Dev commands:**
```bash
# Backend
cd backend && PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev    # → http://localhost:5173

# Tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v
```

