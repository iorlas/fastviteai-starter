import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import structlog
import yaml
from dotenv import load_dotenv
from openai import OpenAI

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ["PROJECT_ROOT"] = str(project_root)

from dagster_project.assets.content_extraction import ExtractedContent  # noqa: E402
from experiments.evaluator import InsightsEvaluator  # noqa: E402
from experiments.schema import KnowledgeGraphSummary  # noqa: E402

load_dotenv()

logger = structlog.get_logger()

EXPERIMENTS_V1_DIR = project_root / "experiments" / "v1"
REPORTS_DIR = EXPERIMENTS_V1_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
HISTORY_FILE = EXPERIMENTS_V1_DIR / "experiment_history.csv"
PROMPTS_FILE = EXPERIMENTS_V1_DIR / "prompts.yaml"


def load_experiments() -> dict:
    """Load experiments from prompts.yaml"""
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(f"prompts.yaml not found at {PROMPTS_FILE}")

    with open(PROMPTS_FILE) as f:
        data = yaml.safe_load(f)

    experiments = {}
    for exp in data.get("experiments", []):
        experiments[exp["name"]] = {
            "system_message": exp["system_message"],
            "user_template": exp["user_template"],
            "model": exp.get("model", "openai/gpt-4o"),
            "temperature": exp.get("temperature", 0.7),
            "max_tokens": exp.get("max_tokens", 1000),
        }

    return experiments


def get_prompt_hash(system_message: str, user_template: str) -> str:
    """Generate hash of prompt for version detection"""
    combined = f"{system_message}\n---\n{user_template}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]


def get_experiment_version(experiment_name: str, prompt_hash: str) -> str:
    """Get version number for experiment based on history"""
    if not HISTORY_FILE.exists():
        return "v1"

    versions = set()
    with open(HISTORY_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["experiment"] == experiment_name:
                versions.add(row["version"])
                if row["prompt_hash"] == prompt_hash:
                    return row["version"]

    # New hash - increment version
    max_version = 0
    for v in versions:
        if v.startswith("v"):
            try:
                num = int(v[1:])
                max_version = max(max_version, num)
            except ValueError:
                pass

    return f"v{max_version + 1}"


def save_to_history(
    experiment_name: str,
    version: str,
    model: str,
    coverage_pct: float,
    latency_sec: float,
    tokens_total: int,
    tokens_prompt: int,
    tokens_completion: int,
    prompt_hash: str,
    report_path: str,
):
    """Append run to history CSV"""
    timestamp = datetime.now().isoformat()

    file_exists = HISTORY_FILE.exists()

    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "experiment",
                    "version",
                    "model",
                    "coverage_pct",
                    "latency_sec",
                    "tokens_total",
                    "tokens_prompt",
                    "tokens_completion",
                    "prompt_hash",
                    "report_path",
                ]
            )

        writer.writerow(
            [
                timestamp,
                experiment_name,
                version,
                model,
                coverage_pct,
                latency_sec,
                tokens_total,
                tokens_prompt,
                tokens_completion,
                prompt_hash,
                report_path,
            ]
        )


def show_leaderboard():
    """Display experiment leaderboard"""
    if not HISTORY_FILE.exists():
        print("📊 No experiment history yet. Run some experiments first!")
        return

    with open(HISTORY_FILE) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("📊 No experiment history yet. Run some experiments first!")
        return

    # Group by experiment+version
    experiments = {}
    for row in rows:
        key = f"{row['experiment']} ({row['version']})"
        if key not in experiments or row["timestamp"] > experiments[key]["timestamp"]:
            experiments[key] = row

    # Sort by coverage
    sorted_experiments = sorted(experiments.items(), key=lambda x: float(x[1]["coverage_pct"]), reverse=True)

    print("\n" + "=" * 120)
    print("📊 EXPERIMENT LEADERBOARD")
    print("=" * 120)
    print(f"{'Rank':<6} {'Experiment':<35} {'Model':<30} {'Coverage':<12} {'Latency':<12} {'Tokens':<10}")
    print("-" * 120)

    for i, (exp_key, data) in enumerate(sorted_experiments, 1):
        coverage = float(data["coverage_pct"])
        if coverage == 100:
            emoji = "🏆"
        elif coverage >= 90:
            emoji = "🥇"
        elif coverage >= 75:
            emoji = "🥈"
        else:
            emoji = "🥉"

        print(
            f"{emoji} #{i:<3} {exp_key:<35} {data['model']:<30} "
            f"{coverage:>6.1f}% {float(data['latency_sec']):>9.2f}s {int(data['tokens_total']):>8}"
        )

    print("=" * 120 + "\n")


