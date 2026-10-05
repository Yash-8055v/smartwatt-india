# Product Requirements Document (PRD)
## SmartWatt India

### 1. Product summary
SmartWatt India is a web application for detecting and explaining unusual household electricity consumption using statistical analysis and machine learning. The system is intended as a Statistics for Machine Learning and Data Science course project, so statistical reasoning must remain central.

### 2. Problem statement
A household may consume more electricity than usual for many legitimate reasons. A fixed threshold such as “above 10 kWh = anomaly” ignores each household's normal baseline, time of day, day of week, weather and historical variability. The project asks whether a context-aware baseline can identify genuinely unusual observations more meaningfully.

### 3. Target users
- Student/demo user evaluating household energy patterns.
- Course evaluator/professor reviewing statistical and ML methodology.
- General visitor exploring an anonymized Indian household energy dataset.

### 4. Goals
1. Show real Indian residential electricity data in an accessible dashboard.
2. Establish household-specific normal consumption patterns.
3. Detect unusually high/low consumption using statistical methods.
4. Predict expected consumption using an interpretable ML model.
5. Compare actual vs expected consumption.
6. Explain anomaly evidence in plain language.
7. Provide an openly accessible deployed frontend and backend.

### 5. Non-goals
- Electricity theft detection.
- Appliance-level diagnosis.
- Real-time smart-meter integration.
- Billing/payment system.
- Mobile native app.
- Deep learning.
- General-purpose energy management platform.

### 6. Core user journeys
#### Journey A: Explore
Select a household and date range -> view consumption trend, weather, statistics and anomaly markers.

#### Journey B: Inspect anomaly
Select an anomalous observation -> see actual usage, expected usage, deviation, Z-score/IQR evidence, severity and contributing contextual features.

#### Journey C: Compare households
Select two or more households -> compare normalized consumption patterns without exposing personally identifying information.

#### Journey D: Methodology
Open methodology page -> understand dataset, statistical formulas, ML model, evaluation and limitations.

### 7. Functional requirements
FR-01: Display project overview and dataset provenance.
FR-02: List available anonymized apartment IDs.
FR-03: Filter observations by household and date range.
FR-04: Display time-series electricity consumption.
FR-05: Display rolling mean and rolling standard deviation.
FR-06: Compute and display Z-score.
FR-07: Compute IQR-based outlier status.
FR-08: Predict expected consumption with trained regression model.
FR-09: Calculate actual-vs-expected deviation.
FR-10: Produce an anomaly severity label.
FR-11: Provide an explanation based only on measurable dataset features.
FR-12: Display ML evaluation metrics.
FR-13: Display statistical summary.
FR-14: Expose API health endpoint.
FR-15: Support public deployment.

### 8. Non-functional requirements
NFR-01: Frontend must be responsive on desktop and mobile.
NFR-02: API responses for normal dashboard requests should target <2 seconds after backend wake-up.
NFR-03: No secret/API key is required for the core product.
NFR-04: No personal user data is collected.
NFR-05: Dataset and model inference must be deterministic for the same input/version.
NFR-06: Backend must bind to the platform-provided PORT.
NFR-07: Frontend must use an environment variable for API base URL.
NFR-08: The deployed app must work if the free backend has cold-start latency.

### 9. Success criteria
- A visitor can open the public frontend and explore at least one household without local setup.
- An anomaly can be traced to numerical evidence.
- Statistical and ML methodology can be reproduced from the repository.
- The model does not claim ground-truth anomaly accuracy where labels do not exist.
- The project can be demonstrated end-to-end in under 5 minutes.

### 10. Limitations to disclose
The dataset covers 19 apartments at one Indian site and is historical. It should not be presented as representative of all Indian households. An anomaly means statistically unusual relative to the modeled baseline, not theft, equipment failure or wrongdoing.
