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
- **Async-first HTTP** - all HTTP operations use AsyncCacheClient with native async/await (no sync clients)

### Async/Await Pattern
**All HTTP operations are async** to leverage Python's native async/await support:

```python
# ✅ Correct - async function with await
async def my_function():
    downloader = HTTPDownloader()
    result = await downloader.download(url)  # await async operations
    return result

# ❌ Wrong - don't use asyncio.run() wrappers in async contexts
async def my_function():
    result = asyncio.run(some_async_function())  # avoid this pattern
    return result
```

**Why async-first:**
- Simpler code - no `asyncio.run()` wrappers needed
- Better concurrency for HTTP operations
- Unified HTTP client API - single `AsyncCacheClient` instead of dual sync/async
- Future-proof for concurrent operations

**Testing async code:**
- Use `@pytest.mark.asyncio` for async tests
- Mock async methods with `AsyncMock` (not `MagicMock`)
- All HTTP cache tests use `get_async_cache_client()`

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

### Pipeline Execution
```bash
# Process URLs from manual input file
make process-manual           # Reads artifacts/inputs/manual_links.txt
uv run ailabbrains process --source manual

# Process URLs from monitoring list
make process-monitoring       # Reads artifacts/inputs/monitoring_list.txt
uv run ailabbrains process --source monitoring

# View statistics
make stats
uv run ailabbrains stats

# Create input files from templates if missing
cp artifacts/inputs/manual_links.txt.template artifacts/inputs/manual_links.txt
cp artifacts/inputs/monitoring_list.txt.template artifacts/inputs/monitoring_list.txt
```

### Cache Management
```bash
# Clean different cache layers
make clean-cache      # Clean HTTP cache only
make clean-bronze     # Clean bronze layer (immutable data)
make clean-silver     # Clean silver layer (regenerable summaries)
make clean-all        # Clean all caches and layers

# Or use CLI directly
uv run ailabbrains clean-cache --layer http
uv run ailabbrains clean-cache --layer bronze
uv run ailabbrains clean-cache --layer silver
uv run ailabbrains clean-cache --layer all
```

### Environment Setup
All configuration is managed via **pydantic-settings** in `ailabbrains/config.py`.

Required `.env` variables (see `.env.example`):
```bash
# Artifacts
ARTIFACTS_PATH=artifacts  # Directory for all persistent data (inputs, bronze, silver, cache)

# OpenAI/OpenRouter
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o

# Feature Flags
ENABLE_SUMMARIZATION=true  # Set to 'false' to disable AI summarization

# Network
HTTP_PROXY=  # Optional: http://proxy:port or socks5://proxy:port for all HTTP operations

# Whisper Transcription
WHISPER_MODEL=large-v3  # Model size: tiny, base, small, medium, large-v2, large-v3, distil-large-v3
WHISPER_DEVICE=cpu  # Device: cpu, cuda, or mps (for Mac M1/M2)
WHISPER_CACHE_DIR=artifacts/cache/whisper_models  # Persistent model cache
```

**ARTIFACTS_PATH Structure:**
```
artifacts/
  inputs/
    manual_links.txt      # Manual URL submissions
    monitoring_list.txt   # RSS feeds and monitoring sources
  bronze/
    html/                 # Extracted HTML content
    youtube_downloads/    # YouTube metadata and transcripts
    discussions/          # Discussion threads
  silver/
    article_summaries/    # Stage 1: Article-only AI analysis
    discussion_summaries/ # Stage 2: Per-discussion AI analysis
    summaries/            # Stage 3: Final synthesis
  cache/
    http_responses/       # HTTP cache database
    whisper_models/       # Whisper model files
    openai_structured_outputs/ # OpenAI response cache
```

**Usage**: Import settings from the global config:
```python
from ailabbrains.config import settings

# Access configuration
if settings.enable_summarization:
    model = settings.openai_model

# Access paths
from ailabbrains.utils.paths import ARTIFACTS_PATH, MANUAL_LINKS_FILE
```

## Architecture

### Simplified CLI Architecture
The pipeline uses a **single-orchestrator design** with Typer CLI and Rich progress bars:

```
ailabbrains/
  cli.py                    # Typer CLI entry point
  orchestrator.py           # Main pipeline orchestration
  storage.py                # Simplified I/O functions (BronzeTable, SilverTable enums)
  core/                     # Pure business logic (framework-agnostic)
  utils/                    # Shared utilities (paths, url_utils, asset_utils)
  config.py                 # Pydantic settings
```

### Integration Unit Boundary Principle
**Code organization follows external service boundaries, not internal usage patterns.**

When integrating with external services, organize code by **integration boundary** (the external system), not by **usage pattern** (how we use it internally). A single external service = single client class with all capabilities.

**Example**: `HackerNewsClient` (in `core/discussions/hn_client.py`) handles BOTH:
- Article URL extraction via HTML scraping (`extract_article_url()`)
- Discussion fetching via Algolia API (`search_by_url()`, `fetch_story()`)

