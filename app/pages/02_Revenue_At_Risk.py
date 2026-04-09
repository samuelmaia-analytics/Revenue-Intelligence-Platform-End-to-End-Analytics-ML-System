from __future__ import annotations

from app.dashboard_metrics import format_currency
from app.page_runtime import prepare_page
from app.views.dashboard_views import render_dashboard_footer, render_empty_dashboard, render_risk_tab


def main() -> None:
    lang, assets, filtered_df = prepare_page()
    if filtered_df.empty:
        render_empty_dashboard(lang)
        render_dashboard_footer(lang)
        return
    render_risk_tab(
        lang,
        filtered_df,
        assets["report"],
        assets["monitoring"],
        assets["alerts"],
        format_currency,
    )
    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
