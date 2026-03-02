SELECT
    c.channel,
    SUM(f.order_amount) AS revenue,
    COUNT(DISTINCT f.customer_id) AS customers,
    SUM(f.order_amount) / NULLIF(COUNT(DISTINCT f.customer_id), 0) AS arpu
FROM fact_orders f
JOIN dim_channel c ON c.channel_key = f.channel_key
GROUP BY c.channel
ORDER BY revenue DESC;
