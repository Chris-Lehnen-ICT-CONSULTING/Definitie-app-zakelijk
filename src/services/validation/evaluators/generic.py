"""Generieke declaratieve evaluator (DEF-606 / ADR-001).

Draagt de declaratieve regelwerking die vandaag in
`ModularValidationService._evaluate_json_rule` staat: verboden patronen,
vereiste patronen, verboden frasen, lengtegrenzen, circulariteit,
zinsstructuur en redundantie. Het gedrag is één-op-één overgenomen, zodat
het invoeren van het evaluatorcontract geen regelbetekenis verschuift.

Bewust NIET meegenomen: de STR-01-tak uit `_evaluate_json_rule` die na
`':'` op `^(is|de|het|een|wordt|betreft)\\\\b` matchte. Dat patroon bevat een
dubbele escape en zoekt daardoor naar een letterlijke backslash gevolgd
door `b`; de tak kon nooit matchen. Weglaten is gedragsidentiek. De vraag
of de body-check alsnog moet worden geïmplementeerd staat als bevinding bij
DEF-624; `additional_patterns['STR-01']` dekt vandaag de variant op de
volledige tekst.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
    Finding,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord
from validation.additional_patterns import get_additional_patterns

__all__ = ["GenericEvaluator", "PatroonUitkomst", "verzamel_generieke_bevindingen"]


@dataclass(frozen=True)
class PatroonUitkomst:
    """Bevindingen plus patroontreffers van de declaratieve pijplijn."""

    findings: tuple[Finding, ...]
    pattern_hits: tuple[str, ...]
    first_hit_pattern: str | None
    first_hit_pos: int | None

    def met(self, extra: tuple[Finding, ...]) -> PatroonUitkomst:
        return PatroonUitkomst(
            findings=(*self.findings, *extra),
            pattern_hits=self.pattern_hits,
            first_hit_pattern=self.first_hit_pattern,
            first_hit_pos=self.first_hit_pos,
        )


def _gecompileerde_patronen(
    code: str, record: RuleRecord, deps: EvaluationDeps
) -> list[re.Pattern[str]]:
    gecached = deps.pattern_cache.get(code)
    if gecached is not None:
        return list(gecached)

    patronen = list(record.get("herkenbaar_patronen", []) or [])
    extra = get_additional_patterns(code)
    if extra:
        patronen = list(dict.fromkeys([*patronen, *extra]))
    # Geen foutafhandeling: `build_rule_record` heeft de compileerbaarheid al
    # afgedwongen, en de hardgecodeerde `additional_patterns` hebben hun eigen
    # guard. Blijkt een patroon hier tóch onbruikbaar, dan is dat een
    # contractbreuk die naar de ERROR-grens in de service moet doorlopen. De
    # oude `except re.error: gecompileerd = []` zette álle patronen van de
    # regel uit én cachete die leegte procesbreed (DEF-667).
    gecompileerd = [re.compile(pat, re.IGNORECASE) for pat in patronen]
    deps.pattern_cache[code] = gecompileerd
    return list(gecompileerd)


def verzamel_generieke_bevindingen(
    record: RuleRecord,
    ctx: EvaluationContext,
    deps: EvaluationDeps,
    *,
    patronen_zijn_positief: bool = False,
) -> PatroonUitkomst:
    """Draai de declaratieve pijplijn over één regelrecord.

    `patronen_zijn_positief` schakelt de verboden-patroonmelding uit voor
    regels waar een treffer juist een gewenst signaal is (CON-02, ESS-03,
    ESS-04, ESS-05). De treffers worden dan nog wél geteld, omdat ze de
    scoreberekening beïnvloeden — precies zoals in de huidige evaluator.
    """
    code = record.rule_id.upper()
    text = ctx.cleaned_text or ""
    text_norm = text.strip()
    woorden = len(text_norm.split()) if text_norm else 0
    tekens = len(text_norm)
    findings: list[Finding] = []

    # 1) Verboden regexpatronen
    treffers: list[str] = []
    eerste_patroon: str | None = None
    eerste_positie: int | None = None
    for patroon in _gecompileerde_patronen(code, record, deps):
        for match in patroon.finditer(text):
            treffers.append(patroon.pattern)
            if eerste_positie is None or match.start() < eerste_positie:
                eerste_positie = match.start()
                eerste_patroon = patroon.pattern

    if treffers and not patronen_zijn_positief:
        lijst = ", ".join(sorted(set(treffers)))
        findings.append(
            Finding(
                message=f"Verboden patroon gedetecteerd: {lijst}",
                reason="forbidden_patterns",
                details=lijst,
            )
        )

    # 2) Vereiste patronen
    vereiste_patronen = list(record.get("required_patterns", []) or [])
    if vereiste_patronen:
        vereist_gecompileerd = [re.compile(p, re.IGNORECASE) for p in vereiste_patronen]
        if not any(p.search(text) for p in vereist_gecompileerd):
            findings.append(
                Finding(
                    message="Vereist patroon niet gevonden",
                    reason="required_patterns",
                    details=", ".join(vereiste_patronen),
                )
            )

    # 3) Verboden frasen (substring)
    for frase in record.get("forbidden_phrases", []) or []:
        if frase and frase in text_norm:
            findings.append(
                Finding(
                    message=f"Verboden term: '{frase}'",
                    reason="forbidden_phrase",
                    details=frase,
                )
            )

    # 4) Numerieke grenzen
    findings.extend(_numerieke_bevindingen(record, woorden, tekens))

    # 5) Circulariteit (begrip letterlijk in de definitie)
    if record.get("circular_definition"):
        begrip = ctx.begrip or None
        if begrip and re.search(
            rf"\b{re.escape(str(begrip))}\b", text_norm, re.IGNORECASE
        ):
            findings.append(
                Finding(
                    message="Circulaire definitie: begrip komt letterlijk voor",
                    reason="circular",
                    details=str(begrip),
                )
            )

    # 6) Zinsstructuur: veel komma's én te lang
    min_kommas = record.get("min_commas")
    max_tekens = record.get("max_chars")
    if isinstance(min_kommas, int) and isinstance(max_tekens, int):
        if text_norm.count(",") >= min_kommas and tekens > max_tekens:
            findings.append(
                Finding(
                    message=(
                        f"Zinsstructuur: veel komma's (≥{min_kommas}) en te lang "
                        f"(> {max_tekens} tekens)"
                    ),
                    reason="structure_runon",
                    details=f"{min_kommas}|{max_tekens}",
                )
            )

    # 7) Redundantie/tegenstrijdigheid
    for patroon_tekst in record.get("redundancy_patterns", []) or []:
        samengesteld = re.compile(patroon_tekst, re.IGNORECASE)
        if samengesteld.search(text_norm):
            findings.append(
                Finding(
                    message="Redundantie/tegenstrijdigheid gedetecteerd",
                    reason="redundancy",
                    details=patroon_tekst,
                )
            )
            break

    return PatroonUitkomst(
        findings=tuple(findings),
        pattern_hits=tuple(treffers),
        first_hit_pattern=eerste_patroon,
        first_hit_pos=eerste_positie,
    )


def _numerieke_bevindingen(
    record: RuleRecord, woorden: int, tekens: int
) -> list[Finding]:
    grenzen: list[tuple[str, Any, str, str, bool]] = [
        (
            "min_words",
            record.get("min_words"),
            "Te weinig woorden (min %s)",
            "min_words",
            True,
        ),
        (
            "max_words",
            record.get("max_words"),
            "Te veel woorden (max %s)",
            "max_words",
            False,
        ),
        (
            "min_chars",
            record.get("min_chars"),
            "Te weinig tekens (min %s)",
            "min_chars",
            True,
        ),
        (
            "max_chars",
            record.get("max_chars"),
            "Te veel tekens (max %s)",
            "max_chars",
            False,
        ),
    ]
    bevindingen: list[Finding] = []
    for naam, waarde, sjabloon, reden, is_minimum in grenzen:
        if not isinstance(waarde, int) or isinstance(waarde, bool):
            continue
        gemeten = woorden if naam.endswith("words") else tekens
        overtreden = gemeten < waarde if is_minimum else gemeten > waarde
        if overtreden:
            bevindingen.append(
                Finding(
                    message=sjabloon % waarde,
                    reason=reden,
                    details=str(waarde),
                )
            )
    return bevindingen


def uitkomst_van(uitkomst: PatroonUitkomst) -> EvaluationOutcome:
    """Zet verzamelde bevindingen om in een pass/fail-uitkomst."""
    if not uitkomst.findings:
        return EvaluationOutcome.passed()
    return EvaluationOutcome(
        status=ResultStatus.FAIL,
        findings=uitkomst.findings,
        pattern_hits=uitkomst.pattern_hits,
        first_hit_pattern=uitkomst.first_hit_pattern,
        first_hit_pos=uitkomst.first_hit_pos,
    )


class GenericEvaluator:
    """Declaratieve regels: patronen, frasen, grenzen, circulariteit."""

    evaluator_type = EvaluatorType.GENERIC

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        return uitkomst_van(verzamel_generieke_bevindingen(record, ctx, deps))
