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
    initial_sidebar_state="expanded",
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


def render_compact_card(summary_data: dict[str, Any]) -> None:
    title = summary_data.get("title", "Untitled")
    url = summary_data.get("url", "")
    domain = extract_domain(url)
    status = summary_data.get("status", "unknown")
    created_at = summary_data.get("created_at", "")

    if status == "failed":
        with st.container(border=True):
            st.markdown(f"### ❌ {title[:60]}...")
            st.caption(f"🌐 {domain} • {format_timestamp(created_at)}")
            st.error(f"Failed: {summary_data.get('error', 'Unknown error')}")
        return

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

    with st.container(border=True):
        st.markdown(f"### {title[:70]}")
        st.caption(f"{topic_tag} • {content_type} • {depth}")

        st.markdown(f"**🔗** [{domain}]({url})")

        st.markdown(f"**📝** {summary.core_answer}")

        if summary.why_this_matters:
            st.markdown(f"**💎 Why:** {summary.why_this_matters}")

        if summary.unique_insights:
            with st.expander(f"💡 {len(summary.unique_insights)} Unique Insights"):
                for insight in summary.unique_insights[:3]:
                    st.markdown(f"• {insight}")
                if len(summary.unique_insights) > 3:
                    st.caption(f"... and {len(summary.unique_insights) - 3} more")

        info_cols = st.columns([1, 1, 1])
        with info_cols[0]:
            if summary.people:
                st.caption(f"👤 {len(summary.people)} people")
        with info_cols[1]:
            if summary.organizations:
                st.caption(f"🏢 {len(summary.organizations)} orgs")
        with info_cols[2]:
            if summary.concepts:
                st.caption(f"🔬 {len(summary.concepts)} concepts")

        st.caption(f"{format_timestamp(created_at)} • {summary_data.get('tokens_used', 'N/A')} tokens")


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
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.markdown(f"**🔗** [{url}]({url})")
            st.caption(f"{topic_tag} • {content_type} • {depth}")
        with header_cols[1]:
            tokens = summary_data.get("tokens_used", "N/A")
            latency = summary_data.get("latency_ms", "N/A")
            if latency != "N/A":
                latency_s = round(latency / 1000, 1)
                st.caption(f"**{tokens}** tok • **{latency_s}s**")
            st.caption(f"{format_timestamp(created_at)}")

        st.info(f"**📝 Core Answer:** {summary.core_answer}")

        if summary.why_this_matters:
            st.success(f"**💎 Why This Matters:** {summary.why_this_matters}")

        if summary.expert_opinion:
            st.markdown(f"**🎓 Expert Opinion:** _{summary.expert_opinion}_")

        tab1, tab2, tab3, tab4 = st.tabs(["💡 Insights", "🎯 Details", "🗺️ Graph & Data", "🧠 Memory"])

        with tab1:
            if summary.unique_insights:
                st.markdown(f"**Unique Insights** ({len(summary.unique_insights)})")
                for insight in summary.unique_insights:
                    st.markdown(f"• {insight}")

            if summary.core_insights:
                st.divider()
                st.markdown("**Core Insights**")
                for i, insight in enumerate(summary.core_insights, 1):
                    with st.container():
                        st.markdown(f"**{i}. {insight.insight}**")
                        st.caption(f"💭 _{insight.memory_aid}_")
                        if insight.supporting_facts:
                            for fact in insight.supporting_facts:
                                st.markdown(f"  • {fact}")
                        if insight.quantitative_data:
                            st.markdown(f"  📊 {insight.quantitative_data}")
                        if insight.why_it_matters:
                            st.markdown(f"  🎯 {insight.why_it_matters}")
                        if insight.connections:
                            st.markdown(f"  🔗 {', '.join(insight.connections)}")
                        st.write("")

        with tab2:
            entity_cols = st.columns(3)
            with entity_cols[0]:
                if summary.people:
                    st.markdown(f"**👤 People** ({len(summary.people)})")
                    for person in summary.people:
                        st.markdown(f"**{person.name}**")
                        st.caption(person.context)
                        st.write("")

            with entity_cols[1]:
                if summary.organizations:
                    st.markdown(f"**🏢 Organizations** ({len(summary.organizations)})")
                    for org in summary.organizations:
                        st.markdown(f"**{org.name}**")
                        st.caption(org.context)
                        st.write("")

            with entity_cols[2]:
                if summary.concepts:
                    st.markdown(f"**🔬 Concepts** ({len(summary.concepts)})")
                    for concept in summary.concepts:
                        st.markdown(f"**{concept.name}**")
                        st.caption(concept.context)
                        st.write("")

        with tab3:
            if summary.knowledge_graph_ascii:
                st.markdown("**🗺️ Knowledge Graph**")
                st.code(summary.knowledge_graph_ascii, language=None)

            data_cols = st.columns(2)
            with data_cols[0]:
                if summary.formulas_data:
                    st.markdown(f"**📊 Formulas & Data** ({len(summary.formulas_data)})")
                    for formula in summary.formulas_data:
                        st.markdown(f"• **{formula.name}**: {formula.context}")

            with data_cols[1]:
                if summary.examples_analogies:
                    st.markdown(f"**📚 Examples & Analogies** ({len(summary.examples_analogies)})")
                    for example in summary.examples_analogies:
                        st.markdown(f"• **{example.name}**: {example.context}")

            if summary.forward_looking:
                st.divider()
                st.markdown("**🔮 Forward Looking**")
                for item in summary.forward_looking:
                    st.markdown(f"• {item}")

        with tab4:
            if summary.memory_aids:
                st.markdown(f"**💬 Key Phrase:** _{summary.memory_aids.key_phrase}_")
                st.markdown(f"**🖼️ Visual Metaphor:** {summary.memory_aids.visual_metaphor}")
                if summary.memory_aids.mnemonic:
                    st.markdown(f"**🔤 Mnemonic:** {summary.memory_aids.mnemonic}")

            if classification and classification.related_topics:
                st.divider()
                st.markdown("**Related Topics**")
                st.caption(", ".join(classification.related_topics))

        st.caption(f"Model: {summary_data.get('model', 'N/A')}")


