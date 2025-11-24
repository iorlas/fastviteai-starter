from openai import AsyncOpenAI

from ailabbrains.config import settings


def get_cached_openai_client(timeout: int = 30) -> AsyncOpenAI:
    """Create AsyncOpenAI client.

    Note: Caching is handled at application level via openai_parse_cache.py,
    not at HTTP level. This function now returns a regular AsyncOpenAI client.
    """
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_retries=3,
        timeout=float(timeout),
    )
