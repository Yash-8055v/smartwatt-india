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

## Current state (updated 2026-10-06 — T013 tests complete)

**Milestone:** M8 — 86/86 pytest tests pass; deployment (T014/T015) next.

**Test suite:** `backend/tests/test_api.py`
```
86 tests / 86 passed / 0 failed
Run: PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v
```

**Test classes:**
| Class | Tests | Covers |
|---|---|---|
| TestHealth | 4 | /health status, schema, values |
| TestMetadata | 10 | /metadata schema, counts, ranges, model |
| TestListHouseholds | 9 | /households count=19, IDs 1–19, total obs |
| TestGetHousehold | 8 | /households/{id} valid/invalid/all 19 |
| TestTimeseries | 17 | limit, date filters, schema, impossible range |
| TestAnomalies | 15 | min_methods monotone, param validation |
| TestSummary | 11 | /summary totals, method keys, rate math |
| TestIntegration | 8 | cross-endpoint consistency, all apts |

**Dataset fact discovered (ADR-011):**
- `dayofweek` column is ISO encoded (1=Mon … 7=Sun) from raw Stata file — not 0-indexed
- No backend code change needed; documented in DECISIONS.md

**Dev commands (full stack):**
```bash
# Backend (Terminal 1)
cd backend && PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev    # → http://localhost:5173

# Tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_api.py -v
```

**Next task: T014 — Deploy backend to Render**
- Render web service (Python, free tier)
- Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set env vars: FRONTEND_ORIGIN, MODEL_VERSION, DATA_VERSION
- Data files must be committed to Git (data/processed/ and ml/models/ currently gitignored — check .gitignore)
- IMPORTANT: Confirm .gitignore allows data/processed/*.csv and ml/models/*.joblib for deployment

**Then T015 — Deploy frontend to Render Static Site or Vercel**
- Build: `npm run build` → dist/
- Env: VITE_API_BASE_URL=https://<backend-render-url>
- Frontend .env.example already in place

