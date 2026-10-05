# Repository Structure

smartwatt-india/
├── .ai/
│   ├── PROJECT_CONTEXT.md
│   ├── PROGRESS.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   └── AGENT_HANDOFF.md
├── docs/
│   ├── PRD.md
│   ├── SRS.md
│   ├── DATASET.md
│   ├── ML_STATISTICS_PLAN.md
│   ├── UI_UX_SPEC.md
│   ├── DEPLOYMENT.md
│   ├── TEST_PLAN.md
│   └── PROJECT_PLAN.md
├── data/
│   ├── raw/                 # downloaded source data; normally gitignored
│   └── processed/           # curated application data
├── ml/
│   ├── notebooks/
│   ├── src/
│   │   ├── preprocess.py
│   │   ├── features.py
│   │   ├── statistics.py
│   │   ├── train.py
│   │   ├── anomaly.py
│   │   └── evaluate.py
│   ├── artifacts/
│   └── reports/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ml/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile            # optional; Render native Python is preferred initially
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── utils/
│   │   └── App.jsx
│   ├── public/
│   ├── package.json
│   └── .env.example
├── tests/
├── README.md
└── .gitignore

## Dependency direction
Frontend -> HTTP API only.
Backend -> data/model services.
ML preprocessing/training -> produces versioned processed data/model artifacts consumed by backend.
Frontend must never import Python/ML code.
