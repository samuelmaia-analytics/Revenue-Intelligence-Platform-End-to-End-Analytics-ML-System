# LGPD and Data Privacy Governance

## Purpose

Define practical privacy controls for this repository under a Brazil-first operating model aligned with LGPD principles.

This document is an engineering policy reference, not legal advice.

## Data Classification

The repository should treat data by sensitivity class:

- `public`: docs, code, and non-sensitive metadata
- `internal`: operational logs and non-identifying analytics artifacts
- `restricted`: customer-level analytical artifacts, raw-source records, and any field that can identify a person directly or indirectly

When in doubt, classify as `restricted`.

## LGPD-Oriented Principles

1. Purpose limitation: process only data needed for the documented analytical objective.
2. Data minimization: avoid ingesting or exporting fields that are not required for pipeline outputs.
3. Need-to-know access: restrict repository, environment, and deployment access to required collaborators.
4. Storage limitation: retain generated artifacts only for operational necessity and governance evidence.
5. Security: keep secrets out of source control and use platform secret stores for deployments.
6. Traceability: preserve manifest and runtime evidence so data handling can be audited.

## Repository Controls

- `.env` and `.streamlit/secrets.toml` must remain local-only.
- Sensitive values must be configured via deployment secret managers.
- Generated runtime artifacts under `data/` must not be committed.
- Documented runtime path remains `python -m src.pipeline run` for traceability.
- Consumer surfaces (Streamlit/API/dbt/SQL) must read governed outputs rather than reimplementing raw logic.

## Deployment Controls

- Private GitHub repositories are allowed with public Streamlit apps when account permissions are explicit and controlled.
- Review app sharing mode before publishing links.
- Validate linked-account ownership on Streamlit when access errors appear.

## Incident Handling

If potential personal data exposure is detected:

1. Contain access immediately (disable sharing, rotate credentials, restrict tokens).
2. Preserve operational evidence (manifests, logs, run metadata).
3. Identify affected artifacts and remove exposed outputs from public surfaces.
4. Open a governance incident issue and document corrective actions.

Reference operational playbooks in `docs/incident_playbooks.md`.

## Change Review Checklist

For changes touching raw ingestion, exports, Streamlit/API payloads, or secrets handling:

- confirm sensitivity class impact
- confirm no new secret material is committed
- confirm docs and runbook still match behavior
- confirm CI and governance checks cover the change
