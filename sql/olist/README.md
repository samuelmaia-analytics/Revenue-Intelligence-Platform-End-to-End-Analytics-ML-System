# Olist Query Pack

Queries executivas e analíticas prontas para uso com:

```powershell
python -m src.file_queries --file sql/olist/001_revenue_by_state.sql
```

Objetivo:

- acelerar análises sobre os CSVs governados
- demonstrar consumo por SQL sem recriar a lógica do pipeline
- oferecer cortes curados para receita, sellers, cohort, RFM, churn proxy, pagamentos, logística e resumo executivo

Arquivos:

- `001_revenue_by_state.sql`: receita, ticket e qualidade operacional por estado
- `002_seller_delay_risk.sql`: sellers com maior atraso relativo e relevância comercial
- `003_cohort_retention_curve.sql`: curva de retenção por coorte
- `004_rfm_segment_summary.sql`: resumo de segmentos RFM
- `005_category_churn_proxy.sql`: proxy de churn por categoria com receita associada
- `006_payment_mix_quality.sql`: mix de pagamentos com qualidade de entrega e satisfação
- `007_logistics_monthly_summary.sql`: resumo mensal de entrega, atraso e cancelamento
- `008_satisfaction_monthly_trend.sql`: tendência mensal de satisfação e promotores
- `009_seller_concentration.sql`: concentração de receita entre sellers
- `010_executive_monthly_summary.sql`: resumo executivo mensal com receita, retenção e entrega
- `011_customer_retention_action_matrix.sql`: matriz de retenção por ação, RFM e faixa de churn
- `012_category_performance_deep_dive.sql`: deep dive de categorias com receita, frete e risco
- `013_geography_opportunity_ranking.sql`: ranking geográfico por valor e qualidade operacional
- `014_seller_watchlist.sql`: watchlist executiva de sellers relevantes com sinal de risco
- `015_executive_one_pager_extract.sql`: extrato de uma linha para one-pager executivo

Camada adicional:

- `views/`: consultas board-ready, organizadas por tema, para demo executiva rápida
