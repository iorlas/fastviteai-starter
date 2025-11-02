# URL-Partitioned Architecture

## Status: **ACTIVE** (Coexists with Legacy Batch Processing)

## Executive Summary

This document describes the new **URL-partitioned medallion pipeline** that enables URL-centric processing with proper lineage tracking, selective re-materialization, and support for multi-source enrichment.

**Key Innovation:** Each URL becomes its own Dagster partition, allowing independent processing, lineage tracking, and selective re-enrichment when new discussion sources (HN, Reddit) are discovered.

## Architecture Overview

```
DISCOVERY LAYER (Non-partitioned coordinator)
  └─ discovered_urls
      ├─ Discovers URLs from RSS, manual lists, monitoring
      ├─ Normalizes to canonical form
      ├─ Tracks sources in url_metadata.json
      └─ Adds URL hashes to url_partitions DynamicPartitionsDefinition

          ↓ Each URL hash becomes a partition key

BRONZE LAYER (Immutable, partitioned by URL hash)
  └─ bronze_raw_html[url_hash]
      ├─ Downloads once, caches forever
      ├─ Path: artifacts/bronze/bronze_raw_html/{url_hash}.json
      └─ IO Manager skips if file exists

          ↓

SILVER LAYER (Cleaned, partitioned by URL hash)
  ├─ silver_extracted_content[url_hash]
  │   ├─ Extracts clean text/transcript
  │   └─ Path: artifacts/silver/silver_extracted_content/{url_hash}.json
  │
  └─ silver_summary[url_hash]
      ├─ Generates LLM summary
      └─ Paths: artifacts/silver/silver_summary/{url_hash}.{json,md}

          ↓ (Future Phase 2)

SILVER LAYER (Discussions - re-fetched on new discoveries)
  ├─ silver_hn_discussions[url_hash]
  └─ silver_reddit_discussions[url_hash]

GOLD LAYER (Aggregated enrichment)
  └─ gold_enriched_summary[url_hash]
```

## Core Components

### 1. URL Partitions (`dagster_project/partitions.py`)

```python
from dagster import DynamicPartitionsDefinition

url_partitions = DynamicPartitionsDefinition(name="urls")

def compute_url_hash(url: str) -> str:
    """SHA256 hash (first 16 chars) - partition key."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def normalize_url(url: str) -> str:
    """Canonical URL normalization for deduplication."""
    return url.strip().rstrip("/")
```

### 2. URL Metadata Store (`dagster_project/url_metadata.py`)

Tracks all URL discoveries with source attribution:

```json
{
  "abc123def456": {
    "canonical_url": "https://example.com/article",
    "url_hash": "abc123def456",
    "sources": {
      "rss": [{"feed_url": "techcrunch.com/feed", "discovered_at": "..."}],
      "hn": [
        {"post_id": "39283920", "discovered_at": "2025-01-02T14:30Z"},
        {"post_id": "39445566", "discovered_at": "2025-02-15T09:15Z"}
      ],
      "manual": [{"file": "manual_links.txt", "discovered_at": "..."}]
    },
    "first_discovered": "2025-01-01T10:00Z",
    "last_discovered": "2025-02-15T09:15Z"
  }
}
```

**Storage:** `artifacts/url_metadata.json`

### 3. IO Managers (ConfigurableIOManager Pattern)

#### BronzeIOManager

**Features:**
- Partitioned storage: `{base_dir}/{asset_name}/{partition_key}.json`
- **Caching:** Skips save if file exists (bronze immutability)
- Raises error on missing files (fail fast)

**Example:**
```python
@asset(partitions_def=url_partitions, io_manager_key="bronze_io_manager")
def bronze_raw_html(context):
    url_hash = context.partition_key  # e.g., "abc123def456"
    # Download logic...
    return {"url": ..., "html_content": ..., "download_info": ...}

# Saved to: artifacts/bronze/bronze_raw_html/abc123def456.json
```

#### SilverIOManager

**Features:**
- Partitioned storage with timestamps
- Markdown generation for summaries
- Lineage tracking in metadata

**Example:**
```python
@asset(partitions_def=url_partitions, io_manager_key="silver_io_manager")
def silver_summary(context, silver_extracted_content):
    url_hash = context.partition_key
    # Summarization logic...
    return {
        "url": ...,
        "summary": ...,
        "model": "gpt-4o",
        "lineage": {...}
    }

# Saved to:
#   artifacts/silver/silver_summary/abc123def456.json
#   artifacts/silver/silver_summary/abc123def456.md
```

### 4. Assets

#### discovered_urls (Coordinator)

**Type:** Non-partitioned
**Purpose:** URL discovery and partition management

**Responsibilities:**
1. Read manual_links.txt and monitoring_list.txt
2. Fetch RSS feed entries
3. Normalize URLs to canonical form
4. Update url_metadata.json with source tracking
5. Add new URL hashes to url_partitions

**Returns:** Discovery statistics

#### bronze_raw_html[url_hash]

**Type:** Partitioned (URL hash)
**Purpose:** Download and cache raw HTML

**Features:**
- BronzeIOManager caching (skip if exists)
- Error handling (stores error metadata)
- Metadata: status_code, headers, final_url

#### silver_extracted_content[url_hash]

**Type:** Partitioned (URL hash)
**Purpose:** Extract clean content

**Features:**
- Auto-detects YouTube vs HTML
- Applies appropriate extractor
- Stores errors for failed extractions

#### silver_summary[url_hash]

