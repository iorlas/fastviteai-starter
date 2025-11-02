import json
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
import structlog
import yaml
from dotenv import load_dotenv
from evaluator import InsightsEvaluator
from openai import OpenAI
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=UserWarning, module="mlflow")

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dagster_project.assets.content_extraction import ExtractedContent  # noqa: E402

load_dotenv()

logger = structlog.get_logger()


class ExperimentConfig(BaseModel):
    name: str
    system_message: str
    user_template: str
    model: str = "openai/gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 1000


class SummaryMetrics(BaseModel):
    summary_length_chars: int
    summary_length_words: int
    original_length_chars: int
    original_length_words: int
    compression_ratio: float
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    latency_ms: float
    cost_estimate_usd: float = 0.0


def load_prompts_from_yaml(yaml_path: Path) -> list[dict[str, Any]]:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return data.get("experiments", [])


def load_content_files(
    artifacts_dir: Path, limit: int | None = None
) -> tuple[list[ExtractedContent], list[Path]]:
    """Load content files and return both content objects and file paths"""
    content_list = []
    file_paths = []

    # For eval_dataset, files are directly in the directory
    # For artifacts, files are in html/ and videos/ subdirectories
    search_dirs = []
    if (artifacts_dir / "html").exists() or (artifacts_dir / "videos").exists():
        # artifacts structure
        search_dirs = [artifacts_dir / "html", artifacts_dir / "videos"]
    else:
        # eval_dataset structure (flat)
        search_dirs = [artifacts_dir]

    for content_dir in search_dirs:
        if not content_dir.exists():
            continue

        for json_file in content_dir.glob("*.json"):
            # Skip insights files
            if json_file.stem.endswith(".insights"):
                continue

            if limit and len(content_list) >= limit:
                break

            try:
                with open(json_file) as f:
                    data = json.load(f)
                # ExtractedContent is a NamedTuple, create from dict
                content_list.append(
                    ExtractedContent(
                        url=data["url"],
                        url_hash=data["url_hash"],
                        content_type=data["content_type"],
                        title=data["title"],
                        text=data["text"],
                        metadata=data.get("metadata", {}),
                        extraction_success=data.get("extraction_success", True),
                        error_message=data.get("error_message"),
                    )
                )
                file_paths.append(json_file)
            except Exception as e:
                logger.error("failed_to_load_content", file=str(json_file), error=str(e))
                continue

    return content_list, file_paths


def create_prompt_messages(
    config: ExperimentConfig, content: ExtractedContent
) -> list[dict[str, str]]:
    content_type = "video transcript" if content.content_type == "youtube" else "article"

    system_message = {"role": "system", "content": config.system_message}

    user_content = config.user_template.format(
        content_type=content_type, title=content.title, content=content.text
    )
    user_message = {"role": "user", "content": user_content}

    return [system_message, user_message]


def calculate_metrics(
    summary: str, original_content: str, response: Any, latency_ms: float
) -> SummaryMetrics:
    summary_words = len(summary.split())
    original_words = len(original_content.split())

    compression_ratio = len(summary) / len(original_content) if len(original_content) > 0 else 0.0

    return SummaryMetrics(
        summary_length_chars=len(summary),
        summary_length_words=summary_words,
        original_length_chars=len(original_content),
        original_length_words=original_words,
        compression_ratio=compression_ratio,
        tokens_prompt=response.usage.prompt_tokens,
        tokens_completion=response.usage.completion_tokens,
        tokens_total=response.usage.total_tokens,
        latency_ms=latency_ms,
    )


