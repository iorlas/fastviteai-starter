# AILabBrains Pipeline: Architecture

## 1. Overview

### Purpose
Content extraction and AI-powered summarization pipeline for technical articles and YouTube videos with community discussion analysis from platforms like HackerNews and Lobsters.

### Core Architecture
**Medallion Data Pattern** (Bronze → Silver):
- **Bronze Layer**: Immutable source-of-truth cache (raw extracted data)
- **Silver Layer**: Regenerable AI-derived insights (summaries and analysis)

### Key Principles
1. **Auto-discovery**: Each step scans filesystem to find its own work
2. **Self-contained steps**: Discovery + progress tracking + execution in one function
3. **Resumability**: Crash-safe by design - restart picks up where it left off
4. **Immutability**: Bronze layer never modified once written
5. **Async-first HTTP**: All network operations use native async/await

### Pipeline Pattern
```
Sequential Orchestration + Auto-Discovery + Medallion Architecture
```

Each step:
1. Scans filesystem to discover what needs processing
2. Filters out already-processed items
3. Creates progress bar
4. Processes all items
5. Writes immutable artifacts

---

## 2. Pipeline Flow

### Orchestrator
```python
# orchestrator.py - ~25 lines

async def _async_process_urls(source: str) -> None:
    """Pipeline: Each step discovers its own work."""
    # Stage 0a/0b: Discovery (fast)
    if source == "manual":
        await discover_manual()
    elif source == "monitoring":
        await discover_monitoring()

    # Stage 0c: Classification (network-heavy)
    await classify_urls()

    # Stage 1: Bronze (immutable extraction)
    await extract_html()
    await download_youtube()
    await transcribe_youtube()
    await fetch_discussions()

    # Stage 2: Silver (AI summarization)
    if settings.enable_summarization:
        await generate_article_summaries()
        await generate_discussion_summaries()
        await synthesize_final_summaries()
```

---

### Stage 0: URL Discovery & Classification

#### Step 0a: Manual Discovery
**Function**: `discover_manual() -> None`

**Input**: `artifacts/inputs/manual_links.txt`

**Process**:
1. Read URLs from file (skip comments and empty lines)
2. Compute url_hash = SHA-256(url)
3. Check if bronze/urls/{url_hash}.json exists (skip if yes)
4. Save minimal metadata

**Output**: `bronze/urls/{url_hash}.json`
```json
{
  "url": "https://example.com/article",
  "source": "manual",
  "discovered_at": "2025-01-15T10:30:00Z"
}
```

#### Step 0b: Monitoring Discovery
**Function**: `discover_monitoring() -> None`

**Input**: `artifacts/inputs/monitoring_list.txt`

**Process**:
1. Read URLs from file (may include RSS feeds)
2. **RSS Expansion**: Detect RSS/Atom feeds → expand to article URLs
3. For each discovered URL:
   - Compute url_hash = SHA-256(url)
   - Check if bronze/urls/{url_hash}.json exists (skip if yes)
   - Save minimal metadata

**Output**: `bronze/urls/{url_hash}.json`
```json
{
  "url": "https://example.com/article",
  "source": "monitoring",
  "feed_url": "https://example.com/rss",  // if from RSS feed
  "discovered_at": "2025-01-15T10:30:00Z"
}
```

**Components**: RSSWatcher

#### Step 0c: URL Classification
**Function**: `classify_urls() -> None`

**Auto-discovery**:
- Scan `bronze/urls/*.json`
- Filter: Exclude those with existing metadata in EITHER `bronze/url_metadata_html/{url_hash}.json` OR `bronze/url_metadata_youtube/{url_hash}.json`

**Process** (network-heavy):
1. **Aggregator Resolution**: Detect HN/Lobsters URLs → fetch discussions + extract linked article
2. **Normalization**: Remove tracking params, standardize format
3. **Content Type Detection**: HTML vs YouTube
4. **Save to type-specific directory**

**Output**:
- HTML: `bronze/url_metadata_html/{url_hash}.json`
- YouTube: `bronze/url_metadata_youtube/{url_hash}.json`

