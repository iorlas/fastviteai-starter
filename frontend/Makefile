.PHONY: help
help: ## Show this help message
	@echo 'Available commands:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: bootstrap
bootstrap: ## Bootstrap frontend for first-time setup
	@echo "📦 Installing frontend dependencies..."
	pnpm install
	@echo "\n📝 Setting up frontend environment file..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env from .env.example"; \
	else \
		echo "⚠  .env already exists, skipping"; \
	fi
	@echo "\n✅ Frontend bootstrap complete!"
	@echo "   💡 Tip: Run 'make codegen' to regenerate API client after backend changes"

.PHONY: install
install: ## Install dependencies with pnpm
	pnpm install

.PHONY: dev
dev: ## Start Vite development server
	pnpm dev

.PHONY: build
build: ## Build for production
	pnpm build

.PHONY: preview
preview: ## Preview production build
	pnpm preview

.PHONY: check
check: ## Format and lint with auto-fix using Biome
	pnpm biome check src/ --write

.PHONY: test
test: ## Run tests with coverage using Vitest
	pnpm test

.PHONY: codegen
codegen: ## Generate TypeScript API client from OpenAPI spec
	pnpm codegen

.PHONY: clean
clean: ## Remove node_modules, build artifacts, and caches
	rm -rf node_modules
	rm -rf dist
	rm -rf .vite
	rm -rf coverage
