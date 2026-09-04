# Revenue Intelligence Platform

> **Projeto legado de portfólio.** Este repositório foi preservado como histórico técnico. O portfólio principal atual está concentrado em [Governed Analytics Platform](https://github.com/samuelmaia-analytics/Governed-Analytics-Platform), Central de Automação e Operações e [AWS Serverless Access Counter](https://github.com/samuelmaia-analytics/aws-serverless-access-counter).

Projeto de portfólio em **Data Analytics, Analytics Engineering e Machine Learning** que transforma comportamento de clientes e pedidos em outputs governados para análise de receita, retenção e priorização de ações.

## O problema

Times de receita precisam responder perguntas como:

- Onde existe maior risco de perda de receita?
- Quais clientes ou segmentos devem ser priorizados?
- Como retenção, recorrência e comportamento afetam o crescimento?
- Os dados e métricas estão confiáveis para uso executivo?
- As regras analíticas estão centralizadas ou espalhadas por dashboards?

## A solução

```text
Dados brutos
 → Bronze
 → Silver
 → features e scoring
 → analytics curado
 → monitoring
 → warehouse
 → Streamlit / API / SQL / dbt
```

O pipeline batch é a fonte de verdade. As camadas de consumo reutilizam os outputs processados, evitando duplicação de regras no dashboard.

## Principais entregas

- Pipeline reprocessável com camadas Bronze, Silver e outputs curados.
- Analytics de receita, retenção, coortes e clientes.
- Churn proxy, propensão de próxima compra, LTV proxy e segmentação RFM.
- Scorecards executivos para receita, clientes, pagamentos, sellers, categorias, estados e operação.
- Warehouse local para consumo SQL.
- Camada analítica compatível com dbt.
- Dashboard Streamlit baseado nos artefatos governados.
- API e exports para consumo downstream.
- Validações de qualidade, contratos, manifests e evidências de execução.
- Testes automatizados e CI/CD.

## Valor demonstrado

O projeto demonstra como transformar análises de receita em um produto analítico reproduzível: uma única camada de métricas alimenta diferentes consumidores, outputs são validados antes do uso e decisões comerciais podem ser apoiadas por segmentação, risco e priorização.

> Métricas como CAC e unit economics são explicitamente tratadas como proxies quando a fonte não possui gasto real de aquisição. O projeto prioriza transparência em vez de precisão artificial.

## Stack

**Dados e Analytics Engineering:** Python, SQL, pandas, DuckDB, SQLite, dbt  
**Machine Learning:** scikit-learn, features, scoring e model registry  
**Consumo:** Streamlit, API, exports e SQL  
**Qualidade e governança:** contratos, manifests, validações, logs e snapshots  
**Engenharia:** pytest, Ruff, Black, mypy, GitHub Actions, Docker

## Principais domínios analíticos

- Receita e scorecard executivo
- Clientes, RFM e retenção
- Churn-risk proxy
- Produtos e categorias
- Sellers
- Logística e atraso
- Pagamentos
- Geografia
- Cenários e priorização comercial

## Como revisar este projeto em 5 minutos

1. Leia esta página para entender o problema e a arquitetura.
2. Explore `src/` para o pipeline e lógica analítica.
3. Veja `contracts/` e os mecanismos de validação.
4. Consulte `app/` para entender como o dashboard consome os outputs governados.
5. Explore `docs/` para arquitetura, governança e runbooks.

## Execução principal

```powershell
python -m src.pipeline run
```

Streamlit:

```powershell
python -m streamlit run app/streamlit_app.py
```

Validação:

```powershell
make verify
make smoke-dashboard
make pipeline
```

## Decisões e limitações

- Arquitetura batch-first por escolha de escopo.
- Warehouse local para favorecer reprodutibilidade.
- Métricas de aquisição são proxies quando a fonte não oferece custo real.
- O projeto é inspirado em práticas de produção, mas é uma solução de portfólio.

## Documentação

- [Visão geral](docs/README.md)
- [Arquitetura](docs/architecture.md)
- [Governança](docs/governance_framework.md)
- [Runbook](docs/runbook.md)
- [Modelo analítico Olist](docs/olist_analytics_model.md)
- [Revisão para contratação](docs/hiring_review.md)

## Autor

Samuel Maia — Analista de Dados | Analytics Engineer

- LinkedIn: https://www.linkedin.com/in/samuelmaia-analytics/
- GitHub: https://github.com/samuelmaia-analytics

Versões localizadas: [PT-BR](README.pt-BR.md) · [PT-PT](README.pt-PT.md)
