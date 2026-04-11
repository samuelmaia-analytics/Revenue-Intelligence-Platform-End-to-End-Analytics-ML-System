-- Resumo RFM por segmento comportamental.
SELECT
    segment,
    COUNT(DISTINCT customer_id) AS customers,
    AVG(recency) AS avg_recency_days,
    AVG(frequency) AS avg_frequency,
    AVG(monetary) AS avg_monetary,
    AVG(rfm_total) AS avg_rfm_total
FROM processed.rfm_segments
GROUP BY segment
ORDER BY avg_monetary DESC, customers DESC, segment ASC;
