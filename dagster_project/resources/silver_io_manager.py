import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from dagster import ConfigurableIOManager, InputContext, OutputContext

from dagster_project.utils.paths import SILVER_EXTRACTED_CONTENT_DIR

logger = structlog.get_logger()


class SilverIOManager(ConfigurableIOManager):
    """IO Manager for Silver layer (cleaned, standardized data).

    Stores transformed data by URL hash.

    Directory structure:
        {base_dir}/{asset_name}/{url_hash}.json

    For summaries, also generates markdown files for human readability.
    """

    base_dir: str = str(SILVER_EXTRACTED_CONTENT_DIR.parent)

    def _get_path(self, asset_name: str, url_hash: str) -> Path:
        """Construct path using asset name and URL hash."""
        return Path(self.base_dir) / asset_name / f"{url_hash}.json"

    def exists(self, asset_name: str, url_hash: str) -> bool:
        """Check if data exists for given URL hash."""
        return self._get_path(asset_name, url_hash).exists()

    def save(self, asset_name: str, url_hash: str, data: dict) -> None:
        """Save transformed data to silver layer."""
        output_path = self._get_path(asset_name, url_hash)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC).isoformat()
        metadata = {
            **data,
            "created_at": now,
            "updated_at": now,
            "url_hash": url_hash,
        }

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        if "summar" in asset_name:
            self._generate_markdown(output_path, metadata)

        logger.info(
            "silver.saved",
            asset=asset_name,
            url_hash=url_hash,
            path=str(output_path),
        )

    def load(self, asset_name: str, url_hash: str) -> dict:
        """Load transformed data from silver layer."""
        input_path = self._get_path(asset_name, url_hash)

        if not input_path.exists():
            msg = f"Silver data not found: {input_path}"
            logger.error("silver.not_found", path=str(input_path))
            raise FileNotFoundError(msg)

        try:
            with input_path.open() as f:
                data = json.load(f)

            logger.info(
                "silver.loaded",
                asset=asset_name,
                url_hash=url_hash,
                path=str(input_path),
            )

            return data

        except json.JSONDecodeError as e:
            logger.error("silver.load_error", path=str(input_path), error=str(e))
            raise

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """Backward compatibility - not used in list-based processing."""
        pass

    def load_input(self, context: InputContext) -> Any:
        """Backward compatibility - not used in list-based processing."""
        pass

    def _generate_markdown(self, json_path: Path, metadata: dict) -> None:
        """Generate human-readable markdown for summaries."""
        md_path = json_path.with_suffix(".md")

        url = metadata.get("url", "Unknown")
        title = metadata.get("title", url)
        status = metadata.get("status", "unknown")

        if status == "success":
            summary = metadata.get("summary", "")
            model = metadata.get("model", "")
            tokens = metadata.get("tokens_used", "N/A")
            latency = metadata.get("latency_ms", "N/A")

            content = f"""# {title}

**URL:** {url}
**Status:** Success
**Model:** {model}

## Summary

{summary}

---
**Generated:** {metadata.get("updated_at", "N/A")}
**Tokens:** {tokens}
**Latency:** {latency}ms
"""
        else:
            error = metadata.get("error", "Unknown error")
            error_type = metadata.get("error_type", "")

            content = f"""# {title}

**URL:** {url}
**Status:** Failed

## Error

{error}

**Error Type:** {error_type}

---
**Generated:** {metadata.get("updated_at", "N/A")}
"""

        with md_path.open("w") as f:
            f.write(content)
