from __future__ import annotations

import json
from pathlib import Path

from scripts.update_runtime_baseline import main as update_runtime_baseline_main


def _write_runtime_metrics(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "run_id": "20260401T000000Z-test",
                "environment": "ci",
                "log_format": "json",
                "stage_count": 3,
                "stage_timings_seconds": {
                    "ingestion.raw": 0.7,
                    "modeling.ml": 4.2,
                    "warehouse.sqlite": 0.8,
                },
                "total_runtime_seconds": 7.5,
                "output_count": 10,
            }
        ),
        encoding="utf-8",
    )


def test_update_runtime_baseline_promotes_stage_timings(tmp_path: Path, monkeypatch) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path)
    monkeypatch.setattr(
        "sys.argv",
        ["update_runtime_baseline.py", str(metrics_path), str(baseline_path)],
    )

    update_runtime_baseline_main()

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["environment"] == "ci"
    assert baseline["stage_timings_seconds"]["modeling.ml"] == 4.2
    assert baseline["max_total_runtime_seconds"] == 45.0
    assert baseline["max_regression_fraction"] == 0.5


def test_update_runtime_baseline_preserves_existing_policy_fields(
    tmp_path: Path, monkeypatch
) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path)
    baseline_path.write_text(
        json.dumps(
            {
                "environment": "ci",
                "max_total_runtime_seconds": 30.0,
                "max_regression_fraction": 0.25,
                "stage_timings_seconds": {"modeling.ml": 5.0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["update_runtime_baseline.py", str(metrics_path), str(baseline_path)],
    )

    update_runtime_baseline_main()

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["max_total_runtime_seconds"] == 30.0
    assert baseline["max_regression_fraction"] == 0.25
    assert baseline["stage_timings_seconds"]["ingestion.raw"] == 0.7