**Why not split by usage pattern?**
- **Shared operational boundary**: Rate limits, monitoring, error handling, and caching operate at the service level
- **Concentrated domain knowledge**: HN URL structure, API quirks, error patterns all live in one place
- **Simpler mental model**: One import for all HN operations
- **Unified configuration**: Single timeout, cache client, retry logic shared across all HN operations
- **Easier testing**: Mock one service, not multiple facades

**Applied to**: `HackerNewsClient`, `LobstersClient` (both in `core/discussions/`)

**Handler responsibility boundary**: Platform handler implementations return data only - no file I/O operations. Orchestrator handles persistence, keeping handlers focused on external service integration.

### Medallion Data Architecture
The pipeline uses a **medallion architecture** (Bronze → Silver) with immutable bronze layer:

```
artifacts/
  bronze/                    # Extracted, immutable data (never modified/deleted)
    html/{url_hash}.json           # Extracted HTML content
    youtube_downloads/{video_id}/  # YouTube video metadata & transcripts
      metadata.json
      transcription.json
      video.m4a
    discussions/{url_hash}/        # HN/Lobsters comments
      metadata.json
      {platform}_{discussion_id}.json
  silver/                    # AI-generated summaries (can be regenerated)
    article_summaries/{url_hash}.json      # Stage 1: Article analysis
    discussion_summaries/{url_hash}/       # Stage 2: Per-discussion analysis
      {platform}_{discussion_id}.json
    summaries/{url_hash}.json              # Stage 3: Final synthesis
```

**Key principle**: Bronze layer is append-only cache. Silver layer can be deleted and regenerated.

### Caching Strategy
The pipeline implements **multi-layer caching** with different strategies per layer:

**HTTP Cache Layer** (via AsyncCacheClient/Hishel):
- Caches raw HTTP responses (GET requests only)
- TTL: 24 hours (86400 seconds)
- Location: `artifacts/cache/http_responses/http_cache.db`
- Prevents redundant external API calls and network requests
- Supports proxy configuration via `HTTP_PROXY` environment variable

**Bronze Layer Caching**:
- All bronze operations check for existing data before downloading
- Immutable by design - once written, never modified
- Cache check is **always required** to prevent duplicate file writes
- Protects external APIs from repeated calls (HN, Lobsters, HTML downloads)

**YouTube Caching** (special case):
- yt_dlp and youtube_transcript_api bypass the HTTP cache layer (use their own HTTP clients)
- Bronze layer caching provides primary protection against re-fetching
- Proxy configuration encapsulated in `YouTubeExtractor` class
- Acceptable by design - bronze cache is sufficient for YouTube operations

**Silver Layer Caching** (selective strategy):
- **Cheap operations** (extraction, discussion parsing): **No cache checks**
  - `silver_article_summary`: Always regenerates from bronze (CPU cost acceptable)
  - `silver_discussion_summary`: Always re-processes discussions (trivial JSON parsing)
  - Rationale: Deterministic operations with negligible cost; simpler code

- **Expensive operations** (AI summarization): **Cache checks required**
  - `silver_summary`: **MUST check cache** to prevent wasteful OpenAI API calls
  - Cost: ~$0.005 per article (~$15/month for 3k articles)
  - Non-deterministic and expensive - cache is critical

**Philosophy**: Cache at the layer where it provides maximum value. HTTP cache prevents network waste, bronze cache protects immutability, silver cache only for operations where regeneration cost is significant.

### Layered Architecture Pattern
Clean separation of concerns following **framework-agnostic core**:

```
ailabbrains/
  cli.py                     # Typer CLI entry point
  orchestrator.py            # Pipeline orchestration with Rich progress bars
  storage.py                 # Simple I/O functions (save, load, exists, get_path)

  core/                      # Pure business logic (framework-agnostic, could be pip package)
    summarizer/
      article/summarizer.py       # Stage 1: Article-only analysis
      discussion/summarizer.py    # Stage 2: Per-discussion analysis
      synthesis/synthesizer.py    # Stage 3: Community synthesis
      schema.py                   # Pydantic models (ArticleAnalysis, CommunityTake)
    content_types/
      generic_html.py             # HTML content extraction
      youtube.py                  # YouTube download + extraction
    extractors/
      watchers.py                 # RSS/feed monitoring
    aggregators/
      detector.py                 # Detect if URL is aggregator (HN, Lobsters)
    discussions/                  # Platform integrations
      hn_client.py                # HackerNews client (extraction + discussions)
      lobsters_client.py          # Lobsters client (extraction + discussions)
      discussion_fetcher.py       # Multi-platform orchestration
      comment_processor.py        # Comment thread flattening
    cache/                        # HTTP caching layer
      http_cache.py               # Cache-aware HTTP client
      cached_openai_client.py     # OpenAI response cache
    tools/
      transcriber/transcriber.py  # Whisper transcription

  utils/                     # Shared utilities
    paths.py                      # Centralized path constants
    url_utils.py                  # URL normalization
    asset_utils.py                # Stats tracking (Pydantic model)

  config.py                  # Pydantic settings
```

