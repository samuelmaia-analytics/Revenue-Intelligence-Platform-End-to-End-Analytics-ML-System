-- Resumo executivo mensal para receita, retenção e entrega.
SELECT
    order_month,
    total_revenue,
    total_orders,
    unique_customers,
    avg_ticket,
    repeat_customer_rate,
    repeat_revenue_share,
    late_delivery_rate,
    on_time_delivery_rate,
    cancellation_rate,
    avg_review_score,
    revenue_growth_pct,
    orders_growth_pct
FROM processed.executive_summary_layer
ORDER BY order_month;
