from __future__ import annotations

import json
from pathlib import Path

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
