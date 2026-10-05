# UI/UX Specification

## Visual direction
Clean analytical dashboard, not an AI-generated sci-fi dashboard. Use a restrained energy/analytics visual language, high contrast, readable charts and clear anomaly states.

## Pages
### 1. Dashboard
- project title and one-line explanation
- household selector
- date range selector
- KPI cards: average usage, peak usage, anomaly count, model error
- consumption trend with expected baseline
- anomaly markers

### 2. Household Explorer
- detailed time-series chart
- temperature overlay/toggle
- hourly/day-of-week pattern
- distribution histogram
- box plot

### 3. Anomaly Explorer
- anomaly table
- severity filter
- selected anomaly detail panel
- evidence cards: actual, expected, deviation %, Z-score, IQR, residual
- plain-language explanation

### 4. Model & Statistics
- MAE/RMSE/R2
- feature importance/coefficients where appropriate
- residual plot
- distribution statistics
- model limitations

### 5. Methodology
- dataset provenance
- data pipeline
- formulas
- model flow
- limitations
- source links

## UX states
Every API-dependent component needs loading, empty, error and success states. The frontend must handle backend cold-start gracefully with a clear “Starting analysis service…” message.
