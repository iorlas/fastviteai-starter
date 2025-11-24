import hashlib
import json
from pathlib import Path
from typing import TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel

from ailabbrains.utils.paths import get_cache_path

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

DEFAULT_CACHE_DIR = get_cache_path() / "openai_structured_outputs"


def compute_cache_key(
    messages: list[dict],
    model: str,
    response_model: type[BaseModel],
    temperature: float,
    max_tokens: int,
) -> str:
    """Generate cache key from request parameters including full schema structure.

    Key includes complete JSON schema to invalidate cache when schema structure changes:
    - Fields are added/removed
    - Field types change
    - Validation constraints change
    - Field descriptions change

    Uses model_json_schema() to capture the complete schema structure that OpenAI's
    structured outputs API uses.
    """
    schema_dict = response_model.model_json_schema()

    key_components = {
        "messages": messages,
        "model": model,
        "schema_structure": schema_dict,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    key_string = json.dumps(key_components, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


async def cached_parse[T: BaseModel](
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    response_model: type[T],
    temperature: float = 0,
    max_tokens: int = 8192,
    cache_dir: Path | None = None,
) -> T:
    """Call OpenAI's structured output API with filesystem caching.

    Caches parsed Pydantic objects as JSON files. Cache key includes schema name
    to prevent collisions when different response_models are used.

    Args:
        client: AsyncOpenAI client
        model: Model name (e.g., "gpt-4o", "mistralai/mistral-medium-3.1")
        messages: Chat messages
        response_model: Pydantic model class for structured output
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        cache_dir: Directory for cache files (default: artifacts/cache/openai_structured_outputs)

    Returns:
        Parsed Pydantic object of type response_model
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    cache_dir.mkdir(parents=True, exist_ok=True)

    schema_name = response_model.__name__
    cache_key = compute_cache_key(messages, model, response_model, temperature, max_tokens)
    cache_file = cache_dir / f"{cache_key}.json"

    if cache_file.exists():
        logger.info(
            "openai_parse_cache.hit",
            model=model,
            schema=schema_name,
            cache_key=cache_key[:16],
        )
        try:
            cached_json = cache_file.read_text()
            return response_model.model_validate_json(cached_json)
        except Exception as e:
            logger.warning(
                "openai_parse_cache.invalid",
                model=model,
                schema=schema_name,
                cache_key=cache_key[:16],
                error=str(e),
            )
            cache_file.unlink()

    logger.info(
        "openai_parse_cache.miss",
        model=model,
        schema=schema_name,
        cache_key=cache_key[:16],
    )

    response = await client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_model,
    )

    parsed = response.choices[0].message.parsed

    if parsed is None:
        raise ValueError(f"OpenAI returned None for parsed message. Response: {response}")

    try:
        cache_file.write_text(parsed.model_dump_json(indent=2))
        logger.info(
            "openai_parse_cache.saved",
            model=model,
            schema=schema_name,
            cache_key=cache_key[:16],
        )
    except Exception as e:
        logger.warning(
            "openai_parse_cache.save_failed",
            model=model,
            schema=schema_name,
            error=str(e),
        )

    return parsed
