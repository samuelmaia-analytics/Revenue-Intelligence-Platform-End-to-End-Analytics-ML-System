import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from main import run_pipeline  # noqa: E402
from src.config import PipelineConfig  # noqa: E402

LANG_MODE = os.getenv("RIP_APP_LANG_MODE", "bilingual").strip().lower()
if LANG_MODE not in {"bilingual", "international"}:
    LANG_MODE = "bilingual"

I18N = {
    "en": {
        "page_title": "Revenue Executive Dashboard",
        "header_title": "Revenue Executive Dashboard",
        "header_sub": "Revenue Intelligence Platform | Updated at {dt}",
        "filters": "Filters",
        "refresh": "Refresh Data",
        "language": "Language",
        "segment": "Segment",
        "channel": "Channel",
        "action": "Action",
        "all_segments": "All",
        "all_channels": "All",
        "all_actions": "All",
        "no_data": "No data available for current filters.",
        "summary": "Executive Summary",
        "customers": "Customers",
        "active_base": "active base",
        "avg_ltv": "Avg LTV",
        "per_customer": "per customer",
        "avg_risk": "Avg Risk",
        "churn_prob": "churn probability",
        "efficiency": "LTV/CAC",
        "avg_efficiency": "average efficiency",
        "impact": "Potential Impact",
        "filtered_portfolio": "filtered portfolio",
        "board_read": "Leadership Read",
        "risk_line": "<b>Risk:</b> {segment} is the most exposed segment ({risk:.1%}).",
        "opp_line": "<b>Opportunity:</b> customer {customer} with potential impact of {impact}.",
        "prio_line": "<b>Priority:</b> {action} represents {pct:.1f}% of current slice.",
        "tab_overview": "Executive Overview",
        "tab_risk_growth": "Risk & Growth",
        "tab_action_list": "Action List",
        "tab_business": "Business Outcomes",
        "download": "Download Prioritized Portfolio (CSV)",
        "board_file": "prioritized_portfolio.csv",
        "action_distribution": "Action Distribution",
        "channel_efficiency": "Channel Efficiency (LTV/CAC)",
        "cohort_retention": "Cohort Retention (%)",
        "months_since": "Months since acquisition",
        "cohort_label": "Acquisition cohort",
        "retention": "Retention %",
        "model_source": "Source: data/processed/executive_report.json",
        "churn_model": "Churn",
        "next_model": "Next Purchase 30d",
        "split": "Split",
        "cv_auc": "ROC-AUC CV",
        "holdout_auc": "ROC-AUC Holdout",
        "churn_by_segment": "Churn Risk by Segment",
        "next_by_channel": "Next Purchase Probability by Channel",
        "drivers": "Risk Drivers: Recency vs Churn (bubble size = Frequency)",
        "business_ltv_cac": "Avg LTV/CAC",
        "business_portfolio": "full portfolio",
        "business_high_risk": "High Risk (>=70%)",
        "business_risk_customers": "customers in risk zone",
        "business_net_impact": "Top-10 Simulated Impact",
        "business_net_impact_sub": "net impact 90d",
        "simulation": "Effect Simulation (Top-10)",
        "baseline": "Baseline 90d",
        "scenario": "Scenario 90d",
        "delta_revenue": "Revenue Delta",
        "roi": "Simulated ROI",
        "ltv_cac_channel": "LTV/CAC by Channel",
        "impact_customer": "Simulated Net Impact by Customer (Top-10)",
        "top_actions": "Top-10 Prioritized Actions",
    },
    "pt-br": {
        "page_title": "Painel Executivo de Receita",
        "header_title": "Painel Executivo de Receita",
        "header_sub": "Revenue Intelligence Platform | Atualizado em {dt}",
        "filters": "Filtros",
        "refresh": "Atualizar Base",
        "language": "Idioma",
        "segment": "Segmento",
        "channel": "Canal",
        "action": "Ação",
        "all_segments": "Todos",
        "all_channels": "Todos",
        "all_actions": "Todas",
        "no_data": "Sem dados para os filtros selecionados.",
        "summary": "Resumo Executivo",
        "customers": "Clientes",
        "active_base": "base ativa",
        "avg_ltv": "LTV Médio",
        "per_customer": "por cliente",
        "avg_risk": "Risco Médio",
        "churn_prob": "probabilidade de churn",
        "efficiency": "LTV/CAC",
        "avg_efficiency": "eficiência média",
        "impact": "Impacto Potencial",
        "filtered_portfolio": "carteira filtrada",
        "board_read": "Leitura de Diretoria",
        "risk_line": "<b>Risco:</b> {segment} é o segmento mais exposto ({risk:.1%}).",
        "opp_line": "<b>Oportunidade:</b> cliente {customer} com impacto potencial de {impact}.",
        "prio_line": "<b>Prioridade:</b> {action} representa {pct:.1f}% do recorte atual.",
        "tab_overview": "Executive Overview",
        "tab_risk_growth": "Risk & Growth",
        "tab_action_list": "Action List",
        "tab_business": "Business Outcomes",
        "download": "Baixar Carteira Priorizada (CSV)",
        "board_file": "carteira_priorizada.csv",
        "action_distribution": "Distribuição de Ações",
        "channel_efficiency": "Eficiência por Canal (LTV/CAC)",
        "cohort_retention": "Retenção por Coorte (%)",
        "months_since": "Meses desde aquisição",
        "cohort_label": "Coorte de aquisição",
        "retention": "Retenção %",
        "model_source": "Fonte: data/processed/executive_report.json",
        "churn_model": "Churn",
        "next_model": "Próxima Compra 30d",
        "split": "Split",
        "cv_auc": "ROC-AUC CV",
        "holdout_auc": "ROC-AUC Holdout",
        "churn_by_segment": "Risco de Churn por Segmento",
        "next_by_channel": "Prob. de Próxima Compra por Canal",
        "drivers": "Drivers de Risco: Recency vs Churn (bolha = Frequency)",
        "business_ltv_cac": "LTV/CAC Médio",
        "business_portfolio": "carteira total",
        "business_high_risk": "Risco Alto (>=70%)",
        "business_risk_customers": "clientes em risco",
        "business_net_impact": "Impacto Simulado Top-10",
        "business_net_impact_sub": "net impact 90d",
        "simulation": "Simulação de Efeito (Top-10)",
        "baseline": "Baseline 90d",
        "scenario": "Scenario 90d",
        "delta_revenue": "Delta Receita",
        "roi": "ROI Simulado",
        "ltv_cac_channel": "LTV/CAC por Canal",
        "impact_customer": "Net Impact Simulado por Cliente (Top-10)",
        "top_actions": "Top-10 Ações Priorizadas",
    },
}


