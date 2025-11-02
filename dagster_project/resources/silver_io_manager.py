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

    Stores transformed data partitioned by URL hash.

    Directory structure:
        {base_dir}/{asset_name}/{url_hash}.json

    For summaries, also generates markdown files for human readability.
    """

    base_dir: str = str(SILVER_EXTRACTED_CONTENT_DIR.parent)

    def _get_path(self, context: OutputContext | InputContext) -> Path:
        """Construct path using asset key and partition key (URL hash)."""
        asset_name = context.asset_key.path[-1]
        partition_key = context.partition_key

        if not partition_key:
            msg = f"SilverIOManager requires partitioned assets, got {context.asset_key}"
            raise ValueError(msg)

        return Path(self.base_dir) / asset_name / f"{partition_key}.json"

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """Save transformed data to silver layer."""
        output_path = self._get_path(context)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC).isoformat()
        metadata = {
            **obj,
            "created_at": now,
            "updated_at": now,
            "partition_key": context.partition_key,
        }

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        asset_name = context.asset_key.path[-1]
        if "summar" in asset_name:
            self._generate_markdown(output_path, metadata)

        logger.info(
            "silver.saved",
            asset=asset_name,
            partition=context.partition_key,
            path=str(output_path),
        )

    def load_input(self, context: InputContext) -> Any:
        """Load transformed data from silver layer."""
        input_path = self._get_path(context)

        if not input_path.exists():
            msg = f"Silver data not found: {input_path}"
            logger.error("silver.not_found", path=str(input_path))
            raise FileNotFoundError(msg)

        try:
            with input_path.open() as f:
                data = json.load(f)

            logger.info(
                "silver.loaded",
                asset=context.asset_key.path[-1],
                partition=context.partition_key,
                path=str(input_path),
            )

            return data

        except json.JSONDecodeError as e:
            logger.error("silver.load_error", path=str(input_path), error=str(e))
            raise

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
