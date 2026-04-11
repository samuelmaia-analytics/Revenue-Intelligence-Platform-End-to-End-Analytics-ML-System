-- Leitura executiva compacta de sellers.
WITH scorecard AS (
    SELECT *
    FROM processed.executive_scorecard
),
top_seller AS (
    SELECT
        seller_id,
        seller_state,
        total_revenue,
        total_orders,
        avg_review_score,
        late_delivery_rate
    FROM processed.seller_scorecard
    ORDER BY total_revenue DESC, total_orders DESC
    LIMIT 1
),
watchlist AS (
    SELECT COUNT(*) AS sellers_in_watchlist
    FROM processed.seller_scorecard
    WHERE total_revenue >= 50000
      AND (late_delivery_rate >= 0.10 OR avg_review_score < 4.0)
)
SELECT
    scorecard.snapshot_date,
    scorecard.top_seller,
    scorecard.seller_top10_revenue_share,
    top_seller.seller_state AS top_seller_state,
    top_seller.total_revenue AS top_seller_revenue,
    top_seller.total_orders AS top_seller_orders,
    top_seller.avg_review_score AS top_seller_review_score,
    top_seller.late_delivery_rate AS top_seller_late_delivery_rate,
    watchlist.sellers_in_watchlist
FROM scorecard
CROSS JOIN top_seller
CROSS JOIN watchlist;
