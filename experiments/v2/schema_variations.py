"""
Schema variations for Phase 2 experiments

Testing if enhanced schema field descriptions can:
1. Achieve higher coverage (target: 100%)
2. Enable simpler prompts (target: <500 chars)
"""

from pydantic import BaseModel, Field

# ========================================
# BASELINE SCHEMA (Current)
# ========================================


class BaselineClassification(BaseModel):
    primary_topic: str = Field(description="Main category/topic as hashtag")
    related_topics: list[str] = Field(description="Related topics as hashtags")
    content_type: str = Field(description="Type: Research/Opinion/Tutorial/Case Study/News")
    depth: str = Field(description="Complexity level: Intro/Intermediate/Advanced")


class BaselineCoreInsight(BaseModel):
    insight: str = Field(description="Main insight statement")
    memory_aid: str = Field(description="Key phrase to remember this insight")
    supporting_facts: list[str] = Field(description="Supporting evidence and examples with exact details")
    quantitative_data: str | None = Field(None, description="Exact numbers, formulas, or metrics")
    why_it_matters: str = Field(description="Practical implication or importance")
    connections: list[str] = Field(default_factory=list, description="How this connects to other insights")


class BaselineEntity(BaseModel):
    name: str = Field(description="Entity name")
    context: str = Field(description="Context, role, or relevance")


class BaselineMemoryAids(BaseModel):
    key_phrase: str = Field(description="Most memorable quote or principle with full context")
    visual_metaphor: str = Field(description="Concrete image to remember concept")
    mnemonic: str | None = Field(None, description="Acronym or memory device if applicable")


class BaselineKnowledgeGraphSummary(BaseModel):
    core_answer: str = Field(description="One clear sentence directly answering the article title")
    unique_insights: list[str] = Field(description="Novel insights, contrarian views, or standout data not typical")
    classification: BaselineClassification
    core_insights: list[BaselineCoreInsight] = Field(description="Hierarchical insights with memory aids and supporting details")
    knowledge_graph_ascii: str = Field(description="ASCII diagram showing key relationships using arrows and hierarchies")
    people: list[BaselineEntity] = Field(
        default_factory=list,
        description="People mentioned with full quote context (who, when, why)",
    )
    organizations: list[BaselineEntity] = Field(default_factory=list, description="Organizations/companies with context and relevance")
    concepts: list[BaselineEntity] = Field(default_factory=list, description="Key concepts/terms with brief definitions")
    formulas_data: list[BaselineEntity] = Field(
        default_factory=list,
        description="Exact metrics/formulas with numbers and what they measure",
    )
    examples_analogies: list[BaselineEntity] = Field(
        default_factory=list,
        description="Examples/cases with specific numbers and what they illustrate",
    )
    forward_looking: list[str] = Field(
        default_factory=list,
        description="Mentions of future posts, upcoming work, or planned content",
    )
    memory_aids: BaselineMemoryAids


# ========================================
# S1: RICH DESCRIPTIONS
# Move V1 prompt instructions into schema
# ========================================


class S1Classification(BaseModel):
    primary_topic: str = Field(description="Main category/topic as hashtag")
    related_topics: list[str] = Field(description="Related topics as hashtags")
    content_type: str = Field(description="Type: Research/Opinion/Tutorial/Case Study/News")
    depth: str = Field(description="Complexity level: Intro/Intermediate/Advanced")


class S1CoreInsight(BaseModel):
    insight: str = Field(
        description="Main insight statement. Capture exact numbers, formulas, team sizes "
        "(e.g., '4 people' not 'small teams'). Include full quote context (who, when, why)."
    )
    memory_aid: str = Field(description="Key phrase to remember this insight")
    supporting_facts: list[str] = Field(
        description="Supporting evidence and examples with specific details. Include exact numbers, names, and contextual details."
    )
    quantitative_data: str | None = Field(None, description="Exact numbers, formulas, or metrics with full specification")
    why_it_matters: str = Field(description="Practical implication or importance")
    connections: list[str] = Field(
        default_factory=list,
        description="How this connects to other insights, concepts, or examples",
    )


class S1Entity(BaseModel):
    name: str = Field(description="Entity name, principle, or concept")
    context: str = Field(
        description="Context, role, or relevance. Include specific details, numbers, "
        "and examples. For quotes, include who said it, when, and why."
    )


class S1MemoryAids(BaseModel):
    key_phrase: str = Field(description="Most memorable quote or principle with full context")
    visual_metaphor: str = Field(description="Concrete image to remember concept")
    mnemonic: str | None = Field(None, description="Acronym or memory device if applicable")


class S1KnowledgeGraphSummary(BaseModel):
    core_answer: str = Field(description="One clear sentence directly answering the article title, synthesizing the main thesis")
    unique_insights: list[str] = Field(
        description="Novel insights, contrarian views, or standout data not found in typical articles. "
        "Include what makes each insight unique or unexpected."
    )
    classification: S1Classification
    core_insights: list[S1CoreInsight] = Field(
        description="ALL key insights with memory aids, supporting facts with exact numbers, "
        "quantitative data, and connections. Extract every insight including supporting ones, "
        "not just main arguments. Include historical comparisons, lessons learned, "
        "cautionary tales, and warnings about pitfalls."
    )
    knowledge_graph_ascii: str = Field(description="ASCII diagram showing key relationships using arrows and hierarchies")
    people: list[S1Entity] = Field(
        default_factory=list,
        description="People mentioned with full quote context (who said it, when, why, exact quote)",
    )
    organizations: list[S1Entity] = Field(
        default_factory=list,
        description="Organizations/companies with context, relevance, and specific details",
    )
    concepts: list[S1Entity] = Field(default_factory=list, description="Key concepts/terms with brief definitions and examples")
    formulas_data: list[S1Entity] = Field(
        default_factory=list,
        description="Exact metrics/formulas with numbers, what they measure, and full specification",
    )
    examples_analogies: list[S1Entity] = Field(
        default_factory=list,
        description="Examples/cases with specific numbers, exact details, and what they illustrate. "
        "Include supporting examples and anecdotes with concrete details.",
    )
    forward_looking: list[str] = Field(
        default_factory=list,
        description="Mentions of future posts, upcoming work, planned content, or tooling plans",
    )
    memory_aids: S1MemoryAids


