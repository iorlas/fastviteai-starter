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

### Storage Strategy: File-Based Artifacts

**Location:** `artifacts/` directory

**Structure:**
```
artifacts/
├── html/
│   └── {url_hash}.json          # Extracted HTML content
├── videos/
│   └── {url_hash}.json          # Video metadata/descriptions
└── summaries/
    └── {url_hash}.json          # LLM summaries (success or failure)
```

**Hashing:** SHA256(url)[:16] for filename uniqueness

**Deduplication Logic:**
- Summary file existence = already processed
- No reprocessing unless summary file manually deleted

### Data Models (Inferred - Pydantic-based)

**Link Record:**
- url: str
- source: "manual" | "monitoring"
- discovered_at: datetime
- watcher_type: str (optional, e.g., "rss")

**Extracted Content:**
- url: str
- type: "html" | "youtube"
- title: str
- content: str (cleaned text)
- extracted_at: datetime
- metadata: dict (author, published_date, word_count, etc.)

**Summary Record (Success):**
- url: str
- status: "success"
- summary: str
- model: str (e.g., "openai/gpt-4o")
- tokens_used: int
- latency_ms: int
- processed_at: datetime

**Summary Record (Failure):**
- url: str
- status: "failed"
- error: str
- error_type: str
- processed_at: datetime
- retry_count: int

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
