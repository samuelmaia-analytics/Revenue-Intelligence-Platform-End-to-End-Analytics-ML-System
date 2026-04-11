-- Sellers com maior pressão de atraso e relevância comercial.
SELECT
    seller_id,
    seller_state,
    total_revenue,
    total_orders,
    late_delivery_rate,
    on_time_delivery_rate,
    avg_review_score,
    seller_tier,
    seller_risk_band
FROM processed.seller_scorecard
WHERE total_orders >= 20
ORDER BY late_delivery_rate DESC, total_revenue DESC, seller_id ASC
LIMIT 100;
