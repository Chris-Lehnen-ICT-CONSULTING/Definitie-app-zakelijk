"""Oordeelregels: expliciet reviewplichtig, nooit stil geslaagd (DEF-624).

Twaalf regels hebben geen betrouwbare automatische toets:

- besluit DEF-624 (acht regels): ARAI-03, ESS-01, ESS-04, INT-02, INT-06,
  STR-03, STR-05 en STR-06;
- SAM-01, dat naast een oordeel ook de begrippenverzameling nodig heeft en
  daarom `definition_repository` als vereiste invoer declareert;
- projectuitbreiding: STR-08 en STR-09;
- DEF-750: ESS-02 (betekenisniveau en aard). Een markerwoord, precies één
  categoriehit of meerdere categoriewoorden bewijzen niets over de
  bedoelde betekenis; de regel draagt `score_policy: no_score`;
- DEF-767: ESS-04 (toetsbaarheid) draagt sinds besluit N2 een eigen
  passagehulp: een getal, termijn of signaalwoord bewijst geen toetsbaarheid
  en het ontbreken ervan is geen gebrek — kwalitatieve criteria kunnen
  volstaan. De regel was al reviewplichtig (`excluded_from_score`).

ESS-03 (telbaarheid) liep hier van 18 tot 21 september 2026 (DEF-766, eerste
uitvoeringsfase); sinds het besluit van 19/21 september beoordeelt de app die
regel zelf via de AI-telbaarheidsbeoordeling
(`services.validation.evaluators.countability_assessment`). INT-03
(voornaamwoord-verwijzing) liep hier tot 25 september 2026 (DEF-772 WP2,
projectuitbreiding); sinds besluit K2 T-c van die datum beoordeelt de app
die regel zelf via de AI-verwijzingsbeoordeling
(`services.validation.evaluators.pronoun_reference_assessment`).

Hun patronen blijven bruikbaar als *signaal* — ze wijzen de reviewer waar
te kijken — maar ze zijn geen *bewijs*: bij alle twaalf vuren de eigen
patronen ook op het gedocumenteerde goede voorbeeld, of missen ze het
gedocumenteerde foute voorbeeld volledig.

Dát het er twaalf zijn wordt bewaakt door
`tests/unit/validation/test_rule_runtime_matrix.py::TestAfgeleideTelling`:
die klasse leidt de klasseverdeling uit de records af en faalt zodra het
aantal `review_required`-regels verschuift. Zij legt alleen die telling
vast — niet de identiteit van de twaalf regels hierboven. Een canonieke,
hardgecodeerde lijst en de bijbehorende semantische dekking komen met
Batch 2 via DEF-623; die tests staan tot dan geparkeerd buiten `main`.

Daarom levert deze evaluator altijd `review_required`. Die uitkomst telt
niet mee in de kwaliteitsscore en wordt nooit als pass genormaliseerd; hij
verschijnt apart in de evaluatiedekking. Een algemene AI-jury voor deze
twaalf regels is bewust níet ingevoerd: dat vraagt per regel een
afzonderlijk besluit over prompt- en modelversie, goldset, privacy, kosten
en foutbeleid (ADR-001) — zoals voor CON-02 (DEF-743), ESS-03 (DEF-766) en
INT-03 (DEF-772) genomen is.
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
        code = record.rule_id.upper()
        signalen = self._signalen(record, ctx, deps)
        toetsvraag = str(record.get("toetsvraag") or record.get("naam") or "").strip()
        reden = toetsvraag or "Deze regel vereist een inhoudelijk oordeel."
        if code == "ESS-01":
            reden = self._ess01_reden(ctx, signalen)
        elif code == "ESS-02":
            reden = self._ess02_reden(ctx, signalen)
        elif code == "ESS-04":
            reden = self._ess04_reden(record, ctx, signalen)
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

    @classmethod
    def _ess04_reden(
        cls, record: RuleRecord, ctx: EvaluationContext, signalen: tuple[str, ...]
    ) -> str:
        """DEF-767 (T2-5a): toetsbaarheid is een menselijk oordeel (N2).

        De patronen wijzen hooguit een criteriumpassage aan (een termijn,
        een percentage, een signaalwoord); per passage staat de neutrale
        vraag hoe dat criterium op een geval wordt toegepast. Een treffer is
        geen 'voldoet niet', geen treffer is geen 'voldoet': kwalitatieve
        criteria kunnen volstaan. Zonder treffer draagt de reden de
        toetsvraag uit het record, zodat de reviewvraag altijd zichtbaar is.
        Toetsen verandert de tekst niet en start geen herstel.
        """
        toetsvraag = str(record.get("toetsvraag") or "").strip()
        return cls._reden_met_passages(
            "ESS-04 — Toetsbaarheid:",
            ctx,
            signalen,
            vraag="Nog te beoordelen. Leg vast hoe het criterium '{passage}' op een "
            "geval wordt toegepast.",
            zonder_signaal=f"Nog te beoordelen. {toetsvraag}".strip(),
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
        kop: str,
        ctx: EvaluationContext,
        signalen: tuple[str, ...],
        *,
        vraag: str,
        zonder_signaal: str = (
            "Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig."
        ),
    ) -> str:
        """Leesbare reden: de kop plus de letterlijk geciteerde passages.

        De regexpatronen zelf reizen als `signals` mee voor diagnostiek; de
        eindgebruiker krijgt uitsluitend de getroffen tekstfragmenten. In
        `vraag` wordt een letterlijke `{passage}` vervangen door het fragment
        (DEF-767); `zonder_signaal` is de tekst na de kop als geen patroon
        vuurt.
        """
        treffers = sorted(
            (hit.start(), hit.group())
            for patroon in signalen
            for hit in re.finditer(patroon, ctx.cleaned_text or "", re.IGNORECASE)
        )
        passages = dict.fromkeys(fragment for _, fragment in treffers)
        if not passages:
            return f"{kop} {zonder_signaal}"
        return (
            kop
            + " "
            + " ".join(
                f"Te beoordelen passage: {fragment}. "
                f"{vraag.replace('{passage}', fragment)} Dit signaal geeft nog geen "
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
