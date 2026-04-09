from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    import duckdb
except ImportError:  # pragma: no cover - fallback path is exercised instead
    duckdb = None


def duckdb_available() -> bool:
    return duckdb is not None


def _load_inputs(
    *,
    customers_path: Path,
    orders_path: Path,
    marketing_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(
        customers_path,
        usecols=["customer_id", "signup_date", "channel", "segment"],
        parse_dates=["signup_date"],
    )
    orders = pd.read_csv(
        orders_path,
        usecols=["order_id", "customer_id", "order_date", "order_value"],
        parse_dates=["order_date"],
    )
    marketing = pd.read_csv(marketing_path, usecols=["channel", "marketing_spend"])
    return customers, orders, marketing


def _connect(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    marketing: pd.DataFrame,
) -> "duckdb.DuckDBPyConnection":
    connection = duckdb.connect(database=":memory:")
    connection.register("customers", customers)
    connection.register("orders", orders)
    connection.register("marketing", marketing)
    return connection


def build_curated_support_frames_duckdb(
    *,
    customers_path: Path,
    orders_path: Path,
    marketing_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers, orders, marketing = _load_inputs(
        customers_path=customers_path,
        orders_path=orders_path,
        marketing_path=marketing_path,
    )
    connection = _connect(customers, orders, marketing)

    cac = connection.execute(
        """
        WITH acquired AS (
            SELECT
                channel,
                COUNT(customer_id) AS customers_acquired
            FROM customers
            GROUP BY 1
        )
        SELECT
            marketing.channel,
            marketing.marketing_spend,
            COALESCE(acquired.customers_acquired, 1) AS customers_acquired,
            marketing.marketing_spend / GREATEST(COALESCE(acquired.customers_acquired, 1), 1) AS cac
        FROM marketing
        LEFT JOIN acquired USING (channel)
        ORDER BY marketing.channel
        """
    ).fetchdf()

    rfm = connection.execute(
        """
        WITH ref_date AS (
            SELECT MAX(order_date) + INTERVAL 1 DAY AS value FROM orders
        ),
        order_agg AS (
            SELECT
                customer_id,
                date_diff('day', MAX(order_date), (SELECT value FROM ref_date)) AS recency,
                COUNT(order_id) AS frequency,
                SUM(order_value) AS monetary
            FROM orders
            GROUP BY 1
        )
        SELECT
            customers.customer_id,
            customers.channel,
            COALESCE(order_agg.recency, 0) AS recency,
            COALESCE(order_agg.frequency, 0) AS frequency,
            COALESCE(order_agg.monetary, 0) AS monetary
        FROM customers
        LEFT JOIN order_agg USING (customer_id)
        ORDER BY customers.customer_id
        """
    ).fetchdf()

    cohort = connection.execute(
        """
        WITH customer_cohorts AS (
            SELECT
                customer_id,
                date_trunc('month', signup_date)::DATE AS cohort_month
            FROM customers
        ),
        order_cohorts AS (
            SELECT
                orders.customer_id,
                customer_cohorts.cohort_month,
                (
                    (EXTRACT(year FROM date_trunc('month', orders.order_date)) - EXTRACT(year FROM customer_cohorts.cohort_month)) * 12
                    + (EXTRACT(month FROM date_trunc('month', orders.order_date)) - EXTRACT(month FROM customer_cohorts.cohort_month))
                )::INTEGER AS cohort_index
            FROM orders
            LEFT JOIN customer_cohorts USING (customer_id)
        ),
        active AS (
            SELECT
                cohort_month,
                cohort_index,
                COUNT(DISTINCT customer_id) AS active_customers
            FROM order_cohorts
            GROUP BY 1, 2
        ),
        cohort_size AS (
            SELECT
                cohort_month,
                COUNT(DISTINCT customer_id) AS cohort_size
            FROM customer_cohorts
            GROUP BY 1
        )
        SELECT
            strftime(active.cohort_month, '%Y-%m') AS cohort_month,
            active.cohort_index,
            active.active_customers,
            cohort_size.cohort_size,
            LEAST(
                GREATEST(active.active_customers * 1.0 / GREATEST(cohort_size.cohort_size, 1), 0.0),
                1.0
            ) AS retention_rate
        FROM active
        INNER JOIN cohort_size USING (cohort_month)
        ORDER BY active.cohort_month, active.cohort_index
        """
    ).fetchdf()
    connection.close()

    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first"), 4, labels=[4, 3, 2, 1])
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4])
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4])
    rfm["rfm_total"] = rfm[["r_score", "f_score", "m_score"]].astype(int).sum(axis=1)

    conditions = [
        rfm["rfm_total"] >= 10,
        rfm["rfm_total"].between(8, 9),
        rfm["r_score"].astype(int) <= 2,
    ]
    choices = ["VIP", "Loyal", "At Risk"]
    rfm["segment"] = np.select(conditions, choices, default="Hibernating")

    return (
        cac.astype({"customers_acquired": "int64"}),
        rfm,
        cohort.astype(
            {
                "cohort_index": "int64",
                "active_customers": "int64",
                "cohort_size": "int64",
            }
        ),
    )
