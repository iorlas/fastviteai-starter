# AI Starter

Full-stack web application boilerplate with FastAPI backend and React frontend, designed for rapid development with built-in quality gates.

## Documentation

- **[Backend Documentation](backend/README.md)** - FastAPI backend (Python, PostgreSQL)
- **[Frontend Documentation](frontend/README.md)** - React frontend (TypeScript, Vite)
- **[AI Assistant Guide (CLAUDE.md)](CLAUDE.md)** - Guide for Claude Code

## First-Time Setup

Bootstrap the project (one-time setup):

```bash
make bootstrap
```

This will:
- Install pre-commit hooks (prek)
- Bootstrap backend (install deps, create `.env`)
- Start PostgreSQL database
- Run database migrations
- Bootstrap frontend (install deps, create `.env`)

**Individual bootstrap**: You can also bootstrap backend or frontend separately:
```bash
cd backend && make bootstrap  # Backend only
cd frontend && make bootstrap # Frontend only
```

**Note**: The API client is pre-generated and committed to the repo. After backend API changes, regenerate it with `cd frontend && make codegen`.

## Quick Start

Start all services with Docker Compose:

```bash
make dev
```

Or for local development without Docker:

```bash
# Terminal 1: Start database only
make db

# Terminal 2: Start backend
cd backend && make dev

# Terminal 3: Start frontend
cd frontend && make dev
```

**See available commands**: Run `make` in any directory (root, backend, or frontend) to see all available commands.

## Pre-commit Hooks

This project uses [prek](https://github.com/astral-sh/prek), a fast Rust-based pre-commit tool.

Pre-commit hooks are automatically installed when you run `make bootstrap`. They run on every commit and enforce code quality standards. **Never bypass** (`--no-verify`).

## License

MIT
