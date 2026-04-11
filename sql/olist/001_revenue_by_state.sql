-- Receita executiva por estado a partir do scorecard governado.
SELECT
    state,
    total_revenue,
    total_orders,
    unique_customers,
    avg_ticket,
    on_time_delivery_rate,
    avg_review_score,
    state_tier,
    state_risk_band
FROM processed.state_scorecard
ORDER BY total_revenue DESC, state ASC;
