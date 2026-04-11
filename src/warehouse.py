from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.io_utils import atomic_write_csv


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def build_star_schema(customers_path: Path, orders_path: Path, output_dir: Path) -> None:
    customer_columns = pd.read_csv(customers_path, nrows=0).columns.tolist()
    order_columns = pd.read_csv(orders_path, nrows=0).columns.tolist()
    customers = pd.read_csv(
        customers_path,
        parse_dates=[column for column in ["signup_date", "latest_order_at"] if column in customer_columns],
    )
    orders = pd.read_csv(
        orders_path,
        parse_dates=[
            column
            for column in [
                "order_date",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]
            if column in order_columns
        ],
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    silver_dir = customers_path.parent

    dim_customers = customers.copy()
    dim_customers["customer_key"] = dim_customers["customer_id"]
    dim_customers["signup_month"] = dim_customers["signup_date"].dt.to_period("M").astype(str)

    date_seed = orders["order_purchase_timestamp"] if "order_purchase_timestamp" in orders.columns else orders["order_date"]
    dim_date = pd.DataFrame({"date": pd.date_range(date_seed.min(), date_seed.max())})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()

    channel_seed = (
        orders.merge(
            dim_customers[["customer_id", "channel"]],
            on="customer_id",
            how="left",
            suffixes=("", "_customer"),
        )
        if "channel" not in orders.columns
        else orders.copy()
    )
    if "channel" not in channel_seed.columns and "channel_customer" in channel_seed.columns:
        channel_seed = channel_seed.rename(columns={"channel_customer": "channel"})
    dim_channel = (
        channel_seed.groupby("channel")["customer_id"].nunique().reset_index(name="acquired_customers")
    )
    dim_channel["channel_key"] = dim_channel["channel"].factorize()[0] + 1

    customer_channel = dim_customers[["customer_id", "channel"]].merge(
        dim_channel[["channel", "channel_key"]], on="channel", how="left"
    )

    fact_orders = orders.copy()
    fact_orders["date_key"] = date_seed.dt.strftime("%Y%m%d").astype(int)
    fact_orders = fact_orders.merge(
        customer_channel[["customer_id", "channel_key"]], on="customer_id", how="left"
    )
    fact_orders["order_amount"] = fact_orders["order_value"]
    fact_orders["order_count"] = 1

    atomic_write_csv(output_dir / "dim_channel.csv", dim_channel)
    atomic_write_csv(output_dir / "dim_customers.csv", dim_customers)
    atomic_write_csv(output_dir / "dim_date.csv", dim_date)
    atomic_write_csv(output_dir / "fact_orders.csv", fact_orders)

    products = _read_optional_csv(silver_dir / "silver_products.csv")
    sellers = _read_optional_csv(silver_dir / "silver_sellers.csv")
    geography = _read_optional_csv(silver_dir / "silver_geography.csv")
    order_items = _read_optional_csv(silver_dir / "silver_order_items.csv")

    if not products.empty:
        dim_products = products.copy()
        dim_products["product_key"] = range(1, len(dim_products) + 1)
        atomic_write_csv(output_dir / "dim_products.csv", dim_products)
    if not sellers.empty:
        dim_sellers = sellers.copy()
        dim_sellers["seller_key"] = range(1, len(dim_sellers) + 1)
        atomic_write_csv(output_dir / "dim_sellers.csv", dim_sellers)
    if not geography.empty:
        dim_geography = geography.copy()
        dim_geography["geography_key"] = range(1, len(dim_geography) + 1)
        atomic_write_csv(output_dir / "dim_geography.csv", dim_geography)
    if not order_items.empty:
        fact_order_items = order_items.copy()
        fact_order_items["line_amount"] = fact_order_items["line_revenue"]
        atomic_write_csv(output_dir / "fact_order_items.csv", fact_order_items)
