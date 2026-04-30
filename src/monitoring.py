from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.io_utils import atomic_write_json

NUMERIC_MONITOR_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "avg_order_value",
    "tenure_days",
    "arpu",
]


def _series_or_empty(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(dtype="float64")


def _summarize_numeric_distribution(
    df: pd.DataFrame, columns: list[str]
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for column in columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        summary[column] = {
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "p10": float(series.quantile(0.10)),
            "p50": float(series.quantile(0.50)),
            "p90": float(series.quantile(0.90)),
        }
    return summary


def _distribution_shift(reference: dict, current: dict) -> dict[str, dict[str, float | str]]:
    drift_report: dict[str, dict[str, float | str]] = {}
    for column, current_stats in current.items():
        reference_stats = reference.get(column)
        if reference_stats is None:
            drift_report[column] = {"status": "new_feature"}
            continue
        reference_std = reference_stats.get("std", 0.0) or 1.0
        mean_shift = abs(current_stats["mean"] - reference_stats["mean"]) / reference_std
        status = "stable"
        if mean_shift >= 0.5:
            status = "watch"
        if mean_shift >= 1.0:
            status = "drift"
        drift_report[column] = {
            "status": status,
            "reference_mean": float(reference_stats["mean"]),
            "current_mean": float(current_stats["mean"]),
            "normalized_mean_shift": float(mean_shift),
        }
    return drift_report


def _calibration_summary(y_true: pd.Series, y_prob: pd.Series, label: str) -> dict:
    try:
        from sklearn.calibration import calibration_curve
        from sklearn.metrics import brier_score_loss
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "scikit-learn is required for calibration monitoring. "
            "Install project dependencies with `python -m pip install -e .[dev]`."
        ) from exc

    clean = pd.DataFrame({"y_true": y_true, "y_prob": y_prob}).dropna()
    if clean.empty or clean["y_true"].nunique() < 2:
        return {"label": label, "status": "insufficient_signal"}

    observed, predicted = calibration_curve(
        clean["y_true"],
        clean["y_prob"],
        n_bins=5,
        strategy="quantile",
    )
    return {
        "label": label,
        "status": "ok",
        "brier_score": float(brier_score_loss(clean["y_true"], clean["y_prob"])),
        "curve": [
            {"predicted_probability": float(pred), "observed_rate": float(obs)}
            for pred, obs in zip(predicted, observed, strict=False)
        ],
    }


def build_monitoring_report(
    scored_df: pd.DataFrame,
    labeled_df: pd.DataFrame,
    output_path: Path,
    baseline_path: Path,
) -> dict:
    current_summary = _summarize_numeric_distribution(scored_df, NUMERIC_MONITOR_COLUMNS)
    if baseline_path.exists():
        with baseline_path.open("r", encoding="utf-8") as file:
            baseline = json.load(file)
        drift = _distribution_shift(baseline.get("numeric_summary", {}), current_summary)
        drift_status = (
            "watch"
            if any(item.get("status") in {"watch", "drift"} for item in drift.values())
            else "stable"
        )
    else:
        drift = {column: {"status": "initialized"} for column in current_summary}
        drift_status = "initialized"

    labeled = labeled_df.copy()
    churn_calibration = _calibration_summary(
        _series_or_empty(labeled, "is_churned"),
        _series_or_empty(labeled, "churn_probability"),
        "churn",
    )
    next_purchase_calibration = _calibration_summary(
        _series_or_empty(labeled, "next_purchase_30d"),
        _series_or_empty(labeled, "next_purchase_probability"),
        "next_purchase_30d",
    )

    report = {
        "drift_status": drift_status,
        "numeric_summary": current_summary,
        "feature_drift": drift,
        "calibration": {
            "churn": churn_calibration,
            "next_purchase_30d": next_purchase_calibration,
        },
    }
    atomic_write_json(output_path, report)
    atomic_write_json(baseline_path, {"numeric_summary": current_summary})
    return report
