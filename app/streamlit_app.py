from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# ruff: noqa: E402, I001



PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.dashboard_data import filter_recommendations, load_processed_assets
from app.dashboard_i18n import translate as t
from app.dashboard_metrics import format_currency, potential_impact
from app.ui.primitives import render_global_styles, render_spacer
from app.views.dashboard_views import (
    build_sidebar,
    render_action_tab,
    render_business_tab,
    render_dashboard_footer,
    render_empty_dashboard,
    render_filter_summary,
    render_header,
    render_leadership_notes,
    render_overview_tab,
    render_risk_tab,
    render_summary,
)

LANG_MODE = os.getenv("RIP_APP_LANG_MODE", "bilingual").strip().lower()
if LANG_MODE not in {"bilingual", "international"}:
    LANG_MODE = "bilingual"


def main() -> None:
    default_lang = "en" if LANG_MODE == "international" else "pt-br"
    st.set_page_config(
        page_title=t(default_lang, "page_title"),
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_global_styles()

    processed_dir = PROJECT_ROOT / "data" / "processed"
    try:
        with st.spinner(t(default_lang, "loading")):
            assets = load_processed_assets(str(processed_dir))
    except Exception as error:  # pragma: no cover
        st.error(f"{t(default_lang, 'error_title')}: {error}")
        st.caption(t(default_lang, "error_body"))
        return

    recommendations = assets["recommendations"]
    lang, selected_segment, selected_channel, selected_action = build_sidebar(
        lang=default_lang,
        lang_mode=LANG_MODE,
        recommendations=recommendations,
        project_root=PROJECT_ROOT,
    )
    filtered_df = filter_recommendations(
        recommendations,
        segment=selected_segment,
        channel=selected_channel,
        action=selected_action,
        all_segments_label=t(lang, "all_segments"),
        all_channels_label=t(lang, "all_channels"),
        all_actions_label=t(lang, "all_actions"),
        potential_impact_fn=potential_impact,
    )

    if filtered_df.empty:
        baseline_df = recommendations.copy()
        baseline_df["potential_impact"] = baseline_df.apply(potential_impact, axis=1)
        render_header(lang, baseline_df, format_currency)
        render_empty_dashboard(lang)
        render_dashboard_footer(lang)
        return

    with st.container():
        render_header(lang, filtered_df, format_currency)
    render_spacer("lg")
    with st.container():
        render_filter_summary(
            lang,
            selected_segment=selected_segment,
            selected_channel=selected_channel,
            selected_action=selected_action,
        )
    render_spacer("lg")
    with st.container():
        render_summary(lang, filtered_df, format_currency)
    render_spacer("lg")
    with st.container():
        render_leadership_notes(lang, filtered_df, format_currency)
    render_spacer("lg")

    overview_tab, risk_tab, action_tab, business_tab = st.tabs(
        [
            t(lang, "tab_overview"),
            t(lang, "tab_risk_growth"),
            t(lang, "tab_action_list"),
            t(lang, "tab_business"),
        ]
    )

    with overview_tab:
        with st.container():
            render_overview_tab(
                lang,
                filtered_df,
                assets["unit"],
                assets["cohort"],
                assets["report"],
                assets["manifest"],
                assets["artifact_validation"],
                assets["freshness"],
                assets["alerts"],
                format_currency,
            )
    with risk_tab:
        with st.container():
            render_risk_tab(
                lang, filtered_df, assets["report"], assets["monitoring"], assets["alerts"]
            )
    with action_tab:
        with st.container():
            render_action_tab(
                lang=lang,
                filtered_df=filtered_df,
                approved_actions=assets["approved_actions"],
                project_root=PROJECT_ROOT,
            )
    with business_tab:
        with st.container():
            render_business_tab(
                lang=lang,
                filtered_df=filtered_df,
                outcomes=assets["outcomes"],
                top10=assets["top10"],
                semantic_metrics=assets["semantic_metrics"],
                format_currency_fn=format_currency,
            )

    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
