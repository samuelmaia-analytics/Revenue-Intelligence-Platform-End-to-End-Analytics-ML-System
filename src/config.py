from __future__ import annotations

import os
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path


def _load_dotenv_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _resolve_int(name: str, default: int, minimum: int | None = None) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if minimum is not None and value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return value


def _resolve_float(
    name: str,
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a float.") from exc
    if minimum is not None and value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    if maximum is not None and value > maximum:
        raise RuntimeError(f"{name} must be <= {maximum}.")
    return value


def _resolve_path(root: Path, env_var: str, default: Path) -> Path:
    raw = os.getenv(env_var, str(default)).strip()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    return candidate


def _resolve_optional_date(name: str) -> date | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must use YYYY-MM-DD format.") from exc


def _resolve_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean-like value.")


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    data_dir: Path
    raw_dir: Path
    bronze_dir: Path
    silver_dir: Path
    gold_dir: Path
    processed_dir: Path
    warehouse_dir: Path
    warehouse_db_path: Path
    semantic_metrics_path: Path
    alerts_output_path: Path
    approvals_output_path: Path
    runs_dir: Path
    manifests_dir: Path
    snapshots_dir: Path
    data_dictionary_path: Path
    env_name: str
    warehouse_target: str
    warehouse_url: str | None
    seed: int
    log_level: str
    freshness_max_age_hours: int
    snapshot_retention_runs: int
    snapshot_retention_days: int
    failure_retention_days: int
    retry_attempts: int = 1
    retry_backoff_seconds: int = 0
    quality_max_null_fraction: float = 0.20
    alert_drift_feature_count_warn: int = 1
    alert_duplicate_rows_warn: int = 0
    alert_null_count_warn: int = 0
    alert_brier_score_warn: float = 0.25
    alert_webhook_url: str | None = None
    backfill_start_date: date | None = None
    backfill_end_date: date | None = None
    warehouse_schema: str | None = None
    synthetic_customer_count: int = 2500
    allow_bundled_seed_fallback: bool = True

    def ensure_directories(self) -> None:
        for directory in [
            self.data_dir,
            self.raw_dir,
            self.bronze_dir,
            self.silver_dir,
            self.gold_dir,
            self.processed_dir,
            self.warehouse_dir,
            self.runs_dir,
            self.manifests_dir,
            self.snapshots_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def with_overrides(
        self,
        *,
        data_dir: Path | None = None,
        seed: int | None = None,
        log_level: str | None = None,
        backfill_start_date: date | None = None,
        backfill_end_date: date | None = None,
    ) -> PipelineConfig:
        resolved_start = (
            self.backfill_start_date if backfill_start_date is None else backfill_start_date
        )
        resolved_end = self.backfill_end_date if backfill_end_date is None else backfill_end_date
        if resolved_start and resolved_end and resolved_start > resolved_end:
            raise RuntimeError("Backfill start date must be <= backfill end date.")

        if data_dir is None:
            return replace(
                self,
                seed=self.seed if seed is None else seed,
                log_level=self.log_level if log_level is None else log_level.upper(),
                backfill_start_date=resolved_start,
                backfill_end_date=resolved_end,
            )

        return replace(
            self,
            data_dir=data_dir,
            raw_dir=data_dir / "raw",
            bronze_dir=data_dir / "bronze",
            silver_dir=data_dir / "silver",
            gold_dir=data_dir / "gold",
            processed_dir=data_dir / "processed",
            warehouse_dir=data_dir / "warehouse",
            warehouse_db_path=data_dir / "warehouse" / "revenue_intelligence.db",
            alerts_output_path=data_dir / "processed" / "alerts_report.json",
            approvals_output_path=data_dir / "processed" / "approved_actions.csv",
            runs_dir=data_dir / "runs",
            manifests_dir=data_dir / "manifests",
            snapshots_dir=data_dir / "snapshots",
            data_dictionary_path=data_dir / "processed" / "data_dictionary.json",
            seed=self.seed if seed is None else seed,
            log_level=self.log_level if log_level is None else log_level.upper(),
            backfill_start_date=resolved_start,
            backfill_end_date=resolved_end,
        )

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> PipelineConfig:
        root = project_root or Path(__file__).resolve().parents[1]
        _load_dotenv_file(root / ".env")

        data_dir = _resolve_path(root, "RIP_DATA_DIR", root / "data")
        seed = _resolve_int("RIP_SEED", 42)
        log_level = os.getenv("RIP_LOG_LEVEL", "INFO").upper()
        backfill_start_date = _resolve_optional_date("RIP_BACKFILL_START_DATE")
        backfill_end_date = _resolve_optional_date("RIP_BACKFILL_END_DATE")
        if backfill_start_date and backfill_end_date and backfill_start_date > backfill_end_date:
            raise RuntimeError("RIP_BACKFILL_START_DATE must be <= RIP_BACKFILL_END_DATE.")

        return cls(
            project_root=root.resolve(),
            data_dir=data_dir,
            raw_dir=data_dir / "raw",
            bronze_dir=data_dir / "bronze",
            silver_dir=data_dir / "silver",
            gold_dir=data_dir / "gold",
            processed_dir=data_dir / "processed",
            warehouse_dir=data_dir / "warehouse",
            warehouse_db_path=data_dir / "warehouse" / "revenue_intelligence.db",
            semantic_metrics_path=_resolve_path(
                root,
                "RIP_SEMANTIC_METRICS_PATH",
                root / "metrics" / "semantic_metrics.json",
            ),
            alerts_output_path=data_dir / "processed" / "alerts_report.json",
            approvals_output_path=data_dir / "processed" / "approved_actions.csv",
            runs_dir=data_dir / "runs",
            manifests_dir=data_dir / "manifests",
            snapshots_dir=data_dir / "snapshots",
            data_dictionary_path=data_dir / "processed" / "data_dictionary.json",
            env_name=os.getenv("RIP_ENV", "local").strip().lower() or "local",
            warehouse_target=os.getenv("RIP_WAREHOUSE_TARGET", "sqlite").strip().lower(),
            warehouse_url=os.getenv("RIP_WAREHOUSE_URL", "").strip() or None,
            seed=seed,
            log_level=log_level,
            freshness_max_age_hours=_resolve_int("RIP_FRESHNESS_MAX_AGE_HOURS", 48, minimum=1),
            snapshot_retention_runs=_resolve_int("RIP_SNAPSHOT_RETENTION_RUNS", 10, minimum=1),
            snapshot_retention_days=_resolve_int("RIP_SNAPSHOT_RETENTION_DAYS", 30, minimum=1),
            failure_retention_days=_resolve_int("RIP_FAILURE_RETENTION_DAYS", 14, minimum=1),
            retry_attempts=_resolve_int("RIP_RETRY_ATTEMPTS", 1, minimum=1),
            retry_backoff_seconds=_resolve_int("RIP_RETRY_BACKOFF_SECONDS", 0, minimum=0),
            quality_max_null_fraction=_resolve_float(
                "RIP_QUALITY_MAX_NULL_FRACTION",
                0.20,
                minimum=0.0,
                maximum=1.0,
            ),
            alert_drift_feature_count_warn=_resolve_int(
                "RIP_ALERT_DRIFT_FEATURE_COUNT_WARN",
                1,
                minimum=0,
            ),
            alert_duplicate_rows_warn=_resolve_int(
                "RIP_ALERT_DUPLICATE_ROWS_WARN",
                0,
                minimum=0,
            ),
            alert_null_count_warn=_resolve_int(
                "RIP_ALERT_NULL_COUNT_WARN",
                0,
                minimum=0,
            ),
            alert_brier_score_warn=_resolve_float(
                "RIP_ALERT_BRIER_SCORE_WARN",
                0.25,
                minimum=0.0,
            ),
            alert_webhook_url=os.getenv("RIP_ALERT_WEBHOOK_URL", "").strip() or None,
            backfill_start_date=backfill_start_date,
            backfill_end_date=backfill_end_date,
            warehouse_schema=os.getenv("RIP_WAREHOUSE_SCHEMA", "").strip() or None,
            synthetic_customer_count=_resolve_int("RIP_SYNTHETIC_CUSTOMERS", 2500, minimum=1),
            allow_bundled_seed_fallback=_resolve_bool("RIP_ALLOW_BUNDLED_SEED_FALLBACK", True),
        )
