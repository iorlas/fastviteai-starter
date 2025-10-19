# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack web application boilerplate with FastAPI backend (Python 3.12+) and React frontend (TypeScript). Designed for rapid development with quality gates and modern tooling.

```
.
├── backend/        # FastAPI backend
├── frontend/       # React + Vite frontend
├── docs/           # Project documentation
└── docker-compose.yml
```

## Documentation Links

- **[Backend Documentation](backend/README.md)** - Backend tech stack, architecture, setup, testing, API docs
- **[Frontend Documentation](frontend/README.md)** - Frontend tech stack, architecture, routing, forms, testing
- **[Backend Gotchas](backend/docs/gotchas.md)** - Common backend pitfalls and best practices (IMPORTANT: read before implementing features)
- **[Frontend Gotchas](frontend/docs/gotchas.md)** - Common frontend pitfalls and best practices (IMPORTANT: read before implementing features)
- **[Root README](README.md)** - Project overview and quick start

## Commands

### Self-Documenting Makefiles

Each directory has a self-documenting Makefile. **See Makefiles for all available commands:**

- **Root**: [Makefile](Makefile) - Run `make help` to see Docker Compose and global commands
- **Backend**: [backend/Makefile](backend/Makefile) - Run `make help` to see Python/FastAPI commands
- **Frontend**: [frontend/Makefile](frontend/Makefile) - Run `make help` to see React/TypeScript commands

### Quick Command Reference

```bash
# Root (Docker Compose)
make bootstrap        # Bootstrap project for first-time setup
make dev              # Start all services (build + remove orphans)
make db               # Start database only (for local development)
make down             # Stop all services
make check            # Run pre-commit hooks on all files

# Backend
cd backend
make bootstrap        # Bootstrap backend (install deps, create .env)
make dev              # Start uvicorn server with hot reload
make check            # Format + lint with auto-fix + type check
make test             # Run tests with coverage
make migrate          # Apply database migrations
make migrate-create MSG="description"  # Create new migration

# Frontend
cd frontend
make bootstrap        # Bootstrap frontend (install deps, create .env, codegen)
make dev              # Start Vite dev server
make check            # Format + lint with auto-fix
make test             # Run tests with coverage
make codegen          # Generate API client from OpenAPI
```

**Note**: Frontend commands work with both `make <cmd>` and `pnpm <cmd>`.

### Pre-commit Hooks

Pre-commit hooks using `prek` (fast Rust-based tool) run automatically before commits. **Never bypass** (`--no-verify`) unless emergency.

**One-time setup:**
```bash
uv tool install prek
prek install
```

## Architecture

### Backend Architecture: Repository → Service → Router

Feature-based organization with clear separation of concerns. Each feature in `backend/app/features/` follows Repository (data) → Service (logic) → Router (HTTP) pattern.

```
features/
└── feature_name/
    ├── models.py         # SQLAlchemy ORM models
    ├── schemas.py        # Pydantic request/response DTOs
    ├── repository.py     # Data access (extends BaseRepository[T])
    ├── service.py        # Business logic (uses repository)
    ├── router.py         # FastAPI endpoints (uses service via DI)
    └── test_service.py   # Unit tests
```

**Key Principles:**
1. **Repository Layer** (`repository.py`): All database operations. Extends `BaseRepository[T]` from `app/core/repository.py`.
2. **Service Layer** (`service.py`): Business logic only. NO direct database access - uses repository.
3. **Router Layer** (`router.py`): HTTP endpoints only. NO business logic - delegates to service via dependency injection.
4. **Models vs Schemas**: Models are SQLAlchemy (database), Schemas are Pydantic (API contracts).

**Anti-patterns to avoid:**
- ❌ Router accessing database directly → Use service
- ❌ Business logic in repository → Keep in service
- ❌ Service containing FastAPI dependencies → Keep framework-agnostic

**See [backend/README.md](backend/README.md) for detailed backend architecture documentation.**

### Frontend Architecture: Feature-Based Components

Feature-based folder organization for scalability. Components organized by domain rather than by type.

```
src/
├── lib/
│   └── api/          # API client, Axios config, generated types (Orval)
├── features/         # Domain-specific components (e.g., auth/, todos/)
├── components/       # Shared UI components (generic, reusable)
├── routes/           # TanStack Router route definitions
└── tests/
    ├── setup.ts      # Vitest and Testing Library config
    └── mocks/        # MSW (Mock Service Worker) API mocks
```

