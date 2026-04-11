from datetime import UTC, datetime
from pathlib import Path
from typing import SupportsFloat, cast

import pandas as pd

from src.business_rules import RECOMMENDATION_POLICIES
from src.io_utils import atomic_write_csv, atomic_write_json


def _as_float(value: SupportsFloat) -> float:
    return float(value)


def simulate_action_portfolio(
    recommendations_df: pd.DataFrame,
    top_n: int = 10,
    policy_overrides: dict[str, dict[str, float | str]] | None = None,
) -> pd.DataFrame:
    top_actions = (
        recommendations_df.sort_values("strategic_score", ascending=False).head(top_n).copy()
    )
    active_policies = {
        name: {
            "uplift_rate": policy.uplift_rate,
            "cost_rate": policy.cost_rate,
            "base": policy.base_metric,
        }
        for name, policy in RECOMMENDATION_POLICIES.items()
    }
    if policy_overrides:
        for name, override in policy_overrides.items():
            if name in active_policies:
                active_policies[name] = {**active_policies[name], **override}

    def _simulate_row(row: pd.Series) -> pd.Series:
        action = row["recommended_action"]
        policy = active_policies.get(action, active_policies["Nurture"])
        uplift_rate = _as_float(cast(SupportsFloat, policy["uplift_rate"]))
        cost_rate = _as_float(cast(SupportsFloat, policy["cost_rate"]))
        if action == "Retention Campaign":
            expected_uplift = (
                _as_float(cast(SupportsFloat, row["ltv"]))
                * _as_float(cast(SupportsFloat, row["churn_probability"]))
                * uplift_rate
            )
        elif action == "Upsell Offer":
            expected_uplift = (
                _as_float(cast(SupportsFloat, row["ltv"]))
                * _as_float(cast(SupportsFloat, row["next_purchase_probability"]))
                * uplift_rate
            )
        elif action == "Reduce Acquisition Spend":
            expected_uplift = _as_float(cast(SupportsFloat, row["cac"])) * uplift_rate
        else:
            expected_uplift = (
                _as_float(cast(SupportsFloat, row["ltv"]))
                * _as_float(cast(SupportsFloat, row["next_purchase_probability"]))
                * uplift_rate
            )

        cost_base = (
            _as_float(cast(SupportsFloat, row["ltv"]))
            if policy["base"] == "ltv"
            else _as_float(cast(SupportsFloat, row["cac"]))
        )
        action_cost = cost_base * cost_rate
        net_impact = expected_uplift - action_cost
        roi = net_impact / action_cost if action_cost > 0 else 0.0
        return pd.Series(
            {
                "expected_uplift": expected_uplift,
                "action_cost": action_cost,
                "net_impact": net_impact,
                "roi_simulated": roi,
            }
        )

    simulated = top_actions.apply(_simulate_row, axis=1)
    top_actions = pd.concat([top_actions, simulated], axis=1)
    top_actions["priority_rank"] = range(1, len(top_actions) + 1)
    top_actions["baseline_revenue_90d"] = (
        top_actions["ltv"] * top_actions["next_purchase_probability"]
    )
    top_actions["scenario_revenue_90d"] = (
        top_actions["baseline_revenue_90d"] + top_actions["expected_uplift"]
    )
    return top_actions


def build_executive_report(
    recommendations_df: pd.DataFrame,
    churn_results: dict,
    next_purchase_results: dict,
    kpi_snapshot: dict,
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
            "avg_ltv": _as_float(kpi_snapshot["avg_ltv"]),
            "avg_cac": _as_float(kpi_snapshot["avg_cac"]),
            "avg_ltv_cac_ratio": _as_float(kpi_snapshot["avg_ltv_cac_ratio"]),
            "avg_churn_probability": float(recommendations_df["churn_probability"].mean()),
            "avg_next_purchase_probability": float(
                recommendations_df["next_purchase_probability"].mean()
            ),
        },
        "business_context": {
            "revenue_proxy": _as_float(kpi_snapshot["revenue_proxy"]),
            "portfolio_size": int(kpi_snapshot["portfolio_size"]),
            "best_channel_efficiency": kpi_snapshot["best_channel_efficiency"],
        },
        "marketplace_overview": {
            "total_orders": int(kpi_snapshot.get("total_orders", 0)),
            "average_ticket": _as_float(cast(SupportsFloat, kpi_snapshot.get("average_ticket", 0.0))),
            "late_delivery_rate": _as_float(cast(SupportsFloat, kpi_snapshot.get("late_delivery_rate", 0.0))),
            "cancellation_rate": _as_float(cast(SupportsFloat, kpi_snapshot.get("cancellation_rate", 0.0))),
            "avg_review_score": _as_float(cast(SupportsFloat, kpi_snapshot.get("avg_review_score", 0.0))),
            "top_category": kpi_snapshot.get("top_category", {}),
            "top_state": kpi_snapshot.get("top_state", {}),
            "top_seller": kpi_snapshot.get("top_seller", {}),
        },
        "model_performance": {
            "churn": churn_results,
            "next_purchase_30d": next_purchase_results,
        },
        "recommendations_top_20": top_20,
    }

    atomic_write_json(output_path, report)
    return report


