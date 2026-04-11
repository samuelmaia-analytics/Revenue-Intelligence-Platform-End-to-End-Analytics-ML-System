-- Matriz de retenção por ação recomendada, segmento RFM e faixa de churn.
SELECT
    recommended_action,
    rfm_segment,
    churn_risk_band,
    customers,
    revenue_proxy,
    avg_ltv,
    avg_ticket,
    avg_churn_probability,
    avg_next_purchase_probability,
    avg_health_score,
    customer_share_pct
FROM processed.customer_segment_health
ORDER BY revenue_proxy DESC, customers DESC, recommended_action ASC;
