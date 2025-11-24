import hashlib
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    # Normalize scheme to https
    scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme

    # Lowercase the domain
    netloc = parsed.netloc.lower()

    # Remove trailing slash from path (unless it's just "/")
    path = parsed.path.rstrip("/") if parsed.path != "/" else parsed.path

    # Sort query parameters for consistent ordering
    query = ""
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Sort by key and maintain list values
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)

    # Ignore fragments
    fragment = ""

    return urlunparse((scheme, netloc, path, parsed.params, query, fragment))
