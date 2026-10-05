# Deployment Plan

## Target
Deploy both frontend and backend publicly using Render free services.

Render supports free static sites and free Python web services, but free web services spin down after 15 minutes of inactivity and may take about a minute to wake. The MVP must therefore tolerate cold starts.

## Services
### Frontend
- Type: Render Static Site
- Root: `frontend`
- Build: `npm ci && npm run build`
- Publish directory: `dist`
- Environment: `VITE_API_BASE_URL=https://<backend>.onrender.com`

### Backend
- Type: Render Web Service
- Root: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`

## CORS
Backend must allow the deployed frontend origin. Do not use wildcard CORS in the final deployed configuration unless there is a documented reason.

## Data/model packaging
Because the MVP has no mutable database, bundle:
- processed dataset
- metadata JSON
- serialized model artifacts
inside the backend image/repository.

Do not depend on writing persistent files at runtime because free service filesystems are ephemeral.

## Environment variables
Backend:
- `APP_ENV=production`
- `FRONTEND_ORIGIN=https://<frontend>.onrender.com`
- `MODEL_VERSION=...`
- `DATA_VERSION=...`

Frontend:
- `VITE_API_BASE_URL=...`

No secret is required for core functionality.

## Deployment acceptance test
1. Open frontend public URL.
2. Dashboard loads without local server.
3. Frontend calls backend HTTPS URL.
4. `/api/health` returns healthy.
5. Household list loads.
6. Charts load.
7. Anomaly details load.
8. Refresh after idle/cold start still works.
9. No localhost URLs remain in production build.
