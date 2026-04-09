from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DEFAULT_THEME = {
    "bg": "#f3f6fb",
    "surface": "#ffffff",
    "surface_alt": "#f4f8fc",
    "surface_dark": "#0f172a",
    "border": "#c7d4e5",
    "text": "#0f172a",
    "muted": "#2f4057",
    "primary": "#0f5bd7",
    "primary_dark": "#0a3f97",
    "success": "#0f766e",
    "warning": "#b45309",
    "danger": "#b91c1c",
}


def apply_chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font={"color": DEFAULT_THEME["text"], "family": "Georgia, Cambria, Times New Roman, serif", "size": 13},
        title_font={"color": DEFAULT_THEME["text"], "size": 18},
        plot_bgcolor=DEFAULT_THEME["surface"],
        paper_bgcolor=DEFAULT_THEME["surface"],
        margin={"l": 24, "r": 24, "t": 56, "b": 24},
        title_x=0.02,
    )
    fig.update_xaxes(gridcolor="#edf2f7")
    fig.update_yaxes(gridcolor="#edf2f7")
    return fig


def render_global_styles() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background:
                    radial-gradient(circle at top right, rgba(15, 91, 215, 0.12), transparent 26%),
                    radial-gradient(circle at bottom left, rgba(10, 63, 151, 0.07), transparent 28%),
                    linear-gradient(180deg, {DEFAULT_THEME["bg"]} 0%, #e9f0f7 100%);
                color: {DEFAULT_THEME["text"]};
                font-family: "Aptos", "Segoe UI", sans-serif;
            }}
            [data-testid="stHeader"] {{ background: transparent; }}
            [data-testid="stMainBlockContainer"] {{
                padding-top: 1.2rem;
                padding-bottom: 2.5rem;
                padding-left: 2rem;
                padding-right: 1.25rem;
                max-width: 1440px;
            }}
            [data-testid="stSidebar"] {{
                background: rgba(255, 255, 255, 0.92);
                border-right: 1px solid rgba(199, 212, 229, 0.72);
                box-shadow: 10px 0 28px rgba(15, 23, 42, 0.04);
            }}
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 1rem;
                padding-right: 1rem;
            }}
            [data-testid="stWidgetLabel"] {{
                color: {DEFAULT_THEME["text"]} !important;
                font-weight: 800 !important;
            }}
            [data-testid="stWidgetLabel"] p {{
                color: {DEFAULT_THEME["text"]} !important;
                font-weight: 800 !important;
            }}
            [data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{
                color: {DEFAULT_THEME["muted"]} !important;
                opacity: 1 !important;
            }}
            .section-label {{
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
                color: {DEFAULT_THEME["primary"]};
                margin-bottom: 0.3rem;
            }}
            .section-head {{
                margin: 0.25rem 0 0.85rem 0;
            }}
            .section-title {{
                font-size: 1.42rem;
                font-weight: 800;
                color: {DEFAULT_THEME["text"]};
                line-height: 1.15;
            }}
            .section-caption {{
                color: {DEFAULT_THEME["muted"]};
                margin-top: 0.15rem;
                line-height: 1.45;
            }}
            .hero {{
                position: relative;
                overflow: hidden;
                padding: 1.6rem 1.8rem;
                border-radius: 28px;
                background:
                    radial-gradient(circle at top right, rgba(255,255,255,0.14), transparent 26%),
                    linear-gradient(135deg, rgba(10, 63, 151, 0.98), rgba(15, 91, 215, 0.92)),
                    linear-gradient(180deg, #0b1b35, #143259);
                color: #f8fbff;
                border: 1px solid rgba(255,255,255,0.08);
                box-shadow: 0 28px 70px rgba(15, 23, 42, 0.18);
            }}
            .hero::after {{
                content: "";
                position: absolute;
                right: -4rem;
                top: -4rem;
                width: 16rem;
                height: 16rem;
                border-radius: 999px;
                background: radial-gradient(circle, rgba(255,255,255,0.16), transparent 62%);
            }}
            .hero-grid {{
                display: grid;
                grid-template-columns: 1.5fr 1fr;
                gap: 1.2rem;
                align-items: start;
            }}
            .hero-badge {{
                display: inline-block;
                padding: 0.42rem 0.72rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.14);
                border: 1px solid rgba(255,255,255,0.08);
                font-size: 0.74rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.85rem;
            }}
            .hero h1 {{
                margin: 0;
                font-family: "Georgia", "Times New Roman", serif;
                font-size: 2.35rem;
                line-height: 1.08;
                font-weight: 800;
                letter-spacing: -0.03em;
                max-width: 10ch;
            }}
            .hero p {{
                margin: 0.65rem 0 0 0;
                color: rgba(248, 251, 255, 0.92);
                font-size: 1rem;
                line-height: 1.65;
                max-width: 60ch;
            }}
            .hero-support {{
                margin-top: 1rem;
                max-width: 64ch;
                color: rgba(255,255,255,0.78);
                font-size: 0.84rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
            }}
            .hero-brief {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin-top: 1.15rem;
            }}
            .hero-brief-card {{
                padding: 0.9rem 1rem;
                border-radius: 18px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.08);
                backdrop-filter: blur(8px);
            }}
            .hero-brief-label {{
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                color: rgba(248, 251, 255, 0.72);
            }}
            .hero-brief-value {{
                margin-top: 0.3rem;
                font-size: 0.98rem;
                font-weight: 800;
                color: #ffffff;
                line-height: 1.25;
            }}
            .hero-meta {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.8rem;
                position: relative;
                z-index: 1;
            }}
            .hero-stat {{
                min-width: 150px;
                padding: 0.95rem 1rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255,255,255,0.08);
                backdrop-filter: blur(10px);
            }}
            .hero-stat-label {{
                font-size: 0.72rem;
                color: rgba(248, 251, 255, 0.78);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
            }}
            .hero-stat-value {{
                font-size: 1.35rem;
                font-weight: 800;
                margin-top: 0.28rem;
                line-height: 1.15;
            }}
            .panel {{
                background: rgba(255,255,255,0.97);
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 20px;
                padding: 1.15rem;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
            }}
            .panel-head {{
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
                margin-bottom: 0.9rem;
            }}
            .panel-title {{
                color: {DEFAULT_THEME["text"]};
                font-size: 1.08rem;
                font-weight: 800;
                line-height: 1.2;
            }}
            .panel-caption {{
                color: {DEFAULT_THEME["muted"]};
                font-size: 0.88rem;
                margin-top: 0.15rem;
                line-height: 1.45;
            }}
            .status-strip {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.85rem;
                margin: 1rem 0 1.25rem 0;
            }}
            .status-card {{
                background: rgba(255,255,255,0.98);
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 18px;
                padding: 0.95rem 1rem;
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
            }}
            .status-label {{
                color: {DEFAULT_THEME["muted"]};
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.72rem;
                font-weight: 800;
            }}
            .status-value {{
                color: {DEFAULT_THEME["text"]};
                font-size: 1.12rem;
                font-weight: 800;
                margin-top: 0.32rem;
                line-height: 1.2;
            }}
            .status-sub {{
                color: {DEFAULT_THEME["muted"]};
                font-size: 0.84rem;
                margin-top: 0.25rem;
                line-height: 1.4;
            }}
            .status-pill {{
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.36rem 0.62rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 800;
                border: 1px solid {DEFAULT_THEME["border"]};
                background: rgba(15, 91, 215, 0.08);
                color: {DEFAULT_THEME["primary_dark"]};
                white-space: nowrap;
            }}
            .status-pill.success {{
                background: rgba(15, 118, 110, 0.1);
                color: {DEFAULT_THEME["success"]};
                border-color: rgba(15, 118, 110, 0.18);
            }}
            .status-pill.warning {{
                background: rgba(180, 83, 9, 0.1);
                color: {DEFAULT_THEME["warning"]};
                border-color: rgba(180, 83, 9, 0.18);
            }}
            .status-pill.danger {{
                background: rgba(185, 28, 28, 0.1);
                color: {DEFAULT_THEME["danger"]};
                border-color: rgba(185, 28, 28, 0.18);
            }}
            .kpi-card {{
                background: linear-gradient(180deg, {DEFAULT_THEME["surface"]}, {DEFAULT_THEME["surface_alt"]});
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 20px;
                padding: 1.05rem;
                min-height: 126px;
                box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            }}
            .kpi-title {{
                color: {DEFAULT_THEME["muted"]};
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
            }}
            .kpi-value {{
                color: {DEFAULT_THEME["text"]};
                font-size: 1.85rem;
                font-weight: 800;
                margin-top: 0.45rem;
                line-height: 1.1;
            }}
            .kpi-sub {{ color: {DEFAULT_THEME["muted"]}; font-size: 0.86rem; margin-top: 0.35rem; }}
            .insight-list {{ margin: 0; padding-left: 1rem; color: {DEFAULT_THEME["text"]}; }}
            .insight-list li {{ margin-bottom: 0.55rem; line-height: 1.45; }}
            .empty-state {{
                padding: 2rem 1.5rem;
                text-align: center;
                border-radius: 20px;
                border: 1px dashed {DEFAULT_THEME["border"]};
                background: rgba(255,255,255,0.72);
            }}
            .footer {{
                margin-top: 1.25rem;
                padding: 1rem 1.15rem;
                border-radius: 18px;
                background: rgba(15, 23, 42, 0.96);
                color: #e2e8f0;
            }}
            .footer-title {{ font-weight: 800; margin-bottom: 0.2rem; }}
            .sidebar-block {{
                padding: 0.9rem 0.95rem;
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 16px;
                background: linear-gradient(180deg, #ffffff, #f6faff);
                margin-bottom: 0.95rem;
            }}
            .sidebar-title {{
                font-size: 0.83rem;
                font-weight: 800;
                color: {DEFAULT_THEME["text"]};
                margin-bottom: 0.25rem;
            }}
            .sidebar-caption {{ font-size: 0.82rem; color: {DEFAULT_THEME["muted"]}; margin-bottom: 0.7rem; }}
            .sidebar-stat {{
                display: grid;
                gap: 0.15rem;
                padding: 0.7rem 0.75rem;
                border-radius: 14px;
                background: #f8fbff;
                border: 1px solid {DEFAULT_THEME["border"]};
                margin-top: 0.55rem;
            }}
            .sidebar-stat-label {{
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {DEFAULT_THEME["muted"]};
            }}
            .sidebar-stat-value {{
                font-size: 0.95rem;
                font-weight: 800;
                color: {DEFAULT_THEME["text"]};
            }}
            [data-testid="stMetric"] {{
                background: linear-gradient(180deg, #ffffff, #f8fbff) !important;
                border: 1px solid {DEFAULT_THEME["border"]} !important;
                border-radius: 16px !important;
                padding: 0.8rem 0.95rem !important;
            }}
            [data-testid="stMetricLabel"] {{
                font-weight: 800 !important;
                color: {DEFAULT_THEME["muted"]} !important;
            }}
            [data-testid="stMetricValue"] {{
                color: {DEFAULT_THEME["text"]} !important;
                font-weight: 800 !important;
                line-height: 1.15 !important;
            }}
            [data-testid="stMetricDelta"] {{
                color: {DEFAULT_THEME["primary_dark"]} !important;
            }}
            [data-testid="stTabs"] [role="tablist"] {{ gap: 0.5rem; margin-bottom: 0.75rem; }}
            [data-testid="stTabs"] button[role="tab"] {{
                border-radius: 999px !important;
                padding: 0.55rem 0.95rem !important;
                border: 1px solid {DEFAULT_THEME["border"]} !important;
                background: rgba(255,255,255,0.98) !important;
                color: {DEFAULT_THEME["text"]} !important;
                font-weight: 800 !important;
            }}
            [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: {DEFAULT_THEME["primary"]} !important;
                border-color: {DEFAULT_THEME["primary"]} !important;
            }}
            [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {{ color: #ffffff !important; }}
            .stButton > button, .stDownloadButton > button {{
                width: 100%;
                border-radius: 12px;
                border: 1px solid {DEFAULT_THEME["primary"]} !important;
                background: {DEFAULT_THEME["primary"]} !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                min-height: 2.8rem;
            }}
            div[data-baseweb="select"] {{
                border-radius: 12px !important;
                border-color: {DEFAULT_THEME["border"]} !important;
                background: #ffffff !important;
                color: {DEFAULT_THEME["text"]} !important;
            }}
            div[data-baseweb="select"] > div {{
                background: #ffffff !important;
                border-color: {DEFAULT_THEME["border"]} !important;
                color: {DEFAULT_THEME["text"]} !important;
                box-shadow: none !important;
            }}
            div[data-baseweb="select"] > div:hover {{
                border-color: {DEFAULT_THEME["primary"]} !important;
            }}
            div[data-baseweb="select"] span {{
                color: {DEFAULT_THEME["text"]} !important;
            }}
            div[data-baseweb="select"] input {{
                color: {DEFAULT_THEME["text"]} !important;
                -webkit-text-fill-color: {DEFAULT_THEME["text"]} !important;
            }}
            div[data-baseweb="select"] svg {{
                fill: {DEFAULT_THEME["text"]} !important;
                color: {DEFAULT_THEME["text"]} !important;
            }}
            div[data-baseweb="select"] * {{
                color: {DEFAULT_THEME["text"]} !important;
            }}
            input, textarea {{
                color: {DEFAULT_THEME["text"]} !important;
            }}
            [data-testid="stExpander"] {{
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 18px;
                background: rgba(255,255,255,0.98);
            }}
            [data-testid="stExpander"] summary,
            [data-testid="stExpander"] summary * {{
                color: {DEFAULT_THEME["text"]} !important;
                font-weight: 700 !important;
            }}
            [data-testid="stDataFrame"] {{
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 18px;
                overflow: hidden;
            }}
            [data-testid="stDataFrame"] * {{
                color: {DEFAULT_THEME["text"]} !important;
            }}
            .table-shell {{
                border: 1px solid {DEFAULT_THEME["border"]};
                border-radius: 18px;
                overflow: hidden;
                background: rgba(255,255,255,0.99);
            }}
            .table-scroll {{
                overflow-x: auto;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.92rem;
            }}
            .data-table th {{
                background: #f8fbff;
                color: {DEFAULT_THEME["muted"]};
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-size: 0.72rem;
                font-weight: 800;
                padding: 0.8rem 0.9rem;
                border-bottom: 1px solid {DEFAULT_THEME["border"]};
                text-align: left;
                white-space: nowrap;
            }}
            .data-table td {{
                padding: 0.82rem 0.9rem;
                border-bottom: 1px solid #edf2f7;
                color: {DEFAULT_THEME["text"]};
                vertical-align: top;
            }}
            .data-table tr:last-child td {{
                border-bottom: none;
            }}
            .table-badge {{
                display: inline-flex;
                align-items: center;
                padding: 0.24rem 0.55rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 800;
                line-height: 1;
                border: 1px solid {DEFAULT_THEME["border"]};
                background: rgba(15, 91, 215, 0.08);
                color: {DEFAULT_THEME["primary_dark"]};
            }}
            .table-badge.success {{
                background: rgba(15, 118, 110, 0.1);
                color: {DEFAULT_THEME["success"]};
                border-color: rgba(15, 118, 110, 0.18);
            }}
            .table-badge.warning {{
                background: rgba(180, 83, 9, 0.1);
                color: {DEFAULT_THEME["warning"]};
                border-color: rgba(180, 83, 9, 0.18);
            }}
            .table-badge.danger {{
                background: rgba(185, 28, 28, 0.1);
                color: {DEFAULT_THEME["danger"]};
                border-color: rgba(185, 28, 28, 0.18);
            }}
            .block-spacer {{
                height: 0.45rem;
            }}
            .block-spacer.lg {{
                height: 0.9rem;
            }}
            @media (max-width: 980px) {{
                [data-testid="stMainBlockContainer"] {{
                    padding-left: 1rem;
                    padding-right: 1rem;
                }}
                .hero-grid {{ grid-template-columns: 1fr; }}
                .hero-meta {{ grid-template-columns: 1fr; }}
                .hero-brief {{ grid-template-columns: 1fr; }}
                .status-strip {{ grid-template-columns: 1fr 1fr; }}
                .panel-head {{ flex-direction: column; }}
                .section-title {{ font-size: 1.24rem; }}
                .data-table {{
                    font-size: 0.88rem;
                }}
                .data-table th, .data-table td {{
                    padding: 0.72rem 0.7rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(eyebrow: str, title: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-label">{eyebrow}</div>
            <div class="section-title">{title}</div>
            <div class="section-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(title: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(eyebrow: str, title: str, caption: str, pill: str | None = None) -> None:
    pill_markup = f'<div class="status-pill">{pill}</div>' if pill else ""
    st.markdown(
        f"""
        <div class="panel-head">
            <div>
                <div class="section-label">{eyebrow}</div>
                <div class="panel-title">{title}</div>
                <div class="panel-caption">{caption}</div>
            </div>
            {pill_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_strip(items: list[dict[str, str]]) -> None:
    if not items:
        return

    columns = st.columns(len(items))
    for column, item in zip(columns, items, strict=False):
        with column:
            st.markdown(
                f"""
                <div class="status-card">
                    <div class="status-label">{escape(str(item["label"]))}</div>
                    <div class="status-value">{escape(str(item["value"]))}</div>
                    <div class="status-sub">{escape(str(item["subtitle"]))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_status_pill(label: str, value: str, tone: str = "neutral") -> None:
    tone_class = tone if tone in {"success", "warning", "danger"} else ""
    st.markdown(
        f'<div class="status-pill {tone_class}">{label}: {value}</div>',
        unsafe_allow_html=True,
    )


def render_chart_panel(
    *,
    eyebrow: str,
    title: str,
    caption: str,
    fig: go.Figure,
) -> None:
    render_panel_header(eyebrow, title, caption)
    st.plotly_chart(apply_chart_style(fig), use_container_width=True, theme=None)


def render_dataframe_panel(
    *,
    eyebrow: str,
    title: str,
    caption: str,
    frame: pd.DataFrame | pd.io.formats.style.Styler,
    height: int | None = None,
) -> None:
    render_panel_header(eyebrow, title, caption)
    dataframe_kwargs: dict[str, object] = {
        "use_container_width": True,
        "hide_index": True,
    }
    if height is not None:
        dataframe_kwargs["height"] = height
    st.dataframe(frame, **dataframe_kwargs)


def _badge_tone(value: str) -> str:
    text = value.strip().lower()
    if text in {"ok", "success", "healthy", "fresh", "approved", "low"}:
        return "success"
    if text in {"warning", "warn", "stale", "medium"}:
        return "warning"
    if text in {"error", "failed", "critical", "high"}:
        return "danger"
    return ""


def render_badge_table_panel(
    *,
    eyebrow: str,
    title: str,
    caption: str,
    frame: pd.DataFrame,
    badge_columns: list[str] | None = None,
) -> None:
    render_panel_header(eyebrow, title, caption)
    badge_columns = badge_columns or []
    if frame.empty:
        st.caption("No rows available.")
        return

    header_html = "".join(f"<th>{escape(str(column))}</th>" for column in frame.columns)
    rows_html: list[str] = []
    for _, row in frame.iterrows():
        cells: list[str] = []
        for column in frame.columns:
            value = "" if pd.isna(row[column]) else str(row[column])
            if column in badge_columns:
                tone_class = _badge_tone(value)
                cell = (
                    f'<span class="table-badge {tone_class}">{escape(value)}</span>'
                    if value
                    else ""
                )
            else:
                cell = escape(value)
            cells.append(f"<td>{cell}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"""
        <div class="table-shell">
            <div class="table-scroll">
                <table class="data-table">
                    <thead><tr>{header_html}</tr></thead>
                    <tbody>{''.join(rows_html)}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div style="font-size:1.15rem;font-weight:800;color:{DEFAULT_THEME["text"]};">
                {title}
            </div>
            <div style="margin-top:0.4rem;color:{DEFAULT_THEME["muted"]};">
                {body}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(title: str, body: str, timestamp_label: str) -> None:
    st.markdown(
        f"""
        <div class="footer">
            <div class="footer-title">{title}</div>
            <div>{body}</div>
            <div style="margin-top:0.45rem;color:#94a3b8;">{timestamp_label.format(dt=datetime.now().strftime("%d/%m/%Y %H:%M"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_spacer(size: str = "md") -> None:
    size_class = " lg" if size == "lg" else ""
    st.markdown(f'<div class="block-spacer{size_class}"></div>', unsafe_allow_html=True)
