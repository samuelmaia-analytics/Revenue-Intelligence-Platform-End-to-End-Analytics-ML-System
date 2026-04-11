from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.dashboard_data import filter_customers, load_processed_assets, refresh_pipeline_outputs
from app.dashboard_metrics import format_currency
from app.ui.primitives import apply_chart_style, render_global_styles

SQL_SNIPPETS = {
    "overview": [
        ("Board de Receita", PROJECT_ROOT / "sql" / "olist" / "views" / "revenue_board.sql"),
        (
            "Extrato One-Pager",
            PROJECT_ROOT / "sql" / "olist" / "015_executive_one_pager_extract.sql",
        ),
    ],
    "customers": [
        ("Board de Retenção", PROJECT_ROOT / "sql" / "olist" / "views" / "retention_board.sql"),
        (
            "Matriz de Retenção por Ação",
            PROJECT_ROOT / "sql" / "olist" / "011_customer_retention_action_matrix.sql",
        ),
    ],
    "products": [
        (
            "Deep Dive de Categorias",
            PROJECT_ROOT / "sql" / "olist" / "012_category_performance_deep_dive.sql",
        ),
        (
            "Churn Proxy por Categoria",
            PROJECT_ROOT / "sql" / "olist" / "005_category_churn_proxy.sql",
        ),
    ],
    "sellers": [
        ("Board de Sellers", PROJECT_ROOT / "sql" / "olist" / "views" / "seller_board.sql"),
        ("Watchlist de Sellers", PROJECT_ROOT / "sql" / "olist" / "014_seller_watchlist.sql"),
    ],
    "operations": [
        (
            "Board de Operações",
            PROJECT_ROOT / "sql" / "olist" / "views" / "operations_board.sql",
        ),
        (
            "Resumo Mensal de Logística",
            PROJECT_ROOT / "sql" / "olist" / "007_logistics_monthly_summary.sql",
        ),
    ],
    "payments_geography": [
        (
            "Board de Geografia",
            PROJECT_ROOT / "sql" / "olist" / "views" / "geography_board.sql",
        ),
        (
            "Mix de Pagamentos",
            PROJECT_ROOT / "sql" / "olist" / "006_payment_mix_quality.sql",
        ),
    ],
    "reliability": [
        ("Board de Receita", PROJECT_ROOT / "sql" / "olist" / "views" / "revenue_board.sql"),
        (
            "Resumo Executivo Mensal",
            PROJECT_ROOT / "sql" / "olist" / "010_executive_monthly_summary.sql",
        ),
    ],
}

SQL_SNIPPET_HELP = {
    "overview": "Use esta área para baixar o SQL da leitura executiva e do extrato de one-pager.",
    "customers": "Consultas curadas para retenção, matriz de ações e leitura de risco do book de clientes.",
    "products": "Snippets para categorias, sortimento e proxy de churn por categoria.",
    "sellers": "Consultas curadas para sellers, concentração e watchlist operacional.",
    "operations": "Snippets para entrega, atraso e leitura mensal de logística.",
    "payments_geography": "Consultas para mix de pagamentos e oportunidade geográfica.",
    "reliability": "SQLs de apoio para leitura executiva e resumo mensal do ciclo publicado.",
}

PTBR_COLUMN_LABELS = {
    "customer_id": "Cliente",
    "customer_state": "Estado",
    "customer_city": "Cidade",
    "segment": "Segmento",
    "frequency": "Frequência",
    "monetary": "Receita",
    "ltv_proxy": "LTV proxy",
    "churn_probability": "Prob. churn",
    "next_purchase_probability": "Prob. próxima compra",
    "recommended_action": "Ação recomendada",
    "avg_review_score": "Nota média",
    "channel": "Canal",
    "total_revenue": "Receita total",
    "total_orders": "Pedidos",
    "avg_ticket": "Ticket médio",
    "late_delivery_rate": "Taxa de atraso",
    "on_time_delivery_rate": "Entrega no prazo",
    "avg_delivery_days": "Prazo médio",
    "median_delivery_days": "Prazo mediano",
    "revenue_per_customer": "Receita por cliente",
    "category": "Categoria",
    "category_tier": "Tier da categoria",
    "seller_id": "Seller",
    "seller_state": "UF seller",
    "seller_tier": "Tier do seller",
    "cohort_month": "Coorte",
    "cohort_index": "Mês da coorte",
    "retention_rate": "Retenção",
    "state": "Estado",
    "state_tier": "Tier do estado",
    "strategic_score": "Score estratégico",
    "order_month": "Mês",
    "top_state": "Estado líder",
    "top_category": "Categoria líder",
}

