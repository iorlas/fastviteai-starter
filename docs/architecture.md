# Architecture Documentation - DeepRock

**Project:** deeprock
**Type:** Data Pipeline (Dagster ETL)
**Architecture Pattern:** DAG-based ETL Pipeline
**Generated:** 2025-11-02
**Scan Level:** Quick

---

## Executive Summary

DeepRock is a Dagster-based data pipeline that ingests links from various sources (manual input, RSS feeds), extracts content from HTML articles and YouTube videos, and generates AI-powered summaries using OpenRouter's LLM API. The system follows an asset-oriented ETL architecture with automated scheduling for continuous monitoring.

**Key Characteristics:**
- **Type:** Monolithic data pipeline
- **Language:** Python 3.12+
- **Orchestration:** Dagster 1.12.0+ (asset-based DAG)
- **Storage:** File-based artifacts (JSON)
- **External Dependencies:** OpenRouter API (GPT-4o via OpenAI client)

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Runtime** | Python | 3.12+ | Core language, modern type hints |
| **Orchestration** | Dagster | 1.12.0+ | Data pipeline orchestration and scheduling |
| **LLM API** | OpenAI (OpenRouter) | 1.0.0+ | GPT-4o for content summarization |
| **Data Validation** | Pydantic | 2.12.2+ | Schema validation and type safety |
| **HTML Parsing** | BeautifulSoup4 | 4.14.2+ | Web content extraction |
| **Video Processing** | yt-dlp | 2025.10.22+ | YouTube metadata extraction |
| **RSS Parsing** | feedparser | 6.0.12+ | RSS/Atom feed monitoring |
| **Logging** | structlog | 23.0.0+ | Structured application logging |
| **Configuration** | python-dotenv | 1.2.1+ | Environment variable management |
| **Testing** | pytest | 8.4.2+ | Unit and integration testing |
| **Linting/Formatting** | ruff | 0.14.0+ | Code quality and formatting |

---

## Architecture Pattern: Asset-Oriented DAG Pipeline

### Pattern Overview

DeepRock implements a **DAG-based ETL pipeline** using Dagster's asset-oriented architecture. Each stage of the pipeline is modeled as a data asset with explicit dependencies, creating a directed acyclic graph of data transformations.

### Core Concepts

**Assets:** Materialized data products (links, content, summaries)
- `raw_links` - Ingested URLs from input sources
- `extracted_content` - Parsed HTML/video content
- `summaries` - LLM-generated summaries

**Jobs:** Pipeline execution workflows
- `manual_pipeline` - On-demand processing of manual_links.txt
- `monitoring_pipeline` - Automated processing of monitored sources

**Schedules:** Time-based automation
- `monitoring_schedule` - 6-hour recurring schedule

**Ops:** Reusable operations
- HTML extraction, YouTube extraction, RSS watching

