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
        import json as _json
        from pathlib import Path

        rid = (rule_id or "").replace("_", "-")
        json_path = Path("src/toetsregels/regels") / f"{rid}.json"
        if not json_path.exists():
            return "", ""
        data = _json.loads(json_path.read_text(encoding="utf-8"))
        name = str(data.get("naam") or "").strip()
        explanation = str(data.get("uitleg") or data.get("toetsvraag") or "").strip()
        return name, explanation
    except (OSError, KeyError, TypeError, ValueError):
        # DEF-246: JSON load failed, return empty
        return "", ""


def _extract_rule_id_from_line(line: str) -> str:
    """Extract rule ID (e.g., CON-01) heuristically from a line."""
    import re as _re

    try:
        m = _re.search(r"([A-Z]{2,5}(?:[-_][A-Z0-9]+)+)", str(line))
        return m.group(1) if m else ""
    except (TypeError, _re.error):
        # DEF-246: Regex extraction failed
        return ""


def _build_rule_hint_markdown(rule_id: str) -> str:
    """Build short hint explanation for a rule from its JSON definition.

    Shows:
    - What the rule checks (uitleg/toetsvraag)
    - Optional good/bad examples (first 1-2)
    - Link to the extended user guide
    """
    try:
        import json as _json
        from pathlib import Path

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
            explanation = str(
                data.get("uitleg") or data.get("toetsvraag") or ""
            ).strip()
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
            "\nMeer uitleg: [Validatieregels (CON-01 e.a.)](docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
        )
        return "\n".join(lines)
    except (OSError, KeyError, TypeError, ValueError):
        # DEF-246: Rule hint generation failed
        return (
            "Meer uitleg: [Validatieregels (CON-01 e.a.)]"
            "(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
        )


def _calculate_validation_stats(violations: list, passed_rules: list) -> dict:
    failed_ids = sorted(
        {
            str(v.get("rule_id") or v.get("code") or "")
            for v in violations
            if isinstance(v, dict)
        }
    )
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


#: Regelstatussen in vaste weergavevolgorde (DEF-743, besluit 3): eerst de
#: werkelijk uitgevoerde oordelen, dan wat open, mislukt of niet gedraaid is.
_DEKKING_VOLGORDE: tuple[tuple[str, str], ...] = (
    ("pass", "✅ {n} voldoet"),
    ("fail", "❌ {n} voldoet niet"),
    ("review_required", "🟠 {n} nog te beoordelen"),
    ("error", "⚙️ {n} technisch probleem"),
    ("not_evaluated", "⏸️ {n} niet beoordeeld"),
    # DEF-766: een afgeronde niet-toepasselijkheid (ESS-03) — geen pass, geen
    # open punt; alleen getoond wanneer zij voorkomt.
    ("not_applicable", "➖ {n} niet van toepassing"),
)


def bereken_beoordelingsdekking(
    validation_result: dict[str, Any],
) -> dict[str, int] | None:
    """Telling per regelstatus: wat is werkelijk beoordeeld en wat niet.

    DEF-743 (besluit 3, 15-09-2026): de app toont geen totaalcijfer en geen
    vervangende deelscore, wél welke controles daadwerkelijk zijn uitgevoerd
    en welke nog niet beoordeeld zijn. Bron in volgorde van betrouwbaarheid:
    ``evaluation_coverage`` (DEF-624), anders ``rule_statuses``, anders — voor
    een oud resultaat zonder statussen — alleen de pass/fail-lijsten. Een
    ontbrekende beoordeling wordt nooit als pass of als nul ingevuld; is er
    niets te tellen, dan is de dekking onbekend (None).
    """
    dekking = validation_result.get("evaluation_coverage")
    if isinstance(dekking, dict) and isinstance(dekking.get("total"), int):
        telling = {
            "pass": int(dekking.get("passed") or 0),
            "fail": int(dekking.get("failed") or 0),
            "review_required": int(dekking.get("review_required") or 0),
            "error": int(dekking.get("error") or 0),
            "not_evaluated": int(dekking.get("not_evaluated") or 0),
            # 2.1.0-veld; een ouder resultaat zonder telling heeft er nul.
            "not_applicable": int(dekking.get("not_applicable") or 0),
        }
        return {"total": int(dekking["total"]), **telling}

    statussen = validation_result.get("rule_statuses")
    if isinstance(statussen, dict) and statussen:
        telling = {status: 0 for status, _ in _DEKKING_VOLGORDE}
        for status in statussen.values():
            sleutel = str(status)
            telling[sleutel] = telling.get(sleutel, 0) + 1
        return {"total": len(statussen), **telling}

    stats = _calculate_validation_stats(
        list(validation_result.get("violations") or []),
        list(validation_result.get("passed_rules") or []),
    )
    if not stats["total"]:
        return None
    return {
        "total": stats["total"],
        "pass": stats["passed_count"],
        "fail": stats["failed_count"],
        "review_required": 0,
        "error": 0,
        "not_evaluated": 0,
        "not_applicable": 0,
    }


