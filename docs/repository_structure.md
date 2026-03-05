# Repository Structure Standard

This repository follows a production-oriented structure with explicit boundaries:

- `src/`: core pipeline and ML domain logic.
- `services/`: runtime services (HTTP APIs, workers).
- `contracts/`: input/output schemas used across pipeline, API and tests.
- `app/`: Streamlit product UI.
- `tests/`: automated quality gates.
- `data/`: local development data and generated artifacts.

## Import Policy

- New code should import API entrypoints from `services.api`.
- New code should import schemas from `contracts.v1.data_contract`.
- `api/` and `src/data_contract.py` are maintained as compatibility shims.
- `contracts/data_contract.py` is a compatibility shim to current versioned contracts.

## Evolution Rule

When adding a new component:
1. Place business/domain logic in `src/`.
2. Expose runtime interfaces in `services/`.
3. Add or update schemas in `contracts/`.
4. Add tests in `tests/`.
5. Update `README.md` and `README.pt-BR.md`.
