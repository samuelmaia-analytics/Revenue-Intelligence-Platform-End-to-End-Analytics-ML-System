## Summary

- What changed:
- Why this change was necessary:
- Main engineering concern addressed:

## Scope

- Category: `feat` / `fix` / `refactor` / `test` / `docs` / `chore`
- Official batch path affected: `yes` / `no`
- Warehouse outputs affected: `yes` / `no`
- Contracts affected: `yes` / `no`
- Dashboard or API affected: `yes` / `no`
- Documentation updated: `yes` / `no`

## Validation

- [ ] `python -m ruff check .`
- [ ] `python -m black --check .`
- [ ] `python -m isort --check-only .`
- [ ] `python -m mypy src services contracts main.py`
- [ ] `python -m pytest -q`
- [ ] `python -m build`

Run when applicable:

- [ ] `python scripts/smoke_dashboard.py`
- [ ] `python scripts/ui_snapshot.py`
- [ ] `python scripts/smoke_api.py`
- [ ] `python scripts/smoke_downstream_sql.py`
- [ ] `python scripts/smoke_processed_exports.py`
- [ ] `python scripts/smoke_partner_payload.py`
- [ ] `python scripts/smoke_dbt_sqlite.py`
- [ ] `docker build -t revenue-intelligence .`
- [ ] `docker build -f Dockerfile.api -t revenue-intelligence-api .`

If any relevant check was skipped, explain why:

-

## Runtime Impact

- Outputs created or changed:
- Runtime policy affected:
- Backfill, retry, retention, or quality impact:
- Warehouse impact:
- Downstream consumer impact:

## Tests

- New or updated tests:
- Why this coverage is sufficient:
- Residual risks:

## Documentation

- [ ] `README.md` reviewed
- [ ] `CONTRIBUTING.md` reviewed when needed
- [ ] architecture/runbook docs reviewed when needed
- [ ] no aspirational documentation introduced

## Review Notes

- Highest risk:
- Rollback path:
- Why this change is proportionate for this repository:
