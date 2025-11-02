# Epic Technical Specification: Medallion Architecture Migration

Date: 2025-11-02
Author: BMad
Epic ID: 1
Status: Draft

---

## Overview

This epic migrates the DeepRock data pipeline from a simple asset-oriented architecture to a medallion architecture with bronze and silver data layers, following Dagster best practices. The refactoring addresses critical architectural gaps: lack of data layering prevents efficient reprocessing, file-based storage lacks proper caching and timestamp tracking, test organization doesn't mirror code structure, and JSON-only summaries aren't optimal for human review.

The migration introduces Dagster IOManagers for each layer, implements full SHA256 hashing for filenames (eliminating potential collisions from the current [:16] truncation), adds comprehensive timestamps and lineage tracking to all artifacts, caches raw HTML in the bronze layer to enable reprocessing without re-downloading, and produces markdown summaries alongside JSON for improved readability. The work restructures tests to mirror code organization (tests/ops/, tests/assets/, tests/resources/) and maintains all existing functionality while establishing a foundation for future gold layer aggregations and analytics.

## Objectives and Scope

**In Scope:**

- Implement bronze layer with BronzeIOManager for raw data (link lists, raw HTML)
- Implement silver layer with SilverIOManager for processed data (extracted content, summaries)
- Migrate all existing assets to use appropriate layer IOManagers
- Add full SHA256 hash-based filenames for all artifacts
- Implement created_at and updated_at timestamps on all JSON artifacts
- Store raw HTML as bronze layer intermediate for caching/reprocessing
- Generate markdown (.md) summary files in addition to JSON
- Restructure test directories to mirror dagster_project code organization
- Add comprehensive tests for both IOManagers
- Update documentation to reflect medallion architecture patterns

**Out of Scope:**

- Gold layer implementation (deferred to future phases)
- Database migration (file-based persistence with IOManagers is the target architecture)
- Additional watcher implementations (Reddit, Twitter, HackerNews)
- YouTube transcript extraction improvements (description-based approach unchanged)
- Deployment infrastructure (Docker, CI/CD)
- API development, real-time processing, or multi-tenancy features

## System Architecture Alignment

This epic aligns with the existing DAG-based ETL pipeline architecture while introducing medallion data layering principles. The current architecture uses three main assets (link_ingestion, content_extraction, summarization) with file-based storage; this refactoring preserves the asset dependency graph while introducing proper data layer abstractions through Dagster IOManagers.

**Architecture Constraints:**
- Must maintain Dagster 1.12.0+ asset-oriented DAG pattern
- Continue using file-based persistence (no database)
- Preserve existing job structure (manual_pipeline, monitoring_pipeline)
- Maintain 6-hour monitoring schedule unchanged
- Keep OpenRouter API integration for LLM summarization
- Support existing watcher protocol (RSSWatcher implementation)

**Components Referenced:**
- `dagster_project/assets/` - All three assets refactored to use IOManagers
- `dagster_project/resources/` - New io_managers.py module for BronzeIOManager and SilverIOManager
- `dagster_project/ops/` - html_extractor and youtube_extractor updated to read from bronze cache
- `tests/` - Complete restructure to mirror code organization
- `artifacts/` - New bronze/ and silver/ subdirectories with layer-specific schemas

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs | Owner |
|--------|---------------|--------|---------|-------|
| **BronzeIOManager** | Persist raw data (links, HTML) to bronze layer | Raw link lists, HTML responses | File storage in `artifacts/bronze/` | Resource layer |
| **SilverIOManager** | Persist processed data (content, summaries) to silver layer | Extracted content, summaries | File storage in `artifacts/silver/` | Resource layer |
| **bronze_raw_links** | Ingest links from input files and watchers | manual_links.txt, monitoring_list.txt, RSSWatcher | List of links with metadata | Asset layer |
| **bronze_raw_html** | Download and cache raw HTML | bronze_raw_links output | Raw HTML with HTTP metadata | Asset layer |
| **silver_extracted_content** | Extract structured content from HTML/videos | bronze_raw_html output | Cleaned content with metadata | Asset layer |
| **silver_summaries** | Generate LLM summaries | silver_extracted_content output | JSON and markdown summaries | Asset layer |
| **html_extractor** | Parse HTML articles | Raw HTML from bronze cache | Structured content (title, body, metadata) | Ops layer |
| **youtube_extractor** | Extract YouTube metadata | Video URL | Video description and metadata | Ops layer |

