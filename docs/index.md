# DeepRock - Project Documentation Index

**Project:** deeprock
**Type:** Data Pipeline (Dagster ETL)
**Repository:** Monolithic
**Generated:** 2025-11-02
**Scan Level:** Quick

---

## Project Overview

**Description:** Content processing pipeline that ingests links from various sources, extracts content, and generates AI-powered summaries.

**Purpose:** Aggregate knowledge from online sources (articles, videos, RSS feeds) using LLMs to create concise, structured summaries.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Repository Type** | Monolith (single cohesive codebase) |
| **Primary Language** | Python 3.12+ |
| **Architecture** | DAG-based ETL Pipeline |
| **Entry Point** | `dagster_project/definitions.py` |
| **Tech Stack** | Dagster + OpenAI + BeautifulSoup + yt-dlp + feedparser |

**Key Components:**
- **Assets:** 3 (link_ingestion, content_extraction, summarization)
- **Jobs:** 2 (manual_pipeline, monitoring_pipeline)
- **Schedules:** 1 (6-hour monitoring)
- **Storage:** File-based artifacts (JSON)

---

## Generated Documentation

**Core Documentation:**
- [Project Overview](./project-overview.md) - Executive summary and quick start
- [Architecture](./architecture.md) - Comprehensive architecture documentation
- [Source Tree Analysis](./source-tree-analysis.md) - Annotated directory structure
- [Development Guide](./development-guide.md) - Setup and development workflow
- [Data Models](./data-models.md) - File-based storage structure

**Additional Documentation:**
- Deployment Guide - _Not applicable (local development only)_
- Contribution Guidelines - _Not applicable (solo developer)_

---

## Existing Documentation

**Project Planning:**
- [README.md](../README.md) - Project README and usage instructions
- [Technical Specification](./tech-spec.md) - Detailed technical specification from planning phase
- [Epic Breakdown](./epics.md) - User stories and epic planning
- [Development Notes](./NOTES.md) - Development notes and decisions

**User Stories:**
- [Story 1: Project Foundation](./stories/story-link-pipeline-1.md)
- [Story 1.1: Project Foundation (Iteration)](./stories/story-link-pipeline-1.1.md)
- [Story 2: Core ETL Pipeline](./stories/story-link-pipeline-2.md)
- [Story 3: Watchers & Polish](./stories/story-link-pipeline-3.md)

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- OpenRouter API key
- uv package manager

### Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenRouter API key

# 3. Create input files
cp manual_links.txt.template manual_links.txt
cp monitoring_list.txt.template monitoring_list.txt

# 4. Start Dagster development server
uv run dagster dev

# 5. Access Dagster UI
# Open http://localhost:3000
```

### Processing Your First Link

**Manual processing:**
```bash
# Add a link
echo "https://example.com/article" >> manual_links.txt

# Trigger manual_pipeline in Dagster UI at http://localhost:3000
# View results in artifacts/summaries/
```

**Automated monitoring:**
```bash
# Add an RSS feed
echo "https://news.ycombinator.com/rss" >> monitoring_list.txt

# Runs automatically every 6 hours
# Or trigger monitoring_pipeline manually in Dagster UI
```

---

## Development Workflow

### Quality Checks

```bash
# Run all checks before committing
make check
```

This runs:
- Code formatting (ruff format)
- Linting (ruff check --fix)
- Type checking (ty check)
- Tests (pytest)

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test types
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
```

**See:** [Development Guide](./development-guide.md) for detailed instructions

---

## Architecture Overview

**Pattern:** Asset-Oriented DAG Pipeline

**Data Flow:**
```
Input Sources → Link Ingestion → Content Extraction → LLM Summarization → File Storage
```

**Key Features:**
- Declarative asset dependencies
- Automatic deduplication
- Time-based scheduling (6-hour monitoring)
- Extensible watcher protocol
- File-based artifact storage

**See:** [Architecture](./architecture.md) for comprehensive details

---

## Directory Structure

