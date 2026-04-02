from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_SOURCE_PATH = Path("data") / "processed" / "runtime_metrics.json"
DEFAULT_BASELINE_PATH = Path("metrics") / "runtime_baseline.json"


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_baseline(
    metrics: dict[str, object], current_baseline: dict[str, object] | None
) -> dict[str, object]:
    stage_timings = metrics.get("stage_timings_seconds", {})
    if not isinstance(stage_timings, dict):
        raise SystemExit("Runtime metrics invalid: stage_timings_seconds must be a mapping.")

    baseline = {
        "environment": metrics.get("environment", "ci"),
        "max_total_runtime_seconds": (
            current_baseline.get("max_total_runtime_seconds", 45.0) if current_baseline else 45.0
        ),
        "max_regression_fraction": (
            current_baseline.get("max_regression_fraction", 0.5) if current_baseline else 0.5
        ),
        "stage_timings_seconds": stage_timings,
    }
    return baseline


def main() -> None:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE_PATH
    baseline_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BASELINE_PATH

    if not source_path.exists():
        raise SystemExit(f"Runtime metrics file not found: {source_path}")

    metrics = _load_json(source_path)
    current_baseline = _load_json(baseline_path) if baseline_path.exists() else None
    baseline = _build_baseline(metrics, current_baseline)

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(f"Updated runtime baseline: {baseline_path}")


if __name__ == "__main__":
    main()
