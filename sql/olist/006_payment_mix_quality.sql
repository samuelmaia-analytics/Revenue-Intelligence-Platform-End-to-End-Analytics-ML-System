-- Mix de pagamentos com qualidade operacional e satisfação.
SELECT
    channel,
    total_revenue,
    total_orders,
    avg_ticket,
    avg_installments,
    late_delivery_rate,
    on_time_delivery_rate,
    review_score,
    review_promoter_rate,
    cancellation_rate,
    revenue_share_pct
FROM processed.payment_scorecard
ORDER BY total_revenue DESC, total_orders DESC, channel ASC;
