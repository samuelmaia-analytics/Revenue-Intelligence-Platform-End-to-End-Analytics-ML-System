# Lineage And Traceability

## Purpose

Make the flow from source data to executive consumption explicit for technical sponsors, delivery teams, and enterprise buyers.

## Canonical Lineage

1. Raw inputs land in `data/raw/`.
2. Bronze copies preserve ingestion metadata in `data/bronze/`.
3. Silver applies validation, normalization, and referential controls in `data/silver/`.
4. Features, scoring, and recommendations are generated in `data/processed/`.
5. Gold and warehouse-ready outputs are persisted in `data/gold/` and `data/warehouse/`.
6. Executive dashboard, API exports, SQL, and dbt consume those governed outputs downstream.

## Traceability Anchors

- `run_id` in `pipeline_manifest.json`
- `input_fingerprint` in runtime artifacts
- `raw_input_metadata.json`
- `freshness_report.json`
- `runtime_metrics.json`
- `run_events.jsonl`
- `insight_draft.json`
- `reliability_report.json`

## Consumer Surfaces

- Streamlit command center
- API executive and export surfaces
- governed CSV exports
- warehouse SQL reads
- dbt downstream marts

## Design Rule

No consumer surface should become an alternate orchestration center or independent source of truth.
