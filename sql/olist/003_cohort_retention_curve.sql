-- Curva de retenção por coorte, pronta para consumo em BI.
SELECT
    cohort_month,
    cohort_index,
    cohort_size,
    active_customers,
    retention_rate,
    retained_customers_pct
FROM processed.retention_scorecard
WHERE cohort_index BETWEEN 0 AND 12
  AND cohort_size >= 25
ORDER BY cohort_month, cohort_index;
