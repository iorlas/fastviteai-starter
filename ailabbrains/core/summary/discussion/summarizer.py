from openai import AsyncOpenAI
from pydantic import BaseModel

from ailabbrains.core.discussions.unified_models import UnifiedDiscussion
from ailabbrains.core.summary.base_summarizer import BaseSummarizer
from ailabbrains.core.summary.input_compiler import _format_comment_thread, _slim_comment
from ailabbrains.core.summary.schema import CommunityTake

DEFAULT_SYSTEM_PROMPT = """You're analyzing community discussion about an article. Extract insights, corrections, expert opinions.

Focus on:
- Key themes and notable insights (information nuggets!)
- Technical corrections to the article
- Missing context the article didn't cover
- Expert perspectives (identify knowledgeable commenters)
- Consensus points vs disagreements
- Overall sentiment and quality assessment

Be specific and preserve important details. Capture everything valuable - no hard limits on list fields.

OUTPUT: CommunityTake with comprehensive discussion analysis"""

DEFAULT_USER_TEMPLATE = """<article_summary>
{semantic_summary}
</article_summary>

<discussion platform="{platform}">
Story by {author} ({points} points)

{formatted_comments}
</discussion>"""


class DiscussionSummarizer(BaseSummarizer):
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        max_tokens: int = 4096,
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
        self.response_model = response_model or CommunityTake

    async def analyze_discussion(
        self,
        discussion: UnifiedDiscussion,
        semantic_summary: str,
    ) -> CommunityTake:
        # Process comments into slim format
        if discussion.comments:
            slim_children = [_slim_comment(c.model_dump()) for c in discussion.comments]
            slim_children = [c for c in slim_children if c is not None]
        else:
            slim_children = []

        # Format comments with tab indentation
        formatted_comments = _format_comment_thread(slim_children) if slim_children else "(No comments)"

        # Build user content with article context
        user_content = self.user_template.format(
            semantic_summary=semantic_summary,
            platform=discussion.platform,
            author=discussion.author or "unknown",
            points=discussion.points or 0,
            formatted_comments=formatted_comments,
        )

        # Call OpenAI with logging context
        log_context = {
            "platform": discussion.platform,
            "discussion_id": discussion.id,
            "discussion_url": discussion.discussion_url,
            "comment_count": discussion.comment_count,
            "stage": "discussion",
        }
        return await self._call_openai(user_content, self.response_model, log_context)
