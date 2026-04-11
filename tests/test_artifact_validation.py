from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.artifact_validation import validate_processed_artifacts
from src.exceptions import DataQualityError


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _build_valid_processed_artifacts(processed_dir: Path) -> None:
    _write_json(
        processed_dir / "quality_report.json",
        {
            "datasets": [
                {
                    "dataset_name": "silver_customers",
                    "row_count": 10,
                    "duplicate_rows": 0,
                    "null_counts": {},
                    "null_fraction_by_column": {},
                    "total_null_fraction": 0.0,
                    "referential_issues": 0,
                }
            ],
            "total_datasets": 1,
        },
    )
    _write_json(
        processed_dir / "quality_business_rules.json",
        {
            "checks": {
                "customer_id_uniqueness_violations": 0,
                "order_id_uniqueness_violations": 0,
            },
            "status": "ok",
        },
    )
    _write_json(
        processed_dir / "freshness_report.json",
        {
            "evaluated_at_utc": "2026-01-01T00:00:00+00:00",
            "max_age_hours": 48,
            "status": "ok",
            "checks": [],
        },
    )
    _write_json(
        processed_dir / "raw_input_metadata.json",
        {
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "dataset_count": 3,
            "datasets": [],
        },
    )
    _write_json(
        processed_dir / "kpi_snapshot.json",
        {
            "revenue_proxy": 4200.0,
            "avg_arpu": 70.0,
            "avg_ltv": 420.0,
            "avg_cac": 70.0,
            "avg_ltv_cac_ratio": 6.0,
            "portfolio_size": 10,
            "best_channel_efficiency": {"channel": "Organic", "ltv_cac_ratio": 6.0},
        },
    )
    _write_json(
        processed_dir / "metrics_report.json",
        {
            "churn": {
                "model_name": "churn",
                "cv_roc_auc_mean": 0.72,
                "temporal_test_roc_auc": 0.74,
            },
            "next_purchase_30d": {
                "model_name": "next_purchase_30d",
                "cv_roc_auc_mean": 0.68,
                "temporal_test_roc_auc": 0.66,
            },
        },
    )
    _write_csv(
        processed_dir / "customer_features.csv",
        [
            {
                "customer_id": 1,
                "segment": "Enterprise",
                "channel": "Organic",
                "recency_days": 12,
                "frequency": 3,
                "monetary": 420.0,
                "avg_order_value": 140.0,
                "tenure_days": 180,
                "arpu": 70.0,
                "is_churned": 0,
                "next_purchase_30d": 1,
            }
        ],
    )
    _write_csv(
        processed_dir / "recommendations.csv",
        [
            {
                "customer_id": 1,
                "channel": "Organic",
                "segment": "Enterprise",
                "ltv": 420.0,
                "cac": 70.0,
                "ltv_cac_ratio": 6.0,
                "churn_probability": 0.2,
                "next_purchase_probability": 0.6,
                "strategic_score": 0.8,
                "recommended_action": "Upsell Offer",
            }
        ],
    )
    _write_csv(
        processed_dir / "unit_economics.csv",
        [
            {
                "channel": "Organic",
                "marketing_spend": 700.0,
                "customers_acquired": 10,
                "cac": 70.0,
                "avg_arpu": 42.0,
                "ltv_cac_ratio": 6.0,
                "contribution_margin": 210.0,
                "payback_period_months": 1.7,
            }
        ],
    )
    _write_csv(
        processed_dir / "top_10_actions.csv",
        [
            {
                "priority_rank": 1,
                "customer_id": 1,
                "channel": "Organic",
                "segment": "Enterprise",
                "action": "Upsell Offer",
                "strategic_priority_score": 0.8,
                "expected_uplift": 40.0,
                "action_cost": 8.0,
                "net_impact": 32.0,
                "roi_simulated": 4.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "cac_by_channel.csv",
        [
            {
                "channel": "Organic",
                "marketing_spend": 700.0,
                "customers_acquired": 10,
                "cac": 70.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "ltv.csv",
        [
            {
                "customer_id": 1,
                "channel": "Organic",
                "segment": "Enterprise",
                "ltv": 420.0,
                "churn_probability": 0.2,
                "next_purchase_probability": 0.6,
            }
        ],
    )
    _write_csv(
        processed_dir / "rfm_segments.csv",
        [
            {
                "customer_id": 1,
                "channel": "Organic",
                "recency": 12,
                "frequency": 3,
                "monetary": 420.0,
                "r_score": 5,
                "f_score": 4,
                "m_score": 5,
                "rfm_total": 14,
                "segment": "Champions",
            }
        ],
    )
    _write_csv(
        processed_dir / "cohort_retention.csv",
        [
            {
                "cohort_month": "2025-01-01",
                "cohort_index": 0,
                "active_customers": 10,
                "cohort_size": 10,
                "retention_rate": 1.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "customer_analytics.csv",
        [
            {
                "customer_id": 1,
                "channel": "Organic",
                "segment": "Enterprise",
                "recency_days": 12,
                "frequency": 3,
                "monetary": 420.0,
                "ltv": 420.0,
                "churn_probability": 0.2,
                "next_purchase_probability": 0.6,
                "recommended_action": "Upsell Offer",
            }
        ],
    )
    _write_csv(
        processed_dir / "payment_analytics.csv",
        [
            {
                "channel": "Organic",
                "total_orders": 10,
                "total_revenue": 4200.0,
                "avg_ticket": 420.0,
                "revenue_share_pct": 1.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "geographic_analytics.csv",
        [
            {
                "state": "SP",
                "total_orders": 10,
                "unique_customers": 9,
                "total_revenue": 4200.0,
                "revenue_share_pct": 1.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "logistics_analytics.csv",
        [
            {
                "order_month": "2025-01",
                "total_orders": 10,
                "delivered_orders": 9,
                "canceled_orders": 1,
                "avg_delivery_days": 7.0,
                "late_delivery_rate": 0.1,
            }
        ],
    )
    _write_csv(
        processed_dir / "executive_summary_layer.csv",
        [
            {
                "order_month": "2025-01",
                "total_revenue": 4200.0,
                "total_orders": 10,
                "unique_customers": 9,
                "avg_ticket": 420.0,
            }
        ],
    )
    _write_csv(
        processed_dir / "executive_scorecard.csv",
        [
            {
                "snapshot_date": "2026-01-01",
                "total_revenue": 4200.0,
                "total_orders": 10,
                "average_ticket": 420.0,
                "recurring_customer_rate": 0.4,
                "late_delivery_rate": 0.1,
                "m1_retention_rate": 0.3,
            }
        ],
    )
    _write_csv(
        processed_dir / "customer_segment_health.csv",
        [
            {
                "recommended_action": "Upsell Offer",
                "rfm_segment": "Champions",
                "churn_risk_band": "Low",
                "customers": 4,
                "revenue_proxy": 1800.0,
                "avg_ltv": 450.0,
                "avg_churn_probability": 0.2,
            }
        ],
    )
    _write_csv(
        processed_dir / "payment_scorecard.csv",
        [
            {
                "channel": "Organic",
                "total_orders": 10,
                "total_revenue": 4200.0,
                "avg_ticket": 420.0,
                "revenue_share_pct": 1.0,
                "on_time_delivery_rate": 0.9,
            }
        ],
    )
    _write_csv(
        processed_dir / "retention_scorecard.csv",
        [
            {
                "cohort_month": "2025-01",
                "cohort_index": 1,
                "active_customers": 3,
                "cohort_size": 10,
                "retention_rate": 0.3,
            }
        ],
    )
    _write_json(
        processed_dir / "executive_report.json",
        {
            "data_refresh_utc": "2026-01-01T00:00:00+00:00",
            "base_size": {"customers_in_scope": 10, "rows_in_recommendation_table": 10},
            "top_kpis": {"avg_ltv": 420.0},
            "business_context": {"revenue_proxy": 4200.0},
            "model_performance": {"churn": {}, "next_purchase_30d": {}},
            "recommendations_top_20": [],
        },
    )
    _write_json(
        processed_dir / "executive_summary.json",
        {
            "data_refresh_utc": "2026-01-01T00:00:00+00:00",
            "kpis": {"total_revenue_proxy": 4200.0, "avg_arpu": 70.0},
            "ltv_cac_by_channel": [],
            "top_churn_risk_customers": [],
            "top_20_recommended_actions": [],
        },
    )
    _write_json(
        processed_dir / "business_outcomes.json",
        {
            "data_refresh_utc": "2026-01-01T00:00:00+00:00",
            "kpis": {"avg_ltv_cac_ratio": 6.0, "simulated_net_impact_top10": 32.0},
            "simulation_assumptions": {},
            "simulation_summary_top10": {"delta_revenue_90d": 40.0},
            "top_10_actions": [],
        },
    )
    _write_json(
        processed_dir / "monitoring_report.json",
        {
            "drift_status": "stable",
            "numeric_summary": {},
            "feature_drift": {},
            "calibration": {"churn": {}, "next_purchase_30d": {}},
        },
    )
    _write_json(
        processed_dir / "alerts_report.json",
        {
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "thresholds": {},
            "alert_count": 0,
            "status": "ok",
            "alerts": [],
        },
    )
    _write_json(
        processed_dir / "insight_draft.json",
        {
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "run_id": "20260101T000000Z-test",
            "mode_requested": "deterministic",
            "mode_applied": "deterministic",
            "headline": "Revenue portfolio stable",
            "summary": "Top marketplace KPIs are available.",
            "kpi_highlights": [],
            "anomalies": [],
            "recommended_actions": [],
            "evidence": {"revenue_proxy": 4200.0},
        },
    )
    _write_json(
        processed_dir / "runtime_metrics.json",
        {
            "run_id": "20260101T000000Z-test",
            "environment": "test",
            "log_format": "json",
            "stage_count": 3,
            "stage_timings_seconds": {"ingestion.raw": 0.1, "modeling.ml": 0.2},
            "total_runtime_seconds": 0.3,
            "event_count": 1,
            "output_count": 20,
            "outputs": ["runtime_metrics.json"],
        },
    )
    _write_json(
        processed_dir / "reliability_report.json",
        {
            "run_id": "20260101T000000Z-test",
            "status": "ok",
            "summary": "Artifacts validated successfully.",
        },
    )
    (processed_dir / "run_events.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "event_type": "pipeline.started",
                "run_id": "20260101T000000Z-test",
                "status": "running",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(processed_dir / "semantic_metrics_catalog.json", {"metrics": []})
    _write_json(
        processed_dir / "executive_kpis.json",
        {
            "total_revenue": 4200.0,
            "total_orders": 10,
            "average_ticket": 420.0,
            "unique_customers": 9,
            "avg_review_score": 4.3,
        },
    )


def test_validate_processed_artifacts_writes_report(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _build_valid_processed_artifacts(processed_dir)

    report = validate_processed_artifacts(
        processed_dir,
        output_path=processed_dir / "artifact_validation_report.json",
    )

    assert report["status"] == "ok"
    assert int(report["artifact_count"]) == 33
    assert (processed_dir / "artifact_validation_report.json").exists()


def test_validate_processed_artifacts_fails_on_missing_columns(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _build_valid_processed_artifacts(processed_dir)
    broken = pd.read_csv(processed_dir / "recommendations.csv").drop(columns=["recommended_action"])
    broken.to_csv(processed_dir / "recommendations.csv", index=False)

    with pytest.raises(DataQualityError, match="recommended_action"):
        validate_processed_artifacts(processed_dir)


def test_validate_processed_artifacts_fails_on_missing_operational_key(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _build_valid_processed_artifacts(processed_dir)
    broken_report = json.loads((processed_dir / "quality_report.json").read_text(encoding="utf-8"))
    broken_report.pop("total_datasets")
    _write_json(processed_dir / "quality_report.json", broken_report)

    with pytest.raises(DataQualityError, match="total_datasets"):
        validate_processed_artifacts(processed_dir)
