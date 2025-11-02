import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import streamlit as st
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

from dagster_project.core.summary_schema import KnowledgeGraphSummary

st.set_page_config(
    page_title="Knowledge Feed",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=60)
def load_summaries() -> list[dict[str, Any]]:
    summaries_dir = Path("artifacts/silver/silver_summary")

    if not summaries_dir.exists():
        return []

    summaries = []
    for json_file in summaries_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                summaries.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    summaries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return summaries


def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "")
    except Exception:
        return "unknown"


def format_timestamp(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except Exception:
        return iso_string


def render_summary_card(summary_data: dict[str, Any]) -> None:
    title = summary_data.get("title", "Untitled")
    url = summary_data.get("url", "")
    domain = extract_domain(url)
    status = summary_data.get("status", "unknown")
    created_at = summary_data.get("created_at", "")

    if status == "failed":
        with st.expander(f"❌ {title} - {domain}", expanded=False):
            st.error("**Failed to summarize**")
            st.write(f"**URL:** {url}")
            if "error" in summary_data:
                st.write(f"**Error:** {summary_data['error']}")
            st.caption(f"Model: {summary_data.get('model', 'N/A')} • {format_timestamp(created_at)}")
        return

    structured_summary = summary_data.get("structured_summary")
    legacy_summary = summary_data.get("summary")

    if structured_summary:
        render_structured_summary(summary_data, title, url, domain, created_at)
    elif legacy_summary:
        render_legacy_summary(summary_data, title, url, domain, created_at, legacy_summary)


def render_legacy_summary(
    summary_data: dict[str, Any],
    title: str,
    url: str,
    domain: str,
    created_at: str,
    summary_text: str,
) -> None:
    with st.expander(f"▼ {title} - {domain}", expanded=False):
        st.markdown(f"**🔗 [{url}]({url})**")

        st.markdown("**📝 Summary**")
        st.info(summary_text)

        st.divider()

        metadata_cols = st.columns(3)
        with metadata_cols[0]:
            tokens = summary_data.get("tokens_used", "N/A")
            st.caption(f"**Tokens:** {tokens}")
        with metadata_cols[1]:
            latency = summary_data.get("latency_ms", "N/A")
            if latency != "N/A":
                latency_s = round(latency / 1000, 1)
                st.caption(f"**Latency:** {latency_s}s")
        with metadata_cols[2]:
            st.caption(f"**Model:** {summary_data.get('model', 'N/A')}")

        st.caption(f"{format_timestamp(created_at)}")


def render_structured_summary(summary_data: dict[str, Any], title: str, url: str, domain: str, created_at: str) -> None:
    structured_summary = summary_data.get("structured_summary")
    if not structured_summary:
        return

    try:
        summary = KnowledgeGraphSummary.model_validate(structured_summary)
    except ValidationError:
        return

    classification = summary.classification
    topic_tag = classification.primary_topic if classification else "N/A"
    content_type = classification.content_type if classification else "N/A"
    depth = classification.depth if classification else "N/A"

    with st.expander(f"▼ {title} - {domain}", expanded=False):
        st.markdown(f"**🔗 [{url}]({url})**")

        st.markdown("**📝 Core Answer**")
        st.info(summary.core_answer)

        if summary.unique_insights:
            st.markdown(f"**💡 Unique Insights** ({len(summary.unique_insights)})")
            for insight in summary.unique_insights[:5]:
                st.markdown(f"- {insight}")
            if len(summary.unique_insights) > 5:
                st.caption(f"... and {len(summary.unique_insights) - 5} more")

        col1, col2, col3 = st.columns(3)

        with col1:
            if summary.people:
                st.markdown(f"**👤 People** ({len(summary.people)})")
                people_names = [p.name for p in summary.people[:5]]
                st.caption(", ".join(people_names))

        with col2:
            if summary.organizations:
                st.markdown(f"**🏢 Organizations** ({len(summary.organizations)})")
                org_names = [o.name for o in summary.organizations[:5]]
                st.caption(", ".join(org_names))

        with col3:
            if summary.concepts:
                st.markdown(f"**🔬 Concepts** ({len(summary.concepts)})")
                concept_names = [c.name for c in summary.concepts[:5]]
                st.caption(", ".join(concept_names))

        st.divider()

        if summary.core_insights:
            st.markdown("**🎯 Core Insights**")
            for i, insight in enumerate(summary.core_insights, 1):
                with st.container():
                    st.markdown(f"**{i}. {insight.insight}**")
                    st.caption(f"💭 Memory aid: _{insight.memory_aid}_")
                    if insight.supporting_facts:
                        st.markdown("Supporting facts:")
                        for fact in insight.supporting_facts:
                            st.markdown(f"  - {fact}")
                    if insight.quantitative_data:
                        st.markdown(f"  📊 {insight.quantitative_data}")
                    if insight.why_it_matters:
                        st.markdown(f"  🎯 Why it matters: {insight.why_it_matters}")
                    st.write("")

        if summary.knowledge_graph_ascii:
            st.markdown("**🗺️ Knowledge Graph**")
            st.code(summary.knowledge_graph_ascii, language=None)

        if summary.examples_analogies:
            st.markdown("**📚 Examples & Analogies**")
            for example in summary.examples_analogies:
                st.markdown(f"- **{example.name}**: {example.description}")
                if example.full_quote_context:
                    st.caption(f'"{example.full_quote_context}"')

        if summary.forward_looking:
            st.markdown("**🔮 Forward Looking**")
            for item in summary.forward_looking:
                st.markdown(f"- {item}")

        if summary.memory_aids:
            st.markdown("**🧠 Memory Aids**")
            st.markdown(f"**Key Phrase:** {summary.memory_aids.key_phrase}")
            st.markdown(f"**Visual Metaphor:** {summary.memory_aids.visual_metaphor}")
            if summary.memory_aids.mnemonic:
                st.markdown(f"**Mnemonic:** {summary.memory_aids.mnemonic}")

        st.divider()

        metadata_cols = st.columns(4)
        with metadata_cols[0]:
            st.caption(f"**Topic:** {topic_tag}")
        with metadata_cols[1]:
            st.caption(f"**Type:** {content_type}")
        with metadata_cols[2]:
            st.caption(f"**Depth:** {depth}")
        with metadata_cols[3]:
            tokens = summary_data.get("tokens_used", "N/A")
            latency = summary_data.get("latency_ms", "N/A")
            if latency != "N/A":
                latency_s = round(latency / 1000, 1)
                st.caption(f"**Stats:** {tokens} tok · {latency_s}s")
            else:
                st.caption(f"**Tokens:** {tokens}")

        st.caption(f"Model: {summary_data.get('model', 'N/A')} • {format_timestamp(created_at)}")


def main():
    st.title("🧠 Knowledge Feed")

    summaries = load_summaries()

    if not summaries:
        st.warning("No summaries found. Run the Dagster pipeline to generate summaries.")
        st.info("Summaries should be located in `artifacts/silver/silver_summary/`")
        return

    success_count = sum(1 for s in summaries if s.get("status") == "success")
    failed_count = sum(1 for s in summaries if s.get("status") == "failed")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles", len(summaries))
    with col2:
        st.metric("Successfully Summarized", success_count)
    with col3:
        st.metric("Failed", failed_count)

    st.divider()

    for summary_data in summaries:
        render_summary_card(summary_data)

    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
