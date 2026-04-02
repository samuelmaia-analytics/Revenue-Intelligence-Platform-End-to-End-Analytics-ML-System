from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_BASELINE_PATH = Path("metrics") / "runtime_baseline.json"
MAX_TOTAL_RUNTIME_SECONDS = 45.0
MAX_STAGE_RUNTIME_SECONDS: dict[str, float] = {
    "ingestion.raw": 10.0,
    "modeling.ml": 20.0,
    "warehouse.sqlite": 10.0,
}


def _load_metrics(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _assert_runtime_thresholds(payload: dict[str, object]) -> None:
    total_runtime_seconds = float(payload["total_runtime_seconds"])
    if total_runtime_seconds > MAX_TOTAL_RUNTIME_SECONDS:
        raise SystemExit(
            "Runtime regression detected: "
            f"total_runtime_seconds={total_runtime_seconds:.3f} exceeds "
            f"{MAX_TOTAL_RUNTIME_SECONDS:.3f}"
        )

    stage_timings = payload.get("stage_timings_seconds", {})
    if not isinstance(stage_timings, dict):
        raise SystemExit("Runtime metrics invalid: stage_timings_seconds must be a mapping.")

    for stage_name, threshold in MAX_STAGE_RUNTIME_SECONDS.items():
        raw_value = stage_timings.get(stage_name)
        if raw_value is None:
            raise SystemExit(f"Runtime metrics invalid: missing stage timing for {stage_name}.")
        stage_elapsed = float(raw_value)
        if stage_elapsed > threshold:
            raise SystemExit(
                "Runtime regression detected: "
                f"{stage_name}={stage_elapsed:.3f} exceeds {threshold:.3f}"
            )


def _assert_against_baseline(payload: dict[str, object], baseline: dict[str, object]) -> None:
    max_total_runtime_seconds = float(
        baseline.get("max_total_runtime_seconds", MAX_TOTAL_RUNTIME_SECONDS)
    )
    total_runtime_seconds = float(payload["total_runtime_seconds"])
    if total_runtime_seconds > max_total_runtime_seconds:
        raise SystemExit(
            "Runtime regression detected: "
            f"total_runtime_seconds={total_runtime_seconds:.3f} exceeds "
            f"baseline ceiling {max_total_runtime_seconds:.3f}"
        )

    max_regression_fraction = float(baseline.get("max_regression_fraction", 0.5))
    baseline_stage_timings = baseline.get("stage_timings_seconds", {})
    payload_stage_timings = payload.get("stage_timings_seconds", {})
    if not isinstance(baseline_stage_timings, dict) or not isinstance(payload_stage_timings, dict):
        raise SystemExit("Runtime baseline invalid: stage_timings_seconds must be a mapping.")

    for stage_name, baseline_value in baseline_stage_timings.items():
        current_raw_value = payload_stage_timings.get(stage_name)
        if current_raw_value is None:
            raise SystemExit(f"Runtime metrics invalid: missing stage timing for {stage_name}.")
        baseline_seconds = float(baseline_value)
        current_seconds = float(current_raw_value)
        allowed_seconds = baseline_seconds * (1 + max_regression_fraction)
        if current_seconds > allowed_seconds:
            raise SystemExit(
                "Runtime regression detected: "
                f"{stage_name}={current_seconds:.3f} exceeds baseline allowance {allowed_seconds:.3f}"
            )


def main() -> None:
    metrics_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("data") / "processed" / "runtime_metrics.json"
    )
    if not metrics_path.exists():
        raise SystemExit(f"Runtime metrics file not found: {metrics_path}")

    payload = _load_metrics(metrics_path)
    _assert_runtime_thresholds(payload)

    baseline_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BASELINE_PATH
    if baseline_path.exists():
        baseline = _load_metrics(baseline_path)
        _assert_against_baseline(payload, baseline)

    print(f"Runtime metrics within thresholds: {metrics_path}")


if __name__ == "__main__":
    main()
