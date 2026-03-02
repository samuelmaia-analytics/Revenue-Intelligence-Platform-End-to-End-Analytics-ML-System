from pathlib import Path

import numpy as np
import pandas as pd


CHANNELS = ["Organic", "Paid Search", "Social Ads", "Referral", "Partnership"]
KAGGLE_FILE = "E-commerce Customer Behavior - Sheet1.csv"


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
        tenure_days = max((today - row.signup_date).days, 1)
        expected_orders = max(1, int(tenure_days / 45))
        num_orders = rng.poisson(lam=expected_orders * 0.6) + 1
        if rng.random() < churn_risk[row.segment]:
            num_orders = max(1, int(num_orders * 0.4))

        order_days = rng.integers(1, tenure_days + 1, size=num_orders)
        order_dates = sorted([row.signup_date + pd.Timedelta(days=int(x)) for x in order_days])
        base_value = {"SMB": 120, "Mid-Market": 320, "Enterprise": 950}[row.segment]
        order_values = np.clip(rng.normal(base_value, base_value * 0.35, size=num_orders), 25, None)

        for idx, (order_date, order_value) in enumerate(zip(order_dates, order_values), start=1):
            order_rows.append(
                {
                    "order_id": f"O{row.customer_id:05d}-{idx:03d}",
                    "customer_id": row.customer_id,
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
        ["customer_id", "channel", "segment", "gender", "age", "city", "membership_type", "satisfaction_level"]
    ].copy()
    customers["signup_date"] = signup_date
    customers = customers[
        ["customer_id", "signup_date", "channel", "segment", "gender", "age", "city", "membership_type", "satisfaction_level"]
    ]

    order_rows = []
    for row, tenure, recency in zip(df.itertuples(index=False), tenure_days, recency_days):
        customer_signup = today - pd.Timedelta(days=int(tenure))
        n_orders = int(max(1, row.items_purchased))
        avg_ticket = float(row.total_spend) / n_orders
        std_ticket = max(5.0, avg_ticket * 0.25)

        if n_orders == 1:
            order_dates = [today - pd.Timedelta(days=int(recency))]
        else:
            max_hist_days = max(int(tenure) - int(recency), 1)
            hist_days = sorted(rng.integers(1, max_hist_days + 1, size=n_orders - 1).tolist())
            order_dates = [customer_signup + pd.Timedelta(days=int(d)) for d in hist_days]
            order_dates.append(today - pd.Timedelta(days=int(recency)))

        order_values = np.clip(rng.normal(avg_ticket, std_ticket, size=n_orders), 5, None)
        correction = float(row.total_spend) / float(order_values.sum())
        order_values = order_values * correction

        for idx, (order_date, order_value) in enumerate(zip(order_dates, order_values), start=1):
            order_rows.append(
                {
                    "order_id": f"O{int(row.customer_id):05d}-{idx:03d}",
                    "customer_id": int(row.customer_id),
                    "order_date": pd.Timestamp(order_date).normalize(),
                    "order_value": round(float(order_value), 2),
                }
            )

    orders = pd.DataFrame(order_rows).sort_values("order_date").reset_index(drop=True)
    acquired = customers.groupby("channel")["customer_id"].count().reset_index(name="customers_acquired")
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


def save_raw_datasets(raw_dir: Path) -> tuple[Path, Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    kaggle_path = raw_dir / KAGGLE_FILE
    if kaggle_path.exists():
        customers, orders, marketing = _build_from_kaggle_dataset(kaggle_path)
    else:
        customers, orders, marketing = generate_synthetic_data()

    customers_path = raw_dir / "customers.csv"
    orders_path = raw_dir / "orders.csv"
    marketing_path = raw_dir / "marketing_spend.csv"

    customers.to_csv(customers_path, index=False)
    orders.to_csv(orders_path, index=False)
    marketing.to_csv(marketing_path, index=False)

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

    customers.to_csv(bronze_customers_path, index=False)
    orders.to_csv(bronze_orders_path, index=False)
    marketing.to_csv(bronze_marketing_path, index=False)

    return bronze_customers_path, bronze_orders_path, bronze_marketing_path
