# Architecture Decisions

## ADR-001: Use Indian household dataset
Decision: Use the IIIT-Delhi/New Delhi residential electricity field-experiment dataset.
Reason: It provides actual kWh consumption, weather and household context, unlike the RESIDE-AC dataset whose core electrical measurements are current rather than direct kWh.

## ADR-002: Hourly modeling
Decision: Use hourly observations for the main ML pipeline.
Reason: Smaller, compatible with hourly weather, and sufficient for a 2–3 day project while preserving meaningful daily patterns.

## ADR-003: No database in MVP
Decision: Bundle processed data/model artifacts with backend.
Reason: Read-only academic demo; avoids unnecessary database deployment and free-tier persistence issues.

## ADR-004: FastAPI backend
Decision: Use FastAPI rather than Node/Express.
Reason: ML/data processing is Python-native, avoiding a second ML runtime/service.

## ADR-005: Render for deployment
Decision: Render static frontend + Render backend web service.
Reason: Both service types are supported on free plans and can be deployed from one repository. Free backend cold starts must be handled in UX.

## ADR-006: Statistical evidence before ML complexity
Decision: Statistical anomaly methods are first-class; ML is used for expected-usage prediction.
Reason: Course objective is Statistics for ML and DS, and the project must remain explainable.