def load_example(example_path: Path) -> tuple[ExtractedContent, list[dict]]:
    """Load content and insights from example file"""
    with open(example_path) as f:
        data = json.load(f)

    content = ExtractedContent(
        url=data["url"],
        url_hash=data["url_hash"],
        content_type=data["content_type"],
        title=data["title"],
        text=data["text"],
        metadata=data.get("metadata", {}),
        extraction_success=data.get("extraction_success", True),
        error_message=data.get("error_message"),
    )

    insights_path = example_path.parent / f"{example_path.stem}.insights.json"
    if insights_path.exists():
        with open(insights_path) as f:
            insights = json.load(f)
    else:
        insights = []

    return content, insights


def create_prompt_messages(system_prompt: str, user_template: str, content: ExtractedContent) -> list[dict[str, str]]:
    """Create messages with template variable substitution"""
    content_type = "video transcript" if content.content_type == "youtube" else "article"

    system_message = {"role": "system", "content": system_prompt}

    user_content = user_template.format(content_type=content_type, title=content.title, content=content.text)
    user_message = {"role": "user", "content": user_content}

    return [system_message, user_message]


def get_model_key(model: str) -> str:
    """Convert model name to clean filename-safe key"""
    return model.replace("/", "-").replace(":", "-")


def save_report(
    experiment_name: str,
    version: str,
    model: str,
    summary: str,
    coverage: dict,
    insights: list[dict],
    latency: float,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    system_prompt: str,
    user_template: str,
    content_title: str,
    input_length: int,
    summary_length: int,
) -> tuple[Path, Path]:
    """Save both JSON and text reports for the run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Organize by experiment name
    exp_dir = REPORTS_DIR / experiment_name
    exp_dir.mkdir(exist_ok=True)

    model_key = get_model_key(model)
    filename = f"{model_key}_{version}_{timestamp}"

    json_path = exp_dir / f"{filename}.json"
    txt_path = exp_dir / f"{filename}.txt"

    missing_insights = []
    partial_insights = []
    for detail in coverage["details"]:
        insight = insights[detail["insight_id"] - 1]
        if detail["status"] == "no":
            missing_insights.append(insight["insight"])
        elif detail["status"] == "partial":
            partial_insights.append(insight["insight"])

    compression_ratio = input_length / summary_length if summary_length > 0 else 0

    json_report = {
        "timestamp": timestamp,
        "experiment": experiment_name,
        "version": version,
        "model": model,
        "summary": summary,
        "coverage_pct": coverage["vital_coverage_pct"],
        "vital_found": coverage["vital_found"],
        "vital_total": coverage["vital_total"],
        "all_found": coverage["all_found"],
        "all_total": coverage["all_total"],
        "latency_sec": latency,
        "tokens_total": total_tokens,
        "tokens_prompt": prompt_tokens,
        "tokens_completion": completion_tokens,
        "input_length": input_length,
        "summary_length": summary_length,
        "compression_ratio": compression_ratio,
        "missing_insights": missing_insights,
        "partial_insights": partial_insights,
        "coverage_details": [
            {"status": detail["status"], "insight": insights[detail["insight_id"] - 1]["insight"]} for detail in coverage["details"]
        ],
        "system_prompt": system_prompt,
        "user_template": user_template,
        "content_title": content_title,
    }

    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)

    score = coverage["vital_coverage_pct"]
    if score == 100:
        status_line = f"✅ Insights Coverage: {score:.1f}% (PERFECT!)"
    elif score >= 90:
        status_line = f"🟢 Insights Coverage: {score:.1f}% (Excellent)"
    elif score >= 75:
        status_line = f"🟡 Insights Coverage: {score:.1f}% (Good)"
    elif score >= 50:
        status_line = f"🟠 Insights Coverage: {score:.1f}% (Fair)"
    else:
        status_line = f"🔴 Insights Coverage: {score:.1f}% (Poor)"

    txt_report = f"""{"=" * 80}
TEST REPORT
{"=" * 80}

Experiment: {experiment_name} ({version})
Timestamp: {timestamp}
Model: {model}
Content: {content_title}