**Guidelines:**
- `lib/api/`: API client configuration and generated types from OpenAPI
- `features/`: Domain-specific logic organized by feature
- `components/`: Generic, reusable UI components
- `routes/`: File-based routing with TanStack Router

**API Client Generation:**
- Uses Orval to generate TypeScript + TanStack Query hooks from FastAPI OpenAPI spec
- Configuration: `orval.config.ts`
- Reads from: `http://localhost:8000/openapi.json` (or `VITE_API_URL`)
- Outputs to: `src/lib/api/generated/`
- Run `make codegen` after backend API changes

**See [frontend/README.md](frontend/README.md) for detailed frontend architecture documentation.**

## Technology Stack

**Backend:**
- Framework: FastAPI
- Database: PostgreSQL 17 + SQLAlchemy (async) + asyncpg
- Migrations: Alembic
- Validation: Pydantic v2
- Package Manager: uv (Astral)
- Linting: Ruff
- Type Checking: ty (Astral)
- Logging: structlog

**Frontend:**
- Framework: React 19
- Build Tool: Vite
- Routing: TanStack Router
- State/Data Fetching: TanStack Query
- Forms: React Hook Form + Zod
- Styling: Tailwind CSS v4 (@tailwindcss/vite)
- Package Manager: pnpm
- Linting/Formatting: Biome
- Testing: Vitest + Testing Library
- API Mocking: MSW (Mock Service Worker)
- API Codegen: Orval

**Infrastructure:**
- Containerization: Docker + Docker Compose
- Dev Container: Node 22 + Python 3.12 + Claude Code CLI

**See app-specific documentation for detailed tech stack information:**
- [backend/README.md#technology-stack](backend/README.md#technology-stack)
- [frontend/README.md#technology-stack](frontend/README.md#technology-stack)

## Database Migrations

Backend uses Alembic for schema migrations.

**Migration workflow:**
1. Modify SQLAlchemy models in `app/features/*/models.py`
2. Generate migration: `make migrate-create MSG="description"`
3. Review generated migration in `alembic/versions/`
4. Apply: `make migrate`
5. Rollback if needed: `make migrate-down`

**Important**: Alembic uses sync driver (psycopg) for migrations, async (asyncpg) for application.

**See [backend/README.md#database-migrations](backend/README.md#database-migrations) for detailed migration documentation.**

## Environment Configuration

Both frontend and backend use environment variables (12-factor app principles).

**Backend:** `backend/.env` (create from `backend/.env.example`)
- `ENVIRONMENT`: Application environment (`development` = colorful logs, `production` = JSON logs)
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`, `JWT_SECRET`: Security keys (MUST change in production)
- `CORS_ORIGINS`: Allowed frontend origins
- `LOG_LEVEL`: Logging level

**Frontend:** `frontend/.env` (create from `frontend/.env.example`)
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

**See app-specific documentation for detailed configuration:**
- [backend/README.md#configuration](backend/README.md#configuration)
- [frontend/README.md#configuration](frontend/README.md#configuration)

## Testing

**Backend:**
- Unit tests: Co-located with features (`app/features/*/test_service.py`)
- Integration tests: `tests/integration/`
- Run: `make test` (includes coverage)
- Uses testcontainers for PostgreSQL in integration tests

**Frontend:**
- Component tests: Co-located with components (`*.test.tsx`)
- Integration tests: `src/tests/integration/`
- Run: `make test` (includes coverage)
- API mocking: MSW (Mock Service Worker)

**See app-specific documentation for detailed testing guides:**
- [backend/README.md#testing](backend/README.md#testing)
- [frontend/README.md#testing](frontend/README.md#testing)

## API Documentation

FastAPI auto-generates OpenAPI documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

API versioning: All endpoints under `/api/v1` prefix (configurable in `app.core.settings`)

**See [backend/README.md#api-documentation](backend/README.md#api-documentation) for more details.**

## Development Workflow

**First-time setup:** Run `make bootstrap` to set up the project (installs dependencies, creates `.env` files, sets up database and migrations).

1. **Start services:** `make dev` (Docker) OR run backend/frontend separately (see Quick Start)
2. **Backend changes:**
   - Modify code in `backend/app/`
   - Run quality checks: `make check`
   - Run tests: `make test`
   - If models changed: `make migrate-create MSG="description"` then `make migrate`
3. **Frontend changes:**
   - Modify code in `frontend/src/`
   - If API changed: `make codegen` to regenerate client
   - Run quality checks: `make check`
   - Run tests: `make test`
4. **Before committing:** Pre-commit hooks run automatically (prek)
