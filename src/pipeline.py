import argparse
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

from src.bootstrap import load_config, resolve_project_root
from src.config import PipelineConfig
from src.observability import export_observability_summary


def _parse_cli_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc


def _parse_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Value must be an integer.") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("Value must be >= 1.")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Revenue Intelligence Platform CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_cmd = subparsers.add_parser("run", help="Run end-to-end pipeline")
    run_cmd.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (default: <project_root>/data).",
    )
    run_cmd.add_argument("--seed", type=int, default=None, help="Override random seed.")
    run_cmd.add_argument(
        "--start-date",
        type=_parse_cli_date,
        default=None,
        help="Optional inclusive backfill start date for order data (YYYY-MM-DD).",
    )
    run_cmd.add_argument(
        "--end-date",
        type=_parse_cli_date,
        default=None,
        help="Optional inclusive backfill end date for source data (YYYY-MM-DD).",
    )
    run_cmd.add_argument(
        "--retry-attempts",
        type=_parse_positive_int,
        default=None,
        help="Override stage retry attempts for transient failures.",
    )
    run_cmd.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level.",
    )
    artifacts_cmd = subparsers.add_parser(
        "artifacts",
        help="Generate governance artifacts without running the full pipeline.",
    )
    artifacts_cmd.add_argument(
        "--data-dictionary-path",
        type=str,
        default=None,
        help="Override data dictionary output path.",
    )

    observability_cmd = subparsers.add_parser(
        "observability",
        help="Summarize processed run observability artifacts.",
    )
    observability_cmd.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Override data directory (default: <project_root>/data).",
    )
    observability_cmd.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Optional JSON output path for the observability summary.",
    )
    return parser


def _resolve_config(args: argparse.Namespace) -> PipelineConfig:
    cfg = load_config(resolve_project_root(Path(__file__).resolve().parents[1]))
    data_dir = (
        (cfg.project_root / args.data_dir).resolve()
        if getattr(args, "data_dir", None) and not Path(args.data_dir).is_absolute()
        else (Path(args.data_dir).resolve() if getattr(args, "data_dir", None) else None)
    )
    seed = getattr(args, "seed", None)
    log_level = getattr(args, "log_level", None)
    retry_attempts = getattr(args, "retry_attempts", None)
    resolved = cfg.with_overrides(
        data_dir=data_dir,
        seed=seed,
        log_level=log_level,
        backfill_start_date=getattr(args, "start_date", None),
        backfill_end_date=getattr(args, "end_date", None),
    )
    if retry_attempts is not None:
        return replace(resolved, retry_attempts=retry_attempts)
    return resolved


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "run":
        from src.orchestration import run_pipeline

        cfg = _resolve_config(args)
        run_pipeline(cfg)
        return

    if args.command == "artifacts":
        from src.governance import build_data_dictionary

        cfg = load_config(resolve_project_root(Path(__file__).resolve().parents[1]))
        dictionary_output_path = (
            Path(args.data_dictionary_path)
            if args.data_dictionary_path
            else cfg.data_dictionary_path
        )
        dictionary = build_data_dictionary(dictionary_output_path)
        print(
            json.dumps(
                {
                    "data_dictionary_path": str(dictionary_output_path),
                    "tables": len(dictionary["tables"]),
                }
            )
        )
        return

    if args.command == "observability":
        cfg = _resolve_config(args)
        observability_output_path: Path | None = (
            Path(args.output_path).resolve() if args.output_path else None
        )
        summary = export_observability_summary(
            cfg.processed_dir,
            output_path=observability_output_path,
        )
        print(json.dumps(summary, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