**Type:** Partitioned (URL hash)
**Purpose:** Generate LLM summary

**Features:**
- Retry policy (3 retries, exponential backoff)
- Dual output (JSON + Markdown)
- Token and latency tracking

## Key Benefits

### 1. Independent URL Processing

Each URL is an independent partition:
- Can materialize individual URLs
- Parallel processing across partitions
- Per-URL lineage in Dagster UI

### 2. Efficient Caching

Bronze layer immutability:
- Download once, use forever
- Re-process silver layer without re-downloading
- Significant time and bandwidth savings

### 3. Multi-Source Tracking

URL metadata tracks all discovery sources:
```python
# Same URL discovered by 3 sources:
sources = {
    "rss": [{"feed_url": "techcrunch.com/feed", ...}],
    "hn": [{"post_id": "39283920", ...}],  # Hacker News discussion
    "reddit": [{"post_id": "abc123", ...}]  # Reddit thread
}
```

### 4. Selective Re-enrichment

When new source discovers existing URL:
- Bronze: Skip (already cached)
- Silver content/summary: Skip (immutable)
- Silver discussions: Re-fetch (new comments)
- Gold enrichment: Re-run (aggregate all)

## Future Enhancements (Phase 2)

### Canonical URL Resolution

HackerNews posts link to articles, not HN itself:

```python
@asset
def hn_watcher(context):
    """Discover articles from HN, track HN post as source."""
    hn_posts = fetch_recent_hn()

    for post in hn_posts:
        canonical_url = post.url  # The actual article URL
        metadata_store.add_discovery(
            canonical_url=canonical_url,
            source="hn",
            source_metadata={
                "hn_post_id": post.id,
                "hn_title": post.title,
                "hn_score": post.score,
            }
        )
```

### Discussion Enrichment

```python
@asset(partitions_def=url_partitions)
def silver_hn_discussions(context):
    """Fetch ALL HN discussions about this canonical URL."""
    url_hash = context.partition_key
    url_metadata = get_metadata(url_hash)

    hn_sources = url_metadata["sources"].get("hn", [])
    all_discussions = []

    for hn_post in hn_sources:
        comments = fetch_hn_comments(hn_post["post_id"])
        all_discussions.append({
            "post_id": hn_post["post_id"],
            "comments": comments,
            "score": hn_post["score"],
        })

    return {"url_hash": url_hash, "discussions": all_discussions}
```

### Gold Layer Aggregation

```python
@asset(partitions_def=url_partitions)
def gold_enriched_summary(
    silver_extracted_content,
    silver_summary,
    silver_hn_discussions,
    silver_reddit_discussions,
):
    """Aggregate content + all source discussions."""
    return {
        "summary": silver_summary["summary"],
        "hn_insights": analyze_hn_sentiment(silver_hn_discussions),
        "reddit_insights": analyze_reddit_discussions(silver_reddit_discussions),
        "community_consensus": find_agreement_points(...),
        "cross_links": find_related_urls(...),
    }
```

## Migration Strategy

### Current State

**Legacy batch assets:**
- bronze_raw_links (returns list)
- bronze_raw_html (processes batch)
- content_extraction (processes batch)
- summarization (processes batch)

**New partitioned assets:**
- discovered_urls (coordinator)
- bronze_raw_html[url_hash] (partitioned)
- silver_extracted_content[url_hash] (partitioned)
- silver_summary[url_hash] (partitioned)

### Coexistence

Both pipelines active simultaneously:
- Legacy: Processes batches
- New: Processes individual URLs
- Shared directories: artifacts/bronze, artifacts/silver

### Transition Plan

**Phase 1 (Now):** Foundation
- ✅ URL partitions + metadata store
- ✅ ConfigurableIOManager classes
- ✅ Partitioned bronze/silver assets
- ✅ discovered_urls coordinator

**Phase 2:** Enrichment
- Add reddit_watcher, hn_watcher
- Implement silver_hn_discussions
- Implement silver_reddit_discussions
- Build gold_enriched_summary

**Phase 3:** Cleanup
- Deprecate legacy batch assets
- Remove compatibility code
- Full migration to partitioned architecture

## Directory Structure

```
artifacts/
  url_metadata.json                    # Central URL registry
  bronze/
    bronze_raw_html/{url_hash}.json    # Raw downloads (immutable)
  silver/
    silver_extracted_content/{url_hash}.json
    silver_summary/{url_hash}.json     # Summary data
    silver_summary/{url_hash}.md       # Human-readable
    # Phase 2:
    silver_hn_discussions/{url_hash}.json
    silver_reddit_discussions/{url_hash}.json
  gold/                                # Phase 2
    gold_enriched_summary/{url_hash}.json
    knowledge_graph.json
```

## Testing

Run validation:

```bash
# Lint and format
make check

# Test partitioned assets
uv run pytest tests/ -k partitioned

# Test URL metadata store
uv run pytest tests/ -k url_metadata
```

## Monitoring

Dagster UI shows per-partition status:
- Navigate to Assets view
- Click on partitioned asset
- See materialization status for each URL hash
- View lineage graph per partition

## References

- **Dagster Partitions:** https://docs.dagster.io/concepts/partitions-schedules-sensors/partitions
- **ConfigurableIOManager:** https://docs.dagster.io/concepts/io-management/io-managers
- **Dynamic Partitions:** https://docs.dagster.io/concepts/partitions-schedules-sensors/partitions#dynamic-partitions
