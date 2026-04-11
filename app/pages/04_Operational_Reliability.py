from __future__ import annotations

import json

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
        with st.expander("Open reliability report JSON"):
            payload = json.dumps(reliability_report, ensure_ascii=False, indent=2)
            st.markdown("**Technical artifact**")
            st.write("Use the download below for the full reliability report payload.")
            st.download_button(
                "Download reliability report",
                data=payload,
                file_name="reliability_report.json",
                mime="application/json",
                use_container_width=True,
            )
    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
