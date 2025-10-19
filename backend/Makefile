.PHONY: help
help: ## Show this help message
	@echo 'Available commands:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: bootstrap
bootstrap: ## Bootstrap backend for first-time setup
	@echo "📦 Installing backend dependencies..."
	uv sync
	@echo "\n📝 Setting up backend environment file..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env from .env.example"; \
		echo "⚠  Please review .env and update SECRET_KEY and JWT_SECRET for production"; \
	else \
		echo "⚠  .env already exists, skipping"; \
	fi

.PHONY: install
install: ## Install dependencies with uv
	uv sync

.PHONY: dev
dev: ## Start uvicorn development server with hot reload
	uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --no-access-log

.PHONY: check
check: ## Format code, lint with auto-fix, and type check
	uv run ruff format .
	uv run ruff check --fix .
	uvx ty check .

.PHONY: test
test: ## Run tests with coverage report
	uv run pytest --cov=app --cov-report=term-missing

.PHONY: migrate
migrate: ## Apply database migrations
	uv run alembic upgrade head

.PHONY: migrate-create
migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate-create MSG=\"description\""; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	uv run alembic downgrade -1

.PHONY: clean
clean: ## Remove cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
