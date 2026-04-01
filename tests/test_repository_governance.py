import tomllib
from pathlib import Path
from subprocess import run

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_repository_contains_high_signal_operational_docs() -> None:
    expected_paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "README.pt-BR.md",
        PROJECT_ROOT / "README.pt-PT.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "docs" / "architecture.md",
        PROJECT_ROOT / "docs" / "runtime_surfaces.md",
        PROJECT_ROOT / "docs" / "environments.md",
        PROJECT_ROOT / "docs" / "runbook.md",
        PROJECT_ROOT / "docs" / "incident_playbooks.md",
        PROJECT_ROOT / "docs" / "troubleshooting_matrix.md",
        PROJECT_ROOT / "docs" / "release_process.md",
        PROJECT_ROOT / "docs" / "deprecation_policy.md",
        PROJECT_ROOT / "docs" / "merge_policy.md",
        PROJECT_ROOT / "docs" / "sql_examples.md",
        PROJECT_ROOT / "docs" / "hiring_review.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.1.0.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.2.0.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.3.0.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.3.1.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.3.2.md",
        PROJECT_ROOT / "docs" / "releases" / "v1.3.3.md",
        PROJECT_ROOT / ".github" / "workflows" / "runtime-baseline.yml",
    ]
    for path in expected_paths:
        assert path.exists(), f"Missing governance or documentation asset: {path}"


def test_ci_workflow_enforces_core_quality_gates() -> None:
    workflow_text = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for expected_snippet in [
        "python -m pip install -e .[dev]",
        "python -m pip check",
        "Repository hygiene and governance tests",
        "python -m ruff check .",
        "python -m black --check .",
        "python -m isort --check-only .",
        "python -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing --cov-report=xml",
        "python scripts/smoke_dashboard.py",
        "python scripts/ui_snapshot.py",
        "python scripts/smoke_api.py",
        "python scripts/smoke_downstream_sql.py",
        "python scripts/smoke_processed_exports.py",
        "python scripts/smoke_partner_payload.py",
        "python scripts/smoke_dbt_sqlite.py",
        "python scripts/assert_runtime_metrics.py ci_artifacts/data/processed/runtime_metrics.json metrics/runtime_baseline.json",
        "API container smoke test",
        "Wheel install smoke test",
        "http://127.0.0.1:8000/health",
        "python -m build",
        "ci_artifacts/data/processed/runtime_metrics.json",
    ]:
        assert expected_snippet in workflow_text


def test_pr_template_and_makefile_expose_senior_review_workflow() -> None:
    pr_template = (PROJECT_ROOT / ".github" / "pull_request_template.md").read_text(
        encoding="utf-8"
    )
    makefile_text = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    for expected_snippet in [
        "Official batch path affected",
        "Contracts affected",
        "Residual risks",
        "Rollback path",
    ]:
        assert expected_snippet in pr_template

    for expected_target in [
        "help:",
        "smoke-dashboard:",
        "snapshot-dashboard:",
        "smoke-api:",
        "smoke-downstream:",
        "smoke-exports:",
        "smoke-partner:",
        "smoke-dbt:",
        "assert-runtime:",
        "update-runtime-baseline:",
        "verify:",
        "clean:",
    ]:
        assert expected_target in makefile_text


def test_readme_and_docs_map_reference_core_operational_docs() -> None:
    readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    docs_map_text = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    shared_references = [
        "docs/architecture.md",
        "docs/runtime_surfaces.md",
        "docs/environments.md",
        "docs/runbook.md",
        "docs/troubleshooting_matrix.md",
        "docs/release_process.md",
        "docs/deprecation_policy.md",
        "docs/merge_policy.md",
        "docs/sql_examples.md",
        "docs/incident_playbooks.md",
        "docs/hiring_review.md",
    ]
    for reference in shared_references:
        assert reference in readme_text
        assert reference.replace("docs/", "") in docs_map_text or reference in docs_map_text


def test_issue_template_config_routes_users_to_operational_docs() -> None:
    config_text = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(
        encoding="utf-8"
    )
    assert "blank_issues_enabled: false" in config_text
    assert "docs/runbook.md" in config_text
    assert "docs/README.md" in config_text


def test_issue_templates_use_merge_policy_labels() -> None:
    bug_report = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(
        encoding="utf-8"
    )
    change_request = (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "change_request.yml").read_text(
        encoding="utf-8"
    )
    documentation_request = (
        PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / "documentation_request.yml"
    ).read_text(encoding="utf-8")

    assert "- runtime" in bug_report
    assert "- runtime" in change_request
    assert "- docs" in documentation_request


def test_pyproject_declares_runtime_and_dev_dependency_paths() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    runtime_dependencies = "\n".join(project["dependencies"])
    dev_dependencies = "\n".join(project["optional-dependencies"]["dev"])
    requirements_dev = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")

    for expected_runtime in ["fastapi==0.115.12", "pydantic==2.11.2", "streamlit==1.43.1"]:
        assert expected_runtime in runtime_dependencies

    for expected_dev in ["pytest==8.3.5", "pytest-cov==6.0.0", "mypy==1.11.2", "ruff==0.6.9"]:
        assert expected_dev in dev_dependencies

    assert "-r requirements.txt" in requirements_dev


def test_onboarding_uses_package_install_and_install_smoke() -> None:
    onboarding = (PROJECT_ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")

    for expected_snippet in [
        "python -m pip install -e .[dev]",
        "python -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing",
        "python -m pip check",
        "python -m src.pipeline --help",
    ]:
        assert expected_snippet in onboarding


def test_gitignore_blocks_local_secrets_and_database_artifacts() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    for expected_snippet in [
        ".env",
        "*.db",
        "data/warehouse/*.db",
    ]:
        assert expected_snippet in gitignore


def test_git_tracked_files_exclude_generated_runtime_artifacts() -> None:
    tracked_files = run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    forbidden_prefixes = [
        "data/processed/",
        "data/warehouse/",
        "data/manifests/",
        "data/runs/",
        "data/snapshots/",
    ]
    forbidden_suffixes = [".db", ".log"]

    offending = [
        path
        for path in tracked_files
        if any(path.startswith(prefix) for prefix in forbidden_prefixes)
        or any(path.endswith(suffix) for suffix in forbidden_suffixes)
    ]

    assert offending == [], f"Tracked generated artifacts must be removed: {offending}"


def test_runtime_baseline_is_versioned_for_ci_regression_checks() -> None:
    baseline_path = PROJECT_ROOT / "metrics" / "runtime_baseline.json"
    assert baseline_path.exists()


def test_runtime_baseline_workflow_opens_pull_request() -> None:
    workflow_text = (PROJECT_ROOT / ".github" / "workflows" / "runtime-baseline.yml").read_text(
        encoding="utf-8"
    )

    for expected_snippet in [
        "contents: write",
        "pull-requests: write",
        "peter-evans/create-pull-request@v7",
        "peter-evans/enable-pull-request-automerge@v3",
        'branch: "automation/runtime-baseline-${{ github.run_id }}"',
        'title: "chore: refresh runtime baseline"',
        "continue-on-error: true",
        "merge-method: squash",
        "runtime",
        "docs",
        "assignees: samuelmaia",
        "reviewers: samuelmaia",
    ]:
        assert expected_snippet in workflow_text
