from pathlib import Path
import shutil

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
from src.transformation import build_customer_features, build_silver_layer
from src.warehouse import build_star_schema


def run_pipeline() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    bronze_dir = data_dir / "bronze"
    silver_dir = data_dir / "silver"
    gold_dir = data_dir / "gold"
    processed_dir = data_dir / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    customers_path, orders_path, marketing_path = save_raw_datasets(raw_dir)
    bronze_customers, bronze_orders, bronze_marketing = build_bronze_layer(
        customers_path, orders_path, marketing_path, bronze_dir
    )
    silver_customers, silver_orders, silver_marketing = build_silver_layer(
        bronze_customers, bronze_orders, bronze_marketing, silver_dir
    )

    features_df = build_customer_features(silver_customers, silver_orders, processed_dir)
    build_star_schema(silver_customers, silver_orders, gold_dir)

    for table in ["dim_customers.csv", "dim_date.csv", "dim_channel.csv", "fact_orders.csv"]:
        shutil.copy2(gold_dir / table, processed_dir / table)

    churn_results, next_purchase_results, scored_df = train_and_score_models(
        features_df, processed_dir
    )

    ltv_df = calculate_ltv(scored_df)
    cac_df = calculate_cac(silver_marketing, silver_customers)
    rfm_df = rfm_segmentation(silver_orders, silver_customers)
    cohort_df = cohort_analysis(silver_orders, silver_customers)
    unit_df = unit_economics(ltv_df, cac_df)
    rec_df = build_recommendations(ltv_df, cac_df)

    ltv_df.to_csv(processed_dir / "ltv.csv", index=False)
    cac_df.to_csv(processed_dir / "cac_by_channel.csv", index=False)
    rfm_df.to_csv(processed_dir / "rfm_segments.csv", index=False)
    cohort_df.to_csv(processed_dir / "cohort_retention.csv", index=False)
    unit_df.to_csv(processed_dir / "unit_economics.csv", index=False)
    rec_df.to_csv(processed_dir / "recommendations.csv", index=False)

    print("Pipeline completed.")
    print(f"Churn split strategy: {churn_results['split_strategy']}")
    print(f"Churn ROC-AUC (CV mean): {churn_results['cv_roc_auc_mean']:.3f}")
    print(f"Churn ROC-AUC (Temporal test): {churn_results['temporal_test_roc_auc']:.3f}")
    print(f"Next Purchase split strategy: {next_purchase_results['split_strategy']}")
    print(
        f"Next Purchase ROC-AUC (CV mean): "
        f"{next_purchase_results['cv_roc_auc_mean']:.3f}"
    )
    print(
        f"Next Purchase ROC-AUC (Temporal test): "
        f"{next_purchase_results['temporal_test_roc_auc']:.3f}"
    )


if __name__ == "__main__":
    run_pipeline()
