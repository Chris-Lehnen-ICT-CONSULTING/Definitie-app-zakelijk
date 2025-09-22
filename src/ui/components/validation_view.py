"""
Shared validation view helpers for rendering V2 validation details consistently
across Generator, Edit and Expert Review tabs.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def _rule_sort_key(rule_id: str) -> tuple[int, int]:
    rid = (rule_id or "").upper().replace("_", "-")
    prefix = rid.split("-", 1)[0] if "-" in rid else rid[:4]
    order = {
        "CON": 0,
        "ESS": 1,
        "STR": 2,
        "INT": 3,
        "SAM": 4,
        "ARAI": 5,
        "VER": 6,
        "VAL": 7,
    }
    grp = order.get(prefix, 99)
    num = 9999
    try:
        tail = rid.split("-", 1)[1] if "-" in rid else ""
        import re as _re
        m = _re.search(r"(\d+)", tail)
        num = int(m.group(1)) if m else 9999
    except Exception:
        num = 9999
    return grp, num


def _get_rule_info(rule_id: str) -> tuple[str, str]:
    """Read (name, explanation) for a rule from JSON when available."""
    try:
        from pathlib import Path
        import json as _json

        rid = (rule_id or "").replace("_", "-")
        json_path = Path("src/toetsregels/regels") / f"{rid}.json"
        if not json_path.exists():
            return "", ""
        data = _json.loads(json_path.read_text(encoding="utf-8"))
        name = str(data.get("naam") or "").strip()
        explanation = str(data.get("uitleg") or data.get("toetsvraag") or "").strip()
        return name, explanation
    except Exception:
        return "", ""


def render_v2_validation_details(validation_result: dict[str, Any]) -> None:
    """Render V2 validation details consistently for all tabs."""
    overall_score = float(validation_result.get("overall_score", 0.0))
    violations = list(validation_result.get("violations") or [])
    passed_rules = list(validation_result.get("passed_rules") or [])

    score_color = "green" if overall_score > 0.8 else ("orange" if overall_score > 0.6 else "red")
    st.markdown(
        f"**Overall Score:** <span style='color: {score_color}'>{overall_score:.2f}</span>",
        unsafe_allow_html=True,
    )

    # Summary
    failed_ids = sorted({str(v.get('rule_id') or v.get('code') or '') for v in violations if isinstance(v, dict)})
    passed_ids = sorted({str(r) for r in passed_rules})
    total = len(set(failed_ids).union(passed_ids))
    passed_count = len(passed_ids)
    failed_count = len(failed_ids)
    pct = (passed_count / total * 100.0) if total > 0 else 0.0
    st.markdown(
        f"📊 **Toetsing Samenvatting**: {passed_count}/{total} regels geslaagd ({pct:.1f}%)"
        + (f" | ❌ {failed_count} gefaald" if failed_count else "")
    )

    # Violations
    if violations:
        st.markdown("#### ❌ Gevallen regels")

        def _v_key(v):
            rid = str(v.get("rule_id") or v.get("code") or "")
            return _rule_sort_key(rid)

        for v in sorted(violations, key=_v_key):
            rid = str(v.get("rule_id") or v.get("code") or "")
            sev = str(v.get("severity", "warning")).lower()
            desc = v.get("description") or v.get("message") or ""
            suggestion = v.get("suggestion")
            if suggestion:
                desc = f"{desc} · Wat verbeteren: {suggestion}"
            emoji = "❌" if sev in {"critical", "error", "high"} else "⚠️"
            name, explanation = _get_rule_info(rid)
            name_part = f" — {name}" if name else ""
            expl_labeled = f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
            st.markdown(f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}")

    # Passed rules
    if passed_ids:
        with st.expander("✅ Geslaagde regels", expanded=False):
            for rid in sorted(passed_ids, key=_rule_sort_key):
                name, explanation = _get_rule_info(rid)
                name_part = f" — {name}" if name else ""
                wat_toetst = f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
                st.markdown(f"✅ {rid}{name_part}: OK · {wat_toetst}")

