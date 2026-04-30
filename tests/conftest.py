from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from src.config import PipelineConfig


@pytest.fixture
def pipeline_config_factory(tmp_path: Path) -> Callable[..., PipelineConfig]:
    def _build(*, semantic_metrics_exists: bool = True) -> PipelineConfig:
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

    return _build
