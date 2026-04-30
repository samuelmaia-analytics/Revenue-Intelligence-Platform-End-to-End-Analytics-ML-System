from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.alerting import build_alert_report, dispatch_alerts
from src.analytics import AnalyticsOutputs, build_analytics_outputs
from src.artifact_validation import validate_processed_artifacts
from src.config import PipelineConfig
from src.io_utils import atomic_write_csv
from src.monitoring import build_monitoring_report
from src.quality import (
    build_dataset_quality_report,
    enforce_quality_gate,
    validate_required_columns,
    write_quality_report,
)
from src.reporting import build_business_outcomes, build_executive_report, build_executive_summary
from src.transformation import SilverDatasets


@dataclass(frozen=True)
class SilverFrames:
    customers: pd.DataFrame
    orders: pd.DataFrame
    marketing: pd.DataFrame


@dataclass(frozen=True)
class ServingArtifacts:
    analytics_outputs: AnalyticsOutputs
    monitoring_payload: dict[str, object]
    alerts_payload: dict[str, object]


def load_silver_frames(silver_datasets: SilverDatasets) -> SilverFrames:
    return SilverFrames(
        customers=pd.read_csv(silver_datasets.customers_path, parse_dates=["signup_date"]),
        orders=pd.read_csv(silver_datasets.orders_path, parse_dates=["order_date"]),
        marketing=pd.read_csv(silver_datasets.marketing_path),
    )


def validate_silver_frames(frames: SilverFrames) -> None:
    validate_required_columns(
        frames.customers,
        {"customer_id", "signup_date", "channel", "segment"},
        "silver_customers",
    )
    validate_required_columns(
        frames.orders,
        {"order_id", "customer_id", "order_date", "order_value"},
        "silver_orders",
    )
    validate_required_columns(
        frames.marketing,
        {"channel", "marketing_spend"},
        "silver_marketing",
    )


def persist_backfill_results(
    silver_datasets: SilverDatasets,
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
) -> None:
    atomic_write_csv(silver_datasets.customers_path, customers_df)
    atomic_write_csv(silver_datasets.orders_path, orders_df)


def build_quality_payload(
    cfg: PipelineConfig,
    *,
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    marketing_df: pd.DataFrame,
) -> dict[str, object]:
    quality_reports = [
        build_dataset_quality_report(
            customers_df,
            "silver_customers",
            primary_key="customer_id",
        ),
        build_dataset_quality_report(
            orders_df,
            "silver_orders",
            primary_key="order_id",
            foreign_key="customer_id",
            valid_values=set(customers_df["customer_id"].tolist()),
        ),
        build_dataset_quality_report(
            marketing_df,
            "silver_marketing",
            primary_key="channel",
        ),
    ]
    enforce_quality_gate(
        quality_reports,
        max_total_null_fraction=cfg.quality_max_null_fraction,
    )
    return write_quality_report(
        quality_reports,
        cfg.processed_dir / "quality_report.json",
    )


def build_warehouse_frames(processed_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "dim_customers": pd.read_csv(processed_dir / "dim_customers.csv"),
        "dim_date": pd.read_csv(processed_dir / "dim_date.csv"),
        "dim_channel": pd.read_csv(processed_dir / "dim_channel.csv"),
        "fact_orders": pd.read_csv(processed_dir / "fact_orders.csv"),
        "customer_features": pd.read_csv(processed_dir / "customer_features.csv"),
        "scored_customers": pd.read_csv(processed_dir / "scored_customers.csv"),
        "recommendations": pd.read_csv(processed_dir / "recommendations.csv"),
        "unit_economics": pd.read_csv(processed_dir / "unit_economics.csv"),
        "top_10_actions": pd.read_csv(processed_dir / "top_10_actions.csv"),
    }


def build_serving_artifacts(
    cfg: PipelineConfig,
    *,
    scored_df: pd.DataFrame,
    silver_datasets: SilverDatasets,
    churn_results: dict[str, object],
    next_purchase_results: dict[str, object],
    quality_payload: dict[str, object],
) -> ServingArtifacts:
    analytics_outputs = build_analytics_outputs(
        scored_df=scored_df,
        silver_customers_path=silver_datasets.customers_path,
        silver_orders_path=silver_datasets.orders_path,
        silver_marketing_path=silver_datasets.marketing_path,
        processed_dir=cfg.processed_dir,
    )

    monitoring_payload = build_monitoring_report(
        scored_df=scored_df,
        labeled_df=scored_df,
        output_path=cfg.processed_dir / "monitoring_report.json",
        baseline_path=cfg.processed_dir / "monitoring_baseline.json",
    )
    alerts_payload = build_alert_report(
        monitoring_report=monitoring_payload,
        quality_report=quality_payload,
        output_path=cfg.alerts_output_path,
        thresholds={
            "drift_feature_count_warn": cfg.alert_drift_feature_count_warn,
            "duplicate_rows_warn": cfg.alert_duplicate_rows_warn,
            "null_count_warn": cfg.alert_null_count_warn,
            "brier_score_warn": cfg.alert_brier_score_warn,
        },
    )
    dispatch_alerts(alerts_payload, webhook_url=cfg.alert_webhook_url)

    recommendations_df = analytics_outputs.recommendations
    unit_df = analytics_outputs.unit_economics
    kpi_snapshot = analytics_outputs.kpi_snapshot

    build_executive_report(
        recommendations_df=recommendations_df,
        churn_results=churn_results,
        next_purchase_results=next_purchase_results,
        kpi_snapshot=kpi_snapshot,
        output_path=cfg.processed_dir / "executive_report.json",
    )
    build_executive_summary(
        recommendations_df=recommendations_df,
        scored_df=scored_df,
        unit_economics_df=unit_df,
        kpi_snapshot=kpi_snapshot,
        output_path=cfg.processed_dir / "executive_summary.json",
    )
    build_business_outcomes(
        recommendations_df=recommendations_df,
        unit_economics_df=unit_df,
        outcomes_path=cfg.processed_dir / "business_outcomes.json",
        top_actions_path=cfg.processed_dir / "top_10_actions.csv",
    )
    validate_processed_artifacts(
        cfg.processed_dir,
        output_path=cfg.processed_dir / "artifact_validation_report.json",
    )

    return ServingArtifacts(
        analytics_outputs=analytics_outputs,
        monitoring_payload=monitoring_payload,
        alerts_payload=alerts_payload,
    )