def dekkingsregel(dekking: dict[str, int] | None) -> str:
    """De dekkingsregel voor de UI, zonder percentage of cijfer.

    Een percentage of 'x/y geslaagd' is een vervangende deelscore en kan
    bij lagere dekking een hogere kwaliteit suggereren; daarom alleen de
    absolute tellingen per status.
    """
    if not dekking:
        return (
            "📋 **Beoordelingsdekking**: onbekend — het resultaat bevat geen "
            "regelstatussen."
        )
    delen = [
        sjabloon.format(n=dekking.get(status, 0))
        for status, sjabloon in _DEKKING_VOLGORDE
        if dekking.get(status, 0) or status in ("pass", "fail")
    ]
    return f"📋 **Beoordelingsdekking**: {dekking['total']} regels · " + " · ".join(
        delen
    )


def _statuslijst_regels(
    validation_result: dict[str, Any], *, uitgesloten: set[str]
) -> list[str]:
    """Regels die open, mislukt of niet gedraaid zijn — als eigen lijnen.

    Zij staan noch bij de violations noch bij de geslaagde regels en zouden
    anders onzichtbaar blijven; een regel met gestructureerde uitkomst
    (``rule_results``) wordt apart in detail getoond en hier overgeslagen.
    """
    statussen = validation_result.get("rule_statuses")
    if not isinstance(statussen, dict):
        return []
    lijnen: list[str] = []
    for status, label in (
        ("review_required", "🟠 Nog te beoordelen"),
        ("error", "⚙️ Technisch probleem"),
        ("not_evaluated", "⏸️ Niet beoordeeld"),
        ("not_applicable", "➖ Niet van toepassing"),
    ):
        codes = sorted(
            (str(code) for code, s in statussen.items() if str(s) == status),
            key=_rule_sort_key,
        )
        codes = [c for c in codes if c not in uitgesloten]
        if codes:
            lijnen.append(f"{label}: {', '.join(codes)}")
    return lijnen


def _build_detailed_assessment(validation_result: dict) -> list[str]:
    """Build a mixed list of summary, violations and passed rules lines."""
    violations = list(validation_result.get("violations") or [])
    passed_rules = list(validation_result.get("passed_rules") or [])
    stats = _calculate_validation_stats(violations, passed_rules)

    def _severity_emoji(sev: str) -> str:
        s = (sev or "").lower()
        if s in {"critical", "error", "high"}:
            return "❌"
        if s in {"warning", "medium", "low"}:
            return "⚠️"
        return "📋"

    lines: list[str] = []
    # Summary first: de dekking, geen 'x/y geslaagd (z%)' (DEF-743, besluit 3).
    lines.append(dekkingsregel(bereken_beoordelingsdekking(validation_result)))

    # Violations (sorted)
    def _v_key(v: dict[str, Any]) -> tuple[int, int]:
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
        expl_labeled = (
            f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
        )
        lines.append(
            f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}"
        )

    # Passed rules (sorted)
    for rid in sorted(stats["passed_ids"], key=_rule_sort_key):
        name, explanation = _get_rule_info(rid)
        name_part = f" — {name}" if name else ""
        wat_toetst = f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
        lines.append(f"✅ {rid}{name_part}: OK · {wat_toetst}")

    return lines


