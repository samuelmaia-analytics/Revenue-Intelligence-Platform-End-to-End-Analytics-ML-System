from __future__ import annotations

import json
import logging

from src.logging_utils import JsonLogFormatter


def test_json_log_formatter_emits_structured_payload() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="revenue_intelligence.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.run_id = "run-123"
    record.request_id = "req-123"

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "revenue_intelligence.test"
    assert payload["message"] == "hello world"
    assert payload["run_id"] == "run-123"
    assert payload["request_id"] == "req-123"


def test_json_log_formatter_preserves_extra_context() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="revenue_intelligence.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="stage finished",
        args=(),
        exc_info=None,
    )
    record.run_id = "run-456"
    record.request_id = "n/a"
    record.event_type = "stage.completed"
    record.stage = "metrics.curated"
    record.elapsed_seconds = 1.234

    payload = json.loads(formatter.format(record))

    assert payload["context"]["event_type"] == "stage.completed"
    assert payload["context"]["stage"] == "metrics.curated"
    assert payload["context"]["elapsed_seconds"] == 1.234
