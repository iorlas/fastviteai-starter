import json

from openai import AsyncOpenAI
from pydantic import BaseModel

from dagster_project.core.summary.base_summarizer import BaseSummarizer
from dagster_project.core.summary.schema import CommunityConsensus, CommunityTake

DEFAULT_SYSTEM_PROMPT = """You're synthesizing multiple discussion summaries to determine overall community consensus.

Evaluate across all discussions:
- Does community validate, split on, or refute the article?
- What's the overall quality of discussions?
- What's the final community verdict (synthesize all discussion verdicts into one cohesive statement)?

Be concise and decisive. Focus on overall patterns, not individual discussions."""

DEFAULT_USER_TEMPLATE = """<article_summary>
{semantic_summary}
</article_summary>

<discussion_summaries>
{discussion_summaries_json}
</discussion_summaries>"""


class CommunitySynthesizer(BaseSummarizer):
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        max_tokens: int = 2048,
        model: str | None = None,
        system_prompt: str | None = None,
        user_template: str | None = None,
        response_model: type[BaseModel] | None = None,
    ):
        super().__init__(
            openai_client,
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            user_template=user_template or DEFAULT_USER_TEMPLATE,
            model=model,
            max_tokens=max_tokens,
        )
        self.response_model = response_model or CommunityConsensus

    async def synthesize(
        self,
        discussion_summaries: list[CommunityTake],
        semantic_summary: str,
    ) -> CommunityTake:
        # Step 1: Programmatic merge of all list fields
        merged = self._merge_lists(discussion_summaries)

        # Step 2: LLM re-evaluation of consensus/quality/verdict only
        consensus = await self._evaluate_consensus(discussion_summaries, semantic_summary)

        # Step 3: Combine programmatic merge + LLM consensus
        merged.consensus = consensus.consensus
        merged.quality = consensus.quality
        merged.community_verdict = consensus.community_verdict

        return merged

    def _merge_lists(self, summaries: list[CommunityTake]) -> CommunityTake:
        return CommunityTake(
            # Placeholder values - will be overwritten by LLM in _evaluate_consensus
            consensus="split",
            quality="med",
            community_verdict="",
            # Merge all list fields from all summaries
            key_themes=[theme for summary in summaries for theme in summary.key_themes],
            notable_insights=[insight for summary in summaries for insight in summary.notable_insights],
            consensus_points=[point for summary in summaries for point in summary.consensus_points],
            disagreements=[disagreement for summary in summaries for disagreement in summary.disagreements],
            experts_found=[expert for summary in summaries for expert in summary.experts_found],
            key_corrections=[correction for summary in summaries for correction in summary.key_corrections],
            added_context=[context for summary in summaries for context in summary.added_context],
        )

    async def _evaluate_consensus(
        self,
        summaries: list[CommunityTake],
        semantic_summary: str,
    ) -> CommunityConsensus:
        # Build user content with all discussion summaries
        user_content = self.user_template.format(
            semantic_summary=semantic_summary,
            discussion_summaries_json=json.dumps([s.model_dump() for s in summaries], indent=2),
        )

        # Call OpenAI with logging context
        log_context = {
            "discussion_count": len(summaries),
            "stage": "synthesis",
        }
        return await self._call_openai(user_content, self.response_model, log_context)
