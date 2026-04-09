from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.dashboard_data import load_processed_assets, refresh_pipeline_outputs
from app.dashboard_i18n import normalize_lang
from app.dashboard_i18n import translate as t
from app.dashboard_metrics import auc_text
from app.ui.primitives import (
    render_badge_table_panel,
    render_chart_panel,
    render_dataframe_panel,
    render_empty_state,
    render_footer,
    render_kpi_card,
    render_panel_header,
    render_section_header,
    render_spacer,
    render_status_pill,
    render_status_strip,
)
from src.config import PipelineConfig
from src.reporting import simulate_action_portfolio
from src.writeback import append_approved_actions


def _style_priority_board(board: pd.DataFrame) -> pd.io.formats.style.Styler:
    styled = board.style
    numeric_gradients = [
        column
        for column in ["strategic_score", "churn_probability", "potential_impact", "ltv_cac_ratio"]
        if column in board.columns
    ]
    if numeric_gradients:
        styled = styled.background_gradient(cmap="Blues", subset=numeric_gradients)
    formatters: dict[str, str] = {}
    for column in ["churn_probability", "next_purchase_probability"]:
        if column in board.columns:
            formatters[column] = "{:.1%}"
    for column in ["potential_impact", "ltv", "cac"]:
        if column in board.columns:
            formatters[column] = "{:,.2f}"
    if "ltv_cac_ratio" in board.columns:
        formatters["ltv_cac_ratio"] = "{:.2f}"
    if formatters:
        styled = styled.format(formatters)
    return styled


def _scope_value(lang: str, value: str) -> str:
    if value in {t(lang, "all_segments"), t(lang, "all_channels"), t(lang, "all_actions")}:
        return t(lang, "all_scope")
    return value


def _status_tone(status: str | None) -> str:
    text = str(status or "").lower()
    if text in {"ok", "success", "fresh", "healthy"}:
        return "success"
    if text in {"warning", "warn", "stale"}:
        return "warning"
    if text in {"error", "failed", "critical"}:
        return "danger"
    return "neutral"


def _portfolio_with_risk(filtered_df: pd.DataFrame) -> pd.DataFrame:
    portfolio = filtered_df.copy()
    portfolio["revenue_at_risk"] = portfolio["ltv"] * portfolio["churn_probability"]
    portfolio["growth_headroom"] = portfolio["ltv"] * portfolio["next_purchase_probability"]
    return portfolio