def run_experiment(
    config: ExperimentConfig,
    content_list: list[ExtractedContent],
    content_files: list[Path],
    openai_client: OpenAI,
    evaluator: InsightsEvaluator,
    experiment_name: str = "summarization_experiments",
    sample_size: int | None = None,
    batch_timestamp: str | None = None,
) -> None:
    mlflow.set_experiment(experiment_name)

    if sample_size:
        content_list = content_list[:sample_size]
        content_files = content_files[:sample_size]

    with mlflow.start_run(run_name=config.name):
        # Add timestamp tags for grouping runs
        if batch_timestamp:
            mlflow.set_tag("run_batch", batch_timestamp)
            mlflow.set_tag("run_date", datetime.fromisoformat(batch_timestamp).strftime("%Y-%m-%d"))

        mlflow.log_params(
            {
                "experiment_name": config.name,
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "content_count": len(content_list),
            }
        )

        mlflow.log_text(config.system_message, "system_prompt.txt")
        mlflow.log_text(config.user_template, "user_prompt_template.txt")

        # Log dataset
        dataset_records = [
            {
                "url": content.url,
                "url_hash": content.url_hash,
                "title": content.title,
                "content_type": content.content_type,
                "text_length": len(content.text),
            }
            for content in content_list
        ]
        df = pd.DataFrame(dataset_records)
        dataset = mlflow.data.from_pandas(df, source="artifacts/html and artifacts/videos")
        mlflow.log_input(dataset, context="content_for_summarization")

        # Also log as CSV artifact for easy viewing
        df.to_csv("dataset_contents.csv", index=False)
        mlflow.log_artifact("dataset_contents.csv")
        os.remove("dataset_contents.csv")

        all_metrics = []
        all_summaries = []
        successful_summaries = 0
        failed_summaries = 0

        for idx, content in enumerate(content_list):
            logger.info(
                "processing_content",
                index=idx + 1,
                total=len(content_list),
                title=content.title,
            )

            try:
                messages = create_prompt_messages(config, content)

                start_time = time.time()
                response = openai_client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000

                summary = response.choices[0].message.content

                metrics = calculate_metrics(summary, content.text, response, latency_ms)
                all_metrics.append(metrics)

                mlflow.log_metrics(
                    {
                        f"item_{idx}_tokens": metrics.tokens_total,
                        f"item_{idx}_latency_ms": metrics.latency_ms,
                        f"item_{idx}_compression_ratio": metrics.compression_ratio,
                    }
                )

                # Log individual summary
                safe_title = "".join(c for c in content.title[:50] if c.isalnum() or c in " -_")
                mlflow.log_text(summary, f"summary_{idx:02d}_{safe_title}.txt")

                # Store for consolidated report
                all_summaries.append(
                    {
                        "idx": idx,
                        "title": content.title,
                        "url": content.url,
                        "summary": summary,
                        "tokens": metrics.tokens_total,
                    }
                )

                successful_summaries += 1

            except Exception as e:
                logger.error(
                    "failed_to_generate_summary", url=content.url, title=content.title, error=str(e)
                )
                failed_summaries += 1
                continue

        logger.info(
            "experiment_completed",
            experiment=config.name,
            successful=successful_summaries,
            failed=failed_summaries,
        )

        if all_metrics:
            avg_tokens = sum(m.tokens_total for m in all_metrics) / len(all_metrics)
            avg_latency = sum(m.latency_ms for m in all_metrics) / len(all_metrics)
            avg_compression = sum(m.compression_ratio for m in all_metrics) / len(all_metrics)
            total_tokens = sum(m.tokens_total for m in all_metrics)

            mlflow.log_metrics(
                {
                    "avg_tokens_per_summary": avg_tokens,
                    "avg_latency_ms": avg_latency,
                    "avg_compression_ratio": avg_compression,
                    "total_tokens": total_tokens,
                    "successful_summaries": successful_summaries,
                    "failed_summaries": failed_summaries,
                }
            )

            logger.info(
                "experiment_metrics",
                avg_tokens=int(avg_tokens),
                avg_latency_ms=int(avg_latency),
            )

        # Create consolidated report with all summaries
        if all_summaries:
            report_lines = [
                f"# Summaries Report: {config.name}",
                f"\nExperiment: {config.name}",
                f"Model: {config.model}",
                f"Temperature: {config.temperature}",
                f"Max Tokens: {config.max_tokens}",
                f"Total Summaries: {len(all_summaries)}",
                "\n---\n",
            ]

            for item in all_summaries:
                report_lines.extend(
                    [
                        f"\n## [{item['idx']}] {item['title']}",
                        f"\n**URL:** {item['url']}",
                        f"\n**Tokens:** {item['tokens']}",
                        f"\n\n### Summary:\n\n{item['summary']}",
                        "\n\n---\n",
                    ]
                )

            report_text = "\n".join(report_lines)
            mlflow.log_text(report_text, "all_summaries_report.md")

        # EVALUATION: Run insights-based evaluation
        if all_summaries:
            logger.info("starting_evaluation", num_summaries=len(all_summaries))

            # Evaluate each summary for insights coverage
            all_insights_coverage = []
            evaluation_details = []

            for idx, item in enumerate(all_summaries):
                content_file = content_files[idx]
                content = content_list[idx]

                eval_result = evaluator.evaluate_summary(
                    summary=item["summary"], source_content=content.text, content_file=content_file
                )

                coverage = eval_result["insights_coverage"]
                all_insights_coverage.append(coverage)

                # Log per-item insights coverage
                mlflow.log_metrics(
                    {
                        f"item_{idx}_insights_coverage": coverage["vital_coverage_pct"],
                    }
                )

                evaluation_details.append(
                    {
                        "idx": idx,
                        "title": item["title"],
                        "vital_coverage": coverage["vital_coverage_pct"],
                        "vital_found": coverage["vital_found"],
                        "vital_total": coverage["vital_total"],
                    }
                )

                logger.info(
                    "summary_evaluated",
                    idx=idx,
                    title=item["title"],
                    vital_coverage=coverage["vital_coverage_pct"],
                )

            # Calculate average insights coverage (PRIMARY METRIC)
            avg_vital_coverage = (
                sum(c["vital_coverage_pct"] for c in all_insights_coverage)
                / len(all_insights_coverage)
                if all_insights_coverage
                else 0.0
            )

            avg_all_coverage = (
                sum(c["all_coverage_pct"] for c in all_insights_coverage)
                / len(all_insights_coverage)
                if all_insights_coverage
                else 0.0
            )

            # Log primary evaluation metrics
            mlflow.log_metrics(
                {
                    "avg_insights_coverage": avg_vital_coverage,
                    "avg_all_insights_coverage": avg_all_coverage,
                }
            )

            logger.info(
                "evaluation_completed",
                avg_insights_coverage=avg_vital_coverage,
                avg_all_coverage=avg_all_coverage,
            )

            # Run all quality metrics using MLflow evaluate (insights + secondary)
            logger.info("running_quality_metrics")

            # Load insights for all content items
            insights_list = [
                evaluator.load_insights(content_files[i]) for i in range(len(all_summaries))
            ]

            # Prepare data for MLflow evaluate
            eval_data = pd.DataFrame(
                [
                    {
                        "inputs": content_list[i].text,
                        "predictions": item["summary"],
                    }
                    for i, item in enumerate(all_summaries)
                ]
            )

            # Create all metrics: insights coverage + secondary quality metrics
            insights_metric = evaluator.create_insights_metric(insights_list)
            secondary_metrics = evaluator.create_secondary_metrics()
            all_metrics = [insights_metric] + secondary_metrics

            # Run MLflow evaluation
            eval_results = mlflow.evaluate(
                data=eval_data,
                predictions="predictions",
                extra_metrics=all_metrics,
                evaluator_config={
                    "col_mapping": {"inputs": "inputs", "predictions": "predictions"}
                },
            )

            logger.info("quality_metrics_completed", metrics=eval_results.metrics)