PTBR_VALUE_LABELS = {
    "Credit Card": "Cartão de Crédito",
    "Debit Card": "Cartão de Débito",
    "Boleto": "Boleto",
    "Voucher": "Voucher",
    "Other": "Outros",
    "Upsell Offer": "Oferta de Upsell",
    "Nurture": "Nutrição",
    "Retention Campaign": "Campanha de Retenção",
    "Reduce Acquisition Spend": "Reduzir Aquisição",
    "Champions": "Campeões",
    "Loyal": "Leais",
    "At Risk": "Em Risco",
    "Hibernating": "Hibernando",
    "Enterprise": "Enterprise",
    "Mid-Market": "Mid-Market",
    "SMB": "SMB",
    "Low": "Baixo",
    "Medium": "Médio",
    "High": "Alto",
    "Strategic": "Estratégico",
    "Core": "Core",
    "Long Tail": "Cauda Longa",
    "Hero": "Hero",
    "Tail": "Cauda",
    "Anchor": "Âncora",
    "Growth": "Crescimento",
    "Emerging": "Emergente",
}
PTBR_REVERSE_VALUE_LABELS = {value: key for key, value in PTBR_VALUE_LABELS.items()}


def _metric_card(title: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-caption">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _story_card(label: str, value: str, copy: str, kicker: bool = False) -> str:
    kicker_class = " kicker" if kicker else ""
    return f"""
        <div class="story-card{kicker_class}">
            <div class="story-label">{label}</div>
            <div class="story-value">{value}</div>
            <div class="story-copy">{copy}</div>
        </div>
    """


def _section_band(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-band">
            <div class="section-band-title">{title}</div>
            <div class="section-band-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_pct(value: float) -> str:
    return f"{value:.1%}"


def _ptbr_value(value: object) -> object:
    if isinstance(value, str):
        return PTBR_VALUE_LABELS.get(value, value)
    return value


def _canonical_value(value: object) -> object:
    if isinstance(value, str):
        return PTBR_REVERSE_VALUE_LABELS.get(value, value)
    return value


def _ptbr_frame(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    data = frame.copy()
    if columns is not None:
        data = data[[column for column in columns if column in data.columns]].copy()
    object_columns = data.select_dtypes(include=["object"]).columns.tolist()
    for column in object_columns:
        data[column] = data[column].map(_ptbr_value)
    return data.rename(columns=PTBR_COLUMN_LABELS)


def _render_sql_snippets(section_key: str) -> None:
    snippets = SQL_SNIPPETS.get(section_key, [])
    if not snippets:
        return
    with st.expander("Snippets SQL curados"):
        st.caption(SQL_SNIPPET_HELP.get(section_key, "Consultas prontas sobre os artefatos governados para demo e export técnico."))
        available = [(label, path) for label, path in snippets if path.exists()]
        if not available:
            st.info("Nenhum snippet SQL disponível nesta seção.")
            return
        labels = [label for label, _ in available]
        selected_label = st.selectbox(
            "Snippet disponível",
            labels,
            index=0,
            key=f"sql_snippet_select_{section_key}",
            label_visibility="collapsed",
        )
        selected_path = next(path for label, path in available if label == selected_label)
        sql_text = selected_path.read_text(encoding="utf-8")
        meta_cols = st.columns([0.68, 0.32])
        with meta_cols[0]:
            st.markdown(f"**{selected_label}**")
            st.caption(f"`{selected_path.relative_to(PROJECT_ROOT)}`")
        with meta_cols[1]:
            st.download_button(
                "Baixar SQL",
                data=sql_text,
                file_name=selected_path.name,
                mime="text/sql",
                use_container_width=True,
                key=f"download_sql_{section_key}_{selected_path.stem}",
            )
        if st.toggle("Ver SQL", value=False, key=f"show_sql_{section_key}_{selected_path.stem}"):
            st.code(sql_text, language="sql")


def _render_sql_reference() -> None:
    st.caption("SQL curado desta visão disponível na aba Confiabilidade.")


def _render_sql_console() -> None:
    with st.expander("SQL curado por tema"):
        st.caption("Central técnico com snippets SQL curados para demo, auditoria e export.")
        theme_options = [
            ("Resumo Executivo", "overview"),
            ("Clientes", "customers"),
            ("Produto e Categoria", "products"),
            ("Sellers", "sellers"),
            ("Operações", "operations"),
            ("Pagamentos e Geografia", "payments_geography"),
            ("Confiabilidade", "reliability"),
        ]
        theme_labels = [label for label, _ in theme_options]
        selected_theme_label = st.selectbox(
            "Tema técnico",
            theme_labels,
            index=0,
            key="sql_console_theme",
        )
        selected_theme = next(key for label, key in theme_options if label == selected_theme_label)
        available = [
            (label, path) for label, path in SQL_SNIPPETS.get(selected_theme, []) if path.exists()
        ]
        st.caption(SQL_SNIPPET_HELP.get(selected_theme, "Consultas técnicas disponíveis."))
        if not available:
            st.info("Nenhum snippet SQL disponível para o tema selecionado.")
            return
        snippet_labels = [label for label, _ in available]
        selected_label = st.selectbox(
            "Snippet",
            snippet_labels,
            index=0,
            key="sql_console_snippet",
        )
        selected_path = next(path for label, path in available if label == selected_label)
        sql_text = selected_path.read_text(encoding="utf-8")
        meta_cols = st.columns([0.68, 0.32])
        with meta_cols[0]:
            st.markdown(f"**{selected_label}**")
            st.caption(f"`{selected_path.relative_to(PROJECT_ROOT)}`")
        with meta_cols[1]:
            st.download_button(
                "Baixar SQL",
                data=sql_text,
                file_name=selected_path.name,
                mime="text/sql",
                use_container_width=True,
                key=f"download_sql_console_{selected_theme}_{selected_path.stem}",
            )


def _render_overview(assets: dict, filtered_customers: pd.DataFrame) -> None:
    kpis = assets["executive_kpis"]
    monthly = assets["summary_layer"].copy()
    categories = assets["categories"].head(8)
    states = assets["geography"].head(10)
    scorecard = assets.get("executive_scorecard", pd.DataFrame())
    customer_segment_health = assets.get("customer_segment_health", pd.DataFrame()).head(12)
    scorecard_row = scorecard.iloc[0] if not scorecard.empty else None

    cols = st.columns(4)
    with cols[0]:
        _metric_card("Receita Total", format_currency(kpis["total_revenue"], "pt-br"), "Receita entregue do marketplace")
    with cols[1]:
        _metric_card("Pedidos Totais", f"{kpis['total_orders']:,}", "Pedidos governados no recorte")
    with cols[2]:
        _metric_card("Ticket Médio", format_currency(kpis["average_ticket"], "pt-br"), "Valor médio por pedido entregue")
    with cols[3]:
        _metric_card("Clientes Recorrentes", _format_pct(kpis["recurring_customer_rate"]), "Clientes com comportamento recorrente")

    st.markdown(
        f"""
        <div class="story-grid">
            {_story_card("Postura de Crescimento", format_currency(float(monthly['total_revenue'].tail(1).iloc[0]), "pt-br"), "Receita do último mês publicada no scorecard executivo.", True)}
            {_story_card("Risco Operacional", _format_pct(kpis['late_delivery_rate']), "Atrasos seguem pressionando confiança comercial e satisfação.")}
            {_story_card("Sinal de Satisfação", f"{kpis['avg_review_score']:.2f} / 5", "A nota média agora faz parte da leitura curada de saúde do cliente.")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    _section_band(
        "Leitura executiva",
        "Esta página foi desenhada para deixar concentração, fricção operacional e qualidade da base claros em uma única leitura. Os gráficos abaixo usam os mesmos artefatos governados consumidos por warehouse e reports.",
    )

    narrative = st.columns([1.55, 1.05])
    with narrative[0]:
        fig = px.area(
            monthly,
            x="order_month",
            y="total_revenue",
            title="Trajetória de receita ao longo do ciclo do marketplace",
        )
        fig.update_traces(line_color="#0d5e54", fillcolor="rgba(13,94,84,0.18)")
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with narrative[1]:
        st.markdown("### Resumo executivo")
        st.markdown(
            f"""
            - A maior concentração de receita está em **{_ptbr_value(kpis.get('top_category', {}).get('category', 'n/a'))}**.
            - O estado líder no recorte é **{kpis.get('top_state', {}).get('state', 'n/a')}**.
            - A taxa de atraso está em **{kpis['late_delivery_rate']:.1%}**, com nota média de **{kpis['avg_review_score']:.2f} / 5**.
            - A ação dominante no recorte atual é **{_ptbr_value(filtered_customers['recommended_action'].mode().iat[0])}**.
            """
        )
        st.markdown("### Qualidade das regras de negócio")
        st.json(assets["quality_business_rules"]["checks"], expanded=False)

    row_two = st.columns(2)
    with row_two[0]:
        fig = px.bar(
            categories,
            x="total_revenue",
            y="category",
            orientation="h",
            title="Concentração de receita por categoria",
            color="avg_review_score",
            color_continuous_scale=["#d9ede8", "#0d5e54"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with row_two[1]:
        fig = px.bar(
            states,
            x="state",
            y="total_revenue",
            title="Participação dos estados na receita",
            color="late_delivery_rate",
            color_continuous_scale=["#e6f2ef", "#c48a3a", "#8c2f2f"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    bottom = st.columns([1.15, 0.85])
    with bottom[0]:
        if not customer_segment_health.empty:
            fig = px.bar(
                customer_segment_health,
                x="recommended_action",
                y="revenue_proxy",
                color="churn_risk_band",
                title="Exposição de receita por ação e faixa de churn",
                color_discrete_map={"Baixo": "#0d5e54", "Médio": "#c48a3a", "Alto": "#8c2f2f"},
            )
            fig.for_each_trace(lambda trace: trace.update(name=_ptbr_value(trace.name)))
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with bottom[1]:
        if scorecard_row is not None:
            st.markdown("### Concentração executiva")
            st.markdown(
                f"""
                - Receita recorrente: **{scorecard_row['repeat_revenue_share']:.1%}**
                - Retenção M+1: **{scorecard_row['m1_retention_rate']:.1%}**
                - Concentração top-10 sellers: **{scorecard_row['seller_top10_revenue_share']:.1%}**
                - Concentração top-10 categorias: **{scorecard_row['category_top10_revenue_share']:.1%}**
                """
            )
    _render_sql_reference()


def _render_customers(assets: dict, filtered_customers: pd.DataFrame) -> None:
    top_customers = filtered_customers.nlargest(15, "ltv_proxy")
    rfm = assets["rfm"]["segment"].value_counts().reset_index()
    rfm.columns = ["rfm_segment", "customers"]
    median_churn = filtered_customers["churn_probability"].median()
    high_value = filtered_customers["ltv_proxy"].quantile(0.75)
    watchlist = filtered_customers[
        (filtered_customers["churn_probability"] >= median_churn)
        & (filtered_customers["ltv_proxy"] >= high_value)
    ].head(10)

    _section_band(
        "Narrativa de inteligência de clientes",
        "A camada de clientes agora combina valor comercial, recência comportamental, qualidade de entrega e scoring supervisionado. Isso deixa a leitura mais útil e mais defensável em contexto executivo.",
    )

    cols = st.columns(2)
    with cols[0]:
        fig = px.scatter(
            filtered_customers,
            x="recency_days",
            y="monetary",
            color="recommended_action",
            size="ltv_proxy",
            hover_data=["customer_state", "segment", "avg_review_score"],
            title="Valor, recência e prioridade de ação",
            color_discrete_sequence=["#0d5e54", "#c48a3a", "#194a8d", "#8c2f2f"],
        )
        fig.for_each_trace(lambda trace: trace.update(name=_ptbr_value(trace.name)))
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        fig = px.bar(
            rfm,
            x="rfm_segment",
            y="customers",
            title="Distribuição dos segmentos comportamentais",
            color="customers",
            color_continuous_scale=["#edf5f3", "#0d5e54"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    if not watchlist.empty:
        st.markdown("### Watchlist prioritário de clientes")
        st.dataframe(
            _ptbr_frame(
                watchlist,
                [
                    "customer_id",
                    "customer_state",
                    "segment",
                    "frequency",
                    "monetary",
                    "ltv_proxy",
                    "churn_probability",
                    "next_purchase_probability",
                    "recommended_action",
                ],
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Clientes de maior valor no recorte")
    st.dataframe(
        _ptbr_frame(
            top_customers,
            [
                "customer_id",
                "customer_state",
                "segment",
                "frequency",
                "monetary",
                "ltv_proxy",
                "avg_review_score",
                "churn_probability",
                "next_purchase_probability",
                "recommended_action",
            ],
        ),
        use_container_width=True,
        hide_index=True,
    )
    _render_sql_reference()


def _render_commercial(assets: dict) -> None:
    payments = assets.get("payment_scorecard", assets["payments"])
    categories = assets.get("category_scorecard", assets["categories"]).head(12)
    sellers = assets.get("seller_scorecard", assets["sellers"]).head(12)

    _section_band(
        "Commercial structure",
        "This view explains where revenue comes from, how category participation is distributed and which sellers carry the marketplace economically.",
    )

    cols = st.columns(2)
    with cols[0]:
        fig = px.pie(
            payments,
            values="total_revenue",
            names="channel",
            title="Revenue mix by payment channel",
            hole=0.62,
            color_discrete_sequence=["#0d5e54", "#c48a3a", "#194a8d", "#8d6e63", "#d3dde6"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        fig = px.bar(
            categories,
            x="category",
            y="revenue_share_pct",
            title="Category participation in total revenue",
            color="avg_review_score",
            color_continuous_scale=["#e6f2ef", "#0d5e54"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    if not sellers.empty:
        fig = px.bar(
            sellers,
            x="seller_id",
            y="total_revenue",
            color="seller_state",
            title="Top sellers by revenue concentration",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def _render_products(assets: dict) -> None:
    categories = assets.get("category_scorecard", assets["categories"]).head(15)
    products = assets["products"].head(15)

    _section_band(
        "Analytics de produto e categoria",
        "Esta visão mostra onde o sortimento gera valor, onde o frete pressiona a economia e quais categorias combinam escala com satisfação.",
    )

    cols = st.columns(2)
    with cols[0]:
        if not categories.empty:
            fig = px.scatter(
                categories,
                x="avg_ticket",
                y="total_revenue",
                size="total_orders",
                color="category_tier" if "category_tier" in categories.columns else "category",
                hover_data=["category", "avg_review_score", "late_delivery_rate"],
                title="Escala, ticket e economia por categoria",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.for_each_trace(lambda trace: trace.update(name=_ptbr_value(trace.name)))
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        st.markdown("### Scorecard de categorias")
        if not categories.empty:
            st.dataframe(
                _ptbr_frame(
                    categories,
                    [
                        "category",
                        "category_tier",
                        "total_revenue",
                        "total_orders",
                        "avg_ticket",
                        "avg_review_score",
                        "late_delivery_rate",
                    ],
                ),
                use_container_width=True,
                hide_index=True,
            )

    if not products.empty:
        st.markdown("### Candidatos premium de sortimento")
        st.dataframe(
            _ptbr_frame(
                products.rename(columns={"product_id": "Produto", "category_name_english": "Categoria"}),
                ["Produto", "Categoria", "total_revenue", "total_orders", "avg_ticket", "avg_review_score"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    _render_sql_reference()


def _render_sellers(assets: dict) -> None:
    sellers = assets.get("seller_scorecard", assets["sellers"]).head(20)

    _section_band(
        "Performance e concentração de sellers",
        "A visão de sellers separa crescimento de dependência. Ela destaca quem move receita, quem pressiona atraso e onde a cauda longa ainda exige disciplina operacional.",
    )

    cols = st.columns(2)
    with cols[0]:
        if not sellers.empty:
            fig = px.scatter(
                sellers,
                x="late_delivery_rate",
                y="total_revenue",
                size="total_orders",
                color="seller_tier" if "seller_tier" in sellers.columns else "seller_state",
                hover_data=["seller_id", "seller_state", "avg_review_score"],
                title="Receita dos sellers versus risco operacional",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.for_each_trace(lambda trace: trace.update(name=_ptbr_value(trace.name)))
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        st.markdown("### Scorecard de sellers")
        if not sellers.empty:
            table_cols = [
                "seller_id",
                "seller_state",
                "seller_tier",
                "total_revenue",
                "total_orders",
                "avg_review_score",
                "late_delivery_rate",
            ]
            st.dataframe(
                _ptbr_frame(sellers, [col for col in table_cols if col in sellers.columns]),
                use_container_width=True,
                hide_index=True,
            )
    _render_sql_reference()


def _render_payments_geography(assets: dict) -> None:
    payments = assets.get("payment_scorecard", assets["payments"])
    states = assets.get("state_scorecard", assets["geography"]).head(15)

    _section_band(
        "Pagamentos e geografia",
        "Esta página conecta monetização com performance territorial. Ela ajuda a diagnosticar onde o marketplace ganha em conveniência, onde perde em serviço e onde priorizar ação regional.",
    )

    cols = st.columns(2)
    with cols[0]:
        if not payments.empty:
            fig = px.bar(
                payments,
                x="channel",
                y="total_revenue",
                color="on_time_delivery_rate",
                title="Receita por meio de pagamento com qualidade de entrega",
                color_continuous_scale=["#8c2f2f", "#c48a3a", "#0d5e54"],
            )
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        if not states.empty:
            fig = px.scatter(
                states,
                x="late_delivery_rate",
                y="total_revenue",
                size="unique_customers",
                color="state_tier" if "state_tier" in states.columns else "state",
                hover_data=["state", "avg_review_score", "revenue_per_customer"],
                title="Receita estadual versus risco de atraso",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.for_each_trace(lambda trace: trace.update(name=_ptbr_value(trace.name)))
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    st.markdown("### Scorecard geografico")
    st.dataframe(
        _ptbr_frame(
            states,
            [col for col in ["state", "state_tier", "total_revenue", "unique_customers", "revenue_per_customer", "avg_review_score", "late_delivery_rate"] if col in states.columns],
        ),
        use_container_width=True,
        hide_index=True,
    )
    _render_sql_reference()


def _render_operations(assets: dict) -> None:
    logistics = assets.get("operations_scorecard", assets["logistics"])
    cohort = assets.get("retention_scorecard", assets["cohort"]).copy()
    cohort["cohort_month"] = cohort["cohort_month"].astype(str)

    _section_band(
        "Entrega e retenção",
        "A leitura operacional não fica mais restrita ao churn. Eficiência de entrega, retenção por coorte e tendência de atraso agora convivem na mesma superfície decisória.",
    )

    cols = st.columns(2)
    with cols[0]:
        fig = px.line(
            logistics,
            x="order_month",
            y=["avg_delivery_days", "estimated_delivery_days"],
            title="Prazo real versus prazo prometido",
            color_discrete_sequence=["#0d5e54", "#c48a3a"],
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with cols[1]:
        fig = px.line(
            logistics,
            x="order_month",
            y="late_delivery_rate",
            title="Taxa de atraso ao longo do tempo",
            markers=True,
        )
        fig.update_traces(line_color="#8c2f2f")
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    bottom = st.columns(2)
    with bottom[0]:
        fig = px.line(
            cohort,
            x="cohort_index",
            y="retention_rate",
            color="cohort_month",
            title="Curvas de retenção por coorte",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    with bottom[1]:
        st.markdown("### Scorecard operacional mensal")
        st.dataframe(
            _ptbr_frame(
                logistics,
                [
                    "order_month",
                    "total_orders",
                    "avg_delivery_days",
                    "median_delivery_days",
                    "late_delivery_rate",
                    "on_time_delivery_rate",
                    "avg_review_score",
                ]
                if "median_delivery_days" in logistics.columns
                else None,
            ),
            use_container_width=True,
            hide_index=True,
        )
    _render_sql_reference()


def _render_reliability(assets: dict) -> None:
    _section_band(
        "Governança e evidências de runtime",
        "Esta aba sustenta a credibilidade do produto: o mesmo batch que alimenta a UI também publica validação, freshness, alertas e manifestos do ciclo.",
    )
    manifest = assets["manifest"]
    reliability = assets["reliability"]
    artifact_validation = assets["artifact_validation"]
    freshness = assets["freshness"]
    alerts = assets["alerts"]
    executive_report = assets["executive_report"]

    completed_at = manifest.get("completed_at_utc", "n/a")
    outputs = len(manifest.get("outputs", []))
    stage_timings = manifest.get("stage_timings_seconds", {})
    slowest_stage = (
        max(stage_timings.items(), key=lambda item: float(item[1])) if stage_timings else ("n/a", 0.0)
    )
    freshness_checks = pd.DataFrame(freshness.get("checks", []))
    alert_rows = pd.DataFrame(alerts.get("alerts", []))
    artifact_checks = pd.DataFrame(artifact_validation.get("checks", []))
    top_recommendations = pd.DataFrame(executive_report.get("recommendations_top_20", [])).head(10)

    cols = st.columns(4)
    with cols[0]:
        st.metric("Freshness", _ptbr_value(freshness["status"]))
    with cols[1]:
        st.metric("Validação de artefatos", _ptbr_value(artifact_validation["status"]))
    with cols[2]:
        st.metric("Alertas", alerts["alert_count"])
    with cols[3]:
        st.metric("Artefatos publicados", outputs)

    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.markdown("### Resumo do runtime")
        st.write(f"Concluído em: `{completed_at}`")
        st.write(f"Run id: `{manifest.get('run_id', 'n/a')}`")
        st.write(f"Ambiente: `{manifest.get('environment', 'n/a')}`")
    with summary_cols[1]:
        st.markdown("### Postura de confiabilidade")
        st.write(f"Status geral: `{reliability.get('status', 'n/a')}`")
        st.write(f"Estágio mais lento: `{slowest_stage[0]}`")
        st.write(f"Tempo: `{float(slowest_stage[1]):.2f}s`")
    with summary_cols[2]:
        st.markdown("### Sinal do artefato executivo")
        st.write(
            f"Clientes em escopo: `{executive_report.get('base_size', {}).get('customers_in_scope', 'n/a')}`"
        )
        st.write(
            f"Linhas de recomendação: `{executive_report.get('base_size', {}).get('rows_in_recommendation_table', 'n/a')}`"
        )
        st.write(
            f"Proxy de receita: `{format_currency(executive_report.get('business_context', {}).get('revenue_proxy', 0.0), 'pt-br')}`"
        )

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("### Checagens de freshness")
        if not freshness_checks.empty:
            st.dataframe(
                _ptbr_frame(
                    freshness_checks.rename(columns={"dataset_name": "Dataset", "status": "Status", "age_hours": "Idade (h)", "row_count": "Linhas", "source_updated_at_utc": "Atualizado em"}),
                    ["Dataset", "Status", "Idade (h)", "Linhas", "Atualizado em"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Nenhuma checagem de freshness disponível.")
    with detail_cols[1]:
        st.markdown("### Validação de artefatos")
        if not artifact_checks.empty:
            st.dataframe(
                _ptbr_frame(
                    artifact_checks.rename(columns={"artifact": "Artefato", "type": "Tipo"}),
                    ["Artefato", "Tipo"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Nenhuma checagem de artefato disponível.")

    lower_cols = st.columns(2)
    with lower_cols[0]:
        st.markdown("### Alertas ativos")
        if not alert_rows.empty:
            st.dataframe(
                _ptbr_frame(
                    alert_rows.rename(columns={"category": "Categoria", "severity": "Severidade", "message": "Mensagem"})
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("Nenhum alerta ativo no run atual.")
    with lower_cols[1]:
        st.markdown("### Principais recomendações executivas")
        if not top_recommendations.empty:
            st.dataframe(
                _ptbr_frame(
                    top_recommendations,
                    [
                        col
                        for col in [
                            "customer_id",
                            "segment",
                            "channel",
                            "recommended_action",
                            "strategic_score",
                        ]
                        if col in top_recommendations.columns
                    ],
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Nenhuma recomendação disponível.")

    with st.expander("Abrir manifesto do pipeline"):
        manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)
        st.markdown("**Artefato técnico**")
        st.write("Use o download abaixo para acessar o manifesto completo do pipeline.")
        st.download_button(
            "Baixar manifesto do pipeline",
            data=manifest_json,
            file_name="pipeline_manifest.json",
            mime="application/json",
            use_container_width=True,
        )
    with st.expander("Abrir artefato do report executivo"):
        executive_report_json = json.dumps(executive_report, ensure_ascii=False, indent=2)
        st.markdown("**Artefato técnico**")
        st.write("Use o download abaixo para acessar o payload completo do report executivo.")
        st.download_button(
            "Baixar relatório executivo",
            data=executive_report_json,
            file_name="executive_report.json",
            mime="application/json",
            use_container_width=True,
        )
    _render_sql_console()


def main() -> None:
    st.set_page_config(
        page_title="Revenue Intelligence Platform",
        page_icon=":material/insights:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_global_styles()

    processed_dir = PROJECT_ROOT / "data" / "processed"
    with st.spinner("Loading governed marketplace artifacts..."):
        assets = load_processed_assets(str(processed_dir))

    customers = assets["customers"]
    with st.sidebar:
        st.markdown("## Torre de Controle")
        st.caption("Navegação executiva sobre os outputs governados do batch Olist.")
        if st.button("Refresh pipeline", use_container_width=True):
            refresh_pipeline_outputs(PROJECT_ROOT)
            st.rerun()
        state_options = (
            ["Todos"] + sorted(customers["customer_state"].dropna().unique().tolist())
            if "customer_state" in customers.columns
            else ["Todos"]
        )
        segment_options = (
            ["Todos"] + sorted(customers["segment"].dropna().unique().tolist())
            if "segment" in customers.columns
            else ["Todos"]
        )
        action_options = (
            ["Todos"] + sorted(customers["recommended_action"].dropna().map(_ptbr_value).tolist())
            if "recommended_action" in customers.columns
            else ["Todos"]
        )
        state = st.selectbox("Estado", state_options)
        segment = st.selectbox("Segmento do cliente", segment_options)
        action = st.selectbox(
            "Ação recomendada",
            action_options,
        )
        st.markdown(
            f"""
            <div class="sidebar-block">
                <div class="sidebar-title">Recorte atual</div>
                <div class="sidebar-caption">A workspace reflete a carteira filtrada de clientes, enquanto os gráficos continuam ancorados nos marts governados.</div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">Clientes</div>
                    <div class="sidebar-stat-value">{customers['customer_id'].nunique():,}</div>
                </div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">Estado líder</div>
                    <div class="sidebar-stat-value">{assets['executive_kpis'].get('top_state', {}).get('state', 'n/a')}</div>
                </div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-label">Categoria líder</div>
                    <div class="sidebar-stat-value">{assets['executive_kpis'].get('top_category', {}).get('category', 'n/a')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    filtered_customers = filter_customers(
        customers,
        state="All" if state == "Todos" else state,
        segment="All" if segment == "Todos" else segment,
        action="All" if action == "Todos" else str(_canonical_value(action)),
    )

    top_action = (
        _ptbr_value(filtered_customers["recommended_action"].mode().iat[0])
        if not filtered_customers.empty and "recommended_action" in filtered_customers.columns
        else "n/a"
    )
    st.markdown(
        """
        <div class="hero">
            <div class="hero-grid">
                <div class="hero-copy">
                    <div>
                        <div class="hero-badge">Analytics Executiva Batch-First</div>
                        <h1>Inteligencia de receita para marketplace com leitura de diretoria.</h1>
                        <p>A aplicação agora se comporta como uma superfície analítica governada, em camadas e opinativa sobre o que a liderança deve ver primeiro em receita, clientes, operação e risco.</p>
                        <div class="hero-support">Fonte Olist • runtime batch governado • marts executivos • evidências operacionais</div>
                    </div>
                    <div class="hero-brief">
                        <div class="hero-brief-card">
                            <div class="hero-brief-label">Foco em Receita</div>
                            <div class="hero-brief-value">O scorecard destaca concentração, eficiência e comportamento recorrente.</div>
                        </div>
                        <div class="hero-brief-card">
                            <div class="hero-brief-label">Sinal Operacional</div>
                            <div class="hero-brief-value">Atraso de entrega e nota de review agora moldam a leitura analítica.</div>
                        </div>
                        <div class="hero-brief-card">
                            <div class="hero-brief-label">Credibilidade</div>
                            <div class="hero-brief-value">As métricas da interface leem os artefatos processados do runtime canônico.</div>
                        </div>
                    </div>
                </div>
                <div class="hero-meta">
                    <div class="hero-stat">
                        <div class="hero-stat-label">Clientes filtrados</div>
                        <div class="hero-stat-value">{:,}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Ação líder</div>
                        <div class="hero-stat-value">{}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Taxa de Atraso</div>
                        <div class="hero-stat-value">{:.1%}</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Nota Media</div>
                        <div class="hero-stat-value">{:.2f}</div>
                    </div>
                </div>
            </div>
        </div>
        """.format(
            filtered_customers["customer_id"].nunique(),
            top_action,
            assets["executive_kpis"]["late_delivery_rate"],
            assets["executive_kpis"]["avg_review_score"],
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Resumo Executivo",
            "Inteligência de Clientes",
            "Produto & Categoria",
            "Performance de Sellers",
            "Logística & Retenção",
            "Pagamentos & Geografia",
            "Confiabilidade",
        ]
    )
    with tabs[0]:
        _render_overview(assets, filtered_customers)
    with tabs[1]:
        _render_customers(assets, filtered_customers)
    with tabs[2]:
        _render_products(assets)
    with tabs[3]:
        _render_sellers(assets)
    with tabs[4]:
        _render_operations(assets)
    with tabs[5]:
        _render_payments_geography(assets)
    with tabs[6]:
        _render_reliability(assets)


if __name__ == "__main__":
    main()