**Resources:** External service integrations
- OpenAI client (OpenRouter endpoint)

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT SOURCES                            │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │ manual_links.txt │          │monitoring_list.txt│        │
│  │  (on-demand)     │          │  (auto, 6hr)      │        │
│  └────────┬─────────┘          └────────┬──────────┘        │
└───────────┼────────────────────────────┼───────────────────┘
            │                            │
            └──────────┬─────────────────┘
                       ▼
            ┌──────────────────────┐
            │  ASSET: raw_links    │ ◄── Watchers (RSS, future: Reddit)
            │  (link_ingestion)    │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │ ASSET: extracted_content │
            │  (content_extraction)    │
            │                          │
            │  Ops:                    │
            │  ├─ html_extractor       │
            │  └─ youtube_extractor    │
            └──────────┬───────────────┘
                       │
                       ├─► artifacts/html/*.json
                       ├─► artifacts/videos/*.json
                       │
                       ▼
            ┌──────────────────────┐
            │  ASSET: summaries    │
            │  (summarization)     │
            │                      │
            │  Resource:           │
            │  └─ OpenAI client    │
            └──────────┬───────────┘
                       │
                       └─► artifacts/summaries/*.json
```

---

## Component Architecture

### 1. Asset Layer (`dagster_project/assets/`)

**Purpose:** Define data transformations as materialized assets

**Components:**

**link_ingestion.py**
- **Input:** manual_links.txt, monitoring_list.txt
- **Output:** List of unprocessed links with metadata
- **Logic:**
  - Read input files
  - Invoke watchers (RSS feed discovery)
  - Deduplicate against existing summaries
  - Return new links for processing

**content_extraction.py**
- **Input:** raw_links (from link_ingestion)
- **Output:** Extracted content (HTML or video)
- **Logic:**
  - Dispatch to html_extractor or youtube_extractor based on URL
  - Clean and structure content
  - Save to artifacts/html/ or artifacts/videos/
  - Return structured content with metadata

**summarization.py**
- **Input:** extracted_content
- **Output:** LLM summaries (JSON)
- **Logic:**
  - Call OpenRouter API (GPT-4o) via OpenAI client
  - Generate 3-5 bullet point summary
  - Save summary to artifacts/summaries/
  - Track model, tokens, latency in metadata

### 2. Job Layer (`dagster_project/jobs/`)

**Purpose:** Define pipeline execution workflows

**manual_pipeline.py**
- Triggers: On-demand (via Dagster UI)
- Scope: Processes manual_links.txt only
- Use case: User-driven link processing

**monitoring_pipeline.py**
- Triggers: Schedule (every 6 hours) or manual
- Scope: Processes monitoring_list.txt
- Use case: Automated content discovery

### 3. Schedule Layer (`dagster_project/schedules/`)

**Purpose:** Automated time-based execution

**monitoring_schedule.py**
- **Cron:** Every 6 hours (0 */6 * * *)
- **Target:** monitoring_pipeline job
- **Behavior:** Automatically processes monitored sources

### 4. Operations Layer (`dagster_project/ops/`)

**Purpose:** Reusable extraction and watching logic

**html_extractor.py**
- **Responsibility:** Extract article content from HTML pages
- **Libraries:** BeautifulSoup4, httpx
- **Logic:**
  - Fetch HTML via HTTP
  - Parse with BeautifulSoup
  - Extract title, body text, metadata
  - Clean (remove scripts, styles, ads)
  - Return structured content

**youtube_extractor.py**
- **Responsibility:** Extract video metadata
- **Libraries:** yt-dlp
- **Current Behavior:** Extracts video description (transcript extraction disabled)
- **Known Limitation:** Does not download actual transcripts
- **Future Enhancement:** Enable subtitle/transcript download

**watchers.py**
- **Responsibility:** Monitor external sources for new content
- **Protocol:** Watcher interface for extensibility
- **Implementations:**
  - `RSSWatcher` - Parse RSS/Atom feeds using feedparser
  - Future: RedditWatcher, TwitterWatcher, etc.

### 5. Resource Layer (`dagster_project/resources/`)

**Purpose:** External service integrations