```
deeprock/
├── dagster_project/           # Main pipeline implementation
│   ├── definitions.py         # [ENTRY POINT]
│   ├── assets/                # ETL data assets
│   ├── jobs/                  # Pipeline workflows
│   ├── schedules/             # Automated scheduling
│   ├── ops/                   # Reusable operations
│   └── resources/             # External integrations
├── tests/                     # Test suite (9 test files)
├── artifacts/                 # Pipeline outputs
│   ├── html/                  # Extracted HTML
│   ├── videos/                # Video metadata
│   └── summaries/             # LLM summaries
├── docs/                      # Documentation
└── pyproject.toml             # Project configuration
```

**See:** [Source Tree Analysis](./source-tree-analysis.md) for detailed structure

---

## Data Architecture

**Storage Type:** File-based (JSON artifacts)

**Organization:**
- `artifacts/html/{url_hash}.json` - Extracted HTML content
- `artifacts/videos/{url_hash}.json` - YouTube metadata
- `artifacts/summaries/{url_hash}.json` - LLM summaries (success or failure)

**Deduplication:** Summary file existence check

**See:** [Data Models](./data-models.md) for schemas and details

---

## Technology Stack

**Core Technologies:**
- **Dagster 1.12.0+** - Data orchestration framework
- **Python 3.12+** - Runtime and development
- **OpenAI API 1.0.0+** - LLM integration (via OpenRouter)
- **Pydantic 2.12.2+** - Data validation

**Specialized Libraries:**
- **BeautifulSoup4** - HTML parsing
- **yt-dlp** - YouTube metadata extraction
- **feedparser** - RSS/Atom feed parsing
- **structlog** - Structured logging
- **pytest** - Testing framework
- **ruff** - Linting and formatting

**See:** [Architecture](./architecture.md) for complete technology analysis

---

## Known Limitations

1. **YouTube Transcripts:** Currently uses video descriptions instead of actual transcripts
   - **Impact:** Lower quality summaries for videos
   - **Workaround:** Video descriptions are used
   - **Future:** Enable yt-dlp transcript extraction

2. **Deployment:** No containerization or CI/CD configuration
   - **Status:** Local development only
   - **Future:** Docker + CI/CD pipeline

3. **Storage:** File-based only (no database)
   - **Status:** JSON files in artifacts/
   - **Future:** PostgreSQL migration for query capabilities

**See:** [Architecture - Known Limitations](./architecture.md#known-limitations--future-enhancements)

---

## External Dependencies

**Required Services:**
- **OpenRouter API** - LLM summarization
  - URL: https://openrouter.ai
  - Configuration: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`

**No Optional Services**

---

## Key Metrics

- **Test Files:** 9 (7 unit, 2 integration)
- **Pipeline Assets:** 3
- **Pipeline Jobs:** 2
- **Automated Schedules:** 1 (6-hour monitoring)
- **Documentation Files:** 10+ (generated + existing)

---

## Next Steps for Brownfield PRD

When planning new features or refactoring, use this documentation as your foundation:

**For UI-only features:**
- Not applicable (data pipeline project)

**For API-only features:**
- Not applicable (no REST/GraphQL APIs)

**For Data Pipeline Features:**
- Reference: [Architecture](./architecture.md)
- Reference: [Data Models](./data-models.md)
- Reference: [Development Guide](./development-guide.md)

**For Full System Refactoring:**
- Reference: [Project Overview](./project-overview.md)
- Reference: [Architecture](./architecture.md)
- Reference: [Source Tree](./source-tree-analysis.md)

---

## Support & Resources

**Documentation:**
- [README.md](../README.md) - Quick start and usage
- [Development Guide](./development-guide.md) - Development workflow
- [Architecture](./architecture.md) - System architecture

**External Resources:**
- [Dagster Documentation](https://docs.dagster.io)
- [OpenRouter API Docs](https://openrouter.ai/docs)

---

## Document Maintenance

**Last Generated:** 2025-11-02
**Scan Level:** Quick
**Workflow Version:** 1.2.0

**To regenerate documentation:**
```bash
# Re-run document-project workflow
# Will update all generated files
```

**To add specific documentation:**
- Deployment guide: Add Docker/docker-compose configuration first
- Contribution guide: Create CONTRIBUTING.md in project root
- API contracts: Not applicable (data pipeline project)

---

_Generated by BMad document-project workflow_
