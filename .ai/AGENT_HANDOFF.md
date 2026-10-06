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

---

## Current state (updated 2026-10-06 — T014 complete)

**Milestone:** M9 — All code on GitHub; render.yaml ready; T015 (frontend deploy) next.

**GitHub:** `git@github.com:Yash-8055v/smartwatt-india.git` — branch `main` up-to-date (2 commits ahead of origin)

**Render deployment config:** `render.yaml` in repo root — Blueprint defines both backend + frontend services.

**Backend local smoke test (7/7 pass):**
```
GET /api/v1/health             200  {"status":"ok","version":"v0.1.0"}
GET /api/v1/metadata           200  19 households, 103,704 obs, 6,549 anomalies, Ridge R²=0.266
GET /api/v1/households         200  19 households
GET /api/v1/summary            200  n_anomalies=6549, rate=6.32%
GET /api/v1/households/7/timeseries?limit=5  200  n_points=5
GET /api/v1/households/7/anomalies           200  n_anomalies=455
GET /api/v1/households/99      404  correct error
```

**Remaining manual step for T014 (backend live on Render):**
1. Go to https://dashboard.render.com
2. New → Blueprint → connect `Yash-8055v/smartwatt-india`
3. Render auto-detects render.yaml → Apply
4. Backend URL will be: `https://smartwatt-india-backend.onrender.com`

**Next task: T015 — Deploy frontend**
- Render Static Site OR Vercel
- Root dir: `frontend`
- Build: `npm ci && npm run build`
- Publish dir: `dist`
- Env var: `VITE_API_BASE_URL=https://smartwatt-india-backend.onrender.com`
- render.yaml already includes the frontend service (Option A: Blueprint deploys both together)

**Dev commands:**
```bash
# Backend
cd backend && PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev    # → http://localhost:5173

# Tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v
```

