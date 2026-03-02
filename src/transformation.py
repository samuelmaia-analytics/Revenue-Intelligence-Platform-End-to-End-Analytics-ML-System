from pathlib import Path

import numpy as np
import pandas as pd


def build_silver_layer(
    bronze_customers_path: Path,
    bronze_orders_path: Path,
    bronze_marketing_path: Path,
    silver_dir: Path,
) -> tuple[Path, Path, Path]:
    silver_dir.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(bronze_customers_path, parse_dates=["signup_date"], low_memory=False)
    orders = pd.read_csv(bronze_orders_path, parse_dates=["order_date"], low_memory=False)
    marketing = pd.read_csv(bronze_marketing_path, low_memory=False)

    customers = customers.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").drop_duplicates(
        subset=["customer_id"]
    )
    orders = orders.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").drop_duplicates(
        subset=["order_id"]
    )
    marketing = marketing.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").drop_duplicates(
        subset=["channel"]
    )

    customers["customer_id"] = customers["customer_id"].astype(int)
    orders["customer_id"] = orders["customer_id"].astype(int)
    orders["order_value"] = pd.to_numeric(orders["order_value"], errors="coerce").fillna(0.0)
    marketing["marketing_spend"] = (
        pd.to_numeric(marketing["marketing_spend"], errors="coerce").fillna(0.0).clip(lower=0)
    )

    valid_customers = set(customers["customer_id"].tolist())
    orders = orders[orders["customer_id"].isin(valid_customers)].copy()
    orders = orders[orders["order_value"] > 0].copy()

    silver_customers_path = silver_dir / "silver_customers.csv"
    silver_orders_path = silver_dir / "silver_orders.csv"
    silver_marketing_path = silver_dir / "silver_marketing_spend.csv"

    customers.to_csv(silver_customers_path, index=False)
    orders.to_csv(silver_orders_path, index=False)
    marketing.to_csv(silver_marketing_path, index=False)
    return silver_customers_path, silver_orders_path, silver_marketing_path


def build_customer_features(
    customers_path: Path, orders_path: Path, output_dir: Path
) -> pd.DataFrame:
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    output_dir.mkdir(parents=True, exist_ok=True)

    max_order_date = orders["order_date"].max()
    as_of_date = max_order_date - pd.Timedelta(days=120)
    hist_orders = orders[orders["order_date"] <= as_of_date].copy()
    future_30 = orders[
        (orders["order_date"] > as_of_date) & (orders["order_date"] <= as_of_date + pd.Timedelta(days=30))
    ].copy()
    future_90 = orders[
        (orders["order_date"] > as_of_date) & (orders["order_date"] <= as_of_date + pd.Timedelta(days=90))
    ].copy()

    agg = (
        hist_orders.groupby("customer_id")
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "count"),
            monetary=("order_value", "sum"),
            avg_order_value=("order_value", "mean"),
        )
        .reset_index()
    )

    features = customers.merge(agg, on="customer_id", how="left")
    features["frequency"] = features["frequency"].fillna(0)
    features["monetary"] = features["monetary"].fillna(0.0)
    features["avg_order_value"] = features["avg_order_value"].fillna(0.0)
    features["recency_days"] = (as_of_date - features["last_order_date"]).dt.days
    features["recency_days"] = features["recency_days"].fillna(999).clip(lower=0)
    features["tenure_days"] = (as_of_date - features["signup_date"]).dt.days.clip(lower=1)

    future_purchase_30 = (
        future_30.groupby("customer_id")["order_id"].count().reset_index(name="future_orders_30d")
    )
    future_purchase_90 = (
        future_90.groupby("customer_id")["order_id"].count().reset_index(name="future_orders_90d")
    )
    features = features.merge(future_purchase_30, on="customer_id", how="left")
    features = features.merge(future_purchase_90, on="customer_id", how="left")
    features["future_orders_30d"] = features["future_orders_30d"].fillna(0)
    features["future_orders_90d"] = features["future_orders_90d"].fillna(0)

    eligible = (features["frequency"] > 0) & (features["tenure_days"] >= 60)
    features["is_churned"] = np.where(eligible, (features["future_orders_90d"] == 0).astype(int), np.nan)
    features["next_purchase_30d"] = np.where(
        eligible, (features["future_orders_30d"] > 0).astype(int), np.nan
    )
    features["arpu"] = np.where(
        features["tenure_days"] > 0, features["monetary"] / (features["tenure_days"] / 30), 0
    )
    features["as_of_date"] = as_of_date

    features.to_csv(output_dir / "customer_features.csv", index=False)
    return features
