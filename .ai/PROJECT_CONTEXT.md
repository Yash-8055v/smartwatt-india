# AI Agent Project Context — READ FIRST

## Project identity
Name: SmartWatt India
Goal: Context-aware household electricity consumption anomaly detection using Indian residential data.

## Frozen decisions
- Primary dataset: Delhi/IIIT-Delhi Indian residential field experiment dataset (Harvard Dataverse DOI 10.7910/DVN/7MEXN4).
- Main frequency: hourly.
- Frontend: React + Vite + JavaScript + Tailwind + Recharts.
- Backend: FastAPI + Pydantic.
- ML: scikit-learn; statistics: NumPy/SciPy/Pandas.
- Deployment: Render frontend static site + Render backend web service.
- No database for MVP.
- No authentication.
- No LLM/AI API dependency.

## Core product rule
An anomaly is a statistically/model-wise unusual observation relative to the modeled household/context baseline. It is NOT proof of theft, appliance failure or wrongdoing.

## Coding rules
1. Inspect existing code before creating files.
2. Prefer small changes.
3. Do not replace working architecture without updating docs.
4. Do not add dependencies without need.
5. Keep JavaScript, not TypeScript, unless explicitly changed.
6. Keep API response schemas stable.
7. Never hardcode localhost URLs in production code.
8. Never commit secrets.
9. Never use random train/test splitting for time-series modeling.
10. Prevent target leakage in rolling/lag features.
11. Add/update tests for non-trivial logic.
12. Update `.ai/PROGRESS.md` after completing a task.
13. Update `.ai/DECISIONS.md` when an architectural decision changes.
14. If a requirement conflicts with PRD/SRS, stop and report the conflict before implementing it.
