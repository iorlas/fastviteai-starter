import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from dagster import InputContext, IOManager, OutputContext

logger = structlog.get_logger()


class BronzeIOManager(IOManager):
    def __init__(self, base_dir: str = "artifacts/bronze"):
        self.base_dir = Path(base_dir)
        self.raw_links_dir = self.base_dir / "raw_links"
        self.raw_html_dir = self.base_dir / "raw_html"

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        if isinstance(obj, list):
            self._handle_output_link_list(context, obj)
        elif isinstance(obj, dict) and "html_content" in obj:
            self._handle_output_html(context, obj)
        else:
            logger.error("Unknown output type", obj_type=type(obj).__name__)
            msg = f"BronzeIOManager cannot handle type: {type(obj).__name__}"
            raise TypeError(msg)

    def load_input(self, context: InputContext) -> Any:
        asset_key = context.asset_key.path[-1] if context.asset_key else "unknown"

        if "raw_links" in asset_key:
            return self._load_input_link_list(context)
        elif "raw_html" in asset_key:
            return self._load_input_html(context)
        else:
            logger.error("Unknown input asset type", asset_key=asset_key)
            msg = f"BronzeIOManager cannot load asset: {asset_key}"
            raise TypeError(msg)

    def _handle_output_link_list(self, context: OutputContext, link_list: list) -> None:
        sorted_links = sorted(link_list)
        links_str = "".join(sorted_links)
        hash_value = hashlib.sha256(links_str.encode()).hexdigest()

        metadata = {
            "links": link_list,
            "created_at": datetime.now(UTC).isoformat(),
            "link_count": len(link_list),
        }

        output_path = self.raw_links_dir / f"{hash_value}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            "Saved link list to bronze layer",
            path=str(output_path),
            link_count=len(link_list),
            hash=hash_value[:16],
        )

    def _load_input_link_list(self, context: InputContext) -> list:
        upstream_key = context.upstream_output.asset_key if context.upstream_output else None

        if not upstream_key:
            logger.warning("No upstream output for link list")
            return []

        pattern = "*.json"
        files = sorted(self.raw_links_dir.glob(pattern))

        if not files:
            logger.warning("No link list files found", directory=str(self.raw_links_dir))
            return []

        latest_file = files[-1]

        try:
            with latest_file.open() as f:
                data = json.load(f)
            logger.info("Loaded link list from bronze layer", path=str(latest_file))
            return data.get("links", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("Failed to load link list", path=str(latest_file), error=str(e))
            return []

    def _handle_output_html(self, context: OutputContext, html_data: dict) -> None:
        url = html_data["url"]
        html_content = html_data["html_content"]
        hash_value = hashlib.sha256(url.encode()).hexdigest()

        metadata = {
            "url": url,
            "content": html_content,
            "created_at": datetime.now(UTC).isoformat(),
            "content_length": len(html_content),
            "download_info": html_data.get("download_info", {}),
        }

        output_path = self.raw_html_dir / f"{hash_value}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            "Saved HTML content to bronze layer",
            path=str(output_path),
            url=url,
            hash=hash_value[:16],
        )

    def _load_input_html(self, context: InputContext) -> dict:
        upstream_key = context.upstream_output.asset_key if context.upstream_output else None

        if not upstream_key:
            logger.warning("No upstream output for HTML content")
            return {}

        pattern = "*.json"
        files = sorted(self.raw_html_dir.glob(pattern))

        if not files:
            logger.warning("No HTML files found", directory=str(self.raw_html_dir))
            return {}

        latest_file = files[-1]

        try:
            with latest_file.open() as f:
                data = json.load(f)
            logger.info("Loaded HTML content from bronze layer", path=str(latest_file))
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("Failed to load HTML content", path=str(latest_file), error=str(e))
            return {}


