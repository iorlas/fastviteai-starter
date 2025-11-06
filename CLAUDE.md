# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Constitution (Non-Negotiable Rules)

### Python Standards
- **No docstrings** at this stage
- **Avoid `__init__.py`** unless demonstrably beneficial
- **Integration tests only** - structure tests to mirror source: `tests/{module}/test_{file}.py`
- **Pydantic V2** (latest version only) - never dataclasses
- **No ad-hoc Python execution** - use tests instead
- **Run `make check`** after every significant change; ask before ignoring rules
- **Use context7** for planning, analysis, and troubleshooting
- **Use structlog** instead of print - minimize verbosity
- **Idiomatic Python only** - ask before diverging
- **All imports at top** - no inline imports
- **"Divide and conquer"** - components with concentrated logic + orchestrator, but not enterprise-scale
- **Happy paths first** - fail fast, fail early; ask before handling edge cases

## Commands

### Development Workflow
```bash
# Initial setup
make init              # Create venv, sync dependencies, install prek hooks

# Quality checks (run after every significant change)
make check             # Runs format, lint, typecheck, test
make format            # Format with ruff
make lint              # Lint with ruff --fix
make typecheck         # Type check with ty
make test              # Run pytest

# Run single test
uv run pytest tests/path/to/test_file.py::test_function_name

# Run test markers
uv run pytest -m integration   # Integration tests only
uv run pytest -m unit          # Unit tests only
uv run pytest -m contract      # Contract tests (external API verification)
```

### Dagster Pipeline
```bash
# Start Dagster development server
uv run dagster dev             # UI at http://localhost:3000

# Add links to process
echo "https://example.com" >> manual_links.txt     # Manual processing
echo "https://news.site/rss" >> monitoring_list.txt # Monitoring (RSS/direct URLs)

# Create input files from templates if missing
cp manual_links.txt.template manual_links.txt
cp monitoring_list.txt.template monitoring_list.txt
```

### Environment Setup
Required `.env` variables (see `.env.example`):
```bash
PROJECT_ROOT=/absolute/path/to/ailabbrains
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o
DAGSTER_HOME=/path/to/ailabbrains/.dagster
```

## Architecture

### Medallion Data Architecture
The pipeline uses a **medallion architecture** (Bronze → Silver → Gold) with immutable bronze layer:

```
artifacts/
  bronze/                    # Raw, immutable data (never modified/deleted)
    raw_html/{url_hash}.json      # Downloaded HTML content
    raw_youtube/{url_hash}.json   # YouTube video metadata
    discussions/{url_hash}.json   # HN/Reddit comments
  silver/                    # Cleaned, transformed data (can be regenerated)
    extracted_content/{url_hash}.json  # Extracted text/metadata
    summaries/{url_hash}.json          # AI-generated summaries
    discussions/{url_hash}.json        # Processed discussion threads
```

**Key principle**: Bronze layer is append-only cache. Silver layer can be deleted and regenerated.

### Layered Architecture Pattern
Clean separation of concerns following **framework-agnostic core**:

```
dagster_project/
  core/                      # Pure business logic (framework-agnostic, could be pip package)
    summarizer.py                 # Summary generation logic
    content_extractor.py          # Content extraction orchestration
    downloader.py                 # HTTP download with caching
    extractors/
      html_extractor.py           # HTML content extraction
      youtube_extractor.py        # YouTube content extraction
      watchers.py                 # RSS/feed monitoring
    aggregators/                  # Content aggregator interfaces (HN, Lobsters)
      base.py                     # Aggregator protocol
      hackernews.py               # HackerNews client
      detector.py                 # Detect if URL is aggregator
    discussions/                  # Discussion thread processing
      hn_client.py                # HN API client
      comment_processor.py        # Comment thread flattening
    cache/                        # HTTP caching layer
      http_cache.py               # Cache-aware HTTP client

  resources/                 # Dagster adapters (thin wrappers managing lifecycle)
    summary_generator_resource.py  # Wraps core/summarizer
    bronze_io_manager.py           # Bronze layer I/O (immutable)
    silver_io_manager.py           # Silver layer I/O (mutable)
    openai.py                      # OpenAI/OpenRouter client wrapper

  assets/                    # Dagster orchestration (DAG definition)
    discovered_urls.py             # Entry point: read input files, detect aggregators
    bronze_raw_html.py             # Download HTML content
    bronze_discussions.py          # Fetch discussion threads
    silver_extracted_content.py    # Extract text from HTML/YouTube
    silver_discussions.py          # Process comment threads
    silver_summary.py              # Generate AI summaries

  jobs/                      # Pipeline definitions
    pipelines.py                   # manual_urls_pipeline, watchers_pipeline

  schedules/                 # Automated scheduling
    monitoring_schedule.py         # Run watchers_pipeline every 6 hours

  utils/                     # Shared utilities
    paths.py                       # Centralized path constants
    url_utils.py                   # URL normalization
    content_type.py                # ContentType enum (HTML/YouTube detection)
```