**New Files Created:**
- `dagster_project/resources/io_managers.py` - BronzeIOManager and SilverIOManager implementations
- `tests/resources/test_bronze_io_manager.py` - Bronze IOManager unit tests
- `tests/resources/test_silver_io_manager.py` - Silver IOManager unit tests
- `tests/assets/` - Restructured asset tests
- `tests/ops/` - Restructured ops tests

**Files Modified:**
- `dagster_project/assets/link_ingestion.py` - Rename to bronze_raw_links, add BronzeIOManager
- `dagster_project/assets/content_extraction.py` - Rename to silver_extracted_content, add SilverIOManager
- `dagster_project/assets/summarization.py` - Rename to silver_summaries, add SilverIOManager
- `dagster_project/ops/html_extractor.py` - Read from bronze cache instead of direct HTTP
- `dagster_project/definitions.py` - Register IOManagers as resources

### Data Models and Contracts

**Bronze Layer Data Models:**

```python
# Bronze Raw Links (JSON)
{
  "url": str,
  "source": "manual" | "monitoring",
  "discovered_at": str (ISO 8601),
  "watcher_type": str | null,  # "rss" for RSS watchers
  "created_at": str (ISO 8601)
}

# Bronze Raw HTML (JSON + .html file)
{
  "url": str,
  "status_code": int,
  "headers": dict,
  "html_content": str,  # Full raw HTML
  "download_timestamp": str (ISO 8601),
  "created_at": str (ISO 8601),
  "error": str | null  # If HTTP error occurred
}
```

**Silver Layer Data Models:**

```python
# Silver Extracted Content (JSON)
{
  "url": str,
  "type": "html" | "youtube",
  "title": str,
  "content": str,  # Cleaned text
  "metadata": {
    "author": str | null,
    "published_date": str | null,
    "word_count": int,
    "extraction_method": "beautifulsoup" | "yt-dlp"
  },
  "lineage": {
    "source_asset": "bronze_raw_html",
    "source_hash": str,  # SHA256 of source URL
    "transformation_timestamp": str (ISO 8601)
  },
  "created_at": str (ISO 8601),
  "updated_at": str (ISO 8601)
}

# Silver Summary (JSON and .md)
{
  "url": str,
  "status": "success" | "failed",
  "summary": str | null,  # 3-5 bullet points (if success)
  "model": str,  # e.g., "openai/gpt-4o"
  "tokens_used": int | null,
  "latency_ms": int | null,
  "error": str | null,  # If failed
  "error_type": str | null,
  "lineage": {
    "source_asset": "silver_extracted_content",
    "source_hash": str,
    "transformation_timestamp": str (ISO 8601)
  },
  "created_at": str (ISO 8601),
  "updated_at": str (ISO 8601)
}
```

**Filename Convention:**
- All files use full SHA256 hash: `{sha256(url)}.{extension}`
- Bronze HTML: `{hash}.json` (metadata) + `{hash}.html` (raw content)
- Silver content: `{hash}.json`
- Silver summaries: `{hash}.json` + `{hash}.md`

**Directory Structure:**

```
artifacts/
├── bronze/
│   ├── raw_links/
│   │   └── {hash}.json
│   └── raw_html/
│       ├── {hash}.json
│       └── {hash}.html
└── silver/
    ├── extracted_content/
    │   └── {hash}.json
    └── summaries/
        ├── {hash}.json
        └── {hash}.md
```

### APIs and Interfaces

**BronzeIOManager Interface:**

```python
class BronzeIOManager(IOManager):
    """Handles persistence of raw data to bronze layer"""

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """
        Serialize and store bronze layer data

        Args:
            context: Dagster output context with asset metadata
            obj: Data to persist (link list or raw HTML)

        Behavior:
            - Generate full SHA256 hash for filename
            - Add created_at timestamp
            - Store in appropriate bronze subdirectory
        """
        pass

    def load_input(self, context: InputContext) -> Any:
        """
        Deserialize and load bronze layer data

        Args:
            context: Dagster input context with asset metadata

        Returns:
            Deserialized data object
        """
        pass
```