#: Nederlandse uitkomstlabels (B-06/B-08). Een technische fout is bewust een
#: eigen label: hij is geen 'Voldoet niet'.
_UITKOMSTLABEL: dict[str, str] = {
    "pass": "✅ Voldoet",
    "fail": "❌ Voldoet niet",
    "review_required": "🟠 Nog te beoordelen",
    "error": "⚙️ Technisch probleem",
    "not_evaluated": "⏸️ Niet beoordeeld",
    # DEF-766: afgeronde niet-toepasselijkheid (ESS-03) — geen 'Voldoet'.
    "not_applicable": "➖ Niet van toepassing",
}


#: Herkomst van een deeloordeel (DEF-743/DEF-766): het `field` van een
#: onderdeel zegt wáár het oordeel vandaan komt. Een AI-oordeel is herkenbaar
#: als AI; een deskundige uitzondering is herkenbaar als uitzondering, nooit
#: als gewone pass.
_HERKOMSTLABEL: dict[str, str] = {
    "source_assessment": "AI-beoordeling",
    "ess03_assessment": "AI-beoordeling",
    "source_review": "deskundige uitzondering",
}

#: Onderdeelnamen van CON-02 (voor de correctieweergave).
_ONDERDEELLABEL: dict[str, str] = {
    "source_authority": "brongezag/toepasselijkheid",
    "semantic_support": "betekenissteun",
    "reference_quality": "verwijskwaliteit",
}

#: Labels voor een geaccepteerde uitzondering (`review.accepted_exception`).
_UITZONDERINGSLABEL: dict[str, str] = {
    "reference": "verwijzingsuitzondering (bron zonder bruikbare hyperlink)",
    "no_source": "uitzondering wegens onderbouwd ontbreken van een passende bron",
}


def _als_dict(waarde: Any) -> dict[str, Any]:
    """Typegetrouwe vernauwing: een dict, anders een lege dict."""
    return waarde if isinstance(waarde, dict) else {}


def _correctieregel(review: dict[str, Any], correctie: dict[str, Any]) -> str:
    """DEF-743 C §6b: correctie van één AI-onderdeel — geen uitzondering en
    geen globale pass; het oorspronkelijke AI-oordeel blijft zichtbaar."""
    origineel = _als_dict(correctie.get("original"))
    onderdeel = _ONDERDEELLABEL.get(
        str(correctie.get("part_id")), str(correctie.get("part_id"))
    )
    return (
        f"🧑‍⚖️ Deskundige correctie van {onderdeel} door "
        f"{correctie.get('actor') or review.get('actor') or 'onbekend'}: "
        f"{_UITKOMSTLABEL.get(str(correctie.get('status')), str(correctie.get('status')))}"
        f" (bewijsclaims: {len(correctie.get('evidence') or [])}). "
        f"Oorspronkelijk AI-oordeel: "
        f"{_UITKOMSTLABEL.get(str(origineel.get('status')), str(origineel.get('status')))}"
        + (f" — {origineel.get('reason')}" if origineel.get("reason") else "")
        + ". Dit is een correctie van één onderdeel, geen uitzondering en geen "
        "algemene beoordeling."
    )


def _beoordelingsnaam(beoordeling: dict[str, Any]) -> str:
    """'AI-bronbeoordeling' (CON-02) of 'AI-beoordeling' (ESS-03, DEF-766).

    Een ESS-03-samenvatting draagt een `verdict`-sleutel (ook als die None
    is); de CON-02-samenvatting niet. Zo blijven de bestaande CON-02-teksten
    ongewijzigd en heet de telbaarheidsbeoordeling niet ten onrechte 'bron'.
    """
    return "AI-beoordeling" if "verdict" in beoordeling else "AI-bronbeoordeling"


