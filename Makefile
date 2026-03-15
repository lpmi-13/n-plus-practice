.PHONY: setup seed test check start stop logs shell migrate video video-silent

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

## Generate walkthrough video (usage: make video or make video exercise=01_basic)
video:
ifdef exercise
	python -m walkthroughs.cli generate --exercise $(exercise) --quality low
else
	python -m walkthroughs.cli generate --all --quality low
endif

## Generate video without audio
video-silent:
ifdef exercise
	python -m walkthroughs.cli generate --exercise $(exercise) --no-audio --quality low
else
	python -m walkthroughs.cli generate --all --no-audio --quality low
endif

## Generate high-quality video
video-hq:
ifdef exercise
	python -m walkthroughs.cli generate --exercise $(exercise) --quality high
else
	python -m walkthroughs.cli generate --all --quality high
endif

## List available walkthrough specs
video-list:
	python -m walkthroughs.cli list

## Validate walkthrough specs
video-validate:
	@for f in walkthroughs/specs/*.yaml; do \
		echo "Validating $$f..."; \
		python -m walkthroughs.cli validate --spec "$$f"; \
	done
