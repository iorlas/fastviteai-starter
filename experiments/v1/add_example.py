import hashlib
import json
import sys
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))

from dagster_project.assets.content_extraction import ExtractedContent
from dagster_project.ops.html_extractor import HTMLExtractionError, extract_html_content

logger = structlog.get_logger()


def generate_url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def find_next_example_number(eval_dataset_dir: Path) -> int:
    """Find next available example number"""
    max_num = 0
    for json_file in eval_dataset_dir.glob("example_*.json"):
        if json_file.stem.endswith(".insights"):
            continue
        try:
            num = int(json_file.stem.split("_")[1])
            max_num = max(max_num, num)
        except (IndexError, ValueError):
            continue
    return max_num + 1


def add_example_from_url(url: str, eval_dataset_dir: Path) -> Path:
    """Extract content from URL and save as new example"""

    logger.info("extracting_content", url=url)

    try:
        html_content = extract_html_content(url)

        url_hash = generate_url_hash(url)

        extracted = ExtractedContent(
            url=url,
            url_hash=url_hash,
            content_type="html",
            title=html_content.title,
            text=html_content.content,
            metadata={
                "author": html_content.author,
                "publish_date": html_content.publish_date,
                **html_content.metadata,
            },
            extraction_success=True,
            error_message=None,
        )

        example_num = find_next_example_number(eval_dataset_dir)
        output_file = eval_dataset_dir / f"example_{example_num:03d}.json"

        data = {
            "url": extracted.url,
            "url_hash": extracted.url_hash,
            "content_type": extracted.content_type,
            "title": extracted.title,
            "text": extracted.text,
            "metadata": extracted.metadata,
            "extraction_success": extracted.extraction_success,
            "error_message": extracted.error_message,
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("example_created", file=str(output_file), title=extracted.title)

        return output_file

    except HTMLExtractionError as e:
        logger.error("extraction_failed", url=url, error=str(e))
        raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_example.py <url>")
        sys.exit(1)

    url = sys.argv[1]

    eval_dataset_dir = Path(__file__).parent / "eval_dataset"
    eval_dataset_dir.mkdir(parents=True, exist_ok=True)

    output_file = add_example_from_url(url, eval_dataset_dir)

    print(f"\nExample created: {output_file}")
    print("\nNext steps:")
    print(f"1. (Optional) Create insights file: {output_file.stem}.insights.json")
    print("2. Run experiments: python experiments/summarization_experiments.py")


if __name__ == "__main__":
    main()
