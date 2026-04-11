from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import pandas as pd

from src.analytics_duckdb import build_curated_support_frames_duckdb, duckdb_available
from src.io_utils import atomic_write_csv, atomic_write_json
from src.marketplace_analytics import build_marketplace_outputs
from src.metrics import (
    build_business_kpi_snapshot,
    calculate_cac,
    calculate_ltv,
    cohort_analysis,
    rfm_segmentation,
    unit_economics,
)
from src.recommendation import build_recommendations


class AnalyticsOutputs(TypedDict):
    ltv: pd.DataFrame
    cac: pd.DataFrame
    rfm: pd.DataFrame
    cohort: pd.DataFrame
    unit_economics: pd.DataFrame
    recommendations: pd.DataFrame
    kpi_snapshot: dict[str, object]


def build_analytics_outputs(
    scored_df: pd.DataFrame,
    silver_customers_path: Path,
    silver_orders_path: Path,
    silver_marketing_path: Path,
    processed_dir: Path,
) -> AnalyticsOutputs:
    processed_dir.mkdir(parents=True, exist_ok=True)

    ltv_df = calculate_ltv(scored_df)
    if duckdb_available():
        cac_df, rfm_df, cohort_df = build_curated_support_frames_duckdb(
            customers_path=silver_customers_path,
            orders_path=silver_orders_path,
            marketing_path=silver_marketing_path,
        )
    else:
        cac_df = calculate_cac(silver_marketing_path, silver_customers_path)
        rfm_df = rfm_segmentation(silver_orders_path, silver_customers_path)
        cohort_df = cohort_analysis(silver_orders_path, silver_customers_path)
    unit_df = unit_economics(ltv_df, cac_df)
    recommendations_df = build_recommendations(ltv_df, cac_df)
    kpi_snapshot = build_business_kpi_snapshot(recommendations_df, scored_df, unit_df)
    marketplace_outputs = build_marketplace_outputs(
        silver_customers_path=silver_customers_path,
        silver_orders_path=silver_orders_path,
        processed_dir=processed_dir,
        scored_df=scored_df,
        recommendations_df=recommendations_df,
        cohort_df=cohort_df,
    )
    kpi_snapshot = {**kpi_snapshot, **marketplace_outputs["executive_kpis"]}

    artifacts = {
        "ltv.csv": ltv_df,
        "cac_by_channel.csv": cac_df,
        "cohort_retention.csv": cohort_df,
        "unit_economics.csv": unit_df,
        "recommendations.csv": recommendations_df,
    }
    for filename, frame in artifacts.items():
        atomic_write_csv(processed_dir / filename, frame)

    atomic_write_json(processed_dir / "kpi_snapshot.json", kpi_snapshot)

    return {
        "ltv": ltv_df,
        "cac": cac_df,
        "rfm": rfm_df,
        "cohort": cohort_df,
        "unit_economics": unit_df,
        "recommendations": recommendations_df,
        "kpi_snapshot": kpi_snapshot,
    }
