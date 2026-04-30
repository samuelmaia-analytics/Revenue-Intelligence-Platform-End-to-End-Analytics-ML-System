from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.io_utils import replace_sqlite_database

CreateEngineFn = Callable[[str], Any]

try:
    from sqlalchemy import create_engine as _sqlalchemy_create_engine
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    create_engine: CreateEngineFn | None = None
else:
    create_engine = _sqlalchemy_create_engine


def persist_frames_to_sqlite(frames: dict[str, pd.DataFrame], database_path: Path) -> list[str]:
    return replace_sqlite_database(database_path, frames)


def persist_frames_to_postgres(
    frames: dict[str, pd.DataFrame],
    warehouse_url: str,
    warehouse_schema: str | None = None,
) -> list[str]:
    if create_engine is None:
        raise RuntimeError(
            "SQLAlchemy is required for Postgres persistence. Install SQLAlchemy and a Postgres driver."
        )
    engine = create_engine(warehouse_url)
    written_tables: list[str] = []
    with engine.begin() as connection:
        for table_name, frame in frames.items():
            frame.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False,
                schema=warehouse_schema,
            )
            written_tables.append(table_name)
    return written_tables


def persist_frames(
    frames: dict[str, pd.DataFrame],
    warehouse_target: str,
    sqlite_path: Path,
    warehouse_url: str | None = None,
    warehouse_schema: str | None = None,
) -> list[str]:
    if warehouse_target == "sqlite":
        return persist_frames_to_sqlite(frames, sqlite_path)
    if warehouse_target == "postgres":
        if not warehouse_url:
            raise RuntimeError("RIP_WAREHOUSE_URL is required when RIP_WAREHOUSE_TARGET=postgres.")
        return persist_frames_to_postgres(frames, warehouse_url, warehouse_schema)
    raise RuntimeError(f"Unsupported warehouse target: {warehouse_target}")


def append_frame_to_warehouse(
    frame: pd.DataFrame,
    table_name: str,
    warehouse_target: str,
    sqlite_path: Path,
    warehouse_url: str | None = None,
    warehouse_schema: str | None = None,
) -> None:
    if warehouse_target == "sqlite":
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(sqlite_path) as connection:
            frame.to_sql(table_name, connection, if_exists="append", index=False)
        return

    if warehouse_target == "postgres":
        if create_engine is None:
            raise RuntimeError(
                "SQLAlchemy is required for Postgres persistence. Install SQLAlchemy and a Postgres driver."
            )
        if not warehouse_url:
            raise RuntimeError("RIP_WAREHOUSE_URL is required when RIP_WAREHOUSE_TARGET=postgres.")
        engine = create_engine(warehouse_url)
        with engine.begin() as connection:
            frame.to_sql(
                table_name,
                connection,
                if_exists="append",
                index=False,
                schema=warehouse_schema,
            )
        return

    raise RuntimeError(f"Unsupported warehouse target: {warehouse_target}")