def _beoordelingsstatusregel(
    status: str, beoordeling: dict[str, Any], attributie: str
) -> str | None:
    """Een niet-uitgevoerde AI-beoordeling: technisch mislukt, geen bronnen,
    geen dienst. None als de status daar niet over gaat."""
    naam = _beoordelingsnaam(beoordeling)
    if status == "error":
        return (
            f"⚙️ {naam} technisch mislukt"
            f"{attributie}: {beoordeling.get('reason') or 'geen details'}"
        )
    if status == "no_sources":
        return "ℹ️ Geen bronnen aangeleverd: geen AI-bronbeoordeling uitgevoerd."
    if status == "unavailable":
        return (
            "⚙️ Geen beoordelingsdienst beschikbaar: "
            f"{beoordeling.get('reason') or f'{naam} niet uitgevoerd'}"
        )
    return None


def _beoordelingsregel(beoordeling: dict[str, Any]) -> str | None:
    """Het `assessment`-blok: status van de AI-beoordeling, of en waarom die
    niet is toegepast (stale/historisch, technische fout) en de attributie."""
    status = str(beoordeling.get("status") or "")
    naam = _beoordelingsnaam(beoordeling)
    model = beoordeling.get("model")
    provider = beoordeling.get("provider")
    attributie = f" ({provider or 'onbekende provider'} · {model})" if model else ""
    statusregel = _beoordelingsstatusregel(status, beoordeling, attributie)
    if statusregel is not None:
        return statusregel
    if beoordeling.get("applied") is False and status == "assessed":
        return (
            f"⏳ {naam} is verouderd/historisch en niet toegepast: "
            f"{beoordeling.get('reason') or 'hoort niet bij deze tekst, context of bronset'}"
        )
    if beoordeling.get("applied") is False:
        return (
            f"ℹ️ {naam} niet uitgevoerd: "
            f"{beoordeling.get('reason') or 'geen beoordeling beschikbaar'}"
        )
    if beoordeling.get("applied"):
        afgewezen = beoordeling.get("rejected") or 0
        return f"🤖 {naam} toegepast{attributie}" + (
            f"; {afgewezen} modelclaim(s) afgewezen (onbewezen of verzonnen)"
            if afgewezen
            else ""
        )
    return None


def _review_regels(review: dict[str, Any]) -> list[str]:
    """Leesbare regels over de review-/beoordelingssamenvatting van een regel.

    CON-01 kent alleen `applied`/`reason`; CON-02 (DEF-743) draagt daarnaast
    `accepted_exception`, `type`, `actor` en een `assessment`-blok (status van
    de AI-beoordeling, of en waarom die niet is toegepast — stale/historisch,
    technische fout — en de attributie). Alles wat niet telt wordt benoemd,
    nooit stil weggelaten.
    """
    regels: list[str] = []
    uitzondering = review.get("accepted_exception")
    correctie = review.get("applied_correction")
    if isinstance(correctie, dict) and correctie:
        regels.append(_correctieregel(review, correctie))
    if uitzondering:
        label = _UITZONDERINGSLABEL.get(str(uitzondering), str(uitzondering))
        actor = review.get("actor") or "onbekend"
        regels.append(
            f"🧑‍⚖️ Geaccepteerde deskundige {label} — vastgelegd door {actor}. "
            "Dit is een uitzondering, geen positieve bronbeoordeling."
        )
    elif (
        review.get("applied") is False
        and review.get("reason")
        and (review.get("actor") or review.get("type") or review.get("fingerprint"))
    ):
        # Alleen een wérkelijk aangeleverde beoordeling kan 'niet toegepast' zijn;
        # zonder beoordeling is er niets te melden.
        regels.append(
            f"⏳ Eerdere deskundige beoordeling niet toegepast: {review['reason']}"
        )
    elif review.get("applied") and review.get("reason"):
        regels.append(f"Beoordeling: {review['reason']}")
    elif review.get("reason") and "accepted_exception" not in review:
        # CON-01-vorm: alleen applied/reason.
        regels.append(f"Beoordeling: {review['reason']}")

    beoordeling = review.get("assessment")
    if isinstance(beoordeling, dict):
        beoordelingsregel = _beoordelingsregel(beoordeling)
        if beoordelingsregel is not None:
            regels.append(beoordelingsregel)
    return regels


