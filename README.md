# Revenue Intelligence Platform - End-to-End Analytics & ML System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Portfolio%20Project-0f766e)](#)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

[Leia em Português](README.pt-BR.md)

## Summary

- [Business Goal](#business-goal)
- [End-to-End Architecture](#end-to-end-architecture)
- [Project Structure](#project-structure)
- [Data Source](#data-source)
- [Core Metrics](#core-metrics)
- [Machine Learning](#machine-learning)
- [Recommendation Engine](#recommendation-engine)
- [Local Run (Windows / PowerShell)](#local-run-windows--powershell)
- [Docker](#docker)
- [Outputs Generated](#outputs-generated)
- [30-Day Delivery Roadmap](#30-day-delivery-roadmap)

Executive-grade revenue analytics product that combines customer intelligence, predictive modeling, and action prioritization in one dashboard.

## Business Goal

Convert raw customer behavior data into clear executive decisions:
- Where revenue is at risk
- Which customers should be targeted for retention or upsell
- Which acquisition channels are financially efficient

## End-to-End Architecture

Data Source (Kaggle CSV / fallback synthetic data)  
-> Data Ingestion (Python)  
-> Data Cleaning & Feature Engineering  
-> SQL Warehouse Outputs (Star Schema)  
-> Analytics Layer (LTV, CAC, RFM, Cohort, Unit Economics)  
-> ML Layer (Churn + Next Purchase Probability)  
-> Recommendation Engine (Next Best Action)  
-> Executive Streamlit App  
-> Docker / Cloud Deployment

## Project Structure

```text
revenue-intelligence-platform/
|- app/
|  \- streamlit_app.py
|- data/
|  |- raw/
|  |  |- E-commerce Customer Behavior - Sheet1.csv
|  |  |- customers.csv
|  |  |- marketing_spend.csv
|  |  \- orders.csv
|  \- processed/
|     |- cac_by_channel.csv
|     |- churn_model.joblib
|     |- cohort_retention.csv
|     |- customer_features.csv
|     |- dim_customers.csv
|     |- dim_date.csv
|     |- fact_orders.csv
|     |- ltv.csv
|     |- next_purchase_model.joblib
|     |- recommendations.csv
|     |- rfm_segments.csv
|     |- scored_customers.csv
|     \- unit_economics.csv
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
|- .gitignore
|- Dockerfile
|- LICENSE
|- main.py
|- README.md
|- README.pt-BR.md
|- requirements.txt
\- (local folders excluded: .venv, .idea, __pycache__)
```

## Data Source

Primary source:
- `data/raw/E-commerce Customer Behavior - Sheet1.csv` (Kaggle)

The ingestion layer automatically maps this dataset into:
- `customers.csv`
- `orders.csv`
- `marketing_spend.csv`

If the Kaggle file is not found, the pipeline generates synthetic data as fallback.

## Core Metrics

- LTV: `LTV = ARPU * Expected Retention * Gross Margin`
- CAC: `CAC = Marketing Spend / Customers Acquired`
- LTV/CAC ratio by channel
- RFM segmentation (`VIP`, `Loyal`, `At Risk`, `Hibernating`)
- Cohort retention by acquisition month
- Unit economics:
- contribution margin
- payback period
- gross margin-aware efficiency indicators

## Machine Learning

- Churn Prediction: `RandomForestClassifier`
- Next Purchase (30d): `LogisticRegression`
- Validation: K-Fold ROC-AUC
- Outputs:
- scored customers
- model artifacts (`joblib`)
- ROC/PR curve points available in pipeline results

## Recommendation Engine

Rule-based strategic actions:
- `churn_prob > 0.7` -> `Retention Campaign`
- `high LTV + low churn` -> `Upsell Offer`
- `low LTV + high CAC` -> `Reduce Acquisition Spend`
- otherwise -> `Nurture`

The executive app also estimates potential financial impact per customer/action.

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

## Outputs Generated

After `python main.py`, check `data/processed/` for:
- `scored_customers.csv`
- `recommendations.csv`
- `ltv.csv`
- `rfm_segments.csv`
- `cohort_retention.csv`
- `unit_economics.csv`
- `churn_model.joblib`
- `next_purchase_model.joblib`
- `dim_customers.csv`, `dim_date.csv`, `fact_orders.csv`

## 30-Day Delivery Roadmap

1. Week 1: Data ingestion + star schema baseline.
2. Week 2: KPI analytics layer and executive reporting.
3. Week 3: ML hardening (temporal validation, drift checks, explainability).
4. Week 4: Recommendation optimization + production deployment.
