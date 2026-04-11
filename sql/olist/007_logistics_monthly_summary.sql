-- Resumo mensal de logística e entrega.
SELECT
    order_month,
    total_orders,
    delivered_orders,
    canceled_orders,
    avg_delivery_days,
    median_delivery_days,
    estimated_delivery_days,
    delivery_gap_days,
    late_delivery_rate,
    on_time_delivery_rate
FROM processed.operations_scorecard
ORDER BY order_month;