# ========================================
# S2: SYNTHESIS FIELDS
# Add explicit cross-content synthesis
# ========================================


class S2Entity(BaseModel):
    name: str = Field(description="Entity name, principle, or rule")
    context: str = Field(description="Context, role, or relevance")
    numeric_specification: str | None = Field(
        None,
        description="If this is a rule/principle/concept, include exact numbers or specifications "
        "mentioned anywhere in content, even in different paragraphs. "
        "Example: 'two-pizza rule' → '6-8 members'",
    )


class S2CoreInsight(BaseModel):
    insight: str = Field(description="Main insight statement")
    memory_aid: str = Field(description="Key phrase to remember this insight")
    supporting_facts: list[str] = Field(description="Supporting evidence and examples with exact details")
    quantitative_data: str | None = Field(None, description="Exact numbers, formulas, or metrics")
    why_it_matters: str = Field(description="Practical implication or importance")
    connections: list[str] = Field(default_factory=list, description="How this connects to other insights")
    synthesis_note: str | None = Field(
        None,
        description="If this insight combines information from different parts of content, "
        "note what was connected (e.g., 'Links principle X from intro to data Y from conclusion')",
    )


class S2KnowledgeGraphSummary(BaseModel):
    core_answer: str = Field(description="One clear sentence directly answering the article title")
    unique_insights: list[str] = Field(description="Novel insights, contrarian views, or standout data not typical")
    classification: BaselineClassification
    core_insights: list[S2CoreInsight] = Field(description="Hierarchical insights with memory aids and supporting details")
    knowledge_graph_ascii: str = Field(description="ASCII diagram showing key relationships using arrows and hierarchies")
    people: list[BaselineEntity] = Field(
        default_factory=list,
        description="People mentioned with full quote context (who, when, why)",
    )
    organizations: list[BaselineEntity] = Field(default_factory=list, description="Organizations/companies with context and relevance")
    concepts: list[S2Entity] = Field(default_factory=list, description="Key concepts/terms with definitions and specifications")
    formulas_data: list[S2Entity] = Field(
        default_factory=list,
        description="Exact metrics/formulas with numbers and what they measure",
    )
    examples_analogies: list[S2Entity] = Field(
        default_factory=list,
        description="Examples/cases with specific numbers and what they illustrate",
    )
    forward_looking: list[str] = Field(
        default_factory=list,
        description="Mentions of future posts, upcoming work, or planned content",
    )
    memory_aids: BaselineMemoryAids


# ========================================
# S3: EXAMPLE-DRIVEN
# Concrete examples in descriptions
# ========================================


class S3KnowledgeGraphSummary(BaseModel):
    core_answer: str = Field(
        description="One clear sentence directly answering the article title. "
        "Example: 'Microservices success depends on small cross-functional teams, not technology.'"
    )
    unique_insights: list[str] = Field(
        description="Novel insights, contrarian views, or standout data not typical. "
        "Example: 'Bezos said communication is terrible (not more is better)'"
    )
    classification: BaselineClassification
    core_insights: list[BaselineCoreInsight] = Field(
        description="Key insights with memory aids and supporting facts. "
        "Example insight: 'Team size matters' with supporting fact 'Navy Seals use 4-person teams' "
        "and quantitative data '(n * n-1) / 2 communication links formula'"
    )
    knowledge_graph_ascii: str = Field(
        description="ASCII diagram showing relationships. Example: 'Small Teams → Effective Communication → Innovation'"
    )
    people: list[BaselineEntity] = Field(
        default_factory=list,
        description="People with quotes and context. "
        "Example: name='Jeff Bezos', context='Amazon CEO stated \"Communication is terrible\" "
        "when managers requested more team communication, emphasizing effective over frequent communication'",
    )
    organizations: list[BaselineEntity] = Field(
        default_factory=list,
        description="Organizations with context. Example: name='Amazon', context='Uses two-pizza team rule limiting teams to 6-8 members'",
    )
    concepts: list[BaselineEntity] = Field(
        default_factory=list,
        description="Key concepts with definitions. Example: name='Two-pizza rule', context='Team size limited to what two pizzas can "
        "feed (6-8 people at Amazon)'",
    )
    formulas_data: list[BaselineEntity] = Field(
        default_factory=list,
        description="Exact formulas with numbers. Example: name='Communication links formula', context='(n * n-1) / 2 "
        "- measures team communication complexity'",
    )
    examples_analogies: list[BaselineEntity] = Field(
        default_factory=list,
        description="Examples with specific numbers. Example: name='Navy Seals'"
        ", context='Work in combat teams of 4 people to maintain effectiveness'",
    )
    forward_looking: list[str] = Field(
        default_factory=list,
        description="Future plans mentioned. Example: 'Author plans to discuss OpenShift and fabric8io tooling in next post'",
    )
    memory_aids: BaselineMemoryAids
