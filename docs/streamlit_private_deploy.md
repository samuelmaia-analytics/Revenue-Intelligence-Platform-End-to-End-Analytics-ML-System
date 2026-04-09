# Private GitHub + Streamlit Deployment

This repository is prepared for a private GitHub workflow with a Streamlit deployment surface.

## Repository Visibility

GitHub repository visibility is expected to remain `private`.

Recommended controls:

- keep deployment secrets in the Streamlit app settings, not in the repository
- keep `.env` and `.streamlit/secrets.toml` local-only
- use the root entrypoint `streamlit_app.py` for a simpler deployment target

## Deployment Target

Main file for Streamlit deployment:

```text
streamlit_app.py
```

Python version:

```text
3.11
```

Dependencies source:

```text
requirements.txt
```

## Deploy Flow

1. Connect Streamlit to the same GitHub account that can read this private repository.
2. Create a new app and select the repository.
3. Set the main file path to `streamlit_app.py`.
4. Add any required runtime secrets in the Streamlit secrets panel.
5. Deploy the app.

## Runtime Behavior

The app consumes processed artifacts from `data/processed`.

If the required governed artifacts are missing, the app triggers the official batch runtime through `run_pipeline(...)` before rendering. This preserves the canonical execution model while keeping the app deployable as a demo surface.

## Recommended Secrets

Use `.streamlit/secrets.toml.example` as the shape reference only.

Typical keys:

- `RIP_APP_LANG_MODE`
- `RIP_API_AUTH_MODE`
- `RIP_API_RATE_LIMIT_PER_MINUTE`

If you later externalize storage or API credentials, add them only in the Streamlit deployment settings.
