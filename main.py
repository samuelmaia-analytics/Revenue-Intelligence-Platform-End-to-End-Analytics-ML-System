from pathlib import Path

from src.ingestion import save_raw_datasets
from src.metrics import (
    calculate_cac,
    calculate_ltv,
    cohort_analysis,
    rfm_segmentation,
    unit_economics,
)
from src.modeling import train_and_score_models
from src.recommendation import build_recommendations
from src.transformation import build_customer_features
from src.warehouse import build_star_schema


def run_pipeline() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    customers_path, orders_path, marketing_path = save_raw_datasets(raw_dir)
    features_df = build_customer_features(customers_path, orders_path, processed_dir)
    build_star_schema(customers_path, orders_path, processed_dir)

    churn_results, next_purchase_results, scored_df = train_and_score_models(
        features_df, processed_dir
    )

    ltv_df = calculate_ltv(scored_df)
    cac_df = calculate_cac(marketing_path, customers_path)
    rfm_df = rfm_segmentation(orders_path, customers_path)
    cohort_df = cohort_analysis(orders_path, customers_path)
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
