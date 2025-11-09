#!/usr/bin/env python3
"""One-off script to generate LLM input from bronze artifacts and show prompt preview."""

import json
from pathlib import Path

from dagster_project.core.summary.input_compiler import compile_summary_input

URL = "https://support.mozilla.org/en-US/forums/contributors/717446"
ARTIFACTS_BASE = "artifacts/bronze"
OUTPUT_FILE = "llm_input.json"

if __name__ == "__main__":
    summary_input = compile_summary_input(url=URL, artifacts_base_path=ARTIFACTS_BASE)

    # Convert Pydantic model to dict, then to JSON
    output_data = summary_input.model_dump(mode="json")

    # Save to file (compact JSON, no whitespace, unicode chars)
    output_path = Path(OUTPUT_FILE)
    output_path.write_text(json.dumps(output_data, ensure_ascii=False))

    print(f"✓ Generated LLM input saved to {OUTPUT_FILE}")
    print(f"  URL: {summary_input.url}")
    print(f"  Title: {summary_input.title}")
    print(f"  Content type: {summary_input.content_type}")
    print(f"  Content length: {len(summary_input.content)} chars")
    print(f"  Discussions: {'Yes' if summary_input.discussions else 'No'}")

    # Show XML-formatted prompt preview
    print("\n" + "=" * 80)
    print("LLM PROMPT PREVIEW (XML FORMAT)")
    print("=" * 80)

    content_type_label = "video transcript" if summary_input.content_type == "youtube" else "article"

    # Build prompt like summarizer does
    user_content_parts = [
        "<content>",
        f"Title: {summary_input.title}",
        f"URL: {summary_input.url}",
        f"Type: {content_type_label}",
        "",
        summary_input.content[:800] + "..." if len(summary_input.content) > 800 else summary_input.content,
        "</content>",
    ]

    if summary_input.discussions:
        user_content_parts.extend(
            [
                "",
                "<discussions>",
                summary_input.discussions[:2500] + "..." if len(summary_input.discussions) > 2500 else summary_input.discussions,
                "</discussions>",
            ]
        )

    print("\n".join(user_content_parts))

    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Total content: {len(summary_input.content):,} chars")
    if summary_input.discussions:
        print(f"Total discussions: {len(summary_input.discussions):,} chars")
        print(f"Combined total: {len(summary_input.content) + len(summary_input.discussions):,} chars")
