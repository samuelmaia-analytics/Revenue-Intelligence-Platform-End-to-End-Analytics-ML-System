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
    rule_violations: list[str]


DATASET_QUALITY_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "silver_customers": {
        "zero_null_columns": ("customer_id", "signup_date", "channel", "segment"),
    },
    "silver_orders": {
        "zero_null_columns": ("order_id", "customer_id", "order_date", "order_value"),
        "non_negative_columns": ("order_value",),
    },
    "silver_marketing": {
        "zero_null_columns": ("channel", "marketing_spend"),
        "non_negative_columns": ("marketing_spend",),
    },
}


def validate_required_columns(df: pd.DataFrame, required: set[str], dataset_name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise DataQualityError(f"{dataset_name} missing required columns: {sorted(missing)}")


def _evaluate_dataset_rules(df: pd.DataFrame, dataset_name: str) -> list[str]:
    rules = DATASET_QUALITY_RULES.get(dataset_name, {})
    violations: list[str] = []

    for column in rules.get("zero_null_columns", ()):
        if column in df.columns and int(df[column].isna().sum()) > 0:
            violations.append(f"{dataset_name}.{column} contains nulls")

    for column in rules.get("non_negative_columns", ()):
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        if bool((series < 0).fillna(False).any()):
            violations.append(f"{dataset_name}.{column} contains negative values")

    return violations


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
        str(column): round(count / denominator, 6) for column, count in null_counts.items()
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
        rule_violations=_evaluate_dataset_rules(df, dataset_name),
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
        if report.rule_violations:
            issues.extend(report.rule_violations)
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
