# Private GitHub + Streamlit Deployment

This repository is prepared for a private GitHub workflow with a Streamlit deployment surface.

## Repository Visibility

GitHub repository visibility is expected to remain `private`.

Recommended controls:

- keep deployment secrets in the Streamlit app settings, not in the repository
- keep `.env` and `.streamlit/secrets.toml` local-only
- use the canonical entrypoint `app/streamlit_app.py`

## Deployment Target

Main file for Streamlit deployment:

```text
app/streamlit_app.py
```

Python version:

```text
3.11
```

Runtime pin file:

```text
runtime.txt
```

Dependencies source:

```text
requirements.txt
```

## Deploy Flow

1. Connect Streamlit to the same GitHub account that can read this private repository.
2. In GitHub linked-account permissions, allow access to this private repository.
3. Create a new app and select the repository/branch.
4. Set the main file path to `app/streamlit_app.py`.
5. Add any required runtime secrets in the Streamlit secrets panel.
6. Deploy the app.
7. If desired, set the app visibility to public in Streamlit app settings.

If you see `You do not have access to this app or it does not exist`, validate linked-account ownership and repository permissions before debugging application code.

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

`.env` exists for local development and scripts; Streamlit Community Cloud does not read your local `.env` file from your machine.

For privacy handling and LGPD-oriented controls, see `docs/lgpd_data_governance.md`.
