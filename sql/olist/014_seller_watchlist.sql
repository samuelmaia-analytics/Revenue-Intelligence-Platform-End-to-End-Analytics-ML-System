-- Watchlist executiva de sellers: risco operacional com impacto de receita.
SELECT
    seller_id,
    seller_state,
    total_revenue,
    total_orders,
    late_delivery_rate,
    on_time_delivery_rate,
    avg_review_score,
    revenue_share_pct,
    seller_tier,
    seller_risk_band
FROM processed.seller_scorecard
WHERE total_revenue >= 50000
  AND (
      late_delivery_rate >= 0.10
      OR avg_review_score < 4.0
  )
ORDER BY total_revenue DESC, late_delivery_rate DESC, avg_review_score ASC, seller_id ASC;
