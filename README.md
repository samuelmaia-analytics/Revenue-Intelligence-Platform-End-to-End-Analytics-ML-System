# Revenue Intelligence Platform - Executive Analytics & ML System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

[Leia em Português](README.pt-BR.md)

## Executive Summary

Revenue Intelligence Platform is an end-to-end decision system that converts customer behavior data into commercial priorities.  
It combines analytics, machine learning, and a board-ready dashboard to answer three executive questions:

- Where is revenue at risk?
- Where should we invest to accelerate growth?
- Which customers should be prioritized now?

## Business Outcomes

- Prioritized customer action list with estimated financial impact.
- Channel efficiency visibility using `LTV/CAC` and unit economics.
- Retention risk and next purchase probability at customer level.
- Executive-ready narrative for weekly commercial reviews.

## Scope and Capabilities

- Data ingestion from Kaggle dataset with synthetic fallback.
- Feature engineering and customer-level scoring dataset.
- Star schema outputs for analytics and BI interoperability.
- KPI layer: LTV, CAC, RFM, Cohort Retention, Unit Economics.
- ML layer: churn prediction + next purchase prediction.
- Recommendation engine for next best action.
- Streamlit executive interface with governance and exports.

## Architecture

Data Source (Kaggle CSV / synthetic fallback)  
-> Ingestion (Python)  
-> Cleaning & Feature Engineering  
-> Warehouse Outputs (Star Schema)  
-> Analytics Layer (KPI + Cohort + Unit Economics)  
-> ML Layer (Churn + Next Purchase)  
-> Recommendation Engine  
-> Executive Dashboard (Streamlit)  
-> Docker / Cloud Deployment

## Repository Structure

```text
revenue-intelligence-platform/
|- app/
|  \- streamlit_app.py
|- data/
|  |- raw/
|  \- processed/
|- notebooks/
|  |- 01_exploration.ipynb
|  |- 02_feature_engineering.ipynb
|  \- 03_modeling.ipynb
|- src/
|  |- ingestion.py
|  |- transformation.py
|  |- warehouse.py
|  |- metrics.py
|  |- modeling.py
|  \- recommendation.py
|- sql/
|  \- create_tables.sql
|- main.py
|- requirements.txt
|- Dockerfile
|- README.md
\- README.pt-BR.md
```

## Model Governance

The pipeline persists model governance metrics to:

- `data/processed/metrics_report.json`

This report includes:

- split strategy (temporal or controlled fallback)
- ROC-AUC cross-validation
- ROC-AUC holdout evaluation

## Executive Dashboard

`app/streamlit_app.py` provides:

- Executive KPI cards
- Board-level narrative (risk, opportunity, priority)
- Prioritized customer action plan with CSV export
- Commercial performance visuals
- Model governance view

## Data Source

Primary file:

- `data/raw/E-commerce Customer Behavior - Sheet1.csv`

Automatically mapped into:

- `customers.csv`
- `orders.csv`
- `marketing_spend.csv`

## Local Run (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
python -m streamlit run .\app\streamlit_app.py
```

## Docker

```bash
docker build -t revenue-intelligence .
docker run -p 8501:8501 revenue-intelligence
```

## Outputs

Main files generated in `data/processed/`:

- `scored_customers.csv`
- `recommendations.csv`
- `cohort_retention.csv`
- `unit_economics.csv`
- `metrics_report.json`
- `churn_model.joblib`
- `next_purchase_model.joblib`

## 30-Day Delivery Plan

1. Week 1: data reliability and warehouse baseline.
2. Week 2: KPI and executive analytics stabilization.
3. Week 3: model hardening and governance improvements.
4. Week 4: recommendation optimization and production deploy.

