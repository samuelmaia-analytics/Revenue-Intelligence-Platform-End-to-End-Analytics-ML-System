from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.io_utils import atomic_write_json


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path.name} must contain JSON objects on each line.")
        events.append(payload)
    if not events:
        raise ValueError(f"{path.name} must contain at least one event.")
    return events


def build_observability_summary(processed_dir: Path) -> dict[str, object]:
    manifest = _read_json(processed_dir / "pipeline_manifest.json")
    runtime_metrics = _read_json(processed_dir / "runtime_metrics.json")
    run_events = _read_jsonl(processed_dir / "run_events.jsonl")

    stage_timings = runtime_metrics.get("stage_timings_seconds", {})
    if not isinstance(stage_timings, dict) or not stage_timings:
        raise ValueError("runtime_metrics.json must contain non-empty stage_timings_seconds.")

    slowest_stage_name, slowest_stage_elapsed = max(
        ((str(name), float(value)) for name, value in stage_timings.items()),
        key=lambda item: item[1],
    )

    retry_events = [
        event for event in run_events if event.get("event_type") == "stage.retry_scheduled"
    ]
    failed_events = [event for event in run_events if str(event.get("status")) == "failed"]
    last_event = run_events[-1]

    summary = {
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "environment": manifest["environment"],
        "log_format": runtime_metrics["log_format"],
        "total_runtime_seconds": runtime_metrics["total_runtime_seconds"],
        "stage_count": runtime_metrics["stage_count"],
        "event_count": runtime_metrics["event_count"],
        "retry_event_count": len(retry_events),
        "failed_event_count": len(failed_events),
        "last_event": {
            "event_type": last_event["event_type"],
            "timestamp": last_event["timestamp"],
            "status": last_event.get("status", "n/a"),
        },
        "slowest_stage": {
            "stage": slowest_stage_name,
            "elapsed_seconds": round(slowest_stage_elapsed, 3),
        },
        "recent_events": [
            {
                "event_type": event["event_type"],
                "timestamp": event["timestamp"],
                "status": event.get("status", "n/a"),
                "stage": event.get("stage"),
            }
            for event in run_events[-5:]
        ],
        "observability_paths": {
            "manifest": str(processed_dir / "pipeline_manifest.json"),
            "runtime_metrics": str(processed_dir / "runtime_metrics.json"),
            "run_events": str(processed_dir / "run_events.jsonl"),
        },
    }
    return summary


def export_observability_summary(
    processed_dir: Path, output_path: Path | None = None
) -> dict[str, object]:
    summary = build_observability_summary(processed_dir)
    if output_path is not None:
        atomic_write_json(output_path, summary)
    return summary


def build_reliability_report(
    *,
    run_id: str,
    stage_timings: dict[str, float],
    runtime_metrics: dict[str, object],
    quality_report: dict[str, object],
    freshness_report: dict[str, object],
    artifact_validation_report: dict[str, object],
    alerts_report: dict[str, object],
    insight_draft: dict[str, object],
    output_path: Path,
    technical_sla_hours: int = 24,
) -> dict[str, Any]:
    slowest_stage_name, slowest_stage_elapsed = max(
        stage_timings.items(),
        key=lambda item: item[1],
    )
    quality_datasets = quality_report.get("datasets", [])
    duplicate_rows = sum(int(item.get("duplicate_rows", 0)) for item in quality_datasets)
    referential_issues = sum(int(item.get("referential_issues", 0)) for item in quality_datasets)
    null_count_total = sum(
        int(value)
        for dataset in quality_datasets
        for value in dataset.get("null_counts", {}).values()
    )
    reliability_status = "ok"
    if (
        str(freshness_report.get("status", "n/a")).lower() != "ok"
        or str(artifact_validation_report.get("status", "n/a")).lower() != "ok"
        or int(alerts_report.get("alert_count", 0)) > 0
    ):
        reliability_status = "warning"

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "status": reliability_status,
        "service_tier": "analytics_operating_system",
        "technical_sla": {
            "cadence": "batch",
            "target_hours": technical_sla_hours,
            "freshness_status": freshness_report.get("status"),
        },
        "runtime": {
            "total_runtime_seconds": runtime_metrics.get("total_runtime_seconds"),
            "stage_count": runtime_metrics.get("stage_count"),
            "slowest_stage": {
                "stage": slowest_stage_name,
                "elapsed_seconds": round(float(slowest_stage_elapsed), 3),
            },
        },
        "quality": {
            "status": "ok" if duplicate_rows == 0 and referential_issues == 0 else "warning",
            "duplicate_rows": duplicate_rows,
            "referential_issues": referential_issues,
            "null_count_total": null_count_total,
        },
        "governance": {
            "artifact_validation_status": artifact_validation_report.get("status"),
            "freshness_status": freshness_report.get("status"),
            "active_alert_count": alerts_report.get("alert_count", 0),
        },
        "operational_readout": {
            "headline": insight_draft.get("headline"),
            "summary": insight_draft.get("summary"),
            "recommended_actions": insight_draft.get("recommended_actions", []),
        },
        "source_artifacts": {
            "runtime_metrics": "runtime_metrics.json",
            "quality_report": "quality_report.json",
            "freshness_report": "freshness_report.json",
            "artifact_validation_report": "artifact_validation_report.json",
            "alerts_report": "alerts_report.json",
            "insight_draft": "insight_draft.json",
        },
    }
    atomic_write_json(output_path, report)
    return report
