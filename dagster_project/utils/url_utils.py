import hashlib


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def extract_aggregator_info(url_data: dict) -> dict:
    if not url_data.get("original_url"):
        return {}
    return {
        "original_url": url_data["original_url"],
        "aggregator_type": url_data["aggregator_type"],
        "aggregator_title": url_data["aggregator_title"],
    }
