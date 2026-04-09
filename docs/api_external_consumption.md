# API External Consumption

## Purpose

Document the API surfaces intended for demos, integrations, and external consumption.

## Core Endpoints

- `/api/v1/health`
- `/api/v1/ready`
- `/api/v1/score`
- `/api/v1/scorecard`
- `/api/v1/executive-summary`
- `/api/v1/insight-draft`
- `/api/v1/reliability-report`
- `/api/v1/exports/top-actions.csv`

## Recommended Use

- use `health` and `ready` for operational checks
- use `scorecard` for executive demo and summary integrations
- use `executive-summary`, `insight-draft`, and `reliability-report` for governed business consumption
- use `top-actions.csv` for lightweight downstream export and ad hoc handoff

## Security

- `demo` mode for controlled demos
- `strict` mode for client-facing deployment
- use `X-API-Key` or `Authorization: Bearer <key>`
