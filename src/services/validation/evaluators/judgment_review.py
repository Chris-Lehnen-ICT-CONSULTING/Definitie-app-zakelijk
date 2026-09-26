"""Oordeelregels: expliciet reviewplichtig, nooit stil geslaagd (DEF-624).

Dertien regels hebben geen betrouwbare automatische toets:

- besluit DEF-624 (acht regels): ARAI-03, ESS-01, ESS-04, INT-02, INT-06,
  STR-03, STR-05 en STR-06;
- SAM-01, dat naast een oordeel ook de begrippenverzameling nodig heeft en
  daarom `definition_repository` als vereiste invoer declareert;
- projectuitbreiding: INT-03, STR-08 en STR-09;
- DEF-750: ESS-02 (betekenisniveau en aard). Een markerwoord, precies één
  categoriehit of meerdere categoriewoorden bewijzen niets over de
  bedoelde betekenis; de regel draagt `score_policy: no_score`;
- DEF-767: ESS-04 (toetsbaarheid) draagt sinds besluit N2 een eigen
  passagehulp: een getal, termijn of signaalwoord bewijst geen toetsbaarheid
  en het ontbreken ervan is geen gebrek — kwalitatieve criteria kunnen
  volstaan. De regel was al reviewplichtig (`excluded_from_score`).
- DEF-771: INT-02 draagt een eigen passagehulp (O1): toetsvraag, per passage
  een neutrale vraag met citaat en positie in de getoetste kern; zonder kern
  of context `not_evaluated`. Signalen blijven leeshulp (B3).

ESS-03 (telbaarheid) liep hier van 18 tot 21 september 2026 (DEF-766, eerste
uitvoeringsfase); sinds het besluit van 19/21 september beoordeelt de app die
regel zelf via de AI-telbaarheidsbeoordeling
(`services.validation.evaluators.countability_assessment`).

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
verschijnt apart in de evaluatiedekking. Een algemene AI-jury voor deze
dertien regels is bewust níet ingevoerd: dat vraagt per regel een
afzonderlijk besluit over prompt- en modelversie, goldset, privacy, kosten
en foutbeleid (ADR-001) — zoals voor CON-02 (DEF-743) en ESS-03 (DEF-766)
genomen is.
"""

from __future__ import annotations

import re

from domain.int01.zinsgrenzen import segmenteer
from services.validation.evaluators.base import (
    EvaluationDeps,
    EvaluationOutcome,
)
from services.validation.types_internal import EvaluationContext
from toetsregels.runtime_contract import (
    EvaluatorType,
    RequiredInput,
    ResultStatus,
    RuleRecord,
)
from validation.additional_patterns import get_additional_patterns

__all__ = [
    "JudgmentReviewEvaluator",
    "int02_niet_uitgevoerd",
    "int02_niet_uitgevoerd_uitkomst",
]

# DEF-771: exacte meldingen uit synthese v5 §4 (skillcontract def771-int02/2).
_INT02_HULP = (
    "INT-02 — Nog te beoordelen. Beschrijft de passage '{zinsdeel}' een kenmerk "
    "of afgeleid feit, of schrijft zij voor wat iemand moet doen of afwegen? Leg "
    "de functie vast met grond uit de kern, de bevestigde bedoeling of een "
    "bronpassage. Behoud noodzakelijke criteria en uitzonderingen. Het signaal is "
    "geen oordeel; beoordeel ook passages zonder signaalwoord."
)
_INT02_ZONDER_SIGNAAL = (
    "INT-02 — Nog te beoordelen. Geen signaalwoord gevonden; een voorschrift of "
    "afweging kan ook zonder signaalwoord voorkomen. Beoordeel de hele kern op "
    "begripscriterium/afleiding tegenover voorschrift of afweging."
)
_INT02_NE = (
    "INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk "
    "oordeel."
)
#: Alleen een termlabel zoals 'Toegang:' is geen definitiekern (C23).
_LABEL_ZONDER_KERN = re.compile(r"[^:.!?;\n]{1,80}:")


def int02_niet_uitgevoerd(kern: str | None, context_aanwezig: bool) -> str | None:
    """De exacte NE-melding bij lege kern, los label of ontbrekende context."""
    tekst = (kern or "").strip()
    kern_ontbreekt = not tekst or bool(_LABEL_ZONDER_KERN.fullmatch(tekst))
    ontbreekt = [
        naam
        for naam, weg in (("kern", kern_ontbreekt), ("context", not context_aanwezig))
        if weg
    ]
    if not ontbreekt:
        return None
    return _INT02_NE.replace("{kern/context}", " en ".join(ontbreekt))


