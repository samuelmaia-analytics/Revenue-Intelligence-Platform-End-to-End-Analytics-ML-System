from pathlib import Path

import pandas as pd

from src.reporting import build_executive_report, build_executive_summary


def test_executive_report_contains_required_sections(tmp_path: Path) -> None:
    recommendations = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "channel": ["Organic", "Paid Search", "Social Ads"],
            "segment": ["SMB", "Mid-Market", "Enterprise"],
            "ltv": [1000.0, 2500.0, 4000.0],
            "cac": [100.0, 300.0, 500.0],
            "ltv_cac_ratio": [10.0, 8.33, 8.0],
            "churn_probability": [0.2, 0.4, 0.6],
            "next_purchase_probability": [0.7, 0.5, 0.3],
            "strategic_score": [0.9, 0.7, 0.5],
            "recommended_action": ["Upsell Offer", "Nurture", "Retention Campaign"],
        }
    )
    output = tmp_path / "executive_report.json"
    report = build_executive_report(
        recommendations_df=recommendations,
        churn_results={
            "split_strategy": "temporal",
            "cv_roc_auc_mean": 0.7,
            "temporal_test_roc_auc": 0.69,
        },
        next_purchase_results={
            "split_strategy": "temporal",
            "cv_roc_auc_mean": 0.66,
            "temporal_test_roc_auc": 0.64,
        },
        output_path=output,
    )

    assert output.exists()
    assert "top_kpis" in report
    assert "base_size" in report
    assert "data_refresh_utc" in report
    assert "recommendations_top_20" in report
    assert len(report["recommendations_top_20"]) == 3


def test_executive_summary_contains_requested_sections(tmp_path: Path) -> None:
    recommendations = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "channel": ["Organic", "Paid Search", "Social Ads"],
            "segment": ["SMB", "Mid-Market", "Enterprise"],
            "ltv_cac_ratio": [10.0, 8.33, 8.0],
            "churn_probability": [0.2, 0.4, 0.6],
            "strategic_score": [0.9, 0.7, 0.5],
            "recommended_action": ["Upsell Offer", "Nurture", "Retention Campaign"],
        }
    )
    scored = pd.DataFrame({"monetary": [100, 200, 300], "arpu": [10, 20, 30]})
    unit = pd.DataFrame(
        {
            "channel": ["Organic", "Paid Search", "Social Ads"],
            "ltv_cac_ratio": [4.0, 3.0, 2.0],
        }
    )

    output = tmp_path / "executive_summary.json"
    summary = build_executive_summary(recommendations, scored, unit, output)

    assert output.exists()
    assert "data_refresh_utc" in summary
    assert "kpis" in summary
    assert "ltv_cac_by_channel" in summary
    assert "top_churn_risk_customers" in summary
    assert "top_20_recommended_actions" in summary
