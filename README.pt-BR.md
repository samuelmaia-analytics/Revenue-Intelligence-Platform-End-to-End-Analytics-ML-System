# Revenue Intelligence Platform - Sistema Executivo de Analytics e ML

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-pronto-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Licença](https://img.shields.io/badge/Licença-MIT-black.svg)](LICENSE)

[Read in English](README.md)

## Resumo Executivo

A Revenue Intelligence Platform é um sistema de decisão comercial de ponta a ponta que transforma dados de comportamento de clientes em prioridades objetivas de negócio.

Responde diretamente a três perguntas de diretoria:

- Onde a receita está em risco?
- Onde acelerar crescimento com maior eficiência?
- Quais clientes priorizar imediatamente?

## Resultados de Negócio

- Carteira de ações priorizada por cliente com impacto financeiro estimado.
- Visibilidade de eficiência por canal com `LTV/CAC` e unit economics.
- Sinalização de risco de churn e probabilidade de nova compra.
- Narrativa executiva pronta para rituais semanais de gestão comercial.

## Escopo e Capacidades

- Ingestão de dados via Kaggle com fallback sintético.
- Engenharia de features e base de scoring por cliente.
- Saídas em Star Schema para interoperabilidade analítica.
- Camada de KPIs: LTV, CAC, RFM, Coorte, Unit Economics.
- Camada de ML: predição de churn e de nova compra.
- Motor de recomendação de próxima melhor ação.
- Dashboard executivo em Streamlit com governança e exportação.

## Arquitetura

Fonte de Dados (CSV Kaggle / fallback sintético)  
-> Ingestão (Python)  
-> Limpeza e Engenharia de Features  
-> Saídas de Warehouse (Star Schema)  
-> Camada Analítica (KPI + Coorte + Unit Economics)  
-> Camada de ML (Churn + Nova Compra)  
-> Motor de Recomendação  
-> Dashboard Executivo (Streamlit)  
-> Deploy com Docker / Cloud

## Estrutura do Repositório

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

## Governança de Modelos

O pipeline grava métricas de governança em:

- `data/processed/metrics_report.json`

Inclui:

- estratégia de split (temporal ou fallback controlado)
- ROC-AUC de validação cruzada
- ROC-AUC de holdout

## Dashboard Executivo

`app/streamlit_app.py` entrega:

- cards executivos de KPI
- leitura de diretoria (risco, oportunidade e prioridade)
- plano de ação por cliente com exportação CSV
- análise de performance comercial
- visão de governança dos modelos

## Fonte de Dados

Arquivo principal:

- `data/raw/E-commerce Customer Behavior - Sheet1.csv`

Convertido automaticamente para:

- `customers.csv`
- `orders.csv`
- `marketing_spend.csv`

## Como Rodar (Windows / PowerShell)

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

## Saídas

Arquivos principais gerados em `data/processed/`:

- `scored_customers.csv`
- `recommendations.csv`
- `cohort_retention.csv`
- `unit_economics.csv`
- `metrics_report.json`
- `churn_model.joblib`
- `next_purchase_model.joblib`

## Plano de Entrega (30 dias)

1. Semana 1: confiabilidade de dados e baseline de warehouse.
2. Semana 2: estabilização da camada de KPIs e visão executiva.
3. Semana 3: robustez de modelos e governança.
4. Semana 4: otimização das recomendações e deploy em produção.

