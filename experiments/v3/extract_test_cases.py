import json
from pathlib import Path

import structlog

logger = structlog.get_logger()


def main():
    silver_dir = Path("artifacts/silver/silver_extracted_content")
    test_cases_dir = Path("experiments/v3/test_cases")
    test_cases_dir.mkdir(parents=True, exist_ok=True)

    if not silver_dir.exists():
        logger.error("silver_extracted_content directory not found", path=str(silver_dir))
        print(f"Error: {silver_dir} not found")
        print("Make sure you have run the dagster pipeline to extract content")
        return

    json_files = sorted(silver_dir.glob("*.json"))

    if not json_files:
        print("No extracted content files found")
        return

    print(f"\nFound {len(json_files)} extracted content files\n")

    cases = []
    for idx, file_path in enumerate(json_files, 1):
        with open(file_path) as f:
            data = json.load(f)

        if not data.get("extraction_success"):
            continue

        title = data.get("title", "Untitled")
        url = data.get("url", "")
        content_type = data.get("content_type", "unknown")
        content_length = len(data.get("content", ""))

        cases.append(
            {
                "idx": idx,
                "file_path": file_path,
                "data": data,
                "title": title,
                "url": url,
                "content_type": content_type,
                "content_length": content_length,
            }
        )

        print(f"{idx:2d}. [{content_type:8s}] {title[:70]}")
        print(f"    {url[:80]}")
        print(f"    Length: {content_length:,} chars")
        print()

    if not cases:
        print("No successfully extracted content found")
        return

    print("\nEnter the numbers of test cases to extract (comma-separated, e.g., 1,3,5)")
    print("Or press Enter to skip: ", end="")

    selection = input().strip()

    if not selection:
        print("No test cases selected")
        return

    try:
        selected_indices = [int(x.strip()) for x in selection.split(",")]
    except ValueError:
        print("Invalid input format")
        return

    existing_cases = sorted(test_cases_dir.glob("case_*.json"))
    next_case_num = len(existing_cases) + 1

    for idx in selected_indices:
        case = next((c for c in cases if c["idx"] == idx), None)
        if not case:
            print(f"Invalid selection: {idx}")
            continue

        case_filename = f"case_{next_case_num:03d}.json"
        case_path = test_cases_dir / case_filename

        test_case_data = {
            "title": case["data"]["title"],
            "content": case["data"]["content"],
            "content_type": case["data"]["content_type"],
            "url": case["data"]["url"],
            "url_hash": case["data"]["url_hash"],
            "metadata": case["data"].get("metadata", {}),
        }

        with open(case_path, "w") as f:
            json.dump(test_case_data, f, indent=2)

        print(f"✓ Created {case_filename}: {case['title'][:60]}")

        insights_path = test_cases_dir / f"case_{next_case_num:03d}.insights.json"
        if not insights_path.exists():
            print(f"  → Remember to create {insights_path.name}")

        next_case_num += 1

    print(f"\n✓ Extracted {len(selected_indices)} test cases to {test_cases_dir}")
    print("\nNext steps:")
    print("1. Create .insights.json files for each test case")
    print('   Format: [{"insight": "...", "vitality": "vital"}]')
    print("2. See experiments/v1/eval_dataset/example_002.insights.json for reference")


if __name__ == "__main__":
    main()
