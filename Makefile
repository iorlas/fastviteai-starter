.PHONY: help
help: ## Show this help message
	@echo 'Available commands:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: bootstrap
bootstrap: ## Bootstrap the project for first-time setup
	@echo "🚀 Bootstrapping project..."
	@echo "\n📦 Installing pre-commit hooks..."
	@if ! command -v prek >/dev/null 2>&1; then \
		echo "Installing prek..."; \
		uv tool install prek; \
	fi
	prek install
	@echo "\n=== Backend Bootstrap ==="
	cd backend && $(MAKE) bootstrap
	@echo "\n🐘 Starting PostgreSQL database..."
	docker-compose up -d postgres
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "\n🔄 Running database migrations..."
	cd backend && $(MAKE) migrate
	@echo "\n=== Frontend Bootstrap ==="
	cd frontend && $(MAKE) bootstrap
	@echo "\n✅ Bootstrap complete!"
	@echo "   🚀 Run 'make dev' to start the application"
	@echo "   💡 API client is pre-generated. Run 'cd frontend && make codegen' after backend API changes"

.PHONY: dev
dev: ## Start all services with Docker Compose (build, remove orphans)
	docker-compose up --build --remove-orphans

.PHONY: db
db: ## Start only database for local development
	docker-compose up postgres

.PHONY: down
down: ## Stop all services
	docker-compose down

.PHONY: clean
clean: ## Stop all services and remove volumes
	docker-compose down -v

.PHONY: logs
logs: ## View logs from all services
	docker-compose logs -f

.PHONY: ps
ps: ## Show running services
	docker-compose ps

.PHONY: check
check: ## Run pre-commit hooks on all files
	prek run --all-files
