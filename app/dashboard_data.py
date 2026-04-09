from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from main import run_pipeline  # noqa: E402
from src.config import PipelineConfig  # noqa: E402


@st.cache_data(show_spinner=False)
def load_processed_assets(processed_dir_str: str) -> dict[str, Any]:
    processed_dir = Path(processed_dir_str)
    required = [
        "recommendations.csv",
        "cohort_retention.csv",
        "unit_economics.csv",
        "executive_report.json",
        "business_outcomes.json",
        "top_10_actions.csv",
        "monitoring_report.json",
        "semantic_metrics_catalog.json",
        "alerts_report.json",
        "pipeline_manifest.json",
        "artifact_validation_report.json",
        "freshness_report.json",
        "insight_draft.json",
        "reliability_report.json",
    ]
    if not all((processed_dir / name).exists() for name in required):
        run_pipeline(PipelineConfig.from_env(PROJECT_ROOT))

    approvals_path = processed_dir / "approved_actions.csv"
    with (processed_dir / "executive_report.json").open("r", encoding="utf-8") as file:
        report = json.load(file)
    with (processed_dir / "business_outcomes.json").open("r", encoding="utf-8") as file:
        outcomes = json.load(file)
    with (processed_dir / "monitoring_report.json").open("r", encoding="utf-8") as file:
        monitoring = json.load(file)
    with (processed_dir / "semantic_metrics_catalog.json").open("r", encoding="utf-8") as file:
        semantic_metrics = json.load(file)
    with (processed_dir / "alerts_report.json").open("r", encoding="utf-8") as file:
        alerts = json.load(file)
    with (processed_dir / "pipeline_manifest.json").open("r", encoding="utf-8") as file:
        manifest = json.load(file)
    with (processed_dir / "artifact_validation_report.json").open("r", encoding="utf-8") as file:
        artifact_validation = json.load(file)
    with (processed_dir / "freshness_report.json").open("r", encoding="utf-8") as file:
        freshness = json.load(file)
    with (processed_dir / "insight_draft.json").open("r", encoding="utf-8") as file:
        insight_draft = json.load(file)
    with (processed_dir / "reliability_report.json").open("r", encoding="utf-8") as file:
        reliability_report = json.load(file)

    return {
        "recommendations": pd.read_csv(processed_dir / "recommendations.csv"),
        "cohort": pd.read_csv(processed_dir / "cohort_retention.csv"),
        "unit": pd.read_csv(processed_dir / "unit_economics.csv"),
        "top10": pd.read_csv(processed_dir / "top_10_actions.csv"),
        "report": report,
        "outcomes": outcomes,
        "monitoring": monitoring,
        "semantic_metrics": semantic_metrics,
        "alerts": alerts,
        "manifest": manifest,
        "artifact_validation": artifact_validation,
        "freshness": freshness,
        "insight_draft": insight_draft,
        "reliability_report": reliability_report,
        "approved_actions": (
            pd.read_csv(approvals_path) if approvals_path.exists() else pd.DataFrame()
        ),
    }


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
    filtered = filtered.copy()
    filtered["potential_impact"] = filtered.apply(potential_impact_fn, axis=1)
    return filtered


def refresh_pipeline_outputs(project_root: Path) -> None:
    run_pipeline(PipelineConfig.from_env(project_root))
    load_processed_assets.clear()
