## Summary

- What changed:
- Why this change is needed:
- Which runtime path, contract, or operational concern it touches:

## Scope

- Category: `feature` / `fix` / `refactor` / `test` / `docs` / `chore`
- Official batch path affected: `yes` / `no`
- Streamlit affected: `yes` / `no`
- Warehouse behavior affected: `yes` / `no`
- Contracts affected: `yes` / `no`

## Validation

- [ ] `python -m ruff check .`
- [ ] `python -m black --check .`
- [ ] `python -m isort --check-only .`
- [ ] `python -m mypy src services contracts main.py`
- [ ] `python -m pytest -q`
- [ ] `python scripts/smoke_dashboard.py`
- [ ] `python -m build`

If any item above was intentionally not run, explain why:

-

## Runtime Impact

- Output artifacts affected:
- Manifest or runbook impact:
- Backfill or retry behavior impact:
- Warehouse impact:
- Dashboard impact:
- LGPD/privacy impact:

## Documentation

- [ ] `README.md` reviewed
- [ ] `README.pt-BR.md` reviewed when needed
- [ ] `docs/architecture.md` reviewed when needed
- [ ] `docs/runbook.md` reviewed when needed
- [ ] `docs/release_process.md` reviewed when needed
- [ ] `docs/lgpd_data_governance.md` reviewed when data handling or deployment exposure changed
- [ ] No aspirational documentation introduced

## Tests Added or Updated

- New or updated tests:
- Why these tests are sufficient:
- Residual risks:

## Review Notes

- Main risk:
- Rollback path:
- Why this change is proportionate for the repository:
