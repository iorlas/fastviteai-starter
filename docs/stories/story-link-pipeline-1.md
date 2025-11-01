# Story: Project Foundation & Resources

Status: Ready for Development

## Story

As a developer,
I want a properly configured Dagster project with all necessary resources,
so that I can build and test the ETL pipeline locally.

## Acceptance Criteria

1. Dagster web UI accessible at localhost:3000 via `uv run dagster dev`
2. Input directory and files created (`backend/storage/input/`)
3. Environment variables loaded correctly from `.env` file
4. OpenRouter resource initializes without errors

## Tasks / Subtasks

- [ ] Initialize backend directory structure (AC: #1)
- [ ] Run `dagster project scaffold --name dagster_project` (AC: #1)
- [ ] Add core dependencies via uv: (AC: #1)
  - [ ] `uv add dagster`
  - [ ] `uv add dagster-webserver`
  - [ ] `uv add httpx`
  - [ ] `uv add beautifulsoup4`
  - [ ] `uv add yt-dlp`
  - [ ] `uv add feedparser`
  - [ ] `uv add pydantic`
  - [ ] `uv add python-dotenv`
- [ ] Add dev dependencies:
  - [ ] `uv add --dev pytest`
  - [ ] `uv add --dev pytest-asyncio`
  - [ ] `uv add --dev ruff`
- [ ] Create input directory and files: (AC: #2)
  - [ ] `mkdir -p backend/storage/input`
  - [ ] `touch backend/storage/input/manual_links.txt`
  - [ ] `touch backend/storage/input/monitoring_list.txt`
  - [ ] Note: Artifact directories auto-created by assets
- [ ] Create `.env` file with environment variables (AC: #3)
- [ ] Implement OpenRouter client resource in `resources/openrouter_client.py` (AC: #4)
  - [ ] Configure API endpoint and authentication
  - [ ] Add model configuration (default: openai/gpt-4o)
  - [ ] Implement basic request/response handling
- [ ] Verify Dagster UI launches: `uv run dagster dev -f backend/dagster_project/repository.py` (AC: #1)

## Dev Notes

### Technical Summary

Bootstrap a Dagster project using CLI scaffolding, install all dependencies via `uv add`, create input files, and implement OpenRouter API client resource for LLM calls. Artifact directories will be auto-created by assets in Story 2.

### Project Structure Notes

- Files to modify:
  - `backend/dagster_project/resources/openrouter_client.py` (new)
  - `backend/dagster_project/resources/__init__.py` (new)
  - `backend/.env` (new)
  - `backend/storage/input/` (new directory with input files)

- Estimated effort: 1.5 story points (2-3 hours)

### References

- **Tech Spec:** See tech-spec.md sections:
  - Development Setup
  - Implementation Guide → Phase 1
  - Implementation Stack (dependency versions)
- **Architecture:** Resources pattern, Dagster configuration

## Dev Agent Record

### Context Reference

- `docs/stories/story-link-pipeline-1.context.xml` (Generated: 2025-11-01)

### Agent Model Used

<!-- Will be populated during dev-story execution -->

### Debug Log References

<!-- Will be populated during dev-story execution -->

### Completion Notes List

<!-- Will be populated during dev-story execution -->

### File List

<!-- Will be populated during dev-story execution -->
