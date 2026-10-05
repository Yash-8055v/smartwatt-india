# SmartWatt India ⚡

### Context-Aware Electricity Consumption Anomaly Detection for Indian Households

SmartWatt India is a data-driven web application that analyzes household electricity consumption and identifies usage patterns that are statistically unusual compared with the household's own historical baseline.

Instead of using a simple fixed threshold such as *"consumption above X kWh is abnormal"*, the system learns what is normal for a household and highlights significant deviations.

> **Important:** SmartWatt India detects statistically unusual consumption. It does **not** claim to detect electricity theft or identify the exact appliance responsible for an anomaly.

---

## 🎯 Problem Statement

Household electricity consumption naturally varies between days and time periods.

A sudden increase in consumption may be caused by:

- Higher-than-usual household activity
- Seasonal or weather-related changes
- Unusual usage patterns
- A sustained increase in consumption
- Random fluctuations

A fixed threshold cannot distinguish between normal variation and genuinely unusual behavior.

### Our Approach

SmartWatt India combines:

**Statistical Analysis + Personal Baselines + Machine Learning**

to estimate expected electricity consumption and identify significant deviations.

---

## 🚀 Key Features

### 1. Household Consumption Analysis
Analyze historical electricity consumption and understand normal usage patterns.

### 2. Statistical Analysis

The system calculates:

- Mean
- Median
- Variance
- Standard deviation
- Minimum / maximum
- Quartiles
- IQR
- Distribution
- Rolling statistics

### 3. Statistical Anomaly Detection

Multiple statistical signals are considered, including:

- Z-score
- IQR-based detection
- Rolling mean and standard deviation
- Historical deviation

### 4. ML-Based Expected Consumption

A machine learning model predicts expected electricity consumption using historical and contextual features.

The system then compares:

```text
Actual Consumption
        ↓
Expected Consumption
        ↓
Deviation
        ↓
Anomaly Score
```

### 5. Explainable Anomalies

Instead of simply showing:

> "Anomaly detected"

the application provides information such as:

- Actual consumption
- Expected consumption
- Percentage deviation
- Z-score
- Historical range
- Severity
- Reason for flagging

### 6. Anomaly Categories

Consumption can be classified into categories such as:

- Normal
- Mild Deviation
- Sudden Spike
- Unusually Low
- Sustained Increase

### 7. Interactive Dashboard

The web application provides:

- Consumption trends
- Actual vs expected usage
- Anomaly timeline
- Statistical summaries
- Recent anomalies
- Model performance metrics

---

# 📊 Dataset

SmartWatt India uses an Indian residential electricity consumption dataset from the IIIT-Delhi / New Delhi field study:

**Dataset:** *Dataset on Information Strategies for Energy Conservation: A Field Experiment in India*

**Source:** Harvard Dataverse

**DOI:** `10.7910/DVN/7MEXN4`

Dataset:

https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi%3A10.7910%2FDVN%2F7MEXN4

Research documentation:

https://pmc.ncbi.nlm.nih.gov/articles/PMC5735253/

The dataset contains electricity consumption measurements from Indian residential apartments in New Delhi along with contextual information such as weather and household characteristics.

The dataset provides measurements at different time resolutions, allowing the project to select an appropriate granularity for anomaly detection.

> The exact preprocessing and aggregation level will be finalized after inspecting the downloaded dataset files.

---

# 🧠 Methodology

The overall pipeline is:

```text
Indian Residential Electricity Dataset
                ↓
        Data Preprocessing
                ↓
       Data Quality Checking
                ↓
        Temporal Aggregation
                ↓
       Exploratory Data Analysis
                ↓
        Statistical Analysis
                ↓
      Personal Usage Baseline
                ↓
    ML Expected Consumption Model
                ↓
       Actual vs Expected
                ↓
      Anomaly Detection Engine
                ↓
     Severity + Explanation
                ↓
       Interactive Dashboard
```

---

## 📐 Statistical Methods

### Z-Score

The Z-score measures how far a consumption value is from the mean:

```text
Z = (X - μ) / σ
```

where:

- `X` = observed consumption
- `μ` = mean consumption
- `σ` = standard deviation

Large absolute Z-scores indicate unusual observations.

---

### IQR Method

The Interquartile Range is:

```text
IQR = Q3 - Q1
```

The typical bounds are:

```text
Lower Bound = Q1 - 1.5 × IQR

Upper Bound = Q3 + 1.5 × IQR
```

Values outside these bounds can be considered statistical outliers.

---

### Rolling Baseline

Instead of comparing every observation against the entire dataset mean, SmartWatt India can use a recent historical baseline.

For example:

```text
Recent 7-day usage
        ↓
Rolling Mean
        ↓
Expected Personal Usage
```

This helps account for changes in a household's normal behavior over time.

---

# 🤖 Machine Learning

The project uses supervised regression to estimate expected electricity consumption.

### Baseline Model

**Linear Regression**

It provides a simple and interpretable baseline.

### Optional Comparison Model

**Random Forest Regressor**

Random Forest may be evaluated if it provides meaningful improvement over the baseline.

The project does not require multiple complex models if a simpler model performs adequately.

---

## Possible Features

Depending on the final dataset structure, features may include:

- Hour
- Day of week
- Weekend indicator
- Previous consumption
- Rolling average
- Rolling standard deviation
- Historical consumption
- Temperature
- Weather-related variables

The final feature set will depend on the actual available dataset columns.

---

# 📈 Model Evaluation

For the consumption prediction model, the following metrics may be used:

### MAE

Mean Absolute Error

```text
MAE = average(|Actual - Predicted|)
```

### MSE

Mean Squared Error

```text
MSE = average((Actual - Predicted)²)
```

### RMSE

Root Mean Squared Error

```text
RMSE = √MSE
```