**SilverIOManager Interface:**

```python
class SilverIOManager(IOManager):
    """Handles persistence of processed data to silver layer"""

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """
        Serialize and store silver layer data with content-type awareness

        Args:
            context: Dagster output context with asset metadata
            obj: Data to persist (extracted content or summary)

        Behavior:
            - Generate full SHA256 hash for filename
            - Add created_at and updated_at timestamps
            - Add lineage metadata (source asset, transformation timestamp)
            - For summaries: Save both .json and .md formats
        """
        pass

    def load_input(self, context: InputContext) -> Any:
        """
        Deserialize and load silver layer data

        Args:
            context: Dagster input context with asset metadata

        Returns:
            Deserialized data object with metadata
        """
        pass
```

**Asset Signatures (Updated - No Partitioning):**

```python
@asset(io_manager_key="bronze_io_manager")
def bronze_raw_links(context: AssetExecutionContext) -> List[str]:
    """
    Ingest links from files and watchers
    Returns: List of URLs to process
    """
    pass

@asset(io_manager_key="bronze_io_manager")
def bronze_raw_html(context: AssetExecutionContext, bronze_raw_links: List[str]) -> List[dict]:
    """
    Download and cache raw HTML for URLs
    Checks bronze cache (file existence) before downloading
    Returns: List of raw HTML metadata for processed URLs
    """
    pass

@asset(io_manager_key="silver_io_manager")
def silver_extracted_content(context: AssetExecutionContext, bronze_raw_html: List[dict]) -> List[dict]:
    """
    Extract content from bronze HTML cache
    Reads cached HTML from bronze layer
    Can be re-materialized without re-downloading HTML
    """
    pass

@asset(io_manager_key="silver_io_manager")
def silver_summaries(context: AssetExecutionContext, silver_extracted_content: List[dict], openai_client: OpenAI) -> List[dict]:
    """
    Generate LLM summaries from extracted content
    Outputs both JSON and markdown files
    """
    pass
```

**Caching Strategy (No Partitioning):**
- `bronze_raw_html` checks if `{hash}.html` exists in `artifacts/bronze/raw_html/` before downloading
- If cached: Skip download, read from cache
- If not cached: Download, save to cache
- Simpler than partitioning, no partition registry overhead
- Cache cleanup: Manually delete old files from bronze layer as needed

**External API Dependencies:**
- OpenRouter API (via OpenAI client) - LLM summarization endpoint
- No new external APIs introduced

### Workflows and Sequencing

**Asset Dependency Flow (Updated - File-based Caching):**

```
manual_links.txt, monitoring_list.txt
           ↓
    [RSSWatcher] (optional)
           ↓
  bronze_raw_links → List[str] (URLs)
           ↓
  bronze_raw_html → List[dict] (checks cache before download)
           ↓
silver_extracted_content → List[dict] (reads from bronze cache)
           ↓
  silver_summaries → List[dict] (JSON + markdown output)
           ↓
  {hash}.json + {hash}.md (per URL)
```

**Caching Behavior (File Existence Check):**

When `manual_pipeline` runs:
1. `bronze_raw_links` discovers 10 URLs (5 new, 5 already processed)
2. `bronze_raw_html`:
   - For each URL, compute `hash = sha256(url)`
   - Check if `artifacts/bronze/raw_html/{hash}.html` exists:
     - **If exists**: Read from cache, skip download ✓
     - **If not exists**: HTTP GET → save to cache
3. Downstream assets read from bronze cache (all URLs)

**Reprocessing Flow (Delete and Re-run):**

```
Scenario: Updated extraction logic, want to reprocess without re-downloading

1. Delete silver artifacts: rm -rf artifacts/silver/extracted_content/*
2. In Dagster UI: Materialize silver_extracted_content + silver_summaries
3. Assets read from bronze_raw_html cache (no re-download)
4. New extraction/summarization logic applied
5. New silver artifacts saved
```