def main():
    project_root = Path(__file__).parent.parent
    eval_dataset_dir = project_root / "experiments" / "eval_dataset"
    prompts_yaml = project_root / "experiments" / "prompts.yaml"

    logger.info("loading_eval_dataset")
    content_list, content_files = load_content_files(eval_dataset_dir, limit=None)
    logger.info("eval_dataset_loaded", count=len(content_list))

    if not content_list:
        logger.error("no_content_files_found")
        return

    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    # Create evaluator
    evaluator = InsightsEvaluator(openai_client)

    if not prompts_yaml.exists():
        logger.error("prompts_yaml_not_found", path=str(prompts_yaml))
        sys.exit(1)

    logger.info("loading_experiments", path=str(prompts_yaml))
    yaml_experiments = load_prompts_from_yaml(prompts_yaml)
    experiments = [ExperimentConfig(**exp) for exp in yaml_experiments]

    if not experiments:
        logger.error("no_experiments_defined")
        sys.exit(1)

    logger.info(
        "starting_experiments", experiment_count=len(experiments), content_count=len(content_list)
    )

    # Create batch timestamp to group all runs from this execution
    batch_timestamp = datetime.now().isoformat()

    for config in experiments:
        logger.info("running_experiment", experiment=config.name)
        run_experiment(
            config=config,
            content_list=content_list,
            content_files=content_files,
            openai_client=openai_client,
            evaluator=evaluator,
            sample_size=None,
            batch_timestamp=batch_timestamp,
        )

    logger.info("all_experiments_completed")


if __name__ == "__main__":
    main()
