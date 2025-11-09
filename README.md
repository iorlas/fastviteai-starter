# DeepRock

Content processing pipeline that ingests links from various sources, extracts content, and generates AI-powered summaries.

## Features

- **Link Ingestion**: Process links from manual input or automated monitoring sources
- **RSS Feed Monitoring**: Automatically discover new content from RSS/Atom feeds
- **Content Extraction**: Extract article text from HTML pages and YouTube videos
- **AI Summarization**: Generate concise summaries using OpenRouter LLM models
- **Automated Scheduling**: Background monitoring of RSS feeds every 6 hours
- **Extensible Architecture**: Pluggable watcher protocol for future content sources

## Requirements

- Python 3.12+
- OpenRouter API key
- Docker and Docker Compose (optional, for containerized deployment)

## Installation

### Local Development

```bash
uv sync
```

### Docker Deployment

DeepRock provides two Docker Compose configurations:
- **Development** (`docker-compose.dev.yml`): Hot-reload configuration files via volume mounts
- **Production** (`docker-compose.prod.yml`): Immutable containers with baked-in configuration

#### Prerequisites

```bash
# Create .env file and input files
cp .env.example .env
mkdir -p artifacts/inputs
cp artifacts/inputs/manual_links.txt.template artifacts/inputs/manual_links.txt
cp artifacts/inputs/monitoring_list.txt.template artifacts/inputs/monitoring_list.txt

# Edit .env and configure required variables:
# - OPENAI_API_KEY (required for AI features)
# - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (optional, defaults provided)
```

#### Development Deployment (with config hot-reload)

```bash
# Build and start development services
make docker-dev-build
make docker-dev-up

# Access Dagster UI at http://localhost:3000

# View logs
make docker-dev-logs

# Stop services
make docker-dev-down
```

**Development features:**
- Configuration files (dagster.yaml, workspace.yaml) mounted as volumes
- Changes to config files take effect on container restart (no rebuild needed)
- Same environment as production, but with more flexibility

#### Production Deployment (immutable configuration)

```bash
# Build and start production services
make docker-prod-build
make docker-prod-up

# Access Dagster UI at http://localhost:3000

# View logs
make docker-prod-logs

# Stop services
make docker-prod-down
```

**Production features:**
- Configuration files baked into Docker image
- Fully immutable - config changes require image rebuild
- Better for production deployments where config stability is critical
- Faster startup (no volume mount overhead)

## Usage

### Dagster Pipeline (Link Processing)

#### Local Development

```bash
# Start Dagster development server
uv run dagster dev

# Access Dagster UI at http://localhost:3000
```

#### Docker Deployment

```bash
# Development (with config hot-reload)
make docker-dev-up
make docker-dev-logs

# Production (immutable config)
make docker-prod-up
make docker-prod-logs

# Access Dagster UI at http://localhost:3000

# Backwards compatible commands (default to development)
make docker-up    # Same as docker-dev-up
make docker-logs  # Same as docker-dev-logs
```

**Adding links to process:**

```bash
# Manual links (processed on-demand)
echo "https://example.com/article" >> artifacts/inputs/manual_links.txt

# Monitoring links - supports both direct URLs and RSS feeds
echo "https://news.ycombinator.com/rss" >> artifacts/inputs/monitoring_list.txt
echo "https://example.com/feed.xml" >> artifacts/inputs/monitoring_list.txt

# RSS feeds are automatically detected and processed by RSSWatcher
# Direct article URLs can also be added to monitoring_list.txt
```

**Note:** Create input files from templates if they don't exist:
```bash
mkdir -p artifacts/inputs
cp artifacts/inputs/manual_links.txt.template artifacts/inputs/manual_links.txt
cp artifacts/inputs/monitoring_list.txt.template artifacts/inputs/monitoring_list.txt
```

#### Known Limitations

**YouTube Transcript Extraction:** The YouTube extractor currently does not download actual video transcripts. Instead, it falls back to using the video description for summarization. This is a known limitation in the current implementation.

- **Workaround:** Video descriptions are used for summarization when transcripts are unavailable
- **Future Enhancement:** Full transcript extraction using yt-dlp subtitle download capabilities

If you need actual transcript extraction, the implementation can be found in `dagster_project/ops/youtube_extractor.py` (see `_extract_transcript()` function).

### Other Usage

```bash
# Classify an email via CLI
echo "Your email text here" | uv run python src/cli/classify.py

# Start Streamlit UI
uv run streamlit run src/ui/app.py
```

## Development

### Local Development

```bash
# Run tests
uv run pytest

# Run quality checks
make check

# Pre-commit hooks (managed by prek)
prek install  # If not already installed
```

### Docker Development

```bash
# Run tests inside development container
make docker-exec CMD="uv run pytest"

# Run quality checks inside container
make docker-exec CMD="make check"

# Open shell in container
make docker-shell

# View logs
make docker-dev-logs

# Rebuild and restart services after code changes
make docker-dev-rebuild

# Switch between dev and prod
make docker-dev-down && make docker-prod-up  # Dev → Prod
make docker-prod-down && make docker-dev-up  # Prod → Dev
```

