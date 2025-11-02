# Development Guide - DeepRock

**Project:** deeprock
**Type:** Data Pipeline (Dagster ETL)
**Generated:** 2025-11-02

---

## Prerequisites

- **Python:** 3.12 or higher
- **Package Manager:** uv (fast Python package manager)
- **API Access:** OpenRouter API key

---

## Initial Setup

### 1. Install Dependencies

```bash
# Sync all dependencies using uv
uv sync
```

**Alternative** (full initialization with venv):
```bash
make init
```

This will:
- Create virtual environment (uv venv)
- Install all dependencies (uv sync)
- Run pre-commit setup (uvx prek)

### 2. Environment Configuration

**Create `.env` file from template:**

```bash
cp .env.example .env
```

**Configure environment variables:**

```env
# OpenAI Configuration (via OpenRouter)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o

# Dagster Configuration
DAGSTER_HOME=/path/to/project/.dagster
```

### 3. Create Input Files

```bash
# Create input files from templates (if they don't exist)
cp manual_links.txt.template manual_links.txt
cp monitoring_list.txt.template monitoring_list.txt
```

---

## Running the Application

### Dagster Pipeline

**Start Dagster development server:**

```bash
uv run dagster dev
```

**Access Dagster UI:**
- URL: http://localhost:3000
- View assets, jobs, schedules, and runs
- Manually trigger pipeline executions

### Processing Links

**Manual Link Processing:**

```bash
# Add article URLs to manual input file
echo "https://example.com/article" >> manual_links.txt

# Process via Dagster UI (run manual_pipeline job)
```

**Automated Monitoring:**

```bash
# Add RSS feeds or direct URLs to monitoring file
echo "https://news.ycombinator.com/rss" >> monitoring_list.txt
echo "https://example.com/feed.xml" >> monitoring_list.txt

# Monitoring job runs automatically every 6 hours
# Can also be triggered manually via Dagster UI
```

**How it works:**
- RSS feeds are auto-detected and processed by RSSWatcher
- Direct article URLs can also be added to monitoring_list.txt
- Deduplication happens automatically (checks artifacts/summaries/)

---

## Development Workflow

### Quality Checks

**Run all checks (recommended before commits):**

```bash
make check
```

This runs:
1. Code formatting (ruff format)
2. Linting (ruff check --fix)
3. Type checking (ty check)
4. Tests (pytest)

### Individual Commands

**Format code:**
```bash
make format
# or
uv run ruff format .
```

**Lint code:**
```bash
make lint
# or
uv run ruff check . --fix
```

**Type check:**
```bash
make typecheck
# or
uv run uvx ty check .
```

**Run tests:**
```bash
make test
# or
uv run pytest
```

---

## Testing

### Test Structure

```
tests/
├── integration/              # End-to-end pipeline tests
│   ├── test_jobs.py
│   └── test_pipeline_integration.py
├── fixtures/                 # Test data and fixtures
├── test_storage.py           # Storage layer tests
├── test_html_extractor.py    # HTML extraction tests
├── test_youtube_extractor.py # YouTube extraction tests
├── test_link_ingestion.py    # Link ingestion tests
├── test_environment.py       # Environment tests
└── test_openai.py            # OpenAI integration tests
```

### Running Tests

**All tests:**
```bash
uv run pytest
```

**Specific test file:**
```bash
uv run pytest tests/test_html_extractor.py
```

**Integration tests only:**
```bash
uv run pytest tests/integration/
```

**With verbose output:**
```bash
uv run pytest -v
```

**Test markers:**
```bash
# Unit tests
uv run pytest -m unit

# Integration tests
uv run pytest -m integration

# Contract tests (external API verification)
uv run pytest -m contract
```

### Test Configuration

**Pytest settings** (from pyproject.toml):
- Test paths: `tests/`
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Options: `-v --strict-markers`

---

## Project Structure

```
deeprock/
├── dagster_project/          # Main pipeline code
│   ├── definitions.py        # [ENTRY POINT] Dagster definitions
│   ├── assets/               # ETL assets
│   ├── jobs/                 # Pipeline jobs
│   ├── schedules/            # Automated schedules
│   ├── ops/                  # Reusable operations
│   └── resources/            # External integrations
├── tests/                    # Test suite
├── artifacts/                # Pipeline outputs
│   ├── html/                 # Extracted HTML
│   ├── videos/               # Video transcripts
│   └── summaries/            # LLM summaries
├── docs/                     # Documentation
├── pyproject.toml            # Project configuration
├── Makefile                  # Development commands
└── .env                      # Environment config
```

---

## Common Development Tasks

### Adding a New Extractor

1. Create new op in `dagster_project/ops/`
2. Implement extraction logic
3. Add tests in `tests/test_<extractor>.py`
4. Import in `dagster_project/ops/__init__.py`
5. Use in content_extraction asset

### Adding a New Watcher

1. Implement Watcher protocol in `dagster_project/ops/watchers.py`
2. Add watcher logic (e.g., RedditWatcher, TwitterWatcher)
3. Add tests in `tests/test_watchers.py`
4. Integrate in link_ingestion asset

### Debugging Pipeline Runs

1. Check Dagster UI: http://localhost:3000
2. View run logs in UI under "Runs" tab
3. Check artifact outputs in `artifacts/` directory
4. Review error summaries in `artifacts/summaries/` (failed runs)

---

## Code Style and Conventions

### Linting: Ruff

**Configured rules:**
- E: Pycodestyle errors
- F: Pyflakes
- I: Import sorting
- N: Naming conventions
- W: Warnings
- UP: Pyupgrade

**Line length:** 100 characters

### Type Checking: ty

**Python version:** 3.12
**Virtual env:** `./.venv`

**Error-level rules:**
- possibly-unresolved-reference
- invalid-argument-type
- missing-argument
- unsupported-operator
- division-by-zero

**Warning-level rules:**
- unused-ignore-comment
- redundant-cast

---

## Troubleshooting

### YouTube Transcript Limitation

**Known Issue:** YouTube extractor does not download actual transcripts

**Current Behavior:**
- Falls back to using video description
- Video descriptions are used for summarization

**Workaround:**
- This is by design in current implementation
- See `dagster_project/ops/youtube_extractor.py` (`_extract_transcript()`)

**Future Enhancement:**
- Full transcript extraction using yt-dlp subtitle capabilities

### API Key Issues

**Error:** `AuthenticationError` or `Invalid API key`

**Solution:**
1. Check `.env` file exists and has correct API key
2. Verify `OPENAI_API_KEY` is set
3. Ensure `OPENAI_BASE_URL` points to OpenRouter
4. Restart Dagster dev server after changing .env

### Dagster UI Not Loading

**Error:** Cannot access http://localhost:3000

**Solution:**
1. Check Dagster dev server is running: `uv run dagster dev`
2. Check for port conflicts (another service on :3000)
3. Try alternative port: `uv run dagster dev -p 3001`

---

## Additional Resources

- **Dagster Documentation:** https://docs.dagster.io
- **Project README:** /README.md
- **Technical Specification:** /docs/tech-spec.md
- **Epic Breakdown:** /docs/epics.md
- **Source Tree Analysis:** /docs/source-tree-analysis.md
