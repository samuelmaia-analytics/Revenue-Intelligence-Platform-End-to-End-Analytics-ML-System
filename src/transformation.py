from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.io_utils import atomic_write_csv

OLIST_SUPPORT_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "sellers": "olist_sellers_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

STATUS_OPEN = {"approved", "created", "invoiced", "processing", "shipped"}
STATUS_CANCELED = {"canceled", "unavailable"}


def _validate_columns(df: pd.DataFrame, required: set[str], table_name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{table_name} missing required columns: {sorted(missing)}")


def _normalize_payment_channel(series: pd.Series) -> pd.Series:
    mapping = {
        "credit_card": "Credit Card",
        "credit card": "Credit Card",
        "boleto": "Boleto",
        "voucher": "Voucher",
        "debit_card": "Debit Card",
        "debit card": "Debit Card",
        "not_defined": "Other",
        "not defined": "Other",
        "other": "Other",
    }
    return (
        series.fillna("not_defined")
        .astype(str)
        .str.strip()
        .str.lower()
        .map(mapping)
        .fillna("Other")
    )


def _segment_from_value(values: pd.Series) -> pd.Series:
    ranked = values.fillna(0).rank(method="first")
    if ranked.nunique() < 3:
        return pd.Series(["SMB"] * len(values), index=values.index)
    return pd.qcut(ranked, q=3, labels=["SMB", "Mid-Market", "Enterprise"]).astype(str)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def _coalesce_columns(frame: pd.DataFrame, base_name: str) -> pd.DataFrame:
    if base_name in frame.columns:
        return frame
    left = f"{base_name}_x"
    right = f"{base_name}_y"
    if left in frame.columns or right in frame.columns:
        primary = (
            frame[right] if right in frame.columns else pd.Series(index=frame.index, dtype=object)
        )
        fallback = (
            frame[left] if left in frame.columns else pd.Series(index=frame.index, dtype=object)
        )
        frame[base_name] = primary.fillna(fallback)
        frame = frame.drop(columns=[left, right], errors="ignore")
    return frame


def _olist_raw_dir_from_silver_dir(silver_dir: Path) -> Path:
    return silver_dir.parent / "raw"


def _olist_support_available(raw_dir: Path) -> bool:
    return all((raw_dir / file_name).exists() for file_name in OLIST_SUPPORT_FILES.values())


def _build_generic_silver(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    marketing: pd.DataFrame,
    silver_dir: Path,
) -> tuple[Path, Path, Path]:
    customers = customers.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore")
    orders = orders.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore")
    marketing = marketing.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore")

    customers = customers.drop_duplicates(subset=["customer_id"]).copy()
    orders = orders.drop_duplicates(subset=["order_id"]).copy()
    marketing = marketing.drop_duplicates(subset=["channel"]).copy()

    customers["customer_id"] = customers["customer_id"].astype(int)
    orders["customer_id"] = orders["customer_id"].astype(int)
    orders["order_value"] = pd.to_numeric(orders["order_value"], errors="coerce").fillna(0.0)
    marketing["marketing_spend"] = (
        pd.to_numeric(marketing["marketing_spend"], errors="coerce").fillna(0.0).clip(lower=0)
    )

    customers = customers.dropna(subset=["customer_id", "signup_date", "channel", "segment"]).copy()
    valid_customers = set(customers["customer_id"].tolist())
    orders = orders[orders["customer_id"].isin(valid_customers)].copy()
    orders = orders.dropna(subset=["order_id", "customer_id", "order_date"]).copy()
    orders = orders[orders["order_value"] > 0].copy()
    marketing = marketing.dropna(subset=["channel"]).copy()

    silver_customers_path = silver_dir / "silver_customers.csv"
    silver_orders_path = silver_dir / "silver_orders.csv"
    silver_marketing_path = silver_dir / "silver_marketing_spend.csv"
    atomic_write_csv(silver_customers_path, customers)
    atomic_write_csv(silver_orders_path, orders)
    atomic_write_csv(silver_marketing_path, marketing)
    return silver_customers_path, silver_orders_path, silver_marketing_path


def _load_olist_support_frames(raw_dir: Path) -> dict[str, pd.DataFrame]:
    orders = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["orders"], low_memory=False)
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    orders["order_approved_at"] = pd.to_datetime(orders["order_approved_at"], errors="coerce")
    orders["order_delivered_carrier_date"] = pd.to_datetime(
        orders["order_delivered_carrier_date"], errors="coerce"
    )
    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )
    orders["order_estimated_delivery_date"] = pd.to_datetime(
        orders["order_estimated_delivery_date"], errors="coerce"
    )

    order_items = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["order_items"], low_memory=False)
    order_items["price"] = pd.to_numeric(order_items["price"], errors="coerce").fillna(0.0)
    order_items["freight_value"] = pd.to_numeric(
        order_items["freight_value"], errors="coerce"
    ).fillna(0.0)
    order_items["shipping_limit_date"] = pd.to_datetime(
        order_items["shipping_limit_date"], errors="coerce"
    )

    order_payments = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["order_payments"], low_memory=False)
    order_payments["payment_value"] = pd.to_numeric(
        order_payments["payment_value"], errors="coerce"
    ).fillna(0.0)
    order_payments["payment_installments"] = pd.to_numeric(
        order_payments["payment_installments"], errors="coerce"
    ).fillna(0.0)

    order_reviews = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["order_reviews"], low_memory=False)
    order_reviews["review_score"] = pd.to_numeric(
        order_reviews["review_score"], errors="coerce"
    ).fillna(np.nan)
    order_reviews["review_creation_date"] = pd.to_datetime(
        order_reviews["review_creation_date"], errors="coerce"
    )
    order_reviews["review_answer_timestamp"] = pd.to_datetime(
        order_reviews["review_answer_timestamp"], errors="coerce"
    )

    products = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["products"], low_memory=False)
    translation = pd.read_csv(
        raw_dir / OLIST_SUPPORT_FILES["category_translation"], low_memory=False
    )
    sellers = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["sellers"], low_memory=False)
    customers = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["customers"], low_memory=False)
    geolocation = pd.read_csv(raw_dir / OLIST_SUPPORT_FILES["geolocation"], low_memory=False)
    geolocation = (
        geolocation.groupby(
            ["geolocation_zip_code_prefix", "geolocation_city", "geolocation_state"]
        )
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
        )
        .reset_index()
    )
    return {
        "orders": orders,
        "order_items": order_items,
        "order_payments": order_payments,
        "order_reviews": order_reviews,
        "products": products,
        "translation": translation,
        "sellers": sellers,
        "customers_raw": customers,
        "geolocation": geolocation,
    }


