# Documentation Map

This repository keeps documentation intentionally scoped and operational. Each document exists to help a reviewer or collaborator answer a concrete question quickly.

## Core Documents

- [architecture.md](architecture.md): system boundary, runtime path, data flow, reliability controls and trade-offs
- [governance_framework.md](governance_framework.md): source-of-truth rules, ownership surfaces, and change-evidence expectations
- [runtime_surfaces.md](runtime_surfaces.md): canonical runtime surface, downstream interfaces, and smoke ownership
- [runbook.md](runbook.md): operational commands, failure investigation, and exported observability evidence
- [environments.md](environments.md): how `.venv`, `.dbt-venv`, and CI relate to each other
- [ci_cd.md](ci_cd.md): CI job topology, required gates, and local-to-CI parity expectations
- [repository_structure.md](repository_structure.md): why directories exist, where new code belongs and what should stay out of the top level
- [onboarding.md](onboarding.md): fastest path to a successful local run, validation commands and common failure modes
- [incident_playbooks.md](incident_playbooks.md): short containment playbooks for the most likely incident classes
- [troubleshooting_matrix.md](troubleshooting_matrix.md): fast diagnosis map from symptom to artifact and first action
- [release_process.md](release_process.md): lightweight release discipline for technical portfolio changes
- [deprecation_policy.md](deprecation_policy.md): how compatibility shims are handled and eventually removed
- [merge_policy.md](merge_policy.md): labels, merge expectations, and what must be green before merging
- [sql_examples.md](sql_examples.md): practical downstream SQL examples over warehouse outputs
- `scripts/smoke_support.py`: shared temporary-runtime helper for downstream smoke checks
- [adr/README.md](adr/README.md): short decision records for the most important architectural trade-offs
- [hiring_review.md](hiring_review.md): honest portfolio assessment from a hiring-review perspective

## Planning and Maintenance

- [staff_upgrade_master_issue.md](staff_upgrade_master_issue.md): tracked work for portfolio hardening and senior-level upgrades
- [issues](issues): issue templates and project-level backlog support
- [releases](releases): release-oriented documentation and changelog support
- [releases/v1.1.0.md](releases/v1.1.0.md): latest portfolio-hardening release summary
- [releases/v1.2.0.md](releases/v1.2.0.md): latest governance and downstream-validation release summary
- [releases/v1.3.0.md](releases/v1.3.0.md): dbt runtime hardening, localized docs updates, and container-level API validation
- [releases/v1.3.1.md](releases/v1.3.1.md): processed-exports smoke coverage, richer incident handling, and CI/runtime alignment
- [releases/v1.3.2.md](releases/v1.3.2.md): partner payload consumer, incident playbooks, and stronger downstream portfolio evidence
- [releases/v1.3.3.md](releases/v1.3.3.md): secondary export contracts, semantic warehouse coverage, and label-governance alignment
- [releases/v1.4.0.md](releases/v1.4.0.md): governance topology, CI discipline, and SQLite-first reviewer story

## Reading Order

1. Start with the root `README` in your preferred language.
2. Read [architecture.md](architecture.md) for the system model.
3. Read [governance_framework.md](governance_framework.md) to understand evidence, ownership, and what must stay aligned.
4. Read [runtime_surfaces.md](runtime_surfaces.md) to understand what is canonical versus downstream.
5. Read [ci_cd.md](ci_cd.md) to understand required checks and failure attribution.
6. Read [runbook.md](runbook.md) to understand operation and recovery.
7. Read [troubleshooting_matrix.md](troubleshooting_matrix.md) for faster diagnosis.
8. Read [repository_structure.md](repository_structure.md) before moving files or adding modules.
9. Use [onboarding.md](onboarding.md) and [environments.md](environments.md) when you need to run, validate or extend the project locally.
