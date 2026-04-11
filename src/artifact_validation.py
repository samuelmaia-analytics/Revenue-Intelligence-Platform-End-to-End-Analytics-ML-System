from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.exceptions import DataQualityError
from src.io_utils import atomic_write_json

CSV_ARTIFACT_SPECS: dict[str, set[str]] = {
    "customer_features.csv": {
        "customer_id",
        "segment",
        "channel",
        "recency_days",
        "frequency",
        "monetary",
        "avg_order_value",
        "tenure_days",
        "arpu",
        "is_churned",
        "next_purchase_30d",
    },
    "recommendations.csv": {
        "customer_id",
        "channel",
        "segment",
        "ltv",
        "cac",
        "ltv_cac_ratio",
        "churn_probability",
        "next_purchase_probability",
        "strategic_score",
        "recommended_action",
    },
    "unit_economics.csv": {
        "channel",
        "marketing_spend",
        "customers_acquired",
        "cac",
        "avg_arpu",
        "ltv_cac_ratio",
        "contribution_margin",
        "payback_period_months",
    },
    "top_10_actions.csv": {
        "priority_rank",
        "customer_id",
        "channel",
        "segment",
        "action",
        "strategic_priority_score",
        "expected_uplift",
        "action_cost",
        "net_impact",
        "roi_simulated",
    },
    "cac_by_channel.csv": {
        "channel",
        "marketing_spend",
        "customers_acquired",
        "cac",
    },
    "ltv.csv": {
        "customer_id",
        "channel",
        "segment",
        "ltv",
        "churn_probability",
        "next_purchase_probability",
    },
    "rfm_segments.csv": {
        "customer_id",
        "channel",
        "recency",
        "frequency",
        "monetary",
        "r_score",
        "f_score",
        "m_score",
        "rfm_total",
        "segment",
    },
    "cohort_retention.csv": {
        "cohort_month",
        "cohort_index",
        "active_customers",
        "cohort_size",
        "retention_rate",
    },
    "customer_analytics.csv": {
        "customer_id",
        "channel",
        "segment",
        "recency_days",
        "frequency",
        "monetary",
        "ltv",
        "churn_probability",
        "next_purchase_probability",
        "recommended_action",
    },
    "payment_analytics.csv": {
        "channel",
        "total_orders",
        "total_revenue",
        "avg_ticket",
        "revenue_share_pct",
    },
    "geographic_analytics.csv": {
        "state",
        "total_orders",
        "unique_customers",
        "total_revenue",
        "revenue_share_pct",
    },
    "logistics_analytics.csv": {
        "order_month",
        "total_orders",
        "delivered_orders",
        "canceled_orders",
        "avg_delivery_days",
        "late_delivery_rate",
    },
    "executive_summary_layer.csv": {
        "order_month",
        "total_revenue",
        "total_orders",
        "unique_customers",
        "avg_ticket",
    },
    "executive_scorecard.csv": {
        "snapshot_date",
        "total_revenue",
        "total_orders",
        "average_ticket",
        "recurring_customer_rate",
        "late_delivery_rate",
        "m1_retention_rate",
    },
    "customer_segment_health.csv": {
        "recommended_action",
        "rfm_segment",
        "churn_risk_band",
        "customers",
        "revenue_proxy",
        "avg_ltv",
        "avg_churn_probability",
    },
    "payment_scorecard.csv": {
        "channel",
        "total_orders",
        "total_revenue",
        "avg_ticket",
        "revenue_share_pct",
        "on_time_delivery_rate",
    },
    "retention_scorecard.csv": {
        "cohort_month",
        "cohort_index",
        "active_customers",
        "cohort_size",
        "retention_rate",
    },
}

