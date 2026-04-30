# Revenue Intelligence Platform

Production-minded revenue analytics repository that turns customer and order behavior into governed batch outputs, warehouse-ready tables, executive decision artifacts, and a Streamlit workspace for actioning revenue opportunities.

Language versions:

- [Português do Brasil](README.pt-BR.md)
- [Português de Portugal](README.pt-PT.md)

## Executive Summary

This repository is an analytics operating system for revenue teams.

It is designed to be used in three ways:

- as a trusted analytical foundation
- as an executive revenue command center
- as a recurring analytics operating model for client delivery

It answers the questions executive buyers and technical sponsors care about:

- Is there one official runtime path?
- Can the pipeline be reprocessed safely?
- Are outputs validated and governed?
- Is there operational evidence when runs fail?
- Can leadership consume trusted business outputs without recreating logic in dashboards?

Short answer: yes.

## Buyer Snapshot

In less than 30 seconds, a buyer or sponsor should see that this repository has:

- one official batch runtime path
- governed outputs with contracts and validation
- operational evidence through manifests, snapshots, and quality reports
- downstream consumption through Streamlit, API, SQL, dbt, and governed exports
- delivery discipline that supports both technical credibility and commercial packaging

## Why This Repository Exists

Most data portfolio projects stop at notebooks, ad hoc scripts, or a standalone dashboard. This repository is intentionally narrower and more operational:

- one official batch entrypoint
- deterministic and reprocessable outputs
- runtime manifests, logs, snapshots, and retention rules
- governed processed artifacts with validation and contracts
- downstream consumers that read the batch core instead of replacing it
- registry-backed model reuse when feature inputs have not changed

The goal is not to simulate an enterprise platform without substance. The goal is to demonstrate sound engineering judgment in a repository small enough to inspect end-to-end.

## Business Value

The platform converts customer behavior data into assets that support commercial and retention decisions:

- churn risk and next-purchase propensity
- unit economics by acquisition channel
- cohort retention analysis
- customer-level recommendations with simulated impact
- executive KPI snapshots, risk scorecards, and monitoring outputs
- warehouse tables ready for SQL and dbt-style consumption
- DuckDB-accelerated curated metrics for SQL-native downstream analytics

Supported raw-source patterns:

- normalized local raw tables under `data/raw/`
- the prior single-file Kaggle customer-behavior sample
- the Brazilian E-Commerce Public Dataset (`olist_*`) now mapped into the platform's governed raw contracts

This is not just a portfolio dashboard. It is a productizable operating layer for revenue analytics with explicit runtime ownership, governed outputs, and downstream accountability.

## Olist Executive Layer

The current implementation now uses the available Olist marketplace CSVs as the main analytical source rather than compressing them into a thin demo schema.

What the runtime now delivers from the Olist base:

- enriched silver entities for customers, orders, order items, payments, reviews, products, sellers, and geography
- expanded gold tables for warehouse consumption, including seller, product, geography, and order-item structures
- executive KPIs for revenue, order volume, average ticket, freight, recurring customers, fulfillment delay, cancellations, review score, category concentration, seller concentration, and state-level performance
- customer analytics with churn proxy, next-purchase propensity, LTV proxy, RFM segmentation, and prioritized actions
- curated marts for logistics, payments, geography, products, categories, sellers, and executive monthly scorecards
- BI-ready curated scorecards for executive summary, customer segment health, payments, retention, sellers, categories, states, and operations
- a Streamlit workspace that reads governed outputs instead of reimplementing metric logic in the UI

Important policy note:

- CAC and unit economics remain explicitly labeled as proxy metrics because the Olist dataset does not contain real acquisition spend.
- The repository now prefers transparent proxy logic over implied precision.

## Who It Serves

### CEOs and Founders

- understand revenue at risk and quality of growth
- get a leadership-ready command center instead of fragmented reports
- inspect whether business decisions are backed by trusted data

### Revenue and Commercial Leaders

- prioritize save, expand, and nurture actions
- compare segment and channel performance
- use scenario views to guide intervention

### Operations

- inspect freshness, artifact validity, and active alerts
- understand whether the current analytical cycle is safe to circulate

### Analytics and Data Teams

- work from one governed runtime
- preserve lineage from source to dashboard
- extend downstream consumption through API, SQL, dbt, and exports

## Productized Offers

- Trusted Analytics Foundation
- Executive Revenue Dashboard
- Recurring Analytics Operations

Commercial references:

- [docs/commercial/offers.md](docs/commercial/offers.md)
- [docs/commercial/evidence_pack.md](docs/commercial/evidence_pack.md)
- [docs/client_adaptation/adaptation_framework.md](docs/client_adaptation/adaptation_framework.md)

