"""
Streamlit UI for evaluating summary generation with different prompts and models.

Run with: uv run streamlit run experiments/v4ui/app.py
"""

import asyncio
from pathlib import Path

import streamlit as st
from openai import OpenAI

from dagster_project.config import settings
from dagster_project.core.content_types.generic_html import GenericHTMLExtractor
from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.core.summary.input_compiler import SummaryInput
from dagster_project.core.summary.summarizer import SummaryGenerator

# Load default prompts
PROJECT_ROOT = Path(__file__).parent.parent.parent
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/system.txt"
USER_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/user.txt"

DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text() if SYSTEM_PROMPT_PATH.exists() else ""
DEFAULT_USER_PROMPT = USER_PROMPT_PATH.read_text() if USER_PROMPT_PATH.exists() else ""


def initialize_openai_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    """Initialize OpenAI client with settings."""
    return OpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=base_url or settings.openai_base_url,
        max_retries=3,
        timeout=30.0,
    )


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
    )

    # Generate summary
    result = generator.generate(summary_input)

    return {
        "title": title,
        "content_preview": content[:500] + "..." if len(content) > 500 else content,
        "content_type": content_type,
        "summary": result.structured_summary.model_dump(),
        "tokens_used": result.tokens_used,
        "latency_ms": result.latency_ms,
        "model": result.model,
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
        model = st.text_input(
            "Model",
            value=settings.openai_model,
            help="OpenRouter model ID (e.g., openai/gpt-4o, anthropic/claude-3.5-sonnet)",
        )

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
                    )
                )

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

                    # Extracted content
                    st.subheader("Extracted Content")
                    st.markdown(f"**Title:** {result['title']}")
                    with st.expander("Content Preview"):
                        st.text(result["content_preview"])

                    # Summary
                    st.subheader("Generated Summary")

                    summary = result["summary"]

                    # Core answer
                    st.markdown("**Core Answer:**")
                    st.info(summary.get("core_answer", "N/A"))

                    # Why this matters
                    st.markdown("**Why This Matters:**")
                    st.info(summary.get("why_this_matters", "N/A"))

                    # Unique insights
                    if summary.get("unique_insights"):
                        st.markdown("**Unique Insights:**")
                        for insight in summary["unique_insights"]:
                            st.markdown(f"- {insight}")

                    # Knowledge graph
                    if summary.get("knowledge_graph_ascii"):
                        with st.expander("Knowledge Graph (ASCII)"):
                            st.code(summary["knowledge_graph_ascii"], language=None)

                    # Full JSON
                    with st.expander("Full Summary JSON"):
                        st.json(summary)

            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback

                with st.expander("Error Details"):
                    st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