def build_executive_summary(
    recommendations_df: pd.DataFrame,
    scored_df: pd.DataFrame,
    unit_economics_df: pd.DataFrame,
    kpi_snapshot: dict,
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
            "total_revenue_proxy": _as_float(kpi_snapshot["revenue_proxy"]),
            "avg_arpu": _as_float(kpi_snapshot["avg_arpu"]),
            "avg_churn_probability": float(recommendations_df["churn_probability"].mean()),
            "portfolio_size": int(kpi_snapshot["portfolio_size"]),
            "repeat_customer_rate": _as_float(cast(SupportsFloat, kpi_snapshot.get("repeat_customer_rate", 0.0))),
            "avg_review_score": _as_float(cast(SupportsFloat, kpi_snapshot.get("avg_review_score", 0.0))),
        },
        "ltv_cac_by_channel": ltv_cac_channel,
        "top_churn_risk_customers": top_churn,
        "top_20_recommended_actions": top_actions,
        "marketplace_highlights": {
            "total_orders": int(kpi_snapshot.get("total_orders", 0)),
            "average_ticket": _as_float(cast(SupportsFloat, kpi_snapshot.get("average_ticket", 0.0))),
            "late_delivery_rate": _as_float(cast(SupportsFloat, kpi_snapshot.get("late_delivery_rate", 0.0))),
            "top_category": kpi_snapshot.get("top_category", {}),
            "top_state": kpi_snapshot.get("top_state", {}),
        },
    }

    atomic_write_json(output_path, summary)
    return summary


def build_business_outcomes(
    recommendations_df: pd.DataFrame,
    unit_economics_df: pd.DataFrame,
    outcomes_path: Path,
    top_actions_path: Path,
    top_n: int = 10,
) -> dict:
    top_actions = simulate_action_portfolio(recommendations_df=recommendations_df, top_n=top_n)

    top_actions_export = top_actions[
        [
            "priority_rank",
            "customer_id",
            "channel",
            "segment",
            "recommended_action",
            "strategic_score",
            "expected_uplift",
            "action_cost",
            "net_impact",
            "roi_simulated",
            "baseline_revenue_90d",
            "scenario_revenue_90d",
            "ltv_cac_ratio",
        ]
    ].rename(
        columns={
            "recommended_action": "action",
            "strategic_score": "strategic_priority_score",
        }
    )

    atomic_write_csv(top_actions_path, top_actions_export)

    baseline_revenue = float(top_actions_export["baseline_revenue_90d"].sum())
    scenario_revenue = float(top_actions_export["scenario_revenue_90d"].sum())
    total_action_cost = float(top_actions_export["action_cost"].sum())
    delta_revenue = scenario_revenue - baseline_revenue
    net_impact = float(top_actions_export["net_impact"].sum())
    roi = net_impact / total_action_cost if total_action_cost > 0 else 0.0

    ltv_cac_by_channel = (
        unit_economics_df[["channel", "ltv_cac_ratio"]]
        .sort_values("ltv_cac_ratio", ascending=False)
        .to_dict(orient="records")
    )

    high_churn_risk_pct = float((recommendations_df["churn_probability"] >= 0.7).mean())
    avg_ltv_cac_ratio = float(recommendations_df["ltv_cac_ratio"].mean())

    outcomes = {
        "data_refresh_utc": datetime.now(UTC).isoformat(),
        "kpis": {
            "avg_ltv_cac_ratio": avg_ltv_cac_ratio,
            "high_churn_risk_pct": high_churn_risk_pct,
            "simulated_net_impact_top10": net_impact,
        },
        "ltv_cac_by_channel": ltv_cac_by_channel,
        "simulation_assumptions": {
            name: {
                "uplift_rate": policy.uplift_rate,
                "cost_rate": policy.cost_rate,
                "base": policy.base_metric,
            }
            for name, policy in RECOMMENDATION_POLICIES.items()
        },
        "simulation_summary_top10": {
            "baseline_revenue_90d": baseline_revenue,
            "scenario_revenue_90d": scenario_revenue,
            "delta_revenue_90d": delta_revenue,
            "total_action_cost": total_action_cost,
            "net_impact": net_impact,
            "roi_simulated": roi,
        },
        "top_10_actions": top_actions_export.to_dict(orient="records"),
    }

    atomic_write_json(outcomes_path, outcomes)
    return outcomes
