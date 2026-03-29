.PHONY: setup lint format test dev dev-backend dev-frontend

setup:
	uv run python scripts/dev.py setup

lint:
	uv run python scripts/dev.py lint

format:
	uv run python scripts/dev.py format

test:
	uv run python scripts/dev.py test

dev:
	uv run python scripts/dev.py dev

dev-backend:
	uv run python scripts/dev.py dev-backend

dev-frontend:
	uv run python scripts/dev.py dev-frontend
