-- Leitura executiva compacta de operações.
WITH monthly AS (
    SELECT *
    FROM processed.operations_scorecard
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
    scorecard.avg_delivery_days,
    scorecard.late_delivery_rate,
    scorecard.on_time_delivery_rate,
    scorecard.avg_review_score,
    scorecard.review_promoter_rate,
    monthly.order_month AS latest_ops_month,
    monthly.delivered_orders,
    monthly.canceled_orders,
    monthly.median_delivery_days,
    monthly.delivery_gap_days
FROM scorecard
CROSS JOIN monthly;
