# ailabbrains - Epic Breakdown

**Author:** BMad
**Date:** 2025-11-02
**Project Level:** 2
**Target Scale:** Level 2 (1-2 epics, 5-15 stories total)

---

## Overview

This document provides the detailed epic breakdown for ailabbrains, expanding on the high-level epic list in the [PRD](./PRD.md).

Each epic includes:

- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**

- Epic 1 establishes foundational infrastructure and initial functionality
- Subsequent epics build progressively, each delivering significant end-to-end value
- Stories within epics are vertically sliced and sequentially ordered
- No forward dependencies - each story builds only on previous work

---

## Epic 1: Medallion Architecture Migration

### Expanded Goal

Migrate the DeepRock pipeline from a simple asset-oriented architecture to a medallion architecture with bronze and silver layers, implementing Dagster IOManagers for proper data management. This refactoring will enable efficient data reprocessing through HTML caching, improve data integrity with full hashes and timestamps, enhance testing structure to mirror code organization, and produce human-readable markdown summaries. The epic delivers a production-ready pipeline following Dagster best practices while preserving all existing functionality.

This work builds the foundation for future scalability by separating raw data (bronze) from application-ready data (silver), enabling reprocessing scenarios without re-downloading content, and establishing patterns for consistent testing and data management.

---

### Story Breakdown

**Story 1.1: Define Bronze and Silver Layer Structure**

As a developer,
I want to define the bronze and silver layer directory structure and naming conventions,
So that we have a clear foundation for organizing assets by data maturity level.

**Acceptance Criteria:**
1. Bronze layer directory created at `artifacts/bronze/` with subdirectories for `raw_links/` and `raw_html/`
2. Silver layer directory created at `artifacts/silver/` with subdirectories for `extracted_content/` and `summaries/`
3. Layer structure documented in development guide or architecture docs
4. Asset naming convention established (e.g., `bronze_raw_links`, `silver_extracted_content`)

**Prerequisites:** None

---

**Story 1.2: Implement Bronze Layer IOManager**

As a developer,
I want to implement a Bronze IOManager for raw data persistence,
So that raw links and HTML content are properly serialized and stored following Dagster patterns.

**Acceptance Criteria:**
1. `BronzeIOManager` class created in `dagster_project/resources/io_managers.py`
2. Handles serialization/deserialization of raw link lists (JSON format)
3. Handles storage of raw HTML content with metadata
4. Uses full SHA256 hash for filename generation
5. Includes `created_at` timestamp in all artifacts
6. Unit tests verify serialization/deserialization behavior
7. Integration test verifies file storage and retrieval

**Prerequisites:** Story 1.1

---

**Story 1.3: Implement Silver Layer IOManager**

As a developer,
I want to implement a Silver IOManager for processed data persistence,
So that extracted content and summaries are properly managed with content-type awareness.

**Acceptance Criteria:**
1. `SilverIOManager` class created in `dagster_project/resources/io_managers.py`
2. Handles storage of extracted content (HTML and video types)
3. Handles storage of summaries in both JSON and markdown formats
4. Uses full SHA256 hash for filename generation
5. Includes `created_at` and `updated_at` timestamps in all artifacts
6. Supports data lineage metadata (source asset references, transformation timestamps)
7. Unit tests verify content-type handling and metadata preservation
8. Integration test verifies file storage and retrieval for both content types

**Prerequisites:** Story 1.2

---

**Story 1.4: Migrate Link Ingestion to Bronze Layer**

As a developer,
I want to migrate the link_ingestion asset to use the Bronze IOManager,
So that raw links from manual_links.txt and monitoring_list.txt are stored as bronze layer assets.

**Acceptance Criteria:**
1. `link_ingestion` asset renamed to `bronze_raw_links`
2. Asset configured to use `BronzeIOManager`
3. Asset outputs list of links with metadata (source, discovered_at, watcher_type)
4. Raw links stored in `artifacts/bronze/raw_links/` with full hash filenames
5. Existing deduplication logic preserved
6. Integration test verifies link ingestion and bronze storage
7. Manual and monitoring pipelines work with new asset

**Prerequisites:** Story 1.3

---

**Story 1.5: Add Raw HTML Download to Bronze Layer**

As a developer,
I want to download and cache raw HTML as a bronze layer asset,
So that content can be reprocessed without re-downloading from source URLs.

**Acceptance Criteria:**
1. New asset `bronze_raw_html` created that depends on `bronze_raw_links`
2. Downloads raw HTML for each link using httpx
3. Stores raw HTML with metadata (url, download_timestamp, status_code, headers)
4. Uses `BronzeIOManager` for storage in `artifacts/bronze/raw_html/`
5. Handles HTTP errors gracefully (stores error metadata)
6. Uses full SHA256 hash of URL for filename
7. Integration test verifies HTML download and storage
8. Existing content extraction can read from bronze cache

**Prerequisites:** Story 1.4

---

**Story 1.6: Migrate Content Extraction to Silver Layer**

As a developer,
I want to migrate content extraction to use raw HTML from bronze and output to silver layer,
So that extracted content is properly layered and can be reprocessed from cached HTML.

