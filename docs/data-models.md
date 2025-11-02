# Data Models - DeepRock

**Project:** deeprock
**Type:** Data Pipeline
**Storage:** File-based (JSON)
**Generated:** 2025-11-02

---

## Overview

DeepRock uses a **file-based storage architecture** for pipeline artifacts. All data is stored as JSON files in the `artifacts/` directory, organized by content type. This approach provides simplicity and transparency for the current scale, with no database required.

---

## Storage Architecture

### Directory Structure

```
artifacts/
├── html/                      # Extracted HTML content
│   └── {url_hash}.json       # SHA256(url)[:16]
├── videos/                    # YouTube video metadata
│   └── {url_hash}.json       # SHA256(url)[:16]
└── summaries/                 # LLM-generated summaries
    └── {url_hash}.json       # SHA256(url)[:16]
```

### Naming Convention

**File Naming:** `{url_hash}.json`

**Hash Function:** SHA256(url)[:16] (first 16 characters)

**Purpose:**
- Unique identifier for each URL
- Filesystem-safe naming
- Deduplication mechanism

**Example:**
```python
import hashlib

url = "https://example.com/article"
url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
# Result: "50d858e0985ecc7f"
# File: artifacts/summaries/50d858e0985ecc7f.json
```

---

## Data Schemas

### 1. Extracted HTML Content

**Location:** `artifacts/html/{url_hash}.json`

**Schema:**
```json
{
  "url": "https://example.com/article",
  "type": "html",
  "title": "Article Title",
  "content": "Cleaned article text...",
  "extracted_at": "2025-11-02T12:34:56Z",
  "metadata": {
    "author": "John Doe",
    "published_date": "2025-11-01",
    "word_count": 1500,
    "source_domain": "example.com"
  }
}
```

**Fields:**
- `url` (string): Original article URL
- `type` (string): Always "html"
- `title` (string): Extracted article title
- `content` (string): Cleaned body text (scripts/styles removed)
- `extracted_at` (ISO 8601): Extraction timestamp
- `metadata` (object): Additional extracted information
  - `author` (string, optional): Article author
  - `published_date` (string, optional): Publication date
  - `word_count` (integer): Content word count
  - `source_domain` (string): Source website domain

---

### 2. YouTube Video Metadata

**Location:** `artifacts/videos/{url_hash}.json`

**Schema:**
```json
{
  "url": "https://youtube.com/watch?v=abc123",
  "type": "youtube",
  "title": "Video Title",
  "content": "Video description text...",
  "extracted_at": "2025-11-02T12:34:56Z",
  "metadata": {
    "channel": "Channel Name",
    "published_date": "2025-10-15",
    "duration": 600,
    "view_count": 10000,
    "video_id": "abc123"
  }
}
```

**Fields:**
- `url` (string): YouTube video URL
- `type` (string): Always "youtube"
- `title` (string): Video title
- `content` (string): Video description (transcript not available currently)
- `extracted_at` (ISO 8601): Extraction timestamp
- `metadata` (object): Video information
  - `channel` (string, optional): Channel name
  - `published_date` (string, optional): Upload date
  - `duration` (integer, optional): Video length in seconds
  - `view_count` (integer, optional): View count
  - `video_id` (string): YouTube video ID

**Note:** Current implementation uses video description instead of actual transcript (known limitation).

---

### 3. Summary (Success)

**Location:** `artifacts/summaries/{url_hash}.json`

**Schema (Successful Summarization):**
```json
{
  "url": "https://example.com/article",
  "status": "success",
  "summary": "• Key point 1\n• Key point 2\n• Key point 3",
  "model": "openai/gpt-4o",
  "tokens_used": 450,
  "latency_ms": 1200,
  "processed_at": "2025-11-02T12:35:30Z"
}
```

**Fields:**
- `url` (string): Original URL
- `status` (string): Always "success" for successful runs
- `summary` (string): LLM-generated summary (3-5 bullet points)
- `model` (string): LLM model used (e.g., "openai/gpt-4o")
- `tokens_used` (integer): Total tokens consumed (prompt + completion)
- `latency_ms` (integer): API call duration in milliseconds
- `processed_at` (ISO 8601): Summarization timestamp

---

### 4. Summary (Failure)

