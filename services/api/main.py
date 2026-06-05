from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from contracts.data_contract import ScoreInputRecord, ScorePrediction, ScoreRequest, ScoreResponse
from src.config import load_env_file, resolve_optional_path
from src.exceptions import ConfigurationError
from src.logging_utils import configure_logging
from src.model_registry import load_registered_model

LOGGER = logging.getLogger("revenue_intelligence.api")
API_VERSION_PREFIX = "/api/v1"
REQUEST_ID_HEADER = "X-Request-ID"


@dataclass(frozen=True)
class APISettings:
    model_dir: Path
    auth_mode: str
    allowed_api_keys: set[str]
    rate_limit_per_minute: int
    log_level: str
    log_format: str

    @classmethod
    def from_env(cls) -> APISettings:
        project_root = Path(__file__).resolve().parents[2]
        load_env_file(project_root)

        resolved_model_dir = resolve_optional_path(
            project_root,
            os.getenv("RIP_MODEL_DIR", "data/processed"),
        )
        assert resolved_model_dir is not None
        auth_mode = os.getenv("RIP_API_AUTH_MODE", "demo").strip().lower()
        if auth_mode not in {"off", "demo", "strict"}:
            raise ConfigurationError("RIP_API_AUTH_MODE must be one of: off, demo, strict.")

        keys_from_env = os.getenv("RIP_API_KEYS", "")
        allowed_api_keys = {
            api_key.strip() for api_key in keys_from_env.split(",") if api_key.strip()
        }
        if not allowed_api_keys:
            single_key = os.getenv("RIP_API_KEY", "").strip()
            if single_key:
                allowed_api_keys = {single_key}

        if not allowed_api_keys:
            tokens_from_env = os.getenv("RIP_API_TOKENS", "")
            allowed_api_keys = {
                token.strip() for token in tokens_from_env.split(",") if token.strip()
            }

        if auth_mode == "strict" and not allowed_api_keys:
            raise ConfigurationError(
                "Strict API auth requires RIP_API_KEYS, RIP_API_KEY, or RIP_API_TOKENS."
            )

        if auth_mode == "demo" and not allowed_api_keys:
            allowed_api_keys = {os.getenv("RIP_API_DEMO_TOKEN", "rip-demo-token-v1")}

        raw_limit = os.getenv("RIP_API_RATE_LIMIT_PER_MINUTE", "60").strip()
        try:
            rate_limit_per_minute = int(raw_limit)
        except ValueError as exc:
            raise ConfigurationError("RIP_API_RATE_LIMIT_PER_MINUTE must be an integer.") from exc
        if rate_limit_per_minute < 1:
            raise ConfigurationError("RIP_API_RATE_LIMIT_PER_MINUTE must be >= 1.")
        log_level = os.getenv("RIP_LOG_LEVEL", "INFO").strip().upper()
        log_format = os.getenv("RIP_LOG_FORMAT", "text").strip().lower()
        if log_format not in {"text", "json"}:
            raise ConfigurationError("RIP_LOG_FORMAT must be one of: text, json.")

        return cls(
            model_dir=resolved_model_dir,
            auth_mode=auth_mode,
            allowed_api_keys=allowed_api_keys,
            rate_limit_per_minute=rate_limit_per_minute,
            log_level=log_level,
            log_format=log_format,
        )


@dataclass(frozen=True)
class ModelBundle:
    model: Any | None
    metadata: dict[str, Any]
    loaded_from: str


