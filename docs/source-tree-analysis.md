# Source Tree Analysis - DeepRock

**Project:** deeprock
**Type:** Data Pipeline (Dagster-based ETL)
**Generated:** 2025-11-02
**Scan Level:** Quick

---

## Project Structure

```
deeprock/
├── dagster_project/                 # [MAIN] Dagster pipeline implementation
│   ├── __init__.py
│   ├── definitions.py               # [ENTRY POINT] Dagster definitions module
│   ├── assets.py                    # Backward-compatible asset exports
│   ├── assets/                      # Data assets (ETL stages)
│   │   ├── __init__.py
│   │   ├── link_ingestion.py        # Asset: Ingest links from files/watchers
│   │   ├── content_extraction.py    # Asset: Extract HTML/YouTube content
│   │   └── summarization.py         # Asset: LLM summarization via OpenAI
│   ├── jobs/                        # Pipeline execution jobs
│   │   ├── __init__.py
│   │   ├── manual_pipeline.py       # Job: Process manual_links.txt
│   │   └── monitoring_pipeline.py   # Job: Process monitoring_list.txt
│   ├── schedules/                   # Automated scheduling
│   │   ├── __init__.py
│   │   └── monitoring_schedule.py   # Schedule: 6-hour monitoring runs
│   ├── ops/                         # Reusable operations
│   │   ├── __init__.py
│   │   ├── html_extractor.py        # Op: HTML content extraction
│   │   ├── youtube_extractor.py     # Op: YouTube transcript extraction
│   │   └── watchers.py              # Op: RSS/Reddit monitoring watchers
│   ├── resources/                   # External service integrations
│   │   ├── __init__.py
│   │   └── openai.py                # Resource: OpenAI API client
│   └── README.md                    # Dagster project documentation
│
├── dagster_project_tests/           # Dagster-specific tests
│   └── test_assets.py               # Asset materialization tests
│
├── tests/                           # Main test suite
│   ├── integration/                 # Integration tests
│   │   ├── test_jobs.py             # Job execution tests
│   │   └── test_pipeline_integration.py  # End-to-end pipeline tests
│   ├── fixtures/                    # Test fixtures and sample data
│   ├── test_storage.py              # Storage layer tests
│   ├── test_html_extractor.py       # HTML extraction tests
│   ├── test_youtube_extractor.py    # YouTube extraction tests
│   ├── test_link_ingestion.py       # Link ingestion tests
│   ├── test_environment.py          # Environment configuration tests
│   └── test_openai.py               # OpenAI integration tests
│
├── artifacts/                       # [OUTPUT] Pipeline artifacts storage
│   ├── html/                        # Extracted HTML content (JSON)
│   ├── videos/                      # YouTube transcripts (JSON)
│   └── summaries/                   # LLM summaries (JSON)
│
├── docs/                            # Project documentation
│   ├── tech-spec.md                 # Technical specification
│   ├── epics.md                     # Epic breakdown
│   ├── NOTES.md                     # Development notes
│   └── stories/                     # User stories
│       ├── story-link-pipeline-1.md
│       ├── story-link-pipeline-1.1.md
│       ├── story-link-pipeline-2.md
│       └── story-link-pipeline-3.md
│
├── pyproject.toml                   # [CONFIG] Python project configuration
├── Makefile                         # Build and development commands
├── README.md                        # Project overview
├── .env.example                     # Environment variable template
└── .env                             # Environment configuration (not in git)
```

---

## Critical Directories

### Core Pipeline (`dagster_project/`)

**Purpose:** Main Dagster pipeline implementation containing all ETL logic

**Entry Point:** `definitions.py` - Defines Dagster repository, assets, jobs, schedules, and resources

**Key Components:**
- `assets/` - Data transformation stages (link_ingestion → content_extraction → summarization)
- `jobs/` - Pipeline execution jobs (manual vs. monitoring modes)
- `schedules/` - Automated scheduling (6-hour monitoring)
- `ops/` - Reusable operations (extractors, watchers)
- `resources/` - External integrations (OpenAI API)

**Architecture Pattern:** Asset-oriented DAG pipeline (Extract → Transform → Load)

### Test Suite (`tests/`)

**Purpose:** Comprehensive testing (unit + integration)

**Structure:**
- **Unit tests** (root): Individual component tests (extractors, storage, ingestion)
- **Integration tests** (`integration/`): End-to-end pipeline tests
- **Fixtures** (`fixtures/`): Sample data for testing

**Test Framework:** pytest with asyncio support

### Output Storage (`artifacts/`)

**Purpose:** File-based artifact storage for pipeline outputs

**Organization:**
- `html/` - Extracted HTML content (cleaned, structured)
- `videos/` - YouTube video transcripts
- `summaries/` - LLM-generated summaries (final output)

**Naming Convention:** Files named using URL hash (SHA256)

### Documentation (`docs/`)

**Purpose:** Project planning and specification documents

**Contents:**
- Technical specification (tech-spec.md)
- Epic breakdown (epics.md)
- User stories (stories/)
- Development notes (NOTES.md)

---

## Data Flow

```
Input Sources (manual_links.txt, monitoring_list.txt)
    ↓
[Asset: link_ingestion]
    ↓
[Asset: content_extraction] → artifacts/html/, artifacts/videos/
    ↓
[Asset: summarization] → artifacts/summaries/
```

---

## Entry Points

**Primary Entry Point:**
- `dagster_project/definitions.py` - Dagster module entry point

**Run Commands:**
- `dagster dev` - Start development server
- `make check` - Run linting and tests
- `pytest` - Run test suite

---

## Configuration Files

- `pyproject.toml` - Project dependencies, tool configuration
- `.env` - Environment variables (API keys, config)
- `Makefile` - Development commands

---

## Notes

- **Deployment:** No containerization detected (no Dockerfile/docker-compose)
- **CI/CD:** No CI/CD pipeline configuration found
- **Database:** File-based storage (no SQL database)
- **External Dependencies:** OpenAI API (via OpenRouter)
