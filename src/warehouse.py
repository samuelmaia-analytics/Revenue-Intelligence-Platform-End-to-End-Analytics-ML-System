from pathlib import Path

import pandas as pd


def build_star_schema(customers_path: Path, orders_path: Path, output_dir: Path) -> None:
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])
    orders = pd.read_csv(orders_path, parse_dates=["order_date"])
    output_dir.mkdir(parents=True, exist_ok=True)

    dim_customers = customers.copy()
    dim_customers["signup_month"] = dim_customers["signup_date"].dt.to_period("M").astype(str)

    dim_date = pd.DataFrame({"date": pd.date_range(orders["order_date"].min(), orders["order_date"].max())})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["quarter"] = dim_date["date"].dt.quarter

    fact_orders = orders.copy()
    fact_orders["date_key"] = fact_orders["order_date"].dt.strftime("%Y%m%d").astype(int)

    dim_customers.to_csv(output_dir / "dim_customers.csv", index=False)
    dim_date.to_csv(output_dir / "dim_date.csv", index=False)
    fact_orders.to_csv(output_dir / "fact_orders.csv", index=False)

