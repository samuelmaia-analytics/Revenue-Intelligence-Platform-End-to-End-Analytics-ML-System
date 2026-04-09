from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.io_utils import atomic_write_json


def _fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def _fmt_currency(value: float) -> str:
    return f"{value:,.2f}"


def build_insight_draft(
    *,
    output_path: Path,
    executive_report: dict[str, Any],
    business_outcomes: dict[str, Any],
    monitoring_report: dict[str, Any],
    alerts_report: dict[str, Any],
    freshness_report: dict[str, Any],
    quality_report: dict[str, Any],
    run_id: str,
    mode_requested: str = "deterministic",
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    top_kpis = executive_report.get("top_kpis", {})
    business_context = executive_report.get("business_context", {})
    model_performance = executive_report.get("model_performance", {})
    top_actions = business_outcomes.get("top_10_actions", [])
    simulation = business_outcomes.get("simulation_summary_top10", {})
    active_alerts = alerts_report.get("alerts", [])
    quality_datasets = quality_report.get("datasets", [])

    top_action = top_actions[0] if top_actions else {}
    drift_status = str(monitoring_report.get("drift_status", "n/a"))
    freshness_status = str(freshness_report.get("status", "n/a"))
    avg_churn = float(top_kpis.get("avg_churn_probability", 0.0))
    avg_next = float(top_kpis.get("avg_next_purchase_probability", 0.0))
    revenue_proxy = float(business_context.get("revenue_proxy", 0.0))
    delta_revenue = float(simulation.get("delta_revenue_90d", 0.0))
    high_risk_share = float(business_outcomes.get("kpis", {}).get("high_churn_risk_pct", 0.0))
    null_count_total = int(
        sum(int(value) for dataset in quality_datasets for value in dataset.get("null_counts", {}).values())
    )

    mode_applied = "deterministic"
    fallback_reason = None
    if mode_requested == "assistive":
        fallback_reason = (
            "Assistive mode requested but no LLM execution path is configured in the governed runtime."
        )

    headline = (
        "Revenue remains commercially actionable with controlled operational risk."
        if alerts_report.get("status") in {"ok", "warning"} and freshness_status == "ok"
        else "Revenue signals need operational review before executive circulation."
    )
    summary = (
        f"Portfolio revenue proxy is {_fmt_currency(revenue_proxy)} with average churn risk at "
        f"{_fmt_pct(avg_churn)} and next-purchase propensity at {_fmt_pct(avg_next)}. "
        f"The current top-10 action portfolio adds {_fmt_currency(delta_revenue)} in projected "
        f"90-day scenario revenue under the governed recommendation policy."
    )
    kpi_highlights = [
        f"Revenue proxy in scope: {_fmt_currency(revenue_proxy)}.",
        f"High-risk share of portfolio: {_fmt_pct(high_risk_share)}.",
        f"Projected 90-day scenario uplift from top actions: {_fmt_currency(delta_revenue)}.",
    ]
    anomalies: list[str] = []
    if active_alerts:
        anomalies.extend(str(item.get("message", "Alert raised.")) for item in active_alerts[:3])
    if null_count_total > 0:
        anomalies.append(f"Quality report recorded {null_count_total} null values across silver datasets.")
    if not anomalies:
        anomalies.append("No critical anomalies were detected in freshness, drift, or quality gates.")
    recommended_actions = [
        (
            f"Prioritize {top_action.get('action', 'top-ranked action')} for customer "
            f"{top_action.get('customer_id', 'n/a')} with projected net impact of "
            f"{_fmt_currency(float(top_action.get('net_impact', 0.0)))}."
        ),
        (
            f"Keep monitoring drift status at {drift_status.upper()} and freshness at "
            f"{freshness_status.upper()} before circulating scorecards."
        ),
    ]
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "mode_requested": mode_requested,
        "mode_applied": mode_applied,
        "deterministic_template_version": "v1",
        "llm": {
            "enabled": False,
            "provider": llm_provider,
            "model": llm_model,
            "fallback_reason": fallback_reason,
        },
        "headline": headline,
        "summary": summary,
        "kpi_highlights": kpi_highlights,
        "anomalies": anomalies,
        "recommended_actions": recommended_actions,
        "evidence": {
            "revenue_proxy": revenue_proxy,
            "high_risk_share": high_risk_share,
            "delta_revenue_90d": delta_revenue,
            "active_alert_count": int(alerts_report.get("alert_count", 0)),
            "drift_status": drift_status,
            "freshness_status": freshness_status,
            "churn_model_auc": model_performance.get("churn", {}).get("temporal_test_roc_auc"),
            "next_purchase_model_auc": model_performance.get("next_purchase_30d", {}).get(
                "temporal_test_roc_auc"
            ),
        },
        "source_artifacts": [
            "executive_report.json",
            "business_outcomes.json",
            "monitoring_report.json",
            "alerts_report.json",
            "freshness_report.json",
            "quality_report.json",
        ],
    }
    atomic_write_json(output_path, payload)
    return payload
