"""
Pydantic models for structured knowledge graph extraction.
"""

from pydantic import BaseModel, Field


class Classification(BaseModel):
    """Content classification metadata."""

    primary_topic: str = Field(description="Main category/topic as hashtag")
    related_topics: list[str] = Field(description="Related topics as hashtags")
    content_type: str = Field(description="Type: Research/Opinion/Tutorial/Case Study/News")
    depth: str = Field(description="Complexity level: Intro/Intermediate/Advanced")


class CoreInsight(BaseModel):
    """Single insight with supporting details."""

    insight: str = Field(description="Main insight statement")
    memory_aid: str = Field(description="Key phrase to remember this insight")
    supporting_facts: list[str] = Field(
        description="Supporting evidence and examples with exact details"
    )
    quantitative_data: str | None = Field(None, description="Exact numbers, formulas, or metrics")
    why_it_matters: str = Field(description="Practical implication or importance")
    connections: list[str] = Field(
        default_factory=list, description="How this connects to other insights"
    )


class Entity(BaseModel):
    """Named entity with context."""

    name: str = Field(description="Entity name")
    context: str = Field(description="Context, role, or relevance")


class MemoryAids(BaseModel):
    """Aids for retention and recall."""

    key_phrase: str = Field(description="Most memorable quote or principle with full context")
    visual_metaphor: str = Field(description="Concrete image to remember concept")
    mnemonic: str | None = Field(None, description="Acronym or memory device if applicable")


class KnowledgeGraphSummary(BaseModel):
    """Complete structured summary optimized for knowledge graphs."""

    core_answer: str = Field(description="One clear sentence directly answering the article title")

    unique_insights: list[str] = Field(
        description="Novel insights, contrarian views, or standout data not found in typical articles"
    )

    classification: Classification

    core_insights: list[CoreInsight] = Field(
        description="Hierarchical insights with memory aids and supporting details"
    )

    knowledge_graph_ascii: str = Field(
        description="ASCII diagram showing key relationships using arrows and hierarchies"
    )

    people: list[Entity] = Field(
        default_factory=list,
        description="People mentioned with full quote context (who, when, why)",
    )

    organizations: list[Entity] = Field(
        default_factory=list, description="Organizations/companies with context and relevance"
    )

    concepts: list[Entity] = Field(
        default_factory=list, description="Key concepts/terms with brief definitions"
    )

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
