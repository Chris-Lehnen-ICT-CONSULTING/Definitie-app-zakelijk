"""DEF-772 WP2: het INT-03-regelrecord draagt de besloten norm (K1, K4, K6).

Bron: besluiten-chris-v1.md (K1(a), K4(i–iii), K6) en synthese-v2 §1 van het
INT-03-onderzoek van 25 september 2026. Alle verwachtingen hieronder zijn uit
die bron afgeleid, niet uit het gedrag van de implementatie.

Wat deze tests bewijzen:

- het record draagt de exacte uitleg, toelichting en toetsvraag (K1(a): geen
  "dezelfde zin of zinsdeel", geen woordsoorteis, antecedent "in de
  definitie");
- het ASTRA-paar is behouden; twee goede en drie foute voorbeelden zijn
  toegevoegd; het vierde synthesevoorstel ("… over zijn besluit") is een
  testgeval en géén JSON-voorbeeld (plan-oplossing van de 3/4-inconsistentie);
- type/geldigheid/brondocument zijn "term"/"alle"/"ASTRA (Ross, DBT 4.3)";
- de patroonlijst (K4): 'in het kader' en 'inzienelijk maken' zijn weg, de
  bestaande verwijsvormen blijven, de deze/dit/die/daarvan-uitzondering staat
  nog op één plek (het record; `additional_patterns` draagt INT-03 niet meer),
  en het/dat/hij/zij/hem/diens/zijn/haar/hun/ervan/hiervan/daarmee zijn als
  laag-precisiesignaal toegevoegd;
- beide laadpaden (ToetsregelManager en CachedToetsregelManager → RuleCache)
  leveren hetzelfde record;
- het runtimecontract wijst sinds WP3 (K2 T-c) de eigen verwijzingsevaluator
  aan (`pronoun_reference_assessment`, automatisch, `excluded_from_score`):
  zonder voorbereide beoordeling — zoals in deze directe service-aanroepen —
  is elke uitkomst expliciet "niet beoordeeld" (`review_required`), nooit
  pass/fail, nooit een cijfer, ook zonder enig signaalwoord; `pass` met de
  K7-motivering ontstaat uitsluitend ná een inhoudelijke beoordeling. De
  signalen uit `herkenbaar_patronen` reizen als zoekhulp mee in het
  gestructureerde `rule_results`-blok.

Ruiswaarschuwing (K4(iii), bewust gedocumenteerd): 'het' vuurt ook als
lidwoord en loos 'het', 'dat' ook als voegwoord, 'zijn' ook als werkwoord,
'die' ook op een correcte betrekkelijke bijzin. Een treffer is zoekhulp, geen
oordeel; geen treffer is geen goedkeuring. Deze tests trekken geen
semantische conclusie uit regexdekking.

Wat ze niet bewijzen: de inhoudelijke kwaliteit van de LLM-beoordeling
(WP6), UI/opslag/export (WP4). De vier uitkomstcategorieën, de binding en
het niet-blokkeren staan in `test_def772_int03_evaluator.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import get_cached_toetsregel_manager
from toetsregels.manager import get_toetsregel_manager
from toetsregels.rule_cache import _RECORD_DEFAULTS, get_rule_cache
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    ExamplePairPolicy,
    Executability,
    RequiredInput,
    ScorePolicy,
    build_rule_record,
)
from validation.additional_patterns import (
    all_additional_patterns,
    get_additional_patterns,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"

#: Afzonderlijke, lemmavrije term voor alle serviceproeven: komt in geen enkel
#: voorbeeld voor, zodat CON-CIRC-001/ARAI-06 niet onbedoeld meespelen.
TERM = "proefbegrip"


def _ruw() -> dict:
    return json.loads((REGELS_DIR / "INT-03.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Exacte teksten (synthese-v2 §1; besluit K1(a))
# ---------------------------------------------------------------------------

UITLEG_K1 = (
    "Voor ieder voornaamwoord in de definitie is voor de lezer duidelijk waarnaar "
    "het verwijst."
)
TOELICHTING_K1 = (
    "Voornaamwoorden en voornaamwoordelijke bijwoorden ('het', 'hij', 'zij', "
    "'die', 'dat', 'dit', 'deze', 'zijn', 'haar', 'hun', 'diens', 'daarvan', "
    "'waarbij' …) verwijzen naar iets in de definitie. Bepaal eerst of een woord "
    "verwijzend gebruikt is: een lidwoord, loos 'het' of het voegwoord 'dat' "
    "verwijst niet. De lezer moet zonder context eenduidig kunnen vaststellen "
    "welk antecedent bedoeld is; dat mag een naamwoordgroep of grotere "
    "tekstinhoud zijn. Een betrekkelijke bijzin waarvan het antecedent eenduidig "
    "is ('persoon die …') voldoet; plaatsing direct na een naamwoord is niet "
    "voldoende als een ander naamwoord ook als antecedent kan worden gelezen. "
    "Meerdere naamwoorden bewijzen nog geen ambiguïteit: motiveer welke "
    "lezingen werkelijk plausibel zijn. Bij meer kandidaten: herhaal het "
    "bedoelde zelfstandig naamwoord ('die gebeurtenis', niet 'het') of "
    "herformuleer, met behoud van betekenis. Context, bronnen, toelichting of "
    "het lemma vervangen een ontbrekende verwijzing niet."
)
TOETSVRAAG_K1 = (
    "Welke verwijzend gebruikte woorden bevat de definitie en naar welk "
    "antecedent verwijst elk daarvan? Is dat voor de lezer zonder context "
    "eenduidig, of zijn er meer kandidaten of geen antecedent? Onderscheid "
    "onduidelijkheid van een nog ontbrekende beoordeling of ontbrekende "
    "herstelgrond."
)

#: ASTRA-paar (letterlijk, ongewijzigd; herkomst astra-INT-03-raw-20260925.txt).
ASTRA_GOED = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en "
    "geanalyseerd."
)
ASTRA_FOUT = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
)
GOED_EXTRA = [
    "persoon die wordt verdacht van een strafbaar feit",
    "teken dat een richting aangeeft",
]
FOUT_EXTRA = [
    "handeling van een medewerker aan een collega waarbij deze vertrekt",
    "verplichting van de werkgever om de werknemer over haar rechten te informeren",
    "voorziening waardoor het kan worden voortgezet",
]
#: Vierde synthesevoorstel (B): aanvullend testgeval, géén JSON-voorbeeld.
TESTGEVAL_B_ZIJN_BESLUIT = (
    "bericht van een medewerker aan een leidinggevende over zijn besluit"
)

#: K4: verwijderd (geen verwijzing) / behouden / toegevoegd (laag-precisie).
VERWIJDERDE_WOORDGROEPEN = ["in het kader", "inzienelijk maken"]
BEHOUDEN_VERWIJSVORMEN = [
    "deze",
    "dit",
    "die",
    "daarvan",
    "daarbij",
    "waarvan",
    "waarmee",
    "waarbij",
]
NIEUWE_SIGNAALWOORDEN = [
    "het",
    "dat",
    "hij",
    "zij",
    "hem",
    "diens",
    "zijn",
    "haar",
    "hun",
    "ervan",
    "hiervan",
    "daarmee",
]


def _patronen(record: dict | None = None) -> list[str]:
    return list((record or _ruw()).get("herkenbaar_patronen") or [])


def _gecompileerd(record: dict | None = None) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in _patronen(record)]


def _fragmenten(tekst: str, record: dict | None = None) -> list[str]:
    """De letterlijk getroffen fragmenten (kleine letters), uit álle patronen."""
    return sorted(
        {
            m.group(0).lower()
            for patroon in _gecompileerd(record)
            for m in patroon.finditer(tekst)
        }
    )


def _patronen_die_vuren(tekst: str, record: dict | None = None) -> list[str]:
    return [p.pattern for p in _gecompileerd(record) if p.search(tekst)]


# ---------------------------------------------------------------------------
# K1: regeltekst
# ---------------------------------------------------------------------------


class TestRegeltekstK1:
    def test_uitleg_toelichting_en_toetsvraag_zijn_de_besloten_teksten(self):
        record = _ruw()
        assert record["uitleg"] == UITLEG_K1
        assert record["toelichting"] == TOELICHTING_K1
        assert record["toetsvraag"] == TOETSVRAAG_K1

    def test_lokale_verscherpingen_zijn_verdwenen(self):
        # K1(a): "dezelfde zin of zinsdeel" en de woordsoorteis vervallen; de
        # oude uitleg ("mogen geen voornaamwoorden bevatten") was een verbod
        # dat ASTRA niet stelt.
        record = _ruw()
        samen = " ".join(
            str(record.get(veld) or "")
            for veld in ("uitleg", "toelichting", "toetsvraag")
        )
        assert "dezelfde zin of zinsdeel" not in samen
        assert "welk zelfstandig naamwoord bedoeld is" not in samen
        assert "mogen geen voornaamwoorden bevatten" not in samen
        assert "direct duidelijk is waarnaar verwezen wordt" not in samen

    def test_toelichting_benoemt_de_k6_uitzonderingen(self):
        # K6(2): loos 'het' en voegwoord 'dat' verwijzen niet; K6(1): bijzin
        # met eenduidig antecedent voldoet; K6(5): lemma repareert niet.
        toelichting = _ruw()["toelichting"]
        assert "loos 'het' of het voegwoord 'dat' verwijst niet" in toelichting
        assert "('persoon die …') voldoet" in toelichting
        assert "het lemma vervangen een ontbrekende verwijzing niet" in toelichting

    def test_naam_en_id_ongewijzigd(self):
        record = _ruw()
        assert record["id"] == "INT_03"
        assert record["naam"] == "Voornaamwoord-verwijzing duidelijk"


# ---------------------------------------------------------------------------
# Voorbeelden
# ---------------------------------------------------------------------------


class TestVoorbeelden:
    def test_astra_paar_behouden_en_twee_goede_drie_foute_toegevoegd(self):
        record = _ruw()
        assert record["goede_voorbeelden"] == [ASTRA_GOED, *GOED_EXTRA]
        assert record["foute_voorbeelden"] == [ASTRA_FOUT, *FOUT_EXTRA]

    def test_vierde_synthesevoorstel_is_testgeval_en_geen_json_voorbeeld(self):
        # Plan-oplossing van de 3/4-inconsistentie: "bericht … over zijn
        # besluit" leeft hier als testgeval (zie TestSignaaldekking).
        record = _ruw()
        assert TESTGEVAL_B_ZIJN_BESLUIT not in record["foute_voorbeelden"]
        assert TESTGEVAL_B_ZIJN_BESLUIT not in record["goede_voorbeelden"]
        assert len(record["foute_voorbeelden"]) == 4

    def test_voorbeelden_zijn_lemmavrij(self):
        # Geen term/lemma in de voorbeeldzinnen: elk voorbeeld is een kale
        # definitiekern, zodat een proef met een afzonderlijke term geen
        # buurregel (CON-CIRC-001, ARAI-06) onbedoeld raakt.
        record = _ruw()
        for voorbeeld in [*record["goede_voorbeelden"], *record["foute_voorbeelden"]]:
            assert ":" not in voorbeeld, voorbeeld
            assert not re.match(
                r"^(een|de|het)\s+\w+\s+is\b", voorbeeld, re.I
            ), voorbeeld
            assert TERM not in voorbeeld.lower()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_type_geldigheid_en_brondocument(self):
        record = _ruw()
        assert record["type"] == "term"
        assert record["geldigheid"] == "alle"
        assert record["brondocument"] == "ASTRA (Ross, DBT 4.3)"

    def test_overige_metadata_ongewijzigd(self):
        record = _ruw()
        assert record["prioriteit"] == "hoog"
        assert record["aanbeveling"] == "verplicht"
        assert record["status"] == "definitief"
        assert record["thema"] == "interne kwaliteit van de definitie"
        assert record["relatie"] == [
            {
                "fulltext": "Voornaamwoord-verwijzing duidelijk",
                "fullurl": "https://www.astraonline.nl/index.php/Voornaamwoord-verwijzing_duidelijk",
            }
        ]


# ---------------------------------------------------------------------------
# K4: patroonlijst — uitsluitend signaal
# ---------------------------------------------------------------------------


class TestPatroonlijstK4:
    def test_record_compileert_en_bouwt_onder_het_contract(self):
        build_rule_record("INT-03", _ruw())

    def test_niet_verwijzende_woordgroepen_zijn_verwijderd(self):
        # K4(i): 'in het kader' en 'inzienelijk maken' zijn geen verwijzing;
        # ARAI-05 is geen vangnet, maar dat maakt ze nog geen INT-03-signaal.
        for patroon in _patronen():
            for woordgroep in VERWIJDERDE_WOORDGROEPEN:
                assert woordgroep not in patroon, patroon
        # Het losse lidwoord 'het' vuurt wel (laag-precisie), maar géén
        # woordgroeppatroon: de treffer is het woord, niet de groep.
        assert _fragmenten("activiteit in het kader van toezicht") == ["het"]
        assert _fragmenten("maatregel om gevolgen inzienelijk maken") == []

    @pytest.mark.parametrize("woord", BEHOUDEN_VERWIJSVORMEN, ids=str)
    def test_bestaande_verwijsvorm_blijft_een_signaal(self, woord):
        assert _fragmenten(f"regeling {woord} een aanvraag betreft") == [woord]

    @pytest.mark.parametrize("woord", NIEUWE_SIGNAALWOORDEN, ids=str)
    def test_nieuw_signaalwoord_vuurt_als_heel_woord(self, woord):
        # K4(iii): laag-precisiesignaal, geen oordeel. Alleen op het hele
        # woord: 'hem' niet in 'geheim', 'zij' niet in 'zijde', 'dat' niet
        # in 'datum'.
        assert _fragmenten(f"regeling waarna {woord} vertrekt") == [woord]
        assert _fragmenten(f"regeling waarna {woord}x vertrekt") == []

    def test_samengestelde_woorden_vuren_niet(self):
        assert _fragmenten("geheim datum zijde hemel diensten hunkering") == []

    def test_uitzondering_staat_alleen_in_het_record(self):
        # K4(ii): de dubbele deze/dit/die/daarvan-uitzondering op één plek —
        # het JSON-record is de bron van waarheid; de Python-mapping draagt
        # INT-03 niet meer (dezelfde lijn als CON-01 en INT-01).
        assert get_additional_patterns("INT-03") == []
        assert "INT-03" not in all_additional_patterns()
        # Op basis 5d3916c03 was de lookahead in Python dood: `\bdeze\b` uit
        # het record vuurde toch op 'deze definitie'. Nu is de uitzondering
        # werkzaam — en meetbaar, want zij zit in het record zelf.
        assert "deze" not in _fragmenten("term waarvoor deze definitie geldt")
        assert "deze" not in _fragmenten("voorschrift waarop deze regel ziet")
        assert "dit" not in _fragmenten("aanduiding van dit begrip")
        assert "die" not in _fragmenten("voorschrift dat die regel opheft")
        # Vóór een ander naamwoord blijft het woord een signaal.
        assert "deze" in _fragmenten("regeling waarna deze afspraak geldt")
        assert "dit" in _fragmenten("regeling waarna dit document geldt")
        assert "die" in _fragmenten("regeling waarna die afspraak geldt")

    def test_astra_paar_krijgt_verschillende_signalen(self):
        # Nulmeting (26f2374d): goed en fout gaven identieke signalen omdat
        # 'het' niet vuurde. Nu verschilt het signaalbeeld op precies het
        # woord waar ASTRA het paar op bouwt. Dat is dekking, geen oordeel.
        goed = _fragmenten(ASTRA_GOED)
        fout = _fragmenten(ASTRA_FOUT)
        assert "het" in fout
        assert "het" not in goed
        assert "die" in goed and "die" in fout

    def test_ruiswaarschuwing_lidwoord_voegwoord_werkwoord(self):
        # Gedocumenteerde ruis (K4(iii)): het patroon kan de taalfunctie niet
        # onderscheiden. Een treffer hier is géén overtreding — de uitkomst
        # blijft in WP2 altijd review_required (TestRuntimecontractOngewijzigd).
        assert "het" in _fragmenten("register van het bestuursorgaan")  # lidwoord
        assert "het" in _fragmenten("regeling waarbij het verboden is")  # loos
        assert "dat" in _fragmenten("verklaring dat een aanvraag volledig is")  # vw
        assert "zijn" in _fragmenten("stukken die door de aanvrager zijn ingediend")
        assert "die" in _fragmenten(GOED_EXTRA[0])  # correcte bijzin
        assert "dat" in _fragmenten(GOED_EXTRA[1])  # correcte bijzin


class TestSignaaldekking:
    """Dekking op de voorbeelden en het testgeval — regexfeit, geen oordeel."""

    @pytest.mark.parametrize(
        ("tekst", "verwacht"),
        [
            (FOUT_EXTRA[0], "deze"),
            (FOUT_EXTRA[1], "haar"),
            (FOUT_EXTRA[2], "het"),
            (TESTGEVAL_B_ZIJN_BESLUIT, "zijn"),
            (ASTRA_FOUT, "het"),
        ],
        ids=[
            "deze-vertrekt",
            "haar-rechten",
            "het-voortgezet",
            "zijn-besluit",
            "astra",
        ],
    )
    def test_fout_voorbeeld_draagt_het_besproken_signaalwoord(self, tekst, verwacht):
        # Nulmeting: 'haar', 'zijn' en 'het' vuurden niet (A/B/C/D).
        assert verwacht in _fragmenten(tekst)

    def test_geen_signaalwoord_geeft_lege_signalen(self):
        # Geen treffer is géén goedkeuring: K7 ('pass' met motivering n.v.t.)
        # komt uitsluitend ná de LLM-controle, nooit op een lege patroonlijst
        # (zie TestRuntimecontractWP3).
        assert _fragmenten("veelhoek met precies drie zijden") == []


# ---------------------------------------------------------------------------
# Beide laadpaden
# ---------------------------------------------------------------------------


@pytest.fixture
def _verse_cache():
    # Geen stale FileCache-entries (TTL 1u, map cache/) uit een eerdere run
    # met het oude record; anders toont het productiepad een oude normversie.
    get_rule_cache().clear_cache()
    yield
    get_rule_cache().clear_cache()


class TestBeideLaadpaden:
    @staticmethod
    def _bronvelden(record: dict) -> dict:
        ruw = _ruw()
        extra = set(record) - set(ruw)
        assert extra <= set(_RECORD_DEFAULTS), extra
        return {veld: record[veld] for veld in ruw}

    @pytest.mark.usefixtures("_verse_cache")
    def test_load_regel_is_gelijk_via_beide_paden(self):
        via_manager = get_toetsregel_manager().load_regel("INT-03")
        via_cache = get_cached_toetsregel_manager().load_regel("INT-03")
        assert via_manager is not None and via_cache is not None
        assert via_manager == _ruw()
        assert self._bronvelden(via_cache) == _ruw()
        assert via_cache["uitleg"] == UITLEG_K1
        assert via_cache["toetsvraag"] == TOETSVRAAG_K1
        assert via_cache["goede_voorbeelden"] == [ASTRA_GOED, *GOED_EXTRA]
        assert via_cache["herkenbaar_patronen"] == _patronen()

    @pytest.mark.usefixtures("_verse_cache")
    def test_get_all_regels_is_gelijk_via_beide_paden(self):
        via_manager = get_toetsregel_manager().get_all_regels()["INT-03"]
        via_cache = get_cached_toetsregel_manager().get_all_regels()["INT-03"]
        assert via_manager == _ruw()
        assert self._bronvelden(via_cache) == _ruw()
        assert via_cache["brondocument"] == "ASTRA (Ross, DBT 4.3)"


# ---------------------------------------------------------------------------
# Runtimecontract: sinds WP3 de eigen verwijzingsevaluator (K2 T-c)
# ---------------------------------------------------------------------------


@pytest.fixture(params=["toetsregel_manager", "cached_manager (productiepad)"])
def svc(request, _verse_cache) -> ModularValidationService:
    if request.param.startswith("cached"):
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


async def _int03(
    svc: ModularValidationService, tekst: str, context: dict | None = None
) -> tuple[dict, dict]:
    """(volledig resultaat, het gestructureerde INT-03-blok in `rule_results`)."""
    res = await svc.validate_definition(
        begrip=TERM, text=tekst, context=dict(context or {})
    )
    return res, res["rule_results"]["INT-03"]


def _review_item(res: dict) -> dict:
    return next(r for r in res["review_required"] if r["rule_id"] == "INT-03")


class TestRuntimecontractWP3:
    def test_contract_wijst_de_verwijzingsevaluator_aan_zonder_score(self):
        record = build_rule_record("INT-03", _ruw())
        assert record.evaluator is EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT
        # De term is ondersteunend; alleen de definitietekst is vereist.
        assert record.required_inputs == (RequiredInput.DEFINITION_TEXT,)
        assert record.executability is Executability.JUDGMENT
        assert record.automation_status is AutomationStatus.AUTOMATED
        assert record.score_policy is ScorePolicy.EXCLUDED_FROM_SCORE
        assert record.example_pair_policy is ExamplePairPolicy.REVIEW_POLICY
        assert record.example_pair_issue == "DEF-772"
        assert record.counts_toward_score is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tekst",
        [ASTRA_GOED, *GOED_EXTRA, ASTRA_FOUT, *FOUT_EXTRA, TESTGEVAL_B_ZIJN_BESLUIT],
        ids=[
            "astra-goed",
            "goed-1",
            "goed-2",
            "astra-fout",
            "fout-1",
            "fout-2",
            "fout-3",
            "testgeval-b",
        ],
    )
    async def test_elk_voorbeeld_zonder_beoordeling_is_expliciet_open(self, svc, tekst):
        # Directe service-aanroep zonder voorbereide beoordeling: expliciet
        # niet beoordeeld — geen stil pass, geen inhoudelijke afkeur, geen cijfer.
        res, detail = await _int03(svc, tekst)
        assert res["rule_statuses"]["INT-03"] == "review_required"
        assert "INT-03" not in res["passed_rules"]
        assert not any(v.get("code") == "INT-03" for v in res["violations"])
        assert detail["status"] == "review_required"
        assert detail["score"] is None
        assert "niet beoordeeld" in detail["parts"][0]["reason"]
        assert "niet beoordeeld" in _review_item(res)["reason"]

    @pytest.mark.asyncio
    async def test_signalen_komen_uitsluitend_uit_het_record(self, svc):
        # Geen samengevoegd Python-patroon meer in de signalen: wat de
        # runtime meldt, staat letterlijk in `herkenbaar_patronen`. De
        # signalen zijn zoekhulp in het detail, geen oordeel.
        res, detail = await _int03(svc, "handeling waarna deze afspraak daarmee geldt")
        assert detail["signals"]
        assert set(detail["signals"]) <= set(_patronen())
        assert detail["signals"] == _patronen_die_vuren(
            "handeling waarna deze afspraak daarmee geldt"
        )
        assert _review_item(res)["signals"] == detail["signals"]

    @pytest.mark.asyncio
    async def test_astra_fout_meldt_het_als_signaal_en_astra_goed_niet(self, svc):
        _, fout = await _int03(svc, ASTRA_FOUT)
        _, goed = await _int03(svc, ASTRA_GOED)
        assert r"\bhet\b" in fout["signals"]
        assert r"\bhet\b" not in goed["signals"]

    @pytest.mark.asyncio
    async def test_zonder_signaalwoord_en_zonder_beoordeling_geen_pass(self, svc):
        # K7 ontstaat nooit op een lege patroonlijst: zonder inhoudelijke
        # beoordeling blijft de regel expliciet open.
        res, detail = await _int03(svc, "veelhoek met precies drie zijden")
        assert res["rule_statuses"]["INT-03"] == "review_required"
        assert detail["signals"] == []
        assert "INT-03" not in res["passed_rules"]

    @pytest.mark.asyncio
    async def test_pass_ontstaat_pas_na_inhoudelijke_beoordeling(self, svc):
        # K7: dezelfde tekst als hierboven, nu mét een (synthetische)
        # modelbeoordeling — dan pas 'pass' met exact de afgesproken motivering.
        from domain.int03.contract import (
            BEVINDING_GEEN_VERWIJZEND_WOORD,
            MOTIVERING_GEEN_VERWIJZEND_WOORD,
        )
        from tests.fixtures.def772_fakes import BINDING, bouw_int03_beoordeling

        tekst = "veelhoek met precies drie zijden"
        context = {
            "record_text": tekst,
            "int03_assessment": bouw_int03_beoordeling(
                TERM, tekst, {}, None, scenario="no_word"
            ),
            "int03_binding": BINDING.als_dict(),
        }
        res, detail = await _int03(svc, tekst, context)
        assert res["rule_statuses"]["INT-03"] == "pass"
        assert "INT-03" in res["passed_rules"]
        assert detail["parts"][0]["reason"] == MOTIVERING_GEEN_VERWIJZEND_WOORD
        assert detail["review"]["assessment"]["finding"] == (
            BEVINDING_GEEN_VERWIJZEND_WOORD
        )
        assert detail["score"] is None


# ---------------------------------------------------------------------------
# Promptkaart (WP1-keten): de nieuwe voorbeelden komen mee in de generatie
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_verse_cache")
def test_int03_kaart_toont_uitleg_en_alle_voorbeelden():
    from services.definition_generator_config import UnifiedGeneratorConfig
    from services.definition_generator_context import EnrichedContext
    from services.prompts.modules.base_module import ModuleContext

    module = JSONBasedRulesModule("INT", "integrity_rules", "INT", "🔒", "INT", 70)
    module.initialize({"include_examples": True})
    enriched = EnrichedContext(
        base_context={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )
    content = module.execute(
        ModuleContext(
            begrip=TERM,
            enriched_context=enriched,
            config=UnifiedGeneratorConfig(),
            shared_state={},
        )
    ).content
    kaart = content.split("🔹 **INT-03", 1)[1].split("🔹 **", 1)[0]
    assert f"- {UITLEG_K1}" in kaart
    for goed in (ASTRA_GOED, *GOED_EXTRA):
        assert f"✅ {goed}" in kaart
    for fout in (ASTRA_FOUT, *FOUT_EXTRA):
        assert f"❌ {fout}" in kaart
    assert TESTGEVAL_B_ZIJN_BESLUIT not in kaart
