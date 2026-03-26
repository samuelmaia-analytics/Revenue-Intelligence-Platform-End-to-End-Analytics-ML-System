-- Watchlist of customers inactive for 90 days using SQLite-portable date arithmetic.
WITH customer_orders AS (
    SELECT
        dc.customer_id,
        dc.segment,
        dc.channel,
        MAX(f.order_date) AS last_order_date,
        SUM(f.order_amount) AS lifetime_revenue
    FROM dim_customers dc
    LEFT JOIN fact_orders f ON f.customer_id = dc.customer_id
    GROUP BY dc.customer_id, dc.segment, dc.channel
)
SELECT
    customer_id,
    segment,
    channel,
    last_order_date,
    lifetime_revenue
FROM customer_orders
WHERE last_order_date IS NULL
   OR DATE(last_order_date) < DATE('now', '-90 day')
ORDER BY lifetime_revenue DESC NULLS LAST;
