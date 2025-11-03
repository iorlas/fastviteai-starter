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
