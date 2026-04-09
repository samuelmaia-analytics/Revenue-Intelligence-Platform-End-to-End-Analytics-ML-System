from __future__ import annotations

from app.dashboard_i18n import translate as t
from app.dashboard_metrics import format_currency
from app.page_runtime import prepare_page
from app.ui.primitives import render_spacer
from app.views.dashboard_views import (
    render_dashboard_footer,
    render_empty_dashboard,
    render_filter_summary,
    render_header,
    render_leadership_notes,
    render_overview_tab,
    render_summary,
)


def main() -> None:
    lang, assets, filtered_df = prepare_page()
    if filtered_df.empty:
        render_empty_dashboard(lang)
        render_dashboard_footer(lang)
        return

    render_header(lang, filtered_df, format_currency)
    render_spacer("lg")
    render_filter_summary(
        lang,
        selected_segment=t(lang, "all_segments"),
        selected_channel=t(lang, "all_channels"),
        selected_action=t(lang, "all_actions"),
    )
    render_spacer("lg")
    render_summary(lang, filtered_df, format_currency)
    render_spacer("lg")
    render_leadership_notes(lang, filtered_df, format_currency, assets.get("insight_draft"))
    render_spacer("lg")
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
    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
