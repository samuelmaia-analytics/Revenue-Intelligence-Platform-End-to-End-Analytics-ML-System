# Local Benchmark

## Measurement Date

2026-03-20

## Commands

Baseline local run:

```powershell
.\.venv\Scripts\python -m src.pipeline run --log-level WARNING
```

Scaled synthetic run:

```powershell
$env:RIP_ALLOW_BUNDLED_SEED_FALLBACK = "false"
$env:RIP_SYNTHETIC_CUSTOMERS = "10000"
.\.venv\Scripts\python -m src.pipeline run --log-level WARNING
```

## Observed Runtime Trend

- reference batch run with `2500` synthetic customers: approximately `6.91s`
- larger batch run with `10000` synthetic customers: approximately `16.21s`
- observed scale factor: about `2.35x` runtime for `4x` more synthetic customers

## Benchmark Notes

- measured on the current local development machine
- includes ingestion, transformations, model scoring, curated artifacts, reporting, warehouse persistence, and manifests
- uses the default SQLite warehouse target
- the larger benchmark disables bundled sample-seed fallback so `RIP_SYNTHETIC_CUSTOMERS` actually controls input size
- should be treated as a developer benchmark, not a production SLA

## Approximate Cost Profile

- infrastructure cost: effectively zero in local execution
- compute profile: single-machine, CPU-only development workload
- operational takeaway: the repository remains inexpensive to run locally, even when the synthetic input size is increased for regression or performance checks

## Why This Matters

This benchmark gives hiring reviewers and contributors a realistic sense of local feedback speed and small-scale growth behavior. It also helps justify why SQLite remains a sensible default for the repository's local-first workflow while still leaving room for optional Postgres validation.
