import json
from pathlib import Path
from typing import Any

import structlog
from mlflow.metrics.genai import EvaluationExample, make_genai_metric
from openai import OpenAI
from pydantic import BaseModel

logger = structlog.get_logger()


class InsightEvaluation(BaseModel):
    insight_id: int
    status: str


class InsightCoverageResponse(BaseModel):
    evaluations: list[InsightEvaluation]


class InsightScoreResponse(BaseModel):
    score: float
    justification: str


class InsightsEvaluator:
    """Evaluates summaries using hand-crafted insights + LLM quality metrics"""

    def __init__(self, openai_client: OpenAI, model: str = "openai/gpt-4o"):
        self.client = openai_client
        self.model = model

    def load_insights(self, content_file: Path) -> list[dict[str, Any]]:
        """Load insights from .insights.json file matching content file"""
        insights_file = content_file.parent / f"{content_file.stem}.insights.json"

        if not insights_file.exists():
            logger.warning("insights_file_not_found", file=str(insights_file))
            return []

        with open(insights_file) as f:
            return json.load(f)

    def check_insights_coverage(self, summary: str, insights: list[dict[str, Any]], source_content: str) -> dict[str, Any]:
        """
        Use LLM to check which insights are present in the summary

        Returns dict with coverage stats and details
        """
        if not insights:
            return {
                "vital_coverage_pct": 0.0,
                "all_coverage_pct": 0.0,
                "vital_found": 0,
                "vital_total": 0,
                "details": [],
            }

        # Build prompt for LLM to check each insight
        insights_text = "\n".join([f"{i + 1}. {ins['insight']} [{ins['vitality']}]" for i, ins in enumerate(insights)])

        prompt = f"""You are evaluating a summary against a list of insights.

For each insight below, determine if it is present in the summary:
- "yes" = fully present (core fact is there)
- "partial" = partially present (mentioned but incomplete)
- "no" = not present at all

Insights to check:
{insights_text}

Summary to evaluate:
{summary}

Evaluate each insight and return the results."""

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format=InsightCoverageResponse,
        )

        # Parse structured response
        parsed_response = response.choices[0].message.parsed
        coverage_results = [{"insight_id": e.insight_id, "status": e.status} for e in parsed_response.evaluations]

        logger.debug("parsed_coverage_results", count=len(coverage_results))

        # Calculate coverage stats
        vital_insights = [ins for ins in insights if ins["vitality"] == "vital"]
        vital_found = sum(
            1
            for result in coverage_results
            if insights[result["insight_id"] - 1]["vitality"] == "vital" and result["status"] in ["yes", "partial"]
        )

        all_found = sum(1 for result in coverage_results if result["status"] in ["yes", "partial"])

        return {
            "vital_coverage_pct": (vital_found / len(vital_insights) * 100) if vital_insights else 0.0,
            "all_coverage_pct": (all_found / len(insights) * 100) if insights else 0.0,
            "vital_found": vital_found,
            "vital_total": len(vital_insights),
            "all_found": all_found,
            "all_total": len(insights),
            "details": coverage_results,
        }

    def create_insights_metric(self, insights_list: list[list[dict[str, Any]]]) -> Any:
        """Create MLflow GenAI metric for insights coverage evaluation

        Args:
            insights_list: List of insights for each content item (parallel to eval data)
        """
        from mlflow.metrics import MetricValue, make_metric

        def insights_eval_fn(predictions, metrics=None, inputs=None, targets=None, parameters=None) -> MetricValue:
            """Evaluates insights coverage with LLM justification"""
            scores = []
            justifications = []

            for idx in range(len(predictions)):
                summary = predictions.iloc[idx]
                insights = insights_list[idx] if idx < len(insights_list) else []

                if not insights:
                    scores.append(0.0)
                    justifications.append("No insights provided for evaluation")
                    continue

                insights_text = "\n".join([f"{i + 1}. {ins['insight']} [{ins['vitality']}]" for i, ins in enumerate(insights)])

                eval_prompt = f"""Evaluate summary insights preservation.

Vital insights that MUST be present:
{insights_text}

Summary to evaluate:
{summary}

For each vital insight, check if present (fully, partially, or missing).
Then provide:
1. Score from 0-100 for percentage of vital insights preserved
2. Brief justification focusing on which insights are MISSING or only partially present
   (if score is 100, explain that all insights were captured)

Return your evaluation."""

                # Use structured output
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[{"role": "user", "content": eval_prompt}],
                    temperature=0.0,
                    response_format=InsightScoreResponse,
                )

                result = response.choices[0].message.parsed
                scores.append(float(result.score))
                justifications.append(result.justification)

            return MetricValue(
                scores=scores,
                justifications=justifications,
                aggregate_results={"mean": sum(scores) / len(scores) if scores else 0.0},
            )

        insights_metric = make_metric(
            eval_fn=insights_eval_fn,
            greater_is_better=True,
            name="insights_coverage_detailed",
        )

        return insights_metric

    def create_secondary_metrics(self) -> list:
        """Create MLflow GenAI metrics for quality evaluation"""

        # Convert model format from "openai/gpt-4o" to "openai:/gpt-4o" for MLflow
        mlflow_model = self.model.replace("openai/", "openai:/", 1)

        faithfulness_metric = make_genai_metric(
            name="faithfulness",
            definition=(
                "Faithfulness measures whether the summary contains only information "
                "that is present in the source document, without adding fabricated facts or claims."
            ),
            grading_prompt=(
                "Score the summary's faithfulness on a scale of 1-5:\n"
                "1 = Contains significant fabricated information not in source\n"
                "2 = Has some inaccuracies or additions not from source\n"
                "3 = Mostly accurate with minor deviations\n"
                "4 = Accurate with only trivial formatting differences\n"
                "5 = Perfectly faithful to the source content"
            ),
            examples=[
                EvaluationExample(
                    input="The company's Q3 revenue was $10M, up 5% from Q2.",
                    output="The company saw massive Q3 revenue growth to $20M.",
                    score=1,
                    justification="Fabricates revenue amount ($20M vs actual $10M)",
                ),
                EvaluationExample(
                    input="Product launch delayed from March to April.",
                    output="Product launch postponed from March to April.",
                    score=5,
                    justification="Perfectly faithful with different wording",
                ),
            ],
            model=mlflow_model,
            parameters={"temperature": 0.0},
            aggregations=["mean", "variance"],
            greater_is_better=True,
        )

        conciseness_metric = make_genai_metric(
            name="conciseness",
            definition=(
                "Conciseness measures how efficiently the summary conveys information "
                "without unnecessary verbosity while maintaining clarity and completeness."
            ),
            grading_prompt=(
                "Score the summary's conciseness on a scale of 1-5:\n"
                "1 = Extremely verbose with significant redundancy\n"
                "2 = Some unnecessary details or repetition\n"
                "3 = Reasonably concise with minor wordiness\n"
                "4 = Very concise with good information density\n"
                "5 = Perfectly concise - every word adds value"
            ),
            examples=[
                EvaluationExample(
                    input="Study found 23% efficiency improvement.",
                    output="The comprehensive study found that efficiency improved by 23 percent.",
                    score=3,
                    justification="Reasonably concise but slightly wordy",
                ),
                EvaluationExample(
                    input="Study found 23% efficiency improvement.",
                    output="Study shows 23% efficiency gain.",
                    score=5,
                    justification="Maximally concise while preserving information",
                ),
            ],
            model=mlflow_model,
            parameters={"temperature": 0.0},
            aggregations=["mean", "variance"],
            greater_is_better=True,
        )

        readability_metric = make_genai_metric(
            name="readability",
            definition=("Readability measures how clear, well-structured, and easy to understand the summary is for a general audience."),
            grading_prompt=(
                "Score the summary's readability on a scale of 1-5:\n"
                "1 = Confusing, poor grammar, hard to follow\n"
                "2 = Some clarity issues or awkward phrasing\n"
                "3 = Generally clear and readable\n"
                "4 = Very clear with good flow and structure\n"
                "5 = Exceptionally clear, professional, and engaging"
            ),
            examples=[
                EvaluationExample(
                    input="Product features include A, B, and C.",
                    output="Product has: A thing, B stuff, and C whatever.",
                    score=2,
                    justification="Awkward phrasing, unprofessional",
                ),
                EvaluationExample(
                    input="Product features include A, B, and C.",
                    output="The product offers three key features: A, B, and C.",
                    score=5,
                    justification="Clear, professional, well-structured",
                ),
            ],
            model=mlflow_model,
            parameters={"temperature": 0.0},
            aggregations=["mean", "variance"],
            greater_is_better=True,
        )

        return [faithfulness_metric, conciseness_metric, readability_metric]

    def evaluate_summary(self, summary: str, source_content: str, content_file: Path) -> dict[str, Any]:
        """
        Evaluate a single summary

        Returns dict with all metrics
        """
        # Load insights
        insights = self.load_insights(content_file)

        # Check insights coverage (PRIMARY METRIC)
        coverage_result = self.check_insights_coverage(summary, insights, source_content)

        logger.info(
            "insights_coverage_checked",
            vital_coverage=coverage_result["vital_coverage_pct"],
            all_coverage=coverage_result["all_coverage_pct"],
        )

        return {
            "insights_coverage": coverage_result,
            "summary": summary,
            "source": source_content,
        }
