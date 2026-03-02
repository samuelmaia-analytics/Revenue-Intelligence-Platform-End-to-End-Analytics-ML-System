# Revenue Intelligence Platform - Sistema Executivo de Analytics e ML

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-pronto-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Licença](https://img.shields.io/badge/Licença-MIT-black.svg)](LICENSE)

[Read in English](README.md)

## Sumário

- [App em Produção](#app-em-produ%C3%A7%C3%A3o)
- [Resumo Executivo](#resumo-executivo)
- [Resultados de Negócio](#resultados-de-neg%C3%B3cio)
- [Escopo e Capacidades](#escopo-e-capacidades)
- [Arquitetura](#arquitetura)
- [Estrutura do Repositório](#estrutura-do-reposit%C3%B3rio)
- [Fonte de Dados](#fonte-de-dados)
- [Como Rodar (Windows / PowerShell)](#como-rodar-windows--powershell)
- [CLI](#cli)
- [Qualidade de Engenharia](#qualidade-de-engenharia)
- [Docker](#docker)
- [Principais Saídas](#principais-sa%C3%ADdas)


## App em Produção

Streamlit Cloud:
- https://revenue-intelligence-platform.streamlit.app/

## Resumo Executivo

A Revenue Intelligence Platform é um sistema de decisão comercial de ponta a ponta que transforma dados de comportamento em prioridades executivas.

## Resultados de Negócio

- Carteira priorizada com impacto financeiro estimado
- Eficiência por canal com `LTV/CAC` e unit economics
- Sinalização de risco de churn e nova compra por cliente
- Narrativa executiva para rituais semanais de gestão

## Escopo e Capacidades

- Ingestão de dados com fonte Kaggle e fallback sintético
- Engenharia de features e scoring por cliente
- Saídas em Star Schema para analytics
- Camada de KPIs: LTV, CAC, RFM, Coorte, Unit Economics
- Camada de ML: churn e nova compra
- Motor de recomendação de próxima melhor ação
- Dashboard executivo com governança e exportação
  (`Executive Overview`, `Risk & Growth`, `Action List`)

## Arquitetura

Fonte de Dados Kaggle
-> Camada Raw
-> Bronze (ingestão auditável)
-> Silver (limpeza e padronização)
-> Gold (Star Schema)
-> Camada Analítica (KPIs em CSV + SQL)
-> Camada de ML (churn e próxima compra)
-> Motor de Recomendação
-> Dashboard Executivo
-> Deploy com Docker / Cloud

## Estrutura do Repositório

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

## Fonte de Dados

Arquivo principal:
- `data/raw/E-commerce Customer Behavior - Sheet1.csv`

Fonte:
- Dataset Kaggle: `E-commerce Customer Behavior Dataset`

Mapeado automaticamente para:
- `customers.csv`
- `orders.csv`
- `marketing_spend.csv`

Depois normalizado em:
- `data/bronze/*.csv`
- `data/silver/*.csv`
- `data/gold/dim_*.csv` e `data/gold/fact_*.csv`

## Como Rodar (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
python -m streamlit run .\app\streamlit_app.py
```

Sobrescritas via ambiente:
- `RIP_DATA_DIR`
- `RIP_SEED`
- `RIP_LOG_LEVEL`

## CLI

```powershell
python -m src.pipeline run
python -m src.pipeline run --seed 123 --log-level DEBUG
```

## Qualidade de Engenharia

```powershell
python -m pip install -r requirements-dev.txt
python -m black .
python -m ruff check . --fix
python -m pytest -q
pre-commit install
pre-commit run --all-files
```

Gates atuais de qualidade:
- `tests/test_output_contract.py` valida geração dos arquivos de saída e colunas mínimas do schema Gold.
- `main.py` inicializa a execução com `PipelineConfig.from_env(...)` para configuração determinística.

## Docker

```bash
docker build -t revenue-intelligence .
docker run -p 8501:8501 revenue-intelligence
```

## Principais Saídas

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





