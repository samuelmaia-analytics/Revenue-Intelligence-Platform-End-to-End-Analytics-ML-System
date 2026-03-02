# Revenue Intelligence Platform - Executive Analytics & ML System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

[Leia em Português](README.pt-BR.md)

## Summary

- [Live App](#live-app)
- [Executive Summary](#executive-summary)
- [Business Outcomes](#business-outcomes)
- [Scope and Capabilities](#scope-and-capabilities)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Data Source](#data-source)
- [Star Schema (Gold)](#star-schema-gold)
- [SQL Organization](#sql-organization)
- [Local Run (Windows / PowerShell)](#local-run-windows--powershell)
- [CLI](#cli)
- [Engineering Quality](#engineering-quality)
- [Docker](#docker)
- [Main Outputs](#main-outputs)
- [Streamlit Cloud](#streamlit-cloud)

## Live App

Streamlit Cloud:
- https://revenue-intelligence-platform.streamlit.app/

## Executive Summary

Revenue Intelligence Platform is an end-to-end decision system that converts customer behavior data into commercial priorities.

This version includes a mature layered data architecture (`raw -> bronze -> silver -> gold`) with a formal Star Schema and structured SQL domains for analytics.

## Business Outcomes

- Prioritized customer action list with estimated financial impact
- Channel efficiency visibility with `LTV/CAC` and unit economics
- Customer-level churn risk and next purchase probability
- Executive narrative for weekly business reviews

## Scope and Capabilities

- Data ingestion from Kaggle source with synthetic fallback
- Layered pipeline: raw, bronze, silver, gold
- Feature engineering and customer-level scoring
- Star schema outputs for analytics interoperability
- KPI layer: LTV, CAC, RFM, Cohort Retention, Unit Economics
- ML layer: churn + next purchase prediction
- Recommendation engine for next best action
- Executive Streamlit dashboard with governance and exports
- Structured SQL domains (`ddl/` and `analytics/`)

## Architecture

Kaggle Source Dataset
-> Raw Layer
-> Bronze (auditable ingestion)
-> Silver (cleaning and standardization)
-> Gold (Star Schema)
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
|  |- bronze/
|  |- silver/
|  |- gold/
|  \- processed/
|- notebooks/
|- src/
|- sql/
|  |- ddl/
|  \- analytics/
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

Then normalized into:
- `data/bronze/*.csv`
- `data/silver/*.csv`
- `data/gold/dim_*.csv` and `data/gold/fact_*.csv`

## Star Schema (Gold)

- Dimensions: `dim_date`, `dim_customers`, `dim_channel`
- Fact: `fact_orders`
- Standardized measures: `order_amount`, `order_count`

## SQL Organization

- `sql/ddl/`: schema creation scripts per table/domain
- `sql/analytics/`: executive queries (revenue KPIs, channel efficiency, churn watchlist)
- `sql/create_tables.sql`: consolidated bootstrap script

## Local Run (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
python -m streamlit run .\app\streamlit_app.py
```

## CLI

```powershell
python -m src.pipeline run
python -m src.pipeline run --seed 123 --log-level DEBUG
```

## Engineering Quality

```powershell
python -m pip install -r requirements-dev.txt
python -m black .
python -m ruff check . --fix
python -m pytest -q
pre-commit install
pre-commit run --all-files
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
- `data/processed/executive_report.json`
- `data/processed/dim_customers.csv`
- `data/processed/dim_date.csv`
- `data/processed/dim_channel.csv`
- `data/processed/fact_orders.csv`

## Streamlit Cloud

- Main file path: `app/streamlit_app.py`
- Dependency file: `requirements.txt`
- Kaggle CSV is versioned in `data/raw/` for deterministic cloud runs


