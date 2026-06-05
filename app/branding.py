from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Branding:
    app_name: str
    hero_title: str
    hero_badge: str
    footer_title: str
    footer_body: str | None


def resolve_branding(
    *, default_app_name: str, default_badge: str, default_footer_body: str
) -> Branding:
    app_name = os.getenv("RIP_BRAND_NAME", "").strip() or default_app_name
    hero_title = os.getenv("RIP_BRAND_HERO_TITLE", "").strip() or app_name
    hero_badge = os.getenv("RIP_BRAND_BADGE", "").strip() or default_badge
    footer_title = os.getenv("RIP_BRAND_FOOTER_TITLE", "").strip() or app_name
    footer_body = os.getenv("RIP_BRAND_FOOTER_BODY", "").strip() or default_footer_body
    return Branding(
        app_name=app_name,
        hero_title=hero_title,
        hero_badge=hero_badge,
        footer_title=footer_title,
        footer_body=footer_body,
    )
