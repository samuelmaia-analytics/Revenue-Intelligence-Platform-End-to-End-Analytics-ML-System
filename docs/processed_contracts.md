# Processed Contract Versioning and Compatibility

## Purpose

Processed artifacts are treated as governed downstream interfaces, not just internal files. This document defines how they evolve without turning the repository into a heavy contract-management system.

## Source of Truth

- canonical processed contract path: `contracts/v1/processed_contract.py`
- backward-compatible shim: `contracts/processed_contract.py`
- runtime evidence:
  - `pipeline_manifest.json.processed_contract_version`
  - `artifact_validation_report.json.contract_version`

## Versioning Rule

Processed contracts follow semantic versioning.

- patch version:
  - documentation-only clarifications
  - stricter internal validation with no column or key changes
  - no downstream adaptation required
- minor version:
  - additive columns or keys
  - new optional artifacts
  - compatibility shim may still point to the older canonical version during migration
- major version:
  - renamed or removed columns
  - changed meaning of an existing field
  - artifact removal
  - incompatible shape changes

## Compatibility Rule

Preferred change order:

1. add a new canonical contract path such as `contracts/v2/processed_contract.py`
2. keep the previous version available during the migration window
3. update producer validation and downstream consumers explicitly
4. ship a release note and changelog entry
5. remove the old shim only after the migration window is closed

## Downstream Consumer Strategy

When a processed contract changes:

1. classify the change as additive or breaking
2. update `src/artifact_validation.py` and the relevant contract module together
3. update the consuming surfaces that read the affected artifact:
   - Streamlit
   - API
   - SQL examples
   - dbt models
   - partner payloads
4. add or update a regression test at the producer-consumer boundary
5. document the migration path in release notes

Consumers should not silently coerce old and new shapes at runtime. If compatibility is required, it should be explicit and versioned.

## Rollback Rule

Rollback must prefer a known-good contract version over ad hoc artifact patching.

Required rollback path:

1. validate the broken artifact set against the last known good contract version
2. revert the producer or consumer change
3. rerun the pipeline
4. keep the compatibility test that reproduces the failure

This is why the repository keeps versioned contract modules and compatibility-focused regression tests.

## Current Decision About `data/processed`

Decision:
- keep `data/processed` versioned only as a very small, reviewer-facing reference surface
- the only tracked reference artifact under `data/processed` is `metrics_report.json`
- generated model binaries and regenerated serving artifacts must stay out of git
- do not treat it as the authoritative storage strategy for production-like environments

Implications:
- small curated reference artifacts are acceptable in git when they improve reviewability
- volatile, regenerated, or binary artifacts must not be committed under `data/processed`
- model binaries and regenerated outputs should move to release assets, object storage, or environment-specific artifact storage if the repository grows further

Why `metrics_report.json` stays:
- it is lightweight
- it gives reviewers an immediate view of model quality without forcing a full run
- it does not create the maintenance cost or binary drift risk of checked-in model artifacts

This repository stays credible because the versioned artifacts are limited, deterministic enough for review, and clearly documented as reference outputs rather than production persistence.
