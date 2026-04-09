# dbt Semantic Story

## Objective

Explain how dbt extends the platform without replacing the canonical runtime.

## Current Pattern

- the pipeline computes and governs the operational outputs
- the warehouse persists analytical tables
- dbt models semantic marts downstream for SQL-native and documentation-friendly consumption

## Why This Matters

- technical sponsors can inspect semantic marts in dbt form
- buyer teams can see an upgrade path toward enterprise-style analytics governance
- the repository stays honest because dbt is downstream, not a parallel orchestration layer

## Recommended Reading

1. `metrics/semantic_metrics.json`
2. `src/semantic_metrics.py`
3. `dbt/models/marts/finance/portfolio_semantic_metrics.sql`
4. `dbt/models/exposures.yml`
5. `docs/semantic_metrics_layer.md`
