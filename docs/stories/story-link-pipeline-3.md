# Story: Watchers & Production Polish

Status: Draft

## Story

As a user,
I want automated monitoring of RSS feeds with extensible watcher architecture,
so that new content is automatically discovered and processed without manual intervention.

## Acceptance Criteria

1. RSS feeds in `monitoring_list.txt` are monitored automatically
2. Watcher protocol defined for future extensibility
3. Failed extractions are logged with error details in summary files
4. Essential E2E integration test passes
5. README includes minimal setup and usage instructions
6. Example `monitoring_list.txt` provided with sample RSS feeds

## Tasks / Subtasks

### Watcher System
- [ ] Define Watcher protocol in `ops/watchers.py` (AC: #2)
  - [ ] Create `Watcher` protocol with `fetch_links()` method
  - [ ] Add type hints and docstrings for extensibility
- [ ] Implement RSSWatcher (AC: #1)
  - [ ] Use feedparser to parse RSS feeds
  - [ ] Extract article URLs from feed entries
  - [ ] Handle malformed feeds gracefully
  - [ ] Return list of discovered URLs
- [ ] Integrate watcher into `link_ingestion` asset (AC: #1)
  - [ ] Read monitoring_list.txt
  - [ ] Pass RSS URLs to RSSWatcher
  - [ ] Merge discovered links with manual links

### Error Handling Verification
- [ ] Verify error handling works correctly (AC: #3)
  - [ ] Test with invalid URL (should save error in summary file)
  - [ ] Verify Dagster logger captures errors
  - [ ] Confirm retry behavior with transient failures
  - [ ] Ensure final failure saves to summary file with status="failed"

### Testing & Documentation
- [ ] Write essential E2E integration test (AC: #4)
  - [ ] `tests/integration/test_pipeline_e2e.py`
  - [ ] Test full pipeline with sample HTML and YouTube URLs
  - [ ] Verify deduplication (re-run should skip existing)
  - [ ] Verify failure tracking (test with invalid URL)
  - [ ] Add test fixtures: sample_article.html, sample_links.txt
- [ ] Update README.md (AC: #5)
  - [ ] Add brief project overview
  - [ ] Document setup steps (match tech-spec)
  - [ ] Add basic usage instructions
  - [ ] Keep it minimal
- [ ] Create example monitoring_list.txt (AC: #6)
  - [ ] Add 2-3 sample RSS feeds (e.g., Hacker News RSS)
  - [ ] Include comments explaining format
  - [ ] Document that future watchers can be added via protocol

### Code Quality
- [ ] Run ruff for basic linting
  - [ ] `uv run ruff check backend/dagster_project`
  - [ ] Fix critical issues only

## Dev Notes

### Technical Summary

Implement pluggable Watcher protocol with RSS implementation (MVP), integrate into link_ingestion asset, verify error handling works correctly, write essential E2E integration test, and create minimal documentation. Architecture ready for future watcher extensions.

### Project Structure Notes

- Files to modify:
  - `backend/dagster_project/ops/watchers.py` (new - Watcher protocol + RSSWatcher)
  - `backend/dagster_project/assets/link_ingestion.py` (update - integrate RSSWatcher)
  - `backend/tests/integration/test_pipeline_e2e.py` (new)
  - `backend/tests/fixtures/sample_article.html` (new)
  - `backend/tests/fixtures/sample_links.txt` (new)
  - `backend/storage/input/monitoring_list.txt` (update - add RSS examples)
  - `README.md` (update - minimal docs)

- Estimated effort: 2 story points (3-4 hours)

### References

- **Tech Spec:** See tech-spec.md sections:
  - Technical Details → Custom Watchers (subsection 6)
  - Implementation Guide → Phase 3
  - Testing Approach
- **Architecture:** Watcher protocol pattern, error handling strategies

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
