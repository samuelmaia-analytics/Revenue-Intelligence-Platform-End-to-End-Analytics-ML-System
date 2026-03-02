import logging
import shutil
from pathlib import Path

from src.config import PipelineConfig
from src.ingestion import build_bronze_layer, save_raw_datasets
from src.metrics import (
    calculate_cac,
    calculate_ltv,
    cohort_analysis,
    rfm_segmentation,
    unit_economics,
)
from src.modeling import train_and_score_models
from src.recommendation import build_recommendations
from src.reporting import build_executive_report, build_executive_summary
from src.transformation import build_customer_features, build_silver_layer
from src.warehouse import build_star_schema

LOGGER = logging.getLogger("revenue_intelligence.pipeline")


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_pipeline(cfg: PipelineConfig) -> None:
    configure_logging(cfg.log_level)
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Pipeline started with data dir: %s", cfg.data_dir)
    customers_path, orders_path, marketing_path = save_raw_datasets(cfg.raw_dir, seed=cfg.seed)
    bronze_customers, bronze_orders, bronze_marketing = build_bronze_layer(
        customers_path, orders_path, marketing_path, cfg.bronze_dir
    )
    silver_customers, silver_orders, silver_marketing = build_silver_layer(
        bronze_customers, bronze_orders, bronze_marketing, cfg.silver_dir
    )

    features_df = build_customer_features(silver_customers, silver_orders, cfg.processed_dir)
    build_star_schema(silver_customers, silver_orders, cfg.gold_dir)

    for table in ["dim_customers.csv", "dim_date.csv", "dim_channel.csv", "fact_orders.csv"]:
        shutil.copy2(cfg.gold_dir / table, cfg.processed_dir / table)

    churn_results, next_purchase_results, scored_df = train_and_score_models(
        features_df, cfg.processed_dir
    )

    ltv_df = calculate_ltv(scored_df)
    cac_df = calculate_cac(silver_marketing, silver_customers)
    rfm_df = rfm_segmentation(silver_orders, silver_customers)
    cohort_df = cohort_analysis(silver_orders, silver_customers)
    unit_df = unit_economics(ltv_df, cac_df)
    rec_df = build_recommendations(ltv_df, cac_df)

    ltv_df.to_csv(cfg.processed_dir / "ltv.csv", index=False)
    cac_df.to_csv(cfg.processed_dir / "cac_by_channel.csv", index=False)
    rfm_df.to_csv(cfg.processed_dir / "rfm_segments.csv", index=False)
    cohort_df.to_csv(cfg.processed_dir / "cohort_retention.csv", index=False)
    unit_df.to_csv(cfg.processed_dir / "unit_economics.csv", index=False)
    rec_df.to_csv(cfg.processed_dir / "recommendations.csv", index=False)
    build_executive_report(
        recommendations_df=rec_df,
        churn_results=churn_results,
        next_purchase_results=next_purchase_results,
        output_path=cfg.processed_dir / "executive_report.json",
    )
    build_executive_summary(
        recommendations_df=rec_df,
        scored_df=scored_df,
        unit_economics_df=unit_df,
        output_path=cfg.processed_dir / "executive_summary.json",
    )

    LOGGER.info("Pipeline completed successfully.")
    LOGGER.info("Churn split strategy: %s", churn_results["split_strategy"])
    LOGGER.info("Churn ROC-AUC (CV mean): %.3f", churn_results["cv_roc_auc_mean"])
    LOGGER.info("Churn ROC-AUC (Temporal test): %.3f", churn_results["temporal_test_roc_auc"])
    LOGGER.info("Next Purchase split strategy: %s", next_purchase_results["split_strategy"])
    LOGGER.info("Next Purchase ROC-AUC (CV mean): %.3f", next_purchase_results["cv_roc_auc_mean"])
    LOGGER.info(
        "Next Purchase ROC-AUC (Temporal test): %.3f",
        next_purchase_results["temporal_test_roc_auc"],
    )


if __name__ == "__main__":
    config = PipelineConfig.from_env(Path(__file__).resolve().parent)
    run_pipeline(config)
