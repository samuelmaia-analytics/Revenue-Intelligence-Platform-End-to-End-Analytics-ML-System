SELECT
    d.year,
    d.month,
    SUM(f.order_amount) AS gross_revenue,
    COUNT(DISTINCT f.customer_id) AS active_customers,
    COUNT(*) AS order_count,
    AVG(f.order_amount) AS avg_ticket
FROM fact_orders f
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
