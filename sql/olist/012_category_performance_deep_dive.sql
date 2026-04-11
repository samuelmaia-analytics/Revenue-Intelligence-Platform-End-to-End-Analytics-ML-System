-- Deep dive de categorias com receita, frete e risco operacional.
SELECT
    category,
    total_revenue,
    total_orders,
    total_items,
    avg_ticket,
    freight_value,
    freight_share_pct,
    late_delivery_rate,
    on_time_delivery_rate,
    avg_review_score,
    category_tier,
    category_risk_band
FROM processed.category_scorecard
WHERE total_orders >= 30
ORDER BY total_revenue DESC, avg_review_score DESC, category ASC;