**Job Execution Sequences:**

**manual_pipeline (single job, handles everything):**
```python
# Job definition (no changes needed)
manual_pipeline = define_asset_job(
    name="manual_pipeline",
    selection=AssetSelection.all()
)
```

**Execution flow:**
1. User adds URLs to manual_links.txt
2. `bronze_raw_links`: Reads file → discovers URLs → returns List[str]
3. `bronze_raw_html`: For each URL:
   - Check if `{hash}.html` exists in bronze cache
   - **If cached**: Read from cache, skip download ✓
   - **If not cached**: HTTP GET → save to bronze/raw_html/
4. `silver_extracted_content`: For each URL → read from bronze cache → extract → save to silver
5. `silver_summaries`: For each URL → call OpenAI → save JSON + markdown

**monitoring_pipeline (6-hour schedule):**
- Same job structure as manual_pipeline
- `bronze_raw_links` reads from monitoring_list.txt instead
- Caching behavior identical (file-existence checks)

**Reprocessing workflow (Delete + Rematerialize):**
- Delete silver artifacts: `rm -rf artifacts/silver/extracted_content/* artifacts/silver/summaries/*`
- In Dagster UI: Materialize `silver_extracted_content` and `silver_summaries`
- Assets read from bronze cache without re-downloading

**Test Execution Sequence:**
1. Integration tests (Required): Full pipeline end-to-end → Cache hit/miss behavior → Reprocessing scenarios
2. Unit tests (Optional): IOManagers for complex serialization logic if needed

## Non-Functional Requirements

### Performance

**Not a focus area for this refactoring** (per PRD NFR001 exclusion)

**Expected behavior:**
- Pipeline throughput: Similar to current implementation (no performance degradation expected)
- IOManager overhead: Minimal serialization/deserialization cost (file-based, non-blocking)
- Partition processing: Sequential per-URL processing (no parallelization required at this stage)
- Caching impact: Bronze HTML caching should *improve* reprocessing performance by eliminating redundant HTTP requests

**No specific performance targets defined**

### Security

**No new security requirements introduced**

**Existing security posture maintained:**
- OpenRouter API key stored in `.env` (excluded from git)
- HTTPS for all external API calls (OpenRouter, HTTP downloads)
- No authentication or authorization (local development only)
- File system access restricted to artifacts directory

**Bronze/Silver layer considerations:**
- Raw HTML may contain sensitive content (stored in bronze layer)
- No encryption at rest (file-based artifacts)
- Access control: File system permissions only

**No changes required for this epic**

### Reliability/Availability

**Reliability improvements through medallion architecture:**

**Data durability:**
- Bronze layer provides durable cache of raw HTML (survives logic changes)
- Full SHA256 hashes eliminate collision risk from current [:16] truncation
- Timestamps enable data lineage tracking and debugging

**Failure handling:**
- HTTP download failures: Store error metadata in bronze layer (allow retry without re-processing entire batch)
- Extraction failures: Isolated to silver layer (bronze cache preserved)
- Summarization failures: Isolated to silver layer (extraction results preserved)
- Per-URL partitioning: Failure in one URL doesn't block others

**Recovery:**
- Reprocessing capability: Delete silver artifacts → re-run from bronze cache
- Idempotent operations: Re-running assets produces same results (deterministic hashing)

**No SLA or availability targets defined** (local development environment)

### Observability

**Dagster built-in observability:**
- Asset materialization tracking (per partition)
- Run history and logs (Dagster UI)
- Asset lineage visualization
- Partition materialization status

**Application logging (structlog):**
- IOManager operations: Log file writes, reads, hash generation
- Partition registration: Log URLs added to url_partitions
- Cache hits/misses: Log when bronze cache is used vs new downloads
- Error conditions: Log HTTP failures, extraction errors, API failures

**Metadata tracking (in artifacts):**
- `created_at`, `updated_at`: Timestamps on all artifacts
- `lineage`: Source asset references and transformation timestamps
- HTTP metadata: Status codes, headers (bronze layer)
- LLM metadata: Model, tokens, latency (silver summaries)

**Metrics:**
- Dagster tracks: Run duration, success/failure rates, asset materialization counts
- No custom metrics implementation required

