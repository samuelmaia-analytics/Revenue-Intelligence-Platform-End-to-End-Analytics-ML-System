from __future__ import annotations

import json
import logging
import shutil
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from time import perf_counter, sleep
from typing import TypeAlias, TypeVar

import pandas as pd

from src.alerting import build_alert_report, dispatch_alerts
from src.analytics import build_analytics_outputs
from src.artifact_validation import validate_processed_artifacts
from src.config import PipelineConfig
from src.exceptions import PipelineStageError
from src.governance import build_data_dictionary
from src.ingestion import build_bronze_layer, save_raw_datasets
from src.insight_drafting import build_insight_draft
from src.io_utils import (
    atomic_copy_file,
    atomic_copy_tree,
    atomic_write_csv,
    atomic_write_json,
    atomic_write_text,
)
from src.logging_utils import configure_logging
from src.modeling import train_and_score_models
from src.monitoring import build_monitoring_report
from src.persistence import persist_frames
from src.quality import (
    build_dataset_quality_report,
    enforce_quality_gate,
    validate_required_columns,
    write_quality_report,
)
from src.reporting import build_business_outcomes, build_executive_report, build_executive_summary
from src.runtime import RunContext, compute_file_fingerprint, is_older_than, utc_now_minus_days
from src.semantic_metrics import build_metric_catalog
from src.transformation import build_customer_features, build_silver_layer
from src.warehouse import build_star_schema

LOGGER = logging.getLogger("revenue_intelligence.pipeline")
T = TypeVar("T")
RawDatasetMetadata: TypeAlias = dict[str, object]  # noqa: UP040
RawInputMetadata: TypeAlias = dict[str, object]  # noqa: UP040


def _copy_gold_outputs(cfg: PipelineConfig) -> None:
    for table in ["dim_customers.csv", "dim_date.csv", "dim_channel.csv", "fact_orders.csv"]:
        atomic_copy_file(cfg.gold_dir / table, cfg.processed_dir / table)


def _run_stage(stage_name: str, func: Callable[[], T]) -> tuple[T, float]:
    start = perf_counter()
    try:
        result = func()
    except Exception as exc:  # pragma: no cover - exercised in runtime failures
        raise PipelineStageError(f"Stage '{stage_name}' failed: {exc}") from exc
    return result, perf_counter() - start


def _run_stage_with_retry(
    stage_name: str,
    func: Callable[[], T],
    *,
    attempts: int,
    backoff_seconds: int,
    on_attempt_failed: Callable[..., None] | None = None,
    on_attempt_succeeded: Callable[..., None] | None = None,
) -> tuple[T, float]:
    last_error: Exception | None = None
    total_elapsed = 0.0
    for attempt in range(1, attempts + 1):
        try:
            result, elapsed = _run_stage(stage_name, func)
            if on_attempt_succeeded is not None:
                on_attempt_succeeded(stage_name, attempt, attempts, total_elapsed + elapsed)
            return result, total_elapsed + elapsed
        except PipelineStageError as exc:
            last_error = exc
            if on_attempt_failed is not None:
                on_attempt_failed(
                    stage_name,
                    attempt,
                    attempts,
                    exc,
                    will_retry=attempt < attempts,
                    elapsed_seconds=total_elapsed,
                )
            if attempt >= attempts:
                break
            LOGGER.warning(
                "Stage failed and will be retried | stage=%s | attempt=%s/%s | error=%s",
                stage_name,
                attempt,
                attempts,
                exc,
            )
            if backoff_seconds > 0:
                sleep(backoff_seconds)
                total_elapsed += float(backoff_seconds)
    assert last_error is not None
    raise last_error


def _build_raw_input_metadata(raw_paths: list[Path]) -> RawInputMetadata:
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
        "dataset_count": len(datasets),
        "datasets": datasets,
    }


def _build_source_aware_freshness_snapshot(
    raw_metadata: RawInputMetadata,
    max_age_hours: int,
) -> dict[str, object]:
    evaluated_at = datetime.now(UTC)
    threshold_seconds = max_age_hours * 3600
    checks: list[dict[str, object]] = []
    datasets = raw_metadata.get("datasets", [])
    for dataset in datasets if isinstance(datasets, list) else []:
        if not isinstance(dataset, dict):
            continue
        source_updated_at = datetime.fromisoformat(str(dataset["source_updated_at_utc"]))
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


