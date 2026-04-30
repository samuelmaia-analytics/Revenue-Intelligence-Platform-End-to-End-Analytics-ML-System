from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.persistence import append_frame_to_warehouse


def append_approved_actions(
    approved_actions: pd.DataFrame,
    csv_path: Path,
    warehouse_target: str,
    sqlite_path: Path,
    warehouse_url: str | None = None,
    warehouse_schema: str | None = None,
) -> pd.DataFrame:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    enriched = approved_actions.copy()
    enriched["approval_timestamp_utc"] = datetime.now(UTC).isoformat()

    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = pd.concat([existing, enriched], ignore_index=True)
    else:
        combined = enriched
    combined.to_csv(csv_path, index=False)

    append_frame_to_warehouse(
        frame=enriched,
        table_name="approved_actions",
        warehouse_target=warehouse_target,
        sqlite_path=sqlite_path,
        warehouse_url=warehouse_url,
        warehouse_schema=warehouse_schema,
    )
    return enriched