JSON_ARTIFACT_SPECS: dict[str, tuple[str, ...]] = {
    "quality_report.json": (
        "datasets",
        "total_datasets",
    ),
    "quality_business_rules.json": (
        "checks",
        "status",
    ),
    "freshness_report.json": (
        "evaluated_at_utc",
        "max_age_hours",
        "status",
        "checks",
    ),
    "raw_input_metadata.json": (
        "generated_at_utc",
        "dataset_count",
        "datasets",
    ),
    "kpi_snapshot.json": (
        "revenue_proxy",
        "avg_arpu",
        "avg_ltv",
        "avg_cac",
        "avg_ltv_cac_ratio",
        "portfolio_size",
        "best_channel_efficiency.channel",
    ),
    "metrics_report.json": (
        "churn.model_name",
        "churn.cv_roc_auc_mean",
        "churn.temporal_test_roc_auc",
        "next_purchase_30d.model_name",
        "next_purchase_30d.cv_roc_auc_mean",
        "next_purchase_30d.temporal_test_roc_auc",
    ),
    "executive_report.json": (
        "data_refresh_utc",
        "base_size.customers_in_scope",
        "base_size.rows_in_recommendation_table",
        "top_kpis.avg_ltv",
        "business_context.revenue_proxy",
        "model_performance.churn",
        "model_performance.next_purchase_30d",
        "recommendations_top_20",
    ),
    "executive_summary.json": (
        "data_refresh_utc",
        "kpis.total_revenue_proxy",
        "kpis.avg_arpu",
        "ltv_cac_by_channel",
        "top_churn_risk_customers",
        "top_20_recommended_actions",
    ),
    "business_outcomes.json": (
        "data_refresh_utc",
        "kpis.avg_ltv_cac_ratio",
        "kpis.simulated_net_impact_top10",
        "simulation_assumptions",
        "simulation_summary_top10.delta_revenue_90d",
        "top_10_actions",
    ),
    "monitoring_report.json": (
        "drift_status",
        "numeric_summary",
        "feature_drift",
        "calibration.churn",
        "calibration.next_purchase_30d",
    ),
    "alerts_report.json": (
        "generated_at_utc",
        "thresholds",
        "alert_count",
        "status",
        "alerts",
    ),
    "insight_draft.json": (
        "generated_at_utc",
        "run_id",
        "mode_requested",
        "mode_applied",
        "headline",
        "summary",
        "kpi_highlights",
        "anomalies",
        "recommended_actions",
        "evidence.revenue_proxy",
    ),
    "runtime_metrics.json": (
        "run_id",
        "environment",
        "log_format",
        "stage_count",
        "stage_timings_seconds",
        "total_runtime_seconds",
        "event_count",
        "output_count",
    ),
    "semantic_metrics_catalog.json": ("metrics",),
    "executive_kpis.json": (
        "total_revenue",
        "total_orders",
        "average_ticket",
        "unique_customers",
        "avg_review_score",
    ),
}
JSONL_ARTIFACT_SPECS: dict[str, tuple[str, ...]] = {
    "run_events.jsonl": (
        "timestamp",
        "event_type",
        "run_id",
    ),
}


def _resolve_nested_key(payload: dict[str, object], dotted_key: str) -> object:
    current: object = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise DataQualityError(f"Missing required key path: {dotted_key}")
        current = current[part]
    return current


def _validate_csv_artifact(
    processed_dir: Path, file_name: str, required_columns: set[str]
) -> dict[str, object]:
    path = processed_dir / file_name
    if not path.exists():
        raise DataQualityError(f"Missing processed artifact: {file_name}")
    frame = pd.read_csv(path, nrows=5)
    missing_columns = sorted(required_columns.difference(frame.columns))
    if missing_columns:
        raise DataQualityError(f"{file_name} missing required columns: {missing_columns}")
    return {
        "artifact": file_name,
        "type": "csv",
        "required_columns": sorted(required_columns),
        "observed_columns": sorted(frame.columns.tolist()),
    }


def _validate_json_artifact(
    processed_dir: Path, file_name: str, required_keys: tuple[str, ...]
) -> dict[str, object]:
    path = processed_dir / file_name
    if not path.exists():
        raise DataQualityError(f"Missing processed artifact: {file_name}")
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    missing_keys: list[str] = []
    for dotted_key in required_keys:
        try:
            _resolve_nested_key(payload, dotted_key)
        except DataQualityError:
            missing_keys.append(dotted_key)
    if missing_keys:
        raise DataQualityError(f"{file_name} missing required key paths: {missing_keys}")
    return {
        "artifact": file_name,
        "type": "json",
        "required_keys": list(required_keys),
    }


def _validate_jsonl_artifact(
    processed_dir: Path, file_name: str, required_keys: tuple[str, ...]
) -> dict[str, object]:
    path = processed_dir / file_name
    if not path.exists():
        raise DataQualityError(f"Missing processed artifact: {file_name}")
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise DataQualityError(f"{file_name} must contain at least one event line")

    payload = json.loads(lines[0])
    missing_keys: list[str] = []
    for dotted_key in required_keys:
        try:
            _resolve_nested_key(payload, dotted_key)
        except DataQualityError:
            missing_keys.append(dotted_key)
    if missing_keys:
        raise DataQualityError(f"{file_name} missing required key paths: {missing_keys}")
    return {
        "artifact": file_name,
        "type": "jsonl",
        "required_keys": list(required_keys),
        "line_count": len(lines),
    }


def validate_processed_artifacts(
    processed_dir: Path, output_path: Path | None = None
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for file_name, required_columns in CSV_ARTIFACT_SPECS.items():
        checks.append(_validate_csv_artifact(processed_dir, file_name, required_columns))
    for file_name, required_keys in JSON_ARTIFACT_SPECS.items():
        checks.append(_validate_json_artifact(processed_dir, file_name, required_keys))
    for file_name, required_keys in JSONL_ARTIFACT_SPECS.items():
        checks.append(_validate_jsonl_artifact(processed_dir, file_name, required_keys))

    payload = {
        "validated_at_utc": datetime.now(UTC).isoformat(),
        "processed_dir": str(processed_dir),
        "status": "ok",
        "artifact_count": len(checks),
        "checks": checks,
    }
    if output_path is not None:
        atomic_write_json(output_path, payload)
    return payload
