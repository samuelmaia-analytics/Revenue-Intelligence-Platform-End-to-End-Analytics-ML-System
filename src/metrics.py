from pathlib import Path

import numpy as np
import pandas as pd


def calculate_ltv(df: pd.DataFrame, gross_margin: float = 0.68) -> pd.DataFrame:
    out = df.copy()
    if "churn_probability" not in out.columns:
        out["churn_probability"] = np.where(out["is_churned"] == 1, 0.8, 0.2)
    out["expected_retention_months"] = 1 / np.clip(out["churn_probability"], 0.05, 0.99)
    out["ltv"] = out["arpu"] * out["expected_retention_months"] * gross_margin
    out["ltv"] = out["ltv"].clip(lower=0)
    return out


def calculate_cac(marketing_path: Path, customers_path: Path) -> pd.DataFrame:
    marketing = pd.read_csv(marketing_path)
    customers = pd.read_csv(customers_path)
    acquired = customers.groupby("channel")["customer_id"].count().reset_index(name="customers_acquired")
    cac = marketing.merge(acquired, on="channel", how="left").fillna({"customers_acquired": 1})
    cac["cac"] = cac["marketing_spend"] / cac["customers_acquired"].clip(lower=1)
    return cac


def rfm_segmentation(orders_path: Path, customers_path: Path) -> pd.DataFrame:
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    customers = pd.read_csv(customers_path)
    ref_date = orders["order_date"].max() + pd.Timedelta(days=1)

    rfm = (
        orders.groupby("customer_id")
        .agg(
            recency=("order_date", lambda x: (ref_date - x.max()).days),
            frequency=("order_id", "count"),
            monetary=("order_value", "sum"),
        )
        .reset_index()
    )
    rfm = customers[["customer_id", "channel"]].merge(rfm, on="customer_id", how="left")
    rfm[["recency", "frequency", "monetary"]] = rfm[["recency", "frequency", "monetary"]].fillna(0)

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
    return rfm


def cohort_analysis(orders_path: Path, customers_path: Path) -> pd.DataFrame:
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])

    customers["cohort_month"] = customers["signup_date"].dt.to_period("M")
    orders = orders.merge(customers[["customer_id", "cohort_month"]], on="customer_id", how="left")
    orders["order_month"] = orders["order_date"].dt.to_period("M")
    orders["cohort_index"] = (orders["order_month"] - orders["cohort_month"]).apply(lambda x: x.n)

    cohort = (
        orders.groupby(["cohort_month", "cohort_index"])["customer_id"]
        .nunique()
        .reset_index(name="active_customers")
    )
    cohort_size = cohort[cohort["cohort_index"] == 0][["cohort_month", "active_customers"]].rename(
        columns={"active_customers": "cohort_size"}
    )
    out = cohort.merge(cohort_size, on="cohort_month", how="left")
    out["retention_rate"] = out["active_customers"] / out["cohort_size"].clip(lower=1)
    out["cohort_month"] = out["cohort_month"].astype(str)
    return out.sort_values(["cohort_month", "cohort_index"])


def unit_economics(ltv_df: pd.DataFrame, cac_df: pd.DataFrame, gross_margin: float = 0.68) -> pd.DataFrame:
    channel_arpu = ltv_df.groupby("channel")["arpu"].mean().reset_index(name="avg_arpu")
    out = cac_df.merge(channel_arpu, on="channel", how="left").fillna({"avg_arpu": 0})
    out["ltv_cac_ratio"] = out["avg_arpu"] * 8 * gross_margin / out["cac"].clip(lower=1)
    out["contribution_margin"] = out["avg_arpu"] * gross_margin - out["cac"] / 6
    out["payback_period_months"] = out["cac"] / (out["avg_arpu"] * gross_margin).replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0)

