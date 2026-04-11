-- Leitura executiva compacta de geografia.
WITH scorecard AS (
    SELECT *
    FROM processed.executive_scorecard
),
top_opportunity AS (
    SELECT
        state,
        revenue_per_customer,
        total_revenue,
        on_time_delivery_rate,
        avg_review_score
    FROM processed.state_scorecard
    WHERE unique_customers >= 100
    ORDER BY revenue_per_customer DESC, on_time_delivery_rate DESC
    LIMIT 1
)
SELECT
    scorecard.snapshot_date,
    scorecard.top_state,
    scorecard.top_state_revenue_share,
    top_opportunity.state AS opportunity_state,
    top_opportunity.revenue_per_customer AS opportunity_revenue_per_customer,
    top_opportunity.total_revenue AS opportunity_total_revenue,
    top_opportunity.on_time_delivery_rate AS opportunity_on_time_delivery_rate,
    top_opportunity.avg_review_score AS opportunity_review_score
FROM scorecard
CROSS JOIN top_opportunity;