def render_rule_results(rule_results: dict[str, Any]) -> None:
    """Toon de uitkomsten van regels zonder cijfer (DEF-622 CON-01, DEF-743 CON-02).

    Per regel de samengestelde uitkomst, per onderdeel de aanleiding
    (gevonden tekst of geverifieerd citaat), de herkomst (AI of deskundige),
    de reden en de vervolgstap (B-08). Een geslaagd onderdeel wordt kort
    genoemd; een falend, open of mislukt onderdeel krijgt zijn volledige
    uitleg. Een geaccepteerde uitzondering en een niet-toegepaste
    (stale/historische) beoordeling worden expliciet benoemd.
    """
    for code, detail in sorted(rule_results.items()):
        if not isinstance(detail, dict):
            continue
        status = str(detail.get("status") or "")
        inhoudelijk = _inhoudelijk_label(detail)
        label = inhoudelijk or _UITKOMSTLABEL.get(status, status or "onbekend")
        st.markdown(f"**{code}** · {label} — zonder cijfer (uitkomst met motivering)")
        for part in detail.get("parts") or []:
            if isinstance(part, dict):
                _render_deeluitkomst(part, label_override=inhoudelijk)
        review = detail.get("review")
        if isinstance(review, dict):
            for regel in _review_regels(review):
                st.markdown(f"_{regel}_")
        if inhoudelijk == _LABEL_ONVOLDOENDE_INFORMATIE:
            st.caption(_HULP_ONVOLDOENDE_INFORMATIE)


#: DEF-766 (R9): een uitgevoerde AI-uitkomst 'onvoldoende informatie' is een
#: inhoudelijke uitkomst met precies één vraag — geen generiek open punt.
_LABEL_ONVOLDOENDE_INFORMATIE = "❓ Onvoldoende informatie"

#: DEF-820 (K2): een verwijzende formulering zonder aangeleverde afspraak
#: levert vrijwel altijd deze vraag op. De gebruiker hoort te weten dat de
#: conventie aanleveren de weg is, niet de tekst herschrijven om de vraag te
#: ontwijken. Staat naast de vervolgstap en herhaalt die niet.
_HULP_ONVOLDOENDE_INFORMATIE = (
    "Verwijst de definitie naar een register, een code of een conventie die niet "
    "is aangeleverd, dan vraagt de beoordeling daar meestal naar. Lever die "
    "conventie of de bronpassage aan; de definitie herschrijven om de vraag te "
    "ontlopen neemt de onduidelijkheid niet weg."
)


def _inhoudelijk_label(detail: dict[str, Any]) -> str | None:
    """Het inhoudelijke label van een toegepaste AI-uitkomst die technisch een
    open status draagt (`review_required`): 'Onvoldoende informatie'. None
    voor alle andere gevallen — dan geldt het statuslabel (een niet-toegepaste,
    historische of niet-beschikbare beoordeling blijft 'Nog te beoordelen')."""
    beoordeling = _als_dict(_als_dict(detail.get("review")).get("assessment"))
    if (
        detail.get("status") == "review_required"
        and beoordeling.get("applied") is True
        and beoordeling.get("verdict") == "insufficient_information"
    ):
        return _LABEL_ONVOLDOENDE_INFORMATIE
    return None


def _render_deeluitkomst(
    part: dict[str, Any], *, label_override: str | None = None
) -> None:
    """Eén onderdeel: kop (label + herkomst + aanleiding + positie), reden en vervolgstap."""
    deelstatus = str(part.get("status") or "")
    kop = _UITKOMSTLABEL.get(deelstatus, deelstatus)
    if label_override and deelstatus == "review_required":
        kop = label_override
    herkomst = _HERKOMSTLABEL.get(str(part.get("field") or ""))
    if herkomst:
        kop += f" · {herkomst}"
    onderdeel = part.get("id")
    if onderdeel and str(onderdeel).startswith("expert_exception"):
        kop += " · uitzondering"
    aanleiding = part.get("evidence")
    if aanleiding:
        kop += f" · aanleiding: '{aanleiding}'"
        positie = part.get("position")
        if isinstance(positie, int):
            kop += f" (positie {positie})"
    reden = str(part.get("reason") or "")
    if deelstatus == "pass":
        st.success(f"{kop} — {reden}")
        return
    tekst = f"{kop}\n\n{reden}\n\n**Vervolgstap:** {part.get('action') or ''}"
    # Een technische fout en een open onderdeel zijn geen 'Voldoet niet'
    # (B-06/B-08): waarschuwing, geen fout. Een afgeronde niet-toepasselijkheid
    # (DEF-766) is noch een gebrek noch een open punt: informatief.
    if deelstatus == "fail":
        st.error(tekst)
    elif deelstatus == "not_applicable":
        st.info(tekst)
    else:
        st.warning(tekst)


