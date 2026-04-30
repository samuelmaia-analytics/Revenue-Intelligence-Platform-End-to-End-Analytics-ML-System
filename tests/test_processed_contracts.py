from contracts.processed_contract import (
    CSV_ARTIFACT_SPECS,
    JSON_ARTIFACT_SPECS,
    PROCESSED_CONTRACT_VERSION,
)
from contracts.v1.processed_contract import CSV_ARTIFACT_SPECS as V1_CSV_ARTIFACT_SPECS
from contracts.v1.processed_contract import JSON_ARTIFACT_SPECS as V1_JSON_ARTIFACT_SPECS
from src.artifact_validation import validate_processed_artifacts
from tests.test_artifact_validation import _build_valid_processed_artifacts


def test_processed_contract_backward_compatibility_shim_matches_v1() -> None:
    assert PROCESSED_CONTRACT_VERSION == "1.0.0"
    assert CSV_ARTIFACT_SPECS == V1_CSV_ARTIFACT_SPECS
    assert JSON_ARTIFACT_SPECS == V1_JSON_ARTIFACT_SPECS


def test_processed_contract_contains_curated_and_operational_artifacts() -> None:
    for required_csv in [
        "customer_features.csv",
        "recommendations.csv",
        "unit_economics.csv",
        "top_10_actions.csv",
    ]:
        assert required_csv in CSV_ARTIFACT_SPECS

    for required_json in [
        "quality_report.json",
        "freshness_report.json",
        "monitoring_report.json",
        "alerts_report.json",
        "semantic_metrics_catalog.json",
    ]:
        assert required_json in JSON_ARTIFACT_SPECS


def test_processed_contract_can_validate_against_previous_version_for_rollback(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    _build_valid_processed_artifacts(processed_dir)

    report = validate_processed_artifacts(
        processed_dir,
        csv_artifact_specs=V1_CSV_ARTIFACT_SPECS,
        json_artifact_specs=V1_JSON_ARTIFACT_SPECS,
        contract_version="1.0.0",
    )

    assert report["status"] == "ok"
    assert report["contract_version"] == "1.0.0"
