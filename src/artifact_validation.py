from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from contracts.processed_contract import (
    CSV_ARTIFACT_SPECS,
    JSON_ARTIFACT_SPECS,
    PROCESSED_CONTRACT_VERSION,
)
from src.exceptions import DataQualityError
from src.io_utils import atomic_write_json


def _resolve_nested_key(payload: dict[str, object], dotted_key: str) -> object:
    current: object = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise DataQualityError(f"Missing required key path: {dotted_key}")
        current = current[part]
    return current


def _validate_csv_artifact(
    processed_dir: Path, file_name: str, required_columns: set[str]
) -> dict[str, object]:
    path = processed_dir / file_name
    if not path.exists():
        raise DataQualityError(f"Missing processed artifact: {file_name}")
    frame = pd.read_csv(path, nrows=5)
    missing_columns = sorted(required_columns.difference(frame.columns))
    if missing_columns:
        raise DataQualityError(f"{file_name} missing required columns: {missing_columns}")
    _validate_csv_artifact_values(file_name, frame)
    return {
        "artifact": file_name,
        "type": "csv",
        "required_columns": sorted(required_columns),
        "observed_columns": sorted(frame.columns.tolist()),
    }


def _validate_json_artifact(
    processed_dir: Path, file_name: str, required_keys: tuple[str, ...]
) -> dict[str, object]:
    path = processed_dir / file_name
    if not path.exists():
        raise DataQualityError(f"Missing processed artifact: {file_name}")
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    missing_keys: list[str] = []
    for dotted_key in required_keys:
        try:
            _resolve_nested_key(payload, dotted_key)
        except DataQualityError:
            missing_keys.append(dotted_key)
    if missing_keys:
        raise DataQualityError(f"{file_name} missing required key paths: {missing_keys}")
    _validate_json_artifact_values(file_name, payload)
    return {
        "artifact": file_name,
        "type": "json",
        "required_keys": list(required_keys),
    }


def _validate_numeric_bounds(
    file_name: str,
    frame: pd.DataFrame,
    *,
    column: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    if column not in frame.columns:
        return
    series = pd.to_numeric(frame[column], errors="coerce")
    if minimum is not None and bool((series < minimum).fillna(False).any()):
        raise DataQualityError(f"{file_name}.{column} contains values below {minimum}")
    if maximum is not None and bool((series > maximum).fillna(False).any()):
        raise DataQualityError(f"{file_name}.{column} contains values above {maximum}")


def _validate_csv_artifact_values(file_name: str, frame: pd.DataFrame) -> None:
    bounded_columns: dict[str, dict[str, tuple[float | None, float | None]]] = {
        "recommendations.csv": {
            "ltv": (0.0, None),
            "cac": (0.0, None),
            "ltv_cac_ratio": (0.0, None),
            "churn_probability": (0.0, 1.0),
            "next_purchase_probability": (0.0, 1.0),
            "strategic_score": (0.0, 1.0),
        },
        "unit_economics.csv": {
            "marketing_spend": (0.0, None),
            "customers_acquired": (1.0, None),
            "cac": (0.0, None),
            "avg_arpu": (0.0, None),
            "ltv_cac_ratio": (0.0, None),
            "payback_period_months": (0.0, None),
        },
        "top_10_actions.csv": {
            "priority_rank": (1.0, None),
            "strategic_priority_score": (0.0, 1.0),
            "expected_uplift": (0.0, None),
            "action_cost": (0.0, None),
        },
        "cac_by_channel.csv": {
            "marketing_spend": (0.0, None),
            "customers_acquired": (1.0, None),
            "cac": (0.0, None),
        },
        "ltv.csv": {
            "ltv": (0.0, None),
            "churn_probability": (0.0, 1.0),
            "next_purchase_probability": (0.0, 1.0),
        },
        "cohort_retention.csv": {
            "cohort_index": (0.0, None),
            "active_customers": (0.0, None),
            "cohort_size": (1.0, None),
            "retention_rate": (0.0, 1.0),
        },
    }
    for column, (minimum, maximum) in bounded_columns.get(file_name, {}).items():
        _validate_numeric_bounds(
            file_name,
            frame,
            column=column,
            minimum=minimum,
            maximum=maximum,
        )

    if file_name == "top_10_actions.csv" and "priority_rank" in frame.columns:
        if frame["priority_rank"].duplicated().any():
            raise DataQualityError("top_10_actions.csv.priority_rank contains duplicates")
    if (
        file_name == "cohort_retention.csv"
        and {"active_customers", "cohort_size"}.issubset(frame.columns)
        and bool((frame["active_customers"] > frame["cohort_size"]).any())
    ):
        raise DataQualityError(
            "cohort_retention.csv.active_customers exceeds cohort_size in at least one row"
        )


def _validate_json_artifact_values(file_name: str, payload: dict[str, object]) -> None:
    bounded_keys: dict[str, dict[str, tuple[float | None, float | None]]] = {
        "kpi_snapshot.json": {
            "revenue_proxy": (0.0, None),
            "avg_arpu": (0.0, None),
            "avg_ltv": (0.0, None),
            "avg_cac": (0.0, None),
            "avg_ltv_cac_ratio": (0.0, None),
            "portfolio_size": (0.0, None),
        },
        "business_outcomes.json": {
            "kpis.avg_ltv_cac_ratio": (0.0, None),
        },
    }
    for dotted_key, (minimum, maximum) in bounded_keys.get(file_name, {}).items():
        value = _resolve_nested_key(payload, dotted_key)
        if not isinstance(value, int | float):
            raise DataQualityError(f"{file_name}.{dotted_key} must be numeric")
        if minimum is not None and float(value) < minimum:
            raise DataQualityError(f"{file_name}.{dotted_key} contains values below {minimum}")
        if maximum is not None and float(value) > maximum:
            raise DataQualityError(f"{file_name}.{dotted_key} contains values above {maximum}")

    if file_name == "alerts_report.json":
        alert_count = _resolve_nested_key(payload, "alert_count")
        alerts = _resolve_nested_key(payload, "alerts")
        if not isinstance(alert_count, int):
            raise DataQualityError("alerts_report.json.alert_count must be an integer")
        if not isinstance(alerts, list):
            raise DataQualityError("alerts_report.json.alerts must be a list")
        if alert_count != len(alerts):
            raise DataQualityError("alerts_report.json.alert_count does not match alerts length")


def validate_processed_artifacts(
    processed_dir: Path,
    output_path: Path | None = None,
    *,
    csv_artifact_specs: dict[str, set[str]] | None = None,
    json_artifact_specs: dict[str, tuple[str, ...]] | None = None,
    contract_version: str = PROCESSED_CONTRACT_VERSION,
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    resolved_csv_specs = CSV_ARTIFACT_SPECS if csv_artifact_specs is None else csv_artifact_specs
    resolved_json_specs = JSON_ARTIFACT_SPECS if json_artifact_specs is None else json_artifact_specs
    for file_name, required_columns in resolved_csv_specs.items():
        checks.append(_validate_csv_artifact(processed_dir, file_name, required_columns))
    for file_name, required_keys in resolved_json_specs.items():
        checks.append(_validate_json_artifact(processed_dir, file_name, required_keys))

    payload = {
        "validated_at_utc": datetime.now(UTC).isoformat(),
        "processed_dir": str(processed_dir),
        "contract_version": contract_version,
        "status": "ok",
        "artifact_count": len(checks),
        "checks": checks,
    }
    if output_path is not None:
        atomic_write_json(output_path, payload)
    return payload