def _build_olist_silver(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    marketing: pd.DataFrame,
    silver_dir: Path,
) -> tuple[Path, Path, Path]:
    raw_dir = _olist_raw_dir_from_silver_dir(silver_dir)
    support = _load_olist_support_frames(raw_dir)

    customers = customers.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").copy()
    orders = orders.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").copy()
    marketing = marketing.drop(columns=["_source_file", "_ingestion_ts"], errors="ignore").copy()

    customers["customer_id"] = customers["customer_id"].astype(int)
    orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce").astype("Int64")
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["order_value"] = pd.to_numeric(orders["order_value"], errors="coerce").fillna(0.0)
    customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="coerce")
    marketing["marketing_spend"] = (
        pd.to_numeric(marketing["marketing_spend"], errors="coerce").fillna(0.0).clip(lower=0)
    )
    customers = customers.dropna(subset=["customer_id", "signup_date"]).drop_duplicates(
        subset=["customer_id"]
    )
    orders = orders.dropna(subset=["customer_id", "order_id", "order_date"]).drop_duplicates(
        subset=["order_id"]
    )
    orders["customer_id"] = orders["customer_id"].astype(int)

    support_orders = support["orders"][
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ].drop_duplicates(subset=["order_id"])
    raw_customers = support["customers_raw"][
        [
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].drop_duplicates(subset=["customer_unique_id"])

    customer_lookup = customers.merge(
        raw_customers,
        on="customer_unique_id",
        how="left",
        suffixes=("", "_raw"),
    )
    customer_lookup = customer_lookup.assign(
        customer_city=lambda frame: frame["customer_city"].fillna(frame.get("customer_city_raw")),
        customer_state=lambda frame: frame["customer_state"].fillna(
            frame.get("customer_state_raw")
        ),
    )
    customer_lookup = customer_lookup.drop(
        columns=[column for column in customer_lookup.columns if column.endswith("_raw")],
        errors="ignore",
    )
    customer_lookup = customer_lookup.drop_duplicates(subset=["customer_id"])

    payment_summary = (
        support["order_payments"]
        .assign(
            payment_type_normalized=lambda frame: _normalize_payment_channel(frame["payment_type"])
        )
        .groupby("order_id")
        .agg(
            payment_value=("payment_value", "sum"),
            payment_installments=("payment_installments", "max"),
            payment_records=("payment_sequential", "count"),
            payment_type=(
                "payment_type_normalized",
                lambda values: values.mode().iat[0] if not values.mode().empty else "Other",
            ),
        )
        .reset_index()
    )
    review_summary = (
        support["order_reviews"]
        .groupby("order_id")
        .agg(
            review_score=("review_score", "mean"),
            review_count=("review_id", "nunique"),
            review_created_at=("review_creation_date", "min"),
        )
        .reset_index()
    )
    item_summary = (
        support["order_items"]
        .assign(
            gross_merchandise_value=lambda frame: frame["price"],
            total_line_value=lambda frame: frame["price"] + frame["freight_value"],
        )
        .groupby("order_id")
        .agg(
            items_count=("order_item_id", "count"),
            distinct_products=("product_id", "nunique"),
            distinct_sellers=("seller_id", "nunique"),
            gross_merchandise_value=("gross_merchandise_value", "sum"),
            freight_value=("freight_value", "sum"),
            total_line_value=("total_line_value", "sum"),
        )
        .reset_index()
    )

    silver_orders = (
        orders.merge(support_orders, on="order_id", how="left", suffixes=("", "_raw"))
        .merge(customer_lookup, on="customer_id", how="left", suffixes=("", "_customer"))
        .merge(item_summary, on="order_id", how="left")
        .merge(payment_summary, on="order_id", how="left")
        .merge(review_summary, on="order_id", how="left")
    )
    if "payment_type_x" in silver_orders.columns or "payment_type_y" in silver_orders.columns:
        payment_type_primary = (
            silver_orders["payment_type_y"]
            if "payment_type_y" in silver_orders.columns
            else pd.Series(index=silver_orders.index, dtype=object)
        )
        payment_type_fallback = (
            silver_orders["payment_type_x"]
            if "payment_type_x" in silver_orders.columns
            else pd.Series(index=silver_orders.index, dtype=object)
        )
        silver_orders["payment_type"] = payment_type_primary.fillna(payment_type_fallback)
        silver_orders = silver_orders.drop(
            columns=["payment_type_x", "payment_type_y"], errors="ignore"
        )
    silver_orders["order_status"] = silver_orders["order_status"].fillna("unknown")
    silver_orders["payment_type"] = silver_orders["payment_type"].fillna(silver_orders["channel"])
    silver_orders["payment_type"] = _normalize_payment_channel(silver_orders["payment_type"])
    silver_orders["gross_merchandise_value"] = silver_orders["gross_merchandise_value"].fillna(
        silver_orders["order_value"]
    )
    silver_orders["freight_value"] = silver_orders["freight_value"].fillna(0.0)
    silver_orders["payment_value"] = silver_orders["payment_value"].fillna(
        silver_orders["order_value"]
    )
    silver_orders["items_count"] = silver_orders["items_count"].fillna(0).astype(int)
    silver_orders["distinct_products"] = silver_orders["distinct_products"].fillna(0).astype(int)
    silver_orders["distinct_sellers"] = silver_orders["distinct_sellers"].fillna(0).astype(int)
    silver_orders["review_count"] = silver_orders["review_count"].fillna(0).astype(int)
    silver_orders["payment_installments"] = (
        silver_orders["payment_installments"].fillna(0).astype(int)
    )
    silver_orders["payment_records"] = silver_orders["payment_records"].fillna(0).astype(int)
    silver_orders["order_purchase_timestamp"] = silver_orders["order_purchase_timestamp"].fillna(
        silver_orders["order_date"]
    )
    silver_orders["delivery_days"] = (
        silver_orders["order_delivered_customer_date"] - silver_orders["order_purchase_timestamp"]
    ).dt.days
    silver_orders["estimated_delivery_days"] = (
        silver_orders["order_estimated_delivery_date"] - silver_orders["order_purchase_timestamp"]
    ).dt.days
    silver_orders["delivery_delay_days"] = (
        silver_orders["order_delivered_customer_date"]
        - silver_orders["order_estimated_delivery_date"]
    ).dt.days
    silver_orders["delivery_delay_days"] = (
        silver_orders["delivery_delay_days"].fillna(0).clip(lower=-60, upper=180)
    )
    silver_orders["delivery_days"] = silver_orders["delivery_days"].clip(lower=0, upper=180)
    silver_orders["estimated_delivery_days"] = silver_orders["estimated_delivery_days"].clip(
        lower=0, upper=180
    )
    silver_orders["is_late"] = (
        silver_orders["order_status"].eq("delivered") & (silver_orders["delivery_delay_days"] > 0)
    ).astype(int)
    silver_orders["is_canceled"] = silver_orders["order_status"].isin(STATUS_CANCELED).astype(int)
    silver_orders["is_open"] = silver_orders["order_status"].isin(STATUS_OPEN).astype(int)
    silver_orders["is_delivered"] = silver_orders["order_status"].eq("delivered").astype(int)
    silver_orders["order_value"] = silver_orders["payment_value"].clip(lower=0)
    silver_orders["channel"] = silver_orders["payment_type"]
    silver_orders = silver_orders.sort_values(["order_purchase_timestamp", "order_id"]).reset_index(
        drop=True
    )

    customer_order_summary = (
        silver_orders.groupby("customer_id")
        .agg(
            signup_date=("order_purchase_timestamp", "min"),
            latest_order_at=("order_purchase_timestamp", "max"),
            total_orders=("order_id", "nunique"),
            delivered_orders=("is_delivered", "sum"),
            canceled_orders=("is_canceled", "sum"),
            total_revenue=("order_value", "sum"),
            total_freight=("freight_value", "sum"),
            avg_ticket=("order_value", "mean"),
            avg_review_score=("review_score", "mean"),
            late_order_rate=("is_late", "mean"),
            channel=(
                "channel",
                lambda values: values.mode().iat[0] if not values.mode().empty else "Other",
            ),
        )
        .reset_index()
    )
    silver_customers = customer_lookup.merge(customer_order_summary, on="customer_id", how="left")
    silver_customers["signup_date"] = silver_customers["signup_date_y"].fillna(
        silver_customers["signup_date_x"]
    )
    silver_customers = silver_customers.drop(
        columns=["signup_date_x", "signup_date_y"], errors="ignore"
    )
    silver_customers["segment"] = _segment_from_value(
        silver_customers["total_revenue"].fillna(silver_customers.get("total_spend", 0))
    )
    silver_customers["channel"] = silver_customers["channel_y"].fillna(
        silver_customers["channel_x"]
    )
    silver_customers = silver_customers.drop(columns=["channel_x", "channel_y"], errors="ignore")
    silver_customers["total_orders"] = silver_customers["total_orders"].fillna(
        silver_customers.get("order_count", 0)
    )
    silver_customers["delivered_orders"] = (
        silver_customers["delivered_orders"].fillna(0).astype(int)
    )
    silver_customers["canceled_orders"] = silver_customers["canceled_orders"].fillna(0).astype(int)
    silver_customers["late_order_rate"] = silver_customers["late_order_rate"].fillna(0.0)
    silver_customers["avg_review_score"] = silver_customers["avg_review_score"].fillna(0.0)
    silver_customers["avg_ticket"] = silver_customers["avg_ticket"].fillna(0.0)
    silver_customers["total_revenue"] = silver_customers["total_revenue"].fillna(
        silver_customers.get("total_spend", 0.0)
    )
    silver_customers["total_freight"] = silver_customers["total_freight"].fillna(0.0)
    silver_customers["is_repeat_customer"] = (
        silver_customers["total_orders"].fillna(0) >= 2
    ).astype(int)
    silver_customers = silver_customers.sort_values("customer_id").reset_index(drop=True)

    translation = support["translation"].rename(
        columns={"product_category_name_english": "category_name_english"}
    )
    silver_products = support["products"].merge(translation, on="product_category_name", how="left")
    silver_products["category_name_english"] = silver_products["category_name_english"].fillna(
        silver_products["product_category_name"].fillna("unknown")
    )
    silver_products = silver_products.rename(columns={"product_category_name": "category_name_pt"})

    silver_sellers = support["sellers"].rename(
        columns={
            "seller_zip_code_prefix": "zip_code_prefix",
            "seller_city": "seller_city",
            "seller_state": "seller_state",
        }
    )

    order_customer_columns = [
        "order_id",
        "customer_id",
        "customer_unique_id",
        "customer_city",
        "customer_state",
        "order_status",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
        "review_score",
        "delivery_days",
        "delivery_delay_days",
    ]
    silver_order_items = (
        support["order_items"]
        .merge(silver_products, on="product_id", how="left")
        .merge(silver_sellers, on="seller_id", how="left")
        .merge(silver_orders[order_customer_columns], on="order_id", how="left")
        .assign(
            line_revenue=lambda frame: frame["price"] + frame["freight_value"],
            volume_cm3=lambda frame: frame["product_length_cm"].fillna(0)
            * frame["product_height_cm"].fillna(0)
            * frame["product_width_cm"].fillna(0),
        )
    )
    silver_order_items["is_delivered"] = (
        silver_order_items["order_status"].eq("delivered").astype(int)
    )

    silver_payments = support["order_payments"].assign(
        payment_type_normalized=lambda frame: _normalize_payment_channel(frame["payment_type"])
    )
    silver_reviews = support["order_reviews"].copy()

    silver_geography = (
        silver_orders.groupby(["customer_state", "customer_city"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("order_value", "sum"),
            unique_customers=("customer_id", "nunique"),
            avg_review_score=("review_score", "mean"),
            late_order_rate=("is_late", "mean"),
        )
        .reset_index()
        .sort_values(["total_revenue", "total_orders"], ascending=[False, False])
    )

    marketing = marketing.copy()
    channel_revenue = (
        silver_orders.groupby("channel")["customer_id"]
        .nunique()
        .reset_index(name="customers_acquired")
    )
    marketing = marketing.merge(channel_revenue, on="channel", how="outer").fillna(
        {"marketing_spend": 0.0, "customers_acquired": 0}
    )
    marketing["marketing_spend"] = marketing["marketing_spend"].clip(lower=0)
    marketing["customers_acquired"] = marketing["customers_acquired"].astype(int)

    silver_customers_path = silver_dir / "silver_customers.csv"
    silver_orders_path = silver_dir / "silver_orders.csv"
    silver_marketing_path = silver_dir / "silver_marketing_spend.csv"
    atomic_write_csv(silver_customers_path, silver_customers)
    atomic_write_csv(silver_orders_path, silver_orders)
    atomic_write_csv(silver_marketing_path, marketing)
    atomic_write_csv(silver_dir / "silver_products.csv", silver_products)
    atomic_write_csv(silver_dir / "silver_sellers.csv", silver_sellers)
    atomic_write_csv(silver_dir / "silver_order_items.csv", silver_order_items)
    atomic_write_csv(silver_dir / "silver_payments.csv", silver_payments)
    atomic_write_csv(silver_dir / "silver_reviews.csv", silver_reviews)
    atomic_write_csv(silver_dir / "silver_geography.csv", silver_geography)
    return silver_customers_path, silver_orders_path, silver_marketing_path


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

    _validate_columns(
        customers,
        {"customer_id", "signup_date", "channel", "segment"},
        "bronze_customers",
    )
    _validate_columns(
        orders, {"order_id", "customer_id", "order_date", "order_value"}, "bronze_orders"
    )
    _validate_columns(marketing, {"channel", "marketing_spend"}, "bronze_marketing_spend")

    raw_dir = _olist_raw_dir_from_silver_dir(silver_dir)
    if _olist_support_available(raw_dir):
        return _build_olist_silver(customers, orders, marketing, silver_dir)
    return _build_generic_silver(customers, orders, marketing, silver_dir)


def build_customer_features(
    customers_path: Path, orders_path: Path, output_dir: Path
) -> pd.DataFrame:
    customers = pd.read_csv(customers_path, parse_dates=["signup_date"])
    order_columns = pd.read_csv(orders_path, nrows=0).columns.tolist()
    orders = pd.read_csv(
        orders_path,
        parse_dates=[
            column
            for column in ["order_date", "order_purchase_timestamp"]
            if column in order_columns
        ],
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    event_date_column = (
        "order_purchase_timestamp" if "order_purchase_timestamp" in orders.columns else "order_date"
    )
    orders["event_date"] = pd.to_datetime(orders[event_date_column], errors="coerce").fillna(
        orders["order_date"]
    )
    default_columns = {
        "freight_value": 0.0,
        "is_delivered": 0,
        "is_canceled": 0,
        "review_score": 0.0,
        "is_late": 0.0,
        "delivery_days": 0.0,
    }
    for column, default_value in default_columns.items():
        if column not in orders.columns:
            orders[column] = default_value
    max_order_date = orders["event_date"].max()
    as_of_date = max_order_date - pd.Timedelta(days=120)
    hist_orders = orders[orders["event_date"] <= as_of_date].copy()
    future_30 = orders[
        (orders["event_date"] > as_of_date)
        & (orders["event_date"] <= as_of_date + pd.Timedelta(days=30))
    ].copy()
    future_90 = orders[
        (orders["event_date"] > as_of_date)
        & (orders["event_date"] <= as_of_date + pd.Timedelta(days=90))
    ].copy()

    agg = (
        hist_orders.groupby("customer_id")
        .agg(
            last_order_date=("event_date", "max"),
            frequency=("order_id", "count"),
            monetary=("order_value", "sum"),
            avg_order_value=("order_value", "mean"),
            total_freight=("freight_value", "sum"),
            delivered_orders=("is_delivered", "sum"),
            canceled_orders=("is_canceled", "sum"),
            avg_review_score=("review_score", "mean"),
            late_order_rate=("is_late", "mean"),
            avg_delivery_days=("delivery_days", "mean"),
        )
        .reset_index()
    )

    features = customers.merge(agg, on="customer_id", how="left")
    for column in [
        "total_freight",
        "delivered_orders",
        "canceled_orders",
        "avg_review_score",
        "late_order_rate",
        "avg_delivery_days",
    ]:
        features = _coalesce_columns(features, column)
    features["frequency"] = features["frequency"].fillna(0)
    features["monetary"] = features["monetary"].fillna(0.0)
    features["avg_order_value"] = features["avg_order_value"].fillna(0.0)
    features["total_freight"] = features["total_freight"].fillna(0.0)
    features["delivered_orders"] = features["delivered_orders"].fillna(0).astype(int)
    features["canceled_orders"] = features["canceled_orders"].fillna(0).astype(int)
    features["avg_review_score"] = features["avg_review_score"].fillna(0.0)
    features["late_order_rate"] = features["late_order_rate"].fillna(0.0)
    features["avg_delivery_days"] = features["avg_delivery_days"].fillna(0.0)
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
    features["is_churned"] = np.where(
        eligible, (features["future_orders_90d"] == 0).astype(int), np.nan
    )
    features["next_purchase_30d"] = np.where(
        eligible, (features["future_orders_30d"] > 0).astype(int), np.nan
    )
    features["arpu"] = np.where(
        features["tenure_days"] > 0, features["monetary"] / (features["tenure_days"] / 30), 0
    )
    features["freight_ratio"] = _safe_divide(
        features["total_freight"], features["monetary"]
    ).fillna(0.0)
    features["review_score_filled"] = features["avg_review_score"].replace(0, np.nan).fillna(3.5)
    features["late_order_rate"] = features["late_order_rate"].fillna(0.0)
    features["repeat_customer_flag"] = (features["frequency"] >= 2).astype(int)
    features["ltv_proxy"] = (
        features["monetary"]
        * (1 + features["repeat_customer_flag"] * 0.35)
        * (0.75 + features["review_score_filled"] / 10)
    ).clip(lower=0)
    features["churn_risk_proxy"] = (
        0.45 * (features["recency_days"] / features["recency_days"].clip(lower=1).max())
        + 0.20 * (1 - np.clip(features["frequency"] / max(features["frequency"].max(), 1), 0, 1))
        + 0.20 * features["late_order_rate"].clip(0, 1)
        + 0.15 * (1 - np.clip(features["review_score_filled"] / 5, 0, 1))
    ).clip(0, 1)
    features["next_purchase_propensity_proxy"] = (
        0.35 * np.clip(features["frequency"] / max(features["frequency"].max(), 1), 0, 1)
        + 0.30 * np.clip(features["review_score_filled"] / 5, 0, 1)
        + 0.20
        * (
            1
            - np.clip(features["recency_days"] / features["recency_days"].clip(lower=1).max(), 0, 1)
        )
        + 0.15 * (1 - features["late_order_rate"].clip(0, 1))
    ).clip(0, 1)
    features["as_of_date"] = as_of_date

    atomic_write_csv(output_dir / "customer_features.csv", features)
    return features
