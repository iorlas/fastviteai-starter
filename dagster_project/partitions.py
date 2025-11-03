import hashlib

from dagster import DynamicPartitionsDefinition

url_partitions = DynamicPartitionsDefinition(name="urls")


def compute_url_hash(url: str) -> str:
    """Compute deterministic hash for a URL to use as partition key."""
    return hashlib.sha256(url.encode()).hexdigest()


def normalize_url(url: str) -> str:
    """Normalize URL to canonical form for deduplication.

    Future: Handle redirects, remove tracking params, normalize domains.
    For now: basic cleanup.
    """
    url = url.strip()
    if url.endswith("/"):
        url = url[:-1]
    return url