{"=" * 80}
GENERATED SUMMARY
{"=" * 80}

{summary}

{"=" * 80}
RESULTS
{"=" * 80}

{status_line}

📈 Stats:
   Vital insights found: {coverage["vital_found"]}/{coverage["vital_total"]}
   All insights found: {coverage["all_found"]}/{coverage["all_total"]}

⚡ Performance:
   Latency: {latency:.2f}s
   Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})

📏 Text Metrics:
   Input length: {input_length:,} chars
   Summary length: {summary_length:,} chars
   Compression ratio: {compression_ratio:.2f}x

{"=" * 80}
COVERAGE DETAILS
{"=" * 80}

"""

    for detail in coverage["details"]:
        insight = insights[detail["insight_id"] - 1]
        status = detail["status"]
        status_emoji = {"yes": "✅", "partial": "⚠️", "no": "❌"}.get(status, "❓")
        txt_report += f"{status_emoji} [{status:7}] {insight['insight']}\n"

    if missing_insights:
        txt_report += f"\n{'=' * 80}\nMISSING INSIGHTS\n{'=' * 80}\n\n"
        for insight in missing_insights:
            txt_report += f"- {insight}\n"

    if partial_insights:
        txt_report += f"\n{'=' * 80}\nPARTIAL INSIGHTS\n{'=' * 80}\n\n"
        for insight in partial_insights:
            txt_report += f"- {insight}\n"

    txt_report += f"\n{'=' * 80}\nPROMPT CONFIGURATION\n{'=' * 80}\n\n"
    txt_report += f"System Prompt:\n{system_prompt}\n\n"
    txt_report += f"User Template:\n{user_template}\n\n"
    txt_report += f"{'=' * 80}\n"

    with open(txt_path, "w") as f:
        f.write(txt_report)

    return json_path, txt_path


def run_experiment(
    experiment_name: str,
    model_override: str = None,
    track_mlflow: bool = False,
) -> None:
    """Run an experiment by name from prompts.yaml"""

    # Load experiments
    experiments = load_experiments()

    if experiment_name not in experiments:
        print(f"❌ Experiment '{experiment_name}' not found in prompts.yaml")
        print("\nAvailable experiments:")
        for name in experiments.keys():
            print(f"  - {name}")
        sys.exit(1)

    exp_config = experiments[experiment_name]

    # Model override
    model = model_override or exp_config["model"]
    system_prompt = exp_config["system_message"]
    user_template = exp_config["user_template"]
    temperature = exp_config["temperature"]
    max_tokens = exp_config["max_tokens"]

    # Get version
    prompt_hash = get_prompt_hash(system_prompt, user_template)
    version = get_experiment_version(experiment_name, prompt_hash)

    # Load test content
    example_path = EXPERIMENTS_V1_DIR / "eval_dataset" / "example_002.json"
    if not example_path.exists():
        print(f"❌ Example file not found: {example_path}")
        sys.exit(1)

    content, insights = load_example(example_path)

    if not insights:
        print(f"⚠️  No insights file found at {example_path.stem}.insights.json")
        print("   Cannot evaluate coverage without insights.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"🔬 Running: {experiment_name} ({version})")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Content: {content.title}")
    print("=" * 80 + "\n")

    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    messages = create_prompt_messages(system_prompt, user_template, content)

    print("🔄 Generating summary...")
    start_time = time.time()

    response = openai_client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=KnowledgeGraphSummary,
    )
    summary_obj = response.choices[0].message.parsed
    summary = summary_obj.model_dump_json(indent=2)

    latency = time.time() - start_time

    print("✅ Summary generated\n")
    print("📝 GENERATED SUMMARY:")
    print("-" * 80)
    print(summary)
    print("-" * 80 + "\n")

    print("🔍 Evaluating insights coverage...")
    evaluator = InsightsEvaluator(openai_client, model="openai/gpt-4o")
    eval_result = evaluator.evaluate_summary(summary=summary, source_content=content.text, content_file=example_path)

    coverage = eval_result["insights_coverage"]

    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80 + "\n")

    score = coverage["vital_coverage_pct"]
    if score == 100:
        print(f"✅ Insights Coverage: {score:.1f}% (PERFECT!)")
    elif score >= 90:
        print(f"🟢 Insights Coverage: {score:.1f}% (Excellent)")
    elif score >= 75:
        print(f"🟡 Insights Coverage: {score:.1f}% (Good)")
    elif score >= 50:
        print(f"🟠 Insights Coverage: {score:.1f}% (Fair)")
    else:
        print(f"🔴 Insights Coverage: {score:.1f}% (Poor)")

    print("\n📈 Stats:")
    print(f"   Vital insights found: {coverage['vital_found']}/{coverage['vital_total']}")
    print(f"   All insights found: {coverage['all_found']}/{coverage['all_total']}")
    print("\n⚡ Performance:")
    print(f"   Latency: {latency:.2f}s")
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    print(f"   Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")

    if coverage["details"]:
        print("\n📋 Coverage Details:")
        for detail in coverage["details"]:
            insight = insights[detail["insight_id"] - 1]
            status = detail["status"]
            status_emoji = {"yes": "✅", "partial": "⚠️", "no": "❌"}.get(status, "❓")
            print(f"   {status_emoji} [{status:7}] {insight['insight']}")

    print("\n" + "=" * 80 + "\n")

    input_length = len(content.text)
    summary_length = len(summary)

    json_path, txt_path = save_report(
        experiment_name=experiment_name,
        version=version,
        model=model,
        summary=summary,
        coverage=coverage,
        insights=insights,
        latency=latency,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        system_prompt=system_prompt,
        user_template=user_template,
        content_title=content.title,
        input_length=input_length,
        summary_length=summary_length,
    )

    # Save to history
    save_to_history(
        experiment_name=experiment_name,
        version=version,
        model=model,
        coverage_pct=coverage["vital_coverage_pct"],
        latency_sec=latency,
        tokens_total=total_tokens,
        tokens_prompt=prompt_tokens,
        tokens_completion=completion_tokens,
        prompt_hash=prompt_hash,
        report_path=str(json_path),
    )

    print("💾 Reports saved:")
    print(f"   JSON: {json_path}")
    print(f"   Text: {txt_path}")
    print(f"   History: {HISTORY_FILE}")
    print()

    # MLflow tracking (optional)
    if track_mlflow:
        try:
            import mlflow

            mlflow.set_experiment(f"prompt_testing_{experiment_name}")

            with mlflow.start_run(run_name=f"{experiment_name}_{version}"):
                mlflow.log_params(
                    {
                        "experiment": experiment_name,
                        "version": version,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "prompt_hash": prompt_hash,
                    }
                )

                mlflow.log_metrics(
                    {
                        "coverage_pct": coverage["vital_coverage_pct"],
                        "latency_sec": latency,
                        "tokens_total": total_tokens,
                        "tokens_prompt": prompt_tokens,
                        "tokens_completion": completion_tokens,
                        "compression_ratio": input_length / summary_length if summary_length > 0 else 0,
                    }
                )

                mlflow.log_text(system_prompt, "system_prompt.txt")
                mlflow.log_text(user_template, "user_template.txt")
                mlflow.log_text(summary, "summary.txt")
                mlflow.log_artifact(str(json_path))
                mlflow.log_artifact(str(txt_path))

            print("📊 MLflow tracking completed")
        except ImportError:
            print("⚠️  MLflow not installed. Skipping MLflow tracking.")
        except Exception as e:
            print(f"⚠️  MLflow tracking failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test prompts from prompts.yaml with automatic versioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run experiment
  python test_prompt.py --experiment knowledge_graph_json

  # Run with different model
  python test_prompt.py --experiment knowledge_graph_json --model openai/gpt-4o-mini

  # Run with MLflow tracking
  python test_prompt.py --experiment knowledge_graph_json --mlflow

  # View leaderboard
  python test_prompt.py --leaderboard
        """,
    )

    parser.add_argument(
        "--experiment",
        type=str,
        help="Experiment name from prompts.yaml",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Override model from prompts.yaml",
    )

    parser.add_argument(
        "--mlflow",
        action="store_true",
        help="Track this run in MLflow",
    )

    parser.add_argument(
        "--leaderboard",
        action="store_true",
        help="Show experiment leaderboard",
    )

    args = parser.parse_args()

    if args.leaderboard:
        show_leaderboard()
        return

    if not args.experiment:
        print("❌ Either --experiment or --leaderboard is required")
        parser.print_help()
        sys.exit(1)

    run_experiment(
        experiment_name=args.experiment,
        model_override=args.model,
        track_mlflow=args.mlflow,
    )


if __name__ == "__main__":
    main()
