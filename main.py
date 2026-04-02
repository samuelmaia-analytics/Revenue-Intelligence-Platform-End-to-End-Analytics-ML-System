from pathlib import Path

from src.bootstrap import run_pipeline_from_env
from src.orchestration import run_pipeline

__all__ = ["run_pipeline"]

if __name__ == "__main__":
    run_pipeline_from_env(Path(__file__))
