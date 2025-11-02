# ailabbrains Product Requirements Document (PRD)

**Author:** BMad
**Date:** 2025-11-02
**Project Level:** 2
**Target Scale:** Level 2 (1-2 epics, 5-15 stories total)

---

## Goals and Background Context

### Goals

1. **Implement medallion architecture in Dagster** - Migrate from simple asset pipeline to bronze/silver/gold layered architecture following data engineering best practices

2. **Improve data management and durability** - Introduce proper IOManagers, timestamp tracking, raw HTML caching, and full-hash filenames for robust data handling

3. **Enhance maintainability and output quality** - Restructure tests to mirror code organization and generate markdown summaries for better readability

### Background Context

DeepRock is a Dagster-based content processing pipeline that ingests links from various sources (manual input, RSS feeds), extracts content, and generates AI-powered summaries. The current implementation uses a simple asset-oriented architecture with file-based storage.

As the pipeline matures, several architectural and operational issues have emerged: lack of proper data layering makes it difficult to reprocess data without re-downloading, file-based storage lacks proper caching and timestamp tracking, test organization doesn't reflect code structure, and output summaries in JSON format are not optimal for human review. This refactoring addresses these issues by introducing medallion architecture (bronze/silver/gold layers), implementing Dagster IOManagers for proper data management, improving testing structure, and enhancing data artifacts with timestamps, caching, and better output formats.

---

## Requirements

### Functional Requirements

#### Data Architecture & Layers

**FR001:** Implement bronze layer for raw data - all input sources (manual_links.txt, monitoring_list.txt content) and raw HTML downloads must be materialized as bronze layer assets

**FR002:** Implement silver layer for processed application-ready data - content extraction outputs (HTML, YouTube) AND summaries stored as silver layer assets with validation

**FR003:** Implement IOManager for bronze layer - handle file-based storage with proper serialization/deserialization for raw links and raw HTML content

**FR004:** Implement IOManager for silver layer - manage extracted content and summary storage with content-type aware handling (HTML/video/markdown)

#### Data Management & Persistence

**FR005:** Store raw HTML content as intermediate artifact - cache downloaded HTML in bronze layer to enable reprocessing without re-downloading

**FR006:** Use full SHA256 hash as filename - replace truncated hash [:16] with full hash to eliminate potential future collisions

**FR007:** Add timestamps to all artifacts - every JSON artifact must include `created_at` and `updated_at` timestamp fields

**FR008:** Preserve data lineage metadata - each layer must track source asset references and transformation timestamps

#### Testing Infrastructure

**FR009:** Restructure test folders to mirror code organization - tests should be organized by component type (tests/ops/, tests/assets/, tests/resources/) matching dagster_project structure

**FR010:** Implement test discovery by component - each op/asset/resource should have corresponding test file in mirrored location

#### Output & Reporting

**FR011:** Generate markdown summary files - summaries must be saved as .md files in addition to JSON for improved human readability

### Non-Functional Requirements

**NFR001:** **Dagster Best Practices Compliance** - All IOManagers and asset layers must follow Dagster's recommended patterns for medallion architecture and resource management

**NFR002:** **Test Coverage for Complex Logic** - Critical components (IOManagers, data transformations, hash generation) must have focused unit or integration tests to verify correct behavior

**NFR003:** **Data Integrity** - All artifacts must include required metadata (timestamps, full hashes) to ensure data can be traced and validated

---

## Epic List

**Epic 1: Medallion Architecture Migration**

Migrate DeepRock pipeline to medallion architecture (bronze/silver layers) with proper IOManagers, enhanced data artifacts (timestamps, full hashes, HTML caching), markdown output, and restructured testing.

**Estimated Stories:** 12-15

**Delivers:** Fully refactored pipeline following Dagster best practices with improved data management, caching capabilities, and maintainability

> **Note:** Detailed epic breakdown with full story specifications is available in [epics.md](./epics.md)

---

## Out of Scope

**Deferred to Future Phases:**
- Gold layer implementation - reserved for future aggregations, analytics, or curated collections
- Database integration - continue using file-based persistence via Dagster IOManagers; database migration is a separate effort
- Additional watcher implementations (Reddit, Twitter, HackerNews) - focus on architectural refactoring only
- YouTube transcript extraction improvements - existing description-based approach remains unchanged
- Deployment infrastructure (Docker, CI/CD) - local development environment only

**Not Addressed:**
- API development - remains a data pipeline without web service endpoints
- Real-time processing - maintain existing batch/scheduled processing model
- User authentication or multi-tenancy - single-user local development setup

**Clarifications:**
- This is architectural refactoring only - no new content sources or extraction capabilities
- Existing functionality (RSS watching, link ingestion, summarization) preserved but restructured
- File-based persistence using Dagster IOManagers is the target architecture, not a limitation
