# Revenue Intelligence Platform - Executive Analytics & ML System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

[Leia em Português](README.pt-BR.md)

## Live App

Streamlit Cloud:
- https://revenue-intelligence-platform.streamlit.app/

## Executive Summary

Revenue Intelligence Platform is an end-to-end decision system that converts customer behavior data into commercial priorities.

## Business Outcomes

- Prioritized customer action list with estimated financial impact
- Channel efficiency visibility with `LTV/CAC` and unit economics
- Customer-level churn risk and next purchase probability
- Executive narrative for weekly business reviews

## Scope and Capabilities

- Data ingestion from Kaggle source with synthetic fallback
- Feature engineering and customer-level scoring
- Star schema outputs for analytics interoperability
- KPI layer: LTV, CAC, RFM, Cohort Retention, Unit Economics
- ML layer: churn + next purchase prediction
- Recommendation engine for next best action
- Executive Streamlit dashboard with governance and exports

## Architecture

Data Source (Kaggle CSV / synthetic fallback)
-> Ingestion
-> Cleaning & Feature Engineering
-> Warehouse Outputs
-> Analytics Layer
-> ML Layer
-> Recommendation Engine
-> Executive Dashboard
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
|- src/
|- sql/
|- main.py
|- requirements.txt
|- Dockerfile
|- README.md
\- README.pt-BR.md
```

## Data Source

Primary file:
- `data/raw/E-commerce Customer Behavior - Sheet1.csv`

Source:
- Kaggle dataset: `E-commerce Customer Behavior Dataset`

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

## Main Outputs

- `data/processed/scored_customers.csv`
- `data/processed/recommendations.csv`
- `data/processed/cohort_retention.csv`
- `data/processed/unit_economics.csv`
- `data/processed/metrics_report.json`