class TelemetryState:
    def __init__(self) -> None:
        self._lock = Lock()
        self.request_volume: dict[str, int] = defaultdict(int)
        self.model_version_usage: dict[str, int] = defaultdict(int)
        self.prediction_count = 0
        self.prediction_latency_total_ms = 0.0
        self.prediction_latency_last_ms = 0.0

    def record_request(self, endpoint: str, status_code: int) -> None:
        key = f"{endpoint}|{status_code}"
        with self._lock:
            self.request_volume[key] += 1

    def record_prediction(self, latency_ms: float, model_versions: dict[str, str]) -> None:
        with self._lock:
            self.prediction_count += 1
            self.prediction_latency_total_ms += latency_ms
            self.prediction_latency_last_ms = latency_ms
            for model_name, version in model_versions.items():
                self.model_version_usage[f"{model_name}:{version}"] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg_latency_ms = (
                self.prediction_latency_total_ms / self.prediction_count
                if self.prediction_count
                else 0.0
            )
            return {
                "prediction_latency_ms": {
                    "last": round(self.prediction_latency_last_ms, 3),
                    "average": round(avg_latency_ms, 3),
                    "total_predictions": self.prediction_count,
                },
                "request_volume": dict(self.request_volume),
                "model_version_usage": dict(self.model_version_usage),
            }

    def prometheus_lines(self) -> list[str]:
        snapshot = self.snapshot()
        prediction = snapshot["prediction_latency_ms"]
        lines = [
            "# HELP rip_api_predictions_total Total predictions served by the API.",
            "# TYPE rip_api_predictions_total counter",
            f"rip_api_predictions_total {prediction['total_predictions']}",
            "# HELP rip_api_prediction_latency_last_ms Last prediction latency in milliseconds.",
            "# TYPE rip_api_prediction_latency_last_ms gauge",
            f"rip_api_prediction_latency_last_ms {prediction['last']}",
            "# HELP rip_api_prediction_latency_avg_ms Average prediction latency in milliseconds.",
            "# TYPE rip_api_prediction_latency_avg_ms gauge",
            f"rip_api_prediction_latency_avg_ms {prediction['average']}",
        ]
        for key, value in sorted(snapshot["request_volume"].items()):
            endpoint, status_code = key.rsplit("|", 1)
            lines.extend(
                [
                    "# HELP rip_api_request_volume_total Total API requests by endpoint and status.",
                    "# TYPE rip_api_request_volume_total counter",
                    f'rip_api_request_volume_total{{endpoint="{endpoint}",status_code="{status_code}"}} {value}',
                ]
            )
        for key, value in sorted(snapshot["model_version_usage"].items()):
            model_name, version = key.split(":", 1)
            lines.extend(
                [
                    "# HELP rip_api_model_version_usage_total Total predictions by model version.",
                    "# TYPE rip_api_model_version_usage_total counter",
                    f'rip_api_model_version_usage_total{{model="{model_name}",version="{version}"}} {value}',
                ]
            )
        return lines


class APIService:
    def __init__(self, settings: APISettings) -> None:
        self.settings = settings
        self.telemetry = TelemetryState()
        self.request_history: dict[str, list[float]] = {}
        self.rate_limit_lock = Lock()
        self.churn_bundle = self._load_model_bundle("churn", "churn_model.joblib")
        self.next_bundle = self._load_model_bundle(
            "next_purchase_30d",
            "next_purchase_model.joblib",
        )

    def _load_model_bundle(self, model_name: str, legacy_name: str) -> ModelBundle:
        try:
            model, metadata = load_registered_model(self.settings.model_dir, model_name)
            return ModelBundle(model=model, metadata=metadata, loaded_from="registry")
        except FileNotFoundError:
            legacy_path = self.settings.model_dir / legacy_name
            if not legacy_path.exists():
                return ModelBundle(model=None, metadata={}, loaded_from="missing")
            try:
                import joblib

                model = joblib.load(legacy_path)
                return ModelBundle(
                    model=model,
                    metadata={
                        "run_id": "legacy",
                        "data_version": "legacy",
                        "model_name": model_name,
                    },
                    loaded_from="legacy",
                )
            except Exception:
                return ModelBundle(model=None, metadata={}, loaded_from="broken")

    def check_auth(self, api_key: str | None) -> None:
        if self.settings.auth_mode == "off":
            return

        if api_key is None:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Missing API key. Provide `X-API-Key` (preferred), `X-API-Token` (legacy), "
                    "or `Authorization: Bearer <key>`."
                ),
            )

        if api_key not in self.settings.allowed_api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key.")

    def enforce_rate_limit(self, client_id: str) -> None:
        now = time.time()
        window_start = now - 60
        with self.rate_limit_lock:
            history = self.request_history.setdefault(client_id, [])
            while history and history[0] <= window_start:
                history.pop(0)
            if len(history) >= self.settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Rate limit exceeded. Try again in 60 seconds or request a higher quota."
                    ),
                )
            history.append(now)

    def health_payload(self) -> dict[str, Any]:
        churn_loaded = self.churn_bundle.model is not None
        next_loaded = self.next_bundle.model is not None
        status = "ok" if churn_loaded and next_loaded else "degraded"
        return {
            "status": status,
            "model_dir": str(self.settings.model_dir.resolve()),
            "models": {
                "churn": {
                    "loaded": churn_loaded,
                    "run_id": self.churn_bundle.metadata.get("run_id"),
                    "data_version": self.churn_bundle.metadata.get("data_version"),
                    "source": self.churn_bundle.loaded_from,
                },
                "next_purchase_30d": {
                    "loaded": next_loaded,
                    "run_id": self.next_bundle.metadata.get("run_id"),
                    "data_version": self.next_bundle.metadata.get("data_version"),
                    "source": self.next_bundle.loaded_from,
                },
            },
            "api_security": {
                "auth_mode": self.settings.auth_mode,
                "api_key_count": (
                    len(self.settings.allowed_api_keys) if self.settings.auth_mode != "off" else 0
                ),
                "accepted_headers": ["X-API-Key", "Authorization: Bearer <key>", "X-API-Token"],
                "rate_limit_per_minute": self.settings.rate_limit_per_minute,
            },
            "telemetry": self.telemetry.snapshot(),
            "input_schema": ScoreInputRecord.model_json_schema()["properties"],
            "export_surfaces": [
                "/api/v1/executive-summary",
                "/api/v1/scorecard",
                "/api/v1/insight-draft",
                "/api/v1/reliability-report",
                "/api/v1/exports/top-actions.csv",
            ],
        }

    def readiness_payload(self) -> dict[str, Any]:
        health = self.health_payload()
        required_artifacts = [
            "executive_summary.json",
            "insight_draft.json",
            "reliability_report.json",
            "top_10_actions.csv",
        ]
        artifacts = {name: (self.settings.model_dir / name).exists() for name in required_artifacts}
        ready = health["status"] == "ok" and all(artifacts.values())
        return {
            "status": "ready" if ready else "degraded",
            "models_status": health["status"],
            "artifacts": artifacts,
            "export_surfaces_ready": all(artifacts.values()),
        }

    def read_processed_json(self, file_name: str) -> dict[str, Any]:
        path = self.settings.model_dir / file_name
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"Processed artifact not found: {file_name}"
            )
        import json

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=500, detail=f"Artifact {file_name} must be a JSON object."
            )
        return payload

    def read_processed_csv_text(self, file_name: str) -> str:
        path = self.settings.model_dir / file_name
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"Processed artifact not found: {file_name}"
            )
        return path.read_text(encoding="utf-8")

    def executive_scorecard_payload(self) -> dict[str, Any]:
        executive_summary = self.read_processed_json("executive_summary.json")
        insight_draft = self.read_processed_json("insight_draft.json")
        reliability_report = self.read_processed_json("reliability_report.json")
        return {
            "executive_summary": executive_summary,
            "insight_draft": {
                "headline": insight_draft.get("headline"),
                "summary": insight_draft.get("summary"),
                "recommended_actions": insight_draft.get("recommended_actions", []),
            },
            "reliability": {
                "status": reliability_report.get("status"),
                "runtime": reliability_report.get("runtime", {}),
                "governance": reliability_report.get("governance", {}),
            },
        }


