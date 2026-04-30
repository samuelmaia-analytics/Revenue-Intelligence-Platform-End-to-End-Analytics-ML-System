from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable

import pandas as pd

from main import run_pipeline
from src.config import PipelineConfig


def test_warehouse_supports_portfolio_semantic_query(
    pipeline_config_factory: Callable[..., PipelineConfig]
) -> None:
    cfg = pipeline_config_factory()
    run_pipeline(cfg)

    expected = json.loads(
        (cfg.processed_dir / "business_outcomes.json").read_text(encoding="utf-8")
    )
    with sqlite3.connect(cfg.warehouse_db_path) as connection:
        semantic_query = pd.read_sql_query(
            """
            SELECT
                SUM(scored.monetary) AS revenue_proxy,
                AVG(recommendations.ltv) AS avg_ltv,
                AVG(recommendations.cac) AS avg_cac,
                AVG(recommendations.ltv_cac_ratio) AS avg_ltv_cac_ratio,
                AVG(CASE WHEN recommendations.churn_probability >= 0.70 THEN 1.0 ELSE 0.0 END) AS high_churn_risk_pct
            FROM scored_customers scored
            INNER JOIN recommendations
                ON scored.customer_id = recommendations.customer_id
            """,
            connection,
        )

    assert float(semantic_query.loc[0, "revenue_proxy"]) > 0
    assert float(semantic_query.loc[0, "avg_ltv_cac_ratio"]) > 0
    assert 0.0 <= float(semantic_query.loc[0, "high_churn_risk_pct"]) <= 1.0
    assert (
        abs(
            float(semantic_query.loc[0, "avg_ltv_cac_ratio"])
            - float(expected["kpis"]["avg_ltv_cac_ratio"])
        )
        < 1e-9
    )


def test_warehouse_supports_channel_analytics_query(
    pipeline_config_factory: Callable[..., PipelineConfig]
) -> None:
    cfg = pipeline_config_factory()
    run_pipeline(cfg)

    unit_economics = pd.read_csv(cfg.processed_dir / "unit_economics.csv")
    with sqlite3.connect(cfg.warehouse_db_path) as connection:
        channel_query = pd.read_sql_query(
            """
            SELECT
                recommendations.channel,
                COUNT(*) AS customers_in_scope,
                AVG(recommendations.ltv) AS avg_ltv,
                AVG(recommendations.cac) AS avg_cac,
                AVG(recommendations.ltv_cac_ratio) AS avg_ltv_cac_ratio,
                AVG(scored.arpu) AS avg_arpu
            FROM recommendations
            INNER JOIN scored_customers scored
                ON recommendations.customer_id = scored.customer_id
            GROUP BY recommendations.channel
            ORDER BY recommendations.channel
            """,
            connection,
        )

    assert not channel_query.empty
    assert set(channel_query["channel"]) == set(unit_economics["channel"])
    assert (channel_query["customers_in_scope"] > 0).all()
    assert (channel_query["avg_ltv_cac_ratio"] > 0).all()


def test_warehouse_supports_segment_priority_query(
    pipeline_config_factory: Callable[..., PipelineConfig]
) -> None:
    cfg = pipeline_config_factory()
    run_pipeline(cfg)

    expected = pd.read_csv(cfg.processed_dir / "recommendations.csv")
    with sqlite3.connect(cfg.warehouse_db_path) as connection:
        segment_query = pd.read_sql_query(
            """
            SELECT
                segment,
                COUNT(*) AS customers_in_scope,
                AVG(strategic_score) AS avg_strategic_score,
                AVG(churn_probability) AS avg_churn_probability
            FROM recommendations
            GROUP BY segment
            ORDER BY segment
            """,
            connection,
        )

    expected_counts = expected.groupby("segment")["customer_id"].count().sort_index()
    observed_counts = segment_query.set_index("segment")["customers_in_scope"].sort_index()

    assert not segment_query.empty
    assert (segment_query["avg_strategic_score"] > 0).all()
    assert segment_query["avg_churn_probability"].between(0, 1).all()
    pd.testing.assert_series_equal(observed_counts, expected_counts, check_names=False)
