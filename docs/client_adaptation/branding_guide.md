# Branding Guide

## Objective

Allow client-specific presentation without forking application logic.

## Supported Environment Variables

- `RIP_BRAND_NAME`
- `RIP_BRAND_HERO_TITLE`
- `RIP_BRAND_BADGE`
- `RIP_BRAND_FOOTER_TITLE`
- `RIP_BRAND_FOOTER_BODY`

## Recommended Use

- keep business logic and metrics unchanged
- adapt visible naming and client-facing framing per deployment
- use client-specific values only in deployment environments, not in source control

## Design Rule

Branding is presentation-only. It must not create a separate decision model or alternate runtime.