**Location:** `artifacts/summaries/{url_hash}.json`

**Schema (Failed Summarization):**
```json
{
  "url": "https://example.com/article",
  "status": "failed",
  "error": "OpenRouter API error: rate limit exceeded",
  "error_type": "RateLimitError",
  "processed_at": "2025-11-02T12:35:30Z",
  "retry_count": 3
}
```

**Fields:**
- `url` (string): Original URL
- `status` (string): Always "failed" for failed runs
- `error` (string): Human-readable error message
- `error_type` (string): Error classification (e.g., "RateLimitError", "APIError")
- `processed_at` (ISO 8601): Failure timestamp
- `retry_count` (integer): Number of retry attempts before failure

**Note:** Failed summaries are still saved to prevent infinite retry loops. Delete the summary file to force retry.

---

## Deduplication Logic

### How It Works

**Check:** Before processing a URL, check if summary file exists

**File Path:** `artifacts/summaries/{url_hash}.json`

**Logic:**
```python
if summary_file_exists(url_hash):
    # Skip processing (already done or permanently failed)
    pass
else:
    # Process the URL
    process_link(url)
```

**Implications:**
- Prevents duplicate processing
- Both successful and failed summaries are preserved
- No automatic retry for failed links
- Manual intervention required to retry (delete summary file)

### Retry Process

**To retry a failed or outdated summary:**

```bash
# 1. Find the summary file
cd artifacts/summaries/

# 2. Delete the summary
rm {url_hash}.json

# 3. Re-trigger pipeline
# The URL will be reprocessed on next run
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────┐
│                INPUT SOURCES                         │
│  manual_links.txt, monitoring_list.txt              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│     ASSET: raw_links (link_ingestion)              │
│  • Read input files                                │
│  • Check summaries/ for existing files             │
│  • Return only new URLs                            │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  ASSET: extracted_content (content_extraction)     │
│  • Dispatch to html_extractor or youtube_extractor │
│  • Save to artifacts/html/ or artifacts/videos/    │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│     ASSET: summaries (summarization)               │
│  • Call OpenRouter API (GPT-4o)                    │
│  • Save to artifacts/summaries/                    │
│  • Status: "success" or "failed"                   │
└────────────────────────────────────────────────────┘
```

---

## Storage Characteristics

**Advantages:**
- ✅ Simple, transparent storage
- ✅ No database setup required
- ✅ Easy to inspect (human-readable JSON)
- ✅ File-level versioning possible (git, backups)
- ✅ Fast deduplication (file existence check)

**Limitations:**
- ❌ No query capabilities (full scan required)
- ❌ No relational data (no foreign keys)
- ❌ Manual cleanup for failed retries
- ❌ Limited scalability (filesystem constraints)
- ❌ No atomic transactions

---

## Validation

**Schema Validation:** Pydantic models (inferred, not explicitly defined in codebase)

**File Format:** JSON (UTF-8 encoding)

**Size Limits:** None enforced (filesystem-dependent)

---

## Future Enhancements

### Database Migration

**Potential Architecture:**
```
PostgreSQL
├── links table
│   └── url, source, discovered_at, status
├── content table
│   └── link_id, type, title, content, extracted_at
└── summaries table
    └── link_id, summary, model, tokens, status
```

**Benefits:**
- Query capabilities (filtering, search)
- Relational data (foreign keys, joins)
- Better concurrency control
- Atomic transactions
- Improved scalability

**Migration Path:**
1. Define database schemas
2. Create migration script (read JSON → insert DB)
3. Update Dagster assets to use DB resources
4. Keep files as backup/archive

---

## Data Retention

**Current Policy:** Indefinite retention (no automatic cleanup)

**Manual Cleanup:**
```bash
# Remove old summaries (example: older than 90 days)
find artifacts/summaries/ -type f -mtime +90 -delete

# Remove failed summaries only
# (requires parsing JSON to check status)
```

**Future Considerations:**
- Configurable retention policies
- Archive old summaries
- Cleanup failed summaries automatically

---

## References

- **Architecture:** [/docs/architecture.md](/docs/architecture.md)
- **Development Guide:** [/docs/development-guide.md](/docs/development-guide.md)
- **Source Tree:** [/docs/source-tree-analysis.md](/docs/source-tree-analysis.md)
