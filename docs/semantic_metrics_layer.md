# Semantic Metrics Layer

## Purpose

Make the core business metrics portable, governed, and explainable across dashboard, API, SQL, and dbt consumers.

## Source Of Truth

- metric definitions: `metrics/semantic_metrics.json`
- generated catalog: `data/processed/semantic_metrics_catalog.json`
- downstream dbt model: `dbt/models/marts/finance/portfolio_semantic_metrics.sql`

## Design Rules

- define a metric once in the semantic catalog
- document owner, grain, decision use, and consumer surfaces
- keep downstream dbt and API surfaces aligned to the same business meaning
- use the batch runtime and processed outputs as the canonical computation path

## Core Metrics

- `revenue_proxy`
- `avg_ltv`
- `avg_cac`
- `avg_ltv_cac_ratio`
- `high_churn_risk_pct`

## Enterprise Relevance

This is the layer that reduces metric ambiguity between executive dashboards, analytics teams, and commercial stakeholders. It is also the bridge between the local pipeline story and a more enterprise-style semantic model approach.