def apply_filters(summaries: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    filtered = summaries

    if filters["topics"] and "All" not in filters["topics"]:
        filtered = [
            s for s in filtered if s.get("structured_summary", {}).get("classification", {}).get("primary_topic") in filters["topics"]
        ]

    if filters["content_types"] and "All" not in filters["content_types"]:
        filtered = [
            s for s in filtered if s.get("structured_summary", {}).get("classification", {}).get("content_type") in filters["content_types"]
        ]

    if filters["depths"] and "All" not in filters["depths"]:
        filtered = [s for s in filtered if s.get("structured_summary", {}).get("classification", {}).get("depth") in filters["depths"]]

    if filters["status"] != "All":
        filtered = [s for s in filtered if s.get("status") == filters["status"]]

    return filtered


def render_sidebar(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    with st.sidebar:
        st.header("🔍 Filters")

        all_topics = set()
        all_content_types = set()
        all_depths = set()

        for s in summaries:
            if s.get("structured_summary"):
                cls = s["structured_summary"].get("classification", {})
                if cls.get("primary_topic"):
                    all_topics.add(cls["primary_topic"])
                if cls.get("content_type"):
                    all_content_types.add(cls["content_type"])
                if cls.get("depth"):
                    all_depths.add(cls["depth"])

        st.subheader("Status")
        status = st.radio("Filter by status", ["All", "success", "failed"], horizontal=True)

        st.subheader("Topics")
        topics = ["All"] + sorted(all_topics)
        selected_topics = st.multiselect("Primary topics", topics, default=["All"])

        st.subheader("Content Type")
        content_types = ["All"] + sorted(all_content_types)
        selected_content_types = st.multiselect("Content types", content_types, default=["All"])

        st.subheader("Depth")
        depths = ["All"] + sorted(all_depths)
        selected_depths = st.multiselect("Complexity level", depths, default=["All"])

        st.divider()

        view_mode = st.radio("View Mode", ["Compact", "Detailed"], horizontal=True)

        return {
            "status": status,
            "topics": selected_topics,
            "content_types": selected_content_types,
            "depths": selected_depths,
            "view_mode": view_mode,
        }


def main():
    st.title("🧠 Knowledge Feed")

    summaries = load_summaries()

    if not summaries:
        st.warning("No summaries found. Run the Dagster pipeline to generate summaries.")
        st.info("Summaries should be located in `artifacts/silver/silver_summary/`")
        return

    filters = render_sidebar(summaries)
    filtered_summaries = apply_filters(summaries, filters)

    success_count = sum(1 for s in filtered_summaries if s.get("status") == "success")
    failed_count = sum(1 for s in filtered_summaries if s.get("status") == "failed")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", len(summaries))
    with col2:
        st.metric("Filtered", len(filtered_summaries))
    with col3:
        st.metric("Success", success_count)
    with col4:
        st.metric("Failed", failed_count)

    st.divider()

    if not filtered_summaries:
        st.info("No summaries match the selected filters.")
        return

    if filters["view_mode"] == "Compact":
        cols_per_row = 2
        for i in range(0, len(filtered_summaries), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(filtered_summaries):
                    with col:
                        render_compact_card(filtered_summaries[i + j])
    else:
        for summary_data in filtered_summaries:
            render_summary_card(summary_data)

    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
