-- Leitura executiva compacta de receita.
WITH monthly AS (
    SELECT *
    FROM processed.executive_summary_layer
    WHERE total_orders >= 100
    ORDER BY order_month DESC
    LIMIT 1
),
scorecard AS (
    SELECT *
    FROM processed.executive_scorecard
)
SELECT
    scorecard.snapshot_date,
    scorecard.total_revenue,
    scorecard.total_orders,
    scorecard.average_ticket,
    scorecard.repeat_revenue_share,
    scorecard.m1_retention_rate,
    scorecard.top_payment_channel,
    scorecard.top_category,
    scorecard.top_state,
    scorecard.seller_top10_revenue_share,
    scorecard.category_top10_revenue_share,
    monthly.revenue_growth_pct,
    monthly.orders_growth_pct
FROM scorecard
CROSS JOIN monthly;