**openai.py**
- **Service:** OpenRouter API (via OpenAI client library)
- **Model:** openai/gpt-4o (configurable via env)
- **Configuration:**
  - API key: `OPENAI_API_KEY`
  - Base URL: `OPENAI_BASE_URL` (https://openrouter.ai/api/v1)
  - Model: `OPENAI_MODEL`
- **Usage:** Injected into summarization asset as resource

---

## Data Architecture

### Storage Strategy: Medallion Architecture with File-Based Artifacts

**Location:** `artifacts/` directory with medallion layers (bronze, silver)

**Current Structure:**
```
artifacts/
├── bronze/                      # Bronze Layer: Raw, Immutable Data
│   ├── raw_links/
│   │   └── {full_sha256}.json  # Link lists from ingestion
│   └── raw_html/
│       └── {full_sha256}.json  # Downloaded HTML cache
├── silver/                      # Silver Layer: Processed, Application-Ready Data
│   ├── extracted_content/
│   │   └── {full_sha256}.json  # Cleaned content (HTML/video)
│   └── summaries/
│       ├── {full_sha256}.json  # LLM summaries (JSON format)
│       └── {full_sha256}.md    # LLM summaries (Markdown format)
├── html/                        # LEGACY - To be deprecated
│   └── {url_hash}.json
├── videos/                      # LEGACY - To be deprecated
│   └── {url_hash}.json
└── summaries/                   # LEGACY - To be deprecated
    └── {url_hash}.json
```

**Hashing:**
- **Current:** Full SHA256(url) for filename uniqueness (64 characters)
- **Legacy:** SHA256(url)[:16] truncated hash (16 characters)
- **Collision Risk:** None with full hash vs. ~1 in 2^64 with truncated

**Deduplication Logic:**
- Summary file existence in silver/summaries/ = already processed
- No reprocessing unless summary file manually deleted
- Can reprocess silver layer by deleting artifacts and rematerializing from bronze cache

**See [Medallion Architecture](#medallion-architecture) section for detailed layer documentation, IOManager patterns, and reprocessing workflows.**

### Data Models (Pydantic V2)

**Bronze Layer Models:**

**Link List (raw_links):**
- links: list[str]
- created_at: datetime (ISO 8601)
- link_count: int

**Raw HTML (raw_html):**
- url: str
- content: str (raw HTML)
- created_at: datetime (ISO 8601)
- content_length: int
- download_info: dict (optional)

**Silver Layer Models:**

**Extracted Content:**
- url: str
- type: "html" | "youtube"
- title: str
- content: str (cleaned text)
- metadata: dict (author, published_date, word_count, etc.)
- lineage: dict (source_asset, source_hash, transformation_timestamp)
- created_at: datetime (ISO 8601)
- updated_at: datetime (ISO 8601)

**Summary Record (Success):**
- url: str
- title: str
- status: "success"
- summary: str
- model: str (e.g., "openai/gpt-4o")
- tokens_used: int
- latency_ms: int
- lineage: dict (source_asset, source_hash, transformation_timestamp)
- created_at: datetime (ISO 8601)
- updated_at: datetime (ISO 8601)

**Summary Record (Failure):**
- url: str
- title: str
- status: "failed"
- error: str
- error_type: str
- lineage: dict (source_asset, source_hash, transformation_timestamp)
- created_at: datetime (ISO 8601)
- updated_at: datetime (ISO 8601)

---

## Medallion Architecture

### Pattern Overview

DeepRock implements a **medallion architecture** pattern for data storage, separating data by maturity level into bronze and silver layers. This pattern enables data lineage tracking, reprocessing capabilities, and clear data quality progression.

### Layers

**Bronze Layer: Raw, Immutable Data**
- **Purpose:** Store raw data exactly as ingested from sources, never modified
- **Location:** `artifacts/bronze/`
- **Subdirectories:**
  - `raw_links/` - Link lists from manual and monitoring sources
  - `raw_html/` - Downloaded HTML content cache
- **Characteristics:**
  - Immutable (write-once, never update)
  - Full fidelity preservation
  - Enables reprocessing without re-downloading
  - No business logic applied

**Silver Layer: Processed, Application-Ready Data**
- **Purpose:** Store cleaned, validated, and enriched data ready for consumption
- **Location:** `artifacts/silver/`
- **Subdirectories:**
  - `extracted_content/` - Cleaned content from HTML and video sources
  - `summaries/` - LLM-generated summaries (JSON + markdown)
- **Characteristics:**
  - Business logic applied
  - Quality validated
  - Enriched with metadata
  - Application-ready format

### Data Flow: Bronze → Silver

```
┌─────────────────────────────────────────────────────────┐
│                   INGESTION SOURCES                      │
│  manual_links.txt / monitoring_list.txt / RSS feeds     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   BRONZE LAYER         │
        │  (Raw, Immutable)      │
        │                        │
        │  raw_links/            │ ◄── Link ingestion output
        │  raw_html/             │ ◄── HTML download cache
        └────────┬───────────────┘
                 │ transformation
                 ▼
        ┌────────────────────────┐
        │   SILVER LAYER         │
        │  (Processed, Ready)    │
        │                        │
        │  extracted_content/    │ ◄── Content extraction
        │  summaries/            │ ◄── LLM summarization
        └────────────────────────┘
```

### File Naming Convention

**Asset Naming Pattern:** `{layer}_{data_type}`

**Bronze Assets:**
- `bronze_raw_links` - Link ingestion output (Stories 1.4)
- `bronze_raw_html` - Raw HTML downloads (Stories 1.5)

**Silver Assets:**
- `silver_extracted_content` - Processed content (Stories 1.6)
- `silver_summaries` - LLM summaries (Stories 1.7)

**File Naming Within Directories:**
- **Format:** `{full_sha256_hash}.{extension}`
- **Example:** `50d858e0985ecc7f8b1b0e3b5c8d2f1a3e4b6c7d8e9f0a1b2c3d4e5f6a7b8c9d.json`
- **Hash Input:** URL for content-based artifacts, link list for raw_links
- **Note:** Replaces current truncated SHA256[:16] approach (64 chars vs. 16 chars)
- **Rationale:** Eliminates hash collision risk entirely

### Metadata Requirements

**All Artifacts (Bronze + Silver):**
- `created_at` (ISO 8601) - Initial creation timestamp

**Silver Layer Only:**
- `updated_at` (ISO 8601) - Last modification timestamp
- `source_asset` - Bronze layer source identifier
- `source_hash` - SHA256 hash of source data
- `transformation_timestamp` (ISO 8601) - When transformation occurred

### IOManager Implementation

DeepRock uses Dagster's **IOManager** pattern to handle data persistence across medallion layers. Each layer has a dedicated IOManager that manages serialization, storage, and retrieval with layer-appropriate metadata.

#### BronzeIOManager

**Purpose:** Persist raw, immutable data with minimal processing.

**Implementation:** `dagster_project/resources/io_managers.py:13-140`

**Key Responsibilities:**
- Store link lists from ingestion sources
- Cache downloaded HTML content
- Generate full SHA256 hash filenames
- Add `created_at` timestamps

**Usage Pattern:**
```python
from dagster import asset

@asset(
    io_manager_key="bronze_io_manager",
    group_name="bronze_layer",
    tags={"layer": "bronze"}
)
def bronze_raw_links(context) -> list:
    links = ["https://example.com/article1", "https://example.com/article2"]
    return links  # BronzeIOManager handles persistence
```

**Storage Format (Link List):**
```json
{
  "links": ["https://example.com/article1", "https://example.com/article2"],
  "created_at": "2025-11-02T10:30:00Z",
  "link_count": 2
}
```

**Storage Format (HTML Content):**
```json
{
  "url": "https://example.com/article",
  "content": "<html>...</html>",
  "created_at": "2025-11-02T10:30:00Z",
  "content_length": 15000,
  "download_info": {}
}
```

#### SilverIOManager

**Purpose:** Persist processed data with lineage tracking and content-type awareness.

**Implementation:** `dagster_project/resources/io_managers.py:142-364`

**Key Responsibilities:**
- Store extracted content (HTML and YouTube)
- Store LLM summaries with dual-format output (JSON + Markdown)
- Track lineage metadata (source_asset, source_hash, transformation_timestamp)
- Add `created_at` and `updated_at` timestamps

**Usage Pattern:**
```python
from dagster import asset

@asset(
    io_manager_key="silver_io_manager",
    group_name="silver_layer",
    tags={"layer": "silver"}
)
def silver_extracted_content(context, bronze_raw_html: dict) -> dict:
    extracted = {
        "url": bronze_raw_html["url"],
        "type": "html",
        "title": "Article Title",
        "content": "Extracted content...",
        "metadata": {},
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "abc123...",
            "transformation_timestamp": "2025-11-02T10:31:00Z"
        }
    }
    return extracted  # SilverIOManager handles persistence
```

**Storage Format (Extracted Content):**
```json
{
  "url": "https://example.com/article",
  "type": "html",
  "title": "Article Title",
  "content": "Extracted content...",
  "metadata": {},
  "lineage": {
    "source_asset": "bronze_raw_html",
    "source_hash": "50d858e0985ecc7f...",
    "transformation_timestamp": "2025-11-02T10:31:00Z"
  },
  "created_at": "2025-11-02T10:31:00Z",
  "updated_at": "2025-11-02T10:31:00Z"
}
```

**Storage Format (Summary - JSON):**
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "status": "success",
  "summary": "Key points from the article...",
  "model": "openai/gpt-4o",
  "tokens_used": 500,
  "latency_ms": 1200,
  "lineage": {
    "source_asset": "silver_extracted_content",
    "source_hash": "50d858e0985ecc7f...",
    "transformation_timestamp": "2025-11-02T10:32:00Z"
  },
  "created_at": "2025-11-02T10:32:00Z",
  "updated_at": "2025-11-02T10:32:00Z"
}
```

**Storage Format (Summary - Markdown):**

SilverIOManager automatically generates a markdown file alongside each summary JSON:

```markdown
# Article Title

**URL:** https://example.com/article
**Status:** Success
**Model:** openai/gpt-4o

## Summary

Key points from the article...

---
**Generated:** 2025-11-02T10:32:00Z
**Tokens:** 500
**Latency:** 1200ms
```

#### IOManager Registration

IOManagers are registered as Dagster resources in `dagster_project/definitions.py`:

```python
from dagster import Definitions
from dagster_project.resources.io_managers import BronzeIOManager, SilverIOManager

defs = Definitions(
    assets=[...],
    resources={
        "bronze_io_manager": BronzeIOManager(),
        "silver_io_manager": SilverIOManager(),
    }
)
```

### Testing Structure

DeepRock follows a **mirrored test organization** pattern where test directories mirror the production code structure. This makes tests easy to discover and maintains clear organizational boundaries.

**Directory Structure:**
```
dagster_project/          tests/
├── assets/      →        ├── assets/
├── ops/         →        ├── ops/
├── resources/   →        ├── resources/
└── jobs/        →        └── jobs/
                          └── integration/  (cross-component tests)
```

**Test Markers:**
- `@pytest.mark.integration` - Multi-component interactions or I/O operations
- `@pytest.mark.unit` - Isolated component tests (optional, used sparingly)

**IOManager Test Pattern:**

Tests use pytest fixtures with `tmp_path` for isolated file operations and Dagster test utilities for context creation:

```python
import pytest
from dagster import OutputContext, InputContext, AssetKey
from dagster_project.resources.io_managers import BronzeIOManager

@pytest.fixture
def bronze_io_manager(tmp_path):
    return BronzeIOManager(base_dir=str(tmp_path / "bronze"))

@pytest.mark.integration
def test_link_list_serialization_round_trip(bronze_io_manager):
    link_list = ["https://example.com/article1", "https://example.com/article2"]

    context = OutputContext(
        name="test_output",
        step_key="test_step",
        mapping_key=None,
        config=None,
        metadata=None,
        log_manager=None,
        version=None,
        resource_config=None,
        resources=None,
        dagster_type=None,
        asset_key=None,
    )

    bronze_io_manager.handle_output(context, link_list)

    files = list(bronze_io_manager.raw_links_dir.glob("*.json"))
    assert len(files) == 1
    assert len(files[0].name.replace(".json", "")) == 64  # Full SHA256
```

**Test Coverage Areas:**
- Serialization/deserialization round-trips
- Hash generation (SHA256, 64 characters)
- Timestamp validation (ISO 8601 format)
- Metadata preservation
- Error handling (TypeError, JSONDecodeError, FileNotFoundError)
- Content-type routing (HTML vs YouTube)
- Dual-format output (JSON + Markdown for summaries)
- Lineage metadata structure

**Reference Implementations:**
- `tests/resources/test_bronze_io_manager_unit.py` - 14 tests covering bronze layer persistence
- `tests/resources/test_silver_io_manager_unit.py` - 20 tests covering silver layer persistence with dual formats

### Reprocessing Workflow

The medallion architecture's key benefit is enabling **reprocessing without re-downloading**. Bronze layer acts as an immutable cache of raw data that silver layer can repeatedly transform.

**Common Scenario:** Updated extraction or summarization logic requires regenerating silver artifacts.

**Reprocessing Steps:**

1. **Delete Silver Artifacts** (preserves bronze cache):
   ```bash
   rm -rf artifacts/silver/extracted_content/*
   rm -rf artifacts/silver/summaries/*
   ```

2. **Rematerialize Silver Assets** in Dagster UI:
   - Navigate to Assets view
   - Select `silver_extracted_content` and `silver_summaries`
   - Click "Materialize selected"

3. **Assets Read from Bronze Cache**:
   - No HTTP requests to external URLs
   - Reads cached HTML from `artifacts/bronze/raw_html/`
   - Applies new extraction/summarization logic
   - Generates new silver artifacts with updated timestamps

**Benefits:**
- **Fast Iteration:** Reprocessing takes seconds instead of minutes (no network latency)
- **Cost Savings:** No redundant API calls or bandwidth usage
- **Bronze Immutability:** Original raw data preserved, can reprocess indefinitely
- **Logic Evolution:** Iteratively refine extraction and summarization without data loss

**Cache Behavior:**
- Bronze layer: Write-once, never modified (even during reprocessing)
- Silver layer: Can be deleted and regenerated freely
- Lineage metadata: Tracks which bronze artifact sourced each silver artifact

**Example Reprocessing Use Case:**

```bash
# Scenario: Improved prompt engineering for summarization

# Step 1: Delete existing summaries
rm -rf artifacts/silver/summaries/*

# Step 2: Update summarization prompt in silver_summaries.py
# (Edit create_summarization_prompt() function)

# Step 3: Rematerialize in Dagster UI
# (Click "Materialize selected" on silver_summaries asset)

# Result: New summaries generated with updated prompts,
# using cached HTML from bronze layer (no re-download)
```

### Migration Strategy

**Current State (Legacy):**
```
artifacts/
├── html/          # Current HTML storage ([:16] hash)
├── videos/        # Current video metadata ([:16] hash)
└── summaries/     # Current summaries ([:16] hash)
```

**Target State (Medallion):**
```
artifacts/
├── bronze/              # NEW - Bronze layer
│   ├── raw_links/      # NEW - Link ingestion output
│   └── raw_html/       # NEW - HTML download cache
├── silver/             # NEW - Silver layer
│   ├── extracted_content/  # NEW - Processed content
│   └── summaries/          # NEW - LLM summaries
├── html/               # LEGACY - To be deprecated
├── videos/             # LEGACY - To be deprecated
└── summaries/          # LEGACY - To be deprecated
```

**Migration Path:**
- Story 1.4: Migrate link ingestion to bronze layer
- Story 1.5: Add raw HTML download to bronze layer
- Story 1.6: Migrate content extraction to silver layer
- Story 1.7: Migrate summarization to silver layer
- Stories 1.4-1.7: Coexistence period (both structures active)
- Future: Deprecate and remove legacy structure

**Coexistence Strategy:**
- New data flows to medallion structure
- Existing artifacts remain in legacy structure
- No backfill or migration of historical data
- Gradual transition as new data is processed

---

## API Design

**Note:** This is a data pipeline, not a web service. No REST/GraphQL APIs.

**Dagster UI:** Primary interface for pipeline interaction
- URL: http://localhost:3000
- Functions: View assets, trigger jobs, monitor runs, view logs

---

## Source Tree

See: [Source Tree Analysis](/docs/source-tree-analysis.md)

**Entry Point:** `dagster_project/definitions.py`

**Key Directories:**
- `dagster_project/` - Main pipeline code
- `dagster_project/assets/` - ETL asset definitions
- `dagster_project/jobs/` - Pipeline workflows
- `dagster_project/schedules/` - Automated schedules
- `dagster_project/ops/` - Reusable operations
- `dagster_project/resources/` - External integrations
- `tests/` - Test suite (unit + integration)
- `artifacts/` - Pipeline outputs

---

## Development Workflow

See: [Development Guide](/docs/development-guide.md)

**Setup:**
```bash
uv sync                # Install dependencies
cp .env.example .env   # Configure environment
uv run dagster dev     # Start development server
```

**Quality Checks:**
```bash
make check             # Format, lint, typecheck, test
```

**Testing:**
```bash
uv run pytest          # Run all tests
uv run pytest -m integration  # Integration tests only
```

---

## Deployment Architecture

**Status:** No containerization or CI/CD configured

**Current Deployment:**
- Local development only
- Manual execution via `uv run dagster dev`

**Future Considerations:**
- Docker containerization
- Dagster Cloud deployment
- CI/CD pipeline (GitHub Actions, GitLab CI)
- Production environment configuration

---

## Testing Strategy

### Test Structure

```
tests/
├── integration/              # End-to-end tests
│   ├── test_jobs.py          # Job execution tests
│   └── test_pipeline_integration.py  # Full pipeline tests
├── fixtures/                 # Test data
├── test_storage.py           # Storage layer tests
├── test_html_extractor.py    # HTML extraction tests
├── test_youtube_extractor.py # YouTube extraction tests
├── test_link_ingestion.py    # Link ingestion tests
├── test_environment.py       # Environment config tests
└── test_openai.py            # OpenAI integration tests
```

### Test Coverage

- **Unit Tests:** 7 files (ops, storage, ingestion)
- **Integration Tests:** 2 files (jobs, end-to-end pipeline)
- **Framework:** pytest with asyncio support

### Test Markers

- `unit` - Fast, isolated tests
- `integration` - Slower, multi-component tests
- `contract` - External API verification tests

---

## Security & Configuration

### Environment Variables

**Required:**
- `OPENAI_API_KEY` - OpenRouter API key
- `OPENAI_BASE_URL` - OpenRouter endpoint
- `OPENAI_MODEL` - LLM model selection

**Optional:**
- `DAGSTER_HOME` - Dagster metadata storage location

### Security Considerations

- API keys stored in .env (excluded from git)
- No user authentication (local development only)
- External API calls: OpenRouter (HTTPS)

---

## Known Limitations & Future Enhancements

### Known Limitations

1. **YouTube Transcript Extraction**
   - Current: Uses video description only
   - Limitation: Actual transcripts not downloaded
   - Impact: Lower quality summaries for videos
   - Location: `dagster_project/ops/youtube_extractor.py`

2. **No Deployment Configuration**
   - No Docker/docker-compose
   - No CI/CD pipeline
   - Local development only

3. **File-Based Storage**
   - No database
   - Manual deduplication management
   - No query capabilities

### Future Enhancements

1. **YouTube Transcripts**
   - Enable yt-dlp subtitle download
   - Use actual transcripts for summarization

2. **Additional Watchers**
   - RedditWatcher (subreddit monitoring)
   - TwitterWatcher (tweet monitoring)
   - HackerNewsWatcher

3. **Database Integration**
   - PostgreSQL for metadata
   - Better query capabilities
   - Relational link tracking

4. **Deployment**
   - Docker containerization
   - Dagster Cloud deployment
   - CI/CD automation

5. **Monitoring & Observability**
   - Metrics collection
   - Error alerting
   - Performance tracking

---

## References

- **Development Guide:** [/docs/development-guide.md](/docs/development-guide.md)
- **Source Tree:** [/docs/source-tree-analysis.md](/docs/source-tree-analysis.md)
- **Technical Spec:** [/docs/tech-spec.md](/docs/tech-spec.md)
- **Epic Breakdown:** [/docs/epics.md](/docs/epics.md)
- **Dagster Docs:** https://docs.dagster.io