def _extract_auth_token(
    x_api_key: str | None,
    x_api_token: str | None,
    authorization: str | None,
) -> str | None:
    if x_api_key:
        return x_api_key.strip()
    if x_api_token:
        return x_api_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if token:
            return token
    return None


def _suggest_action(churn_probability: float, next_purchase_probability: float) -> str:
    if churn_probability >= 0.7:
        return "Retention Campaign"
    if next_purchase_probability >= 0.6:
        return "Upsell Offer"
    if churn_probability <= 0.25 and next_purchase_probability <= 0.35:
        return "Reduce Acquisition Spend"
    return "Nurture"


def _service(request: Request) -> APIService:
    return request.app.state.api_service


def _resolve_request_id(request: Request) -> str:
    incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
    if incoming:
        return incoming
    return f"rip-{uuid4().hex}"


def create_app(settings: APISettings | None = None) -> FastAPI:
    resolved_settings = settings or APISettings.from_env()
    configure_logging(level=resolved_settings.log_level, log_format=resolved_settings.log_format)
    app = FastAPI(
        title="Revenue Intelligence Model Serving API",
        version="1.1.0",
        description=(
            "Serve churn and next-purchase predictions with explicit contracts, "
            "versioned endpoints and production telemetry."
        ),
    )
    app.state.api_service = APIService(resolved_settings)

    @app.middleware("http")
    async def http_telemetry(request: Request, call_next: Any) -> Response:
        request_id = _resolve_request_id(request)
        request.state.request_id = request_id
        response = await call_next(request)
        service = _service(request)
        service.telemetry.record_request(
            endpoint=request.url.path, status_code=response.status_code
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        LOGGER.info(
            "request_volume request_id=%s method=%s endpoint=%s status_code=%s total=%s client=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            service.telemetry.request_volume.get(
                f"{request.url.path}|{response.status_code}",
                0,
            ),
            request.client.host if request.client else "unknown",
            extra={"request_id": request_id},
        )
        return response

    @app.get(f"{API_VERSION_PREFIX}/health")
    @app.get("/health")
    def health(request: Request) -> dict[str, Any]:
        return _service(request).health_payload()

    @app.get(f"{API_VERSION_PREFIX}/ready")
    @app.get("/ready")
    def ready(request: Request) -> dict[str, Any]:
        return _service(request).readiness_payload()

    @app.get(f"{API_VERSION_PREFIX}/metrics", response_class=PlainTextResponse)
    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics(request: Request) -> PlainTextResponse:
        body = "\n".join(_service(request).telemetry.prometheus_lines()) + "\n"
        response = PlainTextResponse(body)
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        return response

    @app.get(f"{API_VERSION_PREFIX}/executive-summary")
    @app.get("/executive-summary")
    def executive_summary(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> JSONResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key, x_api_token=x_api_token, authorization=authorization
        )
        service.check_auth(api_key=api_key)
        response = JSONResponse(service.read_processed_json("executive_summary.json"))
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        return response

    @app.get(f"{API_VERSION_PREFIX}/scorecard")
    @app.get("/scorecard")
    def scorecard(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> JSONResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key, x_api_token=x_api_token, authorization=authorization
        )
        service.check_auth(api_key=api_key)
        response = JSONResponse(service.executive_scorecard_payload())
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        return response

    @app.get(f"{API_VERSION_PREFIX}/insight-draft")
    @app.get("/insight-draft")
    def insight_draft(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> JSONResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key, x_api_token=x_api_token, authorization=authorization
        )
        service.check_auth(api_key=api_key)
        response = JSONResponse(service.read_processed_json("insight_draft.json"))
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        return response

    @app.get(f"{API_VERSION_PREFIX}/reliability-report")
    @app.get("/reliability-report")
    def reliability_report(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> JSONResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key, x_api_token=x_api_token, authorization=authorization
        )
        service.check_auth(api_key=api_key)
        response = JSONResponse(service.read_processed_json("reliability_report.json"))
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        return response

    @app.get(f"{API_VERSION_PREFIX}/exports/top-actions.csv", response_class=PlainTextResponse)
    @app.get("/exports/top-actions.csv", response_class=PlainTextResponse)
    def top_actions_export(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> PlainTextResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key, x_api_token=x_api_token, authorization=authorization
        )
        service.check_auth(api_key=api_key)
        response = PlainTextResponse(service.read_processed_csv_text("top_10_actions.csv"))
        response.headers[REQUEST_ID_HEADER] = getattr(request.state, "request_id", "n/a")
        response.headers["Content-Disposition"] = 'attachment; filename="top_10_actions.csv"'
        return response

    @app.post(f"{API_VERSION_PREFIX}/score", response_model=ScoreResponse)
    @app.post("/score", response_model=ScoreResponse)
    def score(
        payload: ScoreRequest,
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_api_token: str | None = Header(default=None, alias="X-API-Token"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> ScoreResponse:
        service = _service(request)
        api_key = _extract_auth_token(
            x_api_key=x_api_key,
            x_api_token=x_api_token,
            authorization=authorization,
        )
        service.check_auth(api_key=api_key)
        client_id = api_key or (request.client.host if request.client else "unknown")
        service.enforce_rate_limit(client_id=client_id)

        if service.churn_bundle.model is None or service.next_bundle.model is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Model artifacts not available. Run pipeline to generate registry in "
                    "data/processed/registry."
                ),
            )

        prediction_start = time.perf_counter()
        features = pd.DataFrame([record.model_dump() for record in payload.records])
        churn_scores = service.churn_bundle.model.predict_proba(features)[:, 1].tolist()
        next_scores = service.next_bundle.model.predict_proba(features)[:, 1].tolist()

        predictions = [
            ScorePrediction(
                churn_probability=float(churn_probability),
                next_purchase_probability=float(next_purchase_probability),
                suggested_action=_suggest_action(
                    churn_probability=float(churn_probability),
                    next_purchase_probability=float(next_purchase_probability),
                ),
            )
            for churn_probability, next_purchase_probability in zip(
                churn_scores,
                next_scores,
                strict=False,
            )
        ]

        versions = {
            "churn": str(service.churn_bundle.metadata.get("run_id", "unknown")),
            "next_purchase_30d": str(service.next_bundle.metadata.get("run_id", "unknown")),
        }
        prediction_latency_ms = (time.perf_counter() - prediction_start) * 1000
        service.telemetry.record_prediction(
            latency_ms=prediction_latency_ms,
            model_versions=versions,
        )
        LOGGER.info(
            "prediction_latency_ms=%.3f request_id=%s model_version_usage=%s",
            prediction_latency_ms,
            getattr(request.state, "request_id", "n/a"),
            versions,
            extra={"request_id": getattr(request.state, "request_id", "n/a")},
        )
        return ScoreResponse(model_versions=versions, predictions=predictions)

    return app


app = create_app()


def health() -> dict[str, Any]:
    return app.state.api_service.health_payload()


def score(*args: Any, **kwargs: Any) -> ScoreResponse:
    raise RuntimeError("Use the FastAPI application routes instead of calling score() directly.")
