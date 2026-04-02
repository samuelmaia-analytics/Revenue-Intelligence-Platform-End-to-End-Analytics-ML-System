from __future__ import annotations

from pathlib import Path

from src.config import PipelineConfig
from src.orchestration import run_pipeline


def resolve_project_root(anchor: Path | None = None) -> Path:
    candidate = anchor or Path(__file__)
    resolved = candidate.resolve()
    return resolved.parent if resolved.is_file() else resolved


def load_config(project_root: Path | None = None) -> PipelineConfig:
    return PipelineConfig.from_env(resolve_project_root(project_root))


def run_pipeline_from_env(project_root: Path | None = None) -> dict:
    return run_pipeline(load_config(project_root))
