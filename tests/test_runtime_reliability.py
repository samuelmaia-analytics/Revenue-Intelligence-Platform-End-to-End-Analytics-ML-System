from __future__ import annotations

import json
import os
import sqlite3
import sys
from argparse import ArgumentTypeError
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.exceptions import PipelineStageError
from src.governance import build_data_dictionary
from src.ingestion import save_raw_datasets
from src.orchestration import (
    _apply_backfill_window,
    _apply_retention,
    _run_stage_with_retry,
    run_pipeline,
)
from src.pipeline import _parse_positive_int
from src.pipeline import main as pipeline_main


def _build_config(tmp_path: Path, *, semantic_metrics_exists: bool = True) -> PipelineConfig:
    data_dir = tmp_path / "data"
    metrics_path = tmp_path / "metrics" / "semantic_metrics.json"
    if semantic_metrics_exists:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "metrics": [{"name": "revenue_proxy", "expression": "sum(monetary)"}],
                }
            ),
            encoding="utf-8",
        )

    return PipelineConfig(
        project_root=tmp_path,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        bronze_dir=data_dir / "bronze",
        silver_dir=data_dir / "silver",
        gold_dir=data_dir / "gold",
        processed_dir=data_dir / "processed",
        warehouse_dir=data_dir / "warehouse",
        warehouse_db_path=data_dir / "warehouse" / "revenue_intelligence.db",
        semantic_metrics_path=metrics_path,
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
        snapshot_retention_runs=2,
        snapshot_retention_days=30,
        failure_retention_days=14,
    )


