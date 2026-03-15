.PHONY: setup seed test check start stop logs shell migrate

## Start the environment (Docker Compose up)
start:
	docker compose up -d

## Stop the environment
stop:
	docker compose down

## Full setup: build, start, migrate, seed
setup:
	docker compose up -d --build
	@echo "Waiting for database..."
	@sleep 3
	docker compose exec web python manage.py migrate
	docker compose exec web python manage.py seed_db
	@echo ""
	@echo "Ready! Visit http://localhost:8000/graphql"

## Run database migrations
migrate:
	docker compose exec web python manage.py migrate

## Seed the database with sample data
seed:
	docker compose exec web python manage.py seed_db

## Run the test suite
test:
	docker compose exec web pytest -v

## Check query counts (usage: make check or make check q=products_with_category)
check:
	docker compose exec web python manage.py check_queries $(q)

## View container logs
logs:
	docker compose logs -f web

## Open a Django shell
shell:
	docker compose exec web python manage.py shell
