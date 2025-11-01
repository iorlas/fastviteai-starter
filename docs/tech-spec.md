# DeepRock - Technical Specification

**Author:** BMad
**Date:** 2025-11-01
**Project Level:** 1
**Project Type:** software
**Development Context:** greenfield

---

## Source Tree Structure

```
deeprock/
├── backend/
│   ├── dagster_project/
│   │   ├── __init__.py
│   │   ├── assets/
│   │   │   ├── __init__.py
│   │   │   ├── link_ingestion.py      # Asset: ingest links from files
│   │   │   ├── content_extraction.py  # Asset: extract HTML/video content
│   │   │   └── summarization.py       # Asset: OpenRouter LLM + file storage
│   │   ├── jobs/
│   │   │   ├── __init__.py
│   │   │   ├── manual_pipeline.py     # Job: process manual links
│   │   │   └── monitoring_pipeline.py # Job: process monitored sources
│   │   ├── schedules/
│   │   │   ├── __init__.py
│   │   │   └── monitoring_schedule.py # Schedule: every 6 hours
│   │   ├── resources/
│   │   │   ├── __init__.py
│   │   │   └── openrouter_client.py   # OpenRouter API client
│   │   ├── ops/
│   │   │   ├── __init__.py
│   │   │   ├── html_extractor.py      # HTML content extraction
│   │   │   ├── youtube_extractor.py   # YouTube transcript extraction
│   │   │   └── watchers.py            # Custom watcher implementations
│   │   └── repository.py              # Dagster repository definition
│   ├── storage/
│   │   ├── input/
│   │   │   ├── manual_links.txt       # Manual link input
│   │   │   └── monitoring_list.txt    # RSS/Reddit monitoring list
│   │   └── artifacts/
│   │       ├── html/                  # Extracted HTML content
│   │       ├── videos/                # Video transcripts
│   │       └── summaries/             # LLM summaries
│   ├── config/
│   │   ├── dagster.yaml              # Dagster configuration
│   │   └── openrouter.yaml           # OpenRouter API configuration
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_assets.py
│   │   └── test_extractors.py
│   ├── pyproject.toml                # Poetry dependency management
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── tech-spec.md
│   └── epics.md
└── README.md
```

---

## Technical Approach

**Pipeline Architecture:**

DeepRock implements a Dagster-based ETL pipeline with two primary ingestion modes:

1. **Manual Mode**: Process links appended to `manual_links.txt` (Docker volume mount)
2. **Monitoring Mode**: Automated 6-hour polling of sources in `monitoring_list.txt` (RSS feeds, Reddit, custom watchers)

**Data Flow:**

```
Input Sources → Link Ingestion → Content Extraction → LLM Summarization → File Storage
                                                            ↓
                                                    Dagster Metadata
```

**Dagster Asset Graph:**

- `raw_links` → Reads from input files
- `extracted_content` → Depends on `raw_links`, extracts HTML/video, saves to artifacts
- `summaries` → Depends on `extracted_content`, calls OpenRouter, saves to artifacts

**Key Design Decisions:**

- Use **Dagster CLI** to scaffold project structure (`dagster project scaffold`)
- Use **uv** for dependency management (consistent with existing README pattern)
- File-based storage initially (no database complexity)
- OpenRouter for LLM access (GPT-4o or similar via unified API)
- Dagster metadata for run tracking and metrics (model, tokens, latency)
- Dagster default retry strategy (exponential backoff)
- Auto-create storage directories in code (no manual setup)
- Custom watcher protocol for future extensibility (MVP: RSS only)
- Minimal testing (essential E2E only) and documentation for MVP

---

## Implementation Stack

**Core Technologies (DEFINITIVE):**

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Runtime | Python | 3.12+ | Consistent with existing setup |
| Package Manager | uv | 0.4.0+ | Fast, reliable dependency management |
| Orchestration | Dagster | 1.7.0+ | Asset-based ETL pipeline + metadata tracking |
| LLM API | OpenRouter | API v1 | Unified LLM access (GPT-4o) |
| HTML Parser | BeautifulSoup4 | 4.12.0+ | HTML content extraction |
| HTTP Client | httpx | 0.27.0+ | Async HTTP requests |
| YouTube Extraction | yt-dlp | 2024.4.9+ | Video transcript extraction |
| RSS Parser | feedparser | 6.0.11+ | RSS feed parsing |
| Process Manager | systemd/supervisor | - | Optional: run as daemon |

