.PHONY: dev up down logs migrate makemigrations seed shell db-shell backup test lint

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend sh -c "cd /migrations && alembic upgrade head"

makemigrations:
	docker compose exec backend sh -c "cd /migrations && alembic revision --autogenerate -m '$(msg)'"

seed:
	docker compose exec backend python -m scripts.seed_db

shell:
	docker compose exec backend bash

db-shell:
	docker compose exec db psql -U tokyoradar -d tokyoradar

backup:
	bash scripts/backup_db.sh

test:
	docker compose exec backend pytest

lint:
	docker compose exec backend ruff check .
