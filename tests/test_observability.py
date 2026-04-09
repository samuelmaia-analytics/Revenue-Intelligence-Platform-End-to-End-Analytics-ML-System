from __future__ import annotations

import json
from pathlib import Path

from src.observability import (
    build_observability_summary,
    build_reliability_report,
    export_observability_summary,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_observability_summary_aggregates_runtime_evidence(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _write_json(
        processed_dir / "pipeline_manifest.json",
        {
            "run_id": "run-123",
            "status": "success",
            "environment": "test",
        },
    )
    _write_json(
        processed_dir / "runtime_metrics.json",
        {
            "run_id": "run-123",
            "environment": "test",
            "log_format": "json",
            "stage_count": 3,
            "stage_timings_seconds": {
                "ingestion.raw": 0.4,
                "modeling.ml": 2.5,
                "warehouse.sqlite": 0.9,
            },
            "total_runtime_seconds": 3.8,
            "event_count": 5,
            "output_count": 4,
        },
    )
    (processed_dir / "run_events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-01-01T00:00:00+00:00",
                        "event_type": "pipeline.started",
                        "run_id": "run-123",
                        "status": "running",
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-01-01T00:00:01+00:00",
                        "event_type": "stage.retry_scheduled",
                        "run_id": "run-123",
                        "status": "retrying",
                        "stage": "modeling.ml",
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-01-01T00:00:04+00:00",
                        "event_type": "pipeline.completed",
                        "run_id": "run-123",
                        "status": "success",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = build_observability_summary(processed_dir)

    assert summary["run_id"] == "run-123"
    assert summary["retry_event_count"] == 1
    assert summary["slowest_stage"]["stage"] == "modeling.ml"
    assert summary["last_event"]["event_type"] == "pipeline.completed"


def test_export_observability_summary_writes_json_output(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _write_json(
        processed_dir / "pipeline_manifest.json",
        {
            "run_id": "run-456",
            "status": "success",
            "environment": "test",
        },
    )
    _write_json(
        processed_dir / "runtime_metrics.json",
        {
            "run_id": "run-456",
            "environment": "test",
            "log_format": "text",
            "stage_count": 1,
            "stage_timings_seconds": {"ingestion.raw": 0.2},
            "total_runtime_seconds": 0.2,
            "event_count": 1,
            "output_count": 1,
        },
    )
    (processed_dir / "run_events.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "event_type": "pipeline.completed",
                "run_id": "run-456",
                "status": "success",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "observability_summary.json"
    summary = export_observability_summary(processed_dir, output_path=output_path)

    assert output_path.exists()
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["run_id"] == summary["run_id"] == "run-456"


def test_build_reliability_report_writes_governed_operational_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "reliability_report.json"
    payload = build_reliability_report(
        run_id="run-789",
        stage_timings={"modeling.ml": 2.4, "reporting.executive": 0.2},
        runtime_metrics={"total_runtime_seconds": 3.0, "stage_count": 2},
        quality_report={
            "datasets": [
                {"duplicate_rows": 0, "referential_issues": 0, "null_counts": {"a": 2}}
            ]
        },
        freshness_report={"status": "ok"},
        artifact_validation_report={"status": "ok"},
        alerts_report={"alert_count": 1},
        insight_draft={"headline": "All clear", "summary": "demo", "recommended_actions": ["review"]},
        output_path=output_path,
    )

    assert output_path.exists()
    assert payload["run_id"] == "run-789"
    assert payload["runtime"]["slowest_stage"]["stage"] == "modeling.ml"
    assert payload["quality"]["null_count_total"] == 2
