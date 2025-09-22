"""
Shared validation view helpers for rendering V2 validation details consistently
across Generator, Edit and Expert Review tabs.

Implements a unified detailed renderer with:
- Gate status indicator (acceptance_gate or explicit gate data)
- Toggle to show/hide details (per-context via key_prefix)
- Detailed list with icons and inline explanation per rule
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


def _extract_rule_id_from_line(line: str) -> str:
    """Extract rule ID (e.g., CON-01) heuristically from a line."""
    try:
        import re as _re
        m = _re.search(r"([A-Z]{2,5}(?:[-_][A-Z0-9]+)+)", str(line))
        return m.group(1) if m else ""
    except Exception:
        return ""


def _build_rule_hint_markdown(rule_id: str) -> str:
    """Build short hint explanation for a rule from its JSON definition.

    Shows:
    - What the rule checks (uitleg/toetsvraag)
    - Optional good/bad examples (first 1-2)
    - Link to the extended user guide
    """
    try:
        from pathlib import Path
        import json as _json

        rules_dir = Path("src/toetsregels/regels")
        rid = (rule_id or "").replace("_", "-")
        json_path = rules_dir / f"{rid}.json"
        if not json_path.exists():
            json_path = rules_dir / f"{rid}"  # fallback (if full name with ext)

        name = explanation = ""
        good = bad = []
        if json_path.exists():
            data = _json.loads(json_path.read_text(encoding="utf-8"))
            name = str(data.get("naam") or "").strip()
            explanation = str(data.get("uitleg") or data.get("toetsvraag") or "").strip()
            good = list(data.get("goede_voorbeelden") or [])
            bad = list(data.get("foute_voorbeelden") or [])

        lines: list[str] = []
        title = f"**{rule_id}** — {name}" if name else f"**{rule_id}**"
        lines.append(title)
        if explanation:
            lines.append(f"Wat toetst: {explanation}")
        if good:
            lines.append("\nGoed voorbeeld:")
            lines.extend([f"- {g}" for g in good[:2]])
        if bad:
            lines.append("\nFout voorbeeld:")
            lines.extend([f"- {b}" for b in bad[:2]])
        lines.append(
            "\nMeer uitleg: [Validatieregels (CON‑01 e.a.)](docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
        )
        return "\n".join(lines)
    except Exception:
        return (
            f"Meer uitleg: [Validatieregels (CON‑01 e.a.)]"
            f"(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
        )


def _calculate_validation_stats(violations: list, passed_rules: list) -> dict:
    failed_ids = sorted({
        str(v.get("rule_id") or v.get("code") or "")
        for v in violations if isinstance(v, dict)
    })
    passed_ids = sorted({str(r) for r in (passed_rules or [])})
    total = len(set(failed_ids).union(passed_ids))
    passed_count = len(passed_ids)
    failed_count = len(failed_ids)
    pct = (passed_count / total * 100.0) if total > 0 else 0.0
    return {
        "failed_ids": failed_ids,
        "passed_ids": passed_ids,
        "total": total,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "percentage": pct,
    }


def _build_detailed_assessment(validation_result: dict) -> list[str]:
    """Build a mixed list of summary, violations and passed rules lines."""
    violations = list(validation_result.get("violations") or [])
    passed_rules = list(validation_result.get("passed_rules") or [])
    stats = _calculate_validation_stats(violations, passed_rules)

    def _severity_emoji(sev: str) -> str:
        s = (sev or "").lower()
        if s in {"critical", "error", "high"}:
            return "❌"
        elif s in {"warning", "medium", "low"}:
            return "⚠️"
        return "📋"

    lines: list[str] = []
    # Summary first
    summary = (
        f"📊 **Toetsing Samenvatting**: {stats['passed_count']}/{stats['total']} regels geslaagd ({stats['percentage']:.1f}%)"
        + (f" | ❌ {stats['failed_count']} gefaald" if stats["failed_count"] else "")
    )
    lines.append(summary)

    # Violations (sorted)
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
        emoji = _severity_emoji(sev)
        name, explanation = _get_rule_info(rid)
        name_part = f" — {name}" if name else ""
        expl_labeled = f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
        lines.append(f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}")

    # Passed rules (sorted)
    for rid in sorted(stats["passed_ids"], key=_rule_sort_key):
        name, explanation = _get_rule_info(rid)
        name_part = f" — {name}" if name else ""
        wat_toetst = f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
        lines.append(f"✅ {rid}{name_part}: OK · {wat_toetst}")

    return lines


def render_v2_validation_details(validation_result: dict[str, Any]) -> None:
    """Render V2 validation details consistently for all tabs."""
    # Backwards-compatible simple renderer delegates to the unified detailed list without toggle.
    render_validation_detailed_list(validation_result, key_prefix="v2_default", show_toggle=False)


def render_validation_detailed_list(
    validation_result: dict[str, Any],
    *,
    key_prefix: str,
    show_toggle: bool = True,
    gate: dict | None = None,
) -> None:
    """Unified detailed renderer used across tabs.

    Args:
        validation_result: V2 dict result with overall_score, violations, passed_rules, acceptance_gate
        key_prefix: Unique context prefix for session keys (e.g., 'gen', 'edit_123', 'review_123')
        show_toggle: Whether to show a toggle to expand/collapse details
        gate: Optional explicit gate dict. If None, tries validation_result['acceptance_gate']
    """
    from ui.session_state import SessionStateManager

    # Score
    overall_score = float(validation_result.get("overall_score", 0.0))
    score_color = "green" if overall_score > 0.8 else ("orange" if overall_score > 0.6 else "red")
    st.markdown(
        f"**Overall Score:** <span style='color: {score_color}'>{overall_score:.2f}</span>",
        unsafe_allow_html=True,
    )

    # Gate indicator (supports both acceptance_gate and review/preview gate formats)
    g = gate or validation_result.get("acceptance_gate") or {}
    if isinstance(g, dict) and g:
        status = str(g.get("status") or "").lower()
        acceptable = g.get("acceptable")
        if status:
            reasons = list(g.get("reasons") or [])
            if status == "pass":
                st.success("✅ Gate: toegestaan om vast te stellen")
            elif status == "override_required":
                st.warning("⚠️ Gate: override vereist (reden verplicht)")
                if reasons:
                    with st.expander("Reden(en)", expanded=False):
                        for r in reasons:
                            st.write(f"- {r}")
            else:
                st.error("🚫 Gate: blokkade — voldoet niet aan criteria")
                if reasons:
                    with st.expander("Reden(en)", expanded=False):
                        for r in reasons:
                            st.write(f"- {r}")
        elif acceptable is not None:
            gates_failed = list(g.get("gates_failed") or [])
            gates_passed = list(g.get("gates_passed") or [])
            if bool(acceptable):
                msg = "Gates: OK"
                if gates_passed:
                    msg += f" · {', '.join(map(str, gates_passed))}"
                st.success(msg)
            else:
                reason = ", ".join(map(str, gates_failed)) if gates_failed else "niet voldaan"
                st.error(f"Gates: NIET OK · {reason}")

    # Toggle + details
    details_key = f"{key_prefix}_show_validation_details"
    if show_toggle:
        if st.button("📊 Toon/verberg gedetailleerde toetsresultaten", key=f"btn_{details_key}"):
            current_state = SessionStateManager.get_value(details_key, False)
            SessionStateManager.set_value(details_key, not current_state)

    show_details = SessionStateManager.get_value(details_key, False) if show_toggle else True
    if not show_details:
        return

    # Build detailed assessment and render with inline rule explanations
    lines = _build_detailed_assessment(validation_result)
    if not lines:
        st.warning("⚠️ Geen gedetailleerde toetsresultaten beschikbaar.")
        return

    for line in lines:
        # Color per status
        if line.startswith("✅"):
            st.success(line)
        elif "❌" in line and not line.startswith("📊"):
            st.error(line)
        elif "⚠️" in line or line.startswith("📊"):
            st.warning(line) if not line.startswith("📊") else st.info(line)
        else:
            st.info(line)

        # Inline explanation per rule (skip pure summary lines)
        rid = _extract_rule_id_from_line(line)
        if rid:
            with st.expander(f"ℹ️ Toon uitleg voor {rid}", expanded=False):
                st.markdown(_build_rule_hint_markdown(rid))

