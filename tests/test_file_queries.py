from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PipelineConfig
from src.file_queries import list_queryable_objects, run_query


def _build_cfg(tmp_path: Path) -> PipelineConfig:
    data_dir = tmp_path / "data"
    cfg = PipelineConfig.from_env(project_root=Path(__file__).resolve().parents[1]).with_overrides(
        data_dir=data_dir
    )
    cfg.ensure_directories()
    return cfg


def test_query_layer_registers_olist_raw_aliases(tmp_path: Path) -> None:
    cfg = _build_cfg(tmp_path)
    pd.DataFrame({"order_id": ["o1", "o2"], "price": [10.0, 25.0]}).to_csv(
        cfg.raw_dir / "olist_orders_dataset.csv",
        index=False,
    )
    pd.DataFrame({"total_revenue": [35.0], "average_ticket": [17.5]}).to_csv(
        cfg.processed_dir / "executive_scorecard.csv",
        index=False,
    )

    result = run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM raw.orders) AS order_rows,
            (SELECT total_revenue FROM processed.executive_scorecard LIMIT 1) AS total_revenue
        """,
        cfg,
    )

    assert int(result.loc[0, "order_rows"]) == 2
    assert float(result.loc[0, "total_revenue"]) == 35.0


def test_query_layer_lists_schema_and_flat_references(tmp_path: Path) -> None:
    cfg = _build_cfg(tmp_path)
    pd.DataFrame({"customer_id": ["c1"]}).to_csv(
        cfg.processed_dir / "customer_segment_health.csv",
        index=False,
    )

    objects = list_queryable_objects(cfg)

    assert not objects.empty
    assert "processed.customer_segment_health" in set(objects["schema_ref"])
    assert "processed_customer_segment_health" in set(objects["flat_ref"])
