import pandas as pd

from src.metrics import build_business_kpi_snapshot, calculate_ltv
from src.modeling import _build_preprocessor
from src.quality import build_dataset_quality_report, enforce_quality_gate


def test_business_kpi_snapshot_centralizes_revenue_metrics() -> None:
    recommendations = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "ltv": [1000.0, 1500.0],
            "cac": [100.0, 300.0],
            "ltv_cac_ratio": [10.0, 5.0],
            "churn_probability": [0.2, 0.8],
            "channel": ["Organic", "Paid Search"],
        }
    )
    scored = pd.DataFrame({"monetary": [400.0, 600.0], "arpu": [40.0, 60.0]})
    unit = pd.DataFrame(
        {
            "channel": ["Paid Search", "Organic"],
            "ltv_cac_ratio": [3.1, 4.2],
        }
    )

    snapshot = build_business_kpi_snapshot(recommendations, scored, unit)

    assert snapshot["revenue_proxy"] == 1000.0
    assert snapshot["portfolio_size"] == 2
    assert snapshot["best_channel_efficiency"]["channel"] == "Organic"


def test_quality_gate_detects_duplicate_primary_keys() -> None:
    df = pd.DataFrame({"customer_id": [1, 1], "channel": ["Organic", "Organic"]})
    report = build_dataset_quality_report(df, "silver_customers", primary_key="customer_id")

    try:
        enforce_quality_gate([report])
    except Exception as exc:
        assert "duplicate" in str(exc).lower()
    else:  # pragma: no cover - defensive path
        raise AssertionError("Expected quality gate to fail on duplicate keys")


def test_quality_gate_detects_excessive_null_fraction() -> None:
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "segment": [None, None, "SMB"],
            "channel": ["Organic", None, None],
        }
    )
    report = build_dataset_quality_report(df, "silver_customers", primary_key="customer_id")

    try:
        enforce_quality_gate([report], max_total_null_fraction=0.20)
    except Exception as exc:
        assert "null fraction" in str(exc).lower()
    else:  # pragma: no cover - defensive path
        raise AssertionError("Expected quality gate to fail on null fraction threshold")


def test_quality_gate_detects_dataset_rule_violation() -> None:
    df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "customer_id": [1],
            "order_date": ["2025-01-01"],
            "order_value": [-10.0],
        }
    )

    report = build_dataset_quality_report(df, "silver_orders", primary_key="order_id")

    try:
        enforce_quality_gate([report])
    except Exception as exc:
        assert "negative values" in str(exc).lower()
    else:  # pragma: no cover - defensive path
        raise AssertionError("Expected quality gate to fail on dataset-specific rule violation")


def test_preprocessor_handles_expected_feature_groups() -> None:
    preprocessor, numeric_features, categorical_features = _build_preprocessor()
    frame = pd.DataFrame(
        {
            "recency_days": [10, 20],
            "frequency": [2, 5],
            "monetary": [200.0, 500.0],
            "avg_order_value": [100.0, 100.0],
            "tenure_days": [90, 180],
            "arpu": [66.0, 83.0],
            "channel": ["Organic", "Paid Search"],
            "segment": ["SMB", "Enterprise"],
        }
    )

    transformed = preprocessor.fit_transform(frame)

    assert numeric_features == [
        "recency_days",
        "frequency",
        "monetary",
        "avg_order_value",
        "tenure_days",
        "arpu",
    ]
    assert categorical_features == ["channel", "segment"]
    assert transformed.shape[0] == 2


def test_calculate_ltv_outputs_non_negative_values() -> None:
    frame = pd.DataFrame(
        {
            "customer_id": [1],
            "is_churned": [0],
            "arpu": [120.0],
        }
    )

    result = calculate_ltv(frame)

    assert result.loc[0, "ltv"] >= 0
