.PHONY: help install dev install-libs test lint clean run-dashboard run-cli docker-build docker-up

help:
	@echo "AI Red Blue Platform - Makefile"
	@echo ""
	@echo "Commands:"
	@echo "  install          - Install all dependencies"
	@echo "  dev              - Install development dependencies"
	@echo "  install-libs     - Install all library packages"
	@echo "  test             - Run tests"
	@echo "  lint             - Run linting"
	@echo "  clean            - Clean build artifacts"
	@echo "  run-dashboard     - Run Dashboard"
	@echo "  run-cli          - Run CLI"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-up        - Start Docker containers"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black ruff mypy

install-libs:
	cd libs/common && pip install -e .
	cd ../security && pip install -e .
	cd ../core && pip install -e .
	cd ../ai && pip install -e .

test:
	pytest --cov=libs --cov-report=html

lint:
	ruff check .
	black --check .
	mypy .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage

run-dashboard:
	python apps/dashboard/main.py

run-cli:
	python apps/cli/main.py status

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
