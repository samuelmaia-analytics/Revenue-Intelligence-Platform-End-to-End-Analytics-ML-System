from datetime import datetime
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from main import run_pipeline  # noqa: E402


def moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def auc_texto(valor: float | None) -> str:
    if valor is None:
        return "n/a"
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "n/a"
    if pd.isna(v):
        return "n/a"
    return f"{v:.3f}"


def impacto_potencial(row: pd.Series) -> float:
    acao = row["recommended_action"]
    if acao == "Retention Campaign":
        return row["ltv"] * row["churn_probability"] * 0.35
    if acao == "Upsell Offer":
        return row["ltv"] * row["next_purchase_probability"] * 0.15
    if acao == "Reduce Acquisition Spend":
        return row["cac"] * 0.50
    return row["ltv"] * row["next_purchase_probability"] * 0.03


def aplicar_estilo_figura(fig):
    fig.update_layout(
        template="plotly_white",
        font={"color": "#0f172a", "family": "Segoe UI, Aptos, Calibri, sans-serif", "size": 13},
        title_font={"color": "#0f172a", "size": 18},
        xaxis={"title_font": {"color": "#334155", "size": 12}, "tickfont": {"color": "#334155", "size": 12}},
        yaxis={"title_font": {"color": "#334155", "size": 12}, "tickfont": {"color": "#334155", "size": 12}},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def card(titulo: str, valor: str, subtitulo: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{titulo}</div>
        <div class="kpi-value">{valor}</div>
        <div class="kpi-sub">{subtitulo}</div>
    </div>
    """


def carregar(processed_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    arquivos = [
        "recommendations.csv",
        "cohort_retention.csv",
        "unit_economics.csv",
        "metrics_report.json",
    ]
    if not all((processed_dir / f).exists() for f in arquivos):
        run_pipeline()

    rec = pd.read_csv(processed_dir / "recommendations.csv")
    cohort = pd.read_csv(processed_dir / "cohort_retention.csv")
    unit = pd.read_csv(processed_dir / "unit_economics.csv")
    with (processed_dir / "metrics_report.json").open("r", encoding="utf-8") as f:
        report = json.load(f)
    return rec, cohort, unit, report


st.set_page_config(page_title="Painel Executivo de Receita", layout="wide")
st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f4f7fb 0%, #ecf1f7 100%);
            color: #111827;
            font-family: "Segoe UI", "Aptos", "Calibri", sans-serif;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
        .app-head {
            border-radius: 12px;
            padding: 18px 22px;
            background: linear-gradient(130deg, #0b1f3a 0%, #122b4f 100%);
            margin-bottom: 14px;
            color: #f8fafc;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.20);
        }
        .app-sub { color: #cbd5e1; font-size: 0.92rem; margin-top: 4px; }
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 14px 16px;
            min-height: 110px;
            box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
        }
        .kpi-title {
            color: #64748b;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 600;
        }
        .kpi-value { color: #0f172a; font-size: 1.9rem; font-weight: 700; margin-top: 6px; }
        .kpi-sub { color: #64748b; font-size: 0.82rem; margin-top: 4px; }
        .note-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 14px 16px;
            color: #1f2937;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            background: #e2e8f0;
            color: #0f172a;
            font-weight: 600;
            padding: 8px 14px;
        }
        .stButton > button, .stDownloadButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #1d4ed8;
            background: #1d4ed8;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.22);
            transition: all 0.18s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background: #1e40af;
            border-color: #1e40af;
            box-shadow: 0 7px 18px rgba(30, 64, 175, 0.28);
            transform: translateY(-1px);
        }
        .chart-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 10px 10px 2px 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="app-head">
        <h2 style="margin:0;">Painel Executivo de Receita</h2>
        <div class="app-sub">Revenue Intelligence Platform | Atualizado em {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

dir_proc = PROJECT_ROOT / "data" / "processed"
rec, cohort, unit, report = carregar(dir_proc)

with st.sidebar:
    st.header("Filtros")
    if st.button("Atualizar Base", use_container_width=True):
        run_pipeline()
        st.rerun()

    segs = ["Todos"] + sorted(rec["segment"].dropna().unique().tolist())
    canais = ["Todos"] + sorted(rec["channel"].dropna().unique().tolist())
    acoes = ["Todas"] + sorted(rec["recommended_action"].dropna().unique().tolist())

    seg = st.selectbox("Segmento", segs)
    canal = st.selectbox("Canal", canais)
    acao = st.selectbox("Ação", acoes)

df = rec.copy()
if seg != "Todos":
    df = df[df["segment"] == seg]
if canal != "Todos":
    df = df[df["channel"] == canal]
if acao != "Todas":
    df = df[df["recommended_action"] == acao]

df = df.copy()
df["impacto_potencial"] = df.apply(impacto_potencial, axis=1)

if df.empty:
    st.warning("Sem dados para os filtros selecionados.")
    st.stop()

st.subheader("Resumo Executivo")
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(card("Clientes", f"{df['customer_id'].nunique():,}", "base ativa"), unsafe_allow_html=True)
c2.markdown(card("LTV Médio", moeda(float(df["ltv"].mean())), "por cliente"), unsafe_allow_html=True)
c3.markdown(card("Risco Médio", f"{df['churn_probability'].mean():.1%}", "probabilidade de churn"), unsafe_allow_html=True)
c4.markdown(card("LTV/CAC", f"{df['ltv_cac_ratio'].mean():.2f}", "eficiência média"), unsafe_allow_html=True)
c5.markdown(card("Impacto Potencial", moeda(float(df["impacto_potencial"].sum())), "carteira filtrada"), unsafe_allow_html=True)

seg_risco = df.groupby("segment")["churn_probability"].mean().sort_values(ascending=False).reset_index().iloc[0]
acao_mix = df["recommended_action"].value_counts(normalize=True).mul(100).round(1).reset_index()
acao_mix.columns = ["ação", "pct"]
acao_top = acao_mix.iloc[0]
cliente_top = df.sort_values("impacto_potencial", ascending=False).iloc[0]

st.markdown("#### Leitura de Diretoria")
st.markdown(
    f"""
    <div class="note-card">
    <b>Risco:</b> {seg_risco['segment']} é o segmento mais exposto ({seg_risco['churn_probability']:.1%}).<br/>
    <b>Oportunidade:</b> cliente {int(cliente_top['customer_id'])} com impacto potencial de {moeda(float(cliente_top['impacto_potencial']))}.<br/>
    <b>Prioridade:</b> {acao_top['ação']} representa {acao_top['pct']:.1f}% do recorte atual.
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["Plano de Ação", "Performance", "Governança de Modelos"])

with tab1:
    board = df.sort_values("strategic_score", ascending=False).copy()
    board = board.rename(
        columns={
            "customer_id": "Cliente",
            "channel": "Canal",
            "segment": "Segmento",
            "ltv": "LTV Estimado",
            "cac": "CAC",
            "ltv_cac_ratio": "LTV/CAC",
            "churn_probability": "Risco de Churn",
            "next_purchase_probability": "Prob. Compra 30d",
            "strategic_score": "Score Estratégico",
            "recommended_action": "Ação Recomendada",
            "impacto_potencial": "Impacto Potencial (R$)",
        }
    )
    st.dataframe(
        board.head(120),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risco de Churn": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f"),
            "Prob. Compra 30d": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f"),
            "Score Estratégico": st.column_config.NumberColumn(format="%.3f"),
            "LTV/CAC": st.column_config.NumberColumn(format="%.2f"),
            "Impacto Potencial (R$)": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.download_button(
        "Baixar Carteira Priorizada (CSV)",
        board.to_csv(index=False).encode("utf-8"),
        file_name="carteira_priorizada.csv",
        mime="text/csv",
    )

with tab2:
    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        acao_dist = df["recommended_action"].value_counts().reset_index()
        acao_dist.columns = ["Ação", "Clientes"]
        paleta_exec = ["#1e3a8a", "#1d4ed8", "#334155", "#0f172a"]
        cores = paleta_exec[: len(acao_dist)]
        fig1 = go.Figure(
            data=[
                go.Bar(
                    x=acao_dist["Ação"],
                    y=acao_dist["Clientes"],
                    marker_color=cores,
                    marker_line_color="#0f172a",
                    marker_line_width=0.6,
                )
            ]
        )
        fig1.update_layout(title="Distribuição de Ações")
        fig1 = aplicar_estilo_figura(fig1)
        fig1.update_layout(showlegend=False, yaxis_title="Clientes", xaxis_title="Ação")
        st.plotly_chart(fig1, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    with p2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig2 = px.bar(
            unit,
            x="channel",
            y="ltv_cac_ratio",
            color="channel",
            color_discrete_sequence=["#1e3a8a", "#334155", "#475569", "#1d4ed8", "#0f172a"],
            title="Eficiência por Canal (LTV/CAC)",
        )
        fig2.update_traces(marker_line_color="#0f172a", marker_line_width=0.6, textposition="outside")
        fig2 = aplicar_estilo_figura(fig2)
        fig2.update_layout(showlegend=False, yaxis_title="LTV/CAC", xaxis_title="Canal")
        st.plotly_chart(fig2, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    cohort_hm = cohort.copy()
    cohort_hm["retention_pct"] = cohort_hm["retention_rate"] * 100
    heat = cohort_hm.pivot(index="cohort_month", columns="cohort_index", values="retention_pct").sort_index()
    fig3 = px.imshow(
        heat,
        aspect="auto",
        color_continuous_scale=[[0, "#e2e8f0"], [0.5, "#93c5fd"], [1, "#1e3a8a"]],
        text_auto=".0f",
        title="Retenção por Coorte (%)",
        labels={"x": "Mês desde aquisição", "y": "Coorte de aquisição", "color": "% Retenção"},
    )
    fig3 = aplicar_estilo_figura(fig3)
    fig3.update_layout(coloraxis_colorbar_title="%")
    st.plotly_chart(fig3, use_container_width=True, theme=None)
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    gov = pd.DataFrame(
        [
            {
                "Modelo": "Churn",
                "Split": report.get("churn", {}).get("split_strategy", "n/a"),
                "ROC-AUC CV": auc_texto(report.get("churn", {}).get("cv_roc_auc_mean")),
                "ROC-AUC Holdout": auc_texto(report.get("churn", {}).get("temporal_test_roc_auc")),
            },
            {
                "Modelo": "Next Purchase 30d",
                "Split": report.get("next_purchase_30d", {}).get("split_strategy", "n/a"),
                "ROC-AUC CV": auc_texto(report.get("next_purchase_30d", {}).get("cv_roc_auc_mean")),
                "ROC-AUC Holdout": auc_texto(report.get("next_purchase_30d", {}).get("temporal_test_roc_auc")),
            },
        ]
    )
    st.dataframe(gov, use_container_width=True, hide_index=True)
    st.caption("Fonte: data/processed/metrics_report.json")

