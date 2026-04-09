# Local Enterprise Demo

## Objective

Run the batch runtime, API, and Streamlit app together for a guided local demo.

## Command

```powershell
docker compose up --build
```

## Surfaces

- Streamlit app: `http://localhost:8501`
- API: `http://localhost:8000`

## Demo Flow

1. Start with the batch runtime as the governed system of record.
2. Open the app and show executive scorecards, risk, and action views.
3. Open the API health and prediction endpoints to show external consumption.
4. Use the documentation set to show operational maturity and governance.

## Notes

- `batch` runs first and populates `data/`
- `api` and `app` mount the same governed data volume
- `.env` controls runtime behavior for all services
