from __future__ import annotations

import importlib
import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

from src.exceptions import ConfigurationError
from src.model_registry import register_model


def _build_dummy_pipeline() -> Pipeline:
    feature_names = [
        "recency_days",
        "frequency",
        "monetary",
        "avg_order_value",
        "tenure_days",
        "arpu",
        "channel",
        "segment",
    ]
    x = pd.DataFrame(
        [
            [10, 5, 1000.0, 200.0, 300, 120.0, "Organic", "SMB"],
            [120, 1, 100.0, 100.0, 30, 40.0, "Paid Search", "Enterprise"],
        ],
        columns=feature_names,
    )
    y = [0, 1]
    pipe = Pipeline(steps=[("clf", DummyClassifier(strategy="stratified", random_state=42))])
    pipe.fit(x, y)
    return pipe


def _bootstrap_registry(tmp_path: Path) -> None:
    model_dir = tmp_path / "processed"
    model_dir.mkdir(parents=True, exist_ok=True)
    feature_names = [
        "recency_days",
        "frequency",
        "monetary",
        "avg_order_value",
        "tenure_days",
        "arpu",
        "channel",
        "segment",
    ]
    register_model(
        model_name="churn",
        model=_build_dummy_pipeline(),
        output_dir=model_dir,
        data_version="test-v1",
        metrics={"cv_roc_auc_mean": 0.5},
        input_features=feature_names,
        target_name="is_churned",
    )
    register_model(
        model_name="next_purchase_30d",
        model=_build_dummy_pipeline(),
        output_dir=model_dir,
        data_version="test-v1",
        metrics={"cv_roc_auc_mean": 0.5},
        input_features=feature_names,
        target_name="next_purchase_30d",
    )
    (model_dir / "executive_summary.json").write_text(
        '{"kpis":{"total_revenue_proxy":1000},"top_20_recommended_actions":[]}',
        encoding="utf-8",
    )
    (model_dir / "insight_draft.json").write_text(
        '{"headline":"ok","summary":"demo","recommended_actions":["a"]}',
        encoding="utf-8",
    )
    (model_dir / "reliability_report.json").write_text(
        '{"status":"ok","runtime":{"total_runtime_seconds":1.0},"operational_readout":{"headline":"ok"}}',
        encoding="utf-8",
    )
    (model_dir / "top_10_actions.csv").write_text(
        "priority_rank,customer_id,action\n1,10,Upsell Offer\n",
        encoding="utf-8",
    )


