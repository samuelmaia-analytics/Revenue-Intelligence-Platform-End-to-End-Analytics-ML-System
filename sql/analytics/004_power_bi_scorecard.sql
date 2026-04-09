-- Executive scorecard surface suitable for Power BI import on top of the canonical warehouse.
SELECT
    recommendations.channel,
    COUNT(DISTINCT recommendations.customer_id) AS customers_in_scope,
    AVG(recommendations.ltv) AS avg_ltv,
    AVG(recommendations.cac) AS avg_cac,
    AVG(recommendations.ltv_cac_ratio) AS avg_ltv_cac_ratio,
    AVG(CASE WHEN recommendations.churn_probability >= 0.70 THEN 1.0 ELSE 0.0 END) AS high_churn_risk_pct,
    AVG(recommendations.next_purchase_probability) AS avg_next_purchase_probability
FROM recommendations
GROUP BY recommendations.channel
ORDER BY avg_ltv_cac_ratio DESC, recommendations.channel ASC;
