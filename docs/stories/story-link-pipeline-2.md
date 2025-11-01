# Story: Core ETL Pipeline Implementation

Status: Draft

## Story

As a user,
I want to process links from input files through extraction and summarization,
so that I can read AI-generated summaries of articles and videos.

## Acceptance Criteria

1. Manual pipeline processes manual_links.txt end-to-end (input file → artifacts)
2. Monitoring pipeline processes monitoring_list.txt end-to-end
3. HTML articles are extracted and summarized correctly
4. YouTube videos are transcribed and summarized correctly
5. Artifacts saved with proper naming convention (URL hash, auto-create directories)
6. Dagster metadata tracks all summarization runs (model, tokens, latency)
7. Monitoring schedule triggers every 6 hours automatically
8. Duplicate and failed links are skipped (check if summary file exists)
9. Failed links save error details in summary file with status="failed"

## Tasks / Subtasks

### Link Ingestion Asset
- [ ] Implement `assets/link_ingestion.py` (AC: #1, #7)
  - [ ] Read `manual_links.txt` and `monitoring_list.txt`
  - [ ] For each URL, compute hash: SHA256(url)[:16]
  - [ ] Check if `artifacts/summaries/{hash}.json` exists
  - [ ] Return list of unprocessed URL objects (summary file doesn't exist)

### Content Extraction Asset
- [ ] Implement HTML extractor in `ops/html_extractor.py` (AC: #2)
  - [ ] Use BeautifulSoup4 with common selector fallbacks
  - [ ] Clean content (remove scripts, styles, ads)
  - [ ] Extract metadata (title, author, publish date)
  - [ ] Handle extraction errors gracefully
- [ ] Implement YouTube extractor in `ops/youtube_extractor.py` (AC: #3)
  - [ ] Use yt-dlp for transcript extraction
  - [ ] Fallback to video description if no transcript
  - [ ] Handle private/unavailable videos
- [ ] Implement `assets/content_extraction.py` (AC: #3, #4, #5)
  - [ ] Route to appropriate extractor based on URL
  - [ ] Generate URL hash (SHA256[:16])
  - [ ] Auto-create directories: `Path.mkdir(parents=True, exist_ok=True)`
  - [ ] Save extracted content to `artifacts/html/` or `artifacts/videos/`
  - [ ] Return extracted content objects

### Summarization Asset
- [ ] Implement `assets/summarization.py` (AC: #3, #4, #5, #6, #9)
  - [ ] Integrate OpenRouter resource
  - [ ] Create prompt template for summarization
  - [ ] Use Dagster default retry mechanism (exponential backoff)
  - [ ] Call LLM API with extracted content
  - [ ] Auto-create summaries directory: `Path.mkdir(parents=True, exist_ok=True)`
  - [ ] On success:
    - [ ] Log metadata to Dagster: `context.add_output_metadata({"model": "...", "tokens": ..., "latency_ms": ...})`
    - [ ] Save summary with `status: "success"` to `artifacts/summaries/{url_hash}.json`
  - [ ] On failure (after all retries):
    - [ ] Save error details with `status: "failed"` to `artifacts/summaries/{url_hash}.json`
    - [ ] Include error message, type, and retry count

### Jobs & Schedules
- [ ] Create `jobs/manual_pipeline.py` - processes manual_links.txt only (AC: #1)
  - [ ] Define job with all assets
  - [ ] Configure for on-demand triggering via UI
- [ ] Create `jobs/monitoring_pipeline.py` - processes monitoring_list.txt only (AC: #2, #7)
  - [ ] Define job with all assets
  - [ ] Link to schedule
- [ ] Create `schedules/monitoring_schedule.py` (AC: #7)
  - [ ] Implement 6-hour cron schedule: `0 */6 * * *`
  - [ ] Link to monitoring_pipeline job


## Dev Notes

### Technical Summary

Implement the complete Dagster asset graph for link processing: ingest links from files, extract content using BeautifulSoup4 (HTML) or yt-dlp (YouTube), summarize using OpenRouter LLM API, and save all artifacts to file storage (auto-create directories). Add separate jobs for manual (manual_links.txt) and monitoring (monitoring_list.txt) execution, with 6-hour monitoring schedule. Use Dagster default retry and metadata tracking.

### Project Structure Notes

- Files to modify:
  - `backend/dagster_project/assets/link_ingestion.py` (new)
  - `backend/dagster_project/assets/content_extraction.py` (new)
  - `backend/dagster_project/assets/summarization.py` (new)
  - `backend/dagster_project/assets/__init__.py` (new)
  - `backend/dagster_project/ops/html_extractor.py` (new)
  - `backend/dagster_project/ops/youtube_extractor.py` (new)
  - `backend/dagster_project/ops/__init__.py` (new)
  - `backend/dagster_project/jobs/manual_pipeline.py` (new)
  - `backend/dagster_project/jobs/monitoring_pipeline.py` (new)
  - `backend/dagster_project/jobs/__init__.py` (new)
  - `backend/dagster_project/schedules/monitoring_schedule.py` (new)
  - `backend/dagster_project/schedules/__init__.py` (new)
  - `backend/dagster_project/repository.py` (update - add jobs & schedules)

- Estimated effort: 3.5 story points (6-8 hours)

### References

- **Tech Spec:** See tech-spec.md sections:
  - Technical Details (all subsections 1-5)
  - Implementation Guide → Phase 2
  - Testing Approach
- **Architecture:** Dagster assets, dependencies, jobs, schedules

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

<!-- Will be populated during dev-story execution -->

### Debug Log References

<!-- Will be populated during dev-story execution -->

### Completion Notes List

<!-- Will be populated during dev-story execution -->

### File List

<!-- Will be populated during dev-story execution -->
