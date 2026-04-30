from __future__ import annotations

import json

import pytest

from scripts.smoke_postgres_optional import main


def test_postgres_optional_smoke_skips_without_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("RIP_SMOKE_POSTGRES_URL", raising=False)

    main()

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["status"] == "skipped"
    assert "RIP_SMOKE_POSTGRES_URL" in payload["reason"]
