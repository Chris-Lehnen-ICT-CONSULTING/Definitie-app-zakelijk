"""Sources Renderer - Renders web sources/provenance section.

Extracted from definition_generator_tab.py to reduce God Class complexity.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import streamlit as st

from ui.components.formatters import get_provider_label

logger = logging.getLogger(__name__)


def _extract_metadata_value(
    saved_record: Any,
    agent_result: dict[str, Any] | Any,
    key: str,
) -> Any:
    """Extract a metadata value from saved_record or agent_result.

    Tries multiple locations in order:
    1. saved_record.metadata[key]
    2. agent_result.metadata[key] (dict format)
    3. agent_result.metadata[key] (object format)
    """
    # Try saved_record first
    if saved_record and getattr(saved_record, "metadata", None):
        meta = saved_record.metadata
        if isinstance(meta, dict) and key in meta:
            return meta.get(key)

    # Try agent_result dict format
    if isinstance(agent_result, dict):
        meta = agent_result.get("metadata")
        if isinstance(meta, dict) and key in meta:
            return meta.get(key)
    # Try agent_result object format
    elif hasattr(agent_result, "metadata") and isinstance(agent_result.metadata, dict):
        if key in agent_result.metadata:
            return agent_result.metadata.get(key)

    return None


def _extract_sources(
    saved_record: Any,
    agent_result: dict[str, Any] | Any,
) -> list[dict] | None:
    """Extract sources from various locations with fallback chain.

    Tries multiple locations in order:
    1. saved_record.metadata.sources
    2. agent_result.sources (V2 direct key)
    3. agent_result.sources (attribute style)
    4. agent_result.metadata.sources (legacy)
    """
    sources = None

    # 1) Try saved_record.metadata
    if saved_record and getattr(saved_record, "metadata", None):
        metadata = saved_record.metadata
        if isinstance(metadata, dict):
            sources = metadata.get("sources")

    # 2) Direct sources key on agent_result dict
    if sources is None and isinstance(agent_result, dict):
        sources = agent_result.get("sources")

    # 2b) Attribute style (legacy)
    if sources is None and hasattr(agent_result, "sources"):
        sources = agent_result.sources

    # 3) Fallback to agent_result.metadata (legacy)
    if sources is None and isinstance(agent_result, dict):
        meta = agent_result.get("metadata")
        if isinstance(meta, dict):
            sources = meta.get("sources")
    elif sources is None and hasattr(agent_result, "metadata"):
        if isinstance(agent_result.metadata, dict):
            sources = agent_result.metadata.get("sources")

    return sources


class SourcesRenderer:
    """Renders web sources (provenance) section.

    Handles:
    - Finding sources from multiple fallback locations
    - Displaying web lookup status and availability
    - Rendering sources grouped by provider
    - Debug toggles for SRU/WL troubleshooting
    """

    def render_sources_section(
        self,
        generation_result: dict[str, Any],
        agent_result: dict[str, Any] | Any,
        saved_record: Any = None,
    ) -> None:
        """Render complete sources section with fallback logic.

        Args:
            generation_result: Full generation result dict
            agent_result: Agent result (V2 dict or legacy object)
            saved_record: Saved DefinitieRecord (optional)
        """
        try:
            sources = _extract_sources(saved_record, agent_result)

            st.markdown("#### 📚 Gebruikte Bronnen")

            # Extract status metadata
            status_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_status"
            )
            available_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_available"
            )
            timeout_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_timeout"
            )

            # Show status information
            self._render_status_info(status_meta, available_meta, timeout_meta)

            # Debug toggles
            self._render_debug_toggles(
                saved_record, agent_result, status_meta, available_meta, timeout_meta
            )

            # Handle no sources case
            if not sources:
                self._render_no_sources_message(status_meta, available_meta)
                return

            # Render sources list
            self._render_sources_list(sources)

        except (KeyError, AttributeError, TypeError, ValueError) as e:
            logger.error(f"Kon bronnen sectie niet renderen: {e}", exc_info=True)
            st.warning(
                "Bronnen konden niet worden weergegeven. "
                "Probeer de pagina te vernieuwen."
            )

    def _render_status_info(
        self,
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render web lookup status information."""
        if status_meta or available_meta is not None:
            status_text = status_meta or "onbekend"
            avail_text = (
                "beschikbaar"
                if available_meta is True
                else "niet beschikbaar" if available_meta is False else "onbekend"
            )
            # Fallback to env if metadata has no timeout
            if timeout_meta is None:
                try:
                    timeout_meta = float(
                        os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", "10.0")
                    )
                except Exception:
                    timeout_meta = 10.0
            st.caption(
                f"Web lookup: {status_text} ({avail_text}) — timeout {float(timeout_meta):.1f}s"
            )

    def _render_debug_toggles(
        self,
        saved_record: Any,
        agent_result: Any,
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render debug toggles for SRU/WL troubleshooting."""
        debug_info = _extract_metadata_value(
            saved_record, agent_result, "web_lookup_debug"
        )

        # SRU/WL debug: show lookup attempts (JSON)
        if st.checkbox(
            "🐛 SRU/WL debug: Toon lookup attempts (JSON)",
            key="debug_web_lookup_attempts",
        ):
            st.json(debug_info or {})

        # Show attempts table if available
        if debug_info and isinstance(debug_info, dict):
            attempts_list = debug_info.get("attempts") or []
            if attempts_list:
                self._render_attempts_table(attempts_list)

        # Raw web_lookup data debug
        if st.checkbox(
            "🐛 Debug: Toon ruwe web_lookup data (JSON)",
            key="debug_web_lookup_sources_raw",
        ):
            self._render_raw_debug_data(
                saved_record, agent_result, status_meta, available_meta, timeout_meta
            )

    def _render_attempts_table(self, attempts_list: list[dict]) -> None:
        """Render attempts as a table."""
        if st.checkbox(
            "🐛 SRU/WL debug: Toon pogingdetails (tabel)",
            key="debug_web_lookup_attempts_table",
        ):
            rows = []
            for a in attempts_list:
                try:
                    provider = a.get("provider") or a.get("endpoint") or "?"
                    api = a.get("api_type") or "?"
                    strategy = a.get("strategy") or (
                        "fallback" if a.get("fallback") else ""
                    )
                    q = a.get("query") or a.get("term") or ""
                    status = (
                        a.get("status")
                        if "status" in a
                        else (
                            "ok"
                            if a.get("success")
                            else "fail" if "success" in a else ""
                        )
                    )
                    records = a.get("records")
                    url = a.get("url") or ""
                    rows.append(
                        {
                            "provider": provider,
                            "api": api,
                            "strategie": strategy,
                            "query/term": q,
                            "status": status,
                            "records": records,
                            "url": url,
                        }
                    )
                except (TypeError, AttributeError):
                    try:
                        repr_str = repr(a)
                        truncated = repr_str[:100] if len(repr_str) > 100 else repr_str
                    except Exception:
                        truncated = f"<unrepresentable {type(a).__name__}>"
                    logger.warning(
                        "Malformed attempt in _render_attempts_table: "
                        "type=%s, repr=%r",
                        type(a).__name__,
                        truncated,
                    )
                    continue

            if rows:
                try:
                    import pandas as pd  # type: ignore

                    st.dataframe(pd.DataFrame(rows))
                except Exception:
                    # Fallback without pandas
                    for r in rows:
                        st.markdown(
                            f"- {r['provider']} ({r['api']}): {r['strategie']} — {r['query/term']}"
                            f" — status={r['status']} records={r.get('records') or 0}"
                        )

    def _render_raw_debug_data(
        self,
        saved_record: Any,
        agent_result: Any,
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render raw debug data for troubleshooting."""
        saved_meta_sources = None
        agent_meta_sources = None
        agent_attr_sources = None
        agent_top_sources = None

        if saved_record and getattr(saved_record, "metadata", None):
            m = saved_record.metadata
            if isinstance(m, dict):
                saved_meta_sources = m.get("sources")

        if isinstance(agent_result, dict):
            m = agent_result.get("metadata")
            if isinstance(m, dict):
                agent_meta_sources = m.get("sources")
            agent_top_sources = agent_result.get("sources")
        elif hasattr(agent_result, "metadata") and isinstance(
            agent_result.metadata, dict
        ):
            agent_meta_sources = agent_result.metadata.get("sources")

        if hasattr(agent_result, "sources"):
            agent_attr_sources = agent_result.sources

        st.json(
            {
                "web_lookup_status": status_meta,
                "web_lookup_available": available_meta,
                "web_lookup_timeout": timeout_meta,
                "saved_record.metadata.sources": saved_meta_sources,
                "agent_result.metadata.sources": agent_meta_sources,
                "agent_result.sources": agent_attr_sources,
                "agent_result.top_level_sources": agent_top_sources,
            }
        )

    def _render_no_sources_message(
        self,
        status_meta: str | None,
        available_meta: bool | None,
    ) -> None:
        """Render appropriate message when no sources are found."""
        if available_meta is False or status_meta == "not_available":
            msg = "ℹ️ Web lookup is niet beschikbaar in deze omgeving."
        elif status_meta == "timeout":
            msg = "⏱️ Web lookup time-out — geen bronnen opgehaald."
        elif status_meta == "error":
            msg = "⚠️ Web lookup fout — geen bronnen opgehaald."
        else:
            msg = "ℹ️ Geen relevante externe bronnen gevonden."
        st.info(msg)

    def _render_sources_list(self, sources: list[dict]) -> None:
        """Render the list of sources with expanders."""
        for idx, src in enumerate(sources):
            provider_label = src.get("source_label") or get_provider_label(
                src.get("provider", "bron")
            )
            title = src.get("title") or src.get("definition") or "(zonder titel)"
            url = src.get("url") or src.get("link") or ""
            score = src.get("score") or src.get("confidence") or 0.0
            used = src.get("used_in_prompt", False)
            snippet = src.get("snippet") or src.get("context") or ""
            is_authoritative = src.get("is_authoritative", False)
            legal_meta = src.get("legal")

            with st.expander(
                f"{idx+1}. {provider_label} — {title[:80]}", expanded=(idx == 0)
            ):
                # Show badges
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if is_authoritative:
                        st.success("✓ Autoritatief")
                with col2:
                    if used:
                        st.info("→ In prompt")

                # Document source: show filename/location
                if src.get("provider") == "documents":
                    fname = src.get("title") or src.get("filename")
                    cite = src.get("citation_label")
                    if fname or cite:
                        st.markdown(
                            f"**Document**: {fname or '(onbekend)'}"
                            f"{f' · Locatie: {cite}' if cite else ''}"
                        )

                # Show juridical citation if available
                if legal_meta and legal_meta.get("citation_text"):
                    st.markdown(
                        f"**Juridische verwijzing**: {legal_meta['citation_text']}"
                    )

                # Show score and snippet
                st.markdown(f"**Score**: {score:.2f}")
                if snippet:
                    st.markdown(
                        f"**Fragment**: {snippet[:500]}{'...' if len(snippet) > 500 else ''}"
                    )
                if url:
                    st.markdown(f"[🔗 Open bron]({url})")


# Convenience function for module-level usage
def render_sources_section(
    generation_result: dict[str, Any],
    agent_result: dict[str, Any] | Any,
    saved_record: Any = None,
) -> None:
    """Render sources section (convenience function)."""
    renderer = SourcesRenderer()
    renderer.render_sources_section(generation_result, agent_result, saved_record)
