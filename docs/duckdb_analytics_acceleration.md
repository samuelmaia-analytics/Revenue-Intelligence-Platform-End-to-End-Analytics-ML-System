# DuckDB Analytics Acceleration

## Purpose

Use DuckDB as the SQL execution engine for `metrics.curated` while keeping the batch runtime and output contracts unchanged.

## What changed

- `src/analytics.py` now prefers DuckDB for:
  - `cac_by_channel.csv`
  - `rfm_segments.csv`
  - `cohort_retention.csv`
- the stage still writes the same governed artifacts into `data/processed`
- `recommendations.csv`, `unit_economics.csv`, and executive outputs continue to derive from the same governed business logic

## Why this matters

- reduces repeated CSV parsing and Python-side groupby work
- makes the analytics layer more SQL-native and easier to reason about for enterprise reviewers
- creates a cleaner bridge between batch runtime, SQL examples, dbt marts, and BI consumers

## Runtime posture

- DuckDB is an execution detail, not a second source of truth
- the canonical runtime path is still `python -m src.pipeline run`
- if DuckDB is unavailable, the pipeline falls back to the existing pandas logic

## Result

In the Olist-backed local run used during this upgrade, `metrics.curated` dropped to roughly 4 seconds while preserving the same output contract surface.
