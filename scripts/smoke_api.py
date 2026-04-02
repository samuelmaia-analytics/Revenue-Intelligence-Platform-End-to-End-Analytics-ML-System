from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.model_registry import register_model  # noqa: E402


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
    features = pd.DataFrame(
        [
            [10, 5, 1000.0, 200.0, 300, 120.0, "Organic", "SMB"],
            [120, 1, 100.0, 100.0, 30, 40.0, "Paid Search", "Enterprise"],
        ],
        columns=feature_names,
    )
    target = [0, 1]
    pipeline = Pipeline(steps=[("clf", DummyClassifier(strategy="stratified", random_state=42))])
    pipeline.fit(features, target)
    return pipeline


def _bootstrap_registry(output_dir: Path) -> None:
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
        output_dir=output_dir,
        data_version="smoke-test-v1",
        metrics={"cv_roc_auc_mean": 0.5},
        input_features=feature_names,
        target_name="is_churned",
    )
    register_model(
        model_name="next_purchase_30d",
        model=_build_dummy_pipeline(),
        output_dir=output_dir,
        data_version="smoke-test-v1",
        metrics={"cv_roc_auc_mean": 0.5},
        input_features=feature_names,
        target_name="next_purchase_30d",
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rip-api-smoke-") as temp_dir:
        model_dir = Path(temp_dir) / "processed"
        _bootstrap_registry(model_dir)

        os.environ["RIP_MODEL_DIR"] = str(model_dir)
        os.environ["RIP_API_AUTH_MODE"] = "demo"
        os.environ["RIP_API_DEMO_TOKEN"] = "smoke-token"
        os.environ["RIP_API_RATE_LIMIT_PER_MINUTE"] = "5"

        api_module = importlib.import_module("services.api.main")
        api_module = importlib.reload(api_module)
        client = TestClient(api_module.app)

        health = client.get("/api/v1/health")
        if health.status_code != 200:
            raise SystemExit(f"API smoke failed: health returned {health.status_code}.")
        if "X-Request-ID" not in health.headers:
            raise SystemExit("API smoke failed: health response missing X-Request-ID.")

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
            headers={"X-API-Key": "smoke-token"},
        )
        if score.status_code != 200:
            raise SystemExit(f"API smoke failed: score returned {score.status_code}.")

        payload = score.json()
        prediction = payload["predictions"][0]
        for key in ["churn_probability", "next_purchase_probability", "suggested_action"]:
            if key not in prediction:
                raise SystemExit(f"API smoke failed: missing key '{key}' in prediction payload.")

        metrics = client.get("/api/v1/metrics", headers={"X-Request-ID": "smoke-metrics"})
        if metrics.status_code != 200:
            raise SystemExit(f"API smoke failed: metrics returned {metrics.status_code}.")
        if "rip_api_predictions_total" not in metrics.text:
            raise SystemExit("API smoke failed: metrics surface missing prediction counter.")

    print("API smoke check passed.")


if __name__ == "__main__":
    main()