def _onbekend_melding(validation_result: dict[str, Any], reden: str | None) -> str:
    """De melding bij een niet-uitgevoerde run, met de reden die klopt (DEF-624).

    Een ontbrekende of ongeldige status is géén incomplete regelset: die
    oorzaak bij de regelset leggen zou de gebruiker naar de verkeerde plek
    sturen. Alleen `ruleset_incomplete` draagt een gemeten telling; bij een
    ontbrekend contract is er niets gemeten en wordt er niets verzonnen.
    De telling is een extraatje, geen voorwaarde: de guard mag nooit klappen
    op de vorm van het readiness-object. Een exceptie hier zou in de Edit-tab
    stil worden weggeslikt en de hele Kwaliteitstoetsing laten verdwijnen.
    """
    from services.validation.interfaces import (
        UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
        UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
        UNKNOWN_REASON_RULESET_INCOMPLETE,
        UNKNOWN_REASON_VALIDATION_ERROR,
    )

    slot = "Er is niets getoetst; de definitie is niet afgekeurd."
    if reden == UNKNOWN_REASON_CONTRACT_STATUS_MISSING:
        return (
            "⚠️ Validatie niet te bepalen: het resultaat draagt geen runbewijs "
            "(validation_status ontbreekt). Er is geen uitgevoerde toetsing "
            "vastgelegd; de definitie is niet afgekeurd."
        )
    if reden == UNKNOWN_REASON_CONTRACT_STATUS_INVALID:
        return (
            "⚠️ Validatie niet te bepalen: het resultaat draagt geen geldig "
            "runbewijs (validation_status is ongeldig). Er is geen uitgevoerde "
            "toetsing vastgelegd; de definitie is niet afgekeurd."
        )
    if reden == UNKNOWN_REASON_VALIDATION_ERROR:
        systeem = validation_result.get("system")
        fout = systeem.get("error") if isinstance(systeem, dict) else None
        detail = f": {fout}" if fout else ""
        return f"⚠️ Validatie niet te bepalen: de toetsing is technisch mislukt{detail}. {slot}"

    readiness = validation_result.get("validation_readiness")
    if not isinstance(readiness, dict):
        readiness = {}
    geladen = readiness.get("loaded_total")
    verwacht = readiness.get("expected_total")
    telling = (
        f" ({geladen} van {verwacht})"
        if isinstance(geladen, int) and isinstance(verwacht, int)
        else ""
    )
    if reden == UNKNOWN_REASON_RULESET_INCOMPLETE or telling:
        return (
            f"⚠️ Validatie niet te bepalen: niet alle toetsregels konden "
            f"worden geladen{telling}. {slot}"
        )
    return f"⚠️ Validatie niet te bepalen: de toetsing leverde geen oordeel. {slot}"


def _historische_bevindingen(validation_result: dict[str, Any]) -> list[str]:
    """Wat een resultaat zonder runbewijs nog aan bevindingen draagt, neutraal.

    Beschikbaar voor uitleg (DEF-624), niet als actuele geldige verklaring:
    geen ✅/❌, geen gate, geen telling - alleen de tekst per bevinding.
    """
    regels: list[str] = []
    for v in validation_result.get("violations") or []:
        if not isinstance(v, dict):
            continue
        rid = str(v.get("rule_id") or v.get("code") or "?")
        tekst = str(v.get("description") or v.get("message") or "")
        regels.append(f"{rid}: {tekst}".rstrip(": "))
    for code, detail in sorted((validation_result.get("rule_results") or {}).items()):
        if isinstance(detail, dict) and detail.get("status"):
            regels.append(
                f"{code}: {_UITKOMSTLABEL.get(str(detail['status']), str(detail['status']))}"
            )
    return regels


