-- Ranking geográfico combinando receita por cliente, entrega e satisfação.
SELECT
    state,
    total_revenue,
    unique_customers,
    revenue_per_customer,
    avg_ticket,
    on_time_delivery_rate,
    avg_review_score,
    revenue_share_pct,
    state_tier,
    state_risk_band
FROM processed.state_scorecard
WHERE unique_customers >= 100
ORDER BY revenue_per_customer DESC, on_time_delivery_rate DESC, avg_review_score DESC, state ASC;
