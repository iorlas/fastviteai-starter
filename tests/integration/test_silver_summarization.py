import hashlib
import json
import shutil
from unittest.mock import MagicMock

import pytest
from dagster import build_asset_context
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from dagster_project.assets.silver_summaries import silver_summaries
from dagster_project.resources.io_managers import SilverIOManager


@pytest.fixture
def mock_openai_client():
    from openai import OpenAI

    client = MagicMock(spec=OpenAI)
    mock_response = ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content=(
                        "- Main point about AI technology\n"
                        "- Key insight on implementation\n"
                        "- Future implications"
                    ),
                    role="assistant",
                ),
            )
        ],
        created=1234567890,
        model="openai/gpt-4o",
        object="chat.completion",
        usage=CompletionUsage(
            completion_tokens=25,
            prompt_tokens=150,
            total_tokens=175,
        ),
    )
    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def sample_extracted_content():
    return [
        {
            "url": "https://example.com/article1",
            "type": "html",
            "title": "Test Article 1",
            "content": "This is test content about artificial intelligence.",
            "metadata": {
                "author": "Test Author",
                "published_date": "2025-01-01",
                "word_count": 8,
            },
            "lineage": {
                "source_asset": "bronze_raw_html",
                "source_hash": hashlib.sha256(b"https://example.com/article1").hexdigest(),
                "transformation_timestamp": "2025-01-01T00:00:00Z",
            },
        },
        {
            "url": "https://example.com/video1",
            "type": "youtube",
            "title": "Test Video 1",
            "content": "This is a test video transcript about machine learning.",
            "metadata": {
                "channel": "Test Channel",
                "duration": 300,
            },
            "lineage": {
                "source_asset": "bronze_raw_html",
                "source_hash": hashlib.sha256(b"https://example.com/video1").hexdigest(),
                "transformation_timestamp": "2025-01-01T00:00:00Z",
            },
        },
    ]


@pytest.fixture
def temp_artifacts_dir(tmp_path):
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    yield artifacts_dir
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)


@pytest.mark.integration
def test_silver_summaries_success_path(
    mock_openai_client, sample_extracted_content, temp_artifacts_dir
):
    context = build_asset_context()

    result = silver_summaries(context, sample_extracted_content, mock_openai_client)

    assert len(result) == 2
    assert all(summary["status"] == "success" for summary in result)

    for i, summary in enumerate(result):
        assert summary["url"] == sample_extracted_content[i]["url"]
        assert summary["summary"] is not None
        assert summary["model"] == "openai/gpt-4o"
        assert summary["tokens_used"] == 175
        assert summary["latency_ms"] is not None
        assert isinstance(summary["latency_ms"], int)
        assert summary["lineage"]["source_asset"] == "silver_extracted_content"
        assert summary["lineage"]["source_hash"] is not None
        assert summary["lineage"]["transformation_timestamp"] is not None


@pytest.mark.integration
def test_silver_summaries_failure_path(sample_extracted_content, temp_artifacts_dir):
    from openai import OpenAI

    context = build_asset_context()

    mock_client = MagicMock(spec=OpenAI)
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    result = silver_summaries(context, sample_extracted_content, mock_client)

    assert len(result) == 2
    assert all(summary["status"] == "failed" for summary in result)

    for summary in result:
        assert summary["summary"] is None
        assert summary["error"] == "API Error"
        assert summary["error_type"] == "Exception"
        assert summary["tokens_used"] is None
        assert summary["latency_ms"] is None
        assert summary["lineage"]["source_asset"] == "silver_extracted_content"


@pytest.mark.integration
def test_silver_summaries_metadata_structure(mock_openai_client, sample_extracted_content):
    context = build_asset_context()

    result = silver_summaries(context, sample_extracted_content, mock_openai_client)

    summary = result[0]
    assert "url" in summary
    assert "status" in summary
    assert "summary" in summary
    assert "model" in summary
    assert "tokens_used" in summary
    assert "latency_ms" in summary
    assert "lineage" in summary

    lineage = summary["lineage"]
    assert lineage["source_asset"] == "silver_extracted_content"
    assert len(lineage["source_hash"]) == 64
    assert "transformation_timestamp" in lineage


