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
from dagster_project.core.content_types.generic_html import GenericHTMLExtractor
from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.core.summary.input_compiler import SummaryInput
from dagster_project.core.summary.schema import KnowledgeGraphSummary, RawTextSummary, SimpleSummary
from dagster_project.core.summary.summarizer import SummaryGenerator

# Load default prompts
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/system.txt"
USER_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/user.txt"

DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text() if SYSTEM_PROMPT_PATH.exists() else ""
DEFAULT_USER_PROMPT = USER_PROMPT_PATH.read_text() if USER_PROMPT_PATH.exists() else ""

# Schema options for evaluation
SCHEMA_OPTIONS = {
    "Knowledge Graph (comprehensive)": KnowledgeGraphSummary,
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


async def extract_content(url: str) -> tuple[str, str, str]:
    """Extract content from URL (HTML or YouTube)."""
    # Detect content type
    is_youtube = "youtube.com" in url or "youtu.be" in url

    if is_youtube:
        extractor = YouTubeExtractor()
        result = await extractor.extract(url)
    else:
        extractor = GenericHTMLExtractor()
        result = await extractor.extract(url)

    if not result.success:
        raise ValueError(f"Extraction failed: {result.error}")

    return result.title, result.content, result.content_type


async def generate_summary_async(
    url: str,
    system_prompt: str,
    user_prompt_template: str,
    model: str,
    response_schema: type,
) -> dict:
    """Extract content and generate summary."""
    # Extract content
    title, content, content_type = await extract_content(url)

    # Create summary input
    summary_input = SummaryInput(
        content=content,
        title=title,
        content_type=content_type,
        url=url,
        discussions=None,  # No discussions in this simple UI
    )

    # Initialize OpenAI client and generator
    client = initialize_openai_client()
    generator = SummaryGenerator(
        openai_client=client,
        model=model,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        response_schema=response_schema,
    )

    # Generate summary
    result = generator.generate(summary_input)

    # Format the actual user prompt that was sent
    actual_user_prompt = user_prompt_template.format(
        content_type=("video transcript" if content_type == "youtube" else "article"),
        title=title,
        content=content,
    )

    return {
        "title": title,
        "content_preview": content[:500] + "..." if len(content) > 500 else content,
        "content_type": content_type,
        "summary": result.structured_summary.model_dump(),
        "tokens_used": result.tokens_used,
        "latency_ms": result.latency_ms,
        "model": result.model,
        "system_prompt_used": system_prompt,
        "user_prompt_used": actual_user_prompt[:1000] + "..." if len(actual_user_prompt) > 1000 else actual_user_prompt,
    }


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Summary Evaluation UI", layout="wide")

    st.title("Summary Generation Evaluation UI")
    st.markdown("Test different prompts and models for content summarization")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # Model selection
        default_model_index = 0
        if settings.openai_model in MODEL_OPTIONS:
            default_model_index = MODEL_OPTIONS.index(settings.openai_model)

        model_choice = st.selectbox(
            "Model",
            options=MODEL_OPTIONS,
            index=default_model_index,
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

        # Schema selection
        schema_name = st.selectbox(
            "Response Schema",
            options=list(SCHEMA_OPTIONS.keys()),
            index=0,
            help="Choose the output structure - add new schemas in schema.py",
        )
        selected_schema = SCHEMA_OPTIONS[schema_name]

        st.divider()

        # System prompt
        st.subheader("System Prompt")
        system_prompt = st.text_area(
            "System Prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            height=200,
            label_visibility="collapsed",
        )

        st.divider()

        # User prompt template
        st.subheader("User Prompt Template")
        user_prompt_template = st.text_area(
            "User Prompt Template",
            value=DEFAULT_USER_PROMPT,
            height=200,
            label_visibility="collapsed",
            help="Use {content_type}, {title}, {content} as placeholders",
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
                        user_prompt_template=user_prompt_template,
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
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    with meta_col1:
                        st.metric("Content Type", result["content_type"])
                    with meta_col2:
                        st.metric("Tokens Used", f"{result['tokens_used']:,}")
                    with meta_col3:
                        st.metric("Latency", f"{result['latency_ms']:,} ms")

                    # Log file saved indicator
                    st.success(f"✓ Execution logged to: {log_path.name}")

                    # Show prompts actually used
                    with st.expander("Prompts Used (for debugging)", expanded=False):
                        st.markdown("**System Prompt:**")
                        st.code(result["system_prompt_used"], language=None)
                        st.markdown("**User Prompt (preview):**")
                        st.code(result["user_prompt_used"], language=None)

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
