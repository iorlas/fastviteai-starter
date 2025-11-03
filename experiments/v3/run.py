import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import structlog
from dotenv import load_dotenv
from openai import OpenAI

from dagster_project.core.summarizer import SummaryGenerator, SummaryRequest

load_dotenv()
logger = structlog.get_logger()


def load_test_case(test_case_path: str) -> dict:
    with open(test_case_path) as f:
        return json.load(f)


def load_prompt(prompt_path: str) -> str:
    with open(prompt_path) as f:
        return f.read().strip()


def generate_run_filename(model: str, timestamp: str) -> str:
    model_slug = model.replace("/", "_").replace(":", "_").replace(".", "_")
    ts = datetime.fromisoformat(timestamp).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{model_slug}.json"


def main():
    parser = argparse.ArgumentParser(description="Run summarization experiment")
    parser.add_argument("--test-case", required=True, help="Path to test case JSON")
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("--system-prompt", required=True, help="Path to system prompt file")
    parser.add_argument("--user-prompt", required=True, help="Path to user prompt template file")
    parser.add_argument("--temperature", type=float, default=0, help="Temperature (default: 0)")
    parser.add_argument("--max-tokens", type=int, default=3000, help="Max tokens (default: 3000)")
    parser.add_argument("--notes", default="", help="Optional notes about this run")

    args = parser.parse_args()

    test_case = load_test_case(args.test_case)
    system_prompt = load_prompt(args.system_prompt)
    user_prompt_template = load_prompt(args.user_prompt)

    test_case_id = Path(args.test_case).stem
    insights_file = str(Path(args.test_case).with_suffix(".insights.json"))

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise ValueError("OPENAI_API_KEY required")

    openai_client = OpenAI(
        api_key=openai_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    generator = SummaryGenerator(
        openai_client=openai_client,
        model=args.model,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    logger.info(
        "experiment.started",
        test_case=test_case_id,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    request = SummaryRequest(
        content=test_case["content"],
        title=test_case["title"],
        content_type=test_case.get("content_type", "html"),
        url=test_case.get("url", ""),
    )

    start_time = time.time()
    result = generator.generate(request)
    elapsed_ms = int((time.time() - start_time) * 1000)

    timestamp = datetime.now(UTC).isoformat()

    run_data = {
        "timestamp": timestamp,
        "model": args.model,
        "config": {
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "system_prompt": system_prompt,
            "user_prompt_template": user_prompt_template,
            "notes": args.notes,
        },
        "input": {
            "test_case": test_case_id,
            "url": test_case.get("url", ""),
            "title": test_case["title"],
            "content": test_case["content"],
            "content_type": test_case.get("content_type", "html"),
            "content_length": len(test_case["content"]),
        },
        "output": {
            "structured_summary": result.structured_summary.model_dump(),
            "tokens_used": result.tokens_used,
            "latency_ms": result.latency_ms,
        },
        "evaluation": {
            "judgement": None,
            "completeness": {
                "insights_found": [],
                "insights_missing": [],
                "vital_coverage_percent": 0,
            },
        },
        "insights_file": insights_file,
    }

    runs_dir = Path("experiments/v3/runs")
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_filename = generate_run_filename(args.model, timestamp)
    run_path = runs_dir / run_filename

    with open(run_path, "w") as f:
        json.dump(run_data, f, indent=2)

    logger.info(
        "experiment.completed",
        run_file=str(run_path),
        tokens=result.tokens_used,
        latency_ms=result.latency_ms,
    )

    print("\n✓ Experiment completed")
    print(f"  Run file: {run_path}")
    print(f"  Tokens: {result.tokens_used}")
    print(f"  Latency: {result.latency_ms}ms")
    print(f"  Model: {result.model}")


if __name__ == "__main__":
    main()