**No alerting or monitoring infrastructure** (local development only)

## Dependencies and Integrations

**Runtime Dependencies (from pyproject.toml):**

| Dependency | Version Constraint | Purpose | Changes for Epic |
|------------|-------------------|---------|------------------|
| **dagster** | >=1.12.0 | Data orchestration framework | Add DynamicPartitionsDefinition usage |
| **dagster-webserver** | >=1.12.0 | Dagster UI | No changes |
| **openai** | >=1.0.0 | OpenRouter LLM API client | No changes |
| **pydantic** | >=2.12.2 | Data validation and schemas | New models for bronze/silver schemas |
| **structlog** | >=23.0.0 | Structured logging | Add IOManager logging |
| **beautifulsoup4** | >=4.14.2 | HTML parsing | Read from bronze cache |
| **yt-dlp** | >=2025.10.22 | YouTube metadata extraction | No changes |
| **feedparser** | >=6.0.12 | RSS/Atom feed parsing | No changes |
| **python-dotenv** | >=1.2.1 | Environment configuration | No changes |
| **mlflow** | >=2.20.0 | ML experiment tracking | No changes (not used in this epic) |

**Development Dependencies:**

| Dependency | Version Constraint | Purpose | Changes for Epic |
|------------|-------------------|---------|------------------|
| **pytest** | >=8.4.2 | Testing framework | Add partition and IOManager tests |
| **pytest-asyncio** | >=1.2.0 | Async test support | No changes |
| **pytest-mock** | >=3.15.1 | Mocking framework | Mock IOManager behaviors |
| **ruff** | >=0.14.0 | Linting and formatting | No changes |
| **factory-boy** | >=3.3.3 | Test data factories | Possible use for test data |
| **faker** | >=37.11.0 | Fake data generation | Possible use for test data |

**New Dependencies Required:**
- **None** - All required dependencies already present

**External Service Integrations:**

| Service | Purpose | Authentication | Changes for Epic |
|---------|---------|----------------|------------------|
| **OpenRouter API** | LLM summarization (GPT-4o) | API key in .env | No changes |
| **RSS Feeds** | Content discovery via monitoring_list.txt | None (public feeds) | No changes |
| **HTTP URLs** | Content downloading | None (public URLs) | Bronze layer caching added |

**Internal Module Dependencies:**

```
dagster_project/
├── definitions.py           # Registers IOManagers (NEW)
├── assets/
│   ├── link_ingestion.py    # Depends on: watchers (ops)
│   ├── content_extraction.py # Depends on: html_extractor, youtube_extractor (ops), IOManagers (NEW)
│   └── summarization.py      # Depends on: openai_client (resource), IOManagers (NEW)
├── ops/
│   ├── html_extractor.py    # Depends on: beautifulsoup4, httpx → Updated to read from bronze
│   ├── youtube_extractor.py # Depends on: yt-dlp
│   └── watchers.py          # Depends on: feedparser
└── resources/
    ├── openai.py            # Depends on: openai SDK
    └── io_managers.py       # NEW: Depends on: pathlib, json, hashlib, datetime
```

**Integration Points:**

1. **BronzeIOManager ↔ Assets**: Assets decorated with `io_manager_key="bronze_io_manager"`
2. **SilverIOManager ↔ Assets**: Assets decorated with `io_manager_key="silver_io_manager"`
3. **DynamicPartitionsDefinition ↔ Assets**: `url_partitions` shared across partitioned assets
4. **File System ↔ IOManagers**: Read/write to `artifacts/bronze/` and `artifacts/silver/`

**No Breaking Changes to External Integrations**

## Acceptance Criteria (Authoritative)

**AC1: Bronze Layer Implementation**
- Bronze layer directories created at `artifacts/bronze/raw_links/` and `artifacts/bronze/raw_html/`
- BronzeIOManager class implemented in `dagster_project/resources/io_managers.py`
- BronzeIOManager handles serialization/deserialization of link lists and raw HTML
- All bronze artifacts use full SHA256 hash filenames (not [:16] truncated)
- All bronze artifacts include `created_at` timestamp field

