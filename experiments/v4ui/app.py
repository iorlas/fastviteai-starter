"""
Streamlit UI for evaluating summary generation with different prompts and models.

Run with: uv run streamlit run experiments/v4ui/app.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Runs directory for logging executions
RUNS_DIR = Path(__file__).parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)

# ruff: noqa: E402
import streamlit as st
from openai import OpenAI

from dagster_project.config import settings
from dagster_project.core.summary.input_compiler import compile_summary_input
from dagster_project.core.summary.schema import ArticleAnalysis, KnowledgeGraphSummary, RawTextSummary, SimpleSummary
from dagster_project.core.summary.summarizer import DEFAULT_SYSTEM_PROMPT, SummaryGenerator

# Schema options for evaluation
SCHEMA_OPTIONS = {
    "Knowledge Graph (comprehensive)": KnowledgeGraphSummary,
    "Article Analysis (triage + signals)": ArticleAnalysis,
    "Simple (lightweight)": SimpleSummary,
    "Raw Text (minimal)": RawTextSummary,
}

# Model options (OpenRouter-compatible)
MODEL_OPTIONS = [
    "mistralai/mistral-medium-3.1",
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.5-flash",
    "deepseek/deepseek-chat-v3",
    "Custom (enter manually)",
]


def initialize_openai_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    """Initialize OpenAI client with settings."""
    return OpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=base_url or settings.openai_base_url,
        max_retries=3,
        timeout=30.0,
    )


def save_execution_log(
    url: str,
    schema_name: str,
    result: dict | None = None,
    error: str | None = None,
) -> Path:
    """Save execution details to timestamped JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{timestamp}.json"
    filepath = RUNS_DIR / filename

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "schema": schema_name,
        "success": error is None,
    }

    if result:
        log_data["result"] = result

    if error:
        log_data["error"] = error

    filepath.write_text(json.dumps(log_data, indent=2))
    return filepath


async def generate_summary_async(
    url: str,
    system_prompt: str,
    model: str,
    response_schema: type,
) -> dict:
    """Extract content and generate summary using bronze layer data."""
    # Use input compiler to load content and discussions from bronze layer
    bronze_path = PROJECT_ROOT / settings.artifacts_path / "bronze"
    summary_input = compile_summary_input(url, str(bronze_path))

    # Initialize OpenAI client and generator
    client = initialize_openai_client()
    generator = SummaryGenerator(
        openai_client=client,
        model=model,
        system_prompt=system_prompt,
        response_schema=response_schema,
    )

    # Generate summary
    result = generator.generate(summary_input)

    return {
        "title": summary_input.title,
        "content_preview": summary_input.content[:500] + "..." if len(summary_input.content) > 500 else summary_input.content,
        "content_type": summary_input.content_type,
        "summary": result.structured_summary.model_dump(),
        "tokens_used": result.tokens_used,
        "latency_ms": result.latency_ms,
        "model": result.model,
        "system_prompt_used": system_prompt,
        "discussions_count": summary_input.discussions_count or 0,
        "discussions_text": summary_input.discussions,
        "discussions_metadata": [d.model_dump() for d in summary_input.discussions_metadata] if summary_input.discussions_metadata else None,
    }


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Summary Evaluation UI", layout="wide")

    st.title("Summary Generation Evaluation UI")
    st.markdown("Test different prompts and models for content summarization")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Model selection (default to Mistral)
        model_choice = st.selectbox(
            "Model",
            options=MODEL_OPTIONS,
            index=0,  # Default to mistralai/mistral-medium-3.1
            help="Select a model or choose 'Custom' to enter your own",
        )

        if model_choice == "Custom (enter manually)":
            model = st.text_input(
                "Custom Model ID",
                value=settings.openai_model if settings.openai_model not in MODEL_OPTIONS else "",
                placeholder="e.g., meta-llama/llama-3.3-70b",
                help="Enter any OpenRouter-compatible model ID",
            )
        else:
            model = model_choice

        # Schema selection (default to Article Analysis)
        schema_name = st.selectbox(
            "Response Schema",
            options=list(SCHEMA_OPTIONS.keys()),
            index=1,  # Default to Article Analysis
            help="Choose the output structure - add new schemas in schema.py",
        )
        selected_schema = SCHEMA_OPTIONS[schema_name]

        st.divider()

        # System prompt
        st.subheader("System Prompt")
        system_prompt = st.text_area(
            "System Prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            height=300,
            label_visibility="collapsed",
            help="Instructions for extraction. User content is automatically formatted as XML: <content> and <discussions> blocks",
        )

    # Main content area
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Input")
        url = st.text_input("URL", placeholder="https://example.com/article")

        generate_button = st.button("Generate Summary", type="primary", use_container_width=True)

    with col2:
        st.header("Output")
        output_placeholder = st.empty()

    # Generate summary on button click
    if generate_button:
        if not url:
            st.error("Please enter a URL")
            return

        with st.spinner("Extracting content and generating summary..."):
            try:
                # Run async function in sync context
                result = asyncio.run(
                    generate_summary_async(
                        url=url,
                        system_prompt=system_prompt,
                        model=model,
                        response_schema=selected_schema,
                    )
                )

                # Save execution log
                log_path = save_execution_log(url=url, schema_name=schema_name, result=result)

                # Display results
                with output_placeholder.container():
                    # Metadata
                    st.subheader("Metadata")
                    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
                    with meta_col1:
                        st.metric("Content Type", result["content_type"])
                    with meta_col2:
                        st.metric("Tokens Used", f"{result['tokens_used']:,}")
                    with meta_col3:
                        st.metric("Latency", f"{result['latency_ms']:,} ms")
                    with meta_col4:
                        st.metric("Discussions", result["discussions_count"])

                    # Log file saved indicator
                    st.success(f"✓ Execution logged to: {log_path.name}")

                    # Discussions display
                    if result["discussions_count"] > 0 and result["discussions_metadata"]:
                        st.subheader("Discussions")
                        st.markdown(f"**Found {result['discussions_count']} discussion threads**")

                        # Display discussion links
                        for disc in result["discussions_metadata"]:
                            platform_emoji = "🔶" if disc["platform"] == "hackernews" else "🦞"
                            st.markdown(
                                f"{platform_emoji} **[{disc['title']}]({disc['url']})** "
                                f"• {disc['points']} pts • {disc['comment_count']} comments"
                            )

                        # Full discussion text
                        if result["discussions_text"]:
                            with st.expander("View formatted discussion text (sent to LLM)", expanded=False):
                                st.text(result["discussions_text"])

                    # Show system prompt used
                    with st.expander("System Prompt Used (for debugging)", expanded=False):
                        st.code(result["system_prompt_used"], language=None)
                        st.caption("Note: User content is automatically formatted as XML with <content> and <discussions> blocks")

                    # Extracted content
                    st.subheader("Extracted Content")
                    st.markdown(f"**Title:** {result['title']}")
                    with st.expander("Content Preview"):
                        st.text(result["content_preview"])

                    # Summary (schema-agnostic JSON display)
                    st.subheader("Generated Summary")
                    st.json(result["summary"])

            except Exception as e:
                import traceback

                error_details = traceback.format_exc()

                # Save error log
                save_execution_log(url=url, schema_name=schema_name, error=str(e))

                st.error(f"Error: {str(e)}")
                with st.expander("Error Details"):
                    st.code(error_details)


if __name__ == "__main__":
    main()
