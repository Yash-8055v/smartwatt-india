# Statistics and ML Methodology

## 1. Research question
Can a household-specific and time/weather-aware baseline distinguish unusually high or low electricity consumption better than a single global threshold?

## 2. Statistical layer
### Descriptive statistics
Mean, median, variance, standard deviation, minimum, maximum, quartiles, IQR.

### Distribution
Histogram/density and box plots per selected household.

### Correlation
Pearson correlation for numeric features where assumptions are reasonable; report that correlation is association, not causation.

### Rolling baseline
For hourly data, compute a 24-hour rolling mean and standard deviation per apartment, shifted by one observation where needed to avoid using the current target in its own baseline.

### Z-score
`z = (actual - baseline_mean) / baseline_std`.
Initial rule for strong evidence may use `abs(z) >= 3`, but thresholds must be treated as configurable and justified from observed distributions.

### IQR
`IQR = Q3 - Q1`; lower = Q1 - 1.5*IQR; upper = Q3 + 1.5*IQR.

### Advanced Diagnostics (T023)
- **Durbin-Watson Test**: Detects first-order autocorrelation in residuals.
  - *Purpose*: Evaluates whether prediction errors are temporally correlated.
  - *Result*: Mean DW statistic = 0.49.
  - *Interpretation*: Indicates positive autocorrelation. Periods of high/low unexplained consumption tend to cluster.
  - *Limitation*: Only detects first-order (lag-1) autocorrelation.
- **Spearman Rank Correlation (Heteroscedasticity)**:
  - *Purpose*: Checks if prediction errors scale with the predicted value.
  - *Result*: Correlation = 0.050 (p=5.57e-13).
  - *Interpretation*: Minor but statistically significant positive correlation, meaning errors increase slightly as expected consumption increases. Log transformation mostly mitigated this.
  - *Limitation*: Does not formalize a functional form for the variance.

## 3. ML layer
Primary model: **Linear Regression or Ridge Regression** as interpretable baseline.
Optional comparison: **RandomForestRegressor** if time permits.

### Candidate features
- hour
- dayofweek
- is_weekend
- hour_temp
- mean_daily_temp
- lag_1
- lag_24
- rolling_mean_24
- rolling_std_24
- apartment identifier encoded appropriately

### Target
Expected hourly electricity usage.

### Split
Chronological split, e.g. first 70% train, next 15% validation, final 15% test. Do not randomly shuffle time-series observations.

### Metrics
MAE, RMSE, R2. Use the test set only for final reporting.

## 4. Anomaly decision
Do not invent a universal weighted score before inspecting the data. Implement an evidence-based score using:
- standardized deviation from statistical baseline
- ML residual relative to validation residual distribution
- IQR flag

The final severity bands should be calibrated on the training/validation data and documented in code/config.

## 5. Controlled evaluation
Because the original dataset does not provide a ground-truth anomaly label, do not report ordinary classification accuracy on naturally occurring anomalies.

For an additional experiment, create a held-out synthetic anomaly benchmark by injecting controlled perturbations into clean test observations, e.g. +50%, +100%, -50%, while preserving timestamp/context. Report precision/recall/F1 for detecting those injected anomalies and clearly label them as synthetic benchmark results.

## 6. Explanation rules
Explanations must be evidence-based:
- actual vs expected difference
- z-score
- IQR status
- temperature relative to household history
- hour/day pattern
- recent rolling trend

Never say “AC caused this” unless the selected dataset explicitly contains appliance-level evidence for that observation.
