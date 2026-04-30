# Compatibility and Deprecation Policy

## Purpose

This repository contains a small number of compatibility shims to preserve stable import paths while the project evolves.

These shims exist for practical migration support, not as permanent architectural layers.

## Current Compatibility Paths

Current examples:

- `api/`
- `contracts/data_contract.py`
- `contracts/processed_contract.py`
- `src/data_contract.py`

Canonical paths should be preferred in new code:

- `services.api`
- `contracts.v1.data_contract`
- `contracts.v1.processed_contract`

## Contract Compatibility Rule

Governed data contracts should follow these rules:

1. additive changes are preferred over breaking changes
2. breaking schema changes should land in a versioned contract path
3. downstream consumers should be migrated to the new canonical version before old shims are removed
4. release notes should state whether a change is additive, behavior-changing, or compatibility-breaking

For this repository, `contracts.v1.data_contract` is the canonical contract surface until a deliberate version increment is introduced.
The same rule applies to `contracts.v1.processed_contract` for curated batch outputs.

## Deprecation Rule

When a compatibility path exists:

1. document the canonical path
2. keep the shim narrow and obvious
3. avoid building new features on the shim path
4. record breaking changes in release notes and changelog

## When to Remove a Shim

A shim is a candidate for removal when:

- all internal imports already use the canonical path
- the compatibility layer no longer protects a meaningful migration path
- removal improves clarity without breaking the hiring value of the repository

## Repository Guidance

For this project, compatibility should always serve clarity.

If a shim starts to confuse reviewers more than it helps backwards compatibility, it should be scheduled for removal in a future release note and changelog entry.

## Top-Level Breadth Rule

The repository already exposes multiple surfaces:

- batch runtime
- Streamlit workspace
- API serving layer
- dbt downstream consumption
- operational documentation

That breadth is acceptable only because each surface consumes the same governed core.

Do not add new top-level directories unless one of these is true:

1. the directory owns a distinct runtime surface
2. the directory holds governed assets that should not live under `src/`
3. the change would be harder to understand if folded into an existing directory

When in doubt, prefer strengthening an existing canonical path over creating a new top-level concept.

## Visibility Rule

If a compatibility path remains in the repository, the deprecation plan should be visible in:

- `docs/deprecation_policy.md`
- `CHANGELOG.md`
- the next relevant file under `docs/releases/`

This keeps the top-level breadth intentional instead of looking accidental to reviewers.