**Python Dependencies:**

All dependencies are added via `uv add` commands (see Development Setup section).

Core dependencies:
- dagster 1.7.0+
- dagster-webserver 1.7.0+
- httpx 0.27.0+
- beautifulsoup4 4.12.0+
- yt-dlp 2024.4.9+
- feedparser 6.0.11+
- pydantic 2.7.0+
- python-dotenv 1.0.0+

Dev dependencies:
- pytest 8.0.0+
- pytest-asyncio 0.23.0+
- ruff 0.4.0+

**Environment Variables:**

```bash
OPENROUTER_API_KEY=<your-key>
OPENROUTER_MODEL=openai/gpt-4o
DAGSTER_HOME=./backend/.dagster
```

---

## Technical Details

### 1. Link Ingestion Asset

**Input Files:**
- `backend/storage/input/manual_links.txt` - One URL per line, appended by user
- `backend/storage/input/monitoring_list.txt` - Monitored sources (RSS/Reddit URLs)

**Deduplication:**
- Check if summary file exists: `artifacts/summaries/{url_hash}.json`
- If exists (regardless of status) → skip (already processed or permanently failed)
- If not exists → process the link
- Use SHA256(url)[:16] for url_hash

**Note:** To retry a failed link, manually delete its summary file

**Output:** List of unprocessed link objects with metadata

### 2. Content Extraction Asset

**HTML Extraction (BeautifulSoup4):**
```python
# Extract main content using common selectors
selectors = ["article", "main", ".post-content", "#content"]
# Clean: remove scripts, styles, ads
# Extract: title, body text, publish date, author
```

**YouTube Extraction (yt-dlp):**
```python
# Extract transcript using yt-dlp
yt_dlp_opts = {
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['en']
}
# Fallback: use video description if no transcript
```

**Output Format:**
```json
{
  "url": "...",
  "type": "html|youtube",
  "title": "...",
  "content": "...",
  "extracted_at": "ISO8601",
  "metadata": {
    "author": "...",
    "published_date": "...",
    "word_count": 1234
  }
}
```

### 3. Summarization Asset

**OpenRouter Integration:**
```python
# API endpoint: https://openrouter.ai/api/v1/chat/completions
# Model: openai/gpt-4o (configurable via env var)
# System prompt: "Summarize the following article in 3-5 bullet points..."
# Max tokens: 500
# Temperature: 0.3 (consistent, factual summaries)
```

**Dagster Metadata Tracking:**
- Attach metadata to asset materializations via `context.add_output_metadata()`
- Track: model, prompt (truncated), response (truncated), latency, token count
- View all metadata in Dagster UI under asset runs

**Output Format (Success):**
```json
{
  "url": "...",
  "status": "success",
  "summary": "...",
  "model": "openai/gpt-4o",
  "tokens_used": 450,
  "latency_ms": 1200,
  "processed_at": "ISO8601"
}
```

**Output Format (Failure):**
```json
{
  "url": "...",
  "status": "failed",
  "error": "OpenRouter API error: rate limit exceeded",
  "error_type": "RateLimitError",
  "processed_at": "ISO8601",
  "retry_count": 3
}
```

**Retry Strategy:**
- Use Dagster's default retry mechanism (exponential backoff)
- If all retries exhausted → save failure status to summary file
- Failed links won't be retried in future runs
- Manual recovery: delete failed summary file to force retry

### 4. File Storage

**File Structure:**
```
backend/storage/artifacts/
├── html/
│   └── {url_hash}.json          # Extracted HTML content
├── videos/
│   └── {url_hash}.json          # Video transcripts
└── summaries/
    └── {url_hash}.json          # LLM summaries (success or failure)
```

**URL Hashing:** Use SHA256(url)[:16] for filename

