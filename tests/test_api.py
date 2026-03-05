from __future__ import annotations

import importlib
import os
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

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
    score_payload = score.json()
    assert len(score_payload["predictions"]) == 1
    assert "churn_probability" in score_payload["predictions"][0]
    assert "next_purchase_probability" in score_payload["predictions"][0]
    assert "suggested_action" in score_payload["predictions"][0]


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
