"""
Service layer for definition edit interface functionality.

This service orchestrates the edit operations and provides
business logic for the definition edit interface.
"""

import logging
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast

from database.models import DefinitieRecord
from domain.ess03.contract import Beoordelingsbinding, Intentie
from domain.int01.opslag import niet_toepasbaar_detail, tekstvingerafdruk
from services.definition_edit_repository import DefinitionEditRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition
from services.validation.modular_validation_service import ModularValidationService

#: Sleutels uit het geladen record die de toetsing van de bewerkte kandidaat
#: mee moet krijgen (DEF-622 CON-01, DEF-743 CON-02). De bronset is die van
#: het ID-only geladen record; de bewerkte tekst/term/context komen uit de
#: editor. Een `source_assessment` reist bewust NIET mee: de actieve wrapper
#: verkrijgt zelf een beoordeling voor exact deze kandidaat (C-contract §8) en
#: negeert een meegegeven beoordeling — een UI kan zo nooit een oude positieve
#: beoordeling voor een gewijzigde tekst laten gelden.
_RECORDSLEUTELS_VOOR_TOETSING: tuple[str, ...] = (
    "context_review",
    "source_review",
    "peildatum",
)


def bouw_validatiecontext(
    definition: Definition, geladen_metadata: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Eén contextdict voor de sync- én async-toetsing van de bewerkte kandidaat.

    - De drie contextlijsten komen uit de bewerkte kandidaat en gaan altijd
      mee, ook leeg: de editor is gezaghebbend (CON-01-transport, DEF-622).
    - `record_text` = de exacte bewerkte tekst (CON-01/CON-02 binden eraan).
    - `definition_id`/`definition_version`/`context_review`/`source_review`/
      `peildatum` komen uit het geladen record; een verouderde beoordeling
      vervalt in de kern via vingerafdruk + versie, niet via UI-logica.
    - `provenance_sources` = dezelfde bronset als het geladen record (deep
      copy; `sources` als terugval voor oudere metadata). Zonder bronset
      geen sleutel: er wordt niets verzonnen.
    """
    meta: Mapping[str, Any] = geladen_metadata or {}
    ctx: dict[str, Any] = {
        "organisatorische_context": list(definition.organisatorische_context or []),
        "juridische_context": list(definition.juridische_context or []),
        "wettelijke_basis": list(definition.wettelijke_basis or []),
        "definition_id": definition.id,
        "definition_version": meta.get("version_number"),
        "record_text": definition.definitie,
    }
    for sleutel in _RECORDSLEUTELS_VOOR_TOETSING:
        ctx[sleutel] = deepcopy(meta.get(sleutel))
    bronnen = meta.get("provenance_sources")
    if bronnen is None:
        bronnen = meta.get("sources")
    if isinstance(bronnen, list):
        ctx["provenance_sources"] = deepcopy(bronnen)
    # DEF-766: de bedoelde betekenis voor ESS-03 komt uit de bewerkte kandidaat
    # (toelichting, categorie als te controleren claim) en de verduidelijking
    # van deze sessie — anders die van de opgeslagen beoordeling. Zo bindt de
    # editor-toetsing aan dezelfde intentie als de replay op het record.
    ctx["toelichting"] = definition.toelichting or None
    ctx["categorie"] = definition.categorie or None
    # R4: de DEF-751-betekenisverduidelijking van het record gaat mee, zoals
    # in het recordpad en de replay.
    betekenis = _betekenisverduidelijking_uit(meta)
    if betekenis is not None:
        ctx["betekenisverduidelijking"] = betekenis
    eigen_meta = definition.metadata or {}
    # De sessie is gezaghebbend zodra zij de sleutel draagt — ook leeg (de
    # gebruiker heeft de verduidelijking bewust gewist); anders het record.
    verduidelijking = (
        eigen_meta.get("ess03_verduidelijking")
        if "ess03_verduidelijking" in eigen_meta
        else meta.get("ess03_verduidelijking")
    )
    if isinstance(verduidelijking, str) and verduidelijking.strip():
        ctx["ess03_verduidelijking"] = verduidelijking.strip()
    return ctx


def bindingsafwijzing_beoordeling(
    assessment: Any,
    definition: Definition,
    geladen_metadata: Mapping[str, Any] | None,
) -> str | None:
    """Waarom een sessiebeoordeling níet bij de op te slaan kandidaat hoort, of None.

    DEF-809: "Valideren" levert een AI-bronbeoordeling voor exact de bewerkte
    tekst, term en drie contextlijsten met de bronset en peildatum van het
    geladen record. Zij mag alleen als actueel bewijs worden opgeslagen als zij
    is uitgevoerd (`assessed`) en haar vingerafdruk exact die van de kandidaat
    is die nú wordt opgeslagen — dezelfde kernberekening als de wrapper en de
    replay. Anders (verder bewerkt, andere context, technische fout, geen
    bronset) blijft het opgeslagen bewijs staan en wordt de reden benoemd:
    nooit een oude of vreemde beoordeling als kortere weg naar een positief oordeel.
    """
    from domain.sources.contract import bereken_bronvingerafdruk

    if not isinstance(assessment, Mapping):
        return "beoordeling is geen object"
    if assessment.get("status") != "assessed":
        return f"bronbeoordeling niet uitgevoerd (status {assessment.get('status')!r})"
    meta: Mapping[str, Any] = geladen_metadata or {}
    bronnen = meta.get("provenance_sources")
    if bronnen is None:
        bronnen = meta.get("sources")
    if not isinstance(bronnen, list):
        return "het opgeslagen record draagt geen bronset om aan te binden"
    vingerafdruk = bereken_bronvingerafdruk(
        definition.begrip or "",
        definition.definitie or "",
        {
            "organisatorische_context": list(definition.organisatorische_context or []),
            "juridische_context": list(definition.juridische_context or []),
            "wettelijke_basis": list(definition.wettelijke_basis or []),
        },
        bronnen,
        peildatum=meta.get("peildatum"),
    )
    if assessment.get("fingerprint") != vingerafdruk:
        return (
            "beoordeling hoort niet bij de op te slaan kandidaat (tekst, context, "
            "term, peildatum of bronnen zijn sinds de toetsing gewijzigd); valideer "
            "opnieuw na opslaan"
        )
    return None


def _neem_sessiebeoordeling_op(
    assessment: Mapping[str, Any] | None,
    definition: Definition,
    geladen_metadata: Mapping[str, Any] | None,
) -> tuple[bool, str | None]:
    """Zet een bindende sessiebeoordeling als actueel bewijs op de kandidaat.

    Geeft (opgenomen, reden-waarom-niet). Zonder beoordeling: (False, None).
    Bindt zij niet (`bindingsafwijzing_beoordeling`), dan blijft de metadata
    onaangeroerd en is de reden de melding voor de UI.
    """
    if assessment is None:
        return False, None
    reden = bindingsafwijzing_beoordeling(assessment, definition, geladen_metadata)
    if reden is not None:
        return False, reden
    if definition.metadata is None:
        definition.metadata = {}
    definition.metadata["source_assessment"] = deepcopy(dict(assessment))
    return True, None


#: Sentinel: "geen expliciet document meegegeven" (None is een geldige waarde).
_ONGEZET: Any = object()


def _betekenisverduidelijking_uit(meta: Mapping[str, Any]) -> str | None:
    """De DEF-751-betekenisverduidelijking van het record, uit de generatieregistratie."""
    registratie = _als_mapping(meta.get("generation_prompt_data"))
    waarde = registratie.get("betekenisverduidelijking")
    return waarde.strip() if isinstance(waarde, str) and waarde.strip() else None


def ess03_intentie_van_definition(definition: Definition) -> Intentie:
    """De bedoelde betekenis van een record voor de ESS-03-binding (DEF-766).

    Dezelfde bronnen als de validatiecontext: toelichting en categorie van het
    record, de betekenisverduidelijking uit de generatieregistratie (DEF-751)
    en de actuele ESS-03-verduidelijking uit `metadata["ess03_verduidelijking"]`
    (R5: alleen die sleutel telt; "" of afwezig = geen verduidelijking — er
    wordt nooit een verduidelijking uit een oude beoordeling hersteld).
    """
    meta: Mapping[str, Any] = definition.metadata or {}
    verduidelijking = meta.get("ess03_verduidelijking")
    return Intentie(
        toelichting=definition.toelichting or None,
        categorie=getattr(definition, "ontologische_categorie", None)
        or definition.categorie
        or None,
        betekenisverduidelijking=_betekenisverduidelijking_uit(meta),
        verduidelijking=(
            verduidelijking.strip()
            if isinstance(verduidelijking, str) and verduidelijking.strip()
            else None
        ),
    )


def _record_bronnen(meta: Mapping[str, Any]) -> list[Any]:
    bronnen = meta.get("provenance_sources")
    if bronnen is None:
        bronnen = meta.get("sources")
    return bronnen if isinstance(bronnen, list) else []


def ess03_uitkomst_van_definition(
    definition: Definition,
    binding: Beoordelingsbinding | None = None,
    *,
    assessment: Any = _ONGEZET,
) -> dict[str, Any]:
    """De ESS-03-uitkomst van een (herladen) record: replay van de opgeslagen
    beoordeling op term, tekst, context, bedoelde betekenis en bronset van het
    record, tegen de actuele beoordelingsbinding (R1) — geen AI-aanroep. Een
    stale, historische of ontbrekende beoordeling is open, met de reden.

    `assessment` (optioneel) is een expliciet document — bv. de beoordeling
    van de laatste sessietoetsing — dat in plaats van het opgeslagen document
    aan exact deze kandidaat wordt gebonden."""
    from domain.ess03.contract import beoordeel_telbaarheid

    meta: Mapping[str, Any] = definition.metadata or {}
    return beoordeel_telbaarheid(
        definition.begrip or "",
        definition.definitie or "",
        {
            "organisatorische_context": list(definition.organisatorische_context or []),
            "juridische_context": list(definition.juridische_context or []),
            "wettelijke_basis": list(definition.wettelijke_basis or []),
        },
        _record_bronnen(meta),
        intentie=ess03_intentie_van_definition(definition),
        assessment=(
            meta.get("ess03_assessment") if assessment is _ONGEZET else assessment
        ),
        binding=binding,
    ).als_dict()


_ESS03 = "ESS-03"
#: Regelstatus → teller in `evaluation_coverage` (DEF-624/2.1.0).
_DEKKINGSTELLER: dict[str, str] = {
    "pass": "passed",
    "fail": "failed",
    "review_required": "review_required",
    "error": "error",
    "not_evaluated": "not_evaluated",
    "not_applicable": "not_applicable",
}


def herbind_ess03_in_validatieresultaat(
    resultaat: Mapping[str, Any],
    kandidaat: Definition,
    *,
    binding: Beoordelingsbinding | None,
) -> dict[str, Any]:
    """Het V2-validatieresultaat van een eerdere toetsing, met ESS-03 opnieuw
    gebonden aan de kandidaat zoals die nú in de editor staat (R1/R5).

    Pure replay, geen AI-aanroep: de beoordeling van die toetsing
    (`ess03_assessment` in het resultaat) wordt via het contract tegen de
    huidige term, tekst, drie contextlijsten, bedoelde betekenis
    (toelichting, categorie, betekenisverduidelijking, ESS-03-verduidelijking),
    bronset en de actuele prompt/norm/provider/model gelegd. Klopt de binding
    nog, dan blijft het resultaat ongewijzigd (zelfde object). Anders is de
    uitkomst een kopie waarin ESS-03 open/historisch is — in `rule_results`,
    `rule_statuses`, `passed_rules`, `violations`, `review_required` en de
    dekking — zodat een eerder 'Voldoet' nooit als actuele pass wordt getoond
    voor een formulier waarbij het niet meer hoort. Het oorspronkelijke
    resultaat wordt niet gemuteerd; de beoordeling zelf blijft erin (een
    teruggezette invoer maakt haar weer actueel).
    """
    ongewijzigd = resultaat if isinstance(resultaat, dict) else dict(resultaat)
    beoordeling = resultaat.get("ess03_assessment")
    statussen = resultaat.get("rule_statuses")
    if not isinstance(beoordeling, Mapping) or not isinstance(statussen, Mapping):
        return ongewijzigd
    uitkomst = ess03_uitkomst_van_definition(kandidaat, binding, assessment=beoordeling)
    huidig_detail = _als_mapping((resultaat.get("rule_results") or {}).get(_ESS03))
    oude_status = statussen.get(_ESS03)
    if (
        uitkomst["status"] == oude_status
        and uitkomst["fingerprint"] == huidig_detail.get("fingerprint")
        and _als_mapping(uitkomst.get("review")).get("assessment", {}).get("applied")
        == _als_mapping(huidig_detail.get("review"))
        .get("assessment", {})
        .get("applied")
    ):
        return ongewijzigd

    herbonden = deepcopy(dict(resultaat))
    herbonden.setdefault("rule_results", {})[_ESS03] = uitkomst
    herbonden.setdefault("rule_statuses", {})[_ESS03] = uitkomst["status"]
    herbonden["passed_rules"] = [
        code for code in resultaat.get("passed_rules") or [] if code != _ESS03
    ]
    herbonden["violations"] = [
        v
        for v in resultaat.get("violations") or []
        if not (isinstance(v, Mapping) and _ESS03 in (v.get("code"), v.get("rule_id")))
    ]
    herbonden["review_required"] = [
        item
        for item in resultaat.get("review_required") or []
        if not (isinstance(item, Mapping) and item.get("rule_id") == _ESS03)
    ]
    delen = uitkomst.get("parts") or []
    reden = (delen[0].get("reason") if delen else None) or ""
    from services.validation.violation_builder import category_for_rule

    if uitkomst["status"] == "review_required":
        herbonden["review_required"].append(
            {
                "rule_id": _ESS03,
                "category": category_for_rule(_ESS03),
                "reason": reden,
                "signals": [],
            }
        )
    elif uitkomst["status"] == "pass":
        herbonden["passed_rules"].append(_ESS03)
    elif uitkomst["status"] == "fail":
        # Zelfde niet-blokkerende vorm als de evaluator (besluit 21-09-2026).
        herbonden["violations"].append(
            {
                "code": _ESS03,
                "rule_id": _ESS03,
                "severity": "warning",
                "message": reden,
                "description": reden,
                "category": category_for_rule(_ESS03),
                "advisory": True,
            }
        )
    dekking = herbonden.get("evaluation_coverage")
    if isinstance(dekking, dict) and isinstance(oude_status, str):
        oud, nieuw = _DEKKINGSTELLER.get(oude_status), _DEKKINGSTELLER.get(
            uitkomst["status"]
        )
        if oud and nieuw and oud != nieuw:
            dekking[oud] = max(0, int(dekking.get(oud) or 0) - 1)
            dekking[nieuw] = int(dekking.get(nieuw) or 0) + 1
    herbonden["ess03_rebound"] = {
        "from_status": oude_status,
        "to_status": uitkomst["status"],
        "historical": bool(
            _als_mapping(uitkomst.get("review")).get("assessment", {}).get("historical")
        ),
    }
    return herbonden


_INT01 = "INT-01"


def _herbereken_afgeleide_dekking(dekking: dict[str, Any]) -> None:
    """`evaluated` en `coverage_ratio` opnieuw uit de tellers, zoals
    `ModularValidationService._bereken_dekking` ze afleidt (pass + fail)."""
    geevalueerd = int(dekking.get("passed") or 0) + int(dekking.get("failed") or 0)
    totaal = int(dekking.get("total") or 0)
    dekking["evaluated"] = geevalueerd
    dekking["coverage_ratio"] = round(geevalueerd / totaal, 4) if totaal else 0.0


def herbind_int01_in_validatieresultaat(
    resultaat: Mapping[str, Any], kern: str
) -> dict[str, Any]:
    """Het V2-resultaat van een eerdere toetsing met INT-01 gebonden aan de
    tekst die nú in de editor staat (DEF-770).

    De vingerafdruk van de werkelijk getoetste tekst legt de INT-01-evaluator
    zelf vast (`rule_results['INT-01']['fingerprint']`), dus ieder resultaat
    draagt haar, ongeacht welke route het in de sessie zet. Gelijk aan de
    huidige tekst = ongewijzigd (zelfde object). Anders, of zonder
    vingerafdruk (geen deeluitkomst: ongewijzigd), een kopie
    waarin INT-01 open en niet toepasbaar is — zonder de oude onderdelen, dus
    nooit een oude 'één zin'-pass — in `rule_results`, `rule_statuses`,
    `passed_rules`, `violations`, `review_required` en de dekking. Het
    oorspronkelijke resultaat wordt niet gemuteerd.
    """
    ongewijzigd = resultaat if isinstance(resultaat, dict) else dict(resultaat)
    statussen = resultaat.get("rule_statuses")
    detail = _als_mapping(_als_mapping(resultaat.get("rule_results")).get(_INT01))
    if not isinstance(statussen, Mapping) or not detail:
        return ongewijzigd
    if detail.get("fingerprint") == tekstvingerafdruk((kern or "").strip()):
        return ongewijzigd
    reden = (
        "INT-01: de formuliertekst is na deze toetsing gewijzigd; de eerdere "
        "uitkomst geldt niet voor de huidige tekst. Toets opnieuw."
    )
    oude_status = statussen.get(_INT01)
    herbonden = deepcopy(dict(resultaat))
    herbonden.setdefault("rule_results", {})[_INT01] = niet_toepasbaar_detail(reden)
    herbonden["rule_statuses"][_INT01] = "review_required"
    herbonden["passed_rules"] = [
        code for code in resultaat.get("passed_rules") or [] if code != _INT01
    ]
    herbonden["violations"] = [
        v
        for v in resultaat.get("violations") or []
        if not (isinstance(v, Mapping) and _INT01 in (v.get("code"), v.get("rule_id")))
    ]
    from services.validation.violation_builder import category_for_rule

    herbonden["review_required"] = [
        item
        for item in resultaat.get("review_required") or []
        if not (isinstance(item, Mapping) and item.get("rule_id") == _INT01)
    ] + [
        {
            "rule_id": _INT01,
            "category": category_for_rule(_INT01),
            "reason": reden,
            "signals": [],
        }
    ]
    dekking = herbonden.get("evaluation_coverage")
    if isinstance(dekking, dict) and isinstance(oude_status, str):
        oud = _DEKKINGSTELLER.get(oude_status)
        nieuw = _DEKKINGSTELLER.get("review_required")
        if oud and nieuw and oud != nieuw:
            dekking[oud] = max(0, int(dekking.get(oud) or 0) - 1)
            dekking[nieuw] = int(dekking.get(nieuw) or 0) + 1
        _herbereken_afgeleide_dekking(dekking)
    herbonden["int01_rebound"] = {"from_status": oude_status}
    return herbonden


def bindingsafwijzing_ess03(
    assessment: Any,
    definition: Definition,
    *,
    binding: Beoordelingsbinding | None = None,
) -> str | None:
    """Waarom een ESS-03-sessiebeoordeling níet bij de op te slaan kandidaat hoort, of None.

    Zelfde regel als DEF-809 voor CON-02: alleen een uitgevoerde (`assessed`)
    beoordeling waarvan de vingerafdruk exact die van de nu op te slaan
    kandidaat is (term, tekst, contextlijsten, bedoelde betekenis, bronset)
    én die bij de actuele beoordelingsbinding hoort (promptversie, norm,
    provider/model — R1, wanneer bekend) mag als actueel bewijs worden
    vastgelegd. De verduidelijking is de actuele waarde van de kandidaat (R5).
    """
    from domain.ess03.contract import bereken_ess03_vingerafdruk

    if not isinstance(assessment, Mapping):
        return "beoordeling is geen object"
    if assessment.get("status") != "assessed":
        return (
            f"ESS-03-beoordeling niet uitgevoerd (status {assessment.get('status')!r})"
        )
    meta: Mapping[str, Any] = definition.metadata or {}
    vingerafdruk = bereken_ess03_vingerafdruk(
        definition.begrip or "",
        definition.definitie or "",
        {
            "organisatorische_context": list(definition.organisatorische_context or []),
            "juridische_context": list(definition.juridische_context or []),
            "wettelijke_basis": list(definition.wettelijke_basis or []),
        },
        _record_bronnen(meta),
        intentie=ess03_intentie_van_definition(definition),
    )
    if assessment.get("fingerprint") != vingerafdruk:
        return (
            "beoordeling hoort niet bij de op te slaan kandidaat (tekst, context, "
            "term, bedoelde betekenis, verduidelijking of bronnen zijn sinds de "
            "toetsing gewijzigd); toets opnieuw na opslaan"
        )
    return _configuratieafwijzing_ess03(assessment, binding)


def _configuratieafwijzing_ess03(
    assessment: Mapping[str, Any], binding: Beoordelingsbinding | None
) -> str | None:
    """R1: promptversie, norm en provider/model tegen de actuele binding (indien bekend)."""
    if binding is None:
        return None
    attributie = _als_mapping(assessment.get("attribution"))
    if assessment.get("prompt_version") != binding.prompt_version:
        return (
            f"beoordeling hoort bij promptversie {assessment.get('prompt_version')!r}; "
            f"actueel is {binding.prompt_version!r}"
        )
    if assessment.get("norm_sha256") != binding.norm_sha256:
        return "beoordeling hoort bij een eerdere versie van de ESS-03-norm"
    if (attributie.get("provider") or None) != (binding.provider or None) or (
        attributie.get("model") != binding.model
    ):
        return (
            f"beoordeling komt van {attributie.get('provider')!r}/"
            f"{attributie.get('model')!r}; actueel is "
            f"{binding.provider!r}/{binding.model!r}"
        )
    return None


def _neem_ess03_beoordeling_op(
    assessment: Mapping[str, Any] | None,
    definition: Definition,
    binding: Beoordelingsbinding | None,
) -> tuple[bool, str | None]:
    """Zet een bindende ESS-03-sessiebeoordeling als actueel bewijs op de kandidaat.

    Geeft (opgenomen, reden-waarom-niet). Zonder beoordeling: (False, None).
    """
    if assessment is None:
        return False, None
    reden = bindingsafwijzing_ess03(assessment, definition, binding=binding)
    if reden is not None:
        return False, reden
    if definition.metadata is None:
        definition.metadata = {}
    definition.metadata["ess03_assessment"] = deepcopy(dict(assessment))
    return True, None


def _als_mapping(waarde: Any) -> Mapping[str, Any]:
    """Typegetrouwe vernauwing: een mapping, anders een lege mapping."""
    return waarde if isinstance(waarde, Mapping) else {}


def _als_dict(waarde: Any) -> dict[str, Any]:
    """Typegetrouwe vernauwing: een dict, anders een lege dict."""
    return waarde if isinstance(waarde, dict) else {}


@dataclass(frozen=True)
class _Weigering:
    """Een weigering (status/message[/validation]) als onderscheidbaar type,
    zodat een aanroeper haar niet met een validatieresultaat verwart."""

    payload: dict[str, Any]


def normaliseer_validatieresultaat(v: Mapping[str, Any]) -> dict[str, Any]:
    """Vertaal een V2-validatieresultaat naar de UI-structuur van de editor.

    Bewaart alles wat de gebruiker moet kunnen zien: de gestructureerde
    regeluitkomsten (`rule_results`), de status per regel (`rule_statuses`),
    de beoordelingsdekking (`evaluation_coverage`), open onderdelen
    (`review_required`), de validatiestatus/readiness (fail-closed guard) en
    de volledige bronbeoordeling (`source_assessment`, contract 1.4.0). Het
    ruwe resultaat blijft onder `raw_v2`.

    `score` is uitsluitend informatief-intern: `None` wanneer de sleutel
    ontbreekt óf expliciet None is. Er wordt nooit een 0.0 of een positief
    cijfer ingevuld (DEF-622/DEF-743); `valid` blijft fail-closed False bij
    een ontbrekend oordeel.

    DEF-624: de runstatus wordt via het contract expliciet gemaakt. Een
    resultaat zonder geldige `validation_status` is geen uitgevoerde run:
    `valid` is dan False, `validation_status` is `validation_unknown` en
    `unknown_reason` draagt de contractreden - ook in `raw_v2`, dat de
    gedeelde weergave rendert. De bron wordt niet gemuteerd.
    """
    from services.validation.result_contract import met_expliciete_runstatus

    ruw = met_expliciete_runstatus(v)
    violations = ruw.get("violations", []) or []
    normalized_issues = []
    for item in violations:
        if not isinstance(item, dict):
            continue
        normalized_issues.append(
            {
                "rule": item.get("rule_id") or item.get("code"),
                "message": item.get("description") or item.get("message", ""),
                "severity": item.get("severity", "warning"),
            }
        )
    ruwe_score = ruw.get("overall_score")
    try:
        score = None if ruwe_score is None else float(ruwe_score)
    except (TypeError, ValueError):
        score = None
    return {
        "valid": ruw.get("is_acceptable") is True,
        "score": score,
        "issues": normalized_issues,
        "rule_results": deepcopy(dict(ruw.get("rule_results") or {})),
        "rule_statuses": deepcopy(dict(ruw.get("rule_statuses") or {})),
        "evaluation_coverage": deepcopy(ruw.get("evaluation_coverage")),
        "review_required": deepcopy(list(ruw.get("review_required") or [])),
        "validation_status": ruw.get("validation_status"),
        "unknown_reason": ruw.get("unknown_reason"),
        "validation_readiness": deepcopy(ruw.get("validation_readiness")),
        "source_assessment": deepcopy(ruw.get("source_assessment")),
        # DEF-766 (contract 2.1.0): de ESS-03-beoordeling van deze toetsing.
        "ess03_assessment": deepcopy(ruw.get("ess03_assessment")),
        "raw_v2": ruw,
    }


class AutoSaveResult(Enum):
    """Uitkomst van een auto-save (DEF-469).

    Onderscheidt expliciet "opgeslagen", "uitgeschakeld" en "mislukt" zodat de UI
    de gebruiker kan waarschuwen bij een echte fout i.p.v. een mislukte save te
    verwarren met een uitgeschakelde/overgeslagen save.
    """

    SAVED = "saved"
    DISABLED = "disabled"
    FAILED = "failed"

    # Let op: vergelijk met `is` (elk enum-lid is truthy — een `if auto_save(...)`
    # zou dus altijd waar zijn).


logger = logging.getLogger(__name__)


class DefinitionEditService:
    """
    Service for managing definition editing operations.

    Provides:
    - Edit orchestration with validation
    - Version management
    - Auto-save functionality
    - Conflict resolution
    """

    def __init__(
        self,
        repository: DefinitionEditRepository | None = None,
        validation_service: ModularValidationService | None = None,
        proposal_service: Any | None = None,
    ):
        """
        Initialize the edit service.

        Args:
            repository: Repository for data access
            validation_service: Service for validation
            proposal_service: DEF-743: `SourceProposalService` voor het
                handmatige verbetervoorstel (alleen op expliciet verzoek).
                Zonder dienst is de aanvraag geblokkeerd, nooit stil.
        """
        self.repository = repository or DefinitionEditRepository()
        self.validation_service = validation_service
        self.proposal_service = proposal_service

        # Auto-save configuration
        self.auto_save_interval = 30  # seconds
        self.auto_save_enabled = True

        # Cache for performance
        self._cache: dict[str, tuple[list[dict[str, Any]], datetime]] = {}
        self._cache_ttl = 300  # 5 minutes

        logger.info("DefinitionEditService initialized")

    def start_edit_session(
        self, definitie_id: int, user: str = "system"
    ) -> dict[str, Any]:
        """
        Start een edit sessie voor een definitie.

        Args:
            definitie_id: ID van de te bewerken definitie
            user: Gebruiker die edit sessie start

        Returns:
            Sessie informatie inclusief definitie en lock status
        """
        try:
            # Get definition
            definition = self.repository.get(definitie_id)
            if not definition:
                return {"success": False, "error": "Definitie niet gevonden"}

            # Check for existing auto-save
            auto_save = self.repository.get_latest_auto_save(definitie_id)

            # Get version history
            history = self.repository.get_version_history(definitie_id, limit=5)

            return {
                "success": True,
                "definition": definition,
                "auto_save": auto_save,
                "history": history,
                "session_id": self._generate_session_id(definitie_id, user),
                "locked": False,  # Implement locking if needed
                "user": user,
                "started_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error starting edit session: {e}")
            return {"success": False, "error": str(e)}

    def save_definition(
        self,
        definitie_id: int,
        updates: dict[str, Any],
        user: str = "system",
        reason: str | None = None,
        validate: bool = True,
        *,
        source_assessment: Mapping[str, Any] | None = None,
        ess03_assessment: Mapping[str, Any] | None = None,
        ess03_binding: Beoordelingsbinding | None = None,
        categoriekeuze: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Sla definitie wijzigingen op.

        Args:
            definitie_id: ID van de definitie
            updates: Dictionary met updates
            user: Gebruiker die opslaat
            reason: Reden voor wijziging
            validate: Of validatie uitgevoerd moet worden
            source_assessment: DEF-809: de AI-bronbeoordeling uit de laatste
                toetsing in de sessie. Alleen als zij exact aan de op te slaan
                kandidaat bindt (`bindingsafwijzing_beoordeling`) gaat zij als
                actueel bewijs mee; de DB-laag legt haar dan — gebonden aan de
                tekst/context van deze opslag — vast met historie
                (`origin: revalidation`). Anders blijft het opgeslagen bewijs
                staan en meldt het resultaat waarom.
            ess03_assessment: DEF-766: de AI-telbaarheidsbeoordeling (ESS-03)
                uit de laatste toetsing in de sessie; zelfde regel
                (`bindingsafwijzing_ess03`): alleen `assessed` en exact aan de
                op te slaan kandidaat gebonden wordt zij actueel bewijs, met
                historie in de DB-laag; anders benoemt het resultaat waarom niet.
            ess03_binding: R1 — de actuele beoordelingsbinding (promptversie,
                norm, provider/model) waaraan de sessiebeoordeling moet voldoen
                om als actueel te gelden; None = niet gecontroleerd op binding.
                `updates["ess03_verduidelijking"]` (R5) vervoert de actuele
                verduidelijking van de kandidaat (ook bewust leeg) en wordt als
                eigen recordwaarde opgeslagen — ook zonder beoordeling.
            categoriekeuze: DEF-751 B2 — de expliciete menselijke
                categoriekeuze van déze opslaan-actie
                (`{"herkomst": "editor", "actor", "actor_source"}`). Alleen
                via deze parameter — nooit via `updates`/metadata — ontstaat
                een keuze-event; vereist `updates["version_number"]` (de
                versie van de getoonde kandidaat) tot de uiteindelijke UPDATE.

        Returns:
            Result dictionary met success status; `source_assessment_persisted`
            en `source_assessment_reason` zeggen wat er met de beoordeling is
            gebeurd (nooit stil verlies).
        """
        try:
            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {"success": False, "error": "Definitie niet gevonden"}
            if "category_choice_input" in updates or "category_choice" in updates:
                return {
                    "success": False,
                    "error": (
                        "Een categoriekeuze reist niet via updates; gebruik de "
                        "parameter categoriekeuze"
                    ),
                }
            if categoriekeuze is not None and "version_number" not in updates:
                return {
                    "success": False,
                    "error": "Categoriekeuze vereist de versie van de getoonde kandidaat",
                }

            # Check version conflict
            if "version_number" in updates:
                if self.repository.check_version_conflict(
                    definitie_id, updates["version_number"]
                ):
                    return {
                        "success": False,
                        "error": "Versie conflict - definitie is gewijzigd door andere gebruiker",
                        "conflict": True,
                    }

            # Apply updates
            updated_definition = self._apply_updates(current, updates)

            # DEF-809: de sessiebeoordeling als actueel bewijs, uitsluitend bij
            # exacte binding aan de kandidaat die nu wordt opgeslagen.
            beoordeling_bewaard, beoordeling_reden = _neem_sessiebeoordeling_op(
                source_assessment, updated_definition, current.metadata
            )
            # DEF-766: idem voor de ESS-03-beoordeling van de laatste toetsing.
            ess03_bewaard, ess03_reden = _neem_ess03_beoordeling_op(
                ess03_assessment, updated_definition, ess03_binding
            )

            # Validate if requested
            validation_results = None
            if validate and self.validation_service:
                validation_results = self._validate_definition(updated_definition)
                if validation_results and not validation_results.get("valid", True):
                    # Still save but mark validation issues
                    if not updated_definition.metadata:
                        updated_definition.metadata = {}
                    updated_definition.metadata["validation_issues"] = (
                        validation_results.get("issues", [])
                    )

            # Save with history (DEF-751: mét keuze via het expliciete commando)
            saved_id = self.repository.save_with_history(
                updated_definition,
                wijziging_reden=reason,
                gewijzigd_door=user,
                categoriekeuze=categoriekeuze,
            )

            # Clear cache
            self._clear_cache(definitie_id)

            return {
                "success": True,
                "definition_id": saved_id,
                "validation": validation_results,
                "timestamp": datetime.now().isoformat(),
                "source_assessment_persisted": beoordeling_bewaard,
                "source_assessment_reason": beoordeling_reden,
                "ess03_assessment_persisted": ess03_bewaard,
                "ess03_assessment_reason": ess03_reden,
            }

        except Exception as e:
            logger.error(f"Error saving definition: {e}")
            return {"success": False, "error": str(e)}

    def auto_save(self, definitie_id: int, content: dict[str, Any]) -> AutoSaveResult:
        """
        Auto-save draft versie.

        Args:
            definitie_id: ID van de definitie
            content: Content om op te slaan

        Returns:
            AutoSaveResult: SAVED bij succes, DISABLED als auto-save uit staat,
            FAILED bij een fout (DEF-469: zodat de UI bij een echte fout kan
            waarschuwen i.p.v. die te verwarren met "uitgeschakeld").
        """
        if not self.auto_save_enabled:
            return AutoSaveResult.DISABLED

        try:
            # Add timestamp
            content["auto_save_timestamp"] = datetime.now().isoformat()

            # Save draft (repository raiset bij een DB-fout — niet langer stil False)
            self.repository.auto_save_draft(definitie_id, content)
            return AutoSaveResult.SAVED

        except RepositoryError as e:
            # Gericht op de repository-fout: onverwachte (programmeer)fouten laten
            # we bewust doorbubbelen i.p.v. te maskeren als "FAILED".
            logger.error(f"Auto-save failed: {e}", exc_info=True)
            return AutoSaveResult.FAILED

    def restore_auto_save(self, definitie_id: int) -> dict[str, Any] | None:
        """
        Herstel auto-save content.

        Args:
            definitie_id: ID van de definitie

        Returns:
            Auto-save content indien beschikbaar
        """
        try:
            result = self.repository.get_latest_auto_save(definitie_id)
            return cast(dict[str, Any] | None, result)
        except Exception as e:
            logger.error(f"Error restoring auto-save: {e}")
            return None

    def get_version_history(
        self, definitie_id: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Haal versie geschiedenis op.

        Args:
            definitie_id: ID van de definitie
            limit: Maximum aantal versies

        Returns:
            Lijst met versie geschiedenis
        """
        try:
            # Check cache
            cache_key = f"history_{definitie_id}_{limit}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                    return cached_data

            # Get from repository
            history = cast(
                list[dict[str, Any]],
                self.repository.get_version_history(definitie_id, limit),
            )

            # Process history entries
            for entry in history:
                # Add human-readable timestamp
                if "gewijzigd_op" in entry:
                    entry["gewijzigd_op_readable"] = self._format_timestamp(
                        entry["gewijzigd_op"]
                    )

                # Add change summary
                entry["summary"] = self._generate_change_summary(entry)

            # Cache result
            self._cache[cache_key] = (history, datetime.now())

            return history

        except Exception as e:
            logger.error(f"Error getting version history: {e}")
            return []

    def revert_to_version(
        self, definitie_id: int, version_id: int, user: str = "system"
    ) -> dict[str, Any]:
        """
        Revert definitie naar eerdere versie.

        Args:
            definitie_id: ID van de definitie
            version_id: ID van de versie om naar te reverten
            user: Gebruiker die revert uitvoert

        Returns:
            Result dictionary
        """
        try:
            # Get version from history
            history = self.repository.get_version_history(definitie_id, limit=100)

            version_entry = None
            for entry in history:
                if entry.get("id") == version_id:
                    version_entry = entry
                    break

            if not version_entry:
                return {"success": False, "error": "Versie niet gevonden"}

            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {"success": False, "error": "Definitie niet gevonden"}

            # Apply value from selected version (prefer new value of that entry)
            if version_entry.get("definitie_nieuwe_waarde"):
                current.definitie = version_entry["definitie_nieuwe_waarde"]
            elif version_entry.get("definitie_oude_waarde"):
                current.definitie = version_entry["definitie_oude_waarde"]

            # Apply context if available (Context Model V2: drie lijsten)
            if version_entry.get("context_snapshot"):
                context = version_entry["context_snapshot"]
                if isinstance(context, dict):
                    if "organisatorische_context" in context:
                        current.organisatorische_context = (
                            context["organisatorische_context"] or []
                        )
                    if "juridische_context" in context:
                        current.juridische_context = context["juridische_context"] or []
                    if "wettelijke_basis" in context:
                        current.wettelijke_basis = context["wettelijke_basis"] or []

            # Save as new version
            return self.save_definition(
                definitie_id,
                self._definition_to_dict(current),
                user=user,
                reason=f"Reverted naar versie {version_id}",
            )

        except Exception as e:
            logger.error(f"Error reverting to version: {e}")
            return {"success": False, "error": str(e)}

    def batch_update(
        self, updates: list[tuple[int, dict[str, Any]]], user: str = "system"
    ) -> dict[str, Any]:
        """
        Update meerdere definities tegelijk.

        Args:
            updates: Lijst van (definitie_id, update_dict) tuples
            user: Gebruiker die update uitvoert

        Returns:
            Result dictionary met successen en fouten
        """
        results: dict[str, Any] = {
            "success": [],
            "failed": [],
            "total": len(updates),
        }
        success_list: list[int] = results["success"]
        failed_list: list[dict[str, Any]] = results["failed"]

        for definitie_id, update_dict in updates:
            try:
                result = self.save_definition(
                    definitie_id,
                    update_dict,
                    user=user,
                    validate=False,  # Skip validation for batch
                )

                if result["success"]:
                    success_list.append(definitie_id)
                else:
                    failed_list.append(
                        {
                            "id": definitie_id,
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                failed_list.append({"id": definitie_id, "error": str(e)})

        return results

    def search_and_replace(
        self,
        search_term: str,
        replace_term: str,
        field: str = "definitie",
        filters: dict[str, Any] | None = None,
        user: str = "system",
    ) -> dict[str, Any]:
        """
        Zoek en vervang in meerdere definities.

        Args:
            search_term: Te zoeken term
            replace_term: Vervangende term
            field: Veld om in te zoeken (definitie, begrip, etc.)
            filters: Extra filters voor zoeken
            user: Gebruiker die operatie uitvoert

        Returns:
            Result dictionary
        """
        try:
            # Search definitions
            # Normalize filters: map legacy 'context' key to 'context_filter'
            normalized_filters = dict(filters) if filters else {}
            if (
                "context" in normalized_filters
                and "context_filter" not in normalized_filters
            ):
                normalized_filters["context_filter"] = normalized_filters.pop("context")

            definitions = self.repository.search_with_filters(
                search_term=search_term, **normalized_filters
            )

            updates = []
            for definition in definitions:
                # DEF-439: batch_update verwacht non-optional ids; sla door-id-loze
                # definities over (kunnen toch niet geadresseerd worden).
                if definition.id is None:
                    continue
                # Check if field contains search term
                field_value = getattr(definition, field, None)
                if field_value and search_term in field_value:
                    # Prepare update
                    new_value = field_value.replace(search_term, replace_term)
                    updates.append((definition.id, {field: new_value}))

            # Execute batch update
            if updates:
                return self.batch_update(updates, user=user)

            return {
                "success": [],
                "failed": [],
                "total": 0,
                "message": "Geen definities gevonden om te updaten",
            }

        except Exception as e:
            logger.error(f"Error in search and replace: {e}")
            return {"success": [], "failed": [], "error": str(e)}

    def _apply_updates(
        self, definition: Definition, updates: dict[str, Any]
    ) -> Definition:
        """Apply updates to definition object."""
        # Create copy
        updated = Definition(
            id=definition.id,
            begrip=updates.get("begrip", definition.begrip),
            definitie=updates.get("definitie", definition.definitie),
            toelichting=updates.get("toelichting", definition.toelichting),
            bron=updates.get("bron", definition.bron),
            organisatorische_context=updates.get(
                "organisatorische_context",
                getattr(definition, "organisatorische_context", []),
            ),
            juridische_context=updates.get(
                "juridische_context", getattr(definition, "juridische_context", [])
            ),
            wettelijke_basis=updates.get(
                "wettelijke_basis", getattr(definition, "wettelijke_basis", [])
            ),
            categorie=updates.get("categorie", definition.categorie),
            ufo_categorie=updates.get(
                "ufo_categorie", getattr(definition, "ufo_categorie", None)
            ),
            created_at=definition.created_at,
            updated_at=datetime.now(),
            # DEF-751 B2: eigen kopie — de invoersleutel van déze actie mag
            # niet in het geladen (sessie)object achterblijven en bij een
            # volgende opslag opnieuw als keuze meereizen.
            metadata=dict(definition.metadata or {}),
        )

        # Update metadata fields
        metadata_fields = [
            "status",
            "juridische_context",
            "wettelijke_basis",
            "validation_score",
            "version_number",
        ]
        # DEF-439: metadata is dict|None (dataclass); narrow vóór indexed writes.
        if updated.metadata is None:
            updated.metadata = {}
        for field in metadata_fields:
            if field in updates:
                updated.metadata[field] = updates[field]
        # R5: de actuele ESS-03-verduidelijking van deze opslaan-actie (tekst,
        # ook leeg) wordt de recordwaarde; zonder sleutel blijft de geladen
        # waarde staan.
        if isinstance(updates.get("ess03_verduidelijking"), str):
            updated.metadata["ess03_verduidelijking"] = updates[
                "ess03_verduidelijking"
            ].strip()

        return updated

    def _validate_definition(
        self,
        definition: Definition,
        geladen_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Validate definition using injected validation service (sync only).

        Async validation is not executed here. If only an async API is available,
        return None and let the UI call validation via async_bridge.

        DEF-743: de kandidaat is de ACTUELE bewerkte tekst/term/drie contexten;
        `geladen_metadata` (het ID-only geladen record) levert dezelfde
        bronset, recordversie en vastgelegde beoordelingen als het async pad
        (`bouw_validatiecontext`). Zonder `geladen_metadata` wordt
        `definition.metadata` gebruikt (een via de repository geladen record
        draagt die sleutels zelf).
        """
        if not self.validation_service:
            return None

        try:
            import inspect

            vs = self.validation_service

            # Eén contextdict voor sync én async (pariteit): bewerkte lijsten
            # altijd expliciet (ook leeg), bronset/versie/beoordeling uit het
            # geladen record.
            context_dict: dict[str, Any] = bouw_validatiecontext(
                definition,
                (
                    geladen_metadata
                    if geladen_metadata is not None
                    else (definition.metadata or {})
                ),
            )

            if hasattr(vs, "validate_text"):
                fn = vs.validate_text
                # Sla async API over (UI moet async_bridge gebruiken)
                if inspect.iscoroutinefunction(fn):
                    return None
                results = fn(
                    begrip=definition.begrip,
                    text=definition.definitie,
                    ontologische_categorie=getattr(
                        definition, "ontologische_categorie", None
                    )
                    or definition.categorie,
                    context=context_dict,
                )
            else:
                # Try generic validate_definition
                try:
                    fn = vs.validate_definition
                except AttributeError:
                    fn = getattr(vs, "validate", None)
                if fn is None:
                    return None
                if inspect.iscoroutinefunction(fn):
                    return None
                # Support both signatures
                try:
                    results = fn(definition)
                except TypeError:
                    results = fn(
                        begrip=definition.begrip,
                        text=definition.definitie,
                        ontologische_categorie=getattr(
                            definition, "ontologische_categorie", None
                        )
                        or definition.categorie,
                        context=context_dict,
                    )

            # Normalize result to UI format
            # Case 1: dict schema (ModularValidationService/Orchestrator ensure_schema)
            if isinstance(results, dict):
                # DEF-743: status, onderdelen, bewijs, open/technische
                # onderdelen en dekking blijven behouden; geen 0.0-terugval.
                return normaliseer_validatieresultaat(results)

            # Case 2: legacy object with attributes
            if hasattr(results, "overall_status") or hasattr(
                results, "validation_score"
            ):
                issues_attr = getattr(results, "issues", []) or []
                normalized_issues = []
                for issue in issues_attr:
                    try:
                        normalized_issues.append(
                            {
                                "rule": getattr(issue, "regel_code", None)
                                or getattr(issue, "rule", None),
                                "message": getattr(issue, "message", ""),
                                "severity": getattr(issue, "severity", "warning"),
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Validation issue normalisatie gefaald: {e}")
                # DEF-743: een ontbrekend cijfer blijft None (geen 0.0).
                legacy_score = getattr(results, "validation_score", None)
                return {
                    "valid": getattr(results, "overall_status", "") == "success",
                    "score": None if legacy_score is None else float(legacy_score),
                    "issues": normalized_issues,
                }

            # Unknown format
            return None

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None

    # ===== DEF-743: handmatig verbetervoorstel (CON-02) — alleen op verzoek =====

    def bronbasis_van_record(
        self, record: Any, huidig_resultaat: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """De actuele CON-02-uitkomst + bronbeoordeling voor het OPGESLAGEN record.

        Altijd een pure replay van de kern (`beoordeel_bronbasis`) tegen de
        ACTUELE opgeslagen deskundige beoordeling en recordversie — nooit het
        samengestelde CON-02-verdict uit een eerder sessieresultaat (dat
        kent de sindsdien vastgelegde correctie/uitzondering niet). Als
        beoordelingsinvoer geldt de opgeslagen volledige beoordeling wanneer
        die exact aan het record bindt; alleen als die ontbreekt of niet
        (meer) bindt, de sessiebeoordeling van de eigen wrapper, mits exact
        gebonden (zelfde vingerafdruk, status `assessed`). Nooit een
        AI-aanroep. Het oorspronkelijke AI-oordeel blijft via de kern
        zichtbaar (`applied_correction.original`).
        """
        from domain.sources.contract import (
            beoordeel_bronbasis,
            bereken_bronvingerafdruk,
        )

        velden = record.get_contractvelden()
        bronnen = velden.get("provenance_sources")
        if bronnen is None:
            bronnen = velden.get("sources")
        bronnen = list(bronnen or [])
        contexten = record.get_contextlijsten()
        tekst = record.get_definitie_tekst()
        peildatum = velden.get("peildatum")
        vingerafdruk = bereken_bronvingerafdruk(
            record.begrip or "", tekst, contexten, bronnen, peildatum=peildatum
        )
        basis: dict[str, Any] = {
            "bronnen": bronnen,
            "contexten": contexten,
            "tekst": tekst,
            "peildatum": peildatum,
            "fingerprint": vingerafdruk,
            "receipt": velden.get("source_receipt"),
            "validation_status": None,
        }

        def _gebonden(beoordeling: Any) -> bool:
            return (
                isinstance(beoordeling, Mapping)
                and beoordeling.get("fingerprint") == vingerafdruk
                and beoordeling.get("status") == "assessed"
            )

        assessment = velden.get("source_assessment")
        bron = "record"
        if not _gebonden(assessment) and isinstance(huidig_resultaat, Mapping):
            sessie = huidig_resultaat.get("source_assessment")
            if _gebonden(sessie):
                from services.validation.result_contract import bepaal_runstatus

                assessment = sessie
                bron = "sessie"
                # DEF-624: de status van het sessieresultaat via het contract;
                # een sessieresultaat zonder geldige status is geen run en
                # levert daarmee de technische diagnose, geen voorstel.
                basis["validation_status"] = bepaal_runstatus(huidig_resultaat).status
        uitkomst = beoordeel_bronbasis(
            record.begrip or "",
            tekst,
            contexten,
            bronnen,
            assessment=assessment,
            review=velden.get("source_review"),
            definitie_versie=velden.get("definition_version"),
            peildatum=peildatum,
        )
        basis["con02"] = uitkomst.als_dict()
        basis["assessment"] = assessment
        basis["bron"] = bron
        return basis

    # ===== DEF-808: opgegeven bronmetadata aanvullen op een opgeslagen record =====

    def vul_bronmetadata_aan(
        self,
        definitie_id: int,
        *,
        doc_id: str,
        url: Any,
        source_version: Any,
        locator: Any,
        actor: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Zet de opgegeven hyperlink/bronversie/vindplaats op de documentbronnen
        van het OPGESLAGEN record, zodat een bestaand record kan worden hertoetst.

        Volgorde: reviewer-identiteit → record → getoonde versie/bewerkbaarheid
        (F3) → validatie via de gedeelde domeinlaag (DEF-806-hyperlinkregel;
        ongeldig = zichtbaar afgewezen, niets geschreven) → D schrijft onder de
        versieguard. De opgave blijft herkenbaar als opgegeven metadata; de
        eerdere AI-beoordeling geldt daarna niet meer (vingerafdruk) en wordt
        bij de volgende toetsing opnieuw verkregen — er wordt niets goedgekeurd.
        """
        from domain.sources.bronmetadata import valideer_bronmetadata

        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        bewijs = record.get_source_evidence()
        if bewijs is None:
            return {
                "status": "no_evidence",
                "message": "Geen opgeslagen bronbewijs bij dit record; er is niets aan te vullen.",
            }
        documenten = [
            b
            for b in bewijs.get("sources") or []
            if isinstance(b, Mapping)
            and str(b.get("provider") or "").casefold() in ("documents", "document")
            and str(b.get("doc_id") or "") == str(doc_id or "")
        ]
        if not documenten:
            return {
                "status": "no_matching_source",
                "message": f"Geen documentbron met id {doc_id!r} in het opgeslagen bewijs.",
            }
        metadata, fouten = valideer_bronmetadata(
            url,
            source_version,
            locator,
            declared_by=actor,
            bestaand=documenten[0].get("declared_metadata"),
        )
        if metadata is None:
            return {
                "status": "invalid",
                "errors": fouten,
                "message": "Bronmetadata niet vastgelegd: " + "; ".join(fouten),
            }
        try:
            toepassing = self.repository.vul_bronmetadata_aan(
                definitie_id,
                str(doc_id),
                metadata.als_dict(),
                actor,
                expected_version=record.version_number,
            )
        except ValueError as e:
            return {"status": "invalid", "errors": [str(e)], "message": str(e)}
        self._clear_cache(definitie_id)
        return {
            "status": toepassing.status,
            "version_number": toepassing.version_number,
            "aantal_bronnen": toepassing.aantal_bronnen,
            "message": toepassing.reason
            or (
                f"Bronmetadata vastgelegd op {toepassing.aantal_bronnen} passage(s) van "
                "dit document als opgegeven metadata. Een eerdere bronbeoordeling geldt "
                "niet meer: valideer opnieuw."
                if toepassing.ok
                else toepassing.status
            ),
        }

    @staticmethod
    def _canonieke_bronnen_met_passage(
        bronnen: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        from domain.sources.normalisatie import canoniseer_bronnen

        uit: list[dict[str, Any]] = []
        for bron in canoniseer_bronnen(bronnen):
            d = bron.als_dict()
            d["passage"] = bron.passage
            uit.append(d)
        return uit

    @staticmethod
    def _weergavecontrole(
        record: Any, expected_version: int | None
    ) -> dict[str, Any] | None:
        """F3: de getoonde versie en de actuele bewerkbaarheid, vóór elke aanroep.

        De UI geeft de recordversie mee die de gebruiker vóór zich had; wijkt
        het opgeslagen record daarvan af, dan is het antwoord een
        versieconflict — nooit stil de nieuwste versie. Een intussen
        vastgesteld of gearchiveerd record is niet bewerkbaar.
        """
        if expected_version is not None and record.version_number != expected_version:
            return {
                "status": "version_conflict",
                "message": (
                    f"De definitie is intussen gewijzigd (getoond: versie "
                    f"{expected_version}, opgeslagen: versie {record.version_number}); "
                    "ververs en beoordeel de actuele versie opnieuw."
                ),
                "version_number": record.version_number,
            }
        if str(getattr(record, "status", "") or "") in ("established", "archived"):
            return {
                "status": "not_editable",
                "message": (
                    f"De definitie heeft status '{record.status}' en is niet bewerkbaar; "
                    "zet haar via de Expert-tab terug naar Concept."
                ),
                "version_number": record.version_number,
            }
        return None

    def _actievoorbereiding(
        self, definitie_id: int, actor: str, expected_version: int | None
    ) -> DefinitieRecord | dict[str, Any]:
        """Gedeelde aanloop van aanvragen/toepassen/afwijzen, in vaste volgorde:
        reviewer-identiteit → record → weergaveversie/bewerkbaarheid (F3).
        Geeft het record, of de weigering (dict) die de aanroeper teruggeeft."""
        if not (actor or "").strip():
            return {
                "status": "no_actor",
                "message": "Een reviewer-identiteit is vereist.",
            }
        record = self.repository.get_definitie(definitie_id)
        if record is None:
            return {"status": "not_found", "message": "Definitie niet gevonden."}
        geweigerd = self._weergavecontrole(record, expected_version)
        if geweigerd is not None:
            return geweigerd
        return record

    @staticmethod
    def _reserveringsweigering(reservering: Any, diagnose: Any) -> dict[str, Any]:
        """De reservering bij D is niet gelukt: geen modelaanroep, met reden."""
        return {
            "status": reservering.status,
            "diagnose": diagnose.als_dict(),
            "message": reservering.reason
            or {
                "attempt_consumed": "Voor deze generatie is al een voorstel aangevraagd "
                "(maximaal één poging per generatie, DEF-638).",
                "version_conflict": "De definitie is intussen gewijzigd; ververs en "
                "probeer opnieuw.",
                "no_evidence": "Geen opgeslagen bronbewijs bij dit record.",
            }.get(reservering.status, reservering.status),
            "proposal_id": getattr(reservering, "proposal_id", None),
        }

    async def vraag_verbetervoorstel(
        self,
        definitie_id: int,
        *,
        actor: str,
        huidig_resultaat: Mapping[str, Any] | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Expliciete aanvraag van één verbetervoorstel (DEF-743, besluit 2).

        Volgorde: oorzaak bepalen (H) → alléén bij een aantoonbare
        tekortkoming een duurzame reservering bij D (max één poging per
        oorspronkelijke generatie) → één modelaanroep → uitkomst
        (`proposed|blocked|error`) vastleggen. De oorspronkelijke tekst
        wordt hier nooit gewijzigd. Geen dienst/geen reservering ⇒ geen
        aanroep, met een expliciete reden.
        """
        from services.source_proposal_service import diagnose_bronbasis

        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        try:
            basis = self.bronbasis_van_record(record, huidig_resultaat)
        except Exception as e:
            logger.error("Bronbasis niet te bepalen: %s", e, exc_info=True)
            return {
                "status": "error",
                "message": f"Bronbasis niet te bepalen: {type(e).__name__}: {e}",
            }
        diagnose = diagnose_bronbasis(
            basis["con02"],
            basis["assessment"],
            validation_status=basis["validation_status"],
            receipt=basis["receipt"],
        )
        if not diagnose.voorstel_mogelijk:
            # Geen modelaanroep en geen reservering: de poging blijft
            # beschikbaar tot er wél een aantoonbare tekortkoming met bewijs is.
            return {
                "status": "blocked",
                "diagnose": diagnose.als_dict(),
                "message": diagnose.toelichting,
                "proposal_id": None,
            }
        if self.proposal_service is None:
            return {
                "status": "unavailable",
                "diagnose": diagnose.als_dict(),
                "message": "Geen voorsteldienst beschikbaar (AI-service niet geconfigureerd).",
            }

        reservering = self.repository.reserve_source_proposal(
            definitie_id, updated_by=actor, expected_version=record.version_number
        )
        # D-contract: bij `reserved` zijn proposal_id en version_number gezet;
        # zonder die binding is er niets om een uitkomst aan vast te leggen —
        # dan geen modelaanroep (fail-closed, dezelfde weigering).
        proposal_id = reservering.proposal_id
        gereserveerde_versie = reservering.version_number
        if (
            reservering.status != "reserved"
            or proposal_id is None
            or gereserveerde_versie is None
        ):
            return self._reserveringsweigering(reservering, diagnose)

        try:
            voorstel = await self.proposal_service.stel_voor(
                begrip=record.begrip or "",
                tekst=basis["tekst"],
                contexten=basis["contexten"],
                bronnen=self._canonieke_bronnen_met_passage(basis["bronnen"]),
                con02=basis["con02"],
                assessment=basis["assessment"],
                peildatum=basis["peildatum"],
                validation_status=basis["validation_status"],
                receipt=basis["receipt"],
            )
        except Exception as e:
            # F7: de reservering staat al; een onverwachte fout in de dienst
            # wordt als duurzame `error`-uitkomst vastgelegd (poging verbruikt,
            # geen herhaling) — zonder prompt- of brontekst in de melding.
            logger.error(
                "Voorsteldienst faalde onverwacht: %s", type(e).__name__, exc_info=True
            )
            from services.source_proposal_service import Voorstel

            voorstel = Voorstel(
                status="error",
                diagnose=diagnose,
                error={
                    "type": "unexpected",
                    "message": f"{type(e).__name__} in de voorsteldienst",
                },
                findings=diagnose.bevindingen,
            )
        vastgelegd = self.repository.record_source_proposal_outcome(
            definitie_id,
            proposal_id,
            voorstel.als_outcome(),
            updated_by=actor,
            expected_version=gereserveerde_versie,
        )
        if not vastgelegd:
            logger.error(
                "Voorsteluitkomst niet vastgelegd (definitie %s, voorstel %s)",
                definitie_id,
                proposal_id,
            )
        self._clear_cache(definitie_id)
        return {
            "status": voorstel.status,
            "proposal_id": proposal_id,
            "diagnose": voorstel.diagnose.als_dict(),
            "candidate_text": voorstel.candidate_text,
            "rationale": voorstel.rationale,
            "behouden": list(voorstel.behouden),
            "onzekerheid": voorstel.onzekerheid,
            "error": voorstel.error,
            "recorded": bool(vastgelegd),
            "message": (
                "Voorstel beschikbaar; de oorspronkelijke tekst is ongewijzigd."
                if voorstel.status == "proposed"
                else voorstel.rationale
                or (voorstel.error or {}).get("message")
                or voorstel.status
            ),
        }

    def _async_validate_text(self) -> Any | None:
        """De async `validate_text` van de geïnjecteerde validatiedienst, of None."""
        vs = self.validation_service
        if vs is None:
            return None
        fn = getattr(vs, "validate_text", None)
        if fn is None:
            fn = getattr(getattr(vs, "validation_service", None), "validate_text", None)
        return fn

    @staticmethod
    def _beoordelingsfout(v: Mapping[str, Any]) -> str | None:
        """Ontbrekende of niet-uitgevoerde bronbeoordeling in de hertoetsing."""
        beoordeling = v.get("source_assessment")
        if not isinstance(beoordeling, Mapping):
            return "geen bronbeoordeling in het hertoetsingsresultaat"
        if beoordeling.get("status") != "assessed":
            return (
                f"bronbeoordeling niet uitgevoerd (status {beoordeling.get('status')})"
            )
        return None

    @classmethod
    def _technische_fout_in_validatie(cls, v: Mapping[str, Any]) -> str | None:
        """Reden waarom een hertoetsing niet als bewijs kan dienen, of None.

        DEF-624: alleen een expliciete `validated` is een uitgevoerde run;
        een afwezige, null of ongeldige status is geen runbewijs.
        """
        from services.validation.interfaces import UNKNOWN_REASON_RULESET_INCOMPLETE
        from services.validation.result_contract import bepaal_runstatus

        runstatus = bepaal_runstatus(v)
        if not runstatus.uitgevoerd:
            if runstatus.reason == UNKNOWN_REASON_RULESET_INCOMPLETE:
                return "validatie niet te bepalen (regelset onvolledig)"
            return (
                "validatie niet te bepalen (geen geldig runbewijs: "
                f"validation_status {runstatus.reason or 'onbekend'})"
            )
        if _als_mapping(v.get("system")).get("degraded_mode"):
            return "validatie draaide in beperkte modus"
        if _als_mapping(v.get("rule_statuses")).get("CON-02") == "error":
            return "bronbeoordeling technisch mislukt (CON-02: error)"
        beoordelingsfout = cls._beoordelingsfout(v)
        if beoordelingsfout is not None:
            return beoordelingsfout
        dekking = v.get("evaluation_coverage")
        if isinstance(dekking, Mapping) and int(dekking.get("error") or 0):
            return f"{dekking.get('error')} regel(s) met technische fout"
        return None

    @staticmethod
    def _toepasbare_kandidaat(
        record: DefinitieRecord, proposal_id: str
    ) -> str | dict[str, Any]:
        """De kandidaattekst van een toepasbaar voorstel, of de weigering.

        Vaste volgorde: voorstel bestaat → status `proposed` → origineel is
        nog de opgeslagen tekst (anders `stale_original`) → kandidaattekst.
        """
        voorstel = record.get_source_proposal(proposal_id)
        if not isinstance(voorstel, dict):
            return {"status": "not_found", "message": "Voorstel niet gevonden."}
        if voorstel.get("status") != "proposed":
            return {
                "status": "invalid_status",
                "message": f"Voorstel heeft status '{voorstel.get('status')}' en is niet toepasbaar.",
            }
        origineel = _als_dict(voorstel.get("original"))
        if origineel.get("text") != record.get_definitie_tekst():
            return {
                "status": "stale_original",
                "message": "De definitietekst is gewijzigd sinds het voorstel; het voorstel "
                "is verouderd.",
            }
        uitkomst = _als_dict(voorstel.get("outcome"))
        kandidaat = str(uitkomst.get("candidate_text") or "").strip()
        if not kandidaat:
            return {
                "status": "invalid_status",
                "message": "Voorstel bevat geen kandidaattekst.",
            }
        return kandidaat

    async def _hertoets_kandidaat(
        self, definitie_id: int, record: DefinitieRecord, kandidaat: str
    ) -> Mapping[str, Any] | _Weigering:
        """Hertoets de kandidaat met DEZELFDE bronset via de async
        `validate_text`. Geeft het volledige validatieresultaat, of een
        `technical_error`-weigering wanneer de hertoetsing niet als bewijs kan
        dienen (het origineel blijft dan intact)."""
        import inspect

        from services.validation.interfaces import ValidationContext

        # De geïnjecteerde dienst is in productie de DefinitionOrchestratorV2
        # (met `.validation_service` = ValidationOrchestratorV2) of direct de
        # validatie-orchestrator; beide leveren de async `validate_text`.
        fn = self._async_validate_text()
        if fn is None or not inspect.iscoroutinefunction(fn):
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": "Geen asynchrone validatiedienst beschikbaar voor hertoetsing.",
                }
            )
        geladen = self.repository.get(definitie_id)
        geladen_meta = dict(getattr(geladen, "metadata", None) or {})
        contexten = record.get_contextlijsten()
        kandidaat_def = Definition(
            id=definitie_id,
            begrip=record.begrip or "",
            definitie=kandidaat,
            organisatorische_context=list(
                contexten.get("organisatorische_context") or []
            ),
            juridische_context=list(contexten.get("juridische_context") or []),
            wettelijke_basis=list(contexten.get("wettelijke_basis") or []),
            categorie=record.categorie,
        )
        vc = ValidationContext(
            correlation_id=None,
            metadata=bouw_validatiecontext(kandidaat_def, geladen_meta),
        )
        try:
            v = await fn(
                begrip=kandidaat_def.begrip,
                text=kandidaat,
                ontologische_categorie=record.categorie,
                context=vc,
            )
        except Exception as e:
            logger.error("Hertoetsing van voorstel mislukt: %s", e, exc_info=True)
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": f"Hertoetsing mislukt: {type(e).__name__}: {e}",
                }
            )
        if not isinstance(v, Mapping):
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": "Hertoetsing gaf geen resultaat.",
                }
            )
        fout = self._technische_fout_in_validatie(v)
        if fout:
            return _Weigering(
                {
                    "status": "technical_error",
                    "message": f"Hertoetsing niet bruikbaar als bewijs: {fout}. "
                    "De oorspronkelijke tekst blijft staan.",
                    "validation": dict(v),
                }
            )
        return v

    async def pas_voorstel_toe(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        actor: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Neem een opgeslagen voorstel over: hertoets mét dezelfde bronset,
        daarna atomair opslaan bij D tegen de getoonde versie.

        Een verouderd of vervalst voorstel wordt geweigerd; een technische
        fout in de hertoetsing laat het origineel intact (het voorstel blijft
        `proposed`, de reden wordt gemeld). Nooit een oude pass behouden: D
        slaat de nieuwe volledige validatie en bronbeoordeling op.
        """
        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        kandidaat = self._toepasbare_kandidaat(record, proposal_id)
        if isinstance(kandidaat, dict):
            return kandidaat
        hertoetsing = await self._hertoets_kandidaat(definitie_id, record, kandidaat)
        if isinstance(hertoetsing, _Weigering):
            return hertoetsing.payload
        v = hertoetsing
        toepassing = self.repository.apply_source_proposal(
            definitie_id,
            proposal_id,
            updated_by=actor,
            expected_version=record.version_number,
            source_assessment=dict(v["source_assessment"]),
            validation=dict(v),
        )
        self._clear_cache(definitie_id)
        return {
            "status": toepassing.status,
            "version_number": getattr(toepassing, "version_number", None),
            "message": getattr(toepassing, "reason", None)
            or (
                "Voorstel toegepast en opnieuw getoetst."
                if toepassing.status == "applied"
                else toepassing.status
            ),
            "validation": dict(v),
            "candidate_text": kandidaat,
        }

    def wijs_voorstel_af(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        actor: str,
        note: str | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Wijs een voorstel expliciet af (status bewaard als bewijs)."""
        voorbereid = self._actievoorbereiding(definitie_id, actor, expected_version)
        if isinstance(voorbereid, dict):
            return voorbereid
        record = voorbereid
        ok = self.repository.set_source_proposal_status(
            definitie_id,
            proposal_id,
            "rejected",
            actor,
            expected_version=record.version_number,
            note=note,
        )
        self._clear_cache(definitie_id)
        return {
            "status": "rejected" if ok else "version_conflict",
            "message": (
                "Voorstel afgewezen."
                if ok
                else "Afwijzen niet vastgelegd: versie gewijzigd of voorstel niet toepasbaar."
            ),
        }

    def _generate_session_id(self, definitie_id: int, user: str) -> str:
        """Generate unique session ID."""
        import hashlib

        timestamp = datetime.now().isoformat()
        data = f"{definitie_id}_{user}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()

    def _format_timestamp(self, timestamp: str | datetime | Any) -> str:
        """Format timestamp for display."""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return str(timestamp)

        if isinstance(timestamp, datetime):
            delta = datetime.now() - timestamp
            if delta.days > 7:
                return timestamp.strftime("%d-%m-%Y %H:%M")
            if delta.days > 0:
                return f"{delta.days} dagen geleden"
            if delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} uur geleden"
            if delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minuten geleden"
            return "Zojuist"

        return str(timestamp)

    def _generate_change_summary(self, entry: dict[str, Any]) -> str:
        """Generate human-readable change summary."""
        wijziging_type = entry.get("wijziging_type", "")
        gewijzigd_door = entry.get("gewijzigd_door", "Onbekend")

        summaries = {
            "created": f"Aangemaakt door {gewijzigd_door}",
            "updated": f"Bewerkt door {gewijzigd_door}",
            "status_changed": f"Status gewijzigd door {gewijzigd_door}",
            "approved": f"Goedgekeurd door {gewijzigd_door}",
            "archived": f"Gearchiveerd door {gewijzigd_door}",
            "auto_save": "Auto-save",
        }

        return summaries.get(wijziging_type, f"Gewijzigd door {gewijzigd_door}")

    def _definition_to_dict(self, definition: Definition) -> dict[str, Any]:
        """Convert Definition to dictionary."""
        return {
            "begrip": definition.begrip,
            "definitie": definition.definitie,
            "toelichting": definition.toelichting,
            "bron": definition.bron,
            "organisatorische_context": getattr(
                definition, "organisatorische_context", []
            ),
            "juridische_context": getattr(definition, "juridische_context", []),
            "wettelijke_basis": getattr(definition, "wettelijke_basis", []),
            "categorie": definition.categorie,
            **(definition.metadata if definition.metadata else {}),
        }

    def _clear_cache(self, definitie_id: int | None = None) -> None:
        """Clear cache entries."""
        if definitie_id:
            # Clear specific definition cache
            keys_to_remove = [k for k in self._cache if str(definitie_id) in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear all cache
            self._cache.clear()
