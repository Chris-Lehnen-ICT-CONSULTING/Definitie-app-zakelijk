"""ESS-04 (DEF-767, W1 B–E): toetsbaarheid is een menselijk oordeel.

Echte service, echte regelrecords, geen provider. De casussen komen uit het
ESS-04-casusregister v2/v3 (onderzoek 18 september 2026) en zijn synthetische
regressie-invoer, geen deskundig gevalideerde goldset.

Wat deze tests bewijzen:

- B (T2-5a): de evaluator zet ESS-04 op het bestaande passagemechanisme
  (`_reden_met_passages`) met eigen normkop en een neutrale passagevraag;
  zonder treffer draagt de reden de toetsvraag, bij twee treffers staan
  beide passages in tekstvolgorde met elk de vaste slotzin. Status en score
  veranderen niet; ESS-01/ESS-02 blijven zichzelf.
- C (T2-5b): de gedeelde UI toont de open ESS-04-reden letterlijk (`st.text`),
  met én zonder treffer; een andere oordeelregel blijft achter de toggle.
- D (T2-5c): de renderer verzint geen heuristische pass-verklaring
  ('vereist element herkend') meer voor ESS-04.
- E (H2-2): de cijfergerichte herstelhint (termijn/meetgrens) is vervangen
  door een betekenisgerichte hint, uitsluitend op het oude aanroeppunt.

Wat ze niet bewijzen: een opgeslagen menselijk oordeel of een
vaststelroute (DEF-624/626/627).
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from services.validation import modular_validation_service as mvs_module
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.judgment_review import JudgmentReviewEvaluator
from services.validation.modular_validation_service import ModularValidationService
from services.validation.types_internal import EvaluationContext
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import RequiredInput, ResultStatus, build_rule_record
from ui.components import validation_view
from ui.components.validation_renderer import ValidationRenderer
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"


def _ruw(rule_id: str) -> dict:
    return json.loads((REGELS_DIR / f"{rule_id}.json").read_text(encoding="utf-8"))


ESS01 = build_rule_record("ESS-01", _ruw("ESS-01"))
ESS02 = build_rule_record("ESS-02", _ruw("ESS-02"))
ESS04 = build_rule_record("ESS-04", _ruw("ESS-04"))

#: Regex-artefacten die nooit als eindgebruikersverklaring mogen verschijnen.
REGEX_ARTEFACTEN = ("\\b", "\\s", "\\w", "(?", "^\\")

#: R-01: de normkop eindigt op een dubbele punt als scheidingsteken.
NORMKOP = "ESS-04 — Toetsbaarheid:"

#: ESS04-C04: één patroontreffer ('binnen 3 dagen'); het getal bewijst niets.
MET_TREFFER = ("aanvraag", "Belangrijke aanvraag die binnen 3 dagen relevant wordt.")
#: ESS04-C03: kwalitatief criterium zonder enig patroonsignaal.
ZONDER_TREFFER = ("veelhoek", "Veelhoek waarvan alle zijden even lang zijn.")
#: Twee verschillende patronen in één tekst ('binnen 3 dagen' en 'bevat').
#: Alleen hier doen de sortering, de dedup en de join van
#: `_reden_met_passages` werkelijk werk; met één treffer is dat pad blind.
TWEE_TREFFERS = (
    "aanvraag",
    "Aanvraag die binnen 3 dagen wordt afgehandeld en een toelichting bevat.",
)

#: D: zonder eigen ESS-04-tak valt `_build_pass_reason` terug op zijn
#: generieke slotregel — positief vast te pinnen, anders laat elke
#: teruggezette tak met andere woorden de test groen.
GENERIEKE_PASSVERKLARING = "Geen issues gemeld door validator."
#: ESS-05 is de enige overgebleven ESS-tak met een heuristische verklaring.
ESS05_PASSVERKLARING = "Vereist element herkend (heuristiek)."

OUDE_HINT = (
    "Maak een objectief toetsbaar element expliciet (bijv. termijn of meetbare grens)."
)
NIEUWE_HINT = (
    "Benoem welk criterium onvoldoende bepaald is en welke betekenisgrond nodig "
    "is. Gebruik alleen een onderbouwde kwalitatieve of kwantitatieve afbakening; "
    "voeg geen termijn of grens toe om een signaal te verkrijgen."
)


class _StubSupport:
    def severity_for(self, rule):
        return "error"

    def severity_level_for(self, rule):
        return "critical"

    def build_suggestion(self, code, rule, text, ctx, *, reason, details=None):
        return "stub"


def _deps() -> EvaluationDeps:
    return EvaluationDeps(
        support=_StubSupport(),
        available_inputs=frozenset(RequiredInput),
        pattern_cache={},
    )


def _ctx(begrip: str, tekst: str) -> EvaluationContext:
    return EvaluationContext(raw_text=tekst, cleaned_text=tekst, begrip=begrip)


def _evalueer(record, begrip: str, tekst: str):
    return JudgmentReviewEvaluator().evaluate(record, _ctx(begrip, tekst), _deps())


class TestEvaluatorPassagehulp:
    """B — T2-5a."""

    def test_met_treffer_wijst_de_passage_aan_met_de_neutrale_vraag(self):
        uitkomst = _evalueer(ESS04, *MET_TREFFER)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        reden = uitkomst.reason or ""
        assert reden.startswith(f"{NORMKOP} Te beoordelen passage: binnen 3 dagen. ")
        assert (
            "Nog te beoordelen. Leg vast hoe het criterium 'binnen 3 dagen' op een "
            "geval wordt toegepast." in reden
        )
        assert uitkomst.metadata.get("signals")
        # Een treffer is nooit een oordeel: geen pass/fail, geen regex als uitleg.
        assert "voldoet" not in reden.lower()
        for artefact in REGEX_ARTEFACTEN:
            assert artefact not in reden, f"regex als verklaring: {reden!r}"

    def test_zonder_treffer_draagt_de_reden_de_toetsvraag(self):
        uitkomst = _evalueer(ESS04, *ZONDER_TREFFER)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert not uitkomst.metadata.get("signals")
        toetsvraag = str(ESS04.get("toetsvraag"))
        assert "betekenisgrond" in toetsvraag
        assert uitkomst.reason == f"{NORMKOP} Nog te beoordelen. {toetsvraag}"
        # De oude toetsvraag ('objectief kunt vaststellen') is weg.
        assert "objectief" not in uitkomst.reason

    def test_twee_signalen_leveren_beide_passages_in_tekstvolgorde(self):
        """Het meervoudige pad: volgorde, join en slotzin per passage.

        Met één treffer doen `sorted`, `dict.fromkeys` en `" ".join` geen
        werk. Pas bij twee fragmenten is te zien dat de passages op
        tekstpositie staan — niet alfabetisch, want dan zou 'bevat' vóór
        'binnen 3 dagen' komen — en dat elk fragment zijn eigen vraag en
        slotzin krijgt in plaats van één slotzin voor het geheel.
        """
        uitkomst = _evalueer(ESS04, *TWEE_TREFFERS)
        assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
        assert uitkomst.score is None
        assert uitkomst.violation is None
        assert len(uitkomst.metadata.get("signals") or ()) == 2
        reden = uitkomst.reason or ""
        assert reden == (
            f"{NORMKOP} "
            "Te beoordelen passage: binnen 3 dagen. Nog te beoordelen. Leg vast "
            "hoe het criterium 'binnen 3 dagen' op een geval wordt toegepast. "
            "Dit signaal geeft nog geen inhoudelijk oordeel. "
            "Te beoordelen passage: bevat. Nog te beoordelen. Leg vast hoe het "
            "criterium 'bevat' op een geval wordt toegepast. Dit signaal geeft "
            "nog geen inhoudelijk oordeel."
        )
        assert reden.count("Dit signaal geeft nog geen inhoudelijk oordeel.") == 2
        assert "voldoet" not in reden.lower()
        for artefact in REGEX_ARTEFACTEN:
            assert artefact not in reden, f"regex als verklaring: {reden!r}"

    def test_de_reviewvraag_is_altijd_aanwezig(self):
        for begrip, tekst in (MET_TREFFER, ZONDER_TREFFER):
            reden = _evalueer(ESS04, begrip, tekst).reason or ""
            assert reden.startswith(NORMKOP)
            assert "Nog te beoordelen." in reden

    def test_ess01_en_ess02_houden_hun_eigen_kop_en_mechanisme(self):
        for record, kop in ((ESS01, "ESS-01 — Nog te beoordelen"), (ESS02, "ESS-02 —")):
            for begrip, tekst in (MET_TREFFER, ZONDER_TREFFER):
                uitkomst = _evalueer(record, begrip, tekst)
                assert uitkomst.status is ResultStatus.REVIEW_REQUIRED
                reden = uitkomst.reason or ""
                assert reden.startswith(kop)
                assert NORMKOP not in reden
                assert "Leg vast hoe het criterium" not in reden
        # Zonder signaal blijft de bestaande ESS-01-afsluiting staan.
        zonder = _evalueer(ESS01, *ZONDER_TREFFER).reason or ""
        assert zonder.endswith(
            "Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig."
        )


def _svc() -> ModularValidationService:
    return ModularValidationService(get_toetsregel_manager(), None, None)


def _vang_streamlit(monkeypatch) -> dict[str, list[str]]:
    shown = {
        api: []
        for api in ("markdown", "info", "warning", "success", "error", "write", "text")
    }
    for api in shown:
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, _api=api, **kw: shown[_api].append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    return shown


class TestWeergave:
    """C — T2-5b: open status + reviewvraag + reden altijd zichtbaar, letterlijk."""

    @pytest.mark.parametrize(
        ("casus", "begrip", "tekst"),
        [("met treffer", *MET_TREFFER), ("zonder treffer", *ZONDER_TREFFER)],
    )
    async def test_open_ess04_reden_wordt_letterlijk_getoond(
        self, monkeypatch, casus, begrip, tekst
    ):
        result = await _svc().validate_definition(begrip=begrip, text=tekst, context={})
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-04")
        shown = _vang_streamlit(monkeypatch)
        SessionStateManager.set_value("def767_show_validation_details", False)
        validation_view.render_validation_detailed_list(result, key_prefix="def767")
        # Passages zijn gebruikersinvoer: letterlijk via st.text, niet als markdown.
        assert item["reason"] in shown["text"], casus
        assert item["reason"].startswith(NORMKOP)
        assert "Nog te beoordelen." in item["reason"]
        for api, values in shown.items():
            if api != "text":
                assert item["reason"] not in "\n".join(values)

    async def test_andere_oordeelregel_blijft_achter_de_toggle(self, monkeypatch):
        result = await _svc().validate_definition(
            begrip=MET_TREFFER[0], text=MET_TREFFER[1], context={}
        )
        redenen = {r["rule_id"]: r["reason"] for r in result["review_required"]}
        assert "STR-03" in redenen  # oordeelregel zónder directe weergave
        shown = _vang_streamlit(monkeypatch)
        SessionStateManager.set_value("def767b_show_validation_details", False)
        validation_view.render_validation_detailed_list(result, key_prefix="def767b")
        assert redenen["STR-03"] not in "\n".join(shown["text"])
        assert redenen["ESS-04"] in shown["text"]


class TestRenderer:
    """D — T2-5c."""

    def test_geen_heuristische_passverklaring_meer_voor_ess04(self):
        # Positief vastgepind op de generieke slotregel. Alleen de drie
        # negatieve substrings hieronder lieten elke teruggezette tak met
        # andere woorden ('Patroon aangetroffen') groen door (review PR #468).
        renderer = ValidationRenderer()
        reden = renderer._build_pass_reason("ESS-04", MET_TREFFER[1], MET_TREFFER[0])
        assert reden == GENERIEKE_PASSVERKLARING
        assert "Vereist element herkend" not in reden
        assert "heuristiek" not in reden.lower()
        assert "getal" not in reden.lower()

    def test_ess05_houdt_zijn_bestaande_heuristiek(self):
        # Letterlijk: het schrappen van de ESS-04-tak mag de overgebleven
        # ESS-05-uitleg niet meeslepen of stil herformuleren.
        renderer = ValidationRenderer()
        assert (
            renderer._build_pass_reason(
                "ESS-05", "eigenschap die een entiteit onderscheidt", "kenmerk"
            )
            == ESS05_PASSVERKLARING
        )
        assert ESS05_PASSVERKLARING != GENERIEKE_PASSVERKLARING


class TestHerstelhint:
    """E — H2-2."""

    def test_nieuwe_hint_op_het_oude_aanroeppunt(self):
        tekst = MET_TREFFER[1]
        suggestie = _svc().build_suggestion(
            "ESS-04",
            _ruw("ESS-04"),
            tekst,
            _ctx(MET_TREFFER[0], tekst),
            reason="testable",
        )
        assert suggestie == NIEUWE_HINT
        assert "termijn of meetbare grens" not in suggestie
        assert "objectief toetsbaar element" not in suggestie

    def test_hint_hangt_niet_aan_iedere_review_required_status(self):
        tekst = MET_TREFFER[1]
        ctx = _ctx(MET_TREFFER[0], tekst)
        svc = _svc()
        # Een andere oorzaak op ESS-04 en dezelfde oorzaak op een andere regel
        # krijgen de ESS-04-hint niet.
        assert (
            svc.build_suggestion(
                "ESS-04", _ruw("ESS-04"), tekst, ctx, reason="forbidden_patterns"
            )
            != NIEUWE_HINT
        )
        assert (
            svc.build_suggestion(
                "ESS-05", _ruw("ESS-05"), tekst, ctx, reason="testable"
            )
            != NIEUWE_HINT
        )

    def test_oude_termijn_of_grenshint_komt_nergens_meer_voor(self):
        bron = inspect.getsource(mvs_module)
        assert "termijn of meetbare grens" not in bron
        assert OUDE_HINT not in bron

    async def test_geen_ess04_violation_of_autoherstel_in_het_resultaat(self):
        result = await _svc().validate_definition(
            begrip=MET_TREFFER[0], text=MET_TREFFER[1], context={}
        )
        assert not any(v.get("code") == "ESS-04" for v in result["violations"])
        item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-04")
        assert "suggestion" not in item
        suggesties = [v.get("suggestion") or "" for v in result["violations"]]
        assert not any("termijn of meetbare grens" in s for s in suggesties)
