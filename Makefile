.PHONY: help install dev test lint format docker-up docker-down clean

help:
	@echo "Available commands: install, dev, test, lint, format, docker-up, docker-down, clean"

install:
	cd backend && poetry install

dev:
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

test:
	cd backend && poetry run pytest --cov=app tests/

lint:
	cd backend && poetry run ruff check .

format:
	cd backend && poetry run ruff format .

docker-up:
	docker-compose -f docker/docker-compose.yml up -d --build

docker-down:
	docker-compose -f docker/docker-compose.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
