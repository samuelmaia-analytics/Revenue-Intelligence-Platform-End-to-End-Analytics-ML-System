PYTHON ?= python
DBT ?= dbt

.PHONY: help bootstrap install install-dev pipeline backfill artifacts dictionary lint format type-check test test-cov smoke-dashboard snapshot-dashboard smoke-api smoke-downstream smoke-exports smoke-partner smoke-dbt smoke-postgres-optional verify-core verify serve-app serve-api package docker-build-app docker-build-api docker-build docker-smoke dbt-run dbt-test dbt-docs clean

help:
	@echo "High-signal targets:"
	@echo "  bootstrap          Install project in editable mode with development dependencies"
	@echo "  pipeline           Run the official batch pipeline"
	@echo "  backfill           Run a sample bounded backfill"
	@echo "  verify-core        Run lint, typing, tests, and package build"
	@echo "  verify             Run verify-core plus smoke and downstream checks"
	@echo "  smoke-postgres-optional Run the optional Postgres smoke when RIP_SMOKE_POSTGRES_URL is set"
	@echo "  serve-app          Start the Streamlit app"
	@echo "  serve-api          Start the FastAPI service"
	@echo "  docker-build       Build both Docker images"
	@echo "  docker-smoke       Smoke-test the batch container"
	@echo "  clean              Remove local caches and coverage artifacts"

bootstrap:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

pipeline:
	$(PYTHON) -m src.pipeline run

backfill:
	$(PYTHON) -m src.pipeline run --start-date 2025-01-01 --end-date 2025-03-31 --log-level INFO

artifacts: dictionary

dictionary:
	$(PYTHON) -m src.pipeline artifacts

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

test-cov:
	$(PYTHON) -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing

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

smoke-postgres-optional:
	$(PYTHON) scripts/smoke_postgres_optional.py

verify-core: lint type-check test-cov package

verify: verify-core smoke-dashboard snapshot-dashboard smoke-api smoke-downstream smoke-exports smoke-partner smoke-dbt

serve-app:
	$(PYTHON) -m streamlit run app/streamlit_app.py

serve-api:
	$(PYTHON) -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

package:
	$(PYTHON) -m build

docker-build-app:
	docker build -t revenue-intelligence .

docker-build-api:
	docker build -f Dockerfile.api -t revenue-intelligence-api .

docker-build: docker-build-app docker-build-api

docker-smoke:
	docker run --rm revenue-intelligence python -m src.pipeline run --log-level INFO

dbt-run:
	$(DBT) --project-dir dbt run

dbt-test:
	$(DBT) --project-dir dbt test

dbt-docs:
	$(DBT) --project-dir dbt docs generate

clean:
	$(PYTHON) -c "import pathlib, shutil; roots=[pathlib.Path('.')]; dirs={'.pytest_cache','.ruff_cache','.mypy_cache','__pycache__','.ipynb_checkpoints','htmlcov','.streamlit'}; files={'.coverage','coverage.xml'}; [shutil.rmtree(path, ignore_errors=True) for root in roots for path in root.rglob('*') if path.is_dir() and path.name in dirs]; [path.unlink(missing_ok=True) for root in roots for path in root.rglob('*') if path.is_file() and path.name in files]"
