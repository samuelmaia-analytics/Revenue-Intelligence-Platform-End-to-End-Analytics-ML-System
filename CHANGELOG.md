# Changelog

All notable changes to this project are documented in this file.

## Breaking Changes Policy

- API and schema contracts follow semantic versioning.
- Canonical contracts are versioned under `contracts/v{major}/`.
- Breaking API or contract changes must:
  - increment the major version;
  - preserve older contract modules for migration windows when possible;
  - be documented in the relevant release under `Breaking Changes`.

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

