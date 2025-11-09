.PHONY: check format lint typecheck test init
.PHONY: docker-dev-build docker-dev-up docker-dev-down docker-dev-logs docker-dev-restart docker-dev-clean
.PHONY: docker-prod-build docker-prod-up docker-prod-down docker-prod-logs docker-prod-restart docker-prod-clean
.PHONY: docker-build docker-up docker-down docker-logs docker-restart docker-clean

# ============================================
# Local Development Commands
# ============================================

check: format lint typecheck test

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

typecheck:
	uv run uvx ty check .

test:
	uv run pytest

init:
	uv venv
	uv sync
	uvx prek

# ============================================
# Docker Development Commands
# ============================================

# Build development Docker images
docker-dev-build:
	docker compose -f docker-compose.dev.yml build

# Start development services (detached)
docker-dev-up:
	docker compose -f docker-compose.dev.yml up -d --build --remove-orphans

# Stop development services
docker-dev-down:
	docker compose -f docker-compose.dev.yml down

# View development logs (follow mode)
docker-dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

# Restart development services
docker-dev-restart:
	docker compose -f docker-compose.dev.yml restart

# Stop and remove development containers, networks, and volumes
docker-dev-clean:
	docker compose -f docker-compose.dev.yml down -v

# Rebuild and restart development services
docker-dev-rebuild:
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.dev.yml build
	docker compose -f docker-compose.dev.yml up -d

# Check status of development services
docker-dev-status:
	docker compose -f docker-compose.dev.yml ps

# ============================================
# Docker Production Commands
# ============================================

# Build production Docker images
docker-prod-build:
	docker compose -f docker-compose.prod.yml build

# Start production services (detached)
docker-prod-up:
	docker compose -f docker-compose.prod.yml up -d  --build --remove-orphans

# Stop production services
docker-prod-down:
	docker compose -f docker-compose.prod.yml down

# View production logs (follow mode)
docker-prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

# Restart production services
docker-prod-restart:
	docker compose -f docker-compose.prod.yml restart

# Stop and remove production containers, networks, and volumes
docker-prod-clean:
	docker compose -f docker-compose.prod.yml down -v

# Rebuild and restart production services
docker-prod-rebuild:
	docker compose -f docker-compose.prod.yml down
	docker compose -f docker-compose.prod.yml build
	docker compose -f docker-compose.prod.yml up -d

# Check status of production services
docker-prod-status:
	docker compose -f docker-compose.prod.yml ps

# ============================================
# Docker Commands (Backwards Compatibility - defaults to dev)
# ============================================

# Build Docker images
docker-build: docker-dev-build

# Start all services (detached)
docker-up: docker-dev-up

# Stop all services
docker-down: docker-dev-down

# View logs (follow mode)
docker-logs: docker-dev-logs

# View logs for specific service (usage: make docker-logs-service SERVICE=dagster-webserver)
docker-logs-service:
	docker compose -f docker-compose.dev.yml logs -f $(SERVICE)

# Restart all services
docker-restart: docker-dev-restart

# Restart specific service (usage: make docker-restart-service SERVICE=dagster-webserver)
docker-restart-service:
	docker compose -f docker-compose.dev.yml restart $(SERVICE)

# Stop and remove all containers, networks, and volumes
docker-clean: docker-dev-clean

# Rebuild and restart (useful after code changes)
docker-rebuild: docker-dev-rebuild

# Execute command in running webserver container
# Usage: make docker-exec CMD="uv run pytest"
docker-exec:
	docker compose -f docker-compose.dev.yml exec dagster-webserver $(CMD)

# Open shell in webserver container
docker-shell:
	docker compose -f docker-compose.dev.yml exec dagster-webserver bash

# Check status of all services
docker-status: docker-dev-status