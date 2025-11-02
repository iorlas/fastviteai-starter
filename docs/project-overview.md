# Project Overview - DeepRock

**Generated:** 2025-11-02
**Scan Level:** Quick
**Project Type:** Data Pipeline

---

## Project Summary

**Name:** deeprock

**Description:** Content processing pipeline that ingests links from various sources, extracts content, and generates AI-powered summaries.

**Purpose:** Aggregate knowledge from various online sources (articles, videos, RSS feeds) using LLMs to create concise, structured summaries for later review.

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Repository Type** | Monolith (single cohesive codebase) |
| **Primary Language** | Python 3.12+ |
| **Framework** | Dagster 1.12.0+ (data orchestration) |
| **Architecture** | DAG-based ETL Pipeline |
| **Entry Point** | `dagster_project/definitions.py` |
| **Test Framework** | pytest 8.4.2+ |
| **Storage** | File-based (JSON artifacts) |

---

## Technology Stack Summary

### Core Technologies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Orchestration** | Dagster | 1.12.0+ | ETL pipeline framework |
| **Language** | Python | 3.12+ | Runtime and development |
| **LLM Integration** | OpenAI (OpenRouter) | 1.0.0+ | GPT-4o summarization |
| **Data Validation** | Pydantic | 2.12.2+ | Schema validation |

### Specialized Libraries

| Library | Purpose |
|---------|---------|
| BeautifulSoup4 | HTML content parsing |
| yt-dlp | YouTube metadata extraction |
| feedparser | RSS/Atom feed monitoring |
| structlog | Structured logging |
| pytest | Testing framework |
| ruff | Linting and formatting |

---

## Architecture Classification

**Pattern:** Asset-Oriented DAG Pipeline

**Type:** Extract → Transform → Load (ETL)

**Stages:**
1. **Extract:** Link ingestion from files and watchers
2. **Transform:** Content extraction (HTML/YouTube)
3. **Load:** LLM summarization and storage

**Key Characteristics:**
- Asset-based data lineage
- Declarative dependencies
- Time-based scheduling
- Idempotent operations (deduplication)

---

## Repository Structure

```
deeprock/                          # Monolithic repository
├── dagster_project/               # Main pipeline implementation
│   ├── definitions.py             # [ENTRY POINT]
│   ├── assets/                    # ETL data assets
│   ├── jobs/                      # Pipeline workflows
│   ├── schedules/                 # Automated scheduling
│   ├── ops/                       # Reusable operations
│   └── resources/                 # External integrations
├── tests/                         # Test suite
├── artifacts/                     # Pipeline outputs
└── docs/                          # Documentation
```

**Total Parts:** 1 (monolithic data pipeline)

---

## Features

✅ **Link Ingestion**
- Manual input via `manual_links.txt`
- Automated monitoring via `monitoring_list.txt`
- RSS/Atom feed discovery

✅ **Content Extraction**
- HTML article extraction (BeautifulSoup4)
- YouTube video metadata (yt-dlp)
- Content cleaning and structuring

✅ **AI Summarization**
- LLM-powered summaries (GPT-4o)
- OpenRouter API integration
- Metadata tracking (tokens, latency)

✅ **Automated Scheduling**
- 6-hour monitoring schedule
- Background RSS feed monitoring

✅ **Extensible Architecture**
- Watcher protocol for new sources
- Pluggable extractors
- Resource-based integrations

---

## Documentation Links

### Generated Documentation

- **[Architecture](/docs/architecture.md)** - Comprehensive architecture overview
- **[Source Tree Analysis](/docs/source-tree-analysis.md)** - Annotated directory structure
- **[Development Guide](/docs/development-guide.md)** - Setup and development workflow
- **[Data Models](/docs/data-models.md)** - File-based storage structure

### Existing Documentation

- **[README.md](/README.md)** - Project README and usage instructions
- **[Technical Specification](/docs/tech-spec.md)** - Detailed technical specification
- **[Epic Breakdown](/docs/epics.md)** - User stories and epic planning
- **[Development Notes](/docs/NOTES.md)** - Development notes and decisions

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

# 3. Start Dagster development server
uv run dagster dev

# 4. Access Dagster UI
# Open http://localhost:3000 in browser
```

### Processing Links

**Manual processing:**
```bash
echo "https://example.com/article" >> manual_links.txt
# Trigger manual_pipeline in Dagster UI
```

**Automated monitoring:**
```bash
echo "https://news.ycombinator.com/rss" >> monitoring_list.txt
# Runs automatically every 6 hours
```

---

## Development Workflow

**Quality checks:**
```bash
make check    # Format, lint, typecheck, test
```

**Testing:**
```bash
uv run pytest              # All tests
uv run pytest -m unit      # Unit tests only
uv run pytest -m integration  # Integration tests only
```

**See:** [Development Guide](/docs/development-guide.md)

---

## Key Metrics

**Lines of Code:** ~2,500 (estimated from file count)

**Test Files:** 9
- Unit tests: 7
- Integration tests: 2

**Pipeline Components:**
- Assets: 3
- Jobs: 2
- Schedules: 1
- Ops: 3
- Resources: 1

**Documentation Files:** 8 (generated + existing)

---

## Known Limitations

1. **YouTube Transcripts:** Currently uses video descriptions instead of actual transcripts
2. **Deployment:** No containerization or CI/CD configuration
3. **Storage:** File-based only (no database)
4. **Authentication:** None (local development only)

---

## External Dependencies

**Required Services:**
- OpenRouter API (https://openrouter.ai) - LLM summarization

**Optional Services:**
- None currently

---

## Support & Resources

**Documentation:**
- Project README: `/README.md`
- Architecture: `/docs/architecture.md`
- Development Guide: `/docs/development-guide.md`

**External Resources:**
- Dagster Documentation: https://docs.dagster.io
- OpenRouter API: https://openrouter.ai/docs

---

## Project Status

**Version:** 0.1.0

**Status:** Active Development

**Last Updated:** 2025-11-02