def test_pipeline_manifest_and_snapshot_are_created(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    manifest = run_pipeline(cfg)

    assert manifest["status"] == "success"
    assert manifest["run_id"]
    assert manifest["input_fingerprint"]
    assert (cfg.processed_dir / "pipeline_manifest.json").exists()
    assert len(list(cfg.snapshots_dir.iterdir())) == 1
    snapshot_dir = next(cfg.snapshots_dir.iterdir())
    assert (snapshot_dir / "processed" / "quality_report.json").exists()
    assert (snapshot_dir / "processed" / "kpi_snapshot.json").exists()
    assert (snapshot_dir / "processed" / "raw_input_metadata.json").exists()
    assert (snapshot_dir / cfg.warehouse_db_path.name).exists()


def test_pipeline_generates_raw_input_metadata_and_source_aware_freshness(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    run_pipeline(cfg)

    raw_metadata = json.loads(
        (cfg.processed_dir / "raw_input_metadata.json").read_text(encoding="utf-8")
    )
    freshness = json.loads(
        (cfg.processed_dir / "freshness_report.json").read_text(encoding="utf-8")
    )

    assert raw_metadata["dataset_count"] == 3
    assert {item["dataset_name"] for item in raw_metadata["datasets"]} == {
        "customers",
        "orders",
        "marketing_spend",
    }
    assert all(item["row_count"] > 0 for item in raw_metadata["datasets"])
    assert all("source_updated_at_utc" in item for item in raw_metadata["datasets"])
    assert all("fingerprint" in item for item in freshness["checks"])
    assert all("source_updated_at_utc" in item for item in freshness["checks"])


def test_pipeline_persists_queryable_sqlite_warehouse(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    run_pipeline(cfg)

    with sqlite3.connect(cfg.warehouse_db_path) as connection:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
            connection,
        )
        joined = pd.read_sql_query(
            """
            SELECT COUNT(*) AS joined_rows
            FROM fact_orders fo
            INNER JOIN dim_customers dc ON fo.customer_id = dc.customer_id
            INNER JOIN recommendations r ON fo.customer_id = r.customer_id
            """,
            connection,
        )
        counts = pd.read_sql_query(
            """
            SELECT
                (SELECT COUNT(*) FROM fact_orders) AS fact_orders_count,
                (SELECT COUNT(*) FROM customer_features) AS customer_features_count,
                (SELECT COUNT(*) FROM recommendations) AS recommendations_count
            """,
            connection,
        )

    assert {"customer_features", "dim_customers", "fact_orders", "recommendations"}.issubset(
        set(tables["name"])
    )
    assert int(counts.loc[0, "fact_orders_count"]) > 0
    assert int(counts.loc[0, "customer_features_count"]) > 0
    assert int(counts.loc[0, "recommendations_count"]) > 0
    assert int(joined.loc[0, "joined_rows"]) > 0


def test_warehouse_dimensions_remain_consistent_with_facts(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    run_pipeline(cfg)

    with sqlite3.connect(cfg.warehouse_db_path) as connection:
        referential = pd.read_sql_query(
            """
            SELECT
                SUM(CASE WHEN dc.customer_id IS NULL THEN 1 ELSE 0 END) AS missing_customers,
                SUM(CASE WHEN dd.date_key IS NULL THEN 1 ELSE 0 END) AS missing_dates,
                SUM(CASE WHEN ch.channel_key IS NULL THEN 1 ELSE 0 END) AS missing_channels
            FROM fact_orders fo
            LEFT JOIN dim_customers dc ON fo.customer_id = dc.customer_id
            LEFT JOIN dim_date dd ON fo.date_key = dd.date_key
            LEFT JOIN dim_channel ch ON fo.channel_key = ch.channel_key
            """,
            connection,
        )
        aggregates = pd.read_sql_query(
            """
            SELECT
                ch.channel,
                COUNT(*) AS order_count,
                ROUND(SUM(fo.order_amount), 2) AS revenue
            FROM fact_orders fo
            INNER JOIN dim_channel ch ON fo.channel_key = ch.channel_key
            GROUP BY ch.channel
            ORDER BY revenue DESC, ch.channel ASC
            """,
            connection,
        )

    assert int(referential.loc[0, "missing_customers"]) == 0
    assert int(referential.loc[0, "missing_dates"]) == 0
    assert int(referential.loc[0, "missing_channels"]) == 0
    assert not aggregates.empty
    assert (aggregates["order_count"] > 0).all()
    assert (aggregates["revenue"] > 0).all()


def test_pipeline_is_idempotent_for_curated_outputs(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    run_pipeline(cfg)
    first_recommendations = pd.read_csv(cfg.processed_dir / "recommendations.csv")
    first_features = pd.read_csv(cfg.processed_dir / "customer_features.csv")

    run_pipeline(cfg)
    second_recommendations = pd.read_csv(cfg.processed_dir / "recommendations.csv")
    second_features = pd.read_csv(cfg.processed_dir / "customer_features.csv")

    pd.testing.assert_frame_equal(first_recommendations, second_recommendations)
    pd.testing.assert_frame_equal(first_features, second_features)


def test_pipeline_reuses_registered_models_when_training_data_is_unchanged(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    run_pipeline(cfg)
    first_metrics = json.loads((cfg.processed_dir / "metrics_report.json").read_text(encoding="utf-8"))

    run_pipeline(cfg)
    second_metrics = json.loads(
        (cfg.processed_dir / "metrics_report.json").read_text(encoding="utf-8")
    )

    assert second_metrics["churn"]["split_strategy"].endswith("_cached")
    assert second_metrics["next_purchase_30d"]["split_strategy"].endswith("_cached")
    assert first_metrics["churn"]["temporal_test_roc_auc"] == second_metrics["churn"]["temporal_test_roc_auc"]
    assert first_metrics["next_purchase_30d"]["temporal_test_roc_auc"] == second_metrics["next_purchase_30d"]["temporal_test_roc_auc"]


def test_pipeline_manifest_captures_runtime_evidence(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)

    manifest = run_pipeline(cfg)
    artifact_validation = json.loads(
        (cfg.processed_dir / "artifact_validation_report.json").read_text(encoding="utf-8")
    )

    assert manifest["reliability_policy"]["retry_attempts"] == cfg.retry_attempts
    assert manifest["quality_snapshot"]["dataset_count"] >= 1
    assert "artifact_validation_report.json" in manifest["outputs"]
    assert "freshness_report.json" in manifest["outputs"]
    assert "runtime_metrics.json" in manifest["outputs"]
    assert manifest["backfill_window"] == {"start_date": None, "end_date": None}
    assert manifest["observability"]["log_format"] == cfg.log_format
    assert manifest["observability"]["event_count"] > 0
    assert (cfg.processed_dir / "run_events.jsonl").exists()
    assert artifact_validation["status"] == "ok"
    assert any(
        check["artifact"] == "quality_report.json" for check in artifact_validation["checks"]
    )
    assert any(
        check["artifact"] == "raw_input_metadata.json" for check in artifact_validation["checks"]
    )


def test_failure_manifest_is_written(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path, semantic_metrics_exists=False)

    with pytest.raises(PipelineStageError):
        run_pipeline(cfg)

    failure_manifests = list(cfg.manifests_dir.glob("*.failure.json"))
    assert len(failure_manifests) == 1
    payload = json.loads(failure_manifests[0].read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["error_type"]
    assert payload["run_id"]
    assert payload["observability"]["event_count"] > 0
    assert Path(payload["observability"]["run_events_path"]).exists()


def test_kaggle_csv_parsing_creates_curated_raw_tables(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    source = raw_dir / "E-commerce Customer Behavior - Sheet1.csv"
    source.write_text(
        "\n".join(
            [
                "Customer ID,Gender,Age,City,Membership Type,Total Spend,Items Purchased,Average Rating,Discount Applied,Days Since Last Purchase,Satisfaction Level",
                "1,Male,31,Sao Paulo,Gold,900,3,4.8,Yes,14,High",
                "2,Female,28,Recife,Silver,450,2,4.3,No,35,Medium",
            ]
        ),
        encoding="utf-8",
    )

    cfg = _build_config(tmp_path)
    run_pipeline(cfg)

    customers = pd.read_csv(cfg.raw_dir / "customers.csv")
    orders = pd.read_csv(cfg.raw_dir / "orders.csv")
    assert {"customer_id", "channel", "segment", "signup_date"}.issubset(customers.columns)
    assert {"order_id", "customer_id", "order_value"}.issubset(orders.columns)


def test_olist_dataset_parsing_creates_curated_raw_tables(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "olist_customers_dataset.csv").write_text(
        "\n".join(
            [
                "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state",
                "c1,u1,12345,sao paulo,SP",
                "c2,u2,54321,recife,PE",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_orders_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date",
                "o1,c1,delivered,2018-01-10 10:00:00,2018-01-10 10:05:00,2018-01-11 10:00:00,2018-01-15 10:00:00,2018-01-20 00:00:00",
                "o2,c1,delivered,2018-03-12 11:00:00,2018-03-12 11:05:00,2018-03-13 11:00:00,2018-03-17 11:00:00,2018-03-24 00:00:00",
                "o3,c2,delivered,2018-02-05 09:00:00,2018-02-05 09:05:00,2018-02-06 09:00:00,2018-02-10 09:00:00,2018-02-18 00:00:00",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_order_items_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value",
                "o1,1,p1,s1,2018-01-09 00:00:00,100,10",
                "o2,1,p2,s1,2018-03-11 00:00:00,120,12",
                "o3,1,p3,s2,2018-02-04 00:00:00,80,8",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_order_payments_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,payment_sequential,payment_type,payment_installments,payment_value",
                "o1,1,credit_card,1,110",
                "o2,1,voucher,1,132",
                "o3,1,boleto,1,88",
            ]
        ),
        encoding="utf-8",
    )

    customers_path, orders_path, marketing_path = save_raw_datasets(raw_dir)

    customers = pd.read_csv(customers_path)
    orders = pd.read_csv(orders_path)
    marketing = pd.read_csv(marketing_path)
    assert {"customer_id", "channel", "segment", "signup_date", "customer_unique_id"}.issubset(
        customers.columns
    )
    assert {"order_id", "customer_id", "order_value", "payment_type"}.issubset(orders.columns)
    assert set(marketing["channel"]).issubset({"Credit Card", "Boleto", "Voucher", "Debit Card", "Other"})


def test_olist_normalization_is_reused_when_sources_do_not_change(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "olist_customers_dataset.csv").write_text(
        "\n".join(
            [
                "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state",
                "c1,u1,12345,sao paulo,SP",
                "c2,u2,54321,recife,PE",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_orders_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date",
                "o1,c1,delivered,2018-01-10 10:00:00,2018-01-10 10:05:00,2018-01-11 10:00:00,2018-01-15 10:00:00,2018-01-20 00:00:00",
                "o2,c1,delivered,2018-03-12 11:00:00,2018-03-12 11:05:00,2018-03-13 11:00:00,2018-03-17 11:00:00,2018-03-24 00:00:00",
                "o3,c2,delivered,2018-02-05 09:00:00,2018-02-05 09:05:00,2018-02-06 09:00:00,2018-02-10 09:00:00,2018-02-18 00:00:00",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_order_items_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value",
                "o1,1,p1,s1,2018-01-09 00:00:00,100,10",
                "o2,1,p2,s1,2018-03-11 00:00:00,120,12",
                "o3,1,p3,s2,2018-02-04 00:00:00,80,8",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "olist_order_payments_dataset.csv").write_text(
        "\n".join(
            [
                "order_id,payment_sequential,payment_type,payment_installments,payment_value",
                "o1,1,credit_card,1,110",
                "o2,1,voucher,1,132",
                "o3,1,boleto,1,88",
            ]
        ),
        encoding="utf-8",
    )

    customers_path, _, _ = save_raw_datasets(raw_dir)
    first_mtime = customers_path.stat().st_mtime_ns
    customers_path_second, _, _ = save_raw_datasets(raw_dir)
    second_mtime = customers_path_second.stat().st_mtime_ns

    assert first_mtime == second_mtime


def test_data_dictionary_generation_from_contracts(tmp_path: Path) -> None:
    output_path = tmp_path / "dictionary.json"

    dictionary = build_data_dictionary(output_path)

    assert output_path.exists()
    assert dictionary["tables"]
    first_table = dictionary["tables"][0]
    assert {"table_name", "contract_model", "columns"} == set(first_table)


def test_retention_enforces_max_runs_and_age(tmp_path: Path) -> None:
    cfg = _build_config(tmp_path)
    cfg.ensure_directories()
    old_snapshot = cfg.snapshots_dir / "20240101T000000Z-old"
    mid_snapshot = cfg.snapshots_dir / "20240102T000000Z-mid"
    new_snapshot = cfg.snapshots_dir / "20240103T000000Z-new"
    for snapshot in [old_snapshot, mid_snapshot, new_snapshot]:
        snapshot.mkdir(parents=True, exist_ok=True)

    old_failure = cfg.manifests_dir / "old.failure.json"
    old_failure.write_text("{}", encoding="utf-8")

    old_ts = 1_700_000_000
    os.utime(old_snapshot, (old_ts, old_ts))
    os.utime(mid_snapshot, (old_ts + 100, old_ts + 100))
    os.utime(new_snapshot, (old_ts + 200, old_ts + 200))
    os.utime(old_failure, (old_ts, old_ts))

    retained_cfg = replace(
        cfg,
        snapshot_retention_days=1_000,
        snapshot_retention_runs=2,
        failure_retention_days=1,
    )

    _apply_retention(retained_cfg)

    remaining_snapshots = sorted(path.name for path in retained_cfg.snapshots_dir.iterdir())
    assert remaining_snapshots == ["20240102T000000Z-mid", "20240103T000000Z-new"]
    assert not old_failure.exists()


def test_cli_artifacts_command_generates_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_path = tmp_path / "dictionary.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["pipeline", "artifacts", "--data-dictionary-path", str(output_path)],
    )

    pipeline_main()

    assert output_path.exists()


def test_pipeline_config_reads_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "RIP_ENV=ci",
                "RIP_DATA_DIR=./custom-data",
                "RIP_SEED=123",
                "RIP_LOG_LEVEL=debug",
                "RIP_LOG_FORMAT=json",
                "RIP_FRESHNESS_MAX_AGE_HOURS=12",
                "RIP_RETRY_ATTEMPTS=3",
                "RIP_RETRY_BACKOFF_SECONDS=0",
                "RIP_QUALITY_MAX_NULL_FRACTION=0.15",
                "RIP_BACKFILL_START_DATE=2025-01-01",
                "RIP_BACKFILL_END_DATE=2025-03-31",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("RIP_ENV", raising=False)
    monkeypatch.delenv("RIP_DATA_DIR", raising=False)
    monkeypatch.delenv("RIP_SEED", raising=False)
    monkeypatch.delenv("RIP_LOG_LEVEL", raising=False)
    monkeypatch.delenv("RIP_LOG_FORMAT", raising=False)
    monkeypatch.delenv("RIP_FRESHNESS_MAX_AGE_HOURS", raising=False)
    monkeypatch.delenv("RIP_RETRY_ATTEMPTS", raising=False)
    monkeypatch.delenv("RIP_RETRY_BACKOFF_SECONDS", raising=False)
    monkeypatch.delenv("RIP_QUALITY_MAX_NULL_FRACTION", raising=False)
    monkeypatch.delenv("RIP_BACKFILL_START_DATE", raising=False)
    monkeypatch.delenv("RIP_BACKFILL_END_DATE", raising=False)

    cfg = PipelineConfig.from_env(tmp_path)

    assert cfg.env_name == "ci"
    assert cfg.data_dir == (tmp_path / "custom-data").resolve()
    assert cfg.seed == 123
    assert cfg.log_level == "DEBUG"
    assert cfg.log_format == "json"
    assert cfg.freshness_max_age_hours == 12
    assert cfg.retry_attempts == 3
    assert cfg.retry_backoff_seconds == 0
    assert cfg.quality_max_null_fraction == 0.15
    assert str(cfg.backfill_start_date) == "2025-01-01"
    assert str(cfg.backfill_end_date) == "2025-03-31"


def test_stage_runner_retries_transient_failures() -> None:
    attempts = {"count": 0}

    def flaky_stage() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary issue")
        return "ok"

    result, elapsed = _run_stage_with_retry(
        "test.stage",
        flaky_stage,
        attempts=3,
        backoff_seconds=0,
    )

    assert result == "ok"
    assert attempts["count"] == 3
    assert elapsed >= 0


def test_cli_positive_int_parser_rejects_invalid_retry_attempts() -> None:
    with pytest.raises(ArgumentTypeError):
        _parse_positive_int("0")

    with pytest.raises(ArgumentTypeError):
        _parse_positive_int("-2")

    assert _parse_positive_int("3") == 3


def test_backfill_window_filters_orders_and_respects_customer_cutoff() -> None:
    customers = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "signup_date": pd.to_datetime(["2024-12-01", "2025-02-10", "2025-05-01"]),
            "channel": ["Organic", "Paid Search", "Referral"],
            "segment": ["SMB", "SMB", "Enterprise"],
        }
    )
    orders = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4"],
            "customer_id": [1, 2, 2, 3],
            "order_date": pd.to_datetime(["2024-12-15", "2025-01-20", "2025-04-15", "2025-05-10"]),
            "order_value": [100, 200, 150, 900],
        }
    )

    filtered_customers, filtered_orders = _apply_backfill_window(
        customers,
        orders,
        start_date=pd.Timestamp("2025-01-01").date(),
        end_date=pd.Timestamp("2025-04-30").date(),
    )

    assert filtered_customers["customer_id"].tolist() == [1, 2]
    assert filtered_orders["order_id"].tolist() == ["o2", "o3"]
