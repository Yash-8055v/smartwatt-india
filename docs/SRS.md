# Software Requirements Specification (SRS)

## 1. System architecture
React/Vite frontend -> HTTPS REST API -> FastAPI backend -> preprocessed dataset + serialized ML model.

No database is required for MVP because the application is read-heavy and the dataset/model artifacts are versioned with the backend. If later required, persistent storage can be added separately.

## 2. Backend modules
- `api/`: route handlers and schemas
- `services/`: analysis, anomaly and prediction services
- `ml/`: feature preparation, training and inference
- `data/`: processed dataset and metadata
- `core/`: configuration and logging

## 3. API contract
### GET /api/health
Returns service status and model/data version.

### GET /api/metadata
Returns dataset period, household count, available frequencies, model version and feature descriptions.

### GET /api/houses
Returns anonymized apartment IDs and summary metadata.

### GET /api/analysis?apt=1&start=YYYY-MM-DD&end=YYYY-MM-DD
Returns time-series observations, expected usage, anomaly score/severity and required chart data.

### GET /api/summary?apt=1&start=YYYY-MM-DD&end=YYYY-MM-DD
Returns mean, median, standard deviation, variance, min, max, quartiles, IQR and anomaly count.

### GET /api/anomalies?apt=1&start=YYYY-MM-DD&end=YYYY-MM-DD&severity=high
Returns anomaly records with evidence.

### GET /api/model/metrics
Returns validation/test MAE, RMSE and R2 plus model name/version.

### POST /api/predict
Request: `{ "apt": 1, "timestamp": "2014-03-01T14:00:00", "hour_temp": 28.4, "dayofweek": 6, "previous_usage": 0.42 }`.
Response: predicted expected usage plus input validation and a note that the result is model-based, not a bill estimate.

## 4. Error format
All API errors should return JSON:
`{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }`

## 5. Frontend requirements
Pages:
1. Overview Dashboard
2. Household Explorer
3. Anomaly Explorer
4. Model & Statistics
5. Methodology / Dataset

Reusable UI: KPI cards, line chart, anomaly table, distribution chart, correlation view, methodology cards.

## 6. Validation
- Validate apartment IDs against known IDs.
- Validate date range.
- Reject dates outside dataset period.
- Validate numeric prediction inputs.
- Never expose filesystem paths or stack traces.

## 7. Testing
- Unit tests for Z-score, IQR, rolling baseline and anomaly scoring.
- API tests for health, metadata, summary, analysis and invalid requests.
- Frontend tests for loading, empty states and API error states where practical.
