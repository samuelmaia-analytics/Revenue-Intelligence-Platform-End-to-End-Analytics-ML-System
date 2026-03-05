from __future__ import annotations

import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request

from contracts.data_contract import ScoreInputRecord, ScoreRequest, ScoreResponse
from src.model_registry import load_registered_model


def _resolve_model_dir() -> Path:
    return Path(os.getenv("RIP_MODEL_DIR", "data/processed"))


def _resolve_auth_mode() -> str:
    mode = os.getenv("RIP_API_AUTH_MODE", "demo").strip().lower()
    if mode not in {"off", "demo", "strict"}:
        raise RuntimeError("RIP_API_AUTH_MODE must be one of: off, demo, strict.")
    return mode


def _resolve_allowed_tokens() -> set[str]:
    tokens_from_env = os.getenv("RIP_API_TOKENS", "")
    parsed = {token.strip() for token in tokens_from_env.split(",") if token.strip()}
    if parsed:
        return parsed
    demo_token = os.getenv("RIP_API_DEMO_TOKEN", "rip-demo-token-v1")
    return {demo_token}


def _resolve_rate_limit_per_minute() -> int:
    raw = os.getenv("RIP_API_RATE_LIMIT_PER_MINUTE", "60").strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("RIP_API_RATE_LIMIT_PER_MINUTE must be an integer.") from exc
    if value < 1:
        raise RuntimeError("RIP_API_RATE_LIMIT_PER_MINUTE must be >= 1.")
    return value


def _suggest_action(churn_probability: float, next_purchase_probability: float) -> str:
    if churn_probability >= 0.7:
        return "Retention Campaign"
    if next_purchase_probability >= 0.6:
        return "Upsell Offer"
    if churn_probability <= 0.25 and next_purchase_probability <= 0.35:
        return "Reduce Acquisition Spend"
    return "Nurture"


def _load_model_bundle(model_dir: Path, model_name: str, legacy_name: str) -> dict[str, Any]:
    try:
        model, metadata = load_registered_model(model_dir, model_name)
        return {"model": model, "metadata": metadata, "loaded_from": "registry"}
    except FileNotFoundError:
        legacy_path = model_dir / legacy_name
        if not legacy_path.exists():
            return {"model": None, "metadata": {}, "loaded_from": "missing"}
        try:
            import joblib

            model = joblib.load(legacy_path)
            return {
                "model": model,
                "metadata": {
                    "run_id": "legacy",
                    "data_version": "legacy",
                    "model_name": model_name,
                },
                "loaded_from": "legacy",
            }
        except Exception:
            return {"model": None, "metadata": {}, "loaded_from": "broken"}


def _extract_auth_token(
    x_api_token: str | None,
    authorization: str | None,
) -> str | None:
    if x_api_token:
        return x_api_token.strip()

    if authorization:
        prefix = "bearer "
        if authorization.lower().startswith(prefix):
            token = authorization[len(prefix) :].strip()
            if token:
                return token
    return None


def _check_auth(token: str | None) -> None:
    if API_AUTH_MODE == "off":
        return

    if token is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Missing API token. Provide `X-API-Token` or " "`Authorization: Bearer <token>`."
            ),
        )

    if token not in ALLOWED_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid API token.")


def _enforce_rate_limit(client_id: str) -> None:
    now = time.time()
    window_start = now - 60
    with RATE_LIMIT_LOCK:
        history = REQUEST_HISTORY.setdefault(client_id, [])
        while history and history[0] <= window_start:
            history.pop(0)
        if len(history) >= API_RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail=("Rate limit exceeded. Try again in 60 seconds or request a higher quota."),
            )
        history.append(now)


app = FastAPI(
    title="Revenue Intelligence Model Serving API",
    version="1.0.0",
    description="Serve churn and next-purchase predictions with explicit input contracts.",
)

MODEL_DIR = _resolve_model_dir()
API_AUTH_MODE = _resolve_auth_mode()
ALLOWED_TOKENS = _resolve_allowed_tokens()
API_RATE_LIMIT_PER_MINUTE = _resolve_rate_limit_per_minute()
REQUEST_HISTORY: dict[str, list[float]] = {}
RATE_LIMIT_LOCK = Lock()
CHURN_BUNDLE = _load_model_bundle(MODEL_DIR, "churn", "churn_model.joblib")
NEXT_BUNDLE = _load_model_bundle(MODEL_DIR, "next_purchase_30d", "next_purchase_model.joblib")


@app.get("/health")
def health() -> dict[str, Any]:
    churn_loaded = CHURN_BUNDLE["model"] is not None
    next_loaded = NEXT_BUNDLE["model"] is not None
    status = "ok" if churn_loaded and next_loaded else "degraded"

    return {
        "status": status,
        "model_dir": str(MODEL_DIR.resolve()),
        "models": {
            "churn": {
                "loaded": churn_loaded,
                "run_id": CHURN_BUNDLE["metadata"].get("run_id"),
                "data_version": CHURN_BUNDLE["metadata"].get("data_version"),
                "source": CHURN_BUNDLE["loaded_from"],
            },
            "next_purchase_30d": {
                "loaded": next_loaded,
                "run_id": NEXT_BUNDLE["metadata"].get("run_id"),
                "data_version": NEXT_BUNDLE["metadata"].get("data_version"),
                "source": NEXT_BUNDLE["loaded_from"],
            },
        },
        "api_security": {
            "auth_mode": API_AUTH_MODE,
            "token_count": len(ALLOWED_TOKENS) if API_AUTH_MODE != "off" else 0,
            "rate_limit_per_minute": API_RATE_LIMIT_PER_MINUTE,
        },
        "input_schema": ScoreInputRecord.model_json_schema()["properties"],
    }


@app.post("/score", response_model=ScoreResponse)
def score(
    payload: ScoreRequest,
    request: Request,
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ScoreResponse:
    token = _extract_auth_token(x_api_token=x_api_token, authorization=authorization)
    _check_auth(token=token)
    client_id = token or (request.client.host if request.client else "unknown")
    _enforce_rate_limit(client_id=client_id)

    if CHURN_BUNDLE["model"] is None or NEXT_BUNDLE["model"] is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model artifacts not available. Run pipeline to generate registry in "
                "data/processed/model_registry."
            ),
        )

    records = [record.model_dump() for record in payload.records]
    features = pd.DataFrame(records)

    churn_scores = CHURN_BUNDLE["model"].predict_proba(features)[:, 1].tolist()
    next_scores = NEXT_BUNDLE["model"].predict_proba(features)[:, 1].tolist()

    predictions = []
    for churn_probability, next_purchase_probability in zip(
        churn_scores, next_scores, strict=False
    ):
        predictions.append(
            {
                "churn_probability": float(churn_probability),
                "next_purchase_probability": float(next_purchase_probability),
                "suggested_action": _suggest_action(
                    churn_probability=float(churn_probability),
                    next_purchase_probability=float(next_purchase_probability),
                ),
            }
        )

    versions = {
        "churn": str(CHURN_BUNDLE["metadata"].get("run_id", "unknown")),
        "next_purchase_30d": str(NEXT_BUNDLE["metadata"].get("run_id", "unknown")),
    }
    return ScoreResponse(model_versions=versions, predictions=predictions)