class SilverIOManager(IOManager):
    def __init__(self, base_dir: str = "artifacts/silver"):
        self.base_dir = Path(base_dir)
        self.extracted_content_dir = self.base_dir / "extracted_content"
        self.summaries_dir = self.base_dir / "summaries"

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                if (
                    isinstance(item, dict)
                    and "type" in item
                    and item["type"] in ["html", "youtube"]
                ):
                    self._handle_output_extracted_content(context, item)
                elif isinstance(item, dict) and "status" in item:
                    self._handle_output_summary(context, item)
                else:
                    logger.error("Unknown list item type", obj_type=type(item).__name__)
                    msg = f"SilverIOManager cannot handle list item type: {type(item).__name__}"
                    raise TypeError(msg)
        elif isinstance(obj, dict) and "type" in obj and obj["type"] in ["html", "youtube"]:
            self._handle_output_extracted_content(context, obj)
        elif isinstance(obj, dict) and "status" in obj:
            self._handle_output_summary(context, obj)
        else:
            logger.error("Unknown output type", obj_type=type(obj).__name__)
            msg = f"SilverIOManager cannot handle type: {type(obj).__name__}"
            raise TypeError(msg)

    def load_input(self, context: InputContext) -> Any:
        asset_key = context.asset_key.path[-1] if context.asset_key else "unknown"

        if "extracted_content" in asset_key:
            return self._load_input_extracted_content(context)
        elif "summaries" in asset_key or "summary" in asset_key:
            return self._load_input_summary(context)
        else:
            logger.error("Unknown input asset type", asset_key=asset_key)
            msg = f"SilverIOManager cannot load asset: {asset_key}"
            raise TypeError(msg)

    def _handle_output_extracted_content(self, context: OutputContext, content_data: dict) -> None:
        url = content_data["url"]
        hash_value = hashlib.sha256(url.encode()).hexdigest()

        now = datetime.now(UTC).isoformat()
        metadata = {
            "url": url,
            "type": content_data["type"],
            "title": content_data.get("title", ""),
            "content": content_data.get("content", ""),
            "metadata": content_data.get("metadata", {}),
            "lineage": content_data.get("lineage", {}),
            "created_at": now,
            "updated_at": now,
        }

        output_path = self.extracted_content_dir / f"{hash_value}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            "Saved extracted content to silver layer",
            path=str(output_path),
            url=url,
            content_type=content_data["type"],
            hash=hash_value[:16],
        )

    def _load_input_extracted_content(self, context: InputContext) -> dict:
        upstream_key = context.upstream_output.asset_key if context.upstream_output else None

        if not upstream_key:
            logger.warning("No upstream output for extracted content")
            return {}

        pattern = "*.json"
        files = sorted(self.extracted_content_dir.glob(pattern))

        if not files:
            logger.warning(
                "No extracted content files found", directory=str(self.extracted_content_dir)
            )
            return {}

        latest_file = files[-1]

        try:
            with latest_file.open() as f:
                data = json.load(f)
            logger.info("Loaded extracted content from silver layer", path=str(latest_file))
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("Failed to load extracted content", path=str(latest_file), error=str(e))
            return {}

    def _handle_output_summary(self, context: OutputContext, summary_data: dict) -> None:
        url = summary_data["url"]
        hash_value = hashlib.sha256(url.encode()).hexdigest()

        now = datetime.now(UTC).isoformat()
        metadata = {
            "url": url,
            "title": summary_data.get("title", url),
            "status": summary_data["status"],
            "created_at": now,
            "updated_at": now,
        }

        if summary_data["status"] == "success":
            metadata.update(
                {
                    "summary": summary_data.get("summary", ""),
                    "model": summary_data.get("model", ""),
                    "tokens_used": summary_data.get("tokens_used"),
                    "latency_ms": summary_data.get("latency_ms"),
                }
            )
        else:
            metadata.update(
                {
                    "error": summary_data.get("error", ""),
                    "error_type": summary_data.get("error_type", ""),
                }
            )

        metadata["lineage"] = summary_data.get("lineage", {})

        json_path = self.summaries_dir / f"{hash_value}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with json_path.open("w") as f:
            json.dump(metadata, f, indent=2)

        md_path = self.summaries_dir / f"{hash_value}.md"
        md_content = self._generate_markdown_summary(metadata)
        with md_path.open("w") as f:
            f.write(md_content)

        logger.info(
            "Saved summary to silver layer",
            path=str(json_path),
            markdown_path=str(md_path),
            url=url,
            status=summary_data["status"],
            hash=hash_value[:16],
        )

    def _generate_markdown_summary(self, metadata: dict) -> str:
        url = metadata["url"]
        status = metadata["status"]
        updated_at = metadata["updated_at"]

        if status == "success":
            title = metadata.get("title", url)
            summary = metadata.get("summary", "")
            model = metadata.get("model", "")
            tokens_used = metadata.get("tokens_used", "N/A")
            latency_ms = metadata.get("latency_ms", "N/A")

            return f"""# {title}

**URL:** {url}
**Status:** Success
**Model:** {model}

## Summary

{summary}

---
**Generated:** {updated_at}
**Tokens:** {tokens_used}
**Latency:** {latency_ms}ms
"""
        else:
            title = metadata.get("title", "Summary Failed")
            error = metadata.get("error", "")
            error_type = metadata.get("error_type", "")

            return f"""# {title}

**URL:** {url}
**Status:** Failed

## Error

{error}

**Error Type:** {error_type}

---
**Generated:** {updated_at}
"""

    def _load_input_summary(self, context: InputContext) -> dict:
        upstream_key = context.upstream_output.asset_key if context.upstream_output else None

        if not upstream_key:
            logger.warning("No upstream output for summary")
            return {}

        pattern = "*.json"
        files = sorted(self.summaries_dir.glob(pattern))

        if not files:
            logger.warning("No summary files found", directory=str(self.summaries_dir))
            return {}

        latest_file = files[-1]

        try:
            with latest_file.open() as f:
                data = json.load(f)
            logger.info("Loaded summary from silver layer", path=str(latest_file))
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("Failed to load summary", path=str(latest_file), error=str(e))
            return {}