def t(lang: str, key: str, **kwargs: object) -> str:
    text = I18N[lang][key]
    if kwargs:
        return text.format(**kwargs)
    return text


def format_currency(value: float, lang: str) -> str:
    if lang == "pt-br":
        return f"R$ {value:,.0f}".replace(",", ".")
    return f"${value:,.0f}"


def auc_text(value: float | None) -> str:
    if value is None:
        return "n/a"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if pd.isna(v):
        return "n/a"
    return f"{v:.3f}"


def potential_impact(row: pd.Series) -> float:
    action = row["recommended_action"]
    if action == "Retention Campaign":
        return row["ltv"] * row["churn_probability"] * 0.35
    if action == "Upsell Offer":
        return row["ltv"] * row["next_purchase_probability"] * 0.15
    if action == "Reduce Acquisition Spend":
        return row["cac"] * 0.50
    return row["ltv"] * row["next_purchase_probability"] * 0.03


def apply_chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font={"color": "#0f172a", "family": "Segoe UI, Aptos, Calibri, sans-serif", "size": 13},
        title_font={"color": "#0f172a", "size": 18},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def card(title: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """


def load_data(
    processed_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict, pd.DataFrame]:
    required = [
        "recommendations.csv",
        "cohort_retention.csv",
        "unit_economics.csv",
        "executive_report.json",
        "business_outcomes.json",
        "top_10_actions.csv",
    ]
    if not all((processed_dir / f).exists() for f in required):
        run_pipeline(PipelineConfig.from_env(PROJECT_ROOT))

    rec = pd.read_csv(processed_dir / "recommendations.csv")
    cohort = pd.read_csv(processed_dir / "cohort_retention.csv")
    unit = pd.read_csv(processed_dir / "unit_economics.csv")
    top10 = pd.read_csv(processed_dir / "top_10_actions.csv")
    with (processed_dir / "executive_report.json").open("r", encoding="utf-8") as f:
        report = json.load(f)
    with (processed_dir / "business_outcomes.json").open("r", encoding="utf-8") as f:
        outcomes = json.load(f)
    return rec, cohort, unit, report, outcomes, top10


def normalize_lang(option: str) -> str:
    if option.startswith("Portuguese"):
        return "pt-br"
    return "en"


default_lang = "en" if LANG_MODE == "international" else "pt-br"
st.set_page_config(page_title=t(default_lang, "page_title"), layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: linear-gradient(180deg, #f4f7fb 0%, #ecf1f7 100%); color: #111827; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
        [data-testid="stSidebar"] * { color: #0f172a !important; }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] p {
            color: #0f172a !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
            background: #0b1220 !important;
            border: 1px solid #cbd5e1 !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] * {
            color: #ffffff !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }
        div[role="listbox"] * {
            color: #0f172a !important;
            opacity: 1 !important;
        }
        .app-head { border-radius: 12px; padding: 18px 22px; background: linear-gradient(130deg, #0b1f3a 0%, #122b4f 100%); margin-bottom: 14px; color: #f8fafc; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.20); }
        .app-sub { color: #cbd5e1; font-size: 0.92rem; margin-top: 4px; }
        .kpi-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; min-height: 110px; box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04); }
        .kpi-title { color: #64748b; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
        .kpi-value { color: #0f172a; font-size: 1.9rem; font-weight: 700; margin-top: 6px; }
        .kpi-sub { color: #64748b; font-size: 0.82rem; margin-top: 4px; }
        .note-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; color: #1f2937; }
        .kpi-card, .note-card { overflow-wrap: anywhere; word-break: break-word; }
        [data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 12px !important;
            padding: 12px 14px !important;
            box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04) !important;
        }
        [data-testid="stMetricLabel"] {
            color: #475569 !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricValue"] {
            color: #0f172a !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        [data-testid="stMetricDelta"] {
            color: #1e40af !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }
        [data-testid="stTabs"] [role="tablist"] { gap: 8px; }
        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 8px !important;
            background: #e2e8f0 !important;
            color: #0f172a !important;
            opacity: 1 !important;
            font-weight: 700 !important;
            border: 1px solid #cbd5e1 !important;
            padding: 8px 12px !important;
        }
        [data-testid="stTabs"] button[role="tab"] * {
            color: #0f172a !important;
            opacity: 1 !important;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: #1d4ed8 !important;
            border-color: #1e40af !important;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] * {
            color: #ffffff !important;
        }
        .stButton > button, .stDownloadButton > button,
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #1d4ed8 !important;
            background: #1d4ed8 !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }
        .stButton > button *, .stDownloadButton > button *,
        [data-testid="stSidebar"] .stButton > button * {
            color: #ffffff !important;
            opacity: 1 !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover,
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #1e40af !important;
            border-color: #1e40af !important;
            color: #ffffff !important;
        }
        .stButton > button:focus, .stDownloadButton > button:focus {
            outline: 2px solid #93c5fd;
            outline-offset: 1px;
        }
        @media (max-width: 900px) {
            .kpi-value { font-size: 1.35rem; }
            .kpi-title, .kpi-sub { font-size: 0.78rem; }
            .app-head { padding: 14px 16px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

processed_dir = PROJECT_ROOT / "data" / "processed"
rec, cohort, unit, report, outcomes, top10 = load_data(processed_dir)

with st.sidebar:
    if LANG_MODE == "bilingual":
        lang_option = st.selectbox(
            "Language / Idioma",
            ["International (EN)", "Portuguese (BR)"],
            index=1,
        )
        lang = normalize_lang(lang_option)
    else:
        lang = "en"
        st.caption("Language mode: international")

    st.header(t(lang, "filters"))
    if st.button(t(lang, "refresh"), use_container_width=True):
        run_pipeline(PipelineConfig.from_env(PROJECT_ROOT))
        st.rerun()

    segment_options = [t(lang, "all_segments")] + sorted(rec["segment"].dropna().unique().tolist())
    channel_options = [t(lang, "all_channels")] + sorted(rec["channel"].dropna().unique().tolist())
    action_options = [t(lang, "all_actions")] + sorted(
        rec["recommended_action"].dropna().unique().tolist()
    )

    selected_segment = st.selectbox(t(lang, "segment"), segment_options)
    selected_channel = st.selectbox(t(lang, "channel"), channel_options)
    selected_action = st.selectbox(t(lang, "action"), action_options)

st.markdown(
    f"""
    <div class="app-head">
        <h2 style="margin:0;">{t(lang, "header_title")}</h2>
        <div class="app-sub">{t(lang, "header_sub", dt=datetime.now().strftime("%d/%m/%Y %H:%M"))}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

df = rec.copy()
if selected_segment != t(lang, "all_segments"):
    df = df[df["segment"] == selected_segment]
if selected_channel != t(lang, "all_channels"):
    df = df[df["channel"] == selected_channel]
if selected_action != t(lang, "all_actions"):
    df = df[df["recommended_action"] == selected_action]

df = df.copy()
df["potential_impact"] = df.apply(potential_impact, axis=1)
if df.empty:
    st.warning(t(lang, "no_data"))
    st.stop()

st.subheader(t(lang, "summary"))
r1, r2, r3 = st.columns(3)
r1.markdown(
    card(t(lang, "customers"), f"{df['customer_id'].nunique():,}", t(lang, "active_base")),
    unsafe_allow_html=True,
)
r2.markdown(
    card(
        t(lang, "avg_ltv"), format_currency(float(df["ltv"].mean()), lang), t(lang, "per_customer")
    ),
    unsafe_allow_html=True,
)
r3.markdown(
    card(t(lang, "avg_risk"), f"{df['churn_probability'].mean():.1%}", t(lang, "churn_prob")),
    unsafe_allow_html=True,
)
r4, r5 = st.columns(2)
r4.markdown(
    card(t(lang, "efficiency"), f"{df['ltv_cac_ratio'].mean():.2f}", t(lang, "avg_efficiency")),
    unsafe_allow_html=True,
)
r5.markdown(
    card(
        t(lang, "impact"),
        format_currency(float(df["potential_impact"].sum()), lang),
        t(lang, "filtered_portfolio"),
    ),
    unsafe_allow_html=True,
)

risk_row = (
    df.groupby("segment")["churn_probability"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
    .iloc[0]
)
action_mix = df["recommended_action"].value_counts(normalize=True).mul(100).round(1).reset_index()
action_mix.columns = ["action", "pct"]
top_action = action_mix.iloc[0]
top_customer = df.sort_values("potential_impact", ascending=False).iloc[0]

st.markdown(f"#### {t(lang, 'board_read')}")
st.markdown(
    f"""
    <div class="note-card">
    {t(lang, "risk_line", segment=risk_row["segment"], risk=risk_row["churn_probability"])}<br/>
    {t(lang, "opp_line", customer=int(top_customer["customer_id"]), impact=format_currency(float(top_customer["potential_impact"]), lang))}<br/>
    {t(lang, "prio_line", action=top_action["action"], pct=top_action["pct"])}
    </div>
    """,
    unsafe_allow_html=True,
)

tab_overview, tab_risk, tab_action, tab_business = st.tabs(
    [
        t(lang, "tab_overview"),
        t(lang, "tab_risk_growth"),
        t(lang, "tab_action_list"),
        t(lang, "tab_business"),
    ]
)

with tab_action:
    board = df.sort_values("strategic_score", ascending=False).head(120)
    st.dataframe(board, use_container_width=True, hide_index=True, height=460)
    st.download_button(
        t(lang, "download"),
        board.to_csv(index=False).encode("utf-8"),
        file_name=t(lang, "board_file"),
        mime="text/csv",
    )

with tab_overview:
    left, right = st.columns(2)
    with left:
        action_dist = df["recommended_action"].value_counts().reset_index()
        action_dist.columns = [t(lang, "action"), t(lang, "customers")]
        fig1 = go.Figure(
            data=[
                go.Bar(
                    x=action_dist[t(lang, "action")],
                    y=action_dist[t(lang, "customers")],
                    marker_color=["#1e3a8a", "#1d4ed8", "#334155", "#0f172a"][: len(action_dist)],
                )
            ]
        )
        fig1.update_layout(title=t(lang, "action_distribution"), showlegend=False)
        st.plotly_chart(apply_chart_style(fig1), use_container_width=True, theme=None)

    with right:
        fig2 = px.bar(
            unit,
            x="channel",
            y="ltv_cac_ratio",
            color="channel",
            title=t(lang, "channel_efficiency"),
            color_discrete_sequence=["#1e3a8a", "#334155", "#475569", "#1d4ed8", "#0f172a"],
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(apply_chart_style(fig2), use_container_width=True, theme=None)

    cohort_hm = cohort.copy()
    cohort_hm["retention_pct"] = cohort_hm["retention_rate"] * 100
    heat = cohort_hm.pivot(
        index="cohort_month", columns="cohort_index", values="retention_pct"
    ).sort_index()
    fig3 = px.imshow(
        heat,
        aspect="auto",
        text_auto=".0f",
        title=t(lang, "cohort_retention"),
        labels={
            "x": t(lang, "months_since"),
            "y": t(lang, "cohort_label"),
            "color": t(lang, "retention"),
        },
        color_continuous_scale=[[0, "#e2e8f0"], [0.5, "#93c5fd"], [1, "#1e3a8a"]],
    )
    st.plotly_chart(apply_chart_style(fig3), use_container_width=True, theme=None)

with tab_risk:
    model_report = report.get("model_performance", report)
    gov = pd.DataFrame(
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
                t(lang, "split"): model_report.get("next_purchase_30d", {}).get(
                    "split_strategy", "n/a"
                ),
                t(lang, "cv_auc"): auc_text(
                    model_report.get("next_purchase_30d", {}).get("cv_roc_auc_mean")
                ),
                t(lang, "holdout_auc"): auc_text(
                    model_report.get("next_purchase_30d", {}).get("temporal_test_roc_auc")
                ),
            },
        ]
    )
    st.dataframe(gov, use_container_width=True, hide_index=True)
    st.caption(t(lang, "model_source"))

    rg1, rg2 = st.columns(2)
    with rg1:
        churn_seg = (
            df.groupby("segment", as_index=False)["churn_probability"]
            .mean()
            .sort_values("churn_probability", ascending=False)
        )
        fig_churn = px.bar(
            churn_seg,
            x="segment",
            y="churn_probability",
            color="segment",
            title=t(lang, "churn_by_segment"),
        )
        fig_churn.update_layout(showlegend=False, yaxis_tickformat=".0%")
        st.plotly_chart(apply_chart_style(fig_churn), use_container_width=True, theme=None)
    with rg2:
        next_channel = (
            df.groupby("channel", as_index=False)["next_purchase_probability"]
            .mean()
            .sort_values("next_purchase_probability", ascending=False)
        )
        fig_next = px.bar(
            next_channel,
            x="channel",
            y="next_purchase_probability",
            color="channel",
            title=t(lang, "next_by_channel"),
        )
        fig_next.update_layout(showlegend=False, yaxis_tickformat=".0%")
        st.plotly_chart(apply_chart_style(fig_next), use_container_width=True, theme=None)

with tab_business:
    business_kpis = outcomes.get("kpis", {})
    simulation = outcomes.get("simulation_summary_top10", {})
    channel_eff = pd.DataFrame(outcomes.get("ltv_cac_by_channel", []))

    b1, b2, b3 = st.columns(3)
    b1.markdown(
        card(
            t(lang, "business_ltv_cac"),
            f"{business_kpis.get('avg_ltv_cac_ratio', 0):.2f}",
            t(lang, "business_portfolio"),
        ),
        unsafe_allow_html=True,
    )
    b2.markdown(
        card(
            t(lang, "business_high_risk"),
            f"{business_kpis.get('high_churn_risk_pct', 0):.1%}",
            t(lang, "business_risk_customers"),
        ),
        unsafe_allow_html=True,
    )
    b3.markdown(
        card(
            t(lang, "business_net_impact"),
            format_currency(float(business_kpis.get("simulated_net_impact_top10", 0)), lang),
            t(lang, "business_net_impact_sub"),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(f"#### {t(lang, 'simulation')}")
    s1, s2 = st.columns(2)
    s1.metric(
        t(lang, "baseline"), format_currency(float(simulation.get("baseline_revenue_90d", 0)), lang)
    )
    s2.metric(
        t(lang, "scenario"), format_currency(float(simulation.get("scenario_revenue_90d", 0)), lang)
    )
    s3, s4 = st.columns(2)
    s3.metric(
        t(lang, "delta_revenue"),
        format_currency(float(simulation.get("delta_revenue_90d", 0)), lang),
    )
    s4.metric(t(lang, "roi"), f"{float(simulation.get('roi_simulated', 0)):.2f}x")

    c1, c2 = st.columns(2)
    with c1:
        if not channel_eff.empty:
            fig_eff = px.bar(
                channel_eff,
                x="channel",
                y="ltv_cac_ratio",
                color="channel",
                title=t(lang, "ltv_cac_channel"),
            )
            fig_eff.update_layout(showlegend=False)
            st.plotly_chart(apply_chart_style(fig_eff), use_container_width=True, theme=None)
    with c2:
        if not top10.empty:
            fig_impact = px.bar(
                top10.sort_values("net_impact", ascending=True),
                x="net_impact",
                y="customer_id",
                color="action",
                orientation="h",
                title=t(lang, "impact_customer"),
            )
            st.plotly_chart(apply_chart_style(fig_impact), use_container_width=True, theme=None)

    st.markdown(f"#### {t(lang, 'top_actions')}")
    st.dataframe(top10, use_container_width=True, hide_index=True, height=420)
