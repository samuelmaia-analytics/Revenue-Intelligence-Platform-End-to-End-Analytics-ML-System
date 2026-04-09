from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from src.io_utils import atomic_write_csv, atomic_write_json
from src.runtime import compute_file_fingerprint

CHANNELS = ["Organic", "Paid Search", "Social Ads", "Referral", "Partnership"]
KAGGLE_FILE = "E-commerce Customer Behavior - Sheet1.csv"
OLIST_CUSTOMERS_FILE = "olist_customers_dataset.csv"
OLIST_ORDERS_FILE = "olist_orders_dataset.csv"
OLIST_ORDER_ITEMS_FILE = "olist_order_items_dataset.csv"
OLIST_ORDER_PAYMENTS_FILE = "olist_order_payments_dataset.csv"
OLIST_REQUIRED_FILES = [
    OLIST_CUSTOMERS_FILE,
    OLIST_ORDERS_FILE,
    OLIST_ORDER_ITEMS_FILE,
    OLIST_ORDER_PAYMENTS_FILE,
]
OLIST_NORMALIZATION_MANIFEST = "olist_normalization_manifest.json"


def _coerce_signup_date(value: Any) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _coerce_int(value: Any) -> int:
    return int(value)


def _coerce_float(value: Any) -> float:
    return float(value)


def generate_synthetic_data(
    n_customers: int = 2500, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    today = pd.Timestamp.today().normalize()

    customer_ids = np.arange(1, n_customers + 1)
    signup_offsets = rng.integers(30, 730, size=n_customers)
    signup_dates = today - pd.to_timedelta(signup_offsets, unit="D")
    channels = rng.choice(CHANNELS, size=n_customers, p=[0.3, 0.24, 0.2, 0.16, 0.1])
    segments = rng.choice(["SMB", "Mid-Market", "Enterprise"], size=n_customers, p=[0.6, 0.3, 0.1])

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "signup_date": signup_dates,
            "channel": channels,
            "segment": segments,
        }
    )

    churn_risk = {"SMB": 0.38, "Mid-Market": 0.28, "Enterprise": 0.18}
    order_rows = []
    for row in customers.itertuples(index=False):
        signup_date = _coerce_signup_date(row.signup_date)
        segment = cast(str, row.segment)
        customer_id = _coerce_int(row.customer_id)
        tenure_days = max((today - signup_date).days, 1)
        expected_orders = max(1, int(tenure_days / 45))
        num_orders = rng.poisson(lam=expected_orders * 0.6) + 1
        if rng.random() < churn_risk[segment]:
            num_orders = max(1, int(num_orders * 0.4))

        order_days = rng.integers(1, tenure_days + 1, size=num_orders)
        order_dates = sorted(signup_date + pd.to_timedelta(order_days, unit="D"))
        base_value = {"SMB": 120, "Mid-Market": 320, "Enterprise": 950}[segment]
        order_values = np.clip(rng.normal(base_value, base_value * 0.35, size=num_orders), 25, None)

        for idx, (order_date, order_value) in enumerate(
            zip(order_dates, order_values, strict=False), start=1
        ):
            order_rows.append(
                {
                    "order_id": f"O{customer_id:05d}-{idx:03d}",
                    "customer_id": customer_id,
                    "order_date": pd.Timestamp(order_date).normalize(),
                    "order_value": round(float(order_value), 2),
                }
            )

    orders = pd.DataFrame(order_rows)
    orders = orders.sort_values("order_date").reset_index(drop=True)

    marketing = pd.DataFrame(
        {
            "channel": CHANNELS,
            "marketing_spend": [42000, 68000, 52000, 18000, 26000],
        }
    )
    return customers, orders, marketing