### R² Score

Measures how much variation in consumption is explained by the model.

---

## ⚠️ Anomaly Evaluation

The original dataset does not necessarily contain ground-truth labels for electricity anomalies.

Therefore, the project will **not claim anomaly-detection accuracy using fabricated labels**.

Instead, evaluation can use:

1. Statistical candidate anomalies
2. Controlled anomaly injection on held-out data
3. Comparison between actual and expected consumption
4. Consistency between statistical detection methods

---

# 🏗️ Technology Stack

## Frontend

- React
- Vite
- JavaScript
- Tailwind CSS
- Recharts

## Backend

- Python
- FastAPI
- Pydantic

## Data Science / ML

- Python
- Pandas
- NumPy
- SciPy
- Scikit-learn
- Joblib

## Development

- Google Colab
- Antigravity AI IDE
- Git / GitHub

## Deployment

- React frontend
- FastAPI backend
- Render

---

# 📁 Project Structure

```text
smartwatt-india/
│
├── .ai/
│   ├── PROJECT_CONTEXT.md
│   ├── PROGRESS.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   └── AGENT_HANDOFF.md
│
├── docs/
│   ├── PRD.md
│   ├── SRS.md
│   ├── DATASET.md
│   ├── ML_STATISTICS_PLAN.md
│   ├── UI_UX_SPEC.md
│   ├── DEPLOYMENT.md
│   ├── TEST_PLAN.md
│   └── PROJECT_PLAN.md
│
├── data/
│   ├── raw/
│   └── processed/
│
├── ml/
│   ├── notebooks/
│   ├── src/
│   ├── artifacts/
│   └── reports/
│
├── backend/
│
├── frontend/
│
├── tests/
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# 🔌 API

The backend will expose a small set of REST APIs.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Backend health check |
| `GET /api/metadata` | Dataset/model metadata |
| `GET /api/houses` | Available households |
| `GET /api/summary` | Consumption summary |
| `GET /api/analysis` | Statistical analysis |
| `GET /api/anomalies` | Detected anomalies |
| `GET /api/model/metrics` | ML model metrics |
| `POST /api/predict` | Generate expected consumption |

The exact API structure may be adjusted after the dataset and ML pipeline are finalized.

---

# 💻 Local Setup

## 1. Clone Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>

cd smartwatt-india
```

---

## 2. Setup Python Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

---

## 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## 4. Run Backend

From the project root:

```bash
uvicorn backend.app.main:app --reload
```

Backend will normally run at:

```text
http://localhost:8000
```

---

## 5. Run Frontend

```bash
cd frontend
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

---

# 🔐 Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production:

```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
```

No database or API key is required for the core MVP.

---

# ☁️ Deployment

The planned deployment architecture is:

```text
                 INTERNET
                    │
                    ▼
          React Frontend
              Render
                    │
                 HTTPS
                    │
                    ▼
           FastAPI Backend
              Render
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   Processed Dataset      ML Artifacts
```

The frontend communicates with the FastAPI backend through REST APIs.

The MVP does not require a database.

---

# 🎯 Project Objectives

The main objectives are:

1. Analyze residential electricity consumption patterns.
2. Apply statistical techniques to identify unusual consumption.
3. Build a household-specific consumption baseline.
4. Predict expected electricity consumption using machine learning.
5. Compare actual and expected consumption.
6. Generate interpretable anomaly explanations.
7. Provide the results through an interactive web application.
8. Deploy the complete application for public access.

---

# 🚫 Scope Boundaries

To keep the project achievable within the available development time, the MVP will **not** include:

- Deep learning
- LSTM/Transformer forecasting
- IoT hardware integration
- Real-time smart meter streaming
- Electricity theft detection
- Appliance-level identification
- User authentication
- Payment systems
- MongoDB/database infrastructure
- Complex cloud architecture

These may be considered future enhancements.

---

# 🔮 Future Scope

Possible future improvements include:

- Real-time smart meter integration
- Personalized household models
- Appliance-level energy analysis
- Weather-aware predictions
- Mobile application
- Energy-saving recommendations
- Multi-household benchmarking
- Real-time alerts
- Long-term consumption forecasting
- Integration with smart-home devices

---

# ⚠️ Limitations

### Dataset Size

The selected dataset represents a limited number of Indian households and therefore cannot represent all Indian households.

### Generalization

Consumption behavior varies based on:

- Region
- Climate
- Household size
- Appliances
- Lifestyle
- Season

Therefore, the model should not be treated as universally representative of India.

### Anomaly Labels

The dataset does not necessarily contain verified anomaly labels. Therefore, anomaly detection is evaluated through statistical methods and controlled experiments rather than claiming real-world anomaly classification accuracy.

### Causality

An anomaly indicates unusual consumption but does not automatically identify its cause.

For example:

```text
High Consumption
       ≠
AC definitely caused it
```

The system should only make causal claims when supporting data is available.

---

# 📚 Research & References

1. *Dataset on Information Strategies for Energy Conservation: A Field Experiment in India*  
   Harvard Dataverse.

2. Research documentation associated with the residential electricity field study.

3. Scikit-learn documentation for regression and evaluation methods.

4. Pandas / NumPy / SciPy documentation for statistical data processing.

5. FastAPI documentation for backend API development.

---

# 👥 Project Development

**Project:** SmartWatt India

**Domain:** Statistics + Machine Learning + Data Science

**Application Type:** Full-Stack Data Science Web Application

**Primary Language:** Python + JavaScript

---

# 📌 Development Principle

SmartWatt India follows a simple principle:

> **Don't just ask whether electricity usage is high. Ask whether it is unusually high for this household.**

The goal is to combine statistical reasoning, machine learning, and explainability into a small, practical, deployable application.

---

## License

This project is developed for academic and educational purposes.