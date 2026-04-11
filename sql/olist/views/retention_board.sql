-- Leitura executiva compacta de retenção e risco.
WITH scorecard AS (
    SELECT *
    FROM processed.executive_scorecard
),
top_action AS (
    SELECT
        recommended_action,
        rfm_segment,
        churn_risk_band,
        customers,
        revenue_proxy,
        avg_churn_probability,
        avg_next_purchase_probability
    FROM processed.customer_segment_health
    ORDER BY revenue_proxy DESC, customers DESC
    LIMIT 1
)
SELECT
    scorecard.snapshot_date,
    scorecard.m1_retention_rate,
    scorecard.recurring_customer_rate,
    scorecard.repeat_revenue_share,
    scorecard.high_churn_risk_customer_pct,
    scorecard.high_churn_risk_revenue_pct,
    top_action.recommended_action AS priority_action,
    top_action.rfm_segment AS priority_rfm_segment,
    top_action.churn_risk_band AS priority_risk_band,
    top_action.customers AS customers_in_priority_group,
    top_action.revenue_proxy AS revenue_proxy_in_priority_group,
    top_action.avg_churn_probability,
    top_action.avg_next_purchase_probability
FROM scorecard
CROSS JOIN top_action;
