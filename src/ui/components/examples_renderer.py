"""
Uniform examples renderer for UI tabs.

Provides a consistent layout for examples across Generator, Edit, and Expert Review tabs.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

import streamlit as st


def _as_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        # support comma-separated fallbacks
        return [p.strip() for p in s.split(",") if p.strip()]
    return []


def render_examples_readonly(examples: Dict[str, Any] | None) -> None:
    """Render examples in a consistent, read-only layout.

    Sections order:
    - Voorbeeldzinnen
    - Praktijkvoorbeelden
    - Tegenvoorbeelden
    - Synoniemen
    - Antoniemen
    - Toelichting
    """
    data = examples or {}

    sections: list[tuple[str, str, Iterable[str]]] = [
        ("📄 Voorbeeldzinnen", "voorbeeldzinnen", _as_list(data.get("voorbeeldzinnen"))),
        ("💼 Praktijkvoorbeelden", "praktijkvoorbeelden", _as_list(data.get("praktijkvoorbeelden"))),
        ("❌ Tegenvoorbeelden", "tegenvoorbeelden", _as_list(data.get("tegenvoorbeelden"))),
        ("🔄 Synoniemen", "synoniemen", _as_list(data.get("synoniemen"))),
        ("↔️ Antoniemen", "antoniemen", _as_list(data.get("antoniemen"))),
    ]

    for title, _key, items in sections:
        items = list(items)
        with st.expander(title, expanded=bool(items) and title in {"📄 Voorbeeldzinnen", "💼 Praktijkvoorbeelden", "💡 Toelichting", "📝 Toelichting"}):
            if items:
                for it in items:
                    st.write(f"• {it}")
            else:
                st.caption("Geen items")

    # Toelichting (string)
    with st.expander("📝 Toelichting", expanded=bool(data.get("toelichting"))):
        tol = data.get("toelichting")
        if isinstance(tol, str) and tol.strip():
            st.write(tol)
        else:
            st.caption("Geen toelichting")


def render_examples_expandable(examples: Dict[str, Any] | None) -> None:
    """Render examples met dezelfde expanders‑indeling als de Generator‑tab.

    - 📄 Voorbeeldzinnen: bullets
    - 💼 Praktijkvoorbeelden: informatieve blokken
    - ❌ Tegenvoorbeelden: waarschuwing blokken
    - 🔄 Synoniemen: bullets (geen voorkeursterm selectie hier)
    - ↔️ Antoniemen: bullets
    - 📝 Toelichting: tekstblok
    """
    data = examples or {}

    vz = _as_list(data.get("voorbeeldzinnen"))
    if vz:
        with st.expander("📄 Voorbeeldzinnen", expanded=True):
            for v in vz:
                st.write(f"• {v}")

    pv = _as_list(data.get("praktijkvoorbeelden"))
    if pv:
        with st.expander("💼 Praktijkvoorbeelden", expanded=True):
            for v in pv:
                st.info(v)

    tv = _as_list(data.get("tegenvoorbeelden"))
    if tv:
        with st.expander("❌ Tegenvoorbeelden", expanded=False):
            for v in tv:
                st.warning(v)

    syn = _as_list(data.get("synoniemen"))
    if syn:
        with st.expander("🔄 Synoniemen", expanded=False):
            for s in syn:
                st.write(f"• {s}")

    ant = _as_list(data.get("antoniemen"))
    if ant:
        with st.expander("↔️ Antoniemen", expanded=False):
            for a in ant:
                st.write(f"• {a}")

    tol = data.get("toelichting")
    if isinstance(tol, str) and tol.strip():
        with st.expander("📝 Toelichting", expanded=True):
            st.write(tol)
