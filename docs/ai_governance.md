# AI Governance

## Purpose

Use AI only as an optional assistive layer for executive insight drafting, never as the source of record for metrics, scoring, or decisions.

## Current Operating Mode

- default mode: `deterministic`
- optional mode: `assistive`
- current governed runtime behavior: assistive requests fall back to deterministic output unless an approved LLM execution path is explicitly implemented

## Design Rules

- the pipeline remains the source of truth
- insight drafts must reference governed artifacts
- drafted text must carry mode, provider, model, and fallback metadata
- deterministic fallback must always exist
- dashboards consume the draft artifact, not ad hoc runtime prompting

## Governed Artifact

`data/processed/insight_draft.json`

Required properties:

- generation timestamp
- run id
- requested mode and applied mode
- LLM metadata and fallback reason
- drafted headline, summary, highlights, anomalies, and recommended actions
- evidence block tied to governed artifacts

## Environment Controls

- `RIP_INSIGHT_DRAFT_MODE`
- `RIP_LLM_PROVIDER`
- `RIP_LLM_MODEL`

## Non-Goals

- free-form agentic decision making
- replacing scorecards, KPIs, or contracts
- generating numbers independently from governed outputs