```json
{
  "url": "https://example.com/article",
  "url_hash": "abc123...",
  "original_url": "...",  // if different from canonical
  "content_type": "html|youtube",
  "source": "manual|monitoring",
  "feed_url": "...",  // if from RSS
  "discussion_links": [{"type": "hackernews", "url": "...", "id": "..."}],
  "discovered_at": "2025-01-15T10:30:00Z",
  "classified_at": "2025-01-15T10:30:05Z"
}
```

**Components**: HackerNewsClient, LobstersClient, url_normalize, YouTubeExtractor

---

### Stage 1: Bronze Layer (Immutable Extraction)

#### Step 1.1: HTML Extraction
**Function**: `extract_html() -> None`

**Auto-discovery**:
- Scan `bronze/url_metadata_html/*.json`
- Filter: Exclude those with existing `bronze/html/{url_hash}.json`

**Process**: GenericHTMLExtractor → trafilatura extraction

**Output**: `bronze/html/{url_hash}.json`
```json
{
  "url": "...",
  "url_hash": "...",
  "title": "Article Title",
  "author": "Author Name",
  "date": "2025-01-15",
  "text": "Main content...",
  "html_raw": "<html>...",
  "metadata": {...},
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### Step 1.2: YouTube Download
**Function**: `download_youtube() -> None`

**Auto-discovery**:
- Scan `bronze/url_metadata_youtube/*.json`
- Filter: Exclude those with existing `bronze/youtube_downloads/{video_id}/metadata.json`

**Process**: yt-dlp download (metadata + audio)

**Output**: `bronze/youtube_downloads/{video_id}/`
```
├─ metadata.json      # {title, author, duration, views, etc.}
└─ video.m4a         # Audio file
```

---

#### Step 1.3: YouTube Transcription
**Function**: `transcribe_youtube() -> None`

**Auto-discovery**:
- Scan `bronze/youtube_downloads/*/metadata.json`
- Filter: Exclude those with existing `transcription.json`

**Process**: faster-whisper transcription

**Output**: `bronze/youtube_downloads/{video_id}/transcription.json`
```json
{
  "video_id": "...",
  "text": "Full transcription...",
  "segments": [{"start": 0.0, "end": 5.2, "text": "..."}],
  "language": "en",
  "duration": 1234.5,
  "word_count": 5678,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Configuration**: WHISPER_MODEL (tiny|base|small|medium|large-v2|large-v3), WHISPER_DEVICE (cpu|cuda|mps)

---

#### Step 1.4: Discussion Fetching
**Function**: `fetch_discussions() -> None`

**Auto-discovery**:
- Scan BOTH `bronze/url_metadata_html/*.json` AND `bronze/url_metadata_youtube/*.json`
- Filter: Exclude those with existing `bronze/discussions/{url_hash}/metadata.json`

**Process**:
- Multi-platform API calls (HackerNews Algolia API, Lobsters JSON API)
- Convert to UnifiedDiscussion format
- Flatten comment threads

**Output**: `bronze/discussions/{url_hash}/`
```
├─ metadata.json                          # {platforms, counts, fetched_at}
├─ hackernews_{discussion_id}.json       # UnifiedDiscussion
└─ lobsters_{discussion_id}.json         # UnifiedDiscussion
```

**UnifiedDiscussion Schema**:
```json
{
  "platform": "hackernews|lobsters",
  "id": "12345",
  "discussion_url": "...",
  "article_url": "...",
  "title": "Discussion Title",
  "author": "username",
  "points": 150,
  "comment_count": 42,
  "comments": [{"id": "...", "author": "...", "text": "...", "depth": 0}],
  "created_at": "2025-01-15T08:00:00Z",
  "fetched_at": "2025-01-15T10:30:00Z"
}
```

---

### Stage 2: Silver Layer (AI Summarization)

**Principle**: Regenerable AI-derived insights. Can be deleted and rebuilt from bronze.

---

#### Step 2.1: Article Summaries
**Function**: `generate_article_summaries() -> None`

**Auto-discovery**:
- Scan `bronze/html/*.json` + `bronze/youtube_downloads/*/transcription.json`
- Filter: Exclude those with existing `silver/article_summaries/{url_hash}.json`

**Process**: ArticleSummarizer → OpenAI structured output

**LLM Task**:
- Triage: Article type, target audience, novelty signal
- Analysis: Key points, technical depth, practical value
- Metadata: Technical tags, complexity score, time investment

**Output**: `silver/article_summaries/{url_hash}.json`
```json
{
  "url": "...",
  "url_hash": "...",
  "title": "...",
  "content_type": "html|youtube",
  "analysis": {
    "triage": {"type": "tutorial", "audience": "intermediate", "novelty": "incremental"},
    "article": {"one_line": "...", "semantic_summary": "...", "key_points": [...]},
    "signals": {"technical_tags": [...], "complexity": 7, "time_to_read": 15}
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### Step 2.2: Discussion Summaries
**Function**: `generate_discussion_summaries() -> None`

**Auto-discovery**:
- Scan `bronze/discussions/*/` (all discussion JSON files)
- Require: Corresponding article summary exists
- Filter: Exclude those with existing summary in `silver/discussion_summaries/{url_hash}/{platform}_{id}.json`

**Process**: DiscussionSummarizer → OpenAI structured output (uses article semantic_summary as context)

**LLM Task**:
- Key themes in discussion
- Insights and alternative perspectives
- Corrections or disagreements with article
- Consensus vs controversy

**Output**: `silver/discussion_summaries/{url_hash}/{platform}_{discussion_id}.json`
```json
{
  "url": "...",
  "discussion_id": "...",
  "platform": "hackernews",
  "discussion_url": "...",
  "community_take": {
    "themes": ["performance optimization", "security concerns"],
    "insights": ["Alternative approach using X", "Trade-off with Y"],
    "corrections": ["Article incorrectly states Z"],
    "consensus": "Generally positive reception",
    "controversy": "Disagreement on implementation details"
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### Step 2.3: Final Synthesis
**Function**: `synthesize_final_summaries() -> None`

**Auto-discovery**:
- Scan `silver/article_summaries/*.json`
- Filter: Exclude those with existing `silver/summaries/{url_hash}.json`

**Process**: CommunitySynthesizer → OpenAI structured output

**Logic**:
- **0 discussions**: Return article analysis only
- **1 discussion**: Merge directly with article
- **2+ discussions**: LLM synthesis across multiple discussions

**LLM Task** (multi-discussion only):
- Synthesize common themes across platforms
- Identify unique insights per platform
- Reconcile conflicting perspectives

**Output**: `silver/summaries/{url_hash}.json`
```json
{
  "url": "...",
  "title": "...",
  "status": "success",
  "content_type": "html|youtube",
  "structured_summary": {
    "triage": {...},
    "article": {...},
    "signals": {...},
    "community": {  // Synthesized from all discussions
      "themes": [...],
      "insights": [...],
      "corrections": [...],
      "consensus": "...",
      "controversy": "..."
    }
  },
  "discussion_count": 3,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

---

## 3. Medallion Architecture

### Directory Structure

```
artifacts/
  inputs/                     # User-provided data
    manual_links.txt          # Manual URL submissions
    monitoring_list.txt       # RSS feeds and monitoring sources

  bronze/                     # IMMUTABLE: Raw extracted data
    url_metadata/             # Discovered URLs (work registry)
      {url_hash}.json
    html/                     # Extracted HTML content
      {url_hash}.json
    youtube_downloads/        # YouTube metadata + transcripts
      {video_id}/
        metadata.json
        transcription.json
        video.m4a
    discussions/              # Discussion threads
      {url_hash}/
        metadata.json
        hackernews_{id}.json
        lobsters_{id}.json

  silver/                     # REGENERABLE: AI-derived insights
    article_summaries/        # Stage 2.1: Article-only analysis
      {url_hash}.json
    discussion_summaries/     # Stage 2.2: Per-discussion analysis
      {url_hash}/
        {platform}_{id}.json
    summaries/                # Stage 2.3: Final synthesis
      {url_hash}.json

  cache/                      # TEMPORARY: Caching layers
    http_responses/           # Hishel HTTP cache (24hr TTL)
      http_cache.db
    openai_structured_outputs/ # LLM response cache
    whisper_models/           # Model weights
```

### Bronze Layer Rules
- ✅ **Append-only**: Never modify existing files
- ✅ **Check before write**: Always check `exists()` before write
- ✅ **Immutable**: Never delete (source of truth)
- ✅ **URL hash partitioning**: SHA-256(normalized_url) as unique ID

### Silver Layer Rules
- ✅ **Regenerable**: Can be deleted and rebuilt from bronze
- ✅ **Selective caching**: Only cache expensive operations (final synthesis)
- ✅ **Version control**: Track via LLM metadata
- ✅ **Schema evolution**: Can regenerate on model changes

---

## 4. Key Patterns

### Auto-Discovery Pattern

**Every step follows this pattern**:
```python
async def step_name() -> None:
    """Auto-discover and process items."""

    # 1. Discover work (scan filesystem)
    items_needing_work = []
    for source_file in scan_source_directory():
        if matches_criteria() and not already_processed():
            items_needing_work.append(source_file)

    if not items_needing_work:
        return  # Nothing to do

    # 2. Create progress bar
    with Progress(...) as progress:
        task = progress.add_task("Step Name...", total=len(items_needing_work))

        # 3. Process each item
        for item in items_needing_work:
            try:
                result = await do_work(item)
                save_artifact(result)
                progress.update(task, advance=1, description="[green]✓[/green] Success")
            except Exception as e:
                logger.error("step_failed", item=item, error=str(e))
                progress.update(task, advance=1, description="[red]✗[/red] Failed")
```

**Benefits**:
- Crash-safe: Restart anywhere, picks up unfinished work
- Idempotent: Run multiple times safely
- Independent: Can run individual steps
- Simple: No state passing between stages

---

### Async-First HTTP

**All HTTP operations use async/await**:
```python
# ✅ Correct
async def fetch_data():
    client = get_async_cache_client()
    result = await client.get(url)
    return result

# ❌ Wrong (don't wrap sync)
async def fetch_data():
    result = asyncio.run(sync_function())
    return result
```

**Benefits**:
- Simpler code (no asyncio.run() wrappers)
- Better concurrency for I/O-bound operations
- Unified HTTP client API (AsyncCacheClient with Hishel caching)
- Future-proof for concurrent processing

---

### Multi-Layer Caching

**Layer 1: HTTP Cache** (AsyncCacheClient + Hishel)
- Location: `artifacts/cache/http_responses/http_cache.db`
- TTL: 24 hours
- Scope: All HTTP GET requests (except yt-dlp/youtube-transcript)
- Prevents redundant API calls

**Layer 2: Bronze Cache** (Filesystem)
- Location: `artifacts/bronze/`
- Strategy: Check `exists()` before every write
- Immutability: Never modify/delete once written
- Protects external APIs from repeated calls

**Layer 3: OpenAI Cache** (Schema-Aware Filesystem)
- Location: `artifacts/cache/openai_structured_outputs/`
- Cache Key: Hash of (messages, model, schema, temperature)
- Schema Detection: Invalidates on Pydantic model changes
- Saves API costs during development

---

### Integration Unit Boundary

**Pattern**: Organize by external service boundary, not usage pattern.

**Example**: `HackerNewsClient` handles BOTH:
1. Article URL extraction (HTML scraping)
2. Discussion fetching (Algolia API)

**Rationale**:
- Shared operational boundary (rate limits, monitoring, errors)
- Concentrated domain knowledge (HN URL structure, API quirks)
- Simpler mental model (one import for all HN operations)
- Unified configuration (single timeout, cache client, retry logic)

**Applied to**: HackerNewsClient, LobstersClient

---

### Path Ownership Pattern

**Principle**: Each step owns and exports its output paths. Consumers import path helpers from producing steps.

**File Organization**:
- One file per step function
- Path helpers live with the step that produces the data
- Consumers import path helpers from producers

**Pattern**:
```python
# stages/stage1_extract_html.py - Producer
def get_bronze_html_path(url_hash: str) -> Path:
    """Path where extract_html() writes extracted HTML content."""
    return settings.artifacts_path / "bronze" / "html" / f"{url_hash}.json"

async def extract_html() -> None:
    # Uses its own path helper
    output_path = get_bronze_html_path(url_hash)
    if not output_path.exists():
        # ... work ...

# stages/stage2_article_summaries.py - Consumer
from ailabbrains.stages.stage1_extract_html import get_bronze_html_path

async def generate_article_summaries() -> None:
    # Imports and uses producer's path helper
    html_data = json.loads(get_bronze_html_path(url_hash).read_text())
    # ... use data ...
```

**Benefits**:
- **Clear ownership**: Each step defines where it writes
- **Explicit dependencies**: Import statements show data flow
- **Self-contained**: Step logic + path logic live together
- **No global registry**: No centralized paths.py
- **Type-safe**: IDE autocomplete for path helpers
- **One file per step**: Easy to navigate and understand

**Dependencies Diagram**:
```
Stage 0: Discovery
├─ stage0_discovery.py
│  └─ exports: get_url_metadata_path(url_hash)
│
Stage 1: Bronze
├─ stage1_extract_html.py
│  ├─ imports: get_url_metadata_path() from stage0_discovery
│  └─ exports: get_bronze_html_path(url_hash)
│
├─ stage1_download_youtube.py
│  ├─ imports: get_url_metadata_path() from stage0_discovery
│  └─ exports: get_youtube_metadata_path(video_id), get_youtube_dir(video_id)
│
├─ stage1_transcribe_youtube.py
│  ├─ imports: get_youtube_dir(), get_youtube_metadata_path() from stage1_download_youtube
│  └─ exports: get_transcription_path(video_id)
│
├─ stage1_fetch_discussions.py
│  ├─ imports: get_url_metadata_path() from stage0_discovery
│  └─ exports: get_discussions_dir(url_hash), get_discussion_metadata_path(url_hash)
│
Stage 2: Silver
├─ stage2_article_summaries.py
│  ├─ imports: get_bronze_html_path() from stage1_extract_html
│  │          get_transcription_path() from stage1_transcribe_youtube
│  │          get_youtube_metadata_path() from stage1_download_youtube
│  └─ exports: get_article_summary_path(url_hash)
│
├─ stage2_discussion_summaries.py
│  ├─ imports: get_article_summary_path() from stage2_article_summaries
│  │          get_discussions_dir() from stage1_fetch_discussions
│  └─ exports: get_discussion_summary_path(url_hash, platform, discussion_id)
│
└─ stage2_final_synthesis.py
   ├─ imports: get_article_summary_path() from stage2_article_summaries
   │          get_discussion_summary_dir() from stage2_discussion_summaries
   └─ exports: get_final_summary_path(url_hash)
```

**Data Flow**:
```
discover_urls → extract_html → generate_article_summaries → generate_discussion_summaries → synthesize_final_summaries
              → download_youtube → transcribe_youtube ──────┘
              → fetch_discussions ────────────────────────────┘
```

---

## 5. Configuration

### Environment Variables

Create `.env` file (see `.env.example`):

```bash
# Artifacts
ARTIFACTS_PATH=artifacts

# OpenAI/OpenRouter
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o

# Feature Flags
ENABLE_SUMMARIZATION=true

# Network
HTTP_PROXY=  # Optional: http://proxy:port or socks5://proxy:port

# Whisper Transcription
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu
WHISPER_CACHE_DIR=artifacts/cache/whisper_models
```

### Pydantic Settings Pattern

```python
from ailabbrains.config import settings

# Access configuration
if settings.enable_summarization:
    model = settings.openai_model

# Access paths
from ailabbrains.utils.paths import ARTIFACTS_PATH, MANUAL_LINKS_FILE
```

**Benefits**:
- Type-safe configuration
- Environment variable validation
- Default values
- IDE autocomplete

---

## Summary

The AILabBrains pipeline implements:

**Architecture**: Medallion pattern (Bronze → Silver) with auto-discovery
- Bronze: Immutable source-of-truth cache
- Silver: Regenerable AI insights

**Pipeline**: 8 self-contained steps
- Each step discovers own work from filesystem
- Progress tracking embedded in each function
- Crash-safe and resumable by design

**Key Patterns**:
- Auto-discovery (scan filesystem for work)
- Self-contained steps (discovery + progress + execution)
- Async-first HTTP (all network I/O)
- Multi-layer caching (HTTP + Bronze + OpenAI)

**Result**: Simple, maintainable, crash-safe pipeline with clear separation between immutable data (bronze) and regenerable insights (silver).
