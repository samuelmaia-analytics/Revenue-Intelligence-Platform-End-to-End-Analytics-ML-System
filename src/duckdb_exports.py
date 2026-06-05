from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.io_utils import atomic_write_json

duckdb: Any | None
try:
    import duckdb
except ImportError:  # pragma: no cover
    duckdb = None


def export_duckdb_bundle(processed_dir: Path, warehouse_dir: Path) -> dict[str, object]:
    if duckdb is None:
        raise RuntimeError("DuckDB is required to export the governed DuckDB bundle.")

    warehouse_dir.mkdir(parents=True, exist_ok=True)
    duckdb_path = warehouse_dir / "revenue_intelligence.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    exported_tables: list[str] = []
    try:
        table_files = {
            "recommendations": processed_dir / "recommendations.csv",
            "unit_economics": processed_dir / "unit_economics.csv",
            "top_10_actions": processed_dir / "top_10_actions.csv",
            "scored_customers": processed_dir / "scored_customers.csv",
            "cohort_retention": processed_dir / "cohort_retention.csv",
        }
        for table_name, path in table_files.items():
            frame = pd.read_csv(path)
            connection.register(f"{table_name}_frame", frame)
            connection.execute(
                f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name}_frame"
            )
            exported_tables.append(table_name)

        executive_summary = json.loads(
            (processed_dir / "executive_summary.json").read_text(encoding="utf-8")
        )
        summary_frame = pd.DataFrame(
            [
                {
                    "total_revenue_proxy": executive_summary.get("kpis", {}).get(
                        "total_revenue_proxy"
                    ),
                    "avg_arpu": executive_summary.get("kpis", {}).get("avg_arpu"),
                    "avg_churn_probability": executive_summary.get("kpis", {}).get(
                        "avg_churn_probability"
                    ),
                    "portfolio_size": executive_summary.get("kpis", {}).get("portfolio_size"),
                }
            ]
        )
        connection.register("executive_summary_frame", summary_frame)
        connection.execute(
            "CREATE OR REPLACE TABLE executive_summary AS SELECT * FROM executive_summary_frame"
        )
        exported_tables.append("executive_summary")

        connection.execute(
            """
            CREATE OR REPLACE VIEW channel_scorecard AS
            SELECT
                recommendations.channel,
                COUNT(DISTINCT recommendations.customer_id) AS customers_in_scope,
                AVG(recommendations.ltv) AS avg_ltv,
                AVG(recommendations.cac) AS avg_cac,
                AVG(recommendations.ltv_cac_ratio) AS avg_ltv_cac_ratio,
                AVG(CASE WHEN recommendations.churn_probability >= 0.70 THEN 1.0 ELSE 0.0 END) AS high_churn_risk_pct,
                AVG(recommendations.next_purchase_probability) AS avg_next_purchase_probability
            FROM recommendations
            GROUP BY recommendations.channel
            """
        )
    finally:
        connection.close()

    payload = {
        "duckdb_path": str(duckdb_path),
        "exported_tables": exported_tables,
        "exported_view_count": 1,
        "generated_at_utc": pd.Timestamp.utcnow().isoformat(),
    }
    atomic_write_json(processed_dir / "duckdb_export_manifest.json", payload)
    return payload
