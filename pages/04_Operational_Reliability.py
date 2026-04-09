from __future__ import annotations

import streamlit as st

from app.page_runtime import prepare_page
from app.views.dashboard_views import (
    render_dashboard_footer,
    render_empty_dashboard,
    render_reliability_tab,
)


def main() -> None:
    lang, assets, filtered_df = prepare_page()
    if filtered_df.empty:
        render_empty_dashboard(lang)
        render_dashboard_footer(lang)
        return
    render_reliability_tab(
        lang,
        assets["manifest"],
        assets["artifact_validation"],
        assets["freshness"],
        assets["alerts"],
    )
    reliability_report = assets.get("reliability_report", {})
    if reliability_report:
        st.json(reliability_report, expanded=False)
    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