def _render_historische_bevindingen(validation_result: dict[str, Any]) -> None:
    """Eerder vastgelegde bevindingen tonen zonder ze als oordeel te presenteren."""
    regels = _historische_bevindingen(validation_result)
    if not regels:
        return
    with st.expander(
        f"Eerder vastgelegde bevindingen ({len(regels)}) — geen actuele toetsing",
        expanded=False,
    ):
        st.text(
            "Deze bevindingen horen bij een resultaat zonder geldig runbewijs en "
            "gelden niet als actuele toetsing."
        )
        for regel in regels:
            st.text(f"- {regel}")


def render_v2_validation_details(validation_result: dict[str, Any]) -> None:
    """Render V2 validation details consistently for all tabs."""
    # Backwards-compatible simple renderer delegates to the unified detailed list without toggle.
    render_validation_detailed_list(
        validation_result, key_prefix="v2_default", show_toggle=False
    )


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
    # DEF-621/DEF-624: fail-closed stop vóór elk oordeel. Dit is het enige
    # renderpad van alle drie de tabs; loopt hij door zonder uitgevoerde run,
    # dan verschijnt een oordeel terwijl er juist niets (betrouwbaar) is
    # geëvalueerd - en een meegegeven gate uit een review- of previewscherm
    # zou daar groen bovenop komen. De score, de gate, de toggle en beide
    # detailhelpers blijven daarom onbereikt. Sinds DEF-624 stopt de guard
    # niet alleen bij een expliciete `validation_unknown` maar bij elk
    # resultaat zonder geldige status: dat is geen runbewijs.
    #
    # De import staat bewust hier en niet op modulniveau: `services` trekt bij
    # het laden het hele servicepakket mee (container, numpy, httpx), en dan
    # zou het enkel importeren van deze viewmodule een halve applicatie
    # starten. Dit bestand hanteert die lazy UI-laaggrens al voor
    # `SessionStateManager`.
    from services.validation.interfaces import (
        UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
        UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    )
    from services.validation.result_contract import bepaal_runstatus

    runstatus = bepaal_runstatus(validation_result)
    if not runstatus.uitgevoerd:
        st.warning(_onbekend_melding(validation_result, runstatus.reason))
        # Alleen bij een ontbrekend contract dragen de aanwezige bevindingen
        # iets van een eerder resultaat; bij ruleset_incomplete is er niets
        # getoetst en bij een servicefout is de violation de fout zelf.
        if runstatus.reason in (
            UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
            UNKNOWN_REASON_CONTRACT_STATUS_INVALID,
        ):
            _render_historische_bevindingen(validation_result)
        return

    from ui.session_state import SessionStateManager

    # DEF-743 (besluit 3, 15-09-2026): geen totaalcijfer en geen vervangende
    # deelscore — ook niet uit een oud resultaat dat nog een getal draagt.
    # `overall_score` wordt bewust niet gelezen: een oud opgeslagen cijfer is
    # geen actuele kwaliteit. Wat wél telt: de regeloordelen hieronder en de
    # werkelijke beoordelingsdekking (wat is uitgevoerd, wat niet).
    st.markdown(
        "**Totaalscore:** niet beschikbaar — de app toont per regel het "
        "oordeel en de beoordelingsdekking, geen cijfer (DEF-743)."
    )
    dekking = bereken_beoordelingsdekking(validation_result)
    st.markdown(dekkingsregel(dekking))

    # Gate indicator (supports both acceptance_gate and review/preview gate formats)
    g = gate or validation_result.get("acceptance_gate") or {}
    if isinstance(g, dict) and g:
        status = str(g.get("status") or "").lower()
        acceptable = g.get("acceptable")
        # DEF-674: het totaalresultaat is leidend. De service houdt beide velden
        # gelijk, maar deze weergave krijgt ook een los `gate`-argument mee uit
        # review- en preview-schermen, en die kan van een oudere meting komen.
        # Groen tonen terwijl het resultaat is afgekeurd is de ene fout die hier
        # niet gemaakt mag worden, dus dat wordt hier hoe dan ook geblokkeerd.
        eindoordeel = validation_result.get("is_acceptable")
        if eindoordeel is not True and eindoordeel is not None:
            if status == "pass":
                status = "blocked"
            acceptable = False
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
                reason = (
                    ", ".join(map(str, gates_failed))
                    if gates_failed
                    else "niet voldaan"
                )
                st.error(f"Gates: NIET OK · {reason}")

    # DEF-622: uitkomsten van regels zonder cijfer (CON-01) altijd tonen —
    # niet achter de toggle, want zonder totaalscore zijn dit dé uitkomsten.
    render_rule_results(validation_result.get("rule_results") or {})

    # DEF-746/DEF-750/DEF-767: de open reden van ESS-01, ESS-02 en ESS-04 is
    # ook bij ingeklapte details zichtbaar — voor ESS-04 altijd de open
    # status plus de reviewvraag (passagevraag of toetsvraag), ook zonder
    # treffer. Passages zijn gebruikersinvoer: toon ze letterlijk, niet als
    # Markdown of HTML. Dit is de leesbare signaalweergave (A); de menselijke
    # beoordeling zelf en haar opslag volgen in C/D (DEF-624/626/627). ESS-03
    # staat hier sinds DEF-766 niet meer bij: zijn uitkomst (vier oordelen,
    # vraag, fout) komt gestructureerd uit `rule_results` hierboven en zou
    # hier dubbel verschijnen.
    for review_item in validation_result.get("review_required") or []:
        if not isinstance(review_item, dict):
            continue
        rule_id = review_item.get("rule_id")
        if rule_id in ("ESS-01", "ESS-02", "ESS-04"):
            st.text(str(review_item.get("reason") or f"{rule_id} — Nog te beoordelen"))

    # Toggle + details
    details_key = f"{key_prefix}_show_validation_details"
    if show_toggle and st.button(
        "📊 Toon/verberg gedetailleerde toetsresultaten", key=f"btn_{details_key}"
    ):
        current_state = SessionStateManager.get_value(details_key, False)
        SessionStateManager.set_value(details_key, not current_state)

    # Default to expanded on first render after validation
    if show_toggle and SessionStateManager.get_value(details_key, None) is None:
        SessionStateManager.set_value(details_key, True)

    show_details = (
        SessionStateManager.get_value(details_key, False) if show_toggle else True
    )
    if not show_details:
        return

    # Summary (blue info bar) + detailed assessment. De samenvatting is de
    # dekking (tellingen per status), geen 'x/y geslaagd (z%)' — een
    # percentage is een vervangende deelscore (DEF-743, besluit 3). De stats
    # blijven de bron van de gefaalde/geslaagde regelcodes hieronder.
    _calculate_validation_stats(
        list(validation_result.get("violations") or []),
        list(validation_result.get("passed_rules") or []),
    )
    st.info(dekkingsregel(dekking))

    lines = _build_detailed_assessment(validation_result)
    # Filter out the summary line if present (we render a styled summary above)
    lines = [ln for ln in lines if not ln.startswith("📋 **Beoordelingsdekking**")]
    # Regels die open, mislukt of niet gedraaid zijn horen zichtbaar te
    # blijven; regels met gestructureerde uitkomst staan al hierboven.
    lines.extend(
        _statuslijst_regels(
            validation_result,
            uitgesloten={
                str(code)
                for code, detail in (
                    validation_result.get("rule_results") or {}
                ).items()
                if isinstance(detail, dict)
            },
        )
    )
    if not lines:
        st.warning("⚠️ Geen gedetailleerde toetsresultaten beschikbaar.")
        return

    for line in lines:
        # Statuslijsten (open/mislukt/niet gedraaid): informatief, geen
        # uitleg-expander per regel (het is een opsomming van codes).
        if line.startswith(("🟠 Nog te beoordelen:", "⚙️ Technisch probleem:", "⏸️ ")):
            st.info(line)
            continue
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
