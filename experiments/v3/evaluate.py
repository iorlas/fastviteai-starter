import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from url_normalize import url_normalize

from dagster_project.core.summarizer import SummaryGenerator, SummaryRequest
from dagster_project.resources.storage import Storage
from dagster_project.utils.tables import SilverTable
from dagster_project.utils.url_utils import compute_url_hash as compute_url_hash_util

load_dotenv()
logger = structlog.get_logger()


class EvaluationCase(BaseModel):
    url: str
    expectations: str
    anti_patterns: str | None = None


class JudgementResult(BaseModel):
    score: int
    reasoning: str
    strengths: list[str]
    weaknesses: list[str]
    meets_expectations: bool
    violates_anti_patterns: bool


class EvaluationResult(BaseModel):
    url: str
    url_hash: str
    title: str
    expectations: str
    anti_patterns: str | None
    summary: dict
    judgement: JudgementResult
    model: str
    tokens_used: int
    latency_ms: int
    timestamp: str


def load_prompts(prompt_dir: str) -> tuple[str, str]:
    system_path = Path(prompt_dir) / "system.txt"
    user_path = Path(prompt_dir) / "user.txt"

    if not system_path.exists() or not user_path.exists():
        raise FileNotFoundError(f"Prompt files not found in {prompt_dir}")

    return system_path.read_text().strip(), user_path.read_text().strip()


def compute_url_hash(url: str) -> str:
    return compute_url_hash_util(url)


def load_extracted_content(url: str, url_hash: str, silver_storage: Storage) -> dict:
    if not silver_storage.exists(SilverTable.EXTRACTED_CONTENT, url_hash):
        raise FileNotFoundError(
            f"Extracted content not found for: {url}\n"
            f"Run pipeline first:\n"
            f"  1. Add URL to manual_links.txt\n"
            f"  2. Run: dagster dev\n"
            f"  3. Materialize manual_urls_pipeline in UI"
        )

    logger.info("extracted_content.loaded", url=url)
    return silver_storage.load(SilverTable.EXTRACTED_CONTENT, url_hash)


def generate_summary(
    extracted_content: dict,
    url: str,
    generator: SummaryGenerator,
) -> dict:
    title = extracted_content.get("title", url)
    content = extracted_content.get("content", "")
    content_type = extracted_content.get("content_type", "unknown")

    logger.info("summary.generating", url=url, title=title)

    result = generator.generate(
        SummaryRequest(
            content=content,
            title=title,
            content_type=content_type,
            url=url,
            discussions=None,
            discussion_metadata=None,
        )
    )

    return {
        "structured_summary": result.structured_summary.model_dump(),
        "model": result.model,
        "tokens_used": result.tokens_used,
        "latency_ms": result.latency_ms,
    }


def judge_summary(
    summary: dict,
    expectations: str,
    anti_patterns: str | None,
    judge_client: OpenAI,
    judge_model: str,
) -> JudgementResult:
    summary_text = json.dumps(summary["structured_summary"], indent=2)

    judge_prompt = f"""You are evaluating the quality of an AI-generated summary against human expectations.

SUMMARY TO EVALUATE:
{summary_text}

EXPECTATIONS (what the summary should achieve):
{expectations}

ANTI-PATTERNS (what the summary should avoid):
{anti_patterns or "None specified"}

Evaluate the summary on a scale of 1-10 and provide detailed feedback:
- Score: 1-10 (1=completely misses the mark, 10=exceeds expectations)
- Reasoning: Why you gave this score
- Strengths: What the summary does well
- Weaknesses: What the summary misses or does poorly
- Meets expectations: Boolean - does it achieve the stated expectations?
- Violates anti-patterns: Boolean - does it commit any of the anti-patterns?

Be strict but fair. A score of 7+ means it's genuinely good. Don't inflate scores."""

    logger.info("judge.evaluating", model=judge_model)

    response = judge_client.beta.chat.completions.parse(
        model=judge_model,
        messages=[
            {"role": "system", "content": "You are an expert evaluator of AI-generated summaries. Be precise, critical, and honest."},
            {"role": "user", "content": judge_prompt},
        ],
        response_format=JudgementResult,
        temperature=0,
    )

    return response.choices[0].message.parsed


def evaluate_url(
    case: EvaluationCase,
    generator: SummaryGenerator,
    judge_client: OpenAI,
    judge_model: str,
    silver_storage: Storage,
) -> EvaluationResult:
    url = url_normalize(case.url.strip())
    url_hash = compute_url_hash(url)

    logger.info("evaluation.started", url=url)

    extracted_content = load_extracted_content(url, url_hash, silver_storage)

    if not extracted_content.get("extraction_success"):
        raise ValueError(f"Content extraction failed: {extracted_content.get('error_message')}")

    summary = generate_summary(extracted_content, url, generator)

    judgement = judge_summary(
        summary,
        case.expectations,
        case.anti_patterns,
        judge_client,
        judge_model,
    )

    result = EvaluationResult(
        url=url,
        url_hash=url_hash,
        title=extracted_content.get("title", url),
        expectations=case.expectations,
        anti_patterns=case.anti_patterns,
        summary=summary["structured_summary"],
        judgement=judgement,
        model=summary["model"],
        tokens_used=summary["tokens_used"],
        latency_ms=summary["latency_ms"],
        timestamp=datetime.now(UTC).isoformat(),
    )

    logger.info(
        "evaluation.complete",
        url=url,
        score=judgement.score,
        meets_expectations=judgement.meets_expectations,
    )

    return result


