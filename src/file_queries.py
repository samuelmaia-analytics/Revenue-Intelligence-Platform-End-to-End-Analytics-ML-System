from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import PipelineConfig

duckdb: Any | None
try:
    import duckdb
except ImportError:  # pragma: no cover
    duckdb = None


RAW_ALIAS_BY_FILE = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_customers_dataset.csv": "customers",
    "olist_products_dataset.csv": "products",
    "product_category_name_translation.csv": "category_translation",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
}


@dataclass(frozen=True)
class QueryableRelation:
    layer: str
    relation: str
    path: Path


def duckdb_available() -> bool:
    return duckdb is not None


def _sanitize_relation_name(path: Path) -> str:
    stem = path.stem.strip().lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    return stem


def _relation_name_for_csv(layer: str, path: Path) -> str:
    if layer == "raw":
        alias = RAW_ALIAS_BY_FILE.get(path.name.lower())
        if alias:
            return alias
    return _sanitize_relation_name(path)


def discover_queryable_relations(cfg: PipelineConfig) -> list[QueryableRelation]:
    layers = {
        "raw": cfg.raw_dir,
        "bronze": cfg.bronze_dir,
        "silver": cfg.silver_dir,
        "gold": cfg.gold_dir,
        "processed": cfg.processed_dir,
    }
    relations: list[QueryableRelation] = []
    seen_refs: set[tuple[str, str]] = set()
    for layer, directory in layers.items():
        if not directory.exists():
            continue
        paths = sorted(
            directory.glob("*.csv"),
            key=lambda candidate: (
                0 if layer == "raw" and candidate.name.lower() in RAW_ALIAS_BY_FILE else 1,
                candidate.name.lower(),
            ),
        )
        for path in paths:
            relation_name = _relation_name_for_csv(layer, path)
            if (layer, relation_name) in seen_refs:
                relation_name = f"{_sanitize_relation_name(path)}_file"
            relations.append(
                QueryableRelation(
                    layer=layer,
                    relation=relation_name,
                    path=path,
                )
            )
            seen_refs.add((layer, relation_name))
    return relations


def build_query_connection(cfg: PipelineConfig) -> Any:
    if duckdb is None:
        raise RuntimeError("DuckDB is required to query governed CSV layers.")

    connection = duckdb.connect(database=":memory:")
    for relation in discover_queryable_relations(cfg):
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {relation.layer}")
        safe_path = relation.path.as_posix().replace("'", "''")
        connection.execute(
            f"""
            CREATE OR REPLACE VIEW {relation.layer}.{relation.relation} AS
            SELECT * FROM read_csv_auto('{safe_path}', HEADER=TRUE)
            """
        )
        connection.execute(
            f"""
            CREATE OR REPLACE VIEW {relation.layer}_{relation.relation} AS
            SELECT * FROM {relation.layer}.{relation.relation}
            """
        )
    return connection


def run_query(sql: str, cfg: PipelineConfig) -> pd.DataFrame:
    connection = build_query_connection(cfg)
    try:
        return connection.execute(sql).df()
    finally:
        connection.close()


def list_queryable_objects(cfg: PipelineConfig) -> pd.DataFrame:
    rows = [
        {
            "layer": relation.layer,
            "relation": relation.relation,
            "path": str(relation.path),
            "schema_ref": f"{relation.layer}.{relation.relation}",
            "flat_ref": f"{relation.layer}_{relation.relation}",
        }
        for relation in discover_queryable_relations(cfg)
    ]
    return pd.DataFrame(rows)


def _print_table(frame: pd.DataFrame) -> None:
    if frame.empty:
        print("(sem linhas)")
        return
    print(frame.to_string(index=False))


def _write_output(frame: pd.DataFrame, output_path: Path, output_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "csv":
        frame.to_csv(output_path, index=False)
        return
    if output_format == "json":
        output_path.write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")
        return
    if output_format == "parquet":
        frame.to_parquet(output_path, index=False)
        return
    raise ValueError(f"Unsupported output format: {output_format}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query governed CSV layers with DuckDB without changing the batch architecture."
    )
    parser.add_argument(
        "--sql", help="SQL query to execute against raw/bronze/silver/gold/processed."
    )
    parser.add_argument(
        "--file",
        dest="sql_file",
        type=Path,
        help="Path to a .sql file to execute.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all queryable relations discovered from the governed CSV layers.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional path to persist the query result.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "parquet", "table"],
        default="table",
        help="Output format. Defaults to table on stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not duckdb_available():
        parser.error("DuckDB is not installed in the current environment.")

    cfg = PipelineConfig.from_env()

    if args.list:
        frame = list_queryable_objects(cfg)
        if args.output_path:
            _write_output(frame, args.output_path, "csv" if args.format == "table" else args.format)
        else:
            _print_table(frame)
        return 0

    sql: str | None = args.sql
    if args.sql_file:
        sql = args.sql_file.read_text(encoding="utf-8")
    if not sql:
        parser.error("Provide --sql, --file or --list.")

    frame = run_query(sql, cfg)
    if args.output_path:
        _write_output(frame, args.output_path, "csv" if args.format == "table" else args.format)
    else:
        _print_table(frame)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
