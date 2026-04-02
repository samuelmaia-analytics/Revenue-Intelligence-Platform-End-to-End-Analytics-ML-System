PYTHON ?= python
DBT ?= dbt

.PHONY: help install install-dev pipeline artifacts dictionary observability serve-app serve-api lint format type-check test governance smoke-dashboard snapshot-dashboard smoke-api smoke-streamlit smoke-downstream smoke-exports smoke-partner smoke-dbt assert-runtime update-runtime-baseline verify package smoke docker-build-app docker-build-batch docker-build-api docker-build docker-smoke clean

help:
	@echo "Available targets:"
	@echo "  install            Install runtime dependencies"
	@echo "  install-dev        Install runtime and development dependencies"
	@echo "  pipeline           Run the official batch pipeline"
	@echo "  artifacts          Generate governance artifacts only"
	@echo "  observability      Export the batch observability summary"
	@echo "  serve-app          Start the Streamlit app"
	@echo "  serve-api          Start the FastAPI service"
	@echo "  lint               Run isort, ruff, and black checks"
	@echo "  format             Apply import sorting, black, and ruff fixes"
	@echo "  type-check         Run mypy"
	@echo "  test               Run pytest"
	@echo "  governance         Run repository-governance and operational-asset tests"
	@echo "  smoke-dashboard    Run the dashboard smoke check"
	@echo "  snapshot-dashboard Run the dashboard UI snapshot check"
	@echo "  smoke-api          Run the FastAPI smoke check"
	@echo "  smoke-downstream   Run the downstream SQL smoke check"
	@echo "  smoke-exports      Run the processed exports smoke check"
	@echo "  smoke-partner      Run the partner payload smoke check"
	@echo "  smoke-dbt          Run the dbt SQLite smoke validation"
	@echo "  assert-runtime     Assert runtime metrics stay within CI thresholds"
	@echo "  update-runtime-baseline Promote current runtime metrics into the versioned baseline"
	@echo "  verify             Run the local high-signal validation flow"
	@echo "  package            Build the package"
	@echo "  docker-build       Build dashboard, batch, and API Docker images"
	@echo "  docker-smoke       Smoke-test the batch container"
	@echo "  smoke-streamlit    Smoke-test the local Streamlit surface"
	@echo "  clean              Remove local tooling caches"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev: install
	$(PYTHON) -m pip install -e .[dev]

pipeline:
	$(PYTHON) -m src.pipeline run

artifacts: dictionary

dictionary:
	$(PYTHON) -m src.pipeline artifacts

observability:
	$(PYTHON) -m src.pipeline observability --output-path data/processed/observability_summary.json

serve-app:
	$(PYTHON) -m streamlit run app/streamlit_app.py

serve-api:
	$(PYTHON) -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	$(PYTHON) -m isort --check-only .
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

format:
	$(PYTHON) -m isort .
	$(PYTHON) -m black .
	$(PYTHON) -m ruff check . --fix

type-check:
	$(PYTHON) -m mypy src services contracts main.py

test:
	$(PYTHON) -m pytest -q

governance:
	$(PYTHON) -m pytest -q tests/test_repository_governance.py tests/test_operational_assets.py

smoke-dashboard:
	$(PYTHON) scripts/smoke_dashboard.py

snapshot-dashboard:
	$(PYTHON) scripts/ui_snapshot.py

smoke-api:
	$(PYTHON) scripts/smoke_api.py

smoke-downstream:
	$(PYTHON) scripts/smoke_downstream_sql.py

smoke-exports:
	$(PYTHON) scripts/smoke_processed_exports.py

smoke-partner:
	$(PYTHON) scripts/smoke_partner_payload.py

smoke-dbt:
	$(PYTHON) scripts/smoke_dbt_sqlite.py

assert-runtime:
	$(PYTHON) scripts/assert_runtime_metrics.py data/processed/runtime_metrics.json metrics/runtime_baseline.json

update-runtime-baseline:
	$(PYTHON) scripts/update_runtime_baseline.py data/processed/runtime_metrics.json metrics/runtime_baseline.json

quality: lint type-check test

verify: lint type-check test governance smoke-dashboard snapshot-dashboard smoke-api smoke-downstream smoke-exports smoke-partner smoke-dbt package

package:
	$(PYTHON) -m build

smoke:
	$(PYTHON) -m src.pipeline run --log-level INFO

dbt-run:
	$(DBT) --project-dir dbt run

dbt-test:
	$(DBT) --project-dir dbt test

dbt-docs:
	$(DBT) --project-dir dbt docs generate

docker-build-app:
	docker build -t revenue-intelligence-streamlit .

docker-build-batch:
	docker build -f Dockerfile.batch -t revenue-intelligence-batch .

docker-build-api:
	docker build -f Dockerfile.api -t revenue-intelligence-api .

docker-build: docker-build-app docker-build-batch docker-build-api

docker-smoke:
	docker run --rm revenue-intelligence-batch run --log-level INFO

smoke-streamlit:
	$(PYTHON) scripts/smoke_streamlit.py http://127.0.0.1:8501

clean:
	$(PYTHON) -c "import pathlib, shutil; roots=[pathlib.Path('.')]; dirs={'.pytest_cache','.ruff_cache','.mypy_cache','__pycache__','.ipynb_checkpoints','htmlcov','.streamlit'}; files={'.coverage','coverage.xml'}; [shutil.rmtree(path, ignore_errors=True) for root in roots for path in root.rglob('*') if path.is_dir() and path.name in dirs]; [path.unlink(missing_ok=True) for root in roots for path in root.rglob('*') if path.is_file() and path.name in files]"
