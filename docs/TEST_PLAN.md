# Test Plan

## Unit tests
- Z-score calculation
- IQR bounds
- rolling feature generation
- feature leakage prevention
- anomaly severity boundaries
- prediction input validation

## Data tests
- timestamps parse successfully
- no duplicate apartment/timestamp keys after preprocessing
- expected frequency verified
- missingness reported
- no target leakage in engineered features

## API tests
- `/api/health` 200
- `/api/metadata` 200
- `/api/houses` 200
- valid `/api/summary`
- valid `/api/analysis`
- invalid apartment -> 4xx
- invalid date range -> 4xx
- malformed prediction payload -> 422

## Frontend acceptance tests
- initial loading state
- backend error state
- empty data state
- household selection
- date filtering
- anomaly selection
- responsive layout

## Final demo test
A clean browser session can load the public URL, select a household, show an anomaly, and explain the anomaly within 5 minutes.