@pytest.mark.integration
def test_silver_io_manager_saves_summaries_with_full_hash(
    mock_openai_client, sample_extracted_content, temp_artifacts_dir
):
    context = build_asset_context()
    io_manager = SilverIOManager(base_dir=str(temp_artifacts_dir / "silver"))

    result = silver_summaries(context, sample_extracted_content, mock_openai_client)

    mock_output_context = MagicMock()
    for summary in result:
        io_manager._handle_output_summary(mock_output_context, summary)

    summaries_dir = temp_artifacts_dir / "silver" / "summaries"
    assert summaries_dir.exists()

    json_files = list(summaries_dir.glob("*.json"))
    assert len(json_files) == 2

    for json_file in json_files:
        assert len(json_file.stem) == 64

        with json_file.open() as f:
            data = json.load(f)
        assert "created_at" in data
        assert "updated_at" in data
        assert "lineage" in data


@pytest.mark.integration
def test_silver_io_manager_creates_markdown_files(
    mock_openai_client, sample_extracted_content, temp_artifacts_dir
):
    context = build_asset_context()
    io_manager = SilverIOManager(base_dir=str(temp_artifacts_dir / "silver"))

    result = silver_summaries(context, sample_extracted_content, mock_openai_client)

    mock_output_context = MagicMock()
    for summary in result:
        io_manager._handle_output_summary(mock_output_context, summary)

    summaries_dir = temp_artifacts_dir / "silver" / "summaries"
    md_files = list(summaries_dir.glob("*.md"))
    assert len(md_files) == 2

    for md_file in md_files:
        assert len(md_file.stem) == 64
        content = md_file.read_text()
        assert "**URL:**" in content
        assert "**Status:**" in content


@pytest.mark.integration
def test_end_to_end_pipeline_bronze_to_silver_summaries(
    mock_openai_client, sample_extracted_content, temp_artifacts_dir
):
    context = build_asset_context()

    summaries = silver_summaries(context, sample_extracted_content, mock_openai_client)

    assert len(summaries) == 2

    io_manager = SilverIOManager(base_dir=str(temp_artifacts_dir / "silver"))
    mock_output_context = MagicMock()

    for summary in summaries:
        io_manager._handle_output_summary(mock_output_context, summary)

    summaries_dir = temp_artifacts_dir / "silver" / "summaries"
    assert summaries_dir.exists()

    json_files = list(summaries_dir.glob("*.json"))
    assert len(json_files) == 2

    for json_file in json_files:
        with json_file.open() as f:
            data = json.load(f)

        assert data["status"] == "success"
        assert data["summary"] is not None
        assert data["model"] == "openai/gpt-4o"
        assert data["tokens_used"] == 175
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        assert data["lineage"]["source_asset"] == "silver_extracted_content"
        assert len(data["lineage"]["source_hash"]) == 64


@pytest.mark.integration
def test_silver_summaries_handles_mixed_success_and_failure():
    from openai import OpenAI

    context = build_asset_context()

    extracted_content = [
        {
            "url": "https://example.com/success",
            "type": "html",
            "title": "Success Article",
            "content": "Content",
            "metadata": {},
            "lineage": {
                "source_asset": "bronze_raw_html",
                "source_hash": hashlib.sha256(b"https://example.com/success").hexdigest(),
                "transformation_timestamp": "2025-01-01T00:00:00Z",
            },
        },
        {
            "url": "https://example.com/fail",
            "type": "html",
            "title": "Fail Article",
            "content": "Content",
            "metadata": {},
            "lineage": {
                "source_asset": "bronze_raw_html",
                "source_hash": hashlib.sha256(b"https://example.com/fail").hexdigest(),
                "transformation_timestamp": "2025-01-01T00:00:00Z",
            },
        },
    ]

    mock_client = MagicMock(spec=OpenAI)

    success_response = ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Success summary",
                    role="assistant",
                ),
            )
        ],
        created=1234567890,
        model="openai/gpt-4o",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=10, total_tokens=15),
    )

    mock_client.chat.completions.create.side_effect = [success_response, Exception("API Error")]

    result = silver_summaries(context, extracted_content, mock_client)

    assert len(result) == 2
    assert result[0]["status"] == "success"
    assert result[1]["status"] == "failed"
    assert result[0]["summary"] is not None
    assert result[1]["error"] == "API Error"
