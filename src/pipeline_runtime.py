from __future__ import annotations

import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypedDict

import pandas as pd

from contracts.processed_contract import PROCESSED_CONTRACT_VERSION
from src.config import PipelineConfig
from src.exceptions import PipelineStageError
from src.io_utils import atomic_copy_file, atomic_copy_tree, atomic_write_json
from src.runtime import RunContext, compute_file_fingerprint, is_older_than, utc_now_minus_days


class RawDatasetMetadata(TypedDict):
    dataset_name: str
    path: str
    row_count: int
    column_count: int
    columns: list[str]
    fingerprint: str
    source_updated_at_utc: str


class RawInputMetadata(TypedDict):
    generated_at_utc: str
    source_name: str
    dataset_count: int
    datasets: list[RawDatasetMetadata]


def build_raw_input_metadata(raw_paths: list[Path], *, source_name: str) -> RawInputMetadata:
    datasets: list[RawDatasetMetadata] = []
    for path in raw_paths:
        frame = pd.read_csv(path)
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
        datasets.append(
            {
                "dataset_name": path.stem,
                "path": str(path),
                "row_count": int(len(frame)),
                "column_count": int(len(frame.columns)),
                "columns": frame.columns.tolist(),
                "fingerprint": compute_file_fingerprint([path]),
                "source_updated_at_utc": modified_at,
            }
        )
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_name": source_name,
        "dataset_count": len(datasets),
        "datasets": datasets,
    }


def build_source_aware_freshness_snapshot(
    raw_metadata: RawInputMetadata,
    max_age_hours: int,
) -> dict[str, object]:
    evaluated_at = datetime.now(UTC)
    threshold_seconds = max_age_hours * 3600
    checks: list[dict[str, object]] = []
    for dataset in raw_metadata["datasets"]:
        source_updated_at = datetime.fromisoformat(dataset["source_updated_at_utc"])
        age_seconds = (evaluated_at - source_updated_at).total_seconds()
        checks.append(
            {
                "dataset_name": dataset["dataset_name"],
                "path": dataset["path"],
                "source_updated_at_utc": dataset["source_updated_at_utc"],
                "row_count": dataset["row_count"],
                "fingerprint": dataset["fingerprint"],
                "age_hours": round(age_seconds / 3600, 3),
                "status": "fresh" if age_seconds <= threshold_seconds else "stale",
            }
        )
    return {
        "evaluated_at_utc": evaluated_at.isoformat(),
        "max_age_hours": max_age_hours,
        "status": "ok" if all(item["status"] == "fresh" for item in checks) else "warning",
        "checks": checks,
    }