def int02_niet_uitgevoerd_uitkomst(
    melding: str, record: RuleRecord
) -> EvaluationOutcome:
    """`not_evaluated` met de NE-melding als publieke deeluitkomst (contract 2.2.0).

    Zonder oordeel: score en vingerafdruk null, geen review. De contractversie
    komt uit het actieve INT-02-record. De service boekt `rule_result` in
    `rule_results`, zodat de melding de gebruiker bereikt.
    """
    grond = melding.split("Niet uitgevoerd: ", 1)[1].split(" ontbreekt.", 1)[0]
    detail = {
        "status": "not_evaluated",
        "score": None,
        "contract_version": record.get("contractversie"),
        "fingerprint": None,
        "parts": [
            {
                "id": "invoer",
                "status": "not_evaluated",
                "evidence": None,
                "context_value": None,
                "field": None,
                "position": None,
                "reason": melding,
                "action": f"Lever de ontbrekende {grond} aan en toets opnieuw.",
            }
        ],
        "review": None,
    }
    return EvaluationOutcome(
        status=ResultStatus.NOT_EVALUATED,
        reason=melding,
        metadata={"rule_result": detail},
    )


def _int02_passage(kern: str, start: int, einde: int) -> tuple[int, int]:
    """De volledige dragende zin rond een treffer, als (start, einde) in `kern`.

    Grenzen: uitsluitend zekere zinsgrenzen van de INT-01-segmentatie. Een
    komma, puntkomma of dubbele punt is geen grens: een tussenzin, opsomming
    of ingebed criterium hoort bij de dragende zin (review WP5, R1). Bij een
    onzekere zinsgrens, of als alleen het markerwoord overblijft, wordt de
    volledige kern geciteerd.
    """
    segmentatie = segmenteer(kern)
    if segmentatie is None or segmentatie.onzekere_grenzen:
        return _bijgesneden(kern, 0, len(kern))
    grenzen = {grens.positie for grens in segmentatie.zekere_grenzen}
    begin = max((g + 1 for g in grenzen if g < start), default=0)
    eind = min((g for g in grenzen if g >= einde), default=len(kern))
    passage = _bijgesneden(kern, begin, eind)
    if kern[passage[0] : passage[1]].casefold() == kern[start:einde].casefold():
        return _bijgesneden(kern, 0, len(kern))
    return passage


def _bijgesneden(kern: str, begin: int, eind: int) -> tuple[int, int]:
    while begin < eind and kern[begin].isspace():
        begin += 1
    while eind > begin and (kern[eind - 1].isspace() or kern[eind - 1] in ".!?;:,"):
        eind -= 1
    return begin, eind


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
        elif code == "INT-02":
            niet_uitgevoerd = int02_niet_uitgevoerd(
                ctx.cleaned_text, deps.has(RequiredInput.CONTEXT_LISTS)
            )
            if niet_uitgevoerd:
                return int02_niet_uitgevoerd_uitkomst(niet_uitgevoerd, record)
            reden = self._int02_reden(toetsvraag, ctx, deps)
        return EvaluationOutcome.review_required(reden, signals=signalen)

    @staticmethod
    def _int02_reden(
        toetsvraag: str, ctx: EvaluationContext, deps: EvaluationDeps
    ) -> str:
        """DEF-771 (B2/B3, O1): toetsvraag plus per passage de neutrale vraag.

        Signalen zijn leeshulp: een treffer is nooit 'voldoet niet', geen
        treffer nooit 'voldoet'. Het citaat komt uit de getoetste kern
        (`cleaned_text`) en de positie slaat op diezelfde tekst; wijkt die af
        van de aangeleverde tekst, dan staat dat erbij. Meerdere markers in één
        zin delen één vraag; gelijke zinnen op andere posities niet.
        """
        kern = ctx.cleaned_text or ""
        reden = f"INT-02 — Toetsvraag: {toetsvraag}"
        patronen = deps.pattern_cache.get("__judgment__INT-02") or []
        spans = sorted(
            {
                _int02_passage(kern, hit.start(), hit.end())
                for patroon in patronen
                for hit in patroon.finditer(kern)
            }
        )
        if not spans:
            return f"{reden} {_INT02_ZONDER_SIGNAAL}"
        for start, einde in spans:
            reden += (
                f" {_INT02_HULP.replace('{zinsdeel}', kern[start:einde])} Positie in "
                f"de getoetste kern: {start}–{einde} (tekenposities, nulgebaseerd, "
                "einde exclusief)."
            )
        if kern != ctx.raw_text:
            reden += (
                " De posities gelden voor de getoetste kern, die afwijkt van de "
                "aangeleverde tekst."
            )
        return reden

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