**Directory Auto-Creation:**
- Assets use `Path.mkdir(parents=True, exist_ok=True)` before saving files
- No manual directory setup required

**Summary File Handling:**
- Always create summary file (even on failure)
- Success: includes summary content and metadata
- Failure: includes error details and retry information
- File existence = processed (success or permanently failed)

### 5. Monitoring Schedule

**Dagster Schedule:**
```python
# Runs every 6 hours: 00:00, 06:00, 12:00, 18:00 UTC
@schedule(cron_schedule="0 */6 * * *")
def monitoring_schedule():
    return RunRequest(job_name="monitoring_pipeline")
```

### 6. Custom Watchers (Extensibility)

**Watcher Protocol:**
```python
class Watcher(Protocol):
    def fetch_links(self, source_url: str) -> List[str]:
        """Extract links from a monitored source"""
        ...
```

**MVP Implementation:**
- `RSSWatcher` - Parse RSS feeds using feedparser

**Future Extensions:**
- Additional watchers can be added by implementing the Watcher protocol
- Examples: Reddit, Twitter/X, Hacker News, custom APIs

---

## Development Setup

**Prerequisites:**
- Python 3.12+
- uv package manager (already installed)
- OpenRouter API key

**Step 1: Initialize Dagster Project**

```bash
# Navigate to backend directory
cd backend

# Use Dagster CLI to scaffold project structure
dagster project scaffold --name dagster_project

# This creates the standard Dagster layout with:
# - assets/
# - jobs/
# - schedules/
# - resources/
# - repository.py
```

**Step 2: Install Dependencies**

```bash
# Add core dependencies using uv
uv add dagster
uv add dagster-webserver
uv add httpx
uv add beautifulsoup4
uv add yt-dlp
uv add feedparser
uv add pydantic
uv add python-dotenv

# Add dev dependencies
uv add --dev pytest
uv add --dev pytest-asyncio
uv add --dev ruff
```

**Step 3: Configure Environment**

```bash
# Create .env file
cat > backend/.env << EOF
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_MODEL=openai/gpt-4o
DAGSTER_HOME=./.dagster
EOF
```

**Step 4: Create Input Files**

```bash
# Create input directory and files
mkdir -p backend/storage/input
touch backend/storage/input/manual_links.txt
touch backend/storage/input/monitoring_list.txt

# Note: Artifact directories (html, videos, summaries) are auto-created by assets
```

**Step 5: Start Development Environment**

```bash
# Start Dagster web UI (from project root)
uv run dagster dev -f backend/dagster_project/repository.py

# Access Dagster UI at: http://localhost:3000

# In separate terminal: Start MLFlow UI (optional)
uv run mlflow ui --backend-store-uri file:./mlflow/mlruns
# Access MLFlow UI at: http://localhost:5000
```

---

## Implementation Guide

### Phase 1: Project Foundation (Story 1)

**Goal:** Set up Dagster project structure, dependencies, and basic pipeline skeleton

**Tasks:**
1. Initialize backend directory structure
2. Run `dagster project scaffold` to create Dagster project
3. Add dependencies using `uv add` commands
4. Create input directory and files (manual_links.txt, monitoring_list.txt)
5. Configure environment variables in .env file
6. Implement OpenRouter client resource
7. Verify Dagster UI launches successfully with `uv run dagster dev`

**Acceptance Criteria:**
- Dagster web UI accessible at localhost:3000 via `uv run dagster dev`
- Input directory and files created
- Environment variables loaded correctly from .env file
- OpenRouter resource initializes without errors

**Estimated Effort:** 2-3 hours

### Phase 2: Core Pipeline Implementation (Story 2)

**Goal:** Implement the complete ETL pipeline assets

**Tasks:**

**2.1 Link Ingestion Asset:**
- Read manual_links.txt and monitoring_list.txt
- Load processed_links.json for deduplication
- Return list of unprocessed URLs
- Update processed_links.json with new entries

**2.2 Content Extraction Asset:**
- Implement HTML extractor using BeautifulSoup4
  - Common selector fallbacks
  - Content cleaning (remove scripts/styles)
  - Extract metadata (title, author, date)
- Implement YouTube extractor using yt-dlp
  - Transcript extraction
  - Fallback to description
