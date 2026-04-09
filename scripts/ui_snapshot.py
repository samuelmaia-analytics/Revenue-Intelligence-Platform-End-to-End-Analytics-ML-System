from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app" / "streamlit_app.py"
SNAPSHOT_PATH = PROJECT_ROOT / "tests" / "snapshots" / "dashboard_ui_snapshot.json"


def _select_markdown_snippets(at: AppTest, limit: int = 6) -> list[str]:
    snippets: list[str] = []
    for item in at.markdown:
        value = item.value.strip()
        if not value or value.startswith("<style>") or "block-spacer" in value:
            continue
        snippets.append(value[:160])
        if len(snippets) >= limit:
            break
    return snippets


def build_ui_snapshot() -> dict[str, Any]:
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=60)
    tab_summaries = []
    for tab in at.tabs:
        tab_summaries.append(
            {
                "label": tab.label,
                "dataframe_count": len(tab.dataframe),
                "expander_labels": [exp.label for exp in tab.expander],
                "markdown_count": len(tab.markdown),
            }
        )
    return {
        "selectboxes": [item.proto.label for item in at.selectbox],
        "buttons": sorted(item.proto.label for item in at.button),
        "captions": [item.value for item in at.caption[:6]],
        "tabs": [tab.label for tab in at.tabs],
        "tab_summaries": tab_summaries,
        "dataframe_count": len(at.dataframe),
        "expander_labels": [exp.label for exp in at.expander],
        "markdown_snippets": _select_markdown_snippets(at),
    }


def main() -> int:
    snapshot = build_ui_snapshot()
    if "--update" in sys.argv:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Updated snapshot at {SNAPSHOT_PATH}")
        return 0

    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    if snapshot != expected:
        print("Dashboard UI snapshot mismatch.")
        print("Expected:")
        print(json.dumps(expected, ensure_ascii=False, indent=2))
        print("Actual:")
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return 1

    print("Dashboard UI snapshot passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
