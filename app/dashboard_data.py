from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def _canonical_runtime_python(project_root: Path) -> str:
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _run_pipeline(project_root: Path) -> None:
    runtime_python = _canonical_runtime_python(project_root)
    cmd = [runtime_python, "-m", "src.pipeline", "run"]
    try:
        subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "").strip()
        raise RuntimeError(
            "Failed to refresh the pipeline via the canonical runtime. "
            f"Command: {' '.join(cmd)}. "
            f"Details: {details or 'no additional output'}"
        ) from error


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_processed_assets(processed_dir_str: str) -> dict[str, Any]:
    processed_dir = Path(processed_dir_str)
    required = [
        "executive_kpis.json",
        "executive_report.json",
        "executive_summary.json",
        "customer_analytics.csv",
        "payment_analytics.csv",
        "geographic_analytics.csv",
        "logistics_analytics.csv",
        "executive_summary_layer.csv",
        "recommendations.csv",
        "rfm_segments.csv",
        "cohort_retention.csv",
        "quality_report.json",
        "quality_business_rules.json",
        "pipeline_manifest.json",
        "artifact_validation_report.json",
        "freshness_report.json",
        "reliability_report.json",
        "monitoring_report.json",
        "alerts_report.json",
        "insight_draft.json",
    ]
    if not all((processed_dir / name).exists() for name in required):
        _run_pipeline(PROJECT_ROOT)

    assets: dict[str, Any] = {
        "executive_kpis": _load_json(processed_dir / "executive_kpis.json"),
        "executive_report": _load_json(processed_dir / "executive_report.json"),
        "executive_summary": _load_json(processed_dir / "executive_summary.json"),
        "quality_report": _load_json(processed_dir / "quality_report.json"),
        "quality_business_rules": _load_json(processed_dir / "quality_business_rules.json"),
        "manifest": _load_json(processed_dir / "pipeline_manifest.json"),
        "artifact_validation": _load_json(processed_dir / "artifact_validation_report.json"),
        "freshness": _load_json(processed_dir / "freshness_report.json"),
        "reliability": _load_json(processed_dir / "reliability_report.json"),
        "monitoring": _load_json(processed_dir / "monitoring_report.json"),
        "alerts": _load_json(processed_dir / "alerts_report.json"),
        "insight_draft": _load_json(processed_dir / "insight_draft.json"),
        "semantic_metrics": _load_json(processed_dir / "semantic_metrics_catalog.json"),
        "customers": pd.read_csv(processed_dir / "customer_analytics.csv"),
        "payments": pd.read_csv(processed_dir / "payment_analytics.csv"),
        "geography": pd.read_csv(processed_dir / "geographic_analytics.csv"),
        "logistics": pd.read_csv(processed_dir / "logistics_analytics.csv"),
        "summary_layer": pd.read_csv(processed_dir / "executive_summary_layer.csv"),
        "recommendations": pd.read_csv(processed_dir / "recommendations.csv"),
        "rfm": pd.read_csv(processed_dir / "rfm_segments.csv"),
        "cohort": pd.read_csv(processed_dir / "cohort_retention.csv"),
    }

    optional_frames = {
        "sellers": "seller_analytics.csv",
        "products": "product_analytics.csv",
        "categories": "category_analytics.csv",
        "unit_economics": "unit_economics.csv",
        "top_actions": "top_10_actions.csv",
        "executive_scorecard": "executive_scorecard.csv",
        "customer_segment_health": "customer_segment_health.csv",
        "payment_scorecard": "payment_scorecard.csv",
        "retention_scorecard": "retention_scorecard.csv",
        "seller_scorecard": "seller_scorecard.csv",
        "category_scorecard": "category_scorecard.csv",
        "state_scorecard": "state_scorecard.csv",
        "operations_scorecard": "operations_scorecard.csv",
    }
    for key, file_name in optional_frames.items():
        path = processed_dir / file_name
        assets[key] = pd.read_csv(path) if path.exists() else pd.DataFrame()

    # Compatibility aliases for the multipage dashboard/runtime surfaces.
    assets["unit"] = assets.get("unit_economics", pd.DataFrame())
    assets["top10"] = assets.get("top_actions", pd.DataFrame())
    assets["report"] = assets["executive_report"]
    business_outcomes_path = processed_dir / "business_outcomes.json"
    assets["outcomes"] = (
        _load_json(business_outcomes_path) if business_outcomes_path.exists() else {}
    )
    assets["reliability_report"] = assets["reliability"]
    approved_actions_path = processed_dir / "approved_actions.csv"
    assets["approved_actions"] = (
        pd.read_csv(approved_actions_path) if approved_actions_path.exists() else pd.DataFrame()
    )
    return assets


def filter_customers(
    customers: pd.DataFrame,
    *,
    state: str,
    segment: str,
    action: str,
) -> pd.DataFrame:
    filtered = customers.copy()
    if state != "All":
        filtered = filtered[filtered["customer_state"] == state]
    if segment != "All":
        filtered = filtered[filtered["segment"] == segment]
    if action != "All":
        filtered = filtered[filtered["recommended_action"] == action]
    return filtered.reset_index(drop=True)


def filter_recommendations(
    recommendations: pd.DataFrame,
    *,
    segment: str,
    channel: str,
    action: str,
    all_segments_label: str,
    all_channels_label: str,
    all_actions_label: str,
    potential_impact_fn: Any,
) -> pd.DataFrame:
    filtered = recommendations.copy()
    if segment != all_segments_label:
        filtered = filtered[filtered["segment"] == segment]
    if channel != all_channels_label:
        filtered = filtered[filtered["channel"] == channel]
    if action != all_actions_label:
        filtered = filtered[filtered["recommended_action"] == action]
    filtered = filtered.reset_index(drop=True)
    if not filtered.empty:
        filtered["potential_impact"] = filtered.apply(potential_impact_fn, axis=1)
    else:
        filtered["potential_impact"] = pd.Series(dtype=float)
    return filtered


def refresh_pipeline_outputs(project_root: Path) -> None:
    _run_pipeline(project_root)
    load_processed_assets.clear()
