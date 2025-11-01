# Story 1.1: Refactor OpenRouter Client to Use OpenAI Library

Status: drafted

## Story

As a developer,
I want to use the official OpenAI library for OpenRouter API calls,
so that I get built-in retry logic, better error handling, and response validation.

## Context

During code review of Story 1, identified that the custom httpx-based OpenRouter client implementation has 3 LOW severity findings that would be automatically addressed by using the official OpenAI Python library (already installed in dependencies):
1. No retry logic for API calls
2. No input validation on API responses
3. Error context could be enhanced

OpenRouter is OpenAI API-compatible, so we can use the official client with just a base URL change.

## Acceptance Criteria

1. OpenRouter client uses OpenAI library instead of httpx
2. Client configured with `base_url="https://openrouter.ai/api/v1"`
3. Built-in retry logic enabled (`max_retries=3`)
4. Debug logging added for API calls (request and response metadata)
5. All existing tests pass with updated implementation
6. httpx dependency removed from pyproject.toml (if not used elsewhere)

## Tasks / Subtasks

- [ ] Update `dagster_project/resources/openrouter_client.py`:
  - [ ] Replace httpx imports with openai imports
  - [ ] Update OpenRouterClient to use OpenAI client
  - [ ] Configure base_url and max_retries in setup_for_execution
  - [ ] Update chat_completion to use client.chat.completions.create
  - [ ] Add debug logging: log request metadata (model, message count, temperature)
  - [ ] Add debug logging: log response metadata (completion tokens, model used)
  - [ ] Update get_completion_text to use OpenAI response object
- [ ] Update tests:
  - [ ] `tests/test_openrouter_client.py` - Update mocks for OpenAI library
  - [ ] Verify all 19 tests still pass
- [ ] Remove httpx from dependencies:
  - [ ] Check if httpx is used elsewhere (grep for httpx imports)
  - [ ] If not used: `uv remove httpx`
  - [ ] If used elsewhere: Document and keep
- [ ] Run quality checks: `make check`

## Dev Notes

### Technical Summary

Refactor OpenRouter client to use official OpenAI Python library for better reliability and maintainability. This is a drop-in replacement since OpenRouter is OpenAI API-compatible.

### Estimated Effort

0.5 story points (~15-20 minutes)

### Benefits

- ✅ Built-in retry logic with exponential backoff
- ✅ Better error messages with request context
- ✅ Response validation and type safety
- ✅ Debug logging for API call monitoring and troubleshooting
- ✅ Visibility into token usage and model performance
- ✅ Streaming support (for future use)
- ✅ Async support (for future use)
- ✅ Less code to maintain
- ✅ Well-tested library used by thousands of projects

### Implementation Notes

**Debug Logging Example:**
```python
def chat_completion(
    self,
    context,  # Add context parameter for logging
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> Any:
    """Make a chat completion request to OpenRouter."""
    # Log request metadata
    context.log.debug(
        f"OpenRouter API request: model={self.model}, "
        f"messages={len(messages)}, temp={temperature}, "
        f"max_tokens={max_tokens or 'unlimited'}"
    )

    response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )

    # Log response metadata (token usage, model)
    context.log.debug(
        f"OpenRouter API response: model={response.model}, "
        f"completion_tokens={response.usage.completion_tokens}, "
        f"prompt_tokens={response.usage.prompt_tokens}, "
        f"total_tokens={response.usage.total_tokens}"
    )

    return response
```

**Note:** This requires passing `context` from assets to the resource method. Assets will call it as:
```python
@asset
def my_asset(context, openrouter: OpenRouterClient):
    response = openrouter.chat_completion(
        context,  # Pass context for logging
        messages=[{"role": "user", "content": "Hello"}]
    )
```

### References

- OpenAI Python library: https://github.com/openai/openai-python
- OpenRouter API compatibility: https://openrouter.ai/docs
- Story 1 review notes: docs/stories/story-link-pipeline-1.md (Architectural Decisions section)
- Dagster logging: https://docs.dagster.io/concepts/logging/loggers
