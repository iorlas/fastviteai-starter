import hashlib


def compute_url_hash(url: str) -> str:
    """Compute deterministic hash for a URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def normalize_url(url: str) -> str:
    """Normalize URL to canonical form for deduplication.

    Future: Handle redirects, remove tracking params, normalize domains.
    For now: basic cleanup.
    """
    url = url.strip()
    if url.endswith("/"):
        url = url[:-1]
    return url
