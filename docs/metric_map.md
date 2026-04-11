# Metric Map

This repository now centers its analytical story on the Olist marketplace dataset and exposes two metric groups:

## Executive KPIs

- `total_revenue`: delivered-order payment value aggregated from `silver_orders.csv`
- `total_orders`: distinct orders in scope
- `average_ticket`: delivered-order average order value
- `total_freight`: aggregated freight paid by customers
- `avg_freight`: mean freight per delivered order
- `unique_customers`: distinct customers in the curated customer layer
- `recurring_customer_rate`: share of customers with 2 or more historical orders
- `avg_delivery_days`: mean delivery time for delivered orders
- `late_delivery_rate`: share of delivered orders after estimated delivery date
- `on_time_delivery_rate`: complement of late delivery for executive scorecards
- `cancellation_rate`: share of canceled or unavailable orders
- `avg_review_score`: average `review_score` on reviewed orders
- `review_promoter_rate`: share of reviewed delivered orders with score 4 or 5
- `repeat_revenue_share`: share of marketplace revenue associated with repeat-customer portfolios
- `m1_retention_rate`: average month-1 cohort retention across observed cohorts
- `seller_top10_revenue_share`, `category_top10_revenue_share`: revenue concentration metrics for executive risk framing
- `avg_ltv`, `avg_cac`, `avg_ltv_cac_ratio`: proxy unit-economics layer used for prioritization
- `churn_risk_proxy`: customer-level behavioral proxy derived from observed Olist order cadence and recency signals
- `rfm_segment`: customer behavioral segment derived from recency, frequency and monetary ranking

## Business Views

- `customer_analytics.csv`: customer health, churn proxy, next-purchase propensity, LTV proxy, RFM segment and recommended action
- `customer_segment_health.csv`: aggregated customer book by action, RFM segment, churn band, revenue exposure, and health score
- `payment_analytics.csv`: revenue and volume mix by payment channel
- `payment_scorecard.csv`: payment mix with on-time delivery, freight pressure, and promoter-rate proxy
- `geographic_analytics.csv`: revenue, orders, customers and service quality by state
- `state_scorecard.csv`: presentation-ready state operating scorecard
- `logistics_analytics.csv`: monthly delivery performance, cancellation load and review trends
- `operations_scorecard.csv`: logistics scorecard with median delivery, on-time rate, and satisfaction trend
- `seller_analytics.csv`: seller concentration, service quality and revenue contribution
- `seller_scorecard.csv`: seller tiers plus fulfillment-risk bands
- `product_analytics.csv`: product-level revenue and review performance
- `category_analytics.csv`: category participation and category-level performance
- `category_scorecard.csv`: category tiers, freight pressure, and delay risk
- `executive_summary_layer.csv`: monthly executive scorecard feed for BI tools
- `executive_scorecard.csv`: one-row executive brief for buyer-facing and BI consumption
- `cohort_retention.csv`: monthly cohort retention curve
- `retention_scorecard.csv`: retention curve exported as a stable curated scorecard
- `rfm_segments.csv`: customer behavioral segmentation
- `executive_report.json`: narrative and diagnostic executive artifact consumed by the app and reviewer workflows
- `artifact_validation_report.json`, `freshness_report.json`, `pipeline_manifest.json`: governed operational context for trust, reliability, and auditability

## Metric Policy

- Revenue is based on the governed silver order value, not on dashboard-side recomputation.
- Delivery metrics only interpret `delivered` orders as completed fulfillment events.
- Cancellation counts include `canceled` and `unavailable`.
- CAC and unit economics remain explicitly proxy-based because the Olist dataset has no real acquisition spend source.
- The Streamlit app, warehouse tables and executive JSON artifacts all consume the same processed outputs.
- Payment channel scorecards rely on normalized payment labels to preserve real business mix in the Olist source.
- Forecast and scenario views represent simulation on the prioritized action portfolio, not a full-funnel forecast of the entire marketplace.
