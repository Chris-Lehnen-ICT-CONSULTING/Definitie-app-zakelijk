"""Oordeelregels: expliciet reviewplichtig, nooit stil geslaagd (DEF-624).

Dertien regels hebben geen betrouwbare automatische toets:

- besluit DEF-624 (acht regels): ARAI-03, ESS-01, ESS-04, INT-02, INT-06,
  STR-03, STR-05 en STR-06;
- SAM-01, dat naast een oordeel ook de begrippenverzameling nodig heeft en
  daarom `definition_repository` als vereiste invoer declareert;
- projectuitbreiding: INT-03, STR-08 en STR-09;
- DEF-750: ESS-02 (betekenisniveau en aard). Een markerwoord, precies één
  categoriehit of meerdere categoriewoorden bewijzen niets over de
  bedoelde betekenis; de regel draagt `score_policy: no_score`.

Hun patronen blijven bruikbaar als *signaal* — ze wijzen de reviewer waar
te kijken — maar ze zijn geen *bewijs*: bij alle dertien vuren de eigen
patronen ook op het gedocumenteerde goede voorbeeld, of missen ze het
gedocumenteerde foute voorbeeld volledig.

Dát het er dertien zijn wordt bewaakt door
`tests/unit/validation/test_rule_runtime_matrix.py::TestAfgeleideTelling`:
die klasse leidt de klasseverdeling uit de records af en faalt zodra het
aantal `review_required`-regels verschuift. Zij legt alleen die telling
vast — niet de identiteit van de dertien regels hierboven. Een canonieke,
hardgecodeerde lijst en de bijbehorende semantische dekking komen met
Batch 2 via DEF-623; die tests staan tot dan geparkeerd buiten `main`.

Daarom levert deze evaluator altijd `review_required`. Die uitkomst telt
niet mee in de kwaliteitsscore en wordt nooit als pass genormaliseerd; hij
verschijnt apart in de evaluatiedekking. Een gecontroleerde AI-jury is
bewust níet ingevoerd: dat vraagt een afzonderlijk besluit over prompt- en
modelversie, goldset, privacy, kosten en foutbeleid (ADR-001).
"""

from __future__ import annotations

import re

from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import EvaluatorType, RuleRecord
from validation.additional_patterns import get_additional_patterns

__all__ = ["JudgmentReviewEvaluator"]


class JudgmentReviewEvaluator:
    """Menselijk oordeel vereist; patronen zijn hooguit een aanwijzing."""

    evaluator_type = EvaluatorType.JUDGMENT_REVIEW

    def evaluate(
        self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> EvaluationOutcome:
        signalen = self._signalen(record, ctx, deps)
        toetsvraag = str(record.get("toetsvraag") or record.get("naam") or "").strip()
        reden = toetsvraag or "Deze regel vereist een inhoudelijk oordeel."
        code = record.rule_id.upper()
        if code == "ESS-01":
            reden = self._ess01_reden(ctx, signalen)
        elif code == "ESS-02":
            reden = self._ess02_reden(ctx, signalen)
        return EvaluationOutcome.review_required(reden, signals=signalen)

    @classmethod
    def _ess01_reden(cls, ctx: EvaluationContext, signalen: tuple[str, ...]) -> str:
        """A: citeer passages in het bestaande redenveld; geen inhoudelijk oordeel."""
        return cls._reden_met_passages(
            "ESS-01 — Nog te beoordelen: welke kenmerken bepalen de betekenis van "
            "dit begrip? Beoordeel eventuele functie- of doelkenmerken en leg de grond vast.",
            ctx,
            signalen,
            vraag="Bepaalt deze passage het begrip of beschrijft zij een doel, "
            "gebruik of verband?",
        )

    @classmethod
    def _ess02_reden(cls, ctx: EvaluationContext, signalen: tuple[str, ...]) -> str:
        """DEF-750: betekenisniveau en aard zijn een menselijk oordeel.

        Een opgegeven categorielabel of markerwoord is een te controleren
        betekenisclaim en wordt als registratie genoemd, nooit als bewijs.
        De patronen wijzen hooguit een passage aan (niveau-aanduiding in de
        kick-off of een expliciet alternatief tussen activiteit en uitkomst);
        geen treffer is geen 'voldoet', een treffer is geen 'voldoet niet'.
        """
        kop = (
            "ESS-02 — Nog te beoordelen: maakt de definitiekern met voldoende grond "
            "duidelijk welke betekenis en welk betekenisniveau bedoeld zijn (algemeen "
            "begrip of één bepaald ding of voorval; waar relevant activiteit of "
            "uitkomst)? Een categorielabel of markerwoord is hiervoor onvoldoende; "
            "beoordeel de kern met de onderbouwde bedoeling."
        )
        label = cls._opgegeven_categorie(ctx)
        if label:
            kop += (
                f" Registratie: opgegeven categorie '{label}' is een te controleren "
                "betekenisclaim, geen bewijs dat de kern klopt."
            )
        return cls._reden_met_passages(
            kop,
            ctx,
            signalen,
            vraag="Wijst deze passage op een niveau-aanduiding of op een keuze "
            "tussen betekenislagen, of benoemt zij slechts een gerelateerde zaak?",
        )

    @staticmethod
    def _opgegeven_categorie(ctx: EvaluationContext) -> str | None:
        """Het label uit de aanroepmetadata, als leesbare registratie (geen bewijs)."""
        metadata = ctx.metadata if isinstance(ctx.metadata, dict) else {}
        for sleutel in ("ontologische_categorie", "categorie", "marker"):
            waarde = metadata.get(sleutel)
            if isinstance(waarde, str) and waarde.strip():
                return waarde.strip()
        return None

    @staticmethod
    def _reden_met_passages(
        kop: str, ctx: EvaluationContext, signalen: tuple[str, ...], *, vraag: str
    ) -> str:
        """Leesbare reden: de kop plus de letterlijk geciteerde passages.

        De regexpatronen zelf reizen als `signals` mee voor diagnostiek; de
        eindgebruiker krijgt uitsluitend de getroffen tekstfragmenten.
        """
        treffers = sorted(
            (hit.start(), hit.group())
            for patroon in signalen
            for hit in re.finditer(patroon, ctx.cleaned_text or "", re.IGNORECASE)
        )
        passages = dict.fromkeys(fragment for _, fragment in treffers)
        if not passages:
            return (
                kop
                + " Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig."
            )
        return (
            kop
            + " "
            + " ".join(
                f"Te beoordelen passage: {fragment}. {vraag} Dit signaal geeft nog geen "
                "inhoudelijk oordeel."
                for fragment in passages
            )
        )

    @staticmethod
    def _signalen(
        record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> tuple[str, ...]:
        code = record.rule_id.upper()
        sleutel = f"__judgment__{code}"
        gecompileerd = deps.pattern_cache.get(sleutel)
        if gecompileerd is None:
            patronen = list(record.get("herkenbaar_patronen", []) or [])
            extra = get_additional_patterns(code)
            if extra:
                patronen = list(dict.fromkeys([*patronen, *extra]))
            # Zie generic.py: compileerbaarheid is bij het laden afgedwongen;
            # een fout hier is een contractbreuk die naar de ERROR-grens moet
            # doorlopen in plaats van de signalen stil weg te laten (DEF-667).
            gecompileerd = [re.compile(p, re.IGNORECASE) for p in patronen]
            deps.pattern_cache[sleutel] = gecompileerd

        tekst = ctx.cleaned_text or ""
        return tuple(
            patroon.pattern for patroon in gecompileerd if patroon.search(tekst)
        )
