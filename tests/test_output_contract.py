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
        seed=42,
        log_level="WARNING",
    )

    run_pipeline(cfg)

    processed = cfg.processed_dir
    expected_files = [
        "scored_customers.csv",
        "recommendations.csv",
        "cohort_retention.csv",
        "unit_economics.csv",
        "metrics_report.json",
        "executive_report.json",
        "executive_summary.json",
        "business_outcomes.json",
        "top_10_actions.csv",
        "dim_customers.csv",
        "dim_date.csv",
        "dim_channel.csv",
        "fact_orders.csv",
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

    dim_customers = pd.read_csv(processed / "dim_customers.csv")
    dim_date = pd.read_csv(processed / "dim_date.csv")
    dim_channel = pd.read_csv(processed / "dim_channel.csv")
    fact_orders = pd.read_csv(processed / "fact_orders.csv")
    top_10_actions = pd.read_csv(processed / "top_10_actions.csv")
    cohort_retention = pd.read_csv(processed / "cohort_retention.csv")

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
