import json
from pathlib import Path

import pandas as pd

from contracts.data_contract import validate_gold_table
from main import run_pipeline
from src.config import PipelineConfig


def test_pipeline_generates_expected_contract_outputs(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    cfg = PipelineConfig(
        project_root=tmp_path,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        bronze_dir=data_dir / "bronze",
        silver_dir=data_dir / "silver",
        gold_dir=data_dir / "gold",
        processed_dir=data_dir / "processed",
        warehouse_dir=data_dir / "warehouse",
        warehouse_db_path=data_dir / "warehouse" / "revenue_intelligence.db",
        semantic_metrics_path=tmp_path / "metrics" / "semantic_metrics.json",
        alerts_output_path=data_dir / "processed" / "alerts_report.json",
        approvals_output_path=data_dir / "processed" / "approved_actions.csv",
        runs_dir=data_dir / "runs",
        manifests_dir=data_dir / "manifests",
        snapshots_dir=data_dir / "snapshots",
        data_dictionary_path=data_dir / "processed" / "data_dictionary.json",
        env_name="test",
        warehouse_target="sqlite",
        warehouse_url=None,
        seed=42,
        log_level="WARNING",
        freshness_max_age_hours=48,
        snapshot_retention_runs=10,
        snapshot_retention_days=30,
        failure_retention_days=14,
    )

    cfg.semantic_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.semantic_metrics_path.write_text(
        '{"version":"1.0","metrics":[{"name":"revenue_proxy","expression":"sum(monetary)"}]}',
        encoding="utf-8",
    )

    run_pipeline(cfg)

    processed = cfg.processed_dir
    expected_files = [
        "scored_customers.csv",
        "recommendations.csv",
        "cohort_retention.csv",
        "unit_economics.csv",
        "kpi_snapshot.json",
        "metrics_report.json",
        "runtime_metrics.json",
        "run_events.jsonl",
        "monitoring_report.json",
        "monitoring_baseline.json",
        "semantic_metrics_catalog.json",
        "alerts_report.json",
        "executive_report.json",
        "executive_summary.json",
        "business_outcomes.json",
        "insight_draft.json",
        "reliability_report.json",
        "data_dictionary.json",
        "freshness_report.json",
        "raw_input_metadata.json",
        "top_10_actions.csv",
        "quality_report.json",
        "artifact_validation_report.json",
        "pipeline_manifest.json",
        "dim_customers.csv",
        "dim_date.csv",
        "dim_channel.csv",
        "fact_orders.csv",
        "executive_scorecard.csv",
        "customer_segment_health.csv",
        "payment_scorecard.csv",
        "retention_scorecard.csv",
    ]
    for file_name in expected_files:
        assert (processed / file_name).exists(), f"Missing output file: {file_name}"

    model_registry_files = [
        "registry/churn/model_v1/model.pkl",
        "registry/churn/model_v1/model_metadata.json",
        "registry/churn/latest.json",
        "registry/next_purchase_30d/model_v1/model.pkl",
        "registry/next_purchase_30d/model_v1/model_metadata.json",
        "registry/next_purchase_30d/latest.json",
    ]
    for registry_file in model_registry_files:
        assert (
            processed / registry_file
        ).exists(), f"Missing model registry artifact: {registry_file}"
    assert cfg.warehouse_db_path.exists()

    dim_customers = pd.read_csv(processed / "dim_customers.csv")
    dim_date = pd.read_csv(processed / "dim_date.csv")
    dim_channel = pd.read_csv(processed / "dim_channel.csv")
    fact_orders = pd.read_csv(processed / "fact_orders.csv")
    top_10_actions = pd.read_csv(processed / "top_10_actions.csv")
    cohort_retention = pd.read_csv(processed / "cohort_retention.csv")
    unit_economics = pd.read_csv(processed / "unit_economics.csv")
    business_outcomes = pd.read_json(processed / "business_outcomes.json", typ="series")
    runtime_metrics = pd.read_json(processed / "runtime_metrics.json", typ="series")
    run_events = [
        json.loads(line)
        for line in (processed / "run_events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    validate_gold_table(dim_customers, "dim_customers.csv")
    validate_gold_table(dim_date, "dim_date.csv")
    validate_gold_table(dim_channel, "dim_channel.csv")
    validate_gold_table(fact_orders, "fact_orders.csv")
    assert {
        "priority_rank",
        "customer_id",
        "action",
        "expected_uplift",
        "action_cost",
        "net_impact",
        "roi_simulated",
    }.issubset(top_10_actions.columns)
    assert cohort_retention["retention_rate"].between(0, 1).all()
    assert top_10_actions["priority_rank"].tolist() == list(range(1, len(top_10_actions) + 1))
    observed_best_channel = unit_economics.sort_values("ltv_cac_ratio", ascending=False).iloc[0][
        "channel"
    ]
    expected_best_channel = max(
        business_outcomes["ltv_cac_by_channel"], key=lambda item: item["ltv_cac_ratio"]
    )["channel"]
    assert observed_best_channel == expected_best_channel
    assert runtime_metrics["stage_count"] > 0
    assert runtime_metrics["total_runtime_seconds"] >= 0
    assert len(run_events) > 0
    assert run_events[0]["run_id"] == runtime_metrics["run_id"]
