from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.branding import resolve_branding
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.dashboard_data import filter_recommendations, load_processed_assets
from app.dashboard_i18n import translate as t
from app.dashboard_metrics import potential_impact
from app.ui.primitives import render_global_styles
from app.views.dashboard_views import build_sidebar

LANG_MODE = os.getenv("RIP_APP_LANG_MODE", "bilingual").strip().lower()
if LANG_MODE not in {"bilingual", "international"}:
    LANG_MODE = "bilingual"


def prepare_page(page_title_key: str = "page_title") -> tuple[str, dict[str, Any], pd.DataFrame]:
    default_lang = "en" if LANG_MODE == "international" else "pt-br"
    branding = resolve_branding(
        default_app_name=t(default_lang, page_title_key),
        default_badge=t(default_lang, "header_badge"),
        default_footer_body=t(default_lang, "footer_body"),
    )
    st.set_page_config(
        page_title=branding.app_name,
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.session_state["rip_brand_badge"] = branding.hero_badge
    st.session_state["rip_brand_hero_title"] = branding.hero_title
    st.session_state["rip_brand_footer_title"] = branding.footer_title
    st.session_state["rip_brand_footer_body"] = branding.footer_body
    render_global_styles()

    processed_dir = PROJECT_ROOT / "data" / "processed"
    with st.spinner(t(default_lang, "loading")):
        assets = load_processed_assets(str(processed_dir))

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
    return lang, assets, filtered_df
