# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

- versioned runtime baseline in `metrics/runtime_baseline.json`
- runtime baseline refresh script `scripts/update_runtime_baseline.py`
- manual GitHub Actions workflow `.github/workflows/runtime-baseline.yml` for controlled baseline promotion

### Changed

- CI runtime regression gate now compares container smoke runtime metrics against the versioned baseline
- release process now documents when and how to refresh the runtime baseline intentionally
- manual runtime baseline workflow now opens a PR automatically with refreshed baseline evidence
- automated baseline PRs now include labels and reviewer routing aligned with repository policy
- automated baseline PRs now attempt squash auto-merge when repository policy permits it

## Breaking Changes Policy

- API and schema contracts follow semantic versioning.
- Canonical contracts are versioned under `contracts/v{major}/`.
- Breaking API or contract changes must:
  - increment the major version;
  - preserve older contract modules for migration windows when possible;
  - be documented in the relevant release under `Breaking Changes`.

## [1.4.0] - 2026-03-26

### Added

- governance framework document linking runtime, contracts, SQL, CI, and release evidence
- CI/CD document describing job topology, local-to-CI parity, and artifact expectations
- release note `docs/releases/v1.4.0.md`

### Changed

- main and localized READMEs now surface governance and CI checkpoints more explicitly
- merge and release policy now require repository-governance evidence when operational policy changes
- Makefile now exposes a dedicated governance target for repository-policy validation
- SQL bootstrap DDL now matches the dimensional definitions more closely
- analytical SQL examples now describe intent and use SQLite-portable date logic

### Portfolio Deltas

- the repository now reads more like an intentionally operated system than a collection of good individual assets
- CI, SQL, and documentation tell a more consistent story about SQLite-first reproducibility and review discipline

## [1.3.0] - 2026-03-19

### Added

- dbt SQLite smoke validation in the main CI flow
- release note for runtime, dbt, and governance hardening in `docs/releases/v1.3.0.md`
- merge-policy document covering labels, merge gates, and review expectations
- localized README guidance for isolated `.dbt-venv` setup

### Changed

- Docker CI now smoke-tests the containerized API health endpoint
- runbook now covers API smoke failures, dbt smoke failures, and environment bootstrap failures
- deprecation policy now makes top-level breadth and compatibility visibility more explicit
- README documentation now includes concrete SQL consumption examples for the warehouse

### Portfolio Deltas

- dbt is now a validated downstream consumer, not just a documented capability
- the repository makes container-level API operability more visible
- localized documentation now reflects the real environment-isolation strategy for `dbt`

## [1.3.1] - 2026-03-19

### Added

- processed-export smoke validation for curated CSV and JSON outputs
- release note `docs/releases/v1.3.1.md`

### Changed

- CI now validates processed exports as downstream interfaces
- container smoke now asserts presence of key processed business artifacts
- runbook and troubleshooting docs now cover export drift, API container health, and dbt failure classes more explicitly

### Portfolio Deltas

- the repository now shows downstream readiness beyond the local SQLite warehouse path
- reviewer-facing docs connect runtime failures to first actions more directly

## [1.3.2] - 2026-03-19

### Added

- partner-facing payload export from processed artifacts
- partner payload smoke validation in the main quality flow
- incident playbooks document
- SQL examples document
- release note `docs/releases/v1.3.2.md`

### Changed

- local and CI validation now treat partner payload generation as a governed downstream surface
- README and contribution docs now surface downstream query examples and incident playbooks more directly

### Portfolio Deltas

- the repository now demonstrates another consumer path beyond SQLite-local querying
- incident response is documented more like an operated system than a static portfolio

## [1.3.3] - 2026-03-19

### Added

- validation contracts for secondary processed exports
- warehouse semantic test coverage for `cohort_retention`
- release note `docs/releases/v1.3.3.md`

### Changed

- issue templates now use the same label vocabulary documented in merge policy
- merge-policy text no longer contains encoding noise
- incident playbooks now include concrete examples of likely failures

### Portfolio Deltas

- the repository now treats secondary analytical exports with the same seriousness as primary outputs
- governance looks more intentional because issue intake and merge policy now match

## [1.2.0] - 2026-03-19

### Added

- Streamlit runtime health section backed by:
  - `pipeline_manifest.json`
  - `artifact_validation_report.json`
  - `freshness_report.json`
- Operational documentation for:
  - runbook
  - troubleshooting matrix
  - release process
  - ADRs
  - hiring review perspective
- Warehouse consumption tests that validate downstream analytical queries against the persisted SQLite warehouse.

### Changed

- Main README and localized READMEs now include Mermaid diagrams where they reduce reviewer effort.
- Streamlit overview now surfaces operational credibility, not only business KPIs.
- Logistic regression training now uses a more stable solver for this repository context, removing recurring test-suite warnings.

### Portfolio Deltas

- The repository now communicates architecture, operation and trade-offs much faster to recruiters and tech leads.
- The dashboard better reflects a real internal decision tool by exposing runtime health.
- Warehouse validation now demonstrates not just persistence, but actual analytical consumption readiness.

### Governance Deltas

- Critical operational documentation and CI gates are now protected by repository-governance tests.
- Local cache noise is more aggressively ignored to keep the repository review-ready.

## [1.1.0] - 2026-03-05

### Added

- Versioned API endpoints: `GET /api/v1/health` and `POST /api/v1/score`.
- API key validation (`X-API-Key` / bearer) with legacy header compatibility.
- Production telemetry in health payload and logs:
  - `prediction_latency_ms`
  - `request_volume`
  - `model_version_usage`
- Versioned model registry layout:
  - `data/processed/registry/<model_name>/model_vN/`
  - `data/processed/registry/<model_name>/latest.json`

### Changed

- `/health` and `/score` remain available as backward-compatible aliases.
- Model loader now prioritizes the latest versioned registry and still supports legacy `model_registry` paths as fallback.

## [1.0.0] - 2026-03-05

### Added

- API token authentication for `/score` in demo mode by default (`X-API-Token` or bearer token).
- In-memory rate limiting for `/score` with configurable per-minute quota.
- Versioned data contract source at `contracts/v1/data_contract.py`.
- Release notes document for `v1.0.0` with business deltas.

### Breaking Changes

- Contract source of truth moved from `contracts/data_contract.py` to `contracts/v1/data_contract.py`.
  Compatibility import path is still available in `contracts/data_contract.py`.

### Business Deltas

- Prioritization output now ships with API hardening (token + quota) for safer partner demos.
- Product baseline established with versioned contract governance for future API evolution.
- Latest reference run keeps positive scenario economics:
  - Top 10 net impact: `2,550.13`
  - Top 10 simulated ROI: `1.58x`
  - 90-day uplift vs baseline: `+4,165.63`