**AC2: Silver Layer Implementation**
- Silver layer directories created at `artifacts/silver/extracted_content/` and `artifacts/silver/summaries/`
- SilverIOManager class implemented in `dagster_project/resources/io_managers.py`
- SilverIOManager handles extracted content and summary storage with content-type awareness
- All silver artifacts include `created_at` and `updated_at` timestamp fields
- All silver artifacts include lineage metadata (source_asset, source_hash, transformation_timestamp)

**AC3: File-based Caching Implementation**
- `bronze_raw_html` checks for file existence (`{hash}.html` in bronze cache) before downloading
- If file exists: Read from cache and skip HTTP download
- If file doesn't exist: Download via HTTP and save to cache
- Cache behavior verified: Can run pipeline multiple times, only downloads new URLs

**AC4: Asset Migration to IOManagers**
- `link_ingestion.py` renamed to reference bronze_raw_links asset with bronze_io_manager
- New `bronze_raw_html` asset created with bronze_io_manager
- `content_extraction.py` renamed to reference silver_extracted_content asset with silver_io_manager, reads from bronze_raw_html
- `summarization.py` renamed to reference silver_summaries asset with silver_io_manager

**AC5: Raw HTML Caching**
- bronze_raw_html asset downloads HTML via HTTP and caches to bronze layer
- Raw HTML stored with metadata: url, status_code, headers, download_timestamp, error (if failed)
- html_extractor op reads from bronze cache instead of direct HTTP requests
- Reprocessing scenario verified: Can delete silver artifacts and re-run from bronze cache without re-downloading

**AC6: Full SHA256 Hash Filenames**
- All artifacts use full SHA256 hash of URL as filename: `{sha256(url)}.{extension}`
- No truncation (previous [:16] approach replaced)
- Filename collision risk eliminated

**AC7: Timestamp Metadata**
- All JSON artifacts include ISO 8601 `created_at` timestamp
- All silver artifacts include ISO 8601 `updated_at` timestamp
- Timestamps automatically added by IOManagers on persistence

**AC8: Lineage Metadata**
- All silver artifacts include lineage object with: source_asset, source_hash, transformation_timestamp
- Lineage enables tracing data transformations through medallion layers

**AC9: Markdown Summary Output**
- SilverIOManager saves summaries as both `.json` and `.md` files
- Markdown format includes: title, URL, summary content, metadata footer
- Same full hash used for both files: `{hash}.md` and `{hash}.json`
- Failed summaries also get markdown format showing error details

**AC10: Test Restructuring**
- Test directories created: `tests/assets/`, `tests/ops/`, `tests/resources/`, `tests/jobs/`
- Existing tests moved to appropriate mirrored directories
- All tests updated to reference new asset names and IOManager usage
- pytest discovery works with new structure, all test markers preserved

**AC11: IOManager Testing**
- Unit test file `tests/resources/test_bronze_io_manager.py` created with comprehensive tests
- Unit test file `tests/resources/test_silver_io_manager.py` created with comprehensive tests
- Tests verify serialization, deserialization, hash generation, timestamp creation, error handling
- Integration test verifies end-to-end pipeline: bronze → silver flow with partition caching

**AC12: Documentation Updates**
- `docs/architecture.md` updated with medallion architecture section
- Bronze and silver layer responsibilities documented
- IOManager usage patterns documented
- Data flow diagrams updated to show bronze → silver progression
- File naming conventions (full hash), metadata requirements, reprocessing workflow documented

**AC13: Job Execution Unchanged**
- `manual_pipeline` and `monitoring_pipeline` jobs continue to work with same user workflow
- "Materialize All" in Dagster UI processes new URLs and skips cached URLs automatically
- Reprocessing via asset selection in UI works (select silver assets only → uses bronze cache)

## Traceability Mapping

