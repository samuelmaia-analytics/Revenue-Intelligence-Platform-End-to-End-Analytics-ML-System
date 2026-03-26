PYTHON ?= python
DBT ?= dbt

.PHONY: help install install-dev pipeline artifacts dictionary serve-app serve-api lint format type-check test governance smoke-dashboard snapshot-dashboard smoke-api smoke-downstream smoke-exports smoke-partner smoke-dbt verify package smoke docker-build-app docker-build-api docker-build docker-smoke clean

help:
	@echo "Available targets:"
	@echo "  install            Install runtime dependencies"
	@echo "  install-dev        Install runtime and development dependencies"
	@echo "  pipeline           Run the official batch pipeline"
	@echo "  artifacts          Generate governance artifacts only"
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
	@echo "  verify             Run the local high-signal validation flow"
	@echo "  package            Build the package"
	@echo "  docker-build       Build both Docker images"
	@echo "  docker-smoke       Smoke-test the batch container"
	@echo "  clean              Remove local tooling caches"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

pipeline:
	$(PYTHON) -m src.pipeline run

artifacts: dictionary

dictionary:
	$(PYTHON) -m src.pipeline artifacts

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
	docker build -t revenue-intelligence .

docker-build-api:
	docker build -f Dockerfile.api -t revenue-intelligence-api .

docker-build: docker-build-app docker-build-api

docker-smoke:
	docker run --rm revenue-intelligence python -m src.pipeline run --log-level INFO

clean:
	$(PYTHON) -c "import pathlib, shutil; roots=[pathlib.Path('.')]; dirs={'.pytest_cache','.ruff_cache','.mypy_cache','__pycache__','.ipynb_checkpoints','htmlcov','.streamlit'}; files={'.coverage','coverage.xml'}; [shutil.rmtree(path, ignore_errors=True) for root in roots for path in root.rglob('*') if path.is_dir() and path.name in dirs]; [path.unlink(missing_ok=True) for root in roots for path in root.rglob('*') if path.is_file() and path.name in files]"
