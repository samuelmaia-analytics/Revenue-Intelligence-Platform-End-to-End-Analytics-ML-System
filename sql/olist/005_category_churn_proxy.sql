-- Proxy de churn por categoria, usando a camada analítica governada.
WITH category_customer_book AS (
    SELECT
        oi.category_name_english AS category,
        oi.customer_id,
        AVG(ca.churn_probability) AS avg_churn_probability,
        AVG(ca.next_purchase_probability) AS avg_next_purchase_probability,
        SUM(oi.line_revenue) AS category_revenue
    FROM silver.silver_order_items AS oi
    JOIN processed.customer_analytics AS ca
      ON ca.customer_id = oi.customer_id
    WHERE oi.is_delivered = TRUE
      AND oi.category_name_english IS NOT NULL
    GROUP BY oi.category_name_english, oi.customer_id
)
SELECT
    category,
    COUNT(DISTINCT customer_id) AS customers_in_scope,
    SUM(category_revenue) AS total_revenue,
    AVG(avg_churn_probability) AS avg_churn_probability,
    AVG(avg_next_purchase_probability) AS avg_next_purchase_probability
FROM category_customer_book
GROUP BY category
HAVING COUNT(DISTINCT customer_id) >= 30
ORDER BY avg_churn_probability DESC, total_revenue DESC, category ASC;
