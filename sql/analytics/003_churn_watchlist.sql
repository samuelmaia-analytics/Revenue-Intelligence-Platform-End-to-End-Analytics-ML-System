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
   OR last_order_date < CURRENT_DATE - INTERVAL '90' DAY
ORDER BY lifetime_revenue DESC NULLS LAST;
