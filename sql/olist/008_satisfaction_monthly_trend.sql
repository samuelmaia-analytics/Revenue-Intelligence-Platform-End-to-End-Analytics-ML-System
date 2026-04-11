-- Tendência mensal de satisfação e entrega.
SELECT
    order_month,
    avg_review_score,
    review_promoter_rate,
    late_delivery_rate,
    on_time_delivery_rate,
    delivered_orders
FROM processed.operations_scorecard
ORDER BY order_month;
