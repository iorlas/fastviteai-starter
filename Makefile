.PHONY: check format lint typecheck test init
.PHONY: process-manual process-monitoring stats clean-cache
.PHONY: help

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
# Pipeline Commands
# ============================================

process-manual:  ## Process URLs from manual_links.txt
	uv run ailabbrains process --source manual

process-monitoring:  ## Process URLs from monitoring_list.txt
	uv run ailabbrains process --source monitoring

stats:  ## Show artifact statistics
	uv run ailabbrains stats

clean-cache:  ## Clean HTTP cache
	uv run ailabbrains clean-cache --layer http

clean-bronze:  ## Clean bronze layer
	uv run ailabbrains clean-cache --layer bronze

clean-silver:  ## Clean silver layer
	uv run ailabbrains clean-cache --layer silver

clean-all:  ## Clean all caches and layers
	uv run ailabbrains clean-cache --layer all

# ============================================
# Help Command
# ============================================

help:  ## Show this help message
	@echo "AI Lab Brains - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make init              - Initialize project (create venv, install deps)"
	@echo "  make check             - Run all checks (format, lint, typecheck, test)"
	@echo "  make format            - Format code with ruff"
	@echo "  make lint              - Lint code with ruff"
	@echo "  make typecheck         - Type check with ty"
	@echo "  make test              - Run pytest"
	@echo ""
	@echo "Pipeline:"
	@echo "  make process-manual    - Process URLs from manual_links.txt"
	@echo "  make process-monitoring - Process URLs from monitoring_list.txt"
	@echo "  make stats             - Show artifact statistics"
	@echo ""
	@echo "Cache Management:"
	@echo "  make clean-cache       - Clean HTTP cache only"
	@echo "  make clean-bronze      - Clean bronze layer"
	@echo "  make clean-silver      - Clean silver layer"
	@echo "  make clean-all         - Clean all caches and layers"