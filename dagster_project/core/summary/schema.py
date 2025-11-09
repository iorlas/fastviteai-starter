from typing import Literal

from pydantic import BaseModel, Field


class Classification(BaseModel):
    primary_topic: str = Field(description="Main category/topic as hashtag")
    related_topics: list[str] = Field(description="Related topics as hashtags")
    content_type: str = Field(description="Type: Research/Opinion/Tutorial/Case Study/News")
    depth: str = Field(description="Complexity level: Intro/Intermediate/Advanced")


class CoreInsight(BaseModel):
    insight: str = Field(description="Main insight statement")
    memory_aid: str = Field(description="Key phrase to remember this insight")
    supporting_facts: list[str] = Field(description="Supporting evidence and examples with exact details")
    quantitative_data: str | None = Field(None, description="Exact numbers, formulas, or metrics")
    why_it_matters: str = Field(description="Practical implication or importance")
    connections: list[str] = Field(default_factory=list, description="How this connects to other insights")


class Entity(BaseModel):
    name: str = Field(description="Entity name")
    context: str = Field(description="Context, role, or relevance")


class MemoryAids(BaseModel):
    key_phrase: str = Field(description="Most memorable quote or principle with full context")
    visual_metaphor: str = Field(description="Concrete image to remember concept")
    mnemonic: str | None = Field(None, description="Acronym or memory device if applicable")


class OpinionSummary(BaseModel):
    sentiment: str = Field(description="Overall sentiment: Positive/Negative/Mixed/Neutral")
    key_themes: list[str] = Field(description="Main themes emerging from discussions")
    top_opinions: list[str] = Field(description="High-quality comments (weighted by votes, depth, length)")
    debate_points: list[str] = Field(default_factory=list, description="Controversial or debated aspects")
    expert_perspectives: list[str] = Field(default_factory=list, description="Insights from knowledgeable commenters")


class DiscussionMetrics(BaseModel):
    total_stories: int = Field(description="Number of discussion threads found")
    total_comments: int = Field(description="Total comments across all platforms")
    platforms: list[str] = Field(description="Platforms where discussions were found")
    avg_comment_quality_score: float | None = Field(None, description="Average quality score of comments")


class KnowledgeGraphSummary(BaseModel):
    core_answer: str = Field(description="One clear sentence directly answering the article title")
    why_this_matters: str = Field(description="2-3 sentences explaining why this article is valuable and who should read it")
    expert_opinion: str = Field(
        description="1-3 sentences from an expert perspective evaluating the article's quality, unique value, or practical impact"
    )
    unique_insights: list[str] = Field(description="Novel insights, contrarian views, or standout data not typical")
    classification: Classification
    core_insights: list[CoreInsight] = Field(description="Hierarchical insights with memory aids and supporting details")
    knowledge_graph_ascii: str = Field(description="ASCII diagram showing key relationships using arrows and hierarchies")
    people: list[Entity] = Field(
        default_factory=list,
        description="People mentioned with full quote context (who, when, why)",
    )
    organizations: list[Entity] = Field(default_factory=list, description="Organizations/companies with context and relevance")
    concepts: list[Entity] = Field(default_factory=list, description="Key concepts/terms with brief definitions")
    formulas_data: list[Entity] = Field(
        default_factory=list,
        description="Exact metrics/formulas with numbers and what they measure",
    )
    examples_analogies: list[Entity] = Field(
        default_factory=list,
        description="Examples/cases with specific numbers and what they illustrate",
    )
    forward_looking: list[str] = Field(
        default_factory=list,
        description="Mentions of future posts, upcoming work, or planned content",
    )
    memory_aids: MemoryAids
    discussion_summary: OpinionSummary | None = Field(
        None,
        description="Summary of community opinions and discussions from HackerNews, Reddit, etc.",
    )
    discussion_metrics: DiscussionMetrics | None = Field(
        None,
        description="Metrics about discussion activity across platforms",
    )


class SimpleSummary(BaseModel):
    core_answer: str = Field(description="One clear sentence directly answering the article title")
    key_points: list[str] = Field(description="List of key takeaways (3-7 points)")
    topics: list[str] = Field(description="Main topics as hashtags")
    tags: list[str] = Field(description="Content classification tags")


class RawTextSummary(BaseModel):
    summary: str = Field(description="Unstructured summary text")


### NEW


class Triage(BaseModel):
    action: Literal["skip", "read", "dive"]
    confidence: int = Field(ge=0, le=100)
    why: str = Field(description="One reason, expert-style (max 80 chars)")


class Article(BaseModel):
    type: Literal["tutorial", "opinion", "research", "news", "tool", "experience"]
    novelty: Literal["new", "incremental", "rehash"]
    depth: int = Field(ge=1, le=5)
    has_technical_depth: bool

    tldr: str = Field(description="Bottom line. What's the actual insight? (max 150 chars)")

    key_points: list[str] = Field(
        description="Max 5 concrete takeaways. Numbers, approaches, tradeoffs. Use arrows (→), not prose. Each max 100 chars."
    )

    tags: list[str] = Field(description="Max 10 specific technical tags")

    semantic_summary: str = Field(description="Technical density for vector search (max 300 chars)")


class Signals(BaseModel):
    new_info: bool
    controversial: bool
    actionable: bool
    impact: Literal["none", "niche", "significant"]


class LLMTake(BaseModel):
    """Your technical assessment"""

    verdict: Literal["solid", "flawed", "shallow", "excellent"]

    what_works: list[str] = Field(description="Max 2 strengths. Be specific. Each max 80 chars.")

    what_fails: list[str] = Field(description="Max 2 problems. Be direct. Each max 80 chars.")

    bottom_line: str = Field(description="Expert verdict. Worth the time? (max 120 chars)")


class CommunityTake(BaseModel):
    """What people found"""

    consensus: Literal["validates", "split", "refutes"]
    quality: Literal["low", "med", "high"]

    experts_found: list[str] = Field(default_factory=list, description="Max 2. Format: 'username: their take (one line, max 100 chars)'")

    key_corrections: list[str] = Field(default_factory=list, description="Max 3 technical issues raised. Be specific. Each max 100 chars.")

    added_context: list[str] = Field(default_factory=list, description="Max 2. Important info article missed. Each max 100 chars.")

    community_verdict: str = Field(description="What community concluded (max 120 chars)")


class ArticleAnalysis(BaseModel):
    triage: Triage
    article: Article
    signals: Signals
    llm: LLMTake
    community: CommunityTake
