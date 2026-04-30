# ADR 0004: Separate Pipeline Runtime and Service Boundaries

## Status

Accepted

## Context

The original pipeline coordination layer was accumulating orchestration, runtime operations, silver validation, curated artifact assembly, reporting, and warehouse preparation in one place.

That increased:

- review cost
- regression risk during refactors
- hidden coupling between pipeline stages
- the gap between the repository narrative and the actual code structure

## Decision

Split the batch core into three clearer concerns:

- `src.orchestration` for stage coordination
- `src.pipeline_runtime` for manifests, retention, snapshots, freshness, and backfill helpers
- `src.pipeline_services` for silver data services, quality gating, serving artifact assembly, and warehouse frame preparation

## Consequences

Positive:

- the orchestration layer is smaller and easier to inspect
- runtime operations are explicit and easier to test
- data services are reusable without moving business logic into consumers
- the project now communicates seniority through the code structure, not only through documentation

Trade-offs:

- more modules exist in `src/`
- contributors must understand the intended boundary between coordination and service logic

## Why This Was Worth It

This repository is evaluated as a portfolio asset. The split improves maintainability and better reflects how a production-minded data system should separate coordination from operational concerns and stage-specific services.