def _apply_backfill_window(
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


def _quality_snapshot(quality_payload: dict) -> dict[str, object]:
    duplicates = sum(int(item["duplicate_rows"]) for item in quality_payload["datasets"])
    referential = sum(int(item["referential_issues"]) for item in quality_payload["datasets"])
    null_total = sum(
        int(value)
        for dataset in quality_payload["datasets"]
        for value in dataset.get("null_counts", {}).values()
    )
    return {
        "dataset_count": quality_payload["total_datasets"],
        "duplicate_rows": duplicates,
        "referential_issues": referential,
        "null_count_total": null_total,
    }


def _persist_run_snapshot(cfg: PipelineConfig, run_context: RunContext) -> None:
    atomic_copy_tree(cfg.processed_dir, run_context.snapshot_dir / "processed")
    atomic_copy_tree(cfg.gold_dir, run_context.snapshot_dir / "gold")
    atomic_copy_file(cfg.warehouse_db_path, run_context.snapshot_dir / cfg.warehouse_db_path.name)


def _write_executive_outputs(
    cfg: PipelineConfig,
    recommendations_df: pd.DataFrame,
    churn_results: dict,
    next_purchase_results: dict,
    unit_df: pd.DataFrame,
    scored_df: pd.DataFrame,
    kpi_snapshot: dict,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    executive_report = build_executive_report(
        recommendations_df=recommendations_df,
        churn_results=churn_results,
        next_purchase_results=next_purchase_results,
        kpi_snapshot=kpi_snapshot,
        output_path=cfg.processed_dir / "executive_report.json",
    )
    executive_summary = build_executive_summary(
        recommendations_df=recommendations_df,
        scored_df=scored_df,
        unit_economics_df=unit_df,
        kpi_snapshot=kpi_snapshot,
        output_path=cfg.processed_dir / "executive_summary.json",
    )
    business_outcomes = build_business_outcomes(
        recommendations_df=recommendations_df,
        unit_economics_df=unit_df,
        outcomes_path=cfg.processed_dir / "business_outcomes.json",
        top_actions_path=cfg.processed_dir / "top_10_actions.csv",
    )
    return executive_report, executive_summary, business_outcomes


def _load_warehouse_frames(processed_dir: Path) -> dict[str, pd.DataFrame]:
    frame_names = [
        "dim_customers",
        "dim_date",
        "dim_channel",
        "fact_orders",
        "customer_features",
        "scored_customers",
        "recommendations",
        "unit_economics",
        "top_10_actions",
    ]
    return {name: pd.read_csv(processed_dir / f"{name}.csv") for name in frame_names}


def _apply_retention(cfg: PipelineConfig) -> None:
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


def _write_run_manifest(
    cfg: PipelineConfig,
    run_context: RunContext,
    stage_timings: dict[str, float],
    raw_input_metadata: dict,
    quality_payload: dict,
    kpi_snapshot: dict,
    freshness_snapshot: dict,
    outputs: list[str],
    observability: dict[str, object],
) -> dict:
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
        "raw_inputs": raw_input_metadata,
        "freshness_snapshot": freshness_snapshot,
        "quality_snapshot": _quality_snapshot(quality_payload),
        "kpi_snapshot": kpi_snapshot,
        "observability": observability,
        "outputs": outputs,
    }
    atomic_write_json(cfg.processed_dir / "pipeline_manifest.json", manifest)
    atomic_write_json(run_context.success_manifest_path, manifest)
    return manifest


def _write_runtime_metrics(
    cfg: PipelineConfig,
    run_context: RunContext,
    stage_timings: dict[str, float],
    outputs: list[str],
    event_count: int,
) -> dict[str, object]:
    total_runtime_seconds = round(sum(stage_timings.values()), 3)
    payload = {
        "run_id": run_context.run_id,
        "environment": cfg.env_name,
        "log_format": cfg.log_format,
        "stage_count": len(stage_timings),
        "stage_timings_seconds": {name: round(value, 3) for name, value in stage_timings.items()},
        "total_runtime_seconds": total_runtime_seconds,
        "event_count": event_count,
        "output_count": len(outputs),
        "outputs": outputs,
    }
    atomic_write_json(cfg.processed_dir / "runtime_metrics.json", payload)
    return payload


def _write_run_events(path: Path, events: list[dict[str, object]]) -> None:
    serialized = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
    atomic_write_text(path, serialized + "\n")


def _write_failure_manifest(
    cfg: PipelineConfig,
    run_context: RunContext,
    stage_timings: dict[str, float],
    exc: Exception,
    event_count: int,
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
        "observability": {
            "log_path": str(run_context.log_path),
            "run_events_path": str(run_context.run_dir / "run_events.jsonl"),
            "event_count": event_count,
        },
    }
    atomic_write_json(run_context.failure_manifest_path, payload)


class RevenueIntelligencePipeline:
    def __init__(self, cfg: PipelineConfig) -> None:
        self.cfg = cfg
        self.stage_timings: dict[str, float] = {}
        self.run_events: list[dict[str, object]] = []
        self.run_id = "n/a"

    def _record_event(self, event_type: str, **fields: object) -> None:
        self.run_events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "run_id": self.run_id,
                **fields,
            }
        )

    def _stage(self, stage_name: str, func: Callable[[], T]) -> T:
        self._record_event("stage.started", stage=stage_name, status="running")

        def on_attempt_failed(
            current_stage: str,
            attempt: int,
            attempts: int,
            exc: Exception,
            *,
            will_retry: bool,
            elapsed_seconds: float,
        ) -> None:
            self._record_event(
                "stage.retry_scheduled" if will_retry else "stage.failed",
                stage=current_stage,
                status="retrying" if will_retry else "failed",
                attempt=attempt,
                max_attempts=attempts,
                elapsed_seconds=round(elapsed_seconds, 3),
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )

        def on_attempt_succeeded(
            current_stage: str,
            attempt: int,
            attempts: int,
            elapsed_seconds: float,
        ) -> None:
            self._record_event(
                "stage.completed",
                stage=current_stage,
                status="completed",
                attempt=attempt,
                max_attempts=attempts,
                elapsed_seconds=round(elapsed_seconds, 3),
            )

        result, elapsed = _run_stage_with_retry(
            stage_name,
            func,
            attempts=self.cfg.retry_attempts,
            backoff_seconds=self.cfg.retry_backoff_seconds,
            on_attempt_failed=on_attempt_failed,
            on_attempt_succeeded=on_attempt_succeeded,
        )
        self.stage_timings[stage_name] = elapsed
        LOGGER.info(
            "Stage completed | stage=%s | elapsed=%.3fs",
            stage_name,
            elapsed,
            extra={
                "event_type": "stage.completed",
                "stage": stage_name,
                "elapsed_seconds": round(elapsed, 3),
                "status": "completed",
            },
        )
        return result

    def run(self) -> dict:
        self.cfg.ensure_directories()
        run_context = RunContext.build(
            manifests_dir=self.cfg.manifests_dir,
            runs_dir=self.cfg.runs_dir,
            snapshots_dir=self.cfg.snapshots_dir,
            input_files=(
                [path for path in self.cfg.raw_dir.iterdir() if path.is_file()]
                if self.cfg.raw_dir.exists()
                else []
            ),
        )
        run_context.run_dir.mkdir(parents=True, exist_ok=True)
        configure_logging(
            self.cfg.log_level,
            log_path=run_context.log_path,
            run_id=run_context.run_id,
            log_format=self.cfg.log_format,
        )
        self.run_id = run_context.run_id
        self._record_event(
            "pipeline.started",
            environment=self.cfg.env_name,
            data_dir=str(self.cfg.data_dir),
            seed=self.cfg.seed,
            input_fingerprint=run_context.input_fingerprint,
        )
        LOGGER.info(
            "Pipeline started | env=%s | data_dir=%s | seed=%s | fingerprint=%s",
            self.cfg.env_name,
            self.cfg.data_dir,
            self.cfg.seed,
            run_context.input_fingerprint,
            extra={
                "event_type": "pipeline.started",
                "environment": self.cfg.env_name,
                "data_dir": str(self.cfg.data_dir),
                "seed": self.cfg.seed,
                "input_fingerprint": run_context.input_fingerprint,
            },
        )

        try:
            raw_paths = self._stage(
                "ingestion.raw",
                lambda: save_raw_datasets(self.cfg.raw_dir, seed=self.cfg.seed),
            )
            raw_input_metadata = self._stage(
                "ingestion.metadata",
                lambda: _build_raw_input_metadata([Path(path) for path in raw_paths]),
            )
            atomic_write_json(
                self.cfg.processed_dir / "raw_input_metadata.json",
                raw_input_metadata,
            )
            customers_path, orders_path, marketing_path = raw_paths
            bronze_customers, bronze_orders, bronze_marketing = self._stage(
                "ingestion.bronze",
                lambda: build_bronze_layer(
                    customers_path,
                    orders_path,
                    marketing_path,
                    self.cfg.bronze_dir,
                ),
            )

            silver_customers, silver_orders, silver_marketing = self._stage(
                "validation.silver",
                lambda: build_silver_layer(
                    bronze_customers,
                    bronze_orders,
                    bronze_marketing,
                    self.cfg.silver_dir,
                ),
            )

            customers_df = pd.read_csv(silver_customers, parse_dates=["signup_date"])
            orders_df = pd.read_csv(silver_orders, parse_dates=["order_date"])
            marketing_df = pd.read_csv(silver_marketing)
            validate_required_columns(
                customers_df,
                {"customer_id", "signup_date", "channel", "segment"},
                "silver_customers",
            )
            validate_required_columns(
                orders_df,
                {"order_id", "customer_id", "order_date", "order_value"},
                "silver_orders",
            )
            validate_required_columns(
                marketing_df,
                {"channel", "marketing_spend"},
                "silver_marketing",
            )
            if self.cfg.backfill_start_date or self.cfg.backfill_end_date:
                customers_df, orders_df = self._stage(
                    "validation.backfill",
                    lambda: _apply_backfill_window(
                        customers_df,
                        orders_df,
                        start_date=self.cfg.backfill_start_date,
                        end_date=self.cfg.backfill_end_date,
                    ),
                )
                atomic_write_csv(silver_customers, customers_df)
                atomic_write_csv(silver_orders, orders_df)
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
                max_total_null_fraction=self.cfg.quality_max_null_fraction,
            )
            quality_payload = write_quality_report(
                quality_reports,
                self.cfg.processed_dir / "quality_report.json",
            )

            freshness_snapshot = _build_source_aware_freshness_snapshot(
                raw_input_metadata,
                self.cfg.freshness_max_age_hours,
            )
            atomic_write_json(self.cfg.processed_dir / "freshness_report.json", freshness_snapshot)

            features_df = self._stage(
                "transformation.features",
                lambda: build_customer_features(
                    silver_customers, silver_orders, self.cfg.processed_dir
                ),
            )

            self._stage(
                "modeling.gold",
                lambda: build_star_schema(silver_customers, silver_orders, self.cfg.gold_dir),
            )
            _copy_gold_outputs(self.cfg)

            churn_results, next_purchase_results, scored_df = self._stage(
                "modeling.ml",
                lambda: train_and_score_models(
                    features_df,
                    self.cfg.processed_dir,
                    run_id=run_context.run_id,
                ),
            )

            analytics_outputs = self._stage(
                "metrics.curated",
                lambda: build_analytics_outputs(
                    scored_df=scored_df,
                    silver_customers_path=silver_customers,
                    silver_orders_path=silver_orders,
                    silver_marketing_path=silver_marketing,
                    processed_dir=self.cfg.processed_dir,
                ),
            )
            recommendations_df = analytics_outputs["recommendations"]
            unit_df = analytics_outputs["unit_economics"]
            kpi_snapshot = analytics_outputs["kpi_snapshot"]

            self._stage(
                "governance.semantic_metrics",
                lambda: build_metric_catalog(
                    self.cfg.semantic_metrics_path,
                    self.cfg.processed_dir / "semantic_metrics_catalog.json",
                ),
            )
            self._stage(
                "governance.data_dictionary",
                lambda: build_data_dictionary(self.cfg.data_dictionary_path),
            )

            monitoring_payload = self._stage(
                "monitoring.model",
                lambda: build_monitoring_report(
                    scored_df=scored_df,
                    labeled_df=scored_df,
                    output_path=self.cfg.processed_dir / "monitoring_report.json",
                    baseline_path=self.cfg.processed_dir / "monitoring_baseline.json",
                ),
            )

            alerts_payload = self._stage(
                "monitoring.alerting",
                lambda: build_alert_report(
                    monitoring_report=monitoring_payload,
                    quality_report=quality_payload,
                    output_path=self.cfg.alerts_output_path,
                    thresholds={
                        "drift_feature_count_warn": self.cfg.alert_drift_feature_count_warn,
                        "duplicate_rows_warn": self.cfg.alert_duplicate_rows_warn,
                        "null_count_warn": self.cfg.alert_null_count_warn,
                        "brier_score_warn": self.cfg.alert_brier_score_warn,
                    },
                ),
            )
            dispatch_alerts(alerts_payload, webhook_url=self.cfg.alert_webhook_url)

            executive_report, _, business_outcomes = self._stage(
                "reporting.executive",
                lambda: _write_executive_outputs(
                    self.cfg,
                    recommendations_df=recommendations_df,
                    churn_results=churn_results,
                    next_purchase_results=next_purchase_results,
                    unit_df=unit_df,
                    scored_df=scored_df,
                    kpi_snapshot=kpi_snapshot,
                ),
            )
            self._stage(
                "reporting.insight_draft",
                lambda: build_insight_draft(
                    output_path=self.cfg.processed_dir / "insight_draft.json",
                    executive_report=executive_report,
                    business_outcomes=business_outcomes,
                    monitoring_report=monitoring_payload,
                    alerts_report=alerts_payload,
                    freshness_report=freshness_snapshot,
                    quality_report=quality_payload,
                    run_id=run_context.run_id,
                    mode_requested=self.cfg.insight_draft_mode,
                    llm_provider=self.cfg.llm_provider,
                    llm_model=self.cfg.llm_model,
                ),
            )
            current_outputs = sorted(
                set(path.name for path in self.cfg.processed_dir.glob("*") if path.is_file())
                | {self.cfg.warehouse_db_path.name, "run_events.jsonl", "runtime_metrics.json"}
            )
            self._record_event(
                "pipeline.runtime_summary",
                status="running",
                stage_count=len(self.stage_timings),
                output_count=len(current_outputs),
            )
            self._stage(
                "operations.run_events",
                lambda: _write_run_events(
                    self.cfg.processed_dir / "run_events.jsonl", self.run_events
                ),
            )
            _write_run_events(run_context.run_dir / "run_events.jsonl", self.run_events)
            runtime_metrics = self._stage(
                "operations.runtime_metrics",
                lambda: _write_runtime_metrics(
                    self.cfg,
                    run_context=run_context,
                    stage_timings=self.stage_timings,
                    outputs=current_outputs,
                    event_count=len(self.run_events),
                ),
            )
            self._stage(
                "validation.processed_artifacts",
                lambda: validate_processed_artifacts(
                    self.cfg.processed_dir,
                    output_path=self.cfg.processed_dir / "artifact_validation_report.json",
                ),
            )

            warehouse_frames = _load_warehouse_frames(self.cfg.processed_dir)
            self._stage(
                f"warehouse.{self.cfg.warehouse_target}",
                lambda: persist_frames(
                    warehouse_frames,
                    warehouse_target=self.cfg.warehouse_target,
                    sqlite_path=self.cfg.warehouse_db_path,
                    warehouse_url=self.cfg.warehouse_url,
                ),
            )

            self._stage("operations.snapshot", lambda: _persist_run_snapshot(self.cfg, run_context))
            self._stage("operations.retention", lambda: _apply_retention(self.cfg))

            outputs = sorted(
                set(path.name for path in self.cfg.processed_dir.glob("*") if path.is_file())
                | {self.cfg.warehouse_db_path.name}
            )
            manifest = _write_run_manifest(
                self.cfg,
                run_context=run_context,
                stage_timings=self.stage_timings,
                raw_input_metadata=raw_input_metadata,
                quality_payload=quality_payload,
                kpi_snapshot=kpi_snapshot,
                freshness_snapshot=freshness_snapshot,
                observability={
                    "log_format": self.cfg.log_format,
                    "log_path": str(run_context.log_path),
                    "run_events_path": str(self.cfg.processed_dir / "run_events.jsonl"),
                    "event_count": len(self.run_events),
                },
                outputs=outputs,
            )
            self._record_event(
                "pipeline.completed",
                status="success",
                output_count=len(outputs),
                total_runtime_seconds=runtime_metrics["total_runtime_seconds"],
            )
            _write_run_events(self.cfg.processed_dir / "run_events.jsonl", self.run_events)
            _write_run_events(run_context.run_dir / "run_events.jsonl", self.run_events)
            LOGGER.info(
                "Pipeline completed successfully | outputs=%s | total_runtime_seconds=%.3f",
                len(outputs),
                runtime_metrics["total_runtime_seconds"],
                extra={
                    "event_type": "pipeline.completed",
                    "status": "success",
                    "output_count": len(outputs),
                    "total_runtime_seconds": runtime_metrics["total_runtime_seconds"],
                },
            )
            return manifest
        except Exception as exc:
            self._record_event(
                "pipeline.failed",
                status="failed",
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            _write_run_events(run_context.run_dir / "run_events.jsonl", self.run_events)
            _write_failure_manifest(
                self.cfg,
                run_context=run_context,
                stage_timings=self.stage_timings,
                exc=exc,
                event_count=len(self.run_events),
            )
            LOGGER.exception("Pipeline failed")
            raise


def run_pipeline(cfg: PipelineConfig) -> dict:
    pipeline = RevenueIntelligencePipeline(cfg)
    return pipeline.run()