## Official Runtime Path

```powershell
python -m src.pipeline run
```

The batch pipeline is the system of record. The Streamlit app, API layer, warehouse, and dbt project all consume outputs produced by it.

## Architecture

```mermaid
flowchart LR
    A[Raw inputs, Olist ecommerce source, or synthetic source] --> B[Bronze]
    B --> C[Silver]
    C --> D[Features and scoring]
    D --> E[Curated analytics]
    E --> F[Reporting and monitoring]
    D --> G[Warehouse]
    F --> H[Streamlit]
    F --> I[API and dbt consumers]
    G --> I
```

Key characteristics:

- batch-first architecture with local reproducibility
- explicit runtime policy for retries, retention, freshness, and quality thresholds
- processed and operational report validation before pipeline completion
- SQLite warehouse by default, with compatibility paths for service and dbt consumers

Core business domains now surfaced in the governed output layer:

- executive summary and monthly scorecard
- customer intelligence, retention, cohort, RFM, and churn-risk proxy
- product and category performance
- seller concentration and seller quality
- logistics, delay, on-time delivery, and satisfaction
- payments and state-level geography analytics

Primary curated BI files:

- `data/processed/executive_scorecard.csv`
- `data/processed/customer_segment_health.csv`
- `data/processed/payment_scorecard.csv`
- `data/processed/retention_scorecard.csv`
- `data/processed/seller_scorecard.csv`
- `data/processed/category_scorecard.csv`
- `data/processed/state_scorecard.csv`
- `data/processed/operations_scorecard.csv`

## Repository Structure

```text
.
|- .github/                CI workflows, issue templates, and repository governance
|- app/                    Streamlit presentation layer
|  |- ui/                  reusable UI primitives and styles
|  |- views/               page sections and dashboard composition
|  |- dashboard_data.py    cached artifact loading and filtering
|  |- dashboard_i18n.py    EN, PT-BR, and PT-PT language dictionaries
|  |- dashboard_metrics.py shared formatting and KPI helpers
|- src/                    batch pipeline, modeling, reporting, warehouse, and runtime policy
|- contracts/              versioned governed schemas and compatibility shims
|- services/               runtime-facing service interfaces
|- api/                    compatibility shim for API imports
|- tests/                  behavioral, reliability, contract, API, and warehouse coverage
|- docs/                   architecture, onboarding, runbooks, ADRs, and release notes
|- scripts/                smoke tests and lightweight operational automation
|- dbt/                    downstream analytical layer on top of warehouse outputs
|- orchestration/          scheduler examples and deployment wrappers
|- metrics/                semantic metric definitions consumed by the pipeline
|- sql/                    warehouse DDL and downstream SQL assets
|- data/                   local runtime outputs, manifests, snapshots, and warehouse
|- notebooks/              isolated exploration, kept out of the official runtime path
|- main.py                 minimal Python entrypoint wrapper
|- Dockerfile*             container builds for Streamlit, batch, and API surfaces
|- CHANGELOG.md            release-oriented evolution log
```

Primary references:

- [docs/README.md](docs/README.md)
- [docs/audit/executive_audit_2026-04.md](docs/audit/executive_audit_2026-04.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/olist_analytics_model.md](docs/olist_analytics_model.md)
- [docs/metric_map.md](docs/metric_map.md)
- [docs/architecture_decision_summary.md](docs/architecture_decision_summary.md)
- [docs/governance_framework.md](docs/governance_framework.md)
- [docs/runtime_surfaces.md](docs/runtime_surfaces.md)
- [docs/environments.md](docs/environments.md)
- [docs/ci_cd.md](docs/ci_cd.md)
- [docs/github_actions_workflows.md](docs/github_actions_workflows.md)
- [docs/repository_structure.md](docs/repository_structure.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
- [docs/release_process.md](docs/release_process.md)
- [docs/deprecation_policy.md](docs/deprecation_policy.md)
- [docs/merge_policy.md](docs/merge_policy.md)
- [docs/sql_examples.md](docs/sql_examples.md)
- [docs/incident_playbooks.md](docs/incident_playbooks.md)
- [docs/lgpd_data_governance.md](docs/lgpd_data_governance.md)
- [docs/hiring_review.md](docs/hiring_review.md)
- [docs/executive/one_pager.md](docs/executive/one_pager.md)
- [docs/executive/technical_one_pager.md](docs/executive/technical_one_pager.md)
- [docs/executive/decision_layer.md](docs/executive/decision_layer.md)
- [docs/executive/scorecards.md](docs/executive/scorecards.md)
- [docs/demo_enterprise_local.md](docs/demo_enterprise_local.md)

## Reliability and Data Engineering Signals

- idempotent batch execution and reprocessing support
- configurable retry policy per stage
- explicit backfill window in CLI and manifests
- freshness, quality, and processed artifact validation reports
- operational reports validated as part of the processed contract surface
- runtime manifests, logs, and snapshots for traceability
- governed `run_events.jsonl` timeline for stage-level batch observability
- warehouse persistence plus downstream consumption validation
- partner-facing payload generated from governed processed exports
- smoke-tested Streamlit dashboard in CI
- explicit container separation between dashboard, batch runtime, and API
- DuckDB-backed SQL acceleration for curated analytics without changing output contracts

## Streamlit Workspace

The dashboard is not a second source of truth. It consumes processed artifacts generated by the batch pipeline and is organized into:

- `app/ui` for layout primitives and visual consistency
- `app/views` for business sections and user flows
- `app/dashboard_data.py` for cached artifact access
- `app/dashboard_i18n.py` for `EN`, `PT-BR`, and `PT-PT`

Current presentation surfaces:

- `app/streamlit_app.py`: canonical executive command center, optimized for PT-BR-first executive storytelling and governed KPI consumption
- `app/pages/`: multipage compatibility surface that reuses the same processed artifacts and shared views for navigation by business topic

Business-oriented pages currently cover:

- executive summary
- customer and segment performance
- revenue at risk
- projections and scenarios
- operational reliability
- governance and data trust

Important UI policy:

- the Streamlit layer reads governed curated outputs and executive artifacts
- metric logic stays in the pipeline and processed layer, not in ad hoc dashboard calculations
- PT-BR is the most polished presentation path, while `EN` and `PT-PT` remain supported

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
Copy-Item .env.example .env
```

Optional dbt CLI setup in an isolated environment:

```powershell
python -m venv .dbt-venv
.dbt-venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install dbt-core dbt-sqlite
```

Important environment variables:

- `RIP_DATA_DIR`
- `RIP_WAREHOUSE_TARGET`
- `RIP_RETRY_ATTEMPTS`
- `RIP_QUALITY_MAX_NULL_FRACTION`
- `RIP_BACKFILL_START_DATE`
- `RIP_BACKFILL_END_DATE`
- `RIP_MODELING_MAX_TRAINING_ROWS`

For larger raw sources such as the Brazilian E-Commerce Public Dataset (`olist_*`), `RIP_MODELING_MAX_TRAINING_ROWS` can reduce training time while preserving full-corpus scoring and downstream outputs.

Curated analytics also prefer DuckDB when available, which keeps `metrics.curated` SQL-native and faster while preserving the same processed artifacts.
Model training also reuses registered models when the feature dataset fingerprint is unchanged, which keeps repeated local and demo runs materially faster.

## Run Commands

Pipeline:

```powershell
python -m src.pipeline run
```

Backfill:

```powershell
python -m src.pipeline run --start-date 2025-01-01 --end-date 2025-03-31
```

Streamlit:

```powershell
.\scripts\dev\start.ps1 -Target app -SkipPipeline
```

Governed file queries:

```powershell
python -m src.file_queries --list
python -m src.file_queries --sql "SELECT * FROM processed.executive_scorecard"
python -m src.file_queries --sql "SELECT * FROM raw.orders LIMIT 10"
```

Official entrypoint for local and private deploy:

```powershell
python -m streamlit run app/streamlit_app.py
```

Make-based workflow:

```powershell
make verify
make smoke-dashboard
make pipeline
make observability
```

## Validation and Automation

Core validation commands:

```powershell
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy src services contracts main.py
python -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing
python scripts/smoke_dashboard.py
python scripts/smoke_api.py
python scripts/smoke_downstream_sql.py
python scripts/smoke_processed_exports.py
python scripts/smoke_partner_payload.py
python scripts/smoke_dbt_sqlite.py
python -m build
```

Automation surfaces:

- `Makefile` for local developer workflows
- `.pre-commit-config.yaml` for fast local quality gates
- `.github/workflows/ci.yml` for lint, tests, smoke, and build validation
- `.github/workflows/ci.yml` splits quality, governance, dbt-on-SQLite, and container validation so failures are attributable
- `.github/workflows/ci.yml` also runs a dbt-on-SQLite downstream smoke against the generated warehouse
- `.github/workflows/ci.yml` proves dashboard, batch, and API container surfaces independently
- `.github/workflows/ci.yml` exports an `observability_summary.json` artifact from the official batch runtime evidence
- downstream smoke scripts share a common temporary-runtime helper in `scripts/smoke_support.py`
- `docker-compose.yml` packages batch, API, and Streamlit into a local enterprise demo stack

Governance checkpoints:

- runtime changes must preserve `python -m src.pipeline run` as the canonical path
- SQL examples should stay portable to the documented SQLite-first environment unless a dialect requirement is explicit
- README, runbook, release notes, and CI should change together when operational behavior changes

## SQL Consumption Examples

See [docs/sql_examples.md](docs/sql_examples.md) for practical warehouse queries covering channel economics, recommendation ranking, cohort retention, and executive segment views.

## Private GitHub and Streamlit Deployment

The repository is compatible with a private GitHub operating model and a Streamlit deployment surface for controlled demos.

- use the canonical Streamlit entrypoint `app/streamlit_app.py`
- keep `runtime.txt` pinned to `python-3.11` for Streamlit Community Cloud parity
- keep environment-specific values in Streamlit secrets, not in Git
- retain `python -m src.pipeline run` as the canonical runtime even when the app is the demo surface
- private GitHub repo and public Streamlit app can coexist when the linked GitHub account has private-repo access

Deployment reference:

- [docs/streamlit_private_deploy.md](docs/streamlit_private_deploy.md)

Canonical local scripts:

- `scripts/dev/start.ps1`
- `scripts/dev/status.ps1`
- `scripts/dev/stop.ps1`
- `scripts/start-demo.ps1`

## Technical Decisions and Trade-offs

- SQLite is the default warehouse because local reproducibility matters more than introducing mandatory external infrastructure.
- The project is batch-first on purpose. It demonstrates disciplined analytics engineering instead of pretending to be a full streaming platform.
- The Streamlit app consumes artifacts instead of recomputing core business logic, preserving one authoritative runtime path.
- Compatibility shims exist, but canonical imports remain explicit and documented.

## Decision Outputs

This system is designed to support:

- revenue-at-risk review
- segment and channel performance review
- prioritized retention and growth actions
- forecast and scenario conversations
- operational reliability review
- governance and data-trust review

## Governed AI Assist

The repository includes a governed insight-drafting layer for executive summaries.

- deterministic by default
- optional assistive mode with explicit fallback
- versioned as a pipeline artifact instead of ad hoc app prompting

Reference:

- [docs/ai_governance.md](docs/ai_governance.md)

## Recurring Operations

The repository includes a governed reliability and operating pack for recurring analytics delivery.

- `reliability_report.json` for operational confidence and SLA-oriented review
- `insight_draft.json` for executive narrative backed by governed evidence
- API exports for executive summary, reliability, insight draft, and top actions CSV

References:

- [docs/reliability_report.md](docs/reliability_report.md)
- [docs/recurring_analytics_operating_pack.md](docs/recurring_analytics_operating_pack.md)

## Executive Command Center

The Streamlit surface now supports dedicated executive pages in addition to the main command-center dashboard.

- executive overview
- revenue at risk
- forecast and scenarios
- operational reliability
- governance and data trust

References:

- [docs/demo_walkthrough.md](docs/demo_walkthrough.md)
- [docs/lineage_and_traceability.md](docs/lineage_and_traceability.md)

## Proposal And Handoff Assets

The repository now includes commercial and delivery-closeout assets for proposal support and client handoff.

- proposal template
- executive acceptance checklist
- client handoff checklist
- executive transformation summary

References:

- [docs/commercial/proposal_template.md](docs/commercial/proposal_template.md)
- [docs/executive/acceptance_checklist.md](docs/executive/acceptance_checklist.md)
- [docs/client_adaptation/handoff_checklist.md](docs/client_adaptation/handoff_checklist.md)
- [docs/executive_transformation_summary.md](docs/executive_transformation_summary.md)

## Operational Reading Order

If you are reviewing the repository for technical depth, read in this order:

1. this `README`
2. [docs/architecture.md](docs/architecture.md)
3. [docs/runtime_surfaces.md](docs/runtime_surfaces.md)
4. [docs/runbook.md](docs/runbook.md)
5. [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
6. [docs/adr/README.md](docs/adr/README.md)
7. [docs/repository_structure.md](docs/repository_structure.md)
8. [docs/hiring_review.md](docs/hiring_review.md)

## What This Repository Is Not

- not a notebook collection
- not a fake enterprise monorepo
- not a streaming platform demo
- not an MLOps platform clone

It is a production-minded batch analytics system sized honestly for a strong senior-level portfolio.

## Roadmap

Current high-impact next steps:

1. expand processed artifact contracts and integration coverage
2. deepen downstream warehouse and dbt validation beyond SQLite local-first assumptions
3. accumulate more small, coherent release notes
4. add a lightweight visual regression strategy for the dashboard

## Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow expectations, commit conventions, validation standards, and repository boundaries.

## License

This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

To view a copy of this license, visit:
https://creativecommons.org/licenses/by-nc/4.0/

[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc/4.0/)

