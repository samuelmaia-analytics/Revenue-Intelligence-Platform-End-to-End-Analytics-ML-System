from __future__ import annotations

import json
import logging
from pathlib import Path

_STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "run_id",
    "request_id",
    "stack_info",
    "thread",
    "threadName",
}


class _DefaultContextFilter(logging.Filter):
    def __init__(self, *, run_id: str, request_id: str = "n/a") -> None:
        super().__init__()
        self.run_id = run_id
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        if not hasattr(record, "request_id"):
            record.request_id = self.request_id
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", "n/a"),
            "request_id": getattr(record, "request_id", "n/a"),
        }
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
        }
        if extra_fields:
            payload["context"] = extra_fields
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(
    level: str = "INFO",
    log_path: Path | None = None,
    run_id: str = "n/a",
    *,
    log_format: str = "text",
) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | run_id=%(run_id)s | %(message)s",
        force=True,
        handlers=handlers,
    )
    if log_format.lower() == "json":
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | run_id=%(run_id)s | request_id=%(request_id)s | %(message)s"
        )

    context_filter = _DefaultContextFilter(run_id=run_id)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
        handler.addFilter(context_filter)