- Save extracted content to artifacts/html or artifacts/videos

**2.3 Summarization Asset:**
- Integrate OpenRouter API client
- Implement prompt template for summarization
- Add Dagster metadata logging (track model, tokens, latency)
- Handle API errors using Dagster default retry
- Save summaries to artifacts/summaries (auto-create directory)

**2.4 Jobs:**
- Create manual_pipeline job (processes manual_links.txt only)
- Create monitoring_pipeline job (processes monitoring_list.txt only)

**2.5 Schedule:**
- Implement 6-hour monitoring schedule

**Acceptance Criteria:**
- Manual pipeline processes manual_links.txt end-to-end
- Monitoring pipeline processes monitoring_list.txt end-to-end
- HTML articles extracted and summarized correctly
- YouTube videos extracted and summarized correctly
- Artifacts saved with proper naming convention (URL hash)
- Dagster metadata tracks all summarization runs
- Monitoring schedule triggers every 6 hours
- Duplicate links are skipped (summary file existence check)

**Estimated Effort:** 6-8 hours

### Phase 3: Watchers and Polish (Story 3)

**Goal:** Add RSS watcher and minimal polish for MVP

**Tasks:**
1. Implement Watcher protocol (for future extensibility)
2. Implement RSSWatcher (feedparser integration)
3. Integrate watcher into link_ingestion asset
4. Verify error handling and logging throughout pipeline
5. Write essential integration test (E2E pipeline test)
6. Update README with minimal setup and usage instructions
7. Create example monitoring_list.txt with sample RSS feeds

**Acceptance Criteria:**
- RSS feeds monitored automatically (monitoring_list.txt)
- Failed extractions logged with error details in summary files
- Essential E2E test passes
- README includes setup and basic usage instructions
- Example monitoring_list.txt provided with RSS samples
- Watcher protocol ready for future extensions

**Estimated Effort:** 3-4 hours

---

## Testing Approach

**Testing Strategy (MVP - Minimal):**

1. **Essential Integration Test**
   - Test full pipeline execution end-to-end
   - Use sample HTML and YouTube URLs
   - Verify data flow through all assets
   - Test deduplication logic (summary file existence)
   - Verify failure tracking in summary files

2. **Manual Testing**
   - Test via Dagster UI for validation
   - Verify artifacts created correctly
   - Check Dagster metadata in UI

**Test Structure (Minimal):**

```
backend/tests/
├── integration/
│   └── test_pipeline_e2e.py         # Full pipeline execution
└── fixtures/
    ├── sample_article.html           # Test HTML content
    └── sample_links.txt              # Test link files
```

**Test Execution:**

```bash
# Run all tests
uv run pytest

# Run integration test
uv run pytest tests/integration/test_pipeline_e2e.py
```

**Manual Testing:**

1. Add test links to `manual_links.txt`
2. Run manual pipeline via Dagster UI
3. Verify artifacts created in storage directories
4. Check Dagster UI for metadata (model, tokens, latency)
5. Verify summaries are accurate and well-formatted
6. Test duplicate detection (re-run should skip existing summaries)
7. Test failure handling (use invalid URL, verify error in summary file)

---

## Running the Pipeline

**Start Dagster Dev Server:**

```bash
# From project root
uv run dagster dev -f backend/dagster_project/repository.py

# Access Dagster UI at: http://localhost:3000
```

**Add Links to Process:**

```bash
# Manual links (one per line)
echo "https://example.com/article" >> backend/storage/input/manual_links.txt

# Monitored sources (RSS, Reddit, etc.)
echo "https://news.ycombinator.com/rss" >> backend/storage/input/monitoring_list.txt
```

**Trigger Pipelines:**

- **Via Dagster UI:** Navigate to http://localhost:3000, select job, click "Materialize"
- **Via CLI:** `uv run dagster job execute -m backend.dagster_project -j manual_pipeline`
- **Automatic:** Monitoring job runs every 6 hours automatically

**View Metadata:**

- Navigate to Dagster UI → Assets → Select an asset → View runs
- Each run shows metadata: model used, tokens, latency, success/failure
