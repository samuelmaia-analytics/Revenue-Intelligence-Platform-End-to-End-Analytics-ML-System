# Olist Analytics Model

## Layer Intent

- `raw`: original Olist CSVs under `data/raw/`
- `bronze`: normalized source copies with ingestion metadata
- `silver`: cleaned and enriched marketplace entities
- `gold`: warehouse-ready dimensions and facts
- `processed`: executive marts, scorecards, reports and governed exports

## Silver Outputs

- `silver_customers.csv`: one row per analytical customer with state, city, revenue, order counts, review and delivery behavior
- `silver_orders.csv`: one row per order with payment, logistics and review enrichment
- `silver_order_items.csv`: line-level commercial grain with product and seller context
- `silver_products.csv`: products with translated category names
- `silver_sellers.csv`: seller dimension seed
- `silver_payments.csv`: payment event layer
- `silver_reviews.csv`: review event layer
- `silver_geography.csv`: state and city marketplace rollup

## Gold Outputs

- `dim_customers.csv`
- `dim_date.csv`
- `dim_channel.csv`
- `fact_orders.csv`
- `dim_products.csv`
- `dim_sellers.csv`
- `dim_geography.csv`
- `fact_order_items.csv`

## Processed Executive Products

- `executive_kpis.json`
- `executive_report.json`
- `executive_summary.json`
- `executive_scorecard.csv`
- `customer_analytics.csv`
- `customer_segment_health.csv`
- `payment_analytics.csv`
- `payment_scorecard.csv`
- `geographic_analytics.csv`
- `state_scorecard.csv`
- `logistics_analytics.csv`
- `operations_scorecard.csv`
- `seller_analytics.csv`
- `seller_scorecard.csv`
- `product_analytics.csv`
- `category_analytics.csv`
- `category_scorecard.csv`
- `executive_summary_layer.csv`
- `cohort_retention.csv`
- `retention_scorecard.csv`
- `rfm_segments.csv`

## Preferred Consumption by Layer

- executive and BI consumers should start with the curated scorecards and JSON executive artifacts
- exploratory analysis can use the more detailed marts such as `customer_analytics.csv`, `seller_analytics.csv`, `category_analytics.csv` and `logistics_analytics.csv`
- Streamlit consumes the same processed artifacts, which keeps the presentation layer aligned with the governed analytical layer

## Streamlit Surface Mapping

- `app/streamlit_app.py` emphasizes the executive command-center experience with premium PT-BR storytelling
- `app/pages/` exposes the same analytical assets through a multipage structure organized by business topic
- both surfaces read from `data/processed/` and should not introduce parallel metric logic

## Curated Consumption Pattern

- executive and BI tools should prefer the scorecard files when they need stable, presentation-oriented aggregates
- analytical notebooks and warehouse consumers can still read the detailed marts for drill-down and custom modeling
- Streamlit consumes the same processed assets, so the dashboard and exports stay contract-aligned

## Modeling Notes

- Supervised churn and next-purchase models are still preserved to keep the repository’s ML operating path demonstrable.
- Customer features are now derived from real Olist order history instead of a simplified synthetic schema.
- Where the dataset does not provide a real business input, the platform marks the output as a proxy instead of pretending precision.
- Payment normalization explicitly preserves channels such as credit card, debit card, boleto and voucher to avoid collapsing business mix into `Other`.
