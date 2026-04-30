from pathlib import Path

import pandas as pd

from src.ingestion import save_raw_datasets
from src.transformation import build_silver_layer
from src.warehouse import build_star_schema


def test_save_raw_datasets_creates_files(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_datasets = save_raw_datasets(raw_dir, seed=7)

    assert raw_datasets.customers_path.exists()
    assert raw_datasets.orders_path.exists()
    assert raw_datasets.marketing_path.exists()
    assert raw_datasets.source_name == "synthetic"

    customers = pd.read_csv(raw_datasets.customers_path)
    orders = pd.read_csv(raw_datasets.orders_path)
    marketing = pd.read_csv(raw_datasets.marketing_path)
    assert not customers.empty
    assert not orders.empty
    assert not marketing.empty


def test_save_raw_datasets_uses_external_seed_dataset_when_provided(tmp_path: Path) -> None:
    raw_dir = tmp_path / "runtime-raw"
    seed_path = tmp_path / "seed" / "E-commerce Customer Behavior - Sheet1.csv"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        "\n".join(
            [
                "Customer ID,Gender,Age,City,Membership Type,Total Spend,Items Purchased,Average Rating,Discount Applied,Days Since Last Purchase,Satisfaction Level",
                "1,Male,31,Sao Paulo,Gold,900,3,4.8,Yes,14,High",
                "2,Female,28,Recife,Silver,450,2,4.3,No,35,Medium",
            ]
        ),
        encoding="utf-8",
    )

    raw_datasets = save_raw_datasets(raw_dir, seed=7, source_path=seed_path)
    customers = pd.read_csv(raw_datasets.customers_path)

    assert raw_datasets.source_name == "external_kaggle_csv"
    assert set(["customer_id", "channel", "segment", "signup_date"]).issubset(customers.columns)
    assert len(customers) == 2


def test_silver_layer_keeps_referential_integrity(tmp_path: Path) -> None:
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        {
            "customer_id": [1, 2],
            "signup_date": ["2025-01-01", "2025-01-02"],
            "channel": ["Organic", "Paid Search"],
            "segment": ["SMB", "Mid-Market"],
        }
    ).to_csv(bronze_dir / "bronze_customers.csv", index=False)
    pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "customer_id": [1, 999],
            "order_date": ["2025-01-10", "2025-01-11"],
            "order_value": [120.0, 200.0],
        }
    ).to_csv(bronze_dir / "bronze_orders.csv", index=False)
    pd.DataFrame({"channel": ["Organic", "Paid Search"], "marketing_spend": [1000, 2000]}).to_csv(
        bronze_dir / "bronze_marketing_spend.csv", index=False
    )

    silver_datasets = build_silver_layer(
        bronze_dir / "bronze_customers.csv",
        bronze_dir / "bronze_orders.csv",
        bronze_dir / "bronze_marketing_spend.csv",
        silver_dir,
    )
    customers_df = pd.read_csv(silver_datasets.customers_path)
    orders_df = pd.read_csv(silver_datasets.orders_path)

    assert set(orders_df["customer_id"]).issubset(set(customers_df["customer_id"]))
    assert len(orders_df) == 1


def test_gold_star_schema_outputs_expected_tables(tmp_path: Path) -> None:
    customers_path = tmp_path / "silver_customers.csv"
    orders_path = tmp_path / "silver_orders.csv"
    gold_dir = tmp_path / "gold"

    pd.DataFrame(
        {
            "customer_id": [1, 2],
            "signup_date": ["2025-01-01", "2025-01-03"],
            "channel": ["Organic", "Paid Search"],
            "segment": ["SMB", "Enterprise"],
        }
    ).to_csv(customers_path, index=False)
    pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "customer_id": [1, 2],
            "order_date": ["2025-01-10", "2025-01-15"],
            "order_value": [100.0, 300.0],
        }
    ).to_csv(orders_path, index=False)

    build_star_schema(customers_path, orders_path, gold_dir)

    dim_date = pd.read_csv(gold_dir / "dim_date.csv")
    dim_channel = pd.read_csv(gold_dir / "dim_channel.csv")
    fact_orders = pd.read_csv(gold_dir / "fact_orders.csv")

    assert {"date_key", "week_of_year", "day_of_week"}.issubset(dim_date.columns)
    assert {"channel_key", "channel"}.issubset(dim_channel.columns)
    assert {"channel_key", "order_amount", "order_count"}.issubset(fact_orders.columns)
