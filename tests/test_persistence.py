from __future__ import annotations

from pathlib import Path

import pandas as pd

import src.persistence as persistence


class _FakeConnection:
    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeEngine:
    def begin(self) -> _FakeConnection:
        return _FakeConnection()


def test_persist_frames_to_postgres_passes_schema(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_to_sql(
        self: pd.DataFrame,
        name: str,
        con: object,
        if_exists: str,
        index: bool,
        schema: str | None = None,
    ) -> None:
        captured["name"] = name
        captured["if_exists"] = if_exists
        captured["index"] = index
        captured["schema"] = schema

    monkeypatch.setattr(persistence, "create_engine", lambda _: _FakeEngine())
    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)

    persistence.persist_frames(
        {"recommendations": pd.DataFrame([{"customer_id": 1}])},
        warehouse_target="postgres",
        sqlite_path=Path("ignored.db"),
        warehouse_url="postgresql://example",
        warehouse_schema="analytics_smoke",
    )

    assert captured["name"] == "recommendations"
    assert captured["schema"] == "analytics_smoke"