**Notes:**
- **Development deployment** (`docker-compose.dev.yml`): Allows config hot-reload via volume mounts
- **Production deployment** (`docker-compose.prod.yml`): Immutable config baked into image
- Both use production-optimized images with pre-built dependencies
- For hot-reload of source code, use `uv run dagster dev` locally instead of Docker

## Architecture

The project follows a **layered architecture** with clear separation of concerns:

```
dagster_project/
  core/              # Pure business logic (framework-agnostic)
    summarizer.py         # Independent module, could be pip package
    extractors/           # Content extraction modules

  resources/         # Dagster adapters (thin wrappers)
    summary_generator_resource.py  # Wraps core/summarizer

  assets/            # Dagster orchestration
    bronze_links.py        # Link ingestion
    silver_summary_partitioned.py  # Summary generation

  io_managers/       # Data persistence layer
```

**Principle:** Independent modules → Dagster resources → Dagster assets

- **Core modules** are framework-agnostic and testable in isolation
- **Resources** are thin Dagster adapters managing lifecycle
- **Assets** orchestrate the pipeline using resources

## Technical Debt Analysis

*Last updated: 2025-11-03*

### Summary

**Total Issues:** 20
**Critical:** 4 (6 hours to fix)
**High Priority:** 9 (12 hours)
**Medium Priority:** 7 (ongoing)

### ✅ What's Working Well

1. **Architecture** - Clean separation: core → resources → assets
2. **Quality gates** - Prek pre-commit hooks with ruff + ty
3. **Constitution compliance** - Following CLAUDE.md principles
4. **Dependency injection** - Proper inversion of control
5. **Structured logging** - Using structlog throughout

### 🔴 Critical Issues (6 hours)

1. **Missing CI/CD** (2h)
   - No automated testing on PRs
   - Action: Create `.github/workflows/ci.yml`

2. **Test Coverage Gaps** (2h)
   - Missing: `tests/core/test_summarizer.py` (business logic)
   - Missing: `tests/assets/test_bronze_links.py` (orchestration)
   - Current: Only resource + integration tests exist

3. **Missing .env.example** (30min)
   - Environment setup unclear for new developers
   - Action: Document required variables

4. **Unclear ui/ Directory** (30min)
   - Shows as untracked in git
   - Action: Determine status (production/experimental/abandoned)

### 🟠 High Priority (12 hours)

5. **Empty __init__.py Files** (1h)
   - `dagster_project/core/__init__.py` - empty (violates constitution)
   - `dagster_project/core/extractors/__init__.py` - empty
   - Action: Delete per "avoid unless beneficial" rule

6. **No Error Recovery** (3h)
   - Extractors lack retry logic for transient failures
   - Action: Add `tenacity` retry decorators to `html_extractor.py`, `youtube_extractor.py`

7. **Incomplete Type Hints** (2h)
   - Some functions missing return type annotations
   - Action: Add complete type hints, enforce with mypy

8. **Incomplete .gitignore** (15min)
   - Missing: `.pytest_cache/`, `.ruff_cache/`, IDE patterns
   - Action: Add standard Python ignore patterns

9. **No Performance Monitoring** (2h)
   - No timing metrics for API calls
   - No cost tracking for OpenAI usage
   - Action: Add structured logging with duration/token tracking

10. **Missing Development Docs** (2h)
    - No DEVELOPMENT.md guide
    - Action: Document setup, testing, adding new modules

11. **Hardcoded Configuration** (1h)
    - Model name, temperature in code
    - Action: Move to resource configuration

12. **No Rate Limiting** (1h)
    - Risk of hitting API quotas
    - Action: Add rate limiting to OpenAI calls

13. **Test Fixtures Not Shared** (30min)
    - Likely duplication across test files
    - Action: Create `tests/conftest.py` with reusable fixtures

### 🟡 Medium Priority (ongoing)

14. **No Code Coverage Reporting** - Add pytest-cov configuration
15. **No Async/Await** - Consider for batch operations
16. **No Caching Strategy** - Re-extracting same URLs
17. **No Monitoring/Alerting** - Production health checks
18. **No Cost Tracking** - OpenAI usage costs
19. **Magic Numbers** - Extract to named constants
20. **Input Sanitization** - URL validation before processing

### Action Plan

**Week 1: Critical Path** (6 hours)
```bash
# Day 1 - CI/CD (2h)
- Create .github/workflows/ci.yml (run: make check, make test)

# Day 2 - Tests (2h)
- Add tests/core/test_summarizer.py
- Add tests/assets/test_bronze_links.py

# Day 3 - Setup (2h)
- Create .env.example
- Resolve ui/ directory status
- Fix .gitignore
```

**Week 2: High Priority** (8 hours)
```bash
- Delete empty __init__.py files
- Add retry logic to extractors (tenacity)
- Complete type hints
- Add performance monitoring
- Create DEVELOPMENT.md
```

### ROI Analysis

**Investment:** Week 1 = 6 hours
**Returns:**
- Automated quality gates prevent regressions
- Test coverage enables confident refactoring
- Clear onboarding reduces setup time to <1 hour
- Monitoring provides production visibility

**Payback Period:** Immediate (prevents bugs this sprint)

### Success Metrics

After Week 1:
- ✅ Critical debt: 4 → 0
- ✅ Test coverage: ~50% → 80%+
- ✅ CI/CD build success: N/A → 100%
- ✅ Onboarding time: Unknown → <1 hour
