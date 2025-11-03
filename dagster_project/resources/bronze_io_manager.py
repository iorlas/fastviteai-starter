import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from dagster import ConfigurableIOManager, InputContext, OutputContext

from dagster_project.utils.paths import BRONZE_RAW_HTML_DIR

logger = structlog.get_logger()


class BronzeIOManager(ConfigurableIOManager):
    """IO Manager for Bronze layer (raw, immutable data).

    Stores data by URL hash. Each URL's raw data is saved once
    and cached forever (immutable bronze layer principle).

    Directory structure:
        {base_dir}/{asset_name}/{url_hash}.json
    """

    base_dir: str = str(BRONZE_RAW_HTML_DIR.parent)

    def _get_path(self, asset_name: str, url_hash: str) -> Path:
        """Construct path using asset name and URL hash."""
        return Path(self.base_dir) / asset_name / f"{url_hash}.json"

    def exists(self, asset_name: str, url_hash: str) -> bool:
        """Check if data exists for given URL hash."""
        return self._get_path(asset_name, url_hash).exists()

    def save(self, asset_name: str, url_hash: str, data: Any) -> None:
        """Save raw data to bronze layer.

        For bronze layer, we implement caching: if file exists, skip save.
        This ensures immutability and avoids re-downloading.
        """
        output_path = self._get_path(asset_name, url_hash)

        if output_path.exists():
            logger.info(
                "bronze.cache_hit",
                asset=asset_name,
                url_hash=url_hash,
                path=str(output_path),
            )
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "url_hash": url_hash,
        }

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            "bronze.saved",
            asset=asset_name,
            url_hash=url_hash,
            path=str(output_path),
        )

    def load(self, asset_name: str, url_hash: str) -> Any:
        """Load raw data from bronze layer."""
        input_path = self._get_path(asset_name, url_hash)

        if not input_path.exists():
            msg = f"Bronze data not found: {input_path}"
            logger.error("bronze.not_found", path=str(input_path))
            raise FileNotFoundError(msg)

        try:
            with input_path.open() as f:
                metadata = json.load(f)

            logger.info(
                "bronze.loaded",
                asset=asset_name,
                url_hash=url_hash,
                path=str(input_path),
            )

            return metadata.get("data")

        except json.JSONDecodeError as e:
            logger.error("bronze.load_error", path=str(input_path), error=str(e))
            raise

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """Backward compatibility - not used in list-based processing."""
        pass

    def load_input(self, context: InputContext) -> Any:
        """Backward compatibility - not used in list-based processing."""
        pass