def _build_from_kaggle_dataset(
    kaggle_path: Path, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    today = pd.Timestamp.today().normalize()
    raw = pd.read_csv(kaggle_path)

    rename_map = {
        "Customer ID": "customer_id",
        "Gender": "gender",
        "Age": "age",
        "City": "city",
        "Membership Type": "membership_type",
        "Total Spend": "total_spend",
        "Items Purchased": "items_purchased",
        "Average Rating": "average_rating",
        "Discount Applied": "discount_applied",
        "Days Since Last Purchase": "days_since_last_purchase",
        "Satisfaction Level": "satisfaction_level",
    }
    df = raw.rename(columns=rename_map).copy()

    segment_map = {"Bronze": "SMB", "Silver": "Mid-Market", "Gold": "Enterprise"}
    df["segment"] = df["membership_type"].map(segment_map).fillna("SMB")
    df["channel"] = rng.choice(CHANNELS, size=len(df), p=[0.28, 0.27, 0.2, 0.15, 0.1])

    tenure_days = rng.integers(120, 730, size=len(df))
    recency_days = df["days_since_last_purchase"].fillna(30).astype(int).clip(lower=1)
    signup_date = today - pd.to_timedelta(tenure_days, unit="D")

    customers = df[
        [
            "customer_id",
            "channel",
            "segment",
            "gender",
            "age",
            "city",
            "membership_type",
            "satisfaction_level",
        ]
    ].copy()
    customers["signup_date"] = signup_date
    customers = customers[
        [
            "customer_id",
            "signup_date",
            "channel",
            "segment",
            "gender",
            "age",
            "city",
            "membership_type",
            "satisfaction_level",
        ]
    ]

    order_rows = []
    for row, tenure, recency in zip(
        df.itertuples(index=False), tenure_days, recency_days, strict=False
    ):
        customer_id = _coerce_int(row.customer_id)
        items_purchased = max(1, _coerce_int(row.items_purchased))
        total_spend = _coerce_float(row.total_spend)
        customer_signup = today - pd.Timedelta(days=int(tenure))
        n_orders = items_purchased
        avg_ticket = total_spend / n_orders
        std_ticket = max(5.0, avg_ticket * 0.25)

        if n_orders == 1:
            order_dates = [today - pd.Timedelta(days=int(recency))]
        else:
            max_hist_days = max(int(tenure) - int(recency), 1)
            hist_days = sorted(rng.integers(1, max_hist_days + 1, size=n_orders - 1).tolist())
            order_dates = [customer_signup + pd.Timedelta(days=int(d)) for d in hist_days]
            order_dates.append(today - pd.Timedelta(days=int(recency)))

        order_values = np.clip(rng.normal(avg_ticket, std_ticket, size=n_orders), 5, None)
        correction = total_spend / float(order_values.sum())
        order_values = order_values * correction

        for idx, (order_date, order_value) in enumerate(
            zip(order_dates, order_values, strict=False), start=1
        ):
            order_rows.append(
                {
                    "order_id": f"O{customer_id:05d}-{idx:03d}",
                    "customer_id": customer_id,
                    "order_date": pd.Timestamp(order_date).normalize(),
                    "order_value": round(float(order_value), 2),
                }
            )

    orders = pd.DataFrame(order_rows).sort_values("order_date").reset_index(drop=True)
    acquired = (
        customers.groupby("channel")["customer_id"].count().reset_index(name="customers_acquired")
    )
    acquired["base_cac"] = acquired["channel"].map(
        {
            "Organic": 70,
            "Paid Search": 180,
            "Social Ads": 150,
            "Referral": 55,
            "Partnership": 130,
        }
    )
    acquired["marketing_spend"] = (acquired["customers_acquired"] * acquired["base_cac"]).round(0)
    marketing = acquired[["channel", "marketing_spend"]]
    return customers, orders, marketing


def _olist_files_present(raw_dir: Path) -> bool:
    return all((raw_dir / file_name).exists() for file_name in OLIST_REQUIRED_FILES)


def _olist_source_paths(raw_dir: Path) -> list[Path]:
    return [raw_dir / file_name for file_name in OLIST_REQUIRED_FILES]


def _olist_outputs_exist(raw_dir: Path) -> bool:
    return all(
        (raw_dir / file_name).exists()
        for file_name in ["customers.csv", "orders.csv", "marketing_spend.csv"]
    )


def _can_reuse_olist_normalization(raw_dir: Path) -> bool:
    manifest_path = raw_dir / OLIST_NORMALIZATION_MANIFEST
    if not manifest_path.exists() or not _olist_outputs_exist(raw_dir):
        return False
    try:
        manifest = pd.read_json(manifest_path, typ="series")
    except ValueError:
        return False
    expected_fingerprint = compute_file_fingerprint(_olist_source_paths(raw_dir))
    return str(manifest.get("source_fingerprint", "")) == expected_fingerprint


def _normalize_payment_channel(value: Any) -> str:
    mapping = {
        "credit_card": "Credit Card",
        "boleto": "Boleto",
        "voucher": "Voucher",
        "debit_card": "Debit Card",
        "not_defined": "Other",
    }
    return mapping.get(str(value).strip().lower(), "Other")


def _segment_from_customer_value(customer_value: pd.Series) -> pd.Series:
    ranked = customer_value.rank(method="first")
    return pd.qcut(ranked, q=3, labels=["SMB", "Mid-Market", "Enterprise"]).astype(str)


def _build_from_olist_dataset(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers_raw = pd.read_csv(
        raw_dir / OLIST_CUSTOMERS_FILE,
        usecols=[
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
        ],
        low_memory=False,
    )
    orders_raw = pd.read_csv(
        raw_dir / OLIST_ORDERS_FILE,
        usecols=[
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
        low_memory=False,
    )
    order_items_raw = pd.read_csv(
        raw_dir / OLIST_ORDER_ITEMS_FILE,
        usecols=["order_id", "price", "freight_value"],
        low_memory=False,
    )
    order_payments_raw = pd.read_csv(
        raw_dir / OLIST_ORDER_PAYMENTS_FILE,
        usecols=["order_id", "payment_type", "payment_value"],
        low_memory=False,
    )

    orders_raw["order_purchase_timestamp"] = pd.to_datetime(
        orders_raw["order_purchase_timestamp"], errors="coerce"
    )
    delivered_orders = orders_raw.loc[
        orders_raw["order_purchase_timestamp"].notna()
        & orders_raw["order_status"].isin(["delivered", "shipped", "invoiced", "processing"])
    ].copy()

    payment_agg = (
        order_payments_raw.groupby("order_id")
        .agg(
            order_value=("payment_value", "sum"),
            payment_type=("payment_type", lambda values: values.mode().iat[0]),
        )
        .reset_index()
    )
    item_agg = (
        order_items_raw.assign(
            item_total=lambda frame: pd.to_numeric(frame["price"], errors="coerce").fillna(0.0)
            + pd.to_numeric(frame["freight_value"], errors="coerce").fillna(0.0)
        )
        .groupby("order_id")["item_total"]
        .sum()
        .reset_index(name="item_total")
    )

    orders_enriched = (
        delivered_orders.merge(payment_agg, on="order_id", how="left")
        .merge(item_agg, on="order_id", how="left")
        .merge(
            customers_raw[
                [
                    "customer_id",
                    "customer_unique_id",
                    "customer_city",
                    "customer_state",
                ]
            ],
            on="customer_id",
            how="left",
        )
    )
    orders_enriched["order_value"] = orders_enriched["order_value"].fillna(
        orders_enriched["item_total"]
    )
    orders_enriched["payment_type"] = orders_enriched["payment_type"].fillna("not_defined")
    orders_enriched = orders_enriched.loc[
        orders_enriched["customer_unique_id"].notna() & (orders_enriched["order_value"] > 0)
    ].copy()
    orders_enriched["channel"] = orders_enriched["payment_type"].map(_normalize_payment_channel)
    orders_enriched["order_date"] = orders_enriched["order_purchase_timestamp"].dt.normalize()

    customer_summary = (
        orders_enriched.groupby("customer_unique_id")
        .agg(
            signup_date=("order_purchase_timestamp", "min"),
            total_spend=("order_value", "sum"),
            order_count=("order_id", "nunique"),
            channel=("channel", lambda values: values.mode().iat[0]),
            customer_city=("customer_city", lambda values: values.dropna().iat[0]),
            customer_state=("customer_state", lambda values: values.dropna().iat[0]),
        )
        .reset_index()
        .sort_values("customer_unique_id")
        .reset_index(drop=True)
    )
    customer_summary["customer_id"] = customer_summary.index + 1
    customer_summary["signup_date"] = pd.to_datetime(customer_summary["signup_date"]).dt.normalize()
    customer_summary["segment"] = _segment_from_customer_value(customer_summary["total_spend"])

    customer_id_map = customer_summary[["customer_unique_id", "customer_id"]]
    customers = customer_summary[
        [
            "customer_id",
            "signup_date",
            "channel",
            "segment",
            "customer_city",
            "customer_state",
            "customer_unique_id",
            "total_spend",
            "order_count",
        ]
    ].copy()

    orders = (
        orders_enriched.merge(customer_id_map, on="customer_unique_id", how="inner")
        .rename(columns={"customer_id_y": "customer_id"})[
            ["order_id", "customer_id", "order_date", "order_value", "payment_type", "order_status"]
        ]
        .drop_duplicates(subset=["order_id"])
        .sort_values(["order_date", "order_id"])
        .reset_index(drop=True)
    )

    acquired = (
        customers.groupby("channel")["customer_id"].count().reset_index(name="customers_acquired")
    )
    acquired["base_cac"] = acquired["channel"].map(
        {
            "Credit Card": 150,
            "Boleto": 110,
            "Voucher": 75,
            "Debit Card": 95,
            "Other": 120,
        }
    ).fillna(120)
    acquired["marketing_spend"] = (acquired["customers_acquired"] * acquired["base_cac"]).round(0)
    marketing = acquired[["channel", "marketing_spend"]].copy()
    return customers, orders, marketing


def save_raw_datasets(raw_dir: Path, seed: int = 42) -> tuple[Path, Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    kaggle_path = raw_dir / KAGGLE_FILE
    if _olist_files_present(raw_dir):
        customers_path = raw_dir / "customers.csv"
        orders_path = raw_dir / "orders.csv"
        marketing_path = raw_dir / "marketing_spend.csv"
        if _can_reuse_olist_normalization(raw_dir):
            return customers_path, orders_path, marketing_path
        customers, orders, marketing = _build_from_olist_dataset(raw_dir)
    elif kaggle_path.exists():
        customers, orders, marketing = _build_from_kaggle_dataset(kaggle_path, seed=seed)
    else:
        customers, orders, marketing = generate_synthetic_data(seed=seed)

    customers_path = raw_dir / "customers.csv"
    orders_path = raw_dir / "orders.csv"
    marketing_path = raw_dir / "marketing_spend.csv"

    atomic_write_csv(customers_path, customers)
    atomic_write_csv(orders_path, orders)
    atomic_write_csv(marketing_path, marketing)

    if _olist_files_present(raw_dir):
        atomic_write_json(
            raw_dir / OLIST_NORMALIZATION_MANIFEST,
            {
                "source_fingerprint": compute_file_fingerprint(_olist_source_paths(raw_dir)),
                "normalized_outputs": [
                    customers_path.name,
                    orders_path.name,
                    marketing_path.name,
                ],
            },
        )

    return customers_path, orders_path, marketing_path


def build_bronze_layer(
    customers_path: Path, orders_path: Path, marketing_path: Path, bronze_dir: Path
) -> tuple[Path, Path, Path]:
    bronze_dir.mkdir(parents=True, exist_ok=True)
    ingestion_ts = pd.Timestamp.utcnow().isoformat()

    customers = pd.read_csv(customers_path)
    orders = pd.read_csv(orders_path)
    marketing = pd.read_csv(marketing_path)

    customers["_source_file"] = customers_path.name
    customers["_ingestion_ts"] = ingestion_ts
    orders["_source_file"] = orders_path.name
    orders["_ingestion_ts"] = ingestion_ts
    marketing["_source_file"] = marketing_path.name
    marketing["_ingestion_ts"] = ingestion_ts

    bronze_customers_path = bronze_dir / "bronze_customers.csv"
    bronze_orders_path = bronze_dir / "bronze_orders.csv"
    bronze_marketing_path = bronze_dir / "bronze_marketing_spend.csv"

    atomic_write_csv(bronze_customers_path, customers)
    atomic_write_csv(bronze_orders_path, orders)
    atomic_write_csv(bronze_marketing_path, marketing)

    return bronze_customers_path, bronze_orders_path, bronze_marketing_path
