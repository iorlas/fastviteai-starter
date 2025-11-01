# Story: Project Foundation & Resources

Status: done

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

- [x] Initialize backend directory structure (AC: #1)
- [x] Run `dagster project scaffold --name dagster_project` (AC: #1)
- [x] Add core dependencies via uv: (AC: #1)
  - [x] `uv add dagster`
  - [x] `uv add dagster-webserver`
  - [x] `uv add httpx`
  - [x] `uv add beautifulsoup4`
  - [x] `uv add yt-dlp`
  - [x] `uv add feedparser`
  - [x] `uv add pydantic`
  - [x] `uv add python-dotenv`
- [x] Add dev dependencies:
  - [x] `uv add --dev pytest`
  - [x] `uv add --dev pytest-asyncio`
  - [x] `uv add --dev ruff`
- [x] Create input directory and files: (AC: #2)
  - [x] `mkdir -p storage/input` (moved to project root)
  - [x] `touch storage/input/manual_links.txt`
  - [x] `touch storage/input/monitoring_list.txt`
  - [x] Note: Artifact directories auto-created by assets
- [x] Create `.env` file with environment variables (AC: #3)
- [x] Implement OpenRouter client resource in `resources/openrouter_client.py` (AC: #4)
  - [x] Configure API endpoint and authentication
  - [x] Add model configuration (default: openai/gpt-4o)
  - [x] Implement basic request/response handling
- [x] Verify Dagster UI launches: `uv run dagster dev -f dagster_project/definitions.py` (AC: #1)

### Review Follow-ups (AI)

- [x] [AI-Review][High] Add `.env` to .gitignore to prevent committing secrets (Security)

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

- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

**Implementation Approach:**
- Adopted flatter project structure: moved dagster_project and storage to project root instead of nested backend/ directory
- Scaffolded Dagster project using `dagster project scaffold` CLI command
- Installed all dependencies via uv package manager
- Implemented OpenRouter client as a Dagster ConfigurableResource with proper validation and error handling
- Created comprehensive test suite covering environment, storage, OpenRouter client, and integration tests
- Fixed all linting issues with ruff to ensure code quality

### Completion Notes List

**Implementation Summary:**
- Successfully scaffolded Dagster project at project root with standard structure
- Added all core dependencies (dagster, httpx, beautifulsoup4, yt-dlp, feedparser, pydantic, python-dotenv)
- Added dev dependencies (pytest, pytest-asyncio, ruff)
- Created storage/input directory with manual_links.txt and monitoring_list.txt
- Implemented OpenRouter client resource with authentication, model configuration, and request/response handling
- Created .env file with OPENROUTER_API_KEY, OPENROUTER_MODEL, and DAGSTER_HOME variables
- Added [tool.dagster] configuration to pyproject.toml for simpler CLI usage
- Dagster UI verified accessible at localhost:3000 via `uv run dagster dev`
- All 19 tests passing with comprehensive coverage
- Code passes all quality checks: format, lint, typecheck (ty), and tests via `make check`

**Key Technical Decisions:**
- Used Dagster's ConfigurableResource pattern for OpenRouter client
- Leveraged pydantic Field with default_factory for environment variable loading
- Implemented proper validation in setup_for_execution to fail fast on missing config
- Created httpx-based client with proper timeout handling and error raising

### File List

**New Files:**
- `.env` - Environment configuration
- `.dagster/` - Dagster home directory
- `dagster_project/__init__.py` - Package init
- `dagster_project/definitions.py` - Dagster definitions with OpenRouter resource
- `dagster_project/assets.py` - Asset definitions (scaffolded)
- `dagster_project/resources/__init__.py` - Resources package
- `dagster_project/resources/openrouter_client.py` - OpenRouter client resource
- `storage/input/manual_links.txt` - Manual link input file
- `storage/input/monitoring_list.txt` - Monitoring list input file
- `tests/__init__.py` - Test package
- `tests/integration/__init__.py` - Integration tests package
- `tests/fixtures/__init__.py` - Test fixtures package
- `tests/test_environment.py` - Environment configuration tests
- `tests/test_storage.py` - Storage structure tests
- `tests/test_openrouter_client.py` - OpenRouter client tests
- `tests/integration/test_project_setup.py` - Integration tests

**Modified Files:**
- `pyproject.toml` - Added dependencies and [tool.dagster] configuration
- `uv.lock` - Updated lockfile with new dependencies

---

## Senior Developer Review (AI)

**Reviewer:** BMad
**Date:** 2025-11-01
**Model:** Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Outcome

**CHANGES REQUESTED** - Minor security fix required before final approval

### Summary

Excellent implementation of the project foundation! All acceptance criteria are fully met, all 22 tasks are verified as complete, and all 19 tests pass. The code quality is high with proper use of Dagster patterns, comprehensive testing, and clean architecture.

However, there is ONE HIGH SEVERITY security finding that must be addressed: the `.env` file is not included in `.gitignore`, creating a risk of committing secrets to version control. This is a quick fix (single line addition) but critical for security hygiene.

Once this is resolved, the story will be ready for final approval.

### Key Findings

#### HIGH Severity

1. **[HIGH] .env file not in .gitignore** - Security risk
   - **Issue:** The .env file containing API keys is not excluded from version control
   - **Impact:** Risk of accidentally committing secrets to git repository
   - **Evidence:** .gitignore:1-2 only contains `__pycache__` and `.dagster`, missing `.env`
   - **Current state:** .env contains placeholder key (`your_api_key_here`), so no immediate exposure
   - **Fix required:** Add `.env` to .gitignore before story completion

#### MEDIUM Severity

None

#### LOW Severity

1. **[LOW] No retry logic for API calls** - Reliability concern
   - **Issue:** OpenRouter API calls have no retry mechanism for transient failures
   - **Evidence:** openrouter_client.py:85-88 - Single request with no retry wrapper
   - **Recommendation:** Consider adding retry logic with exponential backoff for production use (can be deferred to future story)

2. **[LOW] No input validation on API responses** - Robustness concern
   - **Issue:** Assumes API always returns expected structure (choices[0].message.content)
   - **Evidence:** openrouter_client.py:99 - Direct access without validation
   - **Recommendation:** Add validation/try-except for malformed responses (can be deferred to future story)

3. **[LOW] Error context could be enhanced** - Developer experience
   - **Issue:** Generic httpx.HTTPError without additional context
   - **Evidence:** openrouter_client.py:87 - raise_for_status() without custom message
   - **Recommendation:** Catch and re-raise with request details for easier debugging (can be deferred)

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Dagster web UI accessible at localhost:3000 via `uv run dagster dev` | IMPLEMENTED | pyproject.toml:64-65 [tool.dagster] config; definitions.py:8-13 Dagster Definitions; Background process logs show "Serving dagster-webserver on http://127.0.0.1:3000" |
| AC2 | Input directory and files created | IMPLEMENTED | storage/input/ exists at project root (architectural change from backend/storage/input/ per user decision); manual_links.txt and monitoring_list.txt verified via test command |
| AC3 | Environment variables loaded correctly from `.env` file | IMPLEMENTED | .env:1-6 defines all required vars; openrouter_client.py:8-12 loads dotenv; Dagster logs confirm "Loaded environment variables from .env file: OPENROUTER_API_KEY,OPENROUTER_MODEL,DAGSTER_HOME" |
| AC4 | OpenRouter resource initializes without errors | IMPLEMENTED | openrouter_client.py:15-103 complete implementation; openrouter_client.py:39-50 validation logic; definitions.py:10-12 resource registration; tests/test_openrouter_client.py:46-53 validates successful initialization |

**Summary:** 4 of 4 acceptance criteria fully implemented ✓

### Task Completion Validation

All 22 tasks marked as complete `[x]` have been systematically verified:

| Task Category | Tasks | Verified | Questionable | False Completions |
|---------------|-------|----------|--------------|-------------------|
| Project Setup | 2 | 2 | 0 | 0 |
| Core Dependencies | 7 | 7 | 0 | 0 |
| Dev Dependencies | 3 | 3 | 0 | 0 |
| Storage Setup | 4 | 4 | 0 | 0 |
| Configuration | 1 | 1 | 0 | 0 |
| OpenRouter Client | 4 | 4 | 0 | 0 |
| Verification | 1 | 1 | 0 | 0 |

**Summary:** 22 of 22 completed tasks verified ✓ | 0 questionable | 0 falsely marked complete ✓

**Evidence samples:**
- Scaffolding: dagster_project/assets.py exists (scaffolded files)
- Dependencies: pyproject.toml:11-17 lists all deps; `uv pip list` confirms installation
- Storage: test command verified directory and file existence
- OpenRouter client: openrouter_client.py:15-103 complete implementation
- Tests: All 19 tests passing (pytest output)

### Test Coverage and Gaps

**Test Coverage:** Excellent ✓

- **Test Count:** 19 tests, all passing
- **Test Categories:**
  - Environment tests (4 tests): .env file, variable loading, defaults, path validation
  - Storage tests (4 tests): directory and file existence
  - OpenRouter client tests (5 tests): initialization, config, validation, API calls, response parsing
  - Integration tests (5 tests): Dagster definitions, resource registration, project structure, environment config, resource initialization
  - Contract tests: 1 (environment configuration)

**Test Quality:** ✓
- Proper use of pytest fixtures for setup and teardown
- Mocking used correctly for external dependencies (httpx.Client)
- Tests are deterministic and independent
- Good separation of unit vs integration tests
- Comprehensive edge case coverage (missing API key, invalid responses)

**Coverage Mapping:**
- AC1 (Dagster UI): Covered by integration tests + manual verification via background process
- AC2 (Storage): Covered by storage tests (4 tests)
- AC3 (Environment): Covered by environment tests (4 tests)
- AC4 (OpenRouter): Covered by OpenRouter client tests (5 tests) + integration tests

**Gaps:** None identified - all acceptance criteria have corresponding tests ✓

### Architectural Alignment

**Architecture Decision:** ✓ Flatter project structure adopted
- Original plan: `backend/dagster_project/` and `backend/storage/`
- Actual implementation: `dagster_project/` and `storage/` at project root
- **Rationale:** User decision to remove backend folder as unnecessary nesting
- **Impact:** None negative; actually simplifies structure
- **Documentation:** Well-documented in story completion notes

**Dagster Patterns:** ✓ Correctly implemented
- ConfigurableResource pattern used properly for OpenRouter client
- Resource lifecycle managed via setup_for_execution()
- Clean separation between resource class and factory instance
- Definitions configured with proper resource registration

**Project Structure:** ✓
```
dagster_project/
├── __init__.py
├── definitions.py      # Main Dagster definitions
├── assets.py           # Asset definitions (scaffolded)
└── resources/
    ├── __init__.py
    └── openrouter_client.py  # OpenRouter API client resource

storage/
└── input/
    ├── manual_links.txt
    └── monitoring_list.txt

tests/
├── test_environment.py
├── test_storage.py
├── test_openrouter_client.py
└── integration/
    └── test_project_setup.py
```

**Tech Spec Compliance:** ⚠️ N/A - No tech spec found (noted as WARNING in Step 2)

### Security Notes

**Security Findings:**

1. **[HIGH] .env file not in .gitignore** ⚠️
   - Risk: Accidental commit of secrets to version control
   - Current state: .env contains placeholder key only (no immediate exposure)
   - Required action: Add `.env` to .gitignore before story completion

**Security Strengths:** ✓
- Environment variables used for secrets (not hardcoded)
- HTTPS endpoint for API calls (openrouter_client.py:34)
- Proper validation prevents execution without API key (openrouter_client.py:39-45)
- No SQL injection risks (no database yet)
- No XSS risks (backend-only)

**Security Recommendations:**
- Consider adding .env.example template with placeholder values for documentation
- Future: Add rate limiting for API calls to prevent abuse/cost overruns
- Future: Consider using secret management service for production (e.g., AWS Secrets Manager, HashiCorp Vault)

### Best-Practices and References

**Frameworks and Patterns Used:**
- **Dagster ConfigurableResource:** [Dagster Resources Docs](https://docs.dagster.io/concepts/resources)
- **Pydantic Field with default_factory:** [Pydantic Docs](https://docs.pydantic.dev/latest/concepts/fields/)
- **httpx Client:** [httpx Documentation](https://www.python-httpx.org/)
- **python-dotenv:** [python-dotenv GitHub](https://github.com/theskumar/python-dotenv)
- **pytest fixtures:** [pytest Documentation](https://docs.pytest.org/en/stable/fixture.html)

**Code Quality Tools:**
- ruff (linter/formatter): All checks passing
- ty (type checker): All checks passing (after fix in step 1)
- pytest: 19/19 tests passing

**Best Practices Observed:** ✓
- Fail-fast validation in resource initialization
- Comprehensive docstrings with type hints
- Environment-based configuration
- Context manager for resource cleanup (httpx.Client)
- Proper test isolation and mocking

### Action Items

#### Code Changes Required

- [ ] [High] Add `.env` to .gitignore to prevent committing secrets [file: .gitignore:3]

#### Advisory Notes

- Note: Consider adding .env.example template file for documentation (shows required env vars without exposing secrets)
- Note: Future enhancement: Add retry logic with exponential backoff for OpenRouter API calls (can be in future story)
- Note: Future enhancement: Add response validation for malformed API responses (can be in future story)
- Note: Consider documenting the placeholder API key replacement process in README or setup docs

### Final Approval

**Date:** 2025-11-01
**Reviewer:** BMad

✅ **APPROVED** - Security fix verified and applied. All action items resolved.

**Verification:**
- .gitignore:68 now includes `.env` (plus comprehensive env file coverage)
- All 4 acceptance criteria remain fully implemented
- All 22 tasks verified complete
- All 19 tests passing
- No blocking issues remaining

Story marked as **DONE** and ready for next story.

### Architectural Decisions & Follow-up Work

**Decision:** Defer LOW severity improvements to Story 1.1 (Quick Refactor)

After review discussion, identified that using the official OpenAI Python library (already installed) instead of custom httpx implementation would automatically address all 3 LOW severity findings:
- Built-in retry logic with exponential backoff
- Better error handling and context
- Response validation

**Story 1.1 scope:**
- Replace httpx-based implementation with OpenAI library
- Update tests to match new implementation
- Remove httpx dependency from pyproject.toml
- Estimated effort: ~10 minutes (clean refactor)

This is a quality improvement, not a blocker. Story 1 is complete and functional as-is.

### Change Log

- **2025-11-01:** Senior Developer Review notes appended (BMad)
- **2025-11-01:** Security fix applied (.env added to .gitignore)
- **2025-11-01:** Final approval granted - Story marked DONE (BMad)
