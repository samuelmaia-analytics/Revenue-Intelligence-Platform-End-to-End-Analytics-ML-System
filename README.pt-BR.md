# Revenue Intelligence Platform - Sistema de Analytics e ML de Ponta a Ponta

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-pronto-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Projeto%20de%20Portfólio-0f766e)](#)
[![Licença](https://img.shields.io/badge/Licença-MIT-black.svg)](LICENSE)

[Read in English](README.md)

## Sumário

- [Objetivo de Negócio](#objetivo-de-negócio)
- [Arquitetura End-to-End](#arquitetura-end-to-end)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Fonte de Dados](#fonte-de-dados)
- [Métricas Implementadas](#métricas-implementadas)
- [Camada de Machine Learning](#camada-de-machine-learning)
- [Motor de Recomendação](#motor-de-recomendação)
- [Como Rodar (Windows / PowerShell)](#como-rodar-windows--powershell)
- [Docker](#docker)
- [Arquivos Gerados](#arquivos-gerados)
- [Roadmap de 30 Dias](#roadmap-de-30-dias)

Produto de analytics de receita com abordagem executiva, combinando inteligência de clientes, modelos preditivos e priorização de ações em um único painel.

## Objetivo de Negócio

Transformar dados brutos de comportamento de clientes em decisões executivas claras:
- Onde a receita está em risco.
- Quais clientes devem receber ação de retenção ou upsell.
- Quais canais de aquisição são mais eficientes financeiramente.

## Arquitetura End-to-End

Fonte de Dados (CSV Kaggle / fallback sintético)  
-> Ingestão de Dados (Python)  
-> Limpeza e Engenharia de Features  
-> Saídas de Data Warehouse SQL (Star Schema)  
-> Camada Analítica (LTV, CAC, RFM, Cohort, Unit Economics)  
-> Camada de ML (Churn + Probabilidade de Nova Compra)  
-> Motor de Recomendação (Próxima Melhor Ação)  
-> App Executivo em Streamlit  
-> Deploy com Docker / Cloud

## Estrutura do Projeto

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
\- (pastas locais excluídas: .venv, .idea, __pycache__)
```

## Fonte de Dados

Fonte principal:
- `data/raw/E-commerce Customer Behavior - Sheet1.csv` (Kaggle)

A camada de ingestão converte automaticamente esse dataset em:
- `customers.csv`
- `orders.csv`
- `marketing_spend.csv`

Se o arquivo Kaggle não estiver presente, o pipeline gera dados sintéticos como fallback.

## Métricas Implementadas

- LTV: `LTV = ARPU * Retenção Esperada * Margem Bruta`
- CAC: `CAC = Marketing Spend / Clientes Adquiridos`
- Razão LTV/CAC por canal
- Segmentação RFM (`VIP`, `Loyal`, `At Risk`, `Hibernating`)
- Retenção por cohort de aquisição
- Unit economics: margem de contribuição, payback period e indicadores de eficiência com margem bruta

## Camada de Machine Learning

- Predição de churn: `RandomForestClassifier`
- Predição de nova compra em 30 dias: `LogisticRegression`
- Validação com K-Fold ROC-AUC
- Saídas: score de clientes, artefatos de modelo (`joblib`) e pontos de curvas ROC/PR

## Motor de Recomendação

Regras estratégicas:
- `churn_prob > 0.7` -> `Retention Campaign`
- `LTV alto + churn baixo` -> `Upsell Offer`
- `LTV baixo + CAC alto` -> `Reduce Acquisition Spend`
- Caso contrário -> `Nurture`

O app executivo também estima impacto financeiro potencial por cliente/ação.

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

## Arquivos Gerados

Depois de executar `python main.py`, confira `data/processed/`:
- `scored_customers.csv`
- `recommendations.csv`
- `ltv.csv`
- `rfm_segments.csv`
- `cohort_retention.csv`
- `unit_economics.csv`
- `churn_model.joblib`
- `next_purchase_model.joblib`
- `dim_customers.csv`, `dim_date.csv`, `fact_orders.csv`

## Roadmap de 30 Dias

1. Semana 1: ingestão de dados e base star schema.
2. Semana 2: camada analítica e indicadores executivos.
3. Semana 3: robustez de ML (validação temporal, drift, explicabilidade).
4. Semana 4: otimização de recomendações e deploy em produção.

