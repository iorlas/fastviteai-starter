# DeepRock - Epic Breakdown

## Epic Overview

**Epic:** Link Processing Pipeline

**Slug:** link-pipeline

**Goal:** Build a Dagster-based ETL pipeline that ingests links, extracts content from HTML articles and YouTube videos, generates LLM summaries, and stores artifacts for later review.

**Scope:**
- Manual link ingestion via text files
- Automated monitoring of RSS feeds and Reddit sources (6-hour schedule)
- Content extraction for HTML pages and YouTube videos
- OpenRouter integration for summarization
- MLFlow tracking for LLM evaluation
- File-based storage with deduplication

**Success Criteria:**
- Links can be added to `manual_links.txt` and processed end-to-end
- HTML articles are extracted and summarized correctly
- YouTube videos are transcribed and summarized correctly
- All summaries tracked via Dagster metadata (model, tokens, latency)
- Monitoring schedule runs every 6 hours automatically
- Duplicate and failed links are skipped automatically
- Failed links tracked with error details (manual deletion to retry)
- Dagster UI accessible for pipeline monitoring

**Dependencies:** None (greenfield project)

---

## Epic Details

### Story Map

```
Epic: Link Processing Pipeline
├── Story 1: Project Foundation & Resources (1.5 points)
├── Story 2: Core ETL Pipeline (3.5 points)
└── Story 3: Watchers & Polish (2 points)
```

**Total Story Points:** 7
**Estimated Timeline:** 3-5 days (1-2 points per day typical)

### Implementation Sequence

1. **Story 1** → Set up Dagster project, resources, storage
2. **Story 2** → Implement pipeline assets (depends on Story 1)
3. **Story 3** → Add watchers and production features (depends on Story 2)

---

## Story Summaries

### Story 1: Project Foundation & Resources

**Goal:** Bootstrap Dagster project with all infrastructure needed for development

**Key Deliverables:**
- Dagster project structure via `dagster project scaffold`
- Dependencies installed via `uv add`
- Input files created (manual_links.txt, monitoring_list.txt)
- OpenRouter resource implemented
- Environment configuration
- Dagster UI running

**Estimated Effort:** 1.5 points (2-3 hours)

---

### Story 2: Core ETL Pipeline

**Goal:** Implement complete end-to-end link processing pipeline

**Key Deliverables:**
- Link ingestion asset (read files, dedupe via summary file check)
- Content extraction asset (HTML + YouTube, auto-create directories)
- Summarization asset (OpenRouter integration, save with status tracking)
- Manual and monitoring jobs (separate triggers for different inputs)
- 6-hour schedule for monitoring

**Estimated Effort:** 3.5 points (6-8 hours)

---

### Story 3: Watchers & Polish

**Goal:** Add RSS watcher with extensible architecture and minimal polish

**Key Deliverables:**
- Watcher protocol/interface (for future extensibility)
- RSS watcher implementation (feedparser)
- Watcher integration into link_ingestion asset
- Essential E2E integration test
- Minimal documentation (setup + usage)
- Example monitoring_list.txt

**Estimated Effort:** 2 points (3-4 hours)

---

## Notes

- All stories depend sequentially (no parallel work)
- Each story leaves system in working, testable state
- Tech spec provides detailed implementation guidance
- Story files located in: `docs/stories/`
