-- Concentração de receita entre sellers.
WITH seller_rank AS (
    SELECT
        seller_id,
        seller_state,
        total_revenue,
        revenue_share_pct,
        ROW_NUMBER() OVER (ORDER BY total_revenue DESC, seller_id ASC) AS revenue_rank
    FROM processed.seller_analytics
)
SELECT
    CASE
        WHEN revenue_rank <= 10 THEN 'Top 10'
        WHEN revenue_rank <= 50 THEN 'Top 11-50'
        ELSE 'Long Tail'
    END AS seller_bucket,
    COUNT(*) AS sellers,
    SUM(total_revenue) AS total_revenue,
    SUM(revenue_share_pct) AS revenue_share_pct
FROM seller_rank
GROUP BY 1
ORDER BY total_revenue DESC;
