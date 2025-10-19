# Backend (FastAPI + PostgreSQL)

Python backend API built with FastAPI, PostgreSQL, and modern development tooling.

## Commands

**See [Makefile](Makefile) for all available commands.** Run `make` or `make help` to see the full list.

Quick reference:
- `make install` - Install dependencies
- `make dev` - Start development server with hot reload
- `make check` - Format, lint with auto-fix, and type check
- `make test` - Run tests with coverage

## Technology Stack

### Core
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern async web framework
- **Database**: [PostgreSQL 17](https://www.postgresql.org/) - Production database
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) (async) - Database toolkit and ORM
- **Driver**: asyncpg (runtime), psycopg (migrations)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/) - Database schema migrations

### Development Tools
- **Package Manager**: [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- **Linting**: [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter and formatter
- **Type Checking**: [ty](https://github.com/astral-sh/ty) - Fast type checker
- **Testing**: [pytest](https://pytest.org/) - Testing framework
- **Logging**: [structlog](https://www.structlog.org/) - Structured logging

### Libraries
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/) - Data validation using Python type hints
- **Authentication**: JWT-based authentication
- **CORS**: FastAPI CORS middleware

## Architecture: Repository → Service → Router

Feature-based organization with clear separation of concerns. Each feature in `app/features/` follows this pattern:

```
features/
└── feature_name/
    ├── models.py         # SQLAlchemy ORM models (database layer)
    ├── schemas.py        # Pydantic request/response DTOs (API contracts)
    ├── repository.py     # Data access (extends BaseRepository[T])
    ├── service.py        # Business logic (uses repository)
    ├── router.py         # FastAPI endpoints (uses service via DI)
    └── test_service.py   # Unit tests
```

### Layers

1. **Repository Layer** (`repository.py`): All database operations. Extends `BaseRepository[T]` from `app/core/repository.py` for CRUD operations.
2. **Service Layer** (`service.py`): Business logic only. NO direct database access - uses repository.
3. **Router Layer** (`router.py`): HTTP endpoints only. NO business logic - delegates to service via dependency injection.

### Core Modules (`app/core/`)

- `database.py`: Async SQLAlchemy setup, `get_db()` dependency
- `repository.py`: Generic `BaseRepository[T]` with CRUD operations
- `settings.py`: Pydantic settings (env vars, 12-factor config)
- `exceptions.py`: Custom exceptions (NotFoundError, ForbiddenError, ValidationError)
- `middleware.py`: Request ID middleware for tracing

### Anti-patterns to Avoid

- ❌ Router accessing database directly → Use service
- ❌ Business logic in repository → Keep in service
- ❌ Service containing FastAPI dependencies → Keep framework-agnostic
- ❌ Models and schemas confused → Models are SQLAlchemy (DB), Schemas are Pydantic (API)

### Example Feature

See `app/features/health/` - Health check endpoints with database connectivity test.

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 17 (or use Docker Compose from root)
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
make install

# Or manually
uv sync
```

### Configuration

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Environment variables:

- `ENVIRONMENT`: Application environment (`development` = colorful logs, `production` = JSON logs)
- `DATABASE_URL`: PostgreSQL connection string (async driver)
- `SECRET_KEY`: Application secret key (MUST change in production)
- `JWT_SECRET`: JWT signing secret (MUST change in production)
- `CORS_ORIGINS`: Allowed frontend origins (comma-separated)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Development

```bash
# Start development server with hot reload
make dev

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Database Migrations

Uses Alembic for schema migrations. Configuration in `alembic.ini` and `alembic/env.py`.

### Create Migration

```bash
make migrate-create MSG="add user table"

# Or manually
uv run alembic revision --autogenerate -m "add user table"
```

### Apply Migrations

```bash
make migrate

# Or manually
uv run alembic upgrade head
```

### Rollback Migration

```bash
make migrate-down

# Or manually
uv run alembic downgrade -1
```

### Migration Workflow

1. Modify SQLAlchemy models in `app/features/*/models.py`
2. Generate migration: `make migrate-create MSG="description"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `make migrate`
5. Rollback if needed: `make migrate-down`

**Important**: Alembic uses sync driver (psycopg) for migrations, while the application uses async driver (asyncpg) at runtime. The `Settings.database_url_sync` property handles this conversion.

## Testing

### Run Tests

```bash
make test

# Or manually
uv run pytest --cov=app --cov-report=term-missing
```

### Test Organization

- **Unit tests**: Co-located with features (`app/features/*/test_service.py`)
- **Integration tests**: `tests/integration/`
- **Fixtures**: `tests/conftest.py`
- **Factories**: `tests/factories/` (test data generation)

### Test Database

Integration tests use testcontainers to spin up temporary PostgreSQL instances. No need to manage test databases manually.

### Parallel Execution

```bash
# Run tests in parallel (faster)
uv run pytest -n auto
```

## API Documentation

FastAPI auto-generates OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

All endpoints are under `/api/v1` prefix (configurable in `app.core.settings`).

## Code Quality

### Format, Lint, and Type Check

```bash
make check

# Runs:
# 1. ruff format . (formatting)
# 2. ruff check --fix . (linting with auto-fix)
# 3. ty check . (type checking)
```

Configuration in `pyproject.toml` under `[tool.ruff]` and `[tool.ty]`.

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before commits. See [root README](../README.md#pre-commit-hooks) for setup.

## Logging

Uses structlog for structured, parsable logging.

- **Development** (`ENVIRONMENT=development`): Colorful, human-readable console logs
- **Production** (`ENVIRONMENT=production`): JSON logs for log aggregation systems

Log levels configurable via `LOG_LEVEL` environment variable.

## Related Documentation

- [Frontend Documentation](../frontend/README.md) - React frontend
- [Root README](../README.md) - Project overview and quick start
- [CLAUDE.md](../CLAUDE.md) - AI assistant guide
- [Backend Gotchas](docs/gotchas.md) - Common backend pitfalls and best practices (IMPORTANT: read before implementing features)
- [Makefile](Makefile) - All available commands
