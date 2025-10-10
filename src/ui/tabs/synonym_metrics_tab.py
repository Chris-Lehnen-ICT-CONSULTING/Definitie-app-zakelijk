"""
Synonym Metrics Dashboard Tab - PHASE 4.2 Implementation.

Provides real-time metrics en monitoring voor Synonym Orchestrator v3.1:
- Cache performance (hit rate, size, stats)
- GPT-4 enrichment analytics (success rate, timing)
- Approval workflow statistics (pending review count)
- Top used synonyms

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 1082-1104: Metrics Dashboard specification
"""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class SynonymMetricsTab:
    """
    Synonym Metrics Dashboard Tab.

    Renders monitoring dashboard met:
    - Cache performance metrics
    - GPT-4 enrichment statistics
    - Approval workflow stats
    - Top synonyms by usage
    """

    def __init__(self):
        """Initialize metrics tab."""
        self.enrichment_log_path = Path("logs/synonym_enrichment.log")

    def render(self):
        """Render main metrics dashboard."""
        st.title("📊 Synonym System Metrics")

        # Tab selectors voor verschillende metric categories
        metric_category = st.radio(
            "Selecteer Metric Categorie",
            options=["cache", "enrichment", "approval", "top_usage"],
            format_func=lambda x: {
                "cache": "🚀 Cache Performance",
                "enrichment": "🤖 GPT-4 Enrichment",
                "approval": "✅ Approval Workflow",
                "top_usage": "📈 Top Synonyms",
            }[x],
            horizontal=True,
            key="metric_category_selector",
        )

        st.markdown("---")

        # Render selected category
        if metric_category == "cache":
            self._render_cache_metrics()
        elif metric_category == "enrichment":
            self._render_enrichment_metrics()
        elif metric_category == "approval":
            self._render_approval_metrics()
        elif metric_category == "top_usage":
            self._render_top_usage_metrics()

    def _render_cache_metrics(self):
        """Render cache performance metrics."""
        st.subheader("🚀 Cache Performance")

        try:
            from src.services.container import get_container

            orchestrator = get_container().synonym_orchestrator()
            cache_stats = orchestrator.get_cache_stats()

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                hit_rate = cache_stats["hit_rate"]
                delta_color = "normal" if hit_rate >= 0.8 else "inverse"
                st.metric(
                    "Cache Hit Rate",
                    f"{hit_rate:.1%}",
                    delta="Target: 80%",
                    delta_color=delta_color,
                )

            with col2:
                st.metric("Cache Size", cache_stats["size"])

            with col3:
                st.metric("Cache Hits", cache_stats["hits"])

            with col4:
                st.metric("Cache Misses", cache_stats["misses"])

            # Configuration info
            st.markdown("#### Configuration")
            col1, col2 = st.columns(2)

            with col1:
                st.info(f"**Max Size:** {cache_stats['max_size']} entries")

            with col2:
                st.info(f"**TTL:** {cache_stats['ttl_seconds']} seconds")

            # Performance assessment
            st.markdown("#### Performance Assessment")

            total_queries = cache_stats["hits"] + cache_stats["misses"]

            if total_queries == 0:
                st.warning("⚠️ No queries yet - cache metrics unavailable")
            elif hit_rate >= 0.8:
                st.success(
                    f"✅ **Excellent** - Cache hit rate {hit_rate:.1%} exceeds target (80%)"
                )
            elif hit_rate >= 0.6:
                st.warning(
                    f"⚠️ **Acceptable** - Cache hit rate {hit_rate:.1%} below target but functional"
                )
            else:
                st.error(
                    f"❌ **Poor** - Cache hit rate {hit_rate:.1%} critically low (target: 80%)"
                )

        except Exception as e:
            st.error(f"❌ Failed to load cache metrics: {e}")
            logger.error(f"Cache metrics render failed: {e}", exc_info=True)

    def _render_enrichment_metrics(self):
        """Render GPT-4 enrichment statistics."""
        st.subheader("🤖 GPT-4 Enrichment Analytics")

        if not self.enrichment_log_path.exists():
            st.warning(f"⚠️ Enrichment log niet gevonden: {self.enrichment_log_path}")
            st.info("💡 Run enrichment eerst om metrics te genereren")
            return

        try:
            # Parse enrichment log (last 24 hours)
            enrichment_stats = self._parse_enrichment_logs(hours=24)

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                success_rate = enrichment_stats["success_rate"]
                delta_color = "normal" if success_rate >= 0.95 else "inverse"
                st.metric(
                    "Success Rate",
                    f"{success_rate:.1%}",
                    delta="Target: 95%",
                    delta_color=delta_color,
                )

            with col2:
                st.metric("Total Enrichments", enrichment_stats["total_enrichments"])

            with col3:
                avg_duration = enrichment_stats["avg_duration_seconds"]
                st.metric("Avg Duration", f"{avg_duration:.1f}s")

            with col4:
                st.metric("Timeouts", enrichment_stats["timeout_count"])

            # Recent enrichments
            st.markdown("#### Recent Enrichments (Last 10)")

            if enrichment_stats["recent_enrichments"]:
                for entry in enrichment_stats["recent_enrichments"][-10:]:
                    status_emoji = "✅" if entry["success"] else "❌"
                    st.text(
                        f"{status_emoji} {entry['timestamp']} | '{entry['term']}' | "
                        f"{entry['duration']:.1f}s | {entry['suggestions_count']} suggestions"
                    )
            else:
                st.info("No recent enrichments")

        except Exception as e:
            st.error(f"❌ Failed to parse enrichment logs: {e}")
            logger.error(f"Enrichment metrics parse failed: {e}", exc_info=True)

    def _render_approval_metrics(self):
        """Render approval workflow statistics."""
        st.subheader("✅ Approval Workflow")

        try:
            from src.services.container import get_container

            registry = get_container().synonym_registry()
            stats = registry.get_statistics()

            # Pending review count (Bug #3 FIX: members_by_status not by_status!)
            pending_count = stats.get("members_by_status", {}).get("ai_pending", 0)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Pending Review",
                    pending_count,
                    delta="Alert if > 500",
                    delta_color="inverse" if pending_count > 500 else "off",
                )

            with col2:
                active_count = stats.get("members_by_status", {}).get("active", 0)
                st.metric("Active Synonyms", active_count)

            with col3:
                rejected_count = stats.get("members_by_status", {}).get(
                    "rejected_auto", 0
                )
                st.metric("Rejected", rejected_count)

            # Approval rate calculation
            st.markdown("#### Approval Rate")

            total_reviewed = active_count + rejected_count
            if total_reviewed > 0:
                approval_rate = active_count / total_reviewed

                if approval_rate >= 0.7:
                    st.success(
                        f"✅ **Good** - {approval_rate:.1%} approval rate (target: >70%)"
                    )
                elif approval_rate >= 0.5:
                    st.warning(f"⚠️ **Moderate** - {approval_rate:.1%} approval rate")
                else:
                    st.error(
                        f"❌ **Low** - {approval_rate:.1%} approval rate (target: >70%)"
                    )

                # Bar chart
                import pandas as pd
                import plotly.express as px

                df = pd.DataFrame(
                    {
                        "Status": ["Approved", "Rejected"],
                        "Count": [active_count, rejected_count],
                    }
                )

                fig = px.bar(
                    df,
                    x="Status",
                    y="Count",
                    title="Approval vs Rejection",
                    color="Status",
                    color_discrete_map={"Approved": "#28a745", "Rejected": "#dc3545"},
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No reviews yet")

            # Source breakdown
            st.markdown("#### Source Breakdown")

            source_stats = stats.get("members_by_source", {})  # Bug #3 FIX!
            if source_stats:
                source_df = pd.DataFrame(
                    {
                        "Source": list(source_stats.keys()),
                        "Count": list(source_stats.values()),
                    }
                )

                fig2 = px.pie(
                    source_df,
                    values="Count",
                    names="Source",
                    title="Synonyms by Source",
                )

                st.plotly_chart(fig2, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Failed to load approval metrics: {e}")
            logger.error(f"Approval metrics render failed: {e}", exc_info=True)

    def _render_top_usage_metrics(self):
        """Render top used synonyms."""
        st.subheader("📈 Top Used Synonyms")

        try:
            from src.services.container import get_container

            registry = get_container().synonym_registry()

            # Get top 20 most used synonyms
            top_synonyms = registry.get_top_used_synonyms(limit=20)

            if top_synonyms:
                st.dataframe(
                    top_synonyms,
                    column_config={
                        "term": "Term",
                        "usage_count": st.column_config.NumberColumn(
                            "Usage Count", format="%d"
                        ),
                        "weight": st.column_config.NumberColumn(
                            "Weight", format="%.2f"
                        ),
                        "group": "Group",
                        "last_used": "Last Used",
                    },
                    hide_index=True,
                    use_container_width=True,
                )

                # Usage chart
                import pandas as pd
                import plotly.express as px

                df = pd.DataFrame(top_synonyms)

                fig = px.bar(
                    df.head(10),  # Top 10
                    x="term",
                    y="usage_count",
                    title="Top 10 Most Used Synonyms",
                    labels={"term": "Synonym", "usage_count": "Usage Count"},
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No usage data available yet")

        except Exception as e:
            st.error(f"❌ Failed to load top usage metrics: {e}")
            logger.error(f"Top usage metrics render failed: {e}", exc_info=True)

    def _parse_enrichment_logs(self, hours: int = 24) -> dict[str, Any]:
        """
        Parse enrichment log voor statistics.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with enrichment statistics
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        enrichments = []
        success_count = 0
        timeout_count = 0
        total_duration = 0.0

        try:
            with open(self.enrichment_log_path, encoding="utf-8") as f:
                for line in f:
                    # Parse log line
                    # Format: 2025-10-10 14:32:15 - INFO - Starting GPT-4 enrichment for 'term'
                    if "Enrichment complete" in line:
                        parts = line.split(" - ")
                        if len(parts) >= 3:
                            timestamp_str = parts[0].strip()
                            message = parts[2].strip()

                            # Parse timestamp
                            try:
                                timestamp = datetime.strptime(
                                    timestamp_str, "%Y-%m-%d %H:%M:%S"
                                )
                                timestamp = timestamp.replace(tzinfo=UTC)

                                if timestamp < cutoff_time:
                                    continue

                                # Extract term and duration from message
                                # "Enrichment complete for 'term': 3 suggestions, duration: 8.2s"
                                if "'" in message:
                                    term = message.split("'")[1]
                                    duration = float(
                                        message.split("duration: ")[1].replace("s", "")
                                    )
                                    suggestions_count = int(
                                        message.split(" suggestions")[0].split(": ")[-1]
                                    )

                                    enrichments.append(
                                        {
                                            "timestamp": timestamp_str,
                                            "term": term,
                                            "duration": duration,
                                            "suggestions_count": suggestions_count,
                                            "success": True,
                                        }
                                    )

                                    success_count += 1
                                    total_duration += duration

                            except Exception as parse_err:
                                logger.debug(
                                    f"Failed to parse enrichment line: {parse_err}"
                                )
                                continue

                    elif "timeout" in line.lower():
                        timeout_count += 1

                        # Add to enrichments as failed
                        parts = line.split(" - ")
                        if len(parts) >= 3:
                            timestamp_str = parts[0].strip()
                            message = parts[2].strip()

                            try:
                                timestamp = datetime.strptime(
                                    timestamp_str, "%Y-%m-%d %H:%M:%S"
                                )
                                timestamp = timestamp.replace(tzinfo=UTC)

                                if timestamp >= cutoff_time and "'" in message:
                                    term = message.split("'")[1]
                                    duration = float(
                                        message.split("after ")[1]
                                        .replace("s", "")
                                        .split()[0]
                                    )

                                    enrichments.append(
                                        {
                                            "timestamp": timestamp_str,
                                            "term": term,
                                            "duration": duration,
                                            "suggestions_count": 0,
                                            "success": False,
                                        }
                                    )

                            except Exception:
                                continue

        except FileNotFoundError:
            pass

        total_enrichments = len(enrichments)
        success_rate = (
            success_count / total_enrichments if total_enrichments > 0 else 0.0
        )
        avg_duration = total_duration / success_count if success_count > 0 else 0.0

        return {
            "total_enrichments": total_enrichments,
            "success_count": success_count,
            "success_rate": success_rate,
            "timeout_count": timeout_count,
            "avg_duration_seconds": avg_duration,
            "recent_enrichments": enrichments,
        }
