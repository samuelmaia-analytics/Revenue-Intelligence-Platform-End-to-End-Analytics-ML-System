# Documentation Map

This repository keeps documentation intentionally scoped and operational. Each document exists to help a reviewer or collaborator answer a concrete question quickly.

## Core Documents

- [architecture.md](architecture.md): system boundary, runtime path, data flow, reliability controls and trade-offs
- [architecture_decision_summary.md](architecture_decision_summary.md): short architecture summary for sponsors and fast reviews
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
- [demo_enterprise_local.md](demo_enterprise_local.md): local enterprise demo path across batch, API, and Streamlit
- [export_layer.md](export_layer.md): governed export and downstream consumption paths
- [ai_governance.md](ai_governance.md): governed AI posture for optional insight drafting
- [reliability_report.md](reliability_report.md): governed operational summary for recurring delivery
- [recurring_analytics_operating_pack.md](recurring_analytics_operating_pack.md): recurring analytics operating model and artifact pack
- [lineage_and_traceability.md](lineage_and_traceability.md): source-to-consumer lineage and runtime traceability
- [demo_walkthrough.md](demo_walkthrough.md): guided commercial and technical walkthrough
- [semantic_metrics_layer.md](semantic_metrics_layer.md): governed semantic metrics narrative across runtime, API, SQL, and dbt
- [dbt_semantic_story.md](dbt_semantic_story.md): how dbt extends the platform as a downstream semantic layer
- `scripts/smoke_support.py`: shared temporary-runtime helper for downstream smoke checks
- [adr/README.md](adr/README.md): short decision records for the most important architectural trade-offs
- [hiring_review.md](hiring_review.md): honest portfolio assessment from a hiring-review perspective

## Executive and Commercial

- [audit/executive_audit_2026-04.md](audit/executive_audit_2026-04.md): current audit of product, architecture, and sellability
- [executive/one_pager.md](executive/one_pager.md): short executive summary for leadership buyers
- [executive/technical_one_pager.md](executive/technical_one_pager.md): short technical summary for sponsors and architects
- [executive/decision_layer.md](executive/decision_layer.md): decisions, users, and operating outputs supported by the system
- [executive/scorecards.md](executive/scorecards.md): executive scorecard framing for risk, opportunity, and trust
- [commercial/offers.md](commercial/offers.md): productized service packaging
- [commercial/evidence_pack.md](commercial/evidence_pack.md): proof-point kit for demos, proposals, and recruiting
- [commercial/proposal_template.md](commercial/proposal_template.md): proposal-ready template for premium consulting packaging
- [client_adaptation/adaptation_framework.md](client_adaptation/adaptation_framework.md): controlled adaptation model for client environments
- [client_adaptation/implementation_checklist.md](client_adaptation/implementation_checklist.md): new-client implementation checklist
- [client_adaptation/handoff_checklist.md](client_adaptation/handoff_checklist.md): client handoff checklist for delivery closeout
- [use_case_templates/saas_b2b_revenue.md](use_case_templates/saas_b2b_revenue.md): B2B SaaS template
- [use_case_templates/omnichannel_retail.md](use_case_templates/omnichannel_retail.md): omnichannel retail template
- [executive/acceptance_checklist.md](executive/acceptance_checklist.md): executive acceptance criteria and handoff checks
- [executive_transformation_summary.md](executive_transformation_summary.md): short summary of the repository transformation for sponsors

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
