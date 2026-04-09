# Architecture Decision Summary

## Fast Read

- batch runtime is the system of record
- SQLite is the default warehouse for reproducible delivery
- Streamlit consumes artifacts rather than re-implementing business logic

## Why These Decisions Matter

- one canonical runtime reduces ambiguity and trust erosion
- SQLite lowers demo and pilot friction while preserving SQL consumption
- downstream consumers stay aligned because they read the same governed outputs

## Related ADRs

- `docs/adr/0001-batch-first-system-of-record.md`
- `docs/adr/0002-sqlite-default-warehouse.md`
- `docs/adr/0003-streamlit-consumes-artifacts.md`
