.PHONY: install test lint format build up down bootstrap demo bench report
install:
	python -m pip install -r requirements-dev.lock
	python -m pip install --no-deps -e .
test:
	PENNY_MOCK=1 python -m pytest --cov=penny --cov-report=term-missing
lint:
	ruff check .
	ruff format --check .
format:
	ruff check . --fix
	ruff format .
build:
	python -m build
up:
	docker compose up --build -d --wait
down:
	docker compose down
bootstrap:
	python scripts/bootstrap_bifrost.py
demo:
	python scripts/record_demo.py --mock
bench:
	penny bench --n 3
report:
	penny report --open
