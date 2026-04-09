# Power BI Consumption

## Purpose

Provide a governed Power BI path without reimplementing business logic in the BI layer.

## Recommended connection modes

### 1. Warehouse-first

Use `data/warehouse/revenue_intelligence.db` or an equivalent promoted warehouse target and import:

- `recommendations`
- `unit_economics`
- `scored_customers`
- `top_10_actions`

This is the preferred path for executive scorecards and drilldowns.

### 2. Processed-export-first

Use governed processed exports when a lightweight handoff is more important than a live warehouse connection:

- `executive_summary.json`
- `reliability_report.json`
- `recommendations.csv`
- `unit_economics.csv`
- `top_10_actions.csv`

## Design rules

- do not recreate LTV, CAC, or recommendation logic in Power BI
- keep Power BI as a presentation and slicing surface
- tie every dashboard refresh to a known pipeline run and artifact set
- use dbt marts or SQL examples when semantic reshaping is needed downstream

## Reference assets

- `sql/analytics/004_power_bi_scorecard.sql`
- `docs/export_layer.md`
- `docs/dbt_semantic_story.md`