def build_sidebar(
    *,
    lang: str,
    lang_mode: str,
    recommendations: pd.DataFrame,
    project_root: Path,
) -> tuple[str, str, str, str]:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-block">
                <div class="sidebar-title">{t(lang, "filters_title")}</div>
                <div class="sidebar-caption">{t(lang, "filters_caption")}</div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">{t(lang, "workspace_status")}</div>
                    <div class="sidebar-stat-value">{t(lang, "workspace_status_caption")}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if lang_mode == "bilingual":
            lang_option = st.selectbox(
                t(lang, "language"),
                ["Português (PT-BR)", "Português (PT-PT)", "International (EN)"],
                index=0 if lang == "pt-br" else 1 if lang == "pt-pt" else 2,
            )
            lang = normalize_lang(lang_option)

        if st.button(t(lang, "refresh"), use_container_width=True):
            try:
                with st.spinner(t(lang, "loading")):
                    refresh_pipeline_outputs(project_root)
                st.success(t(lang, "refresh_success"))
                st.rerun()
            except Exception as error:  # pragma: no cover
                st.error(t(lang, "refresh_error", error=str(error)))
        st.caption(t(lang, "refresh_hint"))

        selected_segment = st.selectbox(
            t(lang, "segment"),
            [t(lang, "all_segments")]
            + sorted(recommendations["segment"].dropna().unique().tolist()),
        )
        selected_channel = st.selectbox(
            t(lang, "channel"),
            [t(lang, "all_channels")]
            + sorted(recommendations["channel"].dropna().unique().tolist()),
        )
        selected_action = st.selectbox(
            t(lang, "action"),
            [t(lang, "all_actions")]
            + sorted(recommendations["recommended_action"].dropna().unique().tolist()),
        )

        st.markdown(
            f"""
            <div class="sidebar-block">
                <div class="sidebar-title">{t(lang, "ops_title")}</div>
                <div class="sidebar-caption">{t(lang, "ops_caption")}</div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">{t(lang, "customers")}</div>
                    <div class="sidebar-stat-value">{recommendations["customer_id"].nunique():,}</div>
                </div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">{t(lang, "top_action_mix")}</div>
                    <div class="sidebar-stat-value">{recommendations["recommended_action"].mode().iat[0]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(t(lang, "actions_help"))
    return lang, selected_segment, selected_channel, selected_action


def render_header(lang: str, filtered_df: pd.DataFrame, format_currency_fn: Any) -> None:
    dominant_segment = (
        filtered_df.groupby("segment")["churn_probability"]
        .mean()
        .sort_values(ascending=False)
        .index[0]
    )
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="hero-badge">{t(lang, "header_badge")}</div>
                    <h1>{t(lang, "header_title")}</h1>
                    <p>{t(lang, "header_sub")}</p>
                </div>
                <div class="hero-meta">
                    <div class="hero-stat">
                        <div class="hero-stat-label">{t(lang, "header_updated", dt=datetime.now().strftime("%d/%m/%Y %H:%M"))}</div>
                        <div class="hero-stat-value">{t(lang, "header_scope", customers=filtered_df["customer_id"].nunique())}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">{t(lang, "impact")}</div>
                        <div class="hero-stat-value">{format_currency_fn(float(filtered_df["potential_impact"].sum()), lang)}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">{t(lang, "avg_risk")}</div>
                        <div class="hero-stat-value">{filtered_df["churn_probability"].mean():.1%}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">{t(lang, "top_segment")}</div>
                        <div class="hero-stat-value">{dominant_segment}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(lang: str, filtered_df: pd.DataFrame, format_currency_fn: Any) -> None:
    render_section_header(t(lang, "summary"), t(lang, "summary"), t(lang, "summary_caption"))
    cards = [
        (t(lang, "customers"), f"{filtered_df['customer_id'].nunique():,}", t(lang, "active_base")),
        (
            t(lang, "avg_ltv"),
            format_currency_fn(float(filtered_df["ltv"].mean()), lang),
            t(lang, "per_customer"),
        ),
        (
            t(lang, "avg_risk"),
            f"{filtered_df['churn_probability'].mean():.1%}",
            t(lang, "churn_prob"),
        ),
        (
            t(lang, "efficiency"),
            f"{filtered_df['ltv_cac_ratio'].mean():.2f}",
            t(lang, "avg_efficiency"),
        ),
    ]
    for column, card in zip(st.columns(4), cards, strict=False):
        with column:
            render_kpi_card(*card)
    row_two = st.columns(2)
    with row_two[0]:
        render_kpi_card(
            t(lang, "impact"),
            format_currency_fn(float(filtered_df["potential_impact"].sum()), lang),
            t(lang, "filtered_portfolio"),
        )
    with row_two[1]:
        render_kpi_card(
            t(lang, "business_high_risk"),
            f"{(filtered_df['churn_probability'] >= 0.7).mean():.1%}",
            t(lang, "business_risk_customers"),
        )

    action_mix = filtered_df["recommended_action"].value_counts(normalize=True).mul(100).round(1)
    top_segment = (
        filtered_df.groupby("segment")["churn_probability"].mean().sort_values(ascending=False)
    )
    render_status_strip(
        [
            {
                "label": t(lang, "portfolio_health"),
                "value": f"{filtered_df['churn_probability'].mean():.1%}",
                "subtitle": t(lang, "portfolio_health_caption"),
            },
            {
                "label": t(lang, "high_risk_customers"),
                "value": f"{int((filtered_df['churn_probability'] >= 0.7).sum()):,}",
                "subtitle": t(lang, "business_risk_customers"),
            },
            {
                "label": t(lang, "top_segment"),
                "value": str(top_segment.index[0]),
                "subtitle": f"{top_segment.iloc[0]:.1%}",
            },
            {
                "label": t(lang, "top_action_mix"),
                "value": str(action_mix.index[0]),
                "subtitle": (
                    f"{action_mix.iloc[0]:.1f}% of mix"
                    if lang == "en"
                    else f"{action_mix.iloc[0]:.1f}% do mix"
                ),
            },
        ]
    )
    render_spacer()


def render_filter_summary(
    lang: str,
    *,
    selected_segment: str,
    selected_channel: str,
    selected_action: str,
) -> None:
    render_section_header(
        t(lang, "filter_summary"),
        t(lang, "filter_summary"),
        t(lang, "filter_summary_caption"),
    )
    values = [
        _scope_value(lang, selected_segment),
        _scope_value(lang, selected_channel),
        _scope_value(lang, selected_action),
    ]
    render_status_strip(
        [
            {
                "label": t(lang, "current_scope"),
                "value": (
                    t(lang, "all_scope")
                    if len(set(values)) == 1 and values[0] == t(lang, "all_scope")
                    else t(lang, "workspace_status")
                ),
                "subtitle": t(lang, "workspace_status_caption"),
            },
            {
                "label": t(lang, "selected_segment"),
                "value": values[0],
                "subtitle": t(lang, "segment"),
            },
            {
                "label": t(lang, "selected_channel"),
                "value": values[1],
                "subtitle": t(lang, "channel"),
            },
            {
                "label": t(lang, "selected_action"),
                "value": values[2],
                "subtitle": t(lang, "action"),
            },
        ]
    )
    render_spacer()


def render_leadership_notes(
    lang: str,
    filtered_df: pd.DataFrame,
    format_currency_fn: Any,
    insight_draft: dict[str, Any] | None = None,
) -> None:
    risk_row = (
        filtered_df.groupby("segment")["churn_probability"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .iloc[0]
    )
    action_mix = (
        filtered_df["recommended_action"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .reset_index()
    )
    action_mix.columns = ["action", "pct"]
    top_action = action_mix.iloc[0]
    top_customer = filtered_df.sort_values("potential_impact", ascending=False).iloc[0]

    render_section_header(t(lang, "notes"), t(lang, "board_read"), t(lang, "summary_caption"))
    render_panel_header(
        t(lang, "notes"), t(lang, "board_read"), t(lang, "portfolio_health_caption")
    )
    lines = [
        t(lang, "risk_line", segment=risk_row["segment"], risk=risk_row["churn_probability"]),
        t(
            lang,
            "opp_line",
            customer=int(top_customer["customer_id"]),
            impact=format_currency_fn(float(top_customer["potential_impact"]), lang),
        ),
        t(lang, "prio_line", action=top_action["action"], pct=top_action["pct"]),
    ]
    if insight_draft:
        lines = [str(insight_draft.get("headline", "")), *insight_draft.get("recommended_actions", []), *insight_draft.get("anomalies", [])[:1]]
    bullets = "".join(f"<li>{line}</li>" for line in lines if line)
    st.markdown(f"""<div class="panel"><ul class="insight-list">{bullets}</ul></div>""", unsafe_allow_html=True)


def render_runtime_health(
    lang: str,
    manifest: dict[str, Any],
    artifact_validation: dict[str, Any],
    freshness: dict[str, Any],
    alerts: dict[str, Any],
) -> None:
    render_section_header(
        t(lang, "system_status"), t(lang, "runtime_health"), t(lang, "runtime_caption")
    )
    tone = "success"
    if any(
        _status_tone(item) != "success"
        for item in [
            manifest.get("status"),
            artifact_validation.get("status"),
            freshness.get("status"),
        ]
    ):
        tone = "warning"
    if int(alerts.get("alert_count", 0)) > 0:
        tone = "danger"
    render_status_pill(t(lang, "system_status"), t(lang, "workspace_status"), tone=tone)

    policy = manifest.get("reliability_policy", {})
    backfill = manifest.get("backfill_window", {})
    render_status_strip(
        [
            {
                "label": t(lang, "manifest_status"),
                "value": str(manifest.get("status", "n/a")).upper(),
                "subtitle": t(lang, "system_status"),
            },
            {
                "label": t(lang, "artifact_validation"),
                "value": str(artifact_validation.get("status", "n/a")).upper(),
                "subtitle": "artifact_validation_report.json",
            },
            {
                "label": t(lang, "freshness_status"),
                "value": str(freshness.get("status", "n/a")).upper(),
                "subtitle": "freshness_report.json",
            },
            {
                "label": t(lang, "alerts_count"),
                "value": str(int(alerts.get("alert_count", 0))),
                "subtitle": "alerts_summary.json",
            },
        ]
    )
    render_spacer()
    render_status_strip(
        [
            {
                "label": t(lang, "retry_policy"),
                "value": (
                    f"{int(policy.get('retry_attempts', 0))}x / {int(policy.get('retry_backoff_seconds', 0))}s"
                    if policy
                    else "n/a"
                ),
                "subtitle": t(lang, "runtime_caption"),
            },
            {
                "label": t(lang, "backfill_window"),
                "value": (
                    f"{backfill.get('start_date') or 'open'} -> {backfill.get('end_date') or 'open'}"
                    if backfill.get("start_date") or backfill.get("end_date")
                    else t(lang, "not_configured")
                ),
                "subtitle": "backfill_window",
            },
            {
                "label": t(lang, "outputs_count"),
                "value": str(len(manifest.get("outputs", []))),
                "subtitle": "outputs",
            },
        ]
    )
    render_spacer()

    with st.expander(t(lang, "artifact_validation")):
        st.dataframe(
            pd.DataFrame(
                [
                    {"artifact": "pipeline_manifest.json", "status": manifest.get("status", "n/a")},
                    {
                        "artifact": "artifact_validation_report.json",
                        "status": artifact_validation.get("status", "n/a"),
                    },
                    {"artifact": "freshness_report.json", "status": freshness.get("status", "n/a")},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_overview_tab(
    lang: str,
    filtered_df: pd.DataFrame,
    unit: pd.DataFrame,
    cohort: pd.DataFrame,
    report: dict[str, Any],
    manifest: dict[str, Any],
    artifact_validation: dict[str, Any],
    freshness: dict[str, Any],
    alerts: dict[str, Any],
    format_currency_fn: Any,
) -> None:
    render_runtime_health(lang, manifest, artifact_validation, freshness, alerts)
    business_context = report.get("business_context", {})
    if business_context:
        st.caption(t(lang, "chart_context"))
        best_channel = business_context.get("best_channel_efficiency", {})
        render_status_strip(
            [
                {
                    "label": t(lang, "revenue_proxy"),
                    "value": format_currency_fn(
                        float(business_context.get("revenue_proxy", 0)), lang
                    ),
                    "subtitle": t(lang, "business_context"),
                },
                {
                    "label": t(lang, "portfolio_size"),
                    "value": str(int(business_context.get("portfolio_size", 0))),
                    "subtitle": t(lang, "customers"),
                },
                {
                    "label": t(lang, "best_channel"),
                    "value": str(best_channel.get("channel", "n/a")),
                    "subtitle": f"{float(best_channel.get('ltv_cac_ratio', 0)):.2f}",
                },
            ]
        )

    charts_row = st.columns(2, gap="large")
    with charts_row[0]:
        action_dist = filtered_df["recommended_action"].value_counts().reset_index()
        action_dist.columns = [t(lang, "action"), t(lang, "customers")]
        fig_actions = go.Figure(
            data=[
                go.Bar(
                    x=action_dist[t(lang, "action")],
                    y=action_dist[t(lang, "customers")],
                    marker_color=["#0f5bd7", "#0a3f97", "#0f766e", "#475569"][: len(action_dist)],
                )
            ]
        )
        fig_actions.update_layout(title=t(lang, "action_distribution"), showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "action_distribution"),
            caption=t(lang, "portfolio_health_caption"),
            fig=fig_actions,
        )

    with charts_row[1]:
        fig_efficiency = px.bar(
            unit,
            x="channel",
            y="ltv_cac_ratio",
            color="channel",
            title=t(lang, "channel_efficiency"),
            color_discrete_sequence=["#0f5bd7", "#0a3f97", "#0f766e", "#64748b"],
        )
        fig_efficiency.update_layout(showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "channel_efficiency"),
            caption=t(lang, "summary_caption"),
            fig=fig_efficiency,
        )

    cohort_view = cohort.copy()
    cohort_view["retention_pct"] = cohort_view["retention_rate"] * 100
    heatmap_frame = cohort_view.pivot(
        index="cohort_month", columns="cohort_index", values="retention_pct"
    ).sort_index()
    fig_heatmap = px.imshow(
        heatmap_frame,
        aspect="auto",
        text_auto=".0f",
        title=t(lang, "cohort_retention"),
        labels={
            "x": t(lang, "months_since"),
            "y": t(lang, "cohort_label"),
            "color": t(lang, "retention"),
        },
        color_continuous_scale=[[0, "#e2e8f0"], [0.5, "#7dd3fc"], [1, "#0a3f97"]],
    )
    render_chart_panel(
        eyebrow=t(lang, "chart_context"),
        title=t(lang, "cohort_retention"),
        caption=t(lang, "summary_caption"),
        fig=fig_heatmap,
    )


def render_risk_tab(
    lang: str,
    filtered_df: pd.DataFrame,
    report: dict[str, Any],
    monitoring: dict[str, Any],
    alerts: dict[str, Any],
    format_currency_fn: Any,
) -> None:
    portfolio = _portfolio_with_risk(filtered_df)
    high_risk = portfolio[portfolio["churn_probability"] >= 0.7].copy()
    if high_risk.empty:
        high_risk = portfolio.sort_values("revenue_at_risk", ascending=False).head(10).copy()
    risk_by_segment = (
        portfolio.groupby("segment", as_index=False)
        .agg(
            revenue_at_risk=("revenue_at_risk", "sum"),
            avg_churn_probability=("churn_probability", "mean"),
            customers=("customer_id", "nunique"),
        )
        .sort_values("revenue_at_risk", ascending=False)
    )
    risk_by_channel = (
        portfolio.groupby("channel", as_index=False)
        .agg(
            revenue_at_risk=("revenue_at_risk", "sum"),
            avg_churn_probability=("churn_probability", "mean"),
        )
        .sort_values("revenue_at_risk", ascending=False)
    )
    render_status_strip(
        [
            {
                "label": t(lang, "revenue_at_risk"),
                "value": format_currency_fn(float(portfolio["revenue_at_risk"].sum()), lang),
                "subtitle": t(lang, "risk_caption"),
            },
            {
                "label": t(lang, "high_risk_customers"),
                "value": f"{int((portfolio['churn_probability'] >= 0.7).sum()):,}",
                "subtitle": t(lang, "business_risk_customers"),
            },
            {
                "label": t(lang, "top_segment"),
                "value": str(risk_by_segment.iloc[0]["segment"]),
                "subtitle": f"{risk_by_segment.iloc[0]['avg_churn_probability']:.1%}",
            },
            {
                "label": t(lang, "risk_priority_action"),
                "value": str(high_risk["recommended_action"].mode().iat[0]),
                "subtitle": t(lang, "action_board_caption"),
            },
        ]
    )
    render_spacer()
    charts = st.columns(2, gap="large")
    with charts[0]:
        fig_churn = px.bar(
            risk_by_segment,
            x="segment",
            y="revenue_at_risk",
            color="segment",
            title=t(lang, "revenue_at_risk_by_segment"),
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_churn.update_layout(showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "revenue_at_risk_by_segment"),
            caption=t(lang, "risk_caption"),
            fig=fig_churn,
        )
    with charts[1]:
        fig_next = px.bar(
            risk_by_channel,
            x="channel",
            y="revenue_at_risk",
            color="channel",
            title=t(lang, "revenue_at_risk_by_channel"),
            color_discrete_sequence=px.colors.sequential.Teal_r,
        )
        fig_next.update_layout(showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "revenue_at_risk_by_channel"),
            caption=t(lang, "risk_caption"),
            fig=fig_next,
        )

    top_accounts = high_risk[
        [
            "customer_id",
            "segment",
            "channel",
            "recommended_action",
            "churn_probability",
            "revenue_at_risk",
            "potential_impact",
        ]
    ].sort_values("revenue_at_risk", ascending=False)
    render_badge_table_panel(
        eyebrow=t(lang, "table_context"),
        title=t(lang, "top_accounts_at_risk"),
        caption=t(lang, "risk_caption"),
        frame=top_accounts,
        badge_columns=["recommended_action", "segment"],
    )

def render_segment_performance_tab(
    lang: str,
    filtered_df: pd.DataFrame,
    outcomes: dict[str, Any],
    format_currency_fn: Any,
) -> None:
    portfolio = _portfolio_with_risk(filtered_df)
    segment_perf = (
        portfolio.groupby("segment", as_index=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_ltv=("ltv", "mean"),
            avg_churn_probability=("churn_probability", "mean"),
            avg_next_purchase_probability=("next_purchase_probability", "mean"),
            revenue_at_risk=("revenue_at_risk", "sum"),
            potential_impact=("potential_impact", "sum"),
        )
        .sort_values("potential_impact", ascending=False)
    )
    channel_eff = pd.DataFrame(outcomes.get("ltv_cac_by_channel", []))
    render_status_strip(
        [
            {
                "label": t(lang, "top_segment"),
                "value": str(segment_perf.iloc[0]["segment"]),
                "subtitle": format_currency_fn(float(segment_perf.iloc[0]["potential_impact"]), lang),
            },
            {
                "label": t(lang, "avg_ltv"),
                "value": format_currency_fn(float(portfolio["ltv"].mean()), lang),
                "subtitle": t(lang, "per_customer"),
            },
            {
                "label": t(lang, "avg_risk"),
                "value": f"{portfolio['churn_probability'].mean():.1%}",
                "subtitle": t(lang, "segment_performance_caption"),
            },
            {
                "label": t(lang, "best_channel"),
                "value": str(channel_eff.sort_values("ltv_cac_ratio", ascending=False).iloc[0]["channel"]),
                "subtitle": f"{float(channel_eff['ltv_cac_ratio'].max()):.2f}",
            },
        ]
    )
    render_spacer()
    charts = st.columns(2, gap="large")
    with charts[0]:
        fig_segment = px.bar(
            segment_perf,
            x="segment",
            y="potential_impact",
            color="segment",
            title=t(lang, "performance_by_segment"),
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_segment.update_layout(showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "performance_by_segment"),
            caption=t(lang, "segment_performance_caption"),
            fig=fig_segment,
        )
    with charts[1]:
        fig_channel = px.bar(
            channel_eff,
            x="channel",
            y="ltv_cac_ratio",
            color="channel",
            title=t(lang, "channel_efficiency"),
            color_discrete_sequence=px.colors.sequential.Teal_r,
        )
        fig_channel.update_layout(showlegend=False)
        render_chart_panel(
            eyebrow=t(lang, "chart_context"),
            title=t(lang, "channel_efficiency"),
            caption=t(lang, "segment_performance_caption"),
            fig=fig_channel,
        )
    render_badge_table_panel(
        eyebrow=t(lang, "table_context"),
        title=t(lang, "performance_by_segment"),
        caption=t(lang, "segment_performance_caption"),
        frame=segment_perf,
        badge_columns=["segment"],
    )


def render_forecast_tab(
    *,
    lang: str,
    filtered_df: pd.DataFrame,
    outcomes: dict[str, Any],
    top10: pd.DataFrame,
    format_currency_fn: Any,
) -> None:
    simulation = outcomes.get("simulation_summary_top10", {})
    policy_defaults = outcomes.get("simulation_assumptions", {})
    render_status_strip(
        [
            {
                "label": t(lang, "baseline"),
                "value": format_currency_fn(float(simulation.get("baseline_revenue_90d", 0)), lang),
                "subtitle": t(lang, "forecast_caption"),
            },
            {
                "label": t(lang, "scenario"),
                "value": format_currency_fn(float(simulation.get("scenario_revenue_90d", 0)), lang),
                "subtitle": t(lang, "forecast_caption"),
            },
            {
                "label": t(lang, "delta_revenue"),
                "value": format_currency_fn(float(simulation.get("delta_revenue_90d", 0)), lang),
                "subtitle": t(lang, "forecast_caption"),
            },
            {
                "label": t(lang, "roi"),
                "value": f"{float(simulation.get('roi_simulated', 0)):.2f}x",
                "subtitle": t(lang, "business_net_impact_sub"),
            },
        ]
    )
    render_spacer()
    overrides: dict[str, dict[str, float | str]] = {}
    controls = st.columns(2, gap="large")
    for idx, (action_name, policy) in enumerate(policy_defaults.items()):
        with controls[idx % 2]:
            st.markdown(f"**{action_name}**")
            overrides[action_name] = {
                "uplift_rate": st.slider(
                    f"{action_name} | {t(lang, 'uplift_rate')}",
                    0.0,
                    1.0,
                    float(policy.get("uplift_rate", 0.1)),
                    0.01,
                    key=f"forecast_uplift_{action_name}",
                ),
                "cost_rate": st.slider(
                    f"{action_name} | {t(lang, 'cost_rate')}",
                    0.0,
                    0.5,
                    float(policy.get("cost_rate", 0.05)),
                    0.01,
                    key=f"forecast_cost_{action_name}",
                ),
                "base": str(policy.get("base", "ltv")),
            }
    scenario_actions = simulate_action_portfolio(
        recommendations_df=filtered_df, top_n=10, policy_overrides=overrides
    )
    fig_forecast = go.Figure(
        data=[
            go.Bar(name=t(lang, "baseline"), x=["90d"], y=[scenario_actions["baseline_revenue_90d"].sum()], marker_color="#94a3b8"),
            go.Bar(name=t(lang, "scenario"), x=["90d"], y=[scenario_actions["scenario_revenue_90d"].sum()], marker_color="#0f5bd7"),
        ]
    )
    fig_forecast.update_layout(barmode="group", title=t(lang, "forecast_and_scenarios"))
    render_chart_panel(
        eyebrow=t(lang, "chart_context"),
        title=t(lang, "forecast_and_scenarios"),
        caption=t(lang, "forecast_caption"),
        fig=fig_forecast,
    )
    render_badge_table_panel(
        eyebrow=t(lang, "table_context"),
        title=t(lang, "scenario"),
        caption=t(lang, "forecast_caption"),
        frame=scenario_actions[
            [
                "customer_id",
                "recommended_action",
                "expected_uplift",
                "action_cost",
                "net_impact",
                "roi_simulated",
            ]
        ],
        badge_columns=["recommended_action"],
    )
    if not top10.empty:
        render_dataframe_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "top_actions"),
            caption=t(lang, "forecast_caption"),
            frame=top10,
            height=360,
        )


def render_reliability_tab(
    lang: str,
    manifest: dict[str, Any],
    artifact_validation: dict[str, Any],
    freshness: dict[str, Any],
    alerts: dict[str, Any],
) -> None:
    render_runtime_health(lang, manifest, artifact_validation, freshness, alerts)
    stage_timings = pd.DataFrame(
        [
            {"stage": stage_name, "seconds": seconds}
            for stage_name, seconds in manifest.get("stage_timings_seconds", {}).items()
        ]
    ).sort_values("seconds", ascending=False)
    freshness_checks = pd.DataFrame(freshness.get("checks", []))
    quality_snapshot = manifest.get("quality_snapshot", {})
    render_status_strip(
        [
            {
                "label": t(lang, "duplicate_rows"),
                "value": str(int(quality_snapshot.get("duplicate_rows", 0))),
                "subtitle": t(lang, "reliability_caption"),
            },
            {
                "label": t(lang, "null_count"),
                "value": str(int(quality_snapshot.get("null_count_total", 0))),
                "subtitle": t(lang, "reliability_caption"),
            },
            {
                "label": t(lang, "freshness_status"),
                "value": str(freshness.get("status", "n/a")).upper(),
                "subtitle": t(lang, "reliability_caption"),
            },
            {
                "label": t(lang, "alerts_count"),
                "value": str(int(alerts.get("alert_count", 0))),
                "subtitle": t(lang, "alerts"),
            },
        ]
    )
    render_spacer()
    if not stage_timings.empty:
        render_dataframe_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "run_stage_timings"),
            caption=t(lang, "reliability_caption"),
            frame=stage_timings,
        )
    if not freshness_checks.empty:
        render_badge_table_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "freshness_checks"),
            caption=t(lang, "reliability_caption"),
            frame=freshness_checks[["dataset_name", "row_count", "age_hours", "status"]],
            badge_columns=["status"],
        )


def render_governance_tab(
    lang: str,
    report: dict[str, Any],
    monitoring: dict[str, Any],
    alerts: dict[str, Any],
    semantic_metrics: dict[str, Any],
) -> None:
    model_report = report.get("model_performance", report)
    churn_calibration = monitoring.get("calibration", {}).get("churn", {})
    render_status_strip(
        [
            {
                "label": t(lang, "drift_status"),
                "value": str(monitoring.get("drift_status", "n/a")).upper(),
                "subtitle": t(lang, "governance_caption"),
            },
            {
                "label": t(lang, "calibration"),
                "value": (
                    f"{float(churn_calibration.get('brier_score', 0)):.3f}"
                    if churn_calibration.get("status") == "ok"
                    else "n/a"
                ),
                "subtitle": str(churn_calibration.get("status", "n/a")).upper(),
            },
            {
                "label": t(lang, "semantic_metrics"),
                "value": str(len(semantic_metrics.get("metrics", []))),
                "subtitle": t(lang, "governance_caption"),
            },
            {
                "label": t(lang, "alerts_count"),
                "value": str(len(alerts.get("alerts", []))),
                "subtitle": t(lang, "alerts"),
            },
        ]
    )
    render_spacer()
    governance_frame = pd.DataFrame(
        [
            {
                "Model": t(lang, "churn_model"),
                t(lang, "split"): model_report.get("churn", {}).get("split_strategy", "n/a"),
                t(lang, "cv_auc"): auc_text(model_report.get("churn", {}).get("cv_roc_auc_mean")),
                t(lang, "holdout_auc"): auc_text(
                    model_report.get("churn", {}).get("temporal_test_roc_auc")
                ),
            },
            {
                "Model": t(lang, "next_model"),
                t(lang, "split"): model_report.get("next_purchase_30d", {}).get("split_strategy", "n/a"),
                t(lang, "cv_auc"): auc_text(
                    model_report.get("next_purchase_30d", {}).get("cv_roc_auc_mean")
                ),
                t(lang, "holdout_auc"): auc_text(
                    model_report.get("next_purchase_30d", {}).get("temporal_test_roc_auc")
                ),
            },
        ]
    )
    render_dataframe_panel(
        eyebrow=t(lang, "governance"),
        title=t(lang, "governance"),
        caption=t(lang, "governance_caption"),
        frame=governance_frame,
    )
    drift_rows = [
        {
            t(lang, "driver_feature"): feature_name,
            t(lang, "drift_status"): drift_info.get("status", "n/a"),
        }
        for feature_name, drift_info in monitoring.get("feature_drift", {}).items()
    ]
    if drift_rows:
        render_badge_table_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "drift_status"),
            caption=t(lang, "governance_caption"),
            frame=pd.DataFrame(drift_rows),
            badge_columns=[t(lang, "drift_status")],
        )
    semantic_rows = pd.DataFrame(semantic_metrics.get("metrics", []))
    if not semantic_rows.empty:
        render_dataframe_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "semantic_metrics"),
            caption=t(lang, "governance_caption"),
            frame=semantic_rows.rename(
                columns={"label": "Metric", "owner": t(lang, "owner"), "expression": t(lang, "expression")}
            ),
            height=320,
        )
    alert_rows = pd.DataFrame(alerts.get("alerts", []))
    if alert_rows.empty:
        st.info(t(lang, "alerts_empty"))
    else:
        render_badge_table_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "alerts"),
            caption=t(lang, "governance_caption"),
            frame=alert_rows,
            badge_columns=["severity"],
        )


def render_action_tab(
    *, lang: str, filtered_df: pd.DataFrame, approved_actions: pd.DataFrame, project_root: Path
) -> None:
    render_section_header(
        t(lang, "data_view"), t(lang, "tab_action_list"), t(lang, "action_board_caption")
    )
    render_status_strip(
        [
            {
                "label": t(lang, "customers"),
                "value": f"{filtered_df['customer_id'].nunique():,}",
                "subtitle": t(lang, "tab_action_list"),
            },
            {
                "label": t(lang, "impact"),
                "value": f"{float(filtered_df['potential_impact'].sum()):,.0f}",
                "subtitle": t(lang, "filtered_portfolio"),
            },
            {
                "label": t(lang, "top_action_mix"),
                "value": str(filtered_df["recommended_action"].mode().iat[0]),
                "subtitle": t(lang, "actions_help"),
            },
        ]
    )
    render_spacer()
    render_panel_header(t(lang, "data_view"), t(lang, "tab_action_list"), t(lang, "actions_help"))
    board = filtered_df.sort_values("strategic_score", ascending=False).head(120)
    controls = st.columns([1, 1.1, 1.1], gap="medium")
    with controls[0]:
        st.download_button(
            t(lang, "download"),
            board.to_csv(index=False).encode("utf-8"),
            file_name=t(lang, "board_file"),
            mime="text/csv",
        )
    with controls[1]:
        approver = st.text_input(t(lang, "approver"), value="executive_demo")
    with controls[2]:
        approval_note = st.text_input(t(lang, "approval_note"), value="")
    render_dataframe_panel(
        eyebrow=t(lang, "table_context"),
        title=t(lang, "tab_action_list"),
        caption=t(lang, "action_board_caption"),
        frame=_style_priority_board(board),
        height=460,
    )
    selected_customers = st.multiselect(
        t(lang, "select_customers"), board["customer_id"].astype(int).tolist(), max_selections=10
    )
    if st.button(t(lang, "approve_actions"), use_container_width=True):
        if not selected_customers:
            st.warning(t(lang, "approval_warning"))
        else:
            cfg = PipelineConfig.from_env(project_root)
            approved = board[board["customer_id"].isin(selected_customers)].copy()
            approved["approved_by"] = approver.strip() or "executive_demo"
            approved["approval_note"] = approval_note.strip()
            append_approved_actions(
                approved_actions=approved,
                csv_path=cfg.approvals_output_path,
                warehouse_target=cfg.warehouse_target,
                sqlite_path=cfg.warehouse_db_path,
                warehouse_url=cfg.warehouse_url,
            )
            load_processed_assets.clear()
            st.success(t(lang, "approval_success", count=len(approved)))
            st.rerun()
    with st.expander(t(lang, "approved_actions"), expanded=False):
        if approved_actions.empty:
            st.caption(t(lang, "approvals_empty"))
        else:
            render_badge_table_panel(
                eyebrow=t(lang, "table_context"),
                title=t(lang, "approved_actions"),
                caption=t(lang, "actions_help"),
                frame=approved_actions.tail(20),
                badge_columns=["recommended_action"],
            )


def render_business_tab(
    *,
    lang: str,
    filtered_df: pd.DataFrame,
    outcomes: dict[str, Any],
    top10: pd.DataFrame,
    semantic_metrics: dict[str, Any],
    format_currency_fn: Any,
) -> None:
    business_kpis = outcomes.get("kpis", {})
    simulation = outcomes.get("simulation_summary_top10", {})
    channel_eff = pd.DataFrame(outcomes.get("ltv_cac_by_channel", []))
    policy_defaults = outcomes.get("simulation_assumptions", {})
    render_section_header(
        t(lang, "tab_business"), t(lang, "tab_business"), t(lang, "business_caption")
    )
    for column, card in zip(
        st.columns(3),
        [
            (
                t(lang, "business_ltv_cac"),
                f"{business_kpis.get('avg_ltv_cac_ratio', 0):.2f}",
                t(lang, "business_portfolio"),
            ),
            (
                t(lang, "business_high_risk"),
                f"{business_kpis.get('high_churn_risk_pct', 0):.1%}",
                t(lang, "business_risk_customers"),
            ),
            (
                t(lang, "business_net_impact"),
                format_currency_fn(float(business_kpis.get("simulated_net_impact_top10", 0)), lang),
                t(lang, "business_net_impact_sub"),
            ),
        ],
        strict=False,
    ):
        with column:
            render_kpi_card(*card)

    render_section_header(
        t(lang, "simulation"), t(lang, "simulation"), t(lang, "simulation_caption")
    )
    render_status_strip(
        [
            {
                "label": t(lang, "baseline"),
                "value": format_currency_fn(float(simulation.get("baseline_revenue_90d", 0)), lang),
                "subtitle": t(lang, "simulation"),
            },
            {
                "label": t(lang, "scenario"),
                "value": format_currency_fn(float(simulation.get("scenario_revenue_90d", 0)), lang),
                "subtitle": t(lang, "simulation"),
            },
            {
                "label": t(lang, "delta_revenue"),
                "value": format_currency_fn(float(simulation.get("delta_revenue_90d", 0)), lang),
                "subtitle": t(lang, "simulation"),
            },
            {
                "label": t(lang, "roi"),
                "value": f"{float(simulation.get('roi_simulated', 0)):.2f}x",
                "subtitle": t(lang, "business_net_impact_sub"),
            },
        ]
    )

    with st.expander(t(lang, "scenario_controls")):
        overrides: dict[str, dict[str, float | str]] = {}
        policy_columns = st.columns(2, gap="large")
        for idx, (action_name, policy) in enumerate(policy_defaults.items()):
            with policy_columns[idx % 2]:
                st.markdown(f"**{action_name}**")
                overrides[action_name] = {
                    "uplift_rate": st.slider(
                        f"{action_name} | {t(lang, 'uplift_rate')}",
                        0.0,
                        1.0,
                        float(policy.get("uplift_rate", 0.1)),
                        0.01,
                        key=f"uplift_{action_name}",
                    ),
                    "cost_rate": st.slider(
                        f"{action_name} | {t(lang, 'cost_rate')}",
                        0.0,
                        0.5,
                        float(policy.get("cost_rate", 0.05)),
                        0.01,
                        key=f"cost_{action_name}",
                    ),
                    "base": str(policy.get("base", "ltv")),
                }
        scenario_actions = simulate_action_portfolio(
            recommendations_df=filtered_df, top_n=10, policy_overrides=overrides
        )
        scenario_summary = {
            "baseline_revenue_90d": float(scenario_actions["baseline_revenue_90d"].sum()),
            "scenario_revenue_90d": float(scenario_actions["scenario_revenue_90d"].sum()),
            "delta_revenue_90d": float(
                scenario_actions["scenario_revenue_90d"].sum()
                - scenario_actions["baseline_revenue_90d"].sum()
            ),
            "roi_simulated": (
                float(scenario_actions["net_impact"].sum() / scenario_actions["action_cost"].sum())
                if float(scenario_actions["action_cost"].sum()) > 0
                else 0.0
            ),
        }
        render_status_strip(
            [
                {
                    "label": t(lang, "baseline"),
                    "value": format_currency_fn(
                        float(scenario_summary["baseline_revenue_90d"]), lang
                    ),
                    "subtitle": t(lang, "scenario_controls"),
                },
                {
                    "label": t(lang, "scenario"),
                    "value": format_currency_fn(
                        float(scenario_summary["scenario_revenue_90d"]), lang
                    ),
                    "subtitle": t(lang, "scenario_controls"),
                },
                {
                    "label": t(lang, "delta_revenue"),
                    "value": format_currency_fn(float(scenario_summary["delta_revenue_90d"]), lang),
                    "subtitle": t(lang, "scenario_controls"),
                },
                {
                    "label": t(lang, "roi"),
                    "value": f"{float(scenario_summary['roi_simulated']):.2f}x",
                    "subtitle": "roi_simulated",
                },
            ]
        )
        render_badge_table_panel(
            eyebrow=t(lang, "table_context"),
            title=t(lang, "scenario"),
            caption=t(lang, "simulation_caption"),
            frame=scenario_actions[
                [
                    "customer_id",
                    "recommended_action",
                    "expected_uplift",
                    "action_cost",
                    "net_impact",
                    "roi_simulated",
                ]
            ],
            badge_columns=["recommended_action"],
        )

    charts = st.columns(2, gap="large")
    with charts[0]:
        if not channel_eff.empty:
            fig_eff = px.bar(
                channel_eff,
                x="channel",
                y="ltv_cac_ratio",
                color="channel",
                title=t(lang, "ltv_cac_channel"),
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig_eff.update_layout(showlegend=False)
            render_chart_panel(
                eyebrow=t(lang, "chart_context"),
                title=t(lang, "ltv_cac_channel"),
                caption=t(lang, "business_caption"),
                fig=fig_eff,
            )
    with charts[1]:
        if not top10.empty:
            fig_impact = px.bar(
                top10.sort_values("net_impact", ascending=True),
                x="net_impact",
                y="customer_id",
                color="action",
                orientation="h",
                title=t(lang, "impact_customer"),
                color_discrete_sequence=px.colors.sequential.Teal_r,
            )
            render_chart_panel(
                eyebrow=t(lang, "chart_context"),
                title=t(lang, "impact_customer"),
                caption=t(lang, "business_caption"),
                fig=fig_impact,
            )

    render_dataframe_panel(
        eyebrow=t(lang, "table_context"),
        title=t(lang, "top_actions"),
        caption=t(lang, "business_caption"),
        frame=top10,
        height=420,
    )
    semantic_rows = pd.DataFrame(semantic_metrics.get("metrics", []))
    with st.expander(t(lang, "semantic_metrics"), expanded=False):
        if semantic_rows.empty:
            st.caption(t(lang, "semantic_empty"))
        else:
            render_dataframe_panel(
                eyebrow=t(lang, "table_context"),
                title=t(lang, "semantic_metrics"),
                caption=t(lang, "business_caption"),
                frame=semantic_rows.rename(
                    columns={
                        "label": "Metric",
                        "owner": t(lang, "owner"),
                        "expression": t(lang, "expression"),
                    }
                ),
            )


def render_empty_dashboard(lang: str) -> None:
    render_empty_state(t(lang, "empty_title"), t(lang, "empty_body"))


def render_dashboard_footer(lang: str) -> None:
    render_footer(t(lang, "footer_title"), t(lang, "footer_body"), t(lang, "footer_timestamp"))
