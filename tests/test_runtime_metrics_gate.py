from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.assert_runtime_metrics import main as assert_runtime_metrics_main


def _write_runtime_metrics(path: Path, *, total_runtime_seconds: float, stage_elapsed: float) -> None:
    path.write_text(
        json.dumps(
            {
                "run_id": "20260401T000000Z-test",
                "environment": "ci",
                "log_format": "json",
                "stage_count": 3,
                "stage_timings_seconds": {
                    "ingestion.raw": 0.5,
                    "modeling.ml": stage_elapsed,
                    "warehouse.sqlite": 0.4,
                },
                "total_runtime_seconds": total_runtime_seconds,
                "output_count": 5,
            }
        ),
        encoding="utf-8",
    )


def _write_baseline(path: Path, *, max_total_runtime_seconds: float = 45.0) -> None:
    path.write_text(
        json.dumps(
            {
                "environment": "ci",
                "max_total_runtime_seconds": max_total_runtime_seconds,
                "max_regression_fraction": 0.5,
                "stage_timings_seconds": {
                    "ingestion.raw": 1.0,
                    "modeling.ml": 5.0,
                    "warehouse.sqlite": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )


def test_runtime_metrics_gate_accepts_expected_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path, total_runtime_seconds=5.0, stage_elapsed=3.0)
    _write_baseline(baseline_path)
    monkeypatch.setattr(
        "sys.argv", ["assert_runtime_metrics.py", str(metrics_path), str(baseline_path)]
    )

    assert_runtime_metrics_main()


def test_runtime_metrics_gate_rejects_total_runtime_regression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path, total_runtime_seconds=60.0, stage_elapsed=3.0)
    _write_baseline(baseline_path)
    monkeypatch.setattr(
        "sys.argv", ["assert_runtime_metrics.py", str(metrics_path), str(baseline_path)]
    )

    with pytest.raises(SystemExit, match="total_runtime_seconds"):
        assert_runtime_metrics_main()


def test_runtime_metrics_gate_rejects_stage_runtime_regression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path, total_runtime_seconds=5.0, stage_elapsed=25.0)
    _write_baseline(baseline_path)
    monkeypatch.setattr(
        "sys.argv", ["assert_runtime_metrics.py", str(metrics_path), str(baseline_path)]
    )

    with pytest.raises(SystemExit, match="modeling.ml"):
        assert_runtime_metrics_main()


def test_runtime_metrics_gate_rejects_baseline_regression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metrics_path = tmp_path / "runtime_metrics.json"
    baseline_path = tmp_path / "runtime_baseline.json"
    _write_runtime_metrics(metrics_path, total_runtime_seconds=5.0, stage_elapsed=8.0)
    _write_baseline(baseline_path)
    monkeypatch.setattr(
        "sys.argv", ["assert_runtime_metrics.py", str(metrics_path), str(baseline_path)]
    )

    with pytest.raises(SystemExit, match="baseline allowance"):
        assert_runtime_metrics_main()
