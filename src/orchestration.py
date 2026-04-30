from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from time import perf_counter, sleep
from typing import TypeVar

from src.config import PipelineConfig
from src.exceptions import PipelineStageError
from src.governance import build_data_dictionary
from src.ingestion import KAGGLE_FILE, RawDatasets, build_bronze_layer, save_raw_datasets
from src.io_utils import atomic_copy_file, atomic_write_json
from src.logging_utils import configure_logging
from src.modeling import train_and_score_models
from src.persistence import persist_frames
from src.pipeline_runtime import apply_backfill_window as _apply_backfill_window
from src.pipeline_runtime import apply_retention as _apply_retention
from src.pipeline_runtime import build_raw_input_metadata as _build_raw_input_metadata
from src.pipeline_runtime import (
    build_source_aware_freshness_snapshot as _build_source_aware_freshness_snapshot,
)
from src.pipeline_runtime import persist_run_snapshot as _persist_run_snapshot
from src.pipeline_runtime import write_failure_manifest as _write_failure_manifest
from src.pipeline_runtime import write_run_manifest as _write_run_manifest
from src.pipeline_services import (
    SilverFrames,
    build_quality_payload,
    build_serving_artifacts,
    build_warehouse_frames,
    load_silver_frames,
    persist_backfill_results,
    validate_silver_frames,
)
from src.runtime import RunContext
from src.semantic_metrics import build_metric_catalog
from src.transformation import SilverDatasets, build_customer_features, build_silver_layer
from src.warehouse import build_star_schema

LOGGER = logging.getLogger("revenue_intelligence.pipeline")
T = TypeVar("T")


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
) -> tuple[T, float]:
    last_error: Exception | None = None
    total_elapsed = 0.0
    for attempt in range(1, attempts + 1):
        try:
            result, elapsed = _run_stage(stage_name, func)
            return result, total_elapsed + elapsed
        except PipelineStageError as exc:
            last_error = exc
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

class RevenueIntelligencePipeline:
    def __init__(self, cfg: PipelineConfig) -> None:
        self.cfg = cfg
        self.stage_timings: dict[str, float] = {}

    def _stage(self, stage_name: str, func: Callable[[], T]) -> T:
        result, elapsed = _run_stage_with_retry(
            stage_name,
            func,
            attempts=self.cfg.retry_attempts,
            backoff_seconds=self.cfg.retry_backoff_seconds,
        )
        self.stage_timings[stage_name] = elapsed
        LOGGER.info("Stage completed | stage=%s | elapsed=%.3fs", stage_name, elapsed)
        return result

    def _resolve_seed_source_path(self) -> Path | None:
        if not self.cfg.allow_bundled_seed_fallback:
            return None
        sample_path = self.cfg.project_root / "data" / "raw" / KAGGLE_FILE
        if sample_path.resolve() == (self.cfg.raw_dir / KAGGLE_FILE).resolve():
            return None
        if sample_path.exists():
            return sample_path
        return None

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
            self.cfg.log_level, log_path=run_context.log_path, run_id=run_context.run_id
        )
        LOGGER.info(
            "Pipeline started | env=%s | data_dir=%s | seed=%s | synthetic_customers=%s | fingerprint=%s",
            self.cfg.env_name,
            self.cfg.data_dir,
            self.cfg.seed,
            self.cfg.synthetic_customer_count,
            run_context.input_fingerprint,
        )

        try:
            raw_datasets: RawDatasets = self._stage(
                "ingestion.raw",
                lambda: save_raw_datasets(
                    self.cfg.raw_dir,
                    seed=self.cfg.seed,
                    source_path=self._resolve_seed_source_path(),
                    synthetic_customer_count=self.cfg.synthetic_customer_count,
                ),
            )
            raw_input_metadata = self._stage(
                "ingestion.metadata",
                lambda: _build_raw_input_metadata(
                    raw_datasets.paths(),
                    source_name=raw_datasets.source_name,
                ),
            )
            atomic_write_json(
                self.cfg.processed_dir / "raw_input_metadata.json",
                raw_input_metadata,
            )
            bronze_datasets = self._stage(
                "ingestion.bronze",
                lambda: build_bronze_layer(
                    raw_datasets.customers_path,
                    raw_datasets.orders_path,
                    raw_datasets.marketing_path,
                    self.cfg.bronze_dir,
                ),
            )

            silver_datasets: SilverDatasets = self._stage(
                "validation.silver",
                lambda: build_silver_layer(
                    bronze_datasets.customers_path,
                    bronze_datasets.orders_path,
                    bronze_datasets.marketing_path,
                    self.cfg.silver_dir,
                ),
            )

            silver_frames: SilverFrames = load_silver_frames(silver_datasets)
            validate_silver_frames(silver_frames)
            if self.cfg.backfill_start_date or self.cfg.backfill_end_date:
                customers_df, orders_df = self._stage(
                    "validation.backfill",
                    lambda: _apply_backfill_window(
                        silver_frames.customers,
                        silver_frames.orders,
                        start_date=self.cfg.backfill_start_date,
                        end_date=self.cfg.backfill_end_date,
                    ),
                )
                persist_backfill_results(silver_datasets, customers_df, orders_df)
                silver_frames = SilverFrames(
                    customers=customers_df,
                    orders=orders_df,
                    marketing=silver_frames.marketing,
                )
            quality_payload = build_quality_payload(
                self.cfg,
                customers_df=silver_frames.customers,
                orders_df=silver_frames.orders,
                marketing_df=silver_frames.marketing,
            )

            freshness_snapshot = _build_source_aware_freshness_snapshot(
                raw_input_metadata,
                self.cfg.freshness_max_age_hours,
            )
            atomic_write_json(self.cfg.processed_dir / "freshness_report.json", freshness_snapshot)

            features_df = self._stage(
                "transformation.features",
                lambda: build_customer_features(
                    silver_datasets.customers_path,
                    silver_datasets.orders_path,
                    self.cfg.processed_dir,
                ),
            )

            self._stage(
                "modeling.gold",
                lambda: build_star_schema(
                    silver_datasets.customers_path,
                    silver_datasets.orders_path,
                    self.cfg.gold_dir,
                ),
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

            serving_artifacts = self._stage(
                "serving.artifacts",
                lambda: build_serving_artifacts(
                    self.cfg,
                    scored_df=scored_df,
                    silver_datasets=silver_datasets,
                    churn_results=churn_results,
                    next_purchase_results=next_purchase_results,
                    quality_payload=quality_payload,
                ),
            )
            kpi_snapshot = serving_artifacts.analytics_outputs.kpi_snapshot

            warehouse_frames = build_warehouse_frames(self.cfg.processed_dir)
            self._stage(
                f"warehouse.{self.cfg.warehouse_target}",
                lambda: persist_frames(
                    warehouse_frames,
                    warehouse_target=self.cfg.warehouse_target,
                    sqlite_path=self.cfg.warehouse_db_path,
                    warehouse_url=self.cfg.warehouse_url,
                    warehouse_schema=self.cfg.warehouse_schema,
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
                outputs=outputs,
            )
            LOGGER.info("Pipeline completed successfully | outputs=%s", len(outputs))
            return manifest
        except Exception as exc:
            _write_failure_manifest(
                self.cfg,
                run_context=run_context,
                stage_timings=self.stage_timings,
                exc=exc,
            )
            LOGGER.exception("Pipeline failed")
            raise


def run_pipeline(cfg: PipelineConfig) -> dict:
    pipeline = RevenueIntelligencePipeline(cfg)
    return pipeline.run()