def apply_backfill_window(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    *,
    start_date: date | None,
    end_date: date | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered_customers = customers_df.copy()
    filtered_orders = orders_df.copy()

    if end_date is not None:
        end_ts = pd.Timestamp(end_date)
        filtered_customers = filtered_customers[filtered_customers["signup_date"] <= end_ts].copy()
        filtered_orders = filtered_orders[filtered_orders["order_date"] <= end_ts].copy()

    if start_date is not None:
        start_ts = pd.Timestamp(start_date)
        filtered_orders = filtered_orders[filtered_orders["order_date"] >= start_ts].copy()

    valid_customers = set(filtered_customers["customer_id"].tolist())
    filtered_orders = filtered_orders[filtered_orders["customer_id"].isin(valid_customers)].copy()

    if filtered_customers.empty:
        raise PipelineStageError(
            "Stage 'validation.backfill' failed: no customers remain in window."
        )
    if filtered_orders.empty:
        raise PipelineStageError("Stage 'validation.backfill' failed: no orders remain in window.")

    return filtered_customers, filtered_orders


def quality_snapshot(quality_payload: dict[str, object]) -> dict[str, object]:
    datasets = quality_payload["datasets"]
    assert isinstance(datasets, list)
    duplicates = sum(int(item["duplicate_rows"]) for item in datasets if isinstance(item, dict))
    referential = sum(int(item["referential_issues"]) for item in datasets if isinstance(item, dict))
    null_total = sum(
        int(value)
        for dataset in datasets
        if isinstance(dataset, dict)
        for value in dataset.get("null_counts", {}).values()
    )
    return {
        "dataset_count": quality_payload["total_datasets"],
        "duplicate_rows": duplicates,
        "referential_issues": referential,
        "null_count_total": null_total,
    }


def persist_run_snapshot(cfg: PipelineConfig, run_context: RunContext) -> None:
    atomic_copy_tree(cfg.processed_dir, run_context.snapshot_dir / "processed")
    atomic_copy_tree(cfg.gold_dir, run_context.snapshot_dir / "gold")
    atomic_copy_file(cfg.warehouse_db_path, run_context.snapshot_dir / cfg.warehouse_db_path.name)


def apply_retention(cfg: PipelineConfig) -> None:
    snapshots = [path for path in cfg.snapshots_dir.iterdir() if path.is_dir()]
    snapshots.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    for snapshot in snapshots[cfg.snapshot_retention_runs :]:
        shutil.rmtree(snapshot, ignore_errors=True)

    cutoff_snapshot = utc_now_minus_days(cfg.snapshot_retention_days)
    for snapshot in list(cfg.snapshots_dir.iterdir()):
        if snapshot.is_dir() and is_older_than(snapshot, cutoff_snapshot):
            shutil.rmtree(snapshot, ignore_errors=True)

    cutoff_failure = utc_now_minus_days(cfg.failure_retention_days)
    for manifest in cfg.manifests_dir.glob("*.failure.json"):
        if is_older_than(manifest, cutoff_failure):
            manifest.unlink(missing_ok=True)


def write_run_manifest(
    cfg: PipelineConfig,
    run_context: RunContext,
    stage_timings: dict[str, float],
    raw_input_metadata: RawInputMetadata,
    quality_payload: dict[str, object],
    kpi_snapshot: dict[str, object],
    freshness_snapshot: dict[str, object],
    outputs: list[str],
) -> dict[str, object]:
    manifest = {
        "pipeline_name": "revenue_intelligence_platform",
        "status": "success",
        "run_id": run_context.run_id,
        "started_at_utc": run_context.started_at_utc,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "environment": cfg.env_name,
        "seed": cfg.seed,
        "input_fingerprint": run_context.input_fingerprint,
        "data_dir": str(cfg.data_dir),
        "warehouse_target": cfg.warehouse_target,
        "warehouse_schema": cfg.warehouse_schema,
        "reliability_policy": {
            "retry_attempts": cfg.retry_attempts,
            "retry_backoff_seconds": cfg.retry_backoff_seconds,
            "quality_max_null_fraction": cfg.quality_max_null_fraction,
        },
        "backfill_window": {
            "start_date": cfg.backfill_start_date.isoformat() if cfg.backfill_start_date else None,
            "end_date": cfg.backfill_end_date.isoformat() if cfg.backfill_end_date else None,
        },
        "layers": {
            "raw": str(cfg.raw_dir),
            "bronze": str(cfg.bronze_dir),
            "silver": str(cfg.silver_dir),
            "gold": str(cfg.gold_dir),
            "processed": str(cfg.processed_dir),
            "warehouse": str(cfg.warehouse_db_path),
            "snapshot": str(run_context.snapshot_dir),
            "logs": str(run_context.log_path),
        },
        "stage_timings_seconds": {name: round(value, 3) for name, value in stage_timings.items()},
        "raw_input_metadata_path": str(cfg.processed_dir / "raw_input_metadata.json"),
        "processed_contract_version": PROCESSED_CONTRACT_VERSION,
        "raw_inputs": raw_input_metadata,
        "freshness_snapshot": freshness_snapshot,
        "quality_snapshot": quality_snapshot(quality_payload),
        "kpi_snapshot": kpi_snapshot,
        "outputs": outputs,
    }
    atomic_write_json(cfg.processed_dir / "pipeline_manifest.json", manifest)
    atomic_write_json(run_context.success_manifest_path, manifest)
    return manifest


def write_failure_manifest(
    cfg: PipelineConfig,
    run_context: RunContext,
    stage_timings: dict[str, float],
    exc: Exception,
) -> None:
    payload = {
        "pipeline_name": "revenue_intelligence_platform",
        "status": "failed",
        "run_id": run_context.run_id,
        "started_at_utc": run_context.started_at_utc,
        "failed_at_utc": datetime.now(UTC).isoformat(),
        "environment": cfg.env_name,
        "input_fingerprint": run_context.input_fingerprint,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "stage_timings_seconds": {name: round(value, 3) for name, value in stage_timings.items()},
        "log_path": str(run_context.log_path),
    }
    atomic_write_json(run_context.failure_manifest_path, payload)
