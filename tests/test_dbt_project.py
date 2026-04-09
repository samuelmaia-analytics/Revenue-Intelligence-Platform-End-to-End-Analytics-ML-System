import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dbt_project_files_exist() -> None:
    expected_paths = [
        PROJECT_ROOT / "dbt" / "dbt_project.yml",
        PROJECT_ROOT / "dbt" / "models" / "sources.yml",
        PROJECT_ROOT / "dbt" / "models" / "marts" / "schema.yml",
        PROJECT_ROOT / "dbt" / "models" / "marts" / "finance" / "portfolio_semantic_metrics.sql",
        PROJECT_ROOT / "dbt" / "tests" / "high_churn_risk_pct_in_range.sql",
    ]
    for path in expected_paths:
        assert path.exists(), f"Missing dbt asset: {path}"


def test_dbt_semantic_metrics_align_with_catalog() -> None:
    catalog = json.loads(
        (PROJECT_ROOT / "metrics" / "semantic_metrics.json").read_text(encoding="utf-8")
    )
    semantic_metric_names = {metric["name"] for metric in catalog["metrics"]}
    model_sql = (
        PROJECT_ROOT / "dbt" / "models" / "marts" / "finance" / "portfolio_semantic_metrics.sql"
    ).read_text(encoding="utf-8")

    for metric_name in semantic_metric_names:
        assert metric_name in model_sql, f"dbt semantic model is missing metric '{metric_name}'"


def test_dbt_schema_contains_core_models() -> None:
    schema_text = (PROJECT_ROOT / "dbt" / "models" / "marts" / "schema.yml").read_text(
        encoding="utf-8"
    )
    for model_name in [
        "portfolio_semantic_metrics",
        "channel_semantic_metrics",
        "action_priority_board",
    ]:
        assert f"- name: {model_name}" in schema_text


def test_semantic_metric_catalog_contains_enterprise_metadata() -> None:
    catalog = json.loads(
        (PROJECT_ROOT / "metrics" / "semantic_metrics.json").read_text(encoding="utf-8")
    )
    for metric in catalog["metrics"]:
        assert "source_model" in metric
        assert "decision_use" in metric
        assert "consumer_surfaces" in metric