**Acceptance Criteria:**
1. `content_extraction` asset renamed to `silver_extracted_content`
2. Asset depends on `bronze_raw_html` instead of fetching URLs directly
3. Asset configured to use `SilverIOManager`
4. HTML extractor op reads from bronze cache
5. YouTube extractor continues to use yt-dlp (no HTML caching for videos)
6. Extracted content includes full metadata with timestamps and lineage
7. Content stored in `artifacts/silver/extracted_content/` with full hash filenames
8. Integration test verifies end-to-end flow from bronze HTML to silver content
9. Reprocessing test confirms can regenerate silver from bronze without re-download

**Prerequisites:** Story 1.5

---

**Story 1.7: Migrate Summarization to Silver Layer**

As a developer,
I want to migrate summarization to output silver layer assets,
So that summaries are properly layered with full metadata and lineage tracking.

**Acceptance Criteria:**
1. `summaries` asset renamed to `silver_summaries`
2. Asset depends on `silver_extracted_content`
3. Asset configured to use `SilverIOManager`
4. Summaries include full metadata (timestamps, lineage to source assets)
5. Summaries stored in `artifacts/silver/summaries/` with full hash filenames
6. Success and failure summary formats preserved
7. Integration test verifies end-to-end pipeline bronze → silver content → silver summaries
8. Manual and monitoring pipelines work with new asset structure

**Prerequisites:** Story 1.6

---

**Story 1.8: Generate Markdown Summary Files**

As a user,
I want summaries to be generated as markdown files in addition to JSON,
So that I can easily read and review summaries without parsing JSON.

**Acceptance Criteria:**
1. `SilverIOManager` saves summaries as both `.json` and `.md` files
2. Markdown format includes title, URL, summary content, and metadata footer
3. Markdown files stored alongside JSON in `artifacts/silver/summaries/`
4. Filename uses same full hash as JSON (e.g., `{hash}.md` and `{hash}.json`)
5. Failed summaries also get markdown format showing error details
6. Integration test verifies both JSON and markdown files are created
7. Sample markdown output is human-readable and well-formatted

**Prerequisites:** Story 1.7

---

**Story 1.9: Restructure Tests to Mirror Code Organization**

As a developer,
I want to reorganize tests to mirror the dagster_project structure,
So that tests are easy to discover and maintain alongside their corresponding code.

**Acceptance Criteria:**
1. Test directories created: `tests/assets/`, `tests/ops/`, `tests/resources/`, `tests/jobs/`
2. Existing tests moved to appropriate directories:
   - `test_link_ingestion.py` → `tests/assets/`
   - `test_html_extractor.py` → `tests/ops/`
   - `test_youtube_extractor.py` → `tests/ops/`
   - `test_openai.py` → `tests/resources/`
   - `test_jobs.py` → `tests/jobs/`
   - `test_pipeline_integration.py` → `tests/integration/`
3. Tests updated to reference new asset and IOManager names
4. All tests pass with new structure
5. `pytest` discovery works correctly with new structure
6. Test markers (unit, integration) preserved

**Prerequisites:** Story 1.8

---

**Story 1.10: Add Tests for Bronze IOManager**

As a developer,
I want comprehensive tests for the Bronze IOManager,
So that raw data persistence is verified and reliable.

**Acceptance Criteria:**
1. Unit test file created: `tests/resources/test_bronze_io_manager.py`
2. Tests verify link list serialization/deserialization
3. Tests verify raw HTML storage with metadata
4. Tests verify full SHA256 hash filename generation
5. Tests verify timestamp creation
6. Tests verify error handling for invalid data
7. All tests pass

**Prerequisites:** Story 1.9

---

**Story 1.11: Add Tests for Silver IOManager**

As a developer,
I want comprehensive tests for the Silver IOManager,
So that processed data persistence is verified and reliable.

**Acceptance Criteria:**
1. Unit test file created: `tests/resources/test_silver_io_manager.py`
2. Tests verify extracted content storage for HTML and video types
3. Tests verify summary storage in JSON and markdown formats
4. Tests verify full SHA256 hash filename generation
5. Tests verify timestamp creation and updates
6. Tests verify data lineage metadata preservation
7. Tests verify error handling for invalid data
8. All tests pass

**Prerequisites:** Story 1.10

---

**Story 1.12: Update Documentation for Medallion Architecture**

As a developer,
I want updated documentation explaining the medallion architecture,
So that the new layer structure and IOManagers are well-documented for future development.

**Acceptance Criteria:**
1. `docs/architecture.md` updated with medallion architecture section
2. Bronze and silver layer responsibilities clearly documented
3. IOManager usage patterns documented
4. Data flow diagrams updated to show bronze → silver progression
5. File naming conventions (full hash) documented
6. Metadata requirements (timestamps, lineage) documented
7. Testing structure (mirrored organization) documented
8. Reprocessing workflow documented (using bronze cache)

**Prerequisites:** Story 1.11

---

## Story Guidelines Reference

**Story Format:**

```
**Story [EPIC.N]: [Story Title]**

As a [user type],
I want [goal/desire],
So that [benefit/value].

**Acceptance Criteria:**
1. [Specific testable criterion]
2. [Another specific criterion]
3. [etc.]

**Prerequisites:** [Dependencies on previous stories, if any]
```

**Story Requirements:**

- **Vertical slices** - Complete, testable functionality delivery
- **Sequential ordering** - Logical progression within epic
- **No forward dependencies** - Only depend on previous work
- **AI-agent sized** - Completable in 2-4 hour focused session
- **Value-focused** - Integrate technical enablers into value-delivering stories

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.
