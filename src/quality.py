from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from src.exceptions import DataQualityError
from src.io_utils import atomic_write_json


@dataclass(frozen=True)
class DatasetQualityReport:
    dataset_name: str
    row_count: int
    duplicate_rows: int
    null_counts: dict[str, int]
    null_fraction_by_column: dict[str, float]
    total_null_fraction: float
    referential_issues: int
    negative_value_counts: dict[str, int] | None = None
    domain_violations: dict[str, int] | None = None
    invalid_date_counts: dict[str, int] | None = None


def validate_required_columns(df: pd.DataFrame, required: set[str], dataset_name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise DataQualityError(f"{dataset_name} missing required columns: {sorted(missing)}")


def build_dataset_quality_report(
    df: pd.DataFrame,
    dataset_name: str,
    primary_key: str | None = None,
    foreign_key: str | None = None,
    valid_values: set[int] | None = None,
) -> DatasetQualityReport:
    duplicate_rows = (
        int(df[primary_key].duplicated().sum()) if primary_key else int(df.duplicated().sum())
    )
    referential_issues = 0
    if foreign_key and valid_values is not None and foreign_key in df.columns:
        referential_issues = int((~df[foreign_key].isin(valid_values)).sum())

    null_counts = {str(col): int(value) for col, value in df.isna().sum().to_dict().items()}
    denominator = max(len(df), 1)
    null_fraction_by_column = {
        column: round(count / denominator, 6) for column, count in null_counts.items()
    }
    total_cells = max(len(df) * max(len(df.columns), 1), 1)

    return DatasetQualityReport(
        dataset_name=dataset_name,
        row_count=int(len(df)),
        duplicate_rows=duplicate_rows,
        null_counts=null_counts,
        null_fraction_by_column=null_fraction_by_column,
        total_null_fraction=round(sum(null_counts.values()) / total_cells, 6),
        referential_issues=referential_issues,
    )


def enforce_quality_gate(
    reports: list[DatasetQualityReport],
    *,
    max_total_null_fraction: float | None = None,
) -> None:
    issues: list[str] = []
    for report in reports:
        if report.row_count == 0:
            issues.append(f"{report.dataset_name} is empty")
        if report.duplicate_rows > 0:
            issues.append(f"{report.dataset_name} has {report.duplicate_rows} duplicate keys/rows")
        if report.referential_issues > 0:
            issues.append(
                f"{report.dataset_name} has {report.referential_issues} referential integrity issues"
            )
        if (
            max_total_null_fraction is not None
            and report.total_null_fraction > max_total_null_fraction
        ):
            issues.append(
                f"{report.dataset_name} total null fraction "
                f"{report.total_null_fraction:.3f} exceeds {max_total_null_fraction:.3f}"
            )
    if issues:
        raise DataQualityError("; ".join(issues))


def write_quality_report(reports: list[DatasetQualityReport], output_path: Path) -> dict:
    payload = {
        "datasets": [asdict(report) for report in reports],
        "total_datasets": len(reports),
    }
    atomic_write_json(output_path, payload)
    return payload


def build_business_rule_report(
    *,
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    output_path: Path,
) -> dict[str, object]:
    status_domain = {
        "approved",
        "canceled",
        "created",
        "delivered",
        "invoiced",
        "processing",
        "shipped",
        "unavailable",
    }
    payment_mismatch = 0
    if {"payment_value", "gross_merchandise_value", "freight_value"}.issubset(orders_df.columns):
        expected_total = pd.to_numeric(
            orders_df["gross_merchandise_value"], errors="coerce"
        ).fillna(0.0) + pd.to_numeric(orders_df["freight_value"], errors="coerce").fillna(0.0)
        actual_total = pd.to_numeric(orders_df["payment_value"], errors="coerce").fillna(0.0)
        payment_mismatch = int((actual_total.sub(expected_total).abs() > 5.0).sum())

    delivery_outliers = 0
    if "delivery_days" in orders_df.columns:
        delivery = pd.to_numeric(orders_df["delivery_days"], errors="coerce").dropna()
        if not delivery.empty:
            threshold = float(delivery.quantile(0.99))
            delivery_outliers = int((delivery > threshold).sum())

    invalid_delivery_sequence_rows = 0
    if {"order_purchase_timestamp", "order_delivered_customer_date"}.issubset(orders_df.columns):
        purchased = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce")
        delivered = pd.to_datetime(orders_df["order_delivered_customer_date"], errors="coerce")
        invalid_delivery_sequence_rows = int(((delivered < purchased) & delivered.notna()).sum())

    invalid_estimated_delivery_rows = 0
    if {"order_purchase_timestamp", "order_estimated_delivery_date"}.issubset(orders_df.columns):
        purchased = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce")
        estimated = pd.to_datetime(orders_df["order_estimated_delivery_date"], errors="coerce")
        invalid_estimated_delivery_rows = int(((estimated < purchased) & estimated.notna()).sum())

    payload: dict[str, object] = {
        "checks": {
            "customer_id_uniqueness_violations": int(
                customers_df["customer_id"].duplicated().sum()
            ),
            "order_id_uniqueness_violations": int(orders_df["order_id"].duplicated().sum()),
            "missing_required_customer_fields": int(
                customers_df[["customer_id", "signup_date", "channel", "segment"]]
                .isna()
                .any(axis=1)
                .sum()
            ),
            "missing_required_order_fields": int(
                orders_df[["order_id", "customer_id", "order_date", "order_value"]]
                .isna()
                .any(axis=1)
                .sum()
            ),
            "negative_order_value_rows": int(
                (pd.to_numeric(orders_df["order_value"], errors="coerce").fillna(0.0) < 0).sum()
            ),
            "negative_freight_rows": int(
                (
                    pd.to_numeric(
                        orders_df.get("freight_value", pd.Series(0.0, index=orders_df.index)),
                        errors="coerce",
                    )
                    .fillna(0.0)
                    .lt(0)
                ).sum()
            ),
            "invalid_order_status_rows": (
                int(
                    (
                        ~orders_df.get("order_status", pd.Series(dtype=str))
                        .astype(str)
                        .isin(status_domain)
                    ).sum()
                )
                if "order_status" in orders_df.columns
                else 0
            ),
            "invalid_purchase_dates": int(
                pd.to_datetime(orders_df["order_date"], errors="coerce").isna().sum()
            ),
            "payment_value_mismatch_rows": payment_mismatch,
            "delivery_outlier_rows": delivery_outliers,
            "invalid_delivery_sequence_rows": invalid_delivery_sequence_rows,
            "invalid_estimated_delivery_rows": invalid_estimated_delivery_rows,
            "orphan_order_customer_rows": int(
                (~orders_df["customer_id"].isin(customers_df["customer_id"])).sum()
            ),
            "missing_customer_state_rows": (
                int(customers_df.get("customer_state", pd.Series(dtype=object)).isna().sum())
                if "customer_state" in customers_df.columns
                else 0
            ),
        }
    }
    checks = payload["checks"]
    if not isinstance(checks, dict):
        raise DataQualityError("Quality report checks must be a dictionary.")
    payload["status"] = "ok" if all(int(value) == 0 for value in checks.values()) else "warning"
    atomic_write_json(output_path, payload)
    return payload
