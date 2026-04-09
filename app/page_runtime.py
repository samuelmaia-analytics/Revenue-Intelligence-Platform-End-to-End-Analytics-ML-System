from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

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
    st.set_page_config(
        page_title=t(default_lang, page_title_key),
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
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
