# AI Starter

Full-stack web application boilerplate with FastAPI backend and React frontend, designed for rapid development with built-in quality gates.

## Documentation

- **[Backend Documentation](backend/README.md)** - FastAPI backend (Python, PostgreSQL)
- **[Frontend Documentation](frontend/README.md)** - React frontend (TypeScript, Vite)
- **[AI Assistant Guide (CLAUDE.md)](CLAUDE.md)** - Guide for Claude Code

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

**One-time setup**:

```bash
# Install prek globally
uv tool install prek

# Install hooks
prek install
```

Pre-commit hooks run automatically on every commit and enforce code quality standards. **Never bypass** (`--no-verify`).

## License

MIT
