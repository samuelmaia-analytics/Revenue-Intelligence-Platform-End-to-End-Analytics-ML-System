# Technical One-Pager

## Architecture Summary

- batch-first analytical core
- governed contracts and processed outputs
- SQLite-first warehouse for reproducible delivery
- downstream app, API, SQL, dbt, and export surfaces
- observability through manifests, snapshots, validation reports, and run logs

## Operating Model

- `python -m src.pipeline run` is the canonical runtime
- Streamlit and API are downstream consumers
- runtime policy is environment-driven and testable
- releases are documented and operationally constrained

## Why This Is Delivery-Friendly

- inspectable end to end
- low infra friction for demos and pilots
- clear extension path into client environments
- controlled adaptation surface across contracts, configs, and downstream consumers

## Technical Credibility Signals

- ADRs
- incident playbooks
- merge policy
- release notes
- smoke tests for app, API, dbt, SQL, and exports
