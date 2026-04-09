from __future__ import annotations

from app.page_runtime import prepare_page
from app.views.dashboard_views import (
    render_dashboard_footer,
    render_empty_dashboard,
    render_governance_tab,
)


def main() -> None:
    lang, assets, filtered_df = prepare_page()
    if filtered_df.empty:
        render_empty_dashboard(lang)
        render_dashboard_footer(lang)
        return
    render_governance_tab(
        lang,
        assets["report"],
        assets["monitoring"],
        assets["alerts"],
        assets["semantic_metrics"],
    )
    render_dashboard_footer(lang)


if __name__ == "__main__":
    main()