**Dependency flow**: `core` (pure logic) → `orchestrator` (pipeline coordination) → `cli` (user interface)

### Pipeline Flow
The CLI provides a single orchestrator that processes URLs through three stages:

**Stage 0: URL Discovery**
- Reads input files (`manual_links.txt` or `monitoring_list.txt`)
- Expands RSS feeds to individual article URLs
- Resolves aggregator URLs (HN/Lobsters) to discussions + linked articles
- Normalizes and deduplicates URLs
- Detects content type (HTML vs YouTube)

**Stage 1: Bronze Layer Extraction** (parallel fan-out)
- **HTML extraction**: `GenericHTMLExtractor` via trafilatura
- **YouTube download**: `YouTubeExtractor` via yt-dlp
- **YouTube transcription**: `Transcriber` via faster-whisper
- **Discussion fetching**: Multi-platform via `HackerNewsClient`, `LobstersClient`

**Stage 2: Silver Layer Summarization** (3-stage AI pipeline)
- **Article Summary** (Stage 1): Analyze content only, no discussions
- **Discussion Summaries** (Stage 2): Per-discussion analysis with article context
- **Final Synthesis** (Stage 3): Synthesize multiple discussions into single community take

**Data flow**:
```
Input Files → discover_urls() → Bronze Layer (extract_html, download_youtube,
transcribe_youtube, fetch_discussions) → Silver Layer (generate_article_summary,
generate_discussion_summaries, synthesize_final_summary)
```

**Progress Tracking**:
- Rich progress bars show real-time status for each stage
- Color-coded output: [green]✓ success[/green], [cyan]cached[/cyan], [red]✗ failed[/red]
- Sequential URL processing with async HTTP operations

### Key Architectural Principles
1. **Immutable bronze layer**: Never modify/delete; acts as source-of-truth cache
2. **Regenerable silver layer**: Can delete and re-process from bronze
3. **URL hash partitioning**: All artifacts stored by `sha256(url)` for deduplication
4. **Fan-out pattern**: URL discovery fans out to multiple bronze operations (HTML, YouTube, discussions)
5. **Content type detection**: `ContentType.HTML` vs `ContentType.YOUTUBE` determines processing path
6. **Aggregator expansion**: URLs to HN/Lobsters fetch discussions + expand to linked articles
7. **Caching at every layer**: Bronze caching (immutable), HTTP caching (core/cache/), silver caching (regenerable)
8. **Sequential orchestration with async HTTP**: Process URLs one at a time with progress bars, use async for HTTP

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
  utils/                     # Utility tests
```

**Test markers**:
- `@pytest.mark.integration` - Integration tests (may hit external APIs in controlled manner)
- `@pytest.mark.unit` - Pure unit tests
- `@pytest.mark.contract` - External API contract verification

## Experiments Directory
`experiments/v3/` contains prompt engineering experiments:
- `run.py` - Test different LLM models/prompts for summarization
- `test_cases/` - Sample articles with expected summaries
- `runs/` - Experiment results (JSON)
- Separate from main pipeline; used for prompt iteration

## Data Persistence
- **Bronze/Silver artifacts**: `artifacts/{bronze,silver}/` (git-ignored)
- **Input files**: `manual_links.txt`, `monitoring_list.txt` (use `.template` versions as reference)
- **Cache**: `.cache/` directory for HTTP and OpenAI caches

## Tool Configuration
- **Ruff**: Line length 140, Python 3.12+ target
- **Pytest**: Configured for `tests/` directory with custom markers
- **Ty (type checker)**: Python 3.12, strict type safety rules
- **Prek**: Pre-commit hooks for ruff + ty

## CLI Reference

### Main Commands

**process** - Run the full pipeline (discovery → bronze → silver)
```bash
ailabbrains process --source manual       # Process manual_links.txt
ailabbrains process --source monitoring   # Process monitoring_list.txt
```

**stats** - Show artifact statistics
```bash
ailabbrains stats
# Output: Bronze layer (HTML, YouTube, Discussions) + Silver layer counts
```

**clean-cache** - Clean cache layers
```bash
ailabbrains clean-cache --layer http      # HTTP cache only
ailabbrains clean-cache --layer bronze    # Bronze layer
ailabbrains clean-cache --layer silver    # Silver layer
ailabbrains clean-cache --layer all       # All caches and layers
```

### Makefile Shortcuts

Development:
- `make init` - Initialize project (venv, deps, prek)
- `make check` - Run all checks (format, lint, typecheck, test)
- `make format` - Format code with ruff
- `make lint` - Lint with ruff --fix
- `make typecheck` - Type check with ty
- `make test` - Run pytest

Pipeline:
- `make process-manual` - Process manual URLs
- `make process-monitoring` - Process monitoring URLs
- `make stats` - Show artifact statistics

Cache Management:
- `make clean-cache` - Clean HTTP cache
- `make clean-bronze` - Clean bronze layer
- `make clean-silver` - Clean silver layer
- `make clean-all` - Clean all caches and layers
