.DEFAULT_GOAL := help

# Match .env.example; update these if you changed them in your own .env
DB_USER := receipt
DB_NAME := receipts

.PHONY: help build up down logs reset-db nuke shell psql test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Build the app image
	docker compose build app

up: ## Build (if needed) and start the full stack in the background
	docker compose up --build -d

down: ## Stop and remove containers (keeps saved data)
	docker compose down

logs: ## Follow the app's logs
	docker compose logs -f app

reset-db: ## Wipe saved transactions, keep the schema and Postgres volume
	docker compose exec db psql -U $(DB_USER) -d $(DB_NAME) -c "TRUNCATE TABLE transactions RESTART IDENTITY;"

nuke: ## Stop everything AND delete the Postgres volume (fresh start)
	docker compose down -v

shell: ## Open a shell inside the running app container
	docker compose exec app bash

psql: ## Open a psql prompt against the database
	docker compose exec db psql -U $(DB_USER) -d $(DB_NAME)

test: ## Run the extraction unit tests (no Docker/OCR/DB needed)
	python3 -m pytest
