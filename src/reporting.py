import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def build_executive_report(
    recommendations_df: pd.DataFrame,
    churn_results: dict,
    next_purchase_results: dict,
    output_path: Path,
) -> dict:
    top_20 = (
        recommendations_df.sort_values("strategic_score", ascending=False)
        .head(20)[
            [
                "customer_id",
                "channel",
                "segment",
                "ltv",
                "cac",
                "ltv_cac_ratio",
                "churn_probability",
                "next_purchase_probability",
                "strategic_score",
                "recommended_action",
            ]
        ]
        .to_dict(orient="records")
    )

    report = {
        "data_refresh_utc": datetime.now(UTC).isoformat(),
        "base_size": {
            "customers_in_scope": int(recommendations_df["customer_id"].nunique()),
            "rows_in_recommendation_table": int(len(recommendations_df)),
        },
        "top_kpis": {
            "avg_ltv": float(recommendations_df["ltv"].mean()),
            "avg_cac": float(recommendations_df["cac"].mean()),
            "avg_ltv_cac_ratio": float(recommendations_df["ltv_cac_ratio"].mean()),
            "avg_churn_probability": float(recommendations_df["churn_probability"].mean()),
            "avg_next_purchase_probability": float(
                recommendations_df["next_purchase_probability"].mean()
            ),
        },
        "model_performance": {
            "churn": {
                "split_strategy": churn_results.get("split_strategy"),
                "cv_roc_auc_mean": churn_results.get("cv_roc_auc_mean"),
                "temporal_test_roc_auc": churn_results.get("temporal_test_roc_auc"),
                "train_size": churn_results.get("train_size"),
                "test_size": churn_results.get("test_size"),
            },
            "next_purchase_30d": {
                "split_strategy": next_purchase_results.get("split_strategy"),
                "cv_roc_auc_mean": next_purchase_results.get("cv_roc_auc_mean"),
                "temporal_test_roc_auc": next_purchase_results.get("temporal_test_roc_auc"),
                "train_size": next_purchase_results.get("train_size"),
                "test_size": next_purchase_results.get("test_size"),
            },
        },
        "recommendations_top_20": top_20,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    return report


def build_executive_summary(
    recommendations_df: pd.DataFrame,
    scored_df: pd.DataFrame,
    unit_economics_df: pd.DataFrame,
    output_path: Path,
    top_n: int = 20,
) -> dict:
    top_churn = (
        recommendations_df.sort_values("churn_probability", ascending=False)
        .head(top_n)[["customer_id", "segment", "channel", "churn_probability"]]
        .to_dict(orient="records")
    )
    top_actions = (
        recommendations_df.sort_values("strategic_score", ascending=False)
        .head(top_n)[["customer_id", "recommended_action", "strategic_score", "ltv_cac_ratio"]]
        .to_dict(orient="records")
    )
    ltv_cac_channel = (
        unit_economics_df[["channel", "ltv_cac_ratio"]]
        .sort_values("ltv_cac_ratio", ascending=False)
        .to_dict(orient="records")
    )

    summary = {
        "data_refresh_utc": datetime.now(UTC).isoformat(),
        "kpis": {
            "total_revenue_proxy": float(scored_df["monetary"].sum()),
            "avg_arpu": float(scored_df["arpu"].mean()),
            "avg_churn_probability": float(recommendations_df["churn_probability"].mean()),
        },
        "ltv_cac_by_channel": ltv_cac_channel,
        "top_churn_risk_customers": top_churn,
        "top_20_recommended_actions": top_actions,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)
    return summary
