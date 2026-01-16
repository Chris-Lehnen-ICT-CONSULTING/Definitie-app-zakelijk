"""
Validation results renderer for definition generator tab.

Extracted from definition_generator_tab.py as part of DEF-266 Phase 4 refactoring.
Handles all validation result display including violations, passed rules, and summaries.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import streamlit as st

from ui.session_state import SessionStateManager
from utils.type_helpers import ensure_string

logger = logging.getLogger(__name__)


class ValidationRenderer:
    """Renderer voor validation resultaten in de definitie generator."""

    def render_validation_results(self, validation_result: dict[str, Any]) -> None:
        """Render validation resultaten via gedeelde renderer (V2 dict)."""
        st.markdown("#### ✅ Kwaliteitstoetsing")
        try:
            from ui.components.validation_view import render_validation_detailed_list

            render_validation_detailed_list(
                validation_result,
                key_prefix="gen",
                show_toggle=True,
                gate=(
                    validation_result.get("acceptance_gate")
                    if isinstance(validation_result, dict)
                    else None
                ),
            )
        except Exception as e:
            st.error(f"Validatiesectie kon niet worden gerenderd: {e!s}")

    def build_detailed_assessment(self, validation_result: dict) -> list[str]:
        """Build detailed assessment from validation result."""
        try:
            violations = validation_result.get("violations", []) or []
            passed_rules = validation_result.get("passed_rules", []) or []

            # Calculate statistics
            stats = self._calculate_validation_stats(violations, passed_rules)

            lines = []
            # Add summary line
            lines.append(self._format_validation_summary(stats))

            # Add violation lines
            lines.extend(self._format_violations(violations))

            # Add passed rules
            lines.extend(self._format_passed_rules(stats["passed_ids"]))

            return lines
        except Exception as e:
            logger.debug(f"Kon beoordeling_gen niet afleiden uit V2-resultaat: {e}")
            return []

    def _calculate_validation_stats(
        self, violations: list, passed_rules: list
    ) -> dict[str, Any]:
        """Calculate validation statistics."""
        failed_ids = sorted(
            {
                str(v.get("rule_id") or v.get("code") or "")
                for v in violations
                if isinstance(v, dict)
            }
        )
        passed_ids = sorted({str(r) for r in passed_rules})
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

    def _format_validation_summary(self, stats: dict) -> str:
        """Format validation summary line."""
        summary = f"📊 **Toetsing Samenvatting**: {stats['passed_count']}/{stats['total']} regels geslaagd ({stats['percentage']:.1f}%)"
        if stats["failed_count"] > 0:
            summary += f" | ❌ {stats['failed_count']} gefaald"
        return summary

    def _format_violations(self, violations: list) -> list[str]:
        """Format violation lines with severity-based sorting and emojis."""
        lines = []

        def _v_key(v):
            rid = str(v.get("rule_id") or v.get("code") or "")
            return self._rule_sort_key(rid)

        for v in sorted(violations, key=_v_key):
            rid = str(v.get("rule_id") or v.get("code") or "")
            sev = str(v.get("severity", "warning")).lower()
            desc = v.get("description") or v.get("message") or ""
            suggestion = v.get("suggestion")
            if suggestion:
                desc = f"{desc} · Wat verbeteren: {suggestion}"
            emoji = self._get_severity_emoji(sev)
            name, explanation = self._get_rule_display_and_explanation(rid)
            name_part = f" — {name}" if name else ""
            expl_labeled = (
                f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
            )
            lines.append(
                f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}"
            )

        return lines

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        if severity in {"critical", "error", "high"}:
            return "❌"
        if severity in {"warning", "medium", "low"}:
            return "⚠️"
        return "📋"

    def _format_passed_rules(self, passed_ids: list[str]) -> list[str]:
        """Format passed rule lines, inclusief 'Wat toetst' en 'Waarom'."""
        lines_out: list[str] = []
        text, begrip = self._get_current_text_and_begrip()
        for rid in sorted(passed_ids, key=self._rule_sort_key):
            name, explanation = self._get_rule_display_and_explanation(rid)
            name_part = f" — {name}" if name else ""
            wat_toetst = (
                f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
            )
            reason = self._build_pass_reason(rid, text, begrip)
            waarom = f" · Waarom geslaagd: {reason}" if reason else ""
            lines_out.append(f"✅ {rid}{name_part}: OK · {wat_toetst}{waarom}")
        return lines_out

    def _rule_sort_key(self, rule_id: str) -> tuple[int, int, str]:
        """Groeperings- en sorteersleutel voor regelcodes.

        Volgorde van groepen: CON → ESS → STR → INT → SAM → ARAI → VER → VAL → overige.
        Binnen een groep sorteren we op nummer indien aanwezig (01, 02, ...),
        daarna op volledige code voor stabiele weergave.
        """
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
        # Probeer een numeriek onderdeel na de eerste '-' te parsen
        num = 9999
        try:
            tail = rid.split("-", 1)[1] if "-" in rid else ""
            m = re.search(r"(\d+)", tail)
            if m:
                num = int(m.group(1))
        except Exception:
            num = 9999
        return (grp, num, rid)

    def _build_rule_hint_markdown(self, rule_id: str) -> str:
        """Bouw korte hint-uitleg voor een toetsregel uit JSON en standaardtekst."""
        try:
            rules_dir = Path("src/toetsregels/regels")
            json_path = rules_dir / f"{rule_id}.json"
            if not json_path.exists():
                alt = rule_id.replace("_", "-")
                json_path = rules_dir / f"{alt}.json"

            name = explanation = ""
            good: list[str] = []
            bad: list[str] = []
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                name = str(data.get("naam") or "").strip()
                explanation = str(
                    data.get("uitleg") or data.get("toetsvraag") or ""
                ).strip()
                good = list(data.get("goede_voorbeelden") or [])
                bad = list(data.get("foute_voorbeelden") or [])

            lines = []
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
                "\nMeer uitleg: [Validatieregels (CON-01 e.a.)](docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )
            return "\n".join(lines)
        except Exception:
            return (
                "Meer uitleg: [Validatieregels (CON-01 e.a.)]"
                "(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )

    def _get_rule_display_and_explanation(self, rule_id: str) -> tuple[str, str]:
        """Haal naam/uitleg uit JSON wanneer beschikbaar; anders korte fallback."""
        # 1) Probeer JSON (best-effort)
        try:
            rules_dir = Path("src/toetsregels/regels")
            json_path = rules_dir / f"{rule_id}.json"
            if not json_path.exists():
                alt = rule_id.replace("_", "-")
                json_path = rules_dir / f"{alt}.json"
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                name = str(data.get("naam") or "").strip()
                explanation = str(
                    data.get("uitleg") or data.get("toetsvraag") or ""
                ).strip()
                if name or explanation:
                    return name, explanation
        except Exception:
            logger.debug("Failed to load rule metadata from JSON for %s", rule_id)

        # 2) Fallback mapping (kernregels)
        fallback = {
            "VAL-EMP-001": "Controleert of de definitietekst niet leeg is.",
            "VAL-LEN-001": "Minimale lengte (woorden/tekens) voor voldoende informatiedichtheid.",
            "VAL-LEN-002": "Maximale lengte om overdadigheid te voorkomen.",
            "ESS-CONT-001": "Essentiële inhoud aanwezig (niet te summier).",
            "CON-CIRC-001": "Detecteert of het begrip letterlijk in de definitie voorkomt.",
            "STR-TERM-001": "Terminologiekwesties (bijv. 'HTTP-protocol' i.p.v. 'HTTP protocol').",
            "STR-ORG-001": "Lange, komma-rijke zinnen of redundantie/tegenstrijdigheid.",
            "ESS-02": "Eenduidige ontologische marker (type/particulier/proces/resultaat).",
            "CON-01": "Context niet letterlijk benoemen; waarschuwt bij dubbele context.",
        }
        return "", fallback.get(rule_id, "Geen beschrijving beschikbaar.")

    def extract_rule_id_from_line(self, line: str) -> str:
        """Haal regelcode (bv. CON-01) heuristisch uit een weergegeven lijn."""
        try:
            m = re.search(r"([A-Z]{2,5}(?:[-_][A-Z0-9]+)+)", str(line))
            return m.group(1) if m else ""
        except Exception:
            return ""

    # ============ UI-private utilities ============
    def _get_current_text_and_begrip(self) -> tuple[str, str]:
        """Lees huidige definitietekst/begrip uit UI-state (best effort)."""
        try:
            text = ensure_string(
                SessionStateManager.get_value("current_definition_text", "")
            )
            begrip = ensure_string(SessionStateManager.get_value("current_begrip", ""))
            return text, begrip
        except Exception:
            return "", ""

    def _compute_text_metrics(self, text: str) -> dict[str, int]:
        """Kleine metrics voor pass-rationales (UI-only)."""
        t = ensure_string(text)
        words = len(t.split()) if t else 0
        chars = len(t)
        commas = t.count(",")
        return {"words": words, "chars": chars, "commas": commas}

    def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
        """Beknopte reden waarom regel geslaagd is (heuristiek, UI-only)."""
        rid = ensure_string(rule_id).upper()
        m = self._compute_text_metrics(text)
        w, c, cm = m.get("words", 0), m.get("chars", 0), m.get("commas", 0)

        try:
            if rid == "VAL-EMP-001":
                return f"Niet leeg (tekens={c} > 0)." if c > 0 else ""
            if rid == "VAL-LEN-001":
                return (
                    f"Lengte OK: {w} woorden ≥ 5 en {c} tekens ≥ 15."
                    if (w >= 5 and c >= 15)
                    else ""
                )
            if rid == "VAL-LEN-002":
                return (
                    f"Lengte OK: {w} ≤ 80 en {c} ≤ 600."
                    if (w <= 80 and c <= 600)
                    else ""
                )
            if rid == "ESS-CONT-001":
                return f"Essentie aanwezig: {w} woorden ≥ 6." if w >= 6 else ""
            if rid == "CON-CIRC-001":
                gb = ensure_string(begrip)
                if gb:
                    found = re.search(
                        rf"\b{re.escape(gb)}\b", ensure_string(text), re.IGNORECASE
                    )
                    return (
                        "Begrip niet in tekst (geen exacte match)." if not found else ""
                    )
                return "Begrip niet opgegeven."
            if rid == "STR-TERM-001":
                return (
                    "Verboden term niet aangetroffen ('HTTP protocol')."
                    if "HTTP protocol" not in ensure_string(text)
                    else ""
                )
            if rid == "STR-ORG-001":
                redund = bool(
                    re.search(
                        r"\bsimpel\b.*\bcomplex\b|\bcomplex\b.*\bsimpel\b",
                        ensure_string(text),
                        re.IGNORECASE,
                    )
                )
                return (
                    "Geen lange komma-zin (>300 tekens en ≥6 komma's) en geen redundantiepatroon."
                    if not (c > 300 and cm >= 6) and not redund
                    else ""
                )
            if rid == "ESS-02":
                return "Eenduidige ontologische marker aanwezig."
            if rid == "CON-01":
                return "Context niet letterlijk benoemd; geen duplicaat gedetecteerd."
            if rid in {"ESS-03", "ESS-04", "ESS-05"}:
                return "Vereist element herkend (heuristiek)."
        except Exception:
            return ""

        return "Geen issues gemeld door validator."