| AC | PRD Reference | Spec Section(s) | Component(s) | Test Strategy |
|----|---------------|-----------------|--------------|---------------|
| **AC1** | FR001, FR003, FR005, FR006, FR007 | Data Models (Bronze), APIs and Interfaces (BronzeIOManager) | `resources/io_managers.py`, `artifacts/bronze/` | Unit: test_bronze_io_manager.py verifies serialization, hash generation, timestamps |
| **AC2** | FR002, FR004, FR007, FR008 | Data Models (Silver), APIs and Interfaces (SilverIOManager) | `resources/io_managers.py`, `artifacts/silver/` | Unit: test_silver_io_manager.py verifies content-type handling, lineage metadata |
| **AC3** | FR005 (HTML caching) | APIs and Interfaces (Asset Signatures), Workflows (Caching Strategy) | `assets/bronze_raw_html.py` | Integration: test_pipeline_integration.py verifies file-existence cache checks |
| **AC4** | FR001, FR002, FR003, FR004 | Services and Modules, APIs and Interfaces | `assets/link_ingestion.py`, `assets/content_extraction.py`, `assets/summarization.py` | Integration: test_jobs.py verifies asset migration and IOManager usage |
| **AC5** | FR005 | Data Models (Bronze Raw HTML), Workflows (Caching Behavior) | `assets/bronze_raw_html.py`, `ops/html_extractor.py` | Integration: test_pipeline_integration.py verifies HTML caching and reprocessing from cache |
| **AC6** | FR006 | Data Models (Filename Convention) | All IOManagers (hash generation) | Unit: IOManager tests verify full SHA256 hash generation |
| **AC7** | FR007 | Data Models (Bronze and Silver timestamps) | All IOManagers (timestamp injection) | Unit: IOManager tests verify created_at/updated_at fields |
| **AC8** | FR008 | Data Models (Silver lineage) | SilverIOManager | Unit: test_silver_io_manager.py verifies lineage metadata structure |
| **AC9** | FR011 | Data Models (Silver Summary .md), Services and Modules | SilverIOManager (markdown generation) | Integration: test_pipeline_integration.py verifies .md file creation alongside .json |
| **AC10** | FR009, FR010 | Test Strategy Summary | `tests/` directory structure | Pytest run verifies all tests discoverable and passing in new structure |
| **AC11** | NFR002 (Test Coverage for Complex Logic) | Test Strategy Summary | `tests/resources/test_*_io_manager.py` | Unit tests for IOManagers cover serialization, deserialization, error handling |
| **AC12** | FR001-FR011 (documentation of implementation) | All sections | `docs/architecture.md` | Manual review: Documentation accurately reflects implementation |
| **AC13** | Implicit (preserve existing functionality) | Workflows (Job Execution Sequences) | `jobs/manual_pipeline.py`, `jobs/monitoring_pipeline.py` | Integration: test_jobs.py verifies jobs execute successfully with new architecture |

**Traceability Notes:**

- All 11 functional requirements from PRD are covered by acceptance criteria
- NFR002 (test coverage for complex logic) is addressed by AC10 and AC11
- NFR001 (Dagster best practices) is implicit in AC3 (dynamic partitioning) and AC4 (IOManager usage)
- NFR003 (data integrity) is covered by AC6 (full hashes), AC7 (timestamps), and AC8 (lineage)
- Each AC maps to specific components and has a clear test strategy
- Test strategies use a mix of unit tests (isolated component behavior) and integration tests (end-to-end flows)

## Risks, Assumptions, Open Questions

**Risks:**

**R1: Test Migration Effort (LOW)**
- **Risk:** Moving tests to new directory structure may introduce missed test relocations or broken imports
- **Impact:** Tests not discovered or failing after restructure
- **Mitigation:** Run pytest discovery validation after move; use IDE refactoring tools; verify all test markers preserved

**R2: IOManager Complexity (LOW)**
- **Risk:** Custom IOManagers add complexity vs simple file operations
- **Impact:** Harder to debug; more code to maintain
- **Mitigation:** Comprehensive unit tests for IOManagers; clear logging; follows Dagster best practices

**Assumptions:**

**A1:** File system has sufficient storage for bronze HTML cache (raw HTML for all processed URLs)

**A2:** SHA256 hash generation performance is acceptable (no performance degradation from full hash vs truncated)

**A3:** Markdown summary format requirements are simple (title, content, metadata footer) - no complex rendering needed

**A4:** Existing RSS watcher and extractor logic can be reused with minimal changes (only input/output sources change)