def test_api_health_and_score(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.headers["X-Request-ID"].startswith("rip-")
    health_payload = health.json()
    assert health_payload["status"] == "ok"
    assert health_payload["models"]["churn"]["loaded"] is True
    assert health_payload["api_security"]["auth_mode"] == "demo"
    assert health_payload["api_security"]["api_key_count"] == 1
    assert "recency_days" in health_payload["input_schema"]
    assert "prediction_latency_ms" in health_payload["telemetry"]
    assert "request_volume" in health_payload["telemetry"]
    assert "model_version_usage" in health_payload["telemetry"]

    score = client.post(
        "/api/v1/score",
        json={
            "records": [
                {
                    "recency_days": 14,
                    "frequency": 8,
                    "monetary": 1800.0,
                    "avg_order_value": 225.0,
                    "tenure_days": 420,
                    "arpu": 160.0,
                    "channel": "Organic",
                    "segment": "SMB",
                }
            ]
        },
        headers={"X-API-Key": "test-token"},
    )
    assert score.status_code == 200
    assert score.headers["X-Request-ID"].startswith("rip-")
    score_payload = score.json()
    assert len(score_payload["predictions"]) == 1
    assert "churn_probability" in score_payload["predictions"][0]
    assert "next_purchase_probability" in score_payload["predictions"][0]
    assert "suggested_action" in score_payload["predictions"][0]


def test_api_preserves_incoming_request_id(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    response = client.get("/api/v1/health", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"


def test_api_ready_surface_reports_export_readiness(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["export_surfaces_ready"] is True


def test_api_metrics_surface_exposes_prometheus_text(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    client.get("/api/v1/health")
    client.post(
        "/api/v1/score",
        json={
            "records": [
                {
                    "recency_days": 14,
                    "frequency": 8,
                    "monetary": 1800.0,
                    "avg_order_value": 225.0,
                    "tenure_days": 420,
                    "arpu": 160.0,
                    "channel": "Organic",
                    "segment": "SMB",
                }
            ]
        },
        headers={"X-API-Key": "test-token"},
    )
    metrics = client.get("/api/v1/metrics", headers={"X-Request-ID": "req-metrics"})

    assert metrics.status_code == 200
    assert metrics.headers["content-type"].startswith("text/plain")
    assert metrics.headers["X-Request-ID"] == "req-metrics"
    assert "rip_api_predictions_total" in metrics.text
    assert (
        'rip_api_request_volume_total{endpoint="/api/v1/health",status_code="200"}' in metrics.text
    )


def test_api_exposes_governed_export_surfaces(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)
    headers = {"X-API-Key": "test-token"}

    executive = client.get("/api/v1/executive-summary", headers=headers)
    scorecard = client.get("/api/v1/scorecard", headers=headers)
    insight = client.get("/api/v1/insight-draft", headers=headers)
    reliability = client.get("/api/v1/reliability-report", headers=headers)
    export_csv = client.get("/api/v1/exports/top-actions.csv", headers=headers)

    assert executive.status_code == 200
    assert scorecard.status_code == 200
    assert insight.status_code == 200
    assert reliability.status_code == 200
    assert export_csv.status_code == 200
    assert export_csv.headers["content-disposition"].startswith("attachment;")
    assert "priority_rank,customer_id,action" in export_csv.text


def test_api_requires_token(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    score = client.post(
        "/api/v1/score",
        json={
            "records": [
                {
                    "recency_days": 14,
                    "frequency": 8,
                    "monetary": 1800.0,
                    "avg_order_value": 225.0,
                    "tenure_days": 420,
                    "arpu": 160.0,
                    "channel": "Organic",
                    "segment": "SMB",
                }
            ]
        },
    )
    assert score.status_code == 401


def test_api_rate_limit_enforced(tmp_path: Path) -> None:
    _bootstrap_registry(tmp_path)
    os.environ["RIP_MODEL_DIR"] = str(tmp_path / "processed")
    os.environ["RIP_API_AUTH_MODE"] = "demo"
    os.environ["RIP_API_DEMO_TOKEN"] = "test-token"
    os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "1"

    api_module = importlib.import_module("services.api.main")
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    payload = {
        "records": [
            {
                "recency_days": 14,
                "frequency": 8,
                "monetary": 1800.0,
                "avg_order_value": 225.0,
                "tenure_days": 420,
                "arpu": 160.0,
                "channel": "Organic",
                "segment": "SMB",
            }
        ]
    }
    headers = {"Authorization": "Bearer test-token"}
    first = client.post("/api/v1/score", json=payload, headers=headers)
    second = client.post("/api/v1/score", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 429


def test_api_strict_mode_requires_explicit_key_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bootstrap_registry(tmp_path)
    monkeypatch.setenv("RIP_MODEL_DIR", str(tmp_path / "processed"))
    monkeypatch.setenv("RIP_API_AUTH_MODE", "strict")
    monkeypatch.delenv("RIP_API_KEYS", raising=False)
    monkeypatch.delenv("RIP_API_KEY", raising=False)
    monkeypatch.delenv("RIP_API_TOKENS", raising=False)
    monkeypatch.delenv("RIP_API_DEMO_TOKEN", raising=False)

    with pytest.raises(ConfigurationError):
        importlib.reload(importlib.import_module("services.api.main"))


def test_api_model_dir_is_resolved_from_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bootstrap_registry(tmp_path)
    project_root = Path(__file__).resolve().parents[1]
    relative_model_dir = os.path.relpath(tmp_path / "processed", project_root)
    monkeypatch.setenv("RIP_MODEL_DIR", relative_model_dir)
    monkeypatch.setenv("RIP_API_AUTH_MODE", "demo")
    monkeypatch.setenv("RIP_API_DEMO_TOKEN", "test-token")

    isolated_root = project_root / "tests" / "fixtures"
    isolated_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(isolated_root)

    api_module = importlib.reload(importlib.import_module("services.api.main"))
    settings = api_module.APISettings.from_env()

    assert settings.model_dir == (tmp_path / "processed").resolve()
