from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path

from src.config import PipelineConfig
from src.orchestration import run_pipeline


def _ensure_postgres_schema(warehouse_url: str, warehouse_schema: str | None) -> None:
    if not warehouse_schema:
        return

    try:
        from sqlalchemy import create_engine, text
    except ModuleNotFoundError:
        return

    safe_schema = warehouse_schema.replace('"', '""')
    engine = create_engine(warehouse_url)
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema}"'))


def main() -> None:
    warehouse_url = os.getenv("RIP_SMOKE_POSTGRES_URL", "").strip()
    warehouse_schema = os.getenv("RIP_SMOKE_POSTGRES_SCHEMA", "").strip() or None
    if not warehouse_url:
        print(json.dumps({"status": "skipped", "reason": "RIP_SMOKE_POSTGRES_URL not set"}))
        return

    try:
        import sqlalchemy  # noqa: F401
    except ModuleNotFoundError:
        print(json.dumps({"status": "skipped", "reason": "sqlalchemy not installed"}))
        return

    with tempfile.TemporaryDirectory(prefix="rip-postgres-smoke-") as temp_dir:
        project_root = Path(__file__).resolve().parents[1]
        cfg = PipelineConfig.from_env(project_root)
        _ensure_postgres_schema(warehouse_url, warehouse_schema)
        smoke_cfg = replace(
            cfg,
            data_dir=Path(temp_dir) / "data",
            raw_dir=Path(temp_dir) / "data" / "raw",
            bronze_dir=Path(temp_dir) / "data" / "bronze",
            silver_dir=Path(temp_dir) / "data" / "silver",
            gold_dir=Path(temp_dir) / "data" / "gold",
            processed_dir=Path(temp_dir) / "data" / "processed",
            warehouse_dir=Path(temp_dir) / "data" / "warehouse",
            warehouse_db_path=Path(temp_dir) / "data" / "warehouse" / "revenue_intelligence.db",
            alerts_output_path=Path(temp_dir) / "data" / "processed" / "alerts_report.json",
            approvals_output_path=Path(temp_dir) / "data" / "processed" / "approved_actions.csv",
            runs_dir=Path(temp_dir) / "data" / "runs",
            manifests_dir=Path(temp_dir) / "data" / "manifests",
            snapshots_dir=Path(temp_dir) / "data" / "snapshots",
            data_dictionary_path=Path(temp_dir) / "data" / "processed" / "data_dictionary.json",
            warehouse_target="postgres",
            warehouse_url=warehouse_url,
            warehouse_schema=warehouse_schema,
        )
        manifest = run_pipeline(smoke_cfg)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "warehouse_target": manifest["warehouse_target"],
                    "warehouse_schema": manifest["warehouse_schema"],
                    "run_id": manifest["run_id"],
                    "outputs": len(manifest["outputs"]),
                }
            )
        )


if __name__ == "__main__":
    main()
