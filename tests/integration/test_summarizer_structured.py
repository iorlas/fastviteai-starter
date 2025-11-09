from unittest.mock import MagicMock

import pytest
from openai import OpenAI
from pydantic import ValidationError

from dagster_project.core.summary import (
    Classification,
    CoreInsight,
    Entity,
    KnowledgeGraphSummary,
    MemoryAids,
    SummaryGenerator,
    SummaryInput,
)
from dagster_project.core.summary.summarizer import DEFAULT_SYSTEM_PROMPT


@pytest.fixture
def mock_openai_client():
    client = MagicMock(spec=OpenAI)

    mock_structured_output = KnowledgeGraphSummary(
        core_answer="Microservices enable independent team scaling and rapid deployment.",
        why_this_matters=(
            "Essential reading for engineering leaders scaling teams beyond 20 people, "
            "as it provides proven patterns for maintaining velocity during growth."
        ),
        expert_opinion=(
            "This guide distills Amazon's hard-won lessons into actionable principles. "
            "The two-pizza rule and Conway's Law insights are particularly valuable "
            "for organizations transitioning from monoliths."
        ),
        unique_insights=[
            "Amazon's two-pizza rule limits teams to 6-8 members",
            "Conway's Law drives microservice boundaries",
        ],
        classification=Classification(
            primary_topic="#microservices",
            related_topics=["#architecture", "#scaling"],
            content_type="Tutorial",
            depth="Intermediate",
        ),
        core_insights=[
            CoreInsight(
                insight="Small autonomous teams are more productive",
                memory_aid="Two-pizza teams",
                supporting_facts=["Teams of 6-8 members can move faster"],
                quantitative_data="6-8 members per team",
                why_it_matters="Reduces coordination overhead",
                connections=["Related to Conway's Law"],
            )
        ],
        knowledge_graph_ascii="Team Size -> Productivity\n  |-> Communication\n  |-> Autonomy",
        people=[Entity(name="Werner Vogels", context="Amazon CTO, advocates microservices")],
        organizations=[Entity(name="Amazon", context="Pioneer of microservices architecture")],
        concepts=[Entity(name="Conway's Law", context="Team structure mirrors system design")],
        formulas_data=[Entity(name="Two-pizza rule", context="6-8 members per team")],
        examples_analogies=[Entity(name="Amazon example", context="Decomposed monolith into services")],
        forward_looking=[],
        memory_aids=MemoryAids(
            key_phrase="Two pizzas should feed the whole team",
            visual_metaphor="Small, autonomous pizza-sized teams",
            mnemonic=None,
        ),
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = mock_structured_output
    mock_response.model = "gpt-4o"
    mock_response.usage.total_tokens = 1500

    client.beta.chat.completions.parse.return_value = mock_response

    return client


@pytest.mark.integration
def test_summary_generator_structured_extraction(mock_openai_client):
    generator = SummaryGenerator(
        openai_client=mock_openai_client,
        model="mistralai/mistral-medium-3.1",
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        response_schema=KnowledgeGraphSummary,
        temperature=0,
        max_tokens=3000,
    )

    request = SummaryInput(
        content=(
            "Content about microservices and team organization. "
            "This article discusses how small autonomous teams can build and deploy services independently, "
            "enabling faster iteration and reduced coordination overhead."
        ),
        title="Microservices Architecture Guide",
        content_type="article",
        url="https://example.com/microservices",
    )

    result = generator.generate(request)

    assert result.model == "gpt-4o"
    assert result.tokens_used == 1500
    assert result.latency_ms >= 0

    summary = result.structured_summary
    assert isinstance(summary, KnowledgeGraphSummary)
    assert summary.core_answer == "Microservices enable independent team scaling and rapid deployment."
    assert len(summary.unique_insights) == 2
    assert summary.classification.primary_topic == "#microservices"
    assert len(summary.core_insights) == 1
    assert summary.core_insights[0].memory_aid == "Two-pizza teams"


@pytest.mark.integration
def test_summary_generator_uses_baseline_prompt(mock_openai_client):
    generator = SummaryGenerator(
        openai_client=mock_openai_client,
        model="mistralai/mistral-medium-3.1",
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        response_schema=KnowledgeGraphSummary,
        temperature=0,
        max_tokens=3000,
    )

    request = SummaryInput(
        content=(
            "Test content for validating the baseline prompt structure "
            "and ensuring all required parameters are passed correctly to the OpenAI API during summarization."
        ),
        title="Test Title",
        content_type="article",
        url="https://example.com/test",
    )

    generator.generate(request)

    mock_openai_client.beta.chat.completions.parse.assert_called_once()
    call_args = mock_openai_client.beta.chat.completions.parse.call_args

    assert call_args.kwargs["model"] == "mistralai/mistral-medium-3.1"
    assert call_args.kwargs["temperature"] == 0
    assert call_args.kwargs["max_tokens"] == 3000
    assert call_args.kwargs["response_format"] == KnowledgeGraphSummary

    messages = call_args.kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "Extract information from content" in messages[0]["content"]
    assert "CRITICAL: Capture ALL details" in messages[0]["content"]
    assert "ONE-SENTENCE answer" in messages[0]["content"]

    assert messages[1]["role"] == "user"
    assert "Test Title" in messages[1]["content"]
    assert "Test content" in messages[1]["content"]
    # Check for XML structure
    assert "<content>" in messages[1]["content"]
    assert "</content>" in messages[1]["content"]
    assert "URL: https://example.com/test" in messages[1]["content"]
    assert "Type: article" in messages[1]["content"]


@pytest.mark.integration
def test_summary_generator_retries_on_validation_error():
    client = MagicMock(spec=OpenAI)

    mock_structured_output = KnowledgeGraphSummary(
        core_answer="Success on retry",
        why_this_matters="Demonstrates retry mechanism works correctly.",
        expert_opinion="Well-implemented retry logic ensures robustness.",
        unique_insights=["Retry worked"],
        classification=Classification(
            primary_topic="#test",
            related_topics=[],
            content_type="Test",
            depth="Basic",
        ),
        core_insights=[],
        knowledge_graph_ascii="A -> B",
        people=[],
        organizations=[],
        concepts=[],
        formulas_data=[],
        examples_analogies=[],
        forward_looking=[],
        memory_aids=MemoryAids(
            key_phrase="Retry success",
            visual_metaphor="Second attempt wins",
        ),
    )

    mock_success_response = MagicMock()
    mock_success_response.choices = [MagicMock()]
    mock_success_response.choices[0].message.parsed = mock_structured_output
    mock_success_response.model = "test-model"
    mock_success_response.usage.total_tokens = 500

    call_count = {"count": 0}

    def mock_parse(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise ValidationError.from_exception_data(
                "validation_error",
                [{"type": "json_invalid", "loc": (), "input": "{}", "ctx": {"error": "test"}}],
            )
        return mock_success_response

    client.beta.chat.completions.parse.side_effect = mock_parse

    generator = SummaryGenerator(
        openai_client=client,
        model="test-model",
        max_tokens=4096,
    )

    request = SummaryInput(
        content=(
            "Test content for validating the retry mechanism when validation errors occur. "
            "This ensures the summarizer can recover from transient failures."
        ),
        title="Test",
        content_type="article",
        url="https://example.com",
    )

    result = generator.generate(request)

    assert result.structured_summary.core_answer == "Success on retry"
    assert call_count["count"] == 2


@pytest.mark.integration
def test_summary_generator_fails_after_max_retries():
    client = MagicMock(spec=OpenAI)

    def raise_validation_error(*args, **kwargs):
        raise ValidationError.from_exception_data(
            "validation_error",
            [{"type": "json_invalid", "loc": (), "input": "{}", "ctx": {"error": "test"}}],
        )

    client.beta.chat.completions.parse.side_effect = raise_validation_error

    generator = SummaryGenerator(
        openai_client=client,
        model="test-model",
        max_tokens=4096,
    )

    request = SummaryInput(
        content=(
            "Test content for validating that the summarizer fails gracefully "
            "after exhausting all retry attempts when validation errors persist."
        ),
        title="Test",
        content_type="article",
        url="https://example.com",
    )

    with pytest.raises(ValidationError):
        generator.generate(request)

    assert client.beta.chat.completions.parse.call_count == 2
