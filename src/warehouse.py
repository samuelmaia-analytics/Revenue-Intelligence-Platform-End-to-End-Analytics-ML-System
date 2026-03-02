from pathlib import Path

import pandas as pd


def build_star_schema(customers_path: Path, orders_path: Path, output_dir: Path) -> None:
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    output_dir.mkdir(parents=True, exist_ok=True)

    dim_customers = customers.copy()
    dim_customers["customer_key"] = dim_customers["customer_id"]
    dim_customers["signup_month"] = dim_customers["signup_date"].dt.to_period("M").astype(str)

    dim_date = pd.DataFrame({"date": pd.date_range(orders["order_date"].min(), orders["order_date"].max())})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dim_date["date"].dt.dayofweek + 1

    channel_spend = (
        customers.groupby("channel")["customer_id"].count().reset_index(name="acquired_customers")
    )
    channel_spend["channel_key"] = channel_spend["channel"].factorize()[0] + 1
    dim_channel = channel_spend[["channel_key", "channel", "acquired_customers"]].copy()

    customer_channel = dim_customers[["customer_id", "channel"]].merge(
        dim_channel[["channel", "channel_key"]], on="channel", how="left"
    )

    fact_orders = orders.copy()
    fact_orders["date_key"] = fact_orders["order_date"].dt.strftime("%Y%m%d").astype(int)
    fact_orders = fact_orders.merge(customer_channel[["customer_id", "channel_key"]], on="customer_id", how="left")
    fact_orders["order_amount"] = fact_orders["order_value"]
    fact_orders["order_count"] = 1

    dim_channel.to_csv(output_dir / "dim_channel.csv", index=False)
    dim_customers.to_csv(output_dir / "dim_customers.csv", index=False)
    dim_date.to_csv(output_dir / "dim_date.csv", index=False)
    fact_orders.to_csv(output_dir / "fact_orders.csv", index=False)
