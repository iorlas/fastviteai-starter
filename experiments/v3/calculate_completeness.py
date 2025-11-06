import json
import sys
from pathlib import Path

import structlog

logger = structlog.get_logger()


def flatten_summary_to_text(structured_summary: dict) -> str:
    parts = []

    if "core_answer" in structured_summary:
        parts.append(structured_summary["core_answer"])

    if "unique_insights" in structured_summary:
        parts.extend(structured_summary["unique_insights"])

    if "core_insights" in structured_summary:
        for insight in structured_summary["core_insights"]:
            if isinstance(insight, dict):
                parts.append(insight.get("insight", ""))
                parts.append(insight.get("memory_aid", ""))
                parts.extend(insight.get("supporting_facts", []))
                parts.append(insight.get("quantitative_data", ""))
                parts.append(insight.get("why_it_matters", ""))
            else:
                parts.append(str(insight))

    if "people" in structured_summary:
        for entity in structured_summary["people"]:
            if isinstance(entity, dict):
                parts.append(entity.get("name", ""))
                parts.append(entity.get("context", ""))
                parts.append(entity.get("description", ""))
            else:
                parts.append(str(entity))

    if "organizations" in structured_summary:
        for entity in structured_summary["organizations"]:
            if isinstance(entity, dict):
                parts.append(entity.get("name", ""))
                parts.append(entity.get("context", ""))
            else:
                parts.append(str(entity))

    if "concepts" in structured_summary:
        for entity in structured_summary["concepts"]:
            if isinstance(entity, dict):
                parts.append(entity.get("name", ""))
                parts.append(entity.get("context", ""))
                parts.append(entity.get("description", ""))
            else:
                parts.append(str(entity))

    if "formulas_data" in structured_summary:
        for entity in structured_summary["formulas_data"]:
            if isinstance(entity, dict):
                parts.append(entity.get("name", ""))
                parts.append(entity.get("context", ""))
            else:
                parts.append(str(entity))

    if "examples_analogies" in structured_summary:
        for entity in structured_summary["examples_analogies"]:
            if isinstance(entity, dict):
                parts.append(entity.get("name", ""))
                parts.append(entity.get("context", ""))
            else:
                parts.append(str(entity))

    if "forward_looking" in structured_summary:
        parts.extend(structured_summary["forward_looking"])

    if "memory_aids" in structured_summary:
        aids = structured_summary["memory_aids"]
        if isinstance(aids, dict):
            parts.append(aids.get("key_phrase", ""))
            parts.append(aids.get("visual_metaphor", ""))
            parts.append(aids.get("mnemonic", ""))

    return " ".join(str(p) for p in parts if p).lower()


def check_insight_coverage(insight_text: str, summary_text: str) -> bool:
    insight_lower = insight_text.lower()

    words = insight_lower.split()
    if len(words) < 3:
        return False

    key_words = [w.strip("'\"()[]{}.,!?;:") for w in words if len(w) > 3]
    key_words = [
        w
        for w in key_words
        if w not in {"that", "with", "from", "this", "have", "been", "were", "will", "their", "about", "when", "which", "there"}
    ]

    if not key_words:
        return False

    match_count = sum(1 for w in key_words if w in summary_text)
    coverage_ratio = match_count / len(key_words)

    if coverage_ratio >= 0.5:
        return True

    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python calculate_completeness.py <run_file.json>")
        sys.exit(1)

    run_path = Path(sys.argv[1])

    if not run_path.exists():
        print(f"Run file not found: {run_path}")
        sys.exit(1)

    with open(run_path) as f:
        run_data = json.load(f)

    insights_file = run_data.get("insights_file")
    if not insights_file:
        print("No insights_file specified in run data")
        sys.exit(1)

    insights_path = Path(insights_file)
    if not insights_path.exists():
        print(f"Insights file not found: {insights_path}")
        print("Create it manually based on ground truth insights")
        sys.exit(1)

    with open(insights_path) as f:
        insights = json.load(f)

    structured_summary = run_data["output"]["structured_summary"]
    summary_text = flatten_summary_to_text(structured_summary)

    vital_insights = [i for i in insights if i.get("vitality") == "vital"]

    found_vital = []
    missing_vital = []

    for insight in vital_insights:
        insight_text = insight["insight"]
        if check_insight_coverage(insight_text, summary_text):
            found_vital.append(insight_text)
        else:
            missing_vital.append(insight_text)

    vital_coverage = (len(found_vital) / len(vital_insights) * 100) if vital_insights else 0

    run_data["evaluation"]["completeness"] = {
        "insights_found": found_vital,
        "insights_missing": missing_vital,
        "vital_insights_found": len(found_vital),
        "vital_insights_total": len(vital_insights),
        "vital_coverage_percent": round(vital_coverage, 1),
    }

    with open(run_path, "w") as f:
        json.dump(run_data, f, indent=2)

    print("\n✓ Completeness calculated")
    print(f"  Found: {len(found_vital)}/{len(vital_insights)} vital insights")
    print(f"  Coverage: {vital_coverage:.1f}%")
    print(f"\nUpdated: {run_path}")

    if missing_vital:
        print(f"\nMissing insights ({len(missing_vital)}):")
        for insight in missing_vital:
            print(f"  - {insight[:80]}...")


if __name__ == "__main__":
    main()
