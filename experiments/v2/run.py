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
from schemas import KnowledgeGraphSummary

load_dotenv()
log = structlog.get_logger()


def load_experiments(config_path: Path = Path("experiments.yaml")) -> dict:
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return {exp_name: exp_data for exp_name, exp_data in data["experiments"].items()}


def load_test_data(test_path: Path) -> dict:
    with open(test_path) as f:
        return json.load(f)


def call_llm(model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> tuple[dict, dict]:
    start_time = time.time()

    if model.startswith("openai/"):
        model_id = model.replace("openai/", "")
        client = OpenAI()

        response = client.beta.chat.completions.parse(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=KnowledgeGraphSummary,
        )

        summary_obj = response.choices[0].message.parsed
        output = summary_obj.model_dump()

        metadata = {
            "latency": round(time.time() - start_time, 2),
            "tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }
    else:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=KnowledgeGraphSummary,
        )

        summary_obj = response.choices[0].message.parsed
        output = summary_obj.model_dump() if summary_obj else {}

        metadata = {
            "latency": round(time.time() - start_time, 2),
            "tokens": response.usage.total_tokens if response.usage else 0,
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }

    return output, metadata


def run_experiment(experiment_name: str, model: str, test_file: Path) -> None:
    experiments = load_experiments()

    if experiment_name not in experiments:
        log.error("experiment_not_found", experiment=experiment_name, available=list(experiments.keys()))
        sys.exit(1)

    exp = experiments[experiment_name]
    test_data = load_test_data(test_file)

    log.info("starting_run", experiment=experiment_name, model=model, test_file=str(test_file))

    user_prompt = exp["user_template"].format(
        content_type=test_data.get("metadata", {}).get("type", "article"),
        title=test_data["title"],
        content=test_data["content"],
    )

    output, metadata = call_llm(
        model=model,
        system_prompt=exp["system_prompt"],
        user_prompt=user_prompt,
        temperature=exp.get("temperature", 0),
        max_tokens=exp.get("max_tokens", 3000),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "timestamp": timestamp,
        "experiment": experiment_name,
        "model": model,
        "test_file": str(test_file),
        "content": {
            "title": test_data["title"],
            "type": test_data.get("metadata", {}).get("type", "article"),
        },
        "expected_insights": test_data.get("expected_insights", {}),
        "output": output,
        "metadata": metadata,
        "evaluation": None,
    }

    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)

    filename = f"{timestamp}_{experiment_name}_{model.replace('/', '-')}.json"
    output_path = runs_dir / filename

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    log.info(
        "run_complete",
        output_file=str(output_path),
        latency=metadata["latency"],
        tokens=metadata["tokens"],
    )


if __name__ == "__main__":
    if len(sys.argv) < 4:
        log.error("usage", command="python run.py <experiment_name> <model> <test_file>")
        sys.exit(1)

    run_experiment(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
