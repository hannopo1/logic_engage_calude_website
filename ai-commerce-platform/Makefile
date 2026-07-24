# AI Commerce Platform — developer shortcuts
# Usage: `make up`, `make seed`, `make down`, ...

.PHONY: help up build down logs seed migrate revision test backend-shell db-shell

help:
	@echo "Targets:"
	@echo "  make up        - build + start the whole stack (db, redis, backend, frontend)"
	@echo "  make seed      - load the demo catalog into the database"
	@echo "  make down      - stop the stack"
	@echo "  make logs      - tail all service logs"
	@echo "  make migrate   - apply DB migrations (alembic upgrade head)"
	@echo "  make revision m=\"msg\" - autogenerate a new migration"
	@echo "  make test      - run backend tests"

up:
	@[ -f .env ] || cp .env.example .env
	docker compose up --build -d
	@echo "Backend:  http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"

build:
	docker compose build

down:
	docker compose down

logs:
	docker compose logs -f

seed:
	docker compose exec backend python -m app.seed

migrate:
	docker compose exec backend alembic upgrade head

revision:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

test:
	docker compose exec backend pytest -q

backend-shell:
	docker compose exec backend sh

db-shell:
	docker compose exec db psql -U commerce -d commerce