def generate_markdown_report(results: list[EvaluationResult], prompt_name: str, model: str) -> str:
    total_score = sum(r.judgement.score for r in results)
    avg_score = total_score / len(results) if results else 0
    meets_expectations_count = sum(1 for r in results if r.judgement.meets_expectations)
    violates_anti_patterns_count = sum(1 for r in results if r.judgement.violates_anti_patterns)

    report = f"""# Evaluation Report

**Generated:** {datetime.now(UTC).isoformat()}
**Prompt:** {prompt_name}
**Model:** {model}
**URLs Evaluated:** {len(results)}

## Summary Statistics

- **Average Score:** {avg_score:.1f}/10
- **Meets Expectations:** {meets_expectations_count}/{len(results)}
- **Violates Anti-patterns:** {violates_anti_patterns_count}/{len(results)}

## Individual Results

"""

    for idx, result in enumerate(results, 1):
        status_emoji = "✅" if result.judgement.meets_expectations else "❌"
        anti_pattern_emoji = "⚠️" if result.judgement.violates_anti_patterns else ""

        report += f"""
### {idx}. {result.title} {status_emoji} {anti_pattern_emoji}

**URL:** {result.url}
**Score:** {result.judgement.score}/10
**Model:** {result.model} ({result.tokens_used} tokens, {result.latency_ms}ms)

#### Expectations
{result.expectations}

{f"#### Anti-patterns\\n{result.anti_patterns}\\n" if result.anti_patterns else ""}

#### Judgement Reasoning
{result.judgement.reasoning}

#### Strengths
{chr(10).join(f"- {s}" for s in result.judgement.strengths)}

#### Weaknesses
{chr(10).join(f"- {w}" for w in result.judgement.weaknesses)}

---
"""

    return report


def main():
    parser = argparse.ArgumentParser(description="Evaluate summary quality with LLM judge")
    parser.add_argument(
        "--eval-set",
        required=True,
        help="Path to evaluation set JSON file",
    )
    parser.add_argument(
        "--prompts",
        default="baseline",
        help="Prompt directory name (default: baseline)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use for summarization (default: from core/summarizer.py)",
    )
    parser.add_argument(
        "--judge-model",
        default="openai/gpt-4o-mini",
        help="Model to use for judging (default: openai/gpt-4o-mini)",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Output directory for results (default: results/)",
    )

    args = parser.parse_args()

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(20),
    )

    eval_set_path = Path(__file__).parent / args.eval_set
    if not eval_set_path.exists():
        print(f"Error: Eval set not found: {eval_set_path}")
        sys.exit(1)

    with eval_set_path.open() as f:
        eval_cases_data = json.load(f)

    eval_cases = [EvaluationCase(**case) for case in eval_cases_data]

    prompts_dir = Path(__file__).parent / "prompts" / args.prompts
    system_prompt, user_prompt_template = load_prompts(prompts_dir)

    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).parent.parent.parent))
    artifacts_dir = project_root / "artifacts"

    silver_storage = Storage(base_dir=str(artifacts_dir / "silver"))

    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        max_retries=3,
        timeout=60.0,
    )

    judge_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        max_retries=3,
        timeout=60.0,
    )

    model = args.model or os.getenv("OPENAI_MODEL", "mistralai/mistral-medium-3.1")

    generator = SummaryGenerator(
        openai_client=openai_client,
        model=model,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
    )

    print(f"Evaluating {len(eval_cases)} URLs with prompts={args.prompts}, model={model}, judge={args.judge_model}")
    print("Note: Summaries will be regenerated with current prompts/model")
    print()

    results = []
    for idx, case in enumerate(eval_cases, 1):
        print(f"[{idx}/{len(eval_cases)}] Evaluating: {case.url}")
        try:
            result = evaluate_url(
                case,
                generator,
                judge_client,
                args.judge_model,
                silver_storage,
            )
            results.append(result)
            print(f"  Score: {result.judgement.score}/10 {'✅' if result.judgement.meets_expectations else '❌'}")
        except Exception as e:
            print(f"  Error: {e}")
            logger.error("evaluation.failed", url=case.url, error=str(e))
        print()

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / args.output_dir
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / f"{timestamp}_{args.prompts}.json"
    md_path = output_dir / f"{timestamp}_{args.prompts}.md"

    json_path.write_text(json.dumps([r.model_dump() for r in results], indent=2, default=str))

    markdown_report = generate_markdown_report(results, args.prompts, model)
    md_path.write_text(markdown_report)

    print("Results saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print()

    avg_score = sum(r.judgement.score for r in results) / len(results) if results else 0
    print(f"Average Score: {avg_score:.1f}/10")


if __name__ == "__main__":
    main()
