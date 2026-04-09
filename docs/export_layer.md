# Export Layer

## Purpose

Expose governed outputs to external consumers without creating a second analytical logic path.

## Supported Consumption Modes

- Streamlit executive workspace consuming processed artifacts
- FastAPI external serving surface
- governed CSV exports in `data/processed`
- warehouse SQL consumption
- downstream dbt models over warehouse outputs
- DuckDB-accelerated curated analytics feeding the same governed outputs

## Recommended Client-Facing Export Options

### Power BI

- connect to the warehouse tables for governed reporting
- use curated marts or processed scorecards as the import layer
- use `sql/analytics/004_power_bi_scorecard.sql` as the reference scorecard query

### Streamlit

- use the app as the executive command center and managed demo surface

### API

- use the FastAPI layer for external scoring and lightweight operational status
- expose executive summary, insight draft, reliability report, and governed CSV exports for demos and external consumers

### Governed CSV

- use processed exports for controlled data sharing, ad hoc executive packs, or partner delivery

## Design Rules

- batch runtime remains the system of record
- export contracts must reuse governed processed assets or warehouse outputs
- every export mode must preserve lineage to a known run and artifact set
- client adaptation should configure destinations and access patterns, not fork business logic
- scorecard-style API exports should reuse semantic metrics and governed processed artifacts
- DuckDB may accelerate internal curated analytics, but it does not create a parallel export contract
