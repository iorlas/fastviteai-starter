import hashlib


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()