**Dependency flow**: `core` (pure logic) → `resources` (Dagster adapters) → `assets` (orchestration)

### Pipeline Flow
Two pipelines process content differently:

1. **manual_urls_pipeline** (on-demand):
   - Reads `manual_links.txt`
   - Processes URLs immediately
   - Triggered manually via Dagster UI

2. **watchers_pipeline** (automated):
   - Reads `monitoring_list.txt`
   - Auto-detects RSS feeds vs direct URLs
   - Runs every 6 hours via schedule
   - RSS feeds: RSSWatcher expands to article URLs
   - Aggregators (HN/Lobsters): Fetches discussions, extracts linked URLs

**Asset DAG**:
```
discovered_urls
    ├─> bronze_raw_html ──> silver_extracted_content ─┐
    └─> bronze_discussions ─> silver_discussions ──────┤
                                                        ├─> silver_summary
                                                        ┘
```

**Data flow**:
- `discovered_urls`: Detects content type (HTML/YouTube), aggregators, normalizes URLs
- Bronze assets: Download raw content (HTML, YouTube metadata, discussion threads)
- Silver extraction: Extract clean text/metadata
- Silver summary: Generate AI summaries using extracted content + discussions

### Key Architectural Principles
1. **Immutable bronze layer**: Never modify/delete; acts as source-of-truth cache
2. **Regenerable silver layer**: Can delete and re-process from bronze
3. **URL hash partitioning**: All artifacts stored by `sha256(url)` for deduplication
4. **Fan-out pattern**: `discovered_urls` fans out to multiple bronze assets (HTML, YouTube, discussions)
5. **Content type detection**: `ContentType.HTML` vs `ContentType.YOUTUBE` determines processing path
6. **Aggregator expansion**: URLs to HN/Lobsters fetch discussions + expand to linked articles
7. **Caching at every layer**: Bronze caching (immutable), HTTP caching (core/cache/), silver caching (regenerable)

## Testing Structure
```
tests/
  core/                      # Tests for core business logic
    extractors/
      test_html_extractor.py
      test_youtube_extractor.py
  discussions/
    test_hn_client.py
    test_comment_processor.py
  integration/               # End-to-end integration tests
    test_bronze_fan_out.py       # Test URL discovery → bronze fan-out
  assets/                    # Tests for Dagster assets
  fixtures/                  # Shared test data
  utils/                     # Utility tests
```

**Test markers**:
- `@pytest.mark.integration` - Integration tests (may hit external APIs in controlled manner)
- `@pytest.mark.unit` - Pure unit tests
- `@pytest.mark.contract` - External API contract verification

## Known Limitations
- **YouTube transcripts**: Currently uses video description instead of actual transcripts. Transcript extraction is stubbed in `core/extractors/youtube_extractor.py:_extract_transcript()`

## Experiments Directory
`experiments/v3/` contains prompt engineering experiments:
- `run.py` - Test different LLM models/prompts for summarization
- `test_cases/` - Sample articles with expected summaries
- `runs/` - Experiment results (JSON)
- Separate from main pipeline; used for prompt iteration

## Data Persistence
- **Bronze/Silver artifacts**: `artifacts/{bronze,silver}/` (git-ignored)
- **Input files**: `manual_links.txt`, `monitoring_list.txt` (use `.template` versions as reference)
- **Dagster metadata**: `.dagster/` directory (configured via `DAGSTER_HOME`)

## Tool Configuration
- **Ruff**: Line length 140, Python 3.12+ target
- **Pytest**: Configured for `tests/` directory with custom markers
- **Ty (type checker)**: Python 3.12, strict type safety rules
- **Prek**: Pre-commit hooks for ruff + ty