**A5:** File existence checks are sufficient for cache management (no need for partition registry)

**Open Questions:**

**Q1:** How should we handle existing artifacts/ directory content during migration?
- **Answer needed by:** Story 1.1 (directory structure)
- **Options:** (a) Migrate existing artifacts to new structure, (b) Start fresh (delete old artifacts), (c) Keep both structures temporarily
- **Decision:** Start fresh - delete old artifacts (greenfield approach per PRD)

## Test Strategy Summary

**Test Levels:**

**1. Integration Tests (Required)**
- **Scope:** Multi-component interactions and end-to-end flows
- **Coverage:**
  - Full pipeline flow: bronze_raw_links → bronze_raw_html → silver_extracted_content → silver_summaries
  - Cache behavior: First run downloads HTML, second run uses cache (file-existence check)
  - Reprocessing scenario: Delete silver artifacts → re-run from bronze cache
  - Job execution: manual_pipeline and monitoring_pipeline work with new architecture
  - Test restructure: pytest discovery finds all tests in new structure
- **Framework:** pytest with Dagster test utilities
- **Location:** `tests/integration/`
- **Markers:** `@pytest.mark.integration`

**2. Unit Tests (Optional - only for complex logic)**
- **Scope:** Isolated component behavior where complexity warrants it
- **Coverage (if implemented):**
  - IOManager serialization/deserialization logic (if complex)
  - Hash generation and timestamp handling (if issues arise)
- **Framework:** pytest
- **Location:** `tests/resources/`, `tests/ops/`
- **Markers:** `@pytest.mark.unit`
- **Note:** Not required initially; add only if integration tests reveal need for isolated testing

**3. Contract Tests (Existing)**
- **Scope:** External API verification
- **Coverage:** OpenRouter API integration (unchanged from existing tests)
- **Framework:** pytest
- **Markers:** `@pytest.mark.contract`

**Test Frameworks and Tools:**

- **pytest 8.4.2+**: Main testing framework
- **pytest-mock 3.15.1+**: Mocking file system operations if needed
- **Dagster test utilities**: `build_asset_context`, `materialize` for asset testing

**Coverage of Acceptance Criteria:**

| AC | Test Type | Test File(s) | Key Scenarios |
|----|-----------|--------------|---------------|
| AC1-AC2 | Integration | test_pipeline_integration.py | Bronze and silver IOManagers work end-to-end |
| AC3 | Integration | test_pipeline_integration.py | File-existence cache checks (hit/miss behavior) |
| AC4 | Integration | test_jobs.py | Asset execution with IOManagers |
| AC5 | Integration | test_pipeline_integration.py | HTML download → cache → reprocess from cache |
| AC6-AC8 | Integration | test_pipeline_integration.py | Full hashes, timestamps, lineage in saved artifacts |
| AC9 | Integration | test_pipeline_integration.py | .md and .json file creation for summaries |
| AC10 | Integration | All tests | Verify pytest discovers tests in new structure |
| AC11 | Unit (Optional) | test_*_io_manager.py | IOManager logic if complexity warrants |
| AC12 | Manual | N/A | Documentation review |
| AC13 | Integration | test_jobs.py | Job execution preserves user workflow |

**Edge Cases to Test:**

1. **HTTP download failures:** Verify error metadata stored in bronze layer
2. **Empty link lists:** bronze_raw_links returns empty list → pipeline completes gracefully
3. **Duplicate URLs across multiple runs:** File exists in cache → download skipped
4. **Malformed URLs:** Handle gracefully with error metadata
5. **Large HTML files:** Verify IOManager handles large content correctly
6. **Special characters in URLs:** Hash generation handles correctly
7. **Failed summarization:** Markdown error format generated correctly

**Test Execution:**

```bash
# Run all tests
uv run pytest

# Run only unit tests (fast)
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run with coverage report
uv run pytest --cov=dagster_project --cov-report=term-missing
```

**Quality Gates:**

- All integration tests must pass before marking story complete
- Unit tests (if implemented) must pass
- No test coverage percentage requirement (per PRD NFR guidance)
- Focus on integration tests for end-to-end validation
- `make check` must pass (format, lint, typecheck, test)
