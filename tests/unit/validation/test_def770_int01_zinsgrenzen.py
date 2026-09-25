"""DEF-770 (INT-01): functionele zinsgrenzen in plaats van een woordlijst.

Bron: INT-01-onderzoek 23-09-2026 (synthese v3). Normatieve kern:

- afkeur op losse woorden ('die', 'en') en leestekens (komma, puntkomma)
  vervalt; het ASTRA-goedvoorbeeld 'eis die ...' en 'dr. Smit' zijn geen
  overtreding meer, een vraagzin plus tweede zin wel;
- een grens wordt naar haar functie beoordeeld: regelomloop is niet vanzelf
  een tweede zin, aanhalingstekens rond de hele kern maken twee zinnen niet
  één, een afkorting kan ook een zin afsluiten (dan onzeker), een puntkomma
  is geen zelfstandige grens;
- 'één zin vastgesteld' is een deelbevinding: compactheid en begrijpelijkheid
  zijn daarmee niet beoordeeld, dus de regel als geheel staat nooit stil op
  `pass` (geen groen volledig INT-01-oordeel), levert geen cijfer en blokkeert
  niet zelfstandig.

Alle verwachtingen hieronder zijn vooraf uit de onderzoeksbron afgeleid, niet
uit het gedrag van de implementatie.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

REGELPAD = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "toetsregels"
    / "regels"
    / "INT-01.json"
)

ASTRA_GOED = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
ASTRA_FOUT = (
    ASTRA_GOED + " In tegenstelling tot andere eisen vertegenwoordigen "
    "transitie-eisen tijdelijke behoeften, in plaats van meer permanente."
)


def _segmenteer(tekst: str):
    from services.validation.evaluators.sentence_boundary import segmenteer

    return segmenteer(tekst)


# (id, tekst, aantal zekere grenzen, aantal onzekere grenzen)
SEGMENTATIEGEVALLEN = [
    # Nulmeting A (26f2374d): E01/E04 faalden onterecht, E05 passeerde onterecht.
    ("E01-astra-goed", ASTRA_GOED, 0, 0),
    ("E02-dat", "Object dat gegevens bevat.", 0, 0),
    ("E03-die-geen-woordafkeur", "Object die gegevens bevat.", 0, 0),
    ("E04-dr-smit", "Document op naam van dr. Smit.", 0, 0),
    ("E05-vraagzin", "Wat is dit? Afgebakend object.", 1, 0),
    ("E06-twee-zinnen", "Afgebakend object. Heeft vaste vorm.", 1, 0),
    ("astra-fout", ASTRA_FOUT, 1, 0),
    ("uitroep", "Afgebakend object! Heeft vaste vorm.", 1, 0),
    # Noodzakelijke bijzin, nevenschikking, naam: geen INT-01-overtreding.
    (
        "bijzin-waarbij-die",
        (
            "activiteit waarbij een ambtenaar gegevens controleert, die volgens de "
            "wet vereist zijn."
        ),
        0,
        0,
    ),
    (
        "naam-met-en",
        "beleidsregel van het Ministerie van Justitie en Veiligheid over detentie.",
        0,
        0,
    ),
    # K4: puntkomma is geen zelfstandige zinsgrens.
    (
        "puntkomma-opsomming",
        (
            "sanctie bestaande uit een van de volgende straffen: gevangenisstraf; "
            "hechtenis; taakstraf; geldboete."
        ),
        0,
        0,
    ),
    ("getallen", "bedrag van 3,5 procent van 1.000 euro per jaar.", 0, 0),
    ("afkorting-bijv", "maatregel zoals bijv. een boete die de rechter oplegt.", 0, 0),
    ("afkorting-oa", "register met o.a. persoonsgegevens van verdachten.", 0, 0),
    ("afkorting-art", "besluit op grond van art. 3 van de wet.", 0, 0),
    # Reviewronde 2: een losse hoofdletter + hoofdletter is zonder
    # naamcontext niet te onderscheiden van een zinseinde ('categorie A.
    # Registratie ...'): zichtbaar onzeker, nooit stil één zin. Alleen na een
    # titel of een andere initiaal is de naamfunctie duidelijk.
    ("initiaal-zonder-naamcontext", "rapport van J. Jansen over detentie.", 0, 1),
    ("titel-initiaal-naam", "rapport van dr. J. Jansen over detentie.", 0, 0),
    ("twee-initialen-naam", "rapport van J. K. Jansen over detentie.", 0, 1),
    ("titel-twee-initialen", "rapport van dr. J. K. Jansen over detentie.", 0, 0),
    ("initiaal-tussenvoegsel", "rapport van J. de Vries over detentie.", 0, 0),
    ("haakjes-met-afkorting", "besluit (zie art. 4) van de minister.", 0, 0),
    ("getal-einde-zin", "termijn van 3 dagen. Het begint na ontvangst.", 1, 0),
    # Regelomloop is niet vanzelf een tweede zin (E07/EB02).
    ("omloop-E07", "Veelhoek met precies\ndrie zijden.", 0, 0),
    (
        "omloop-EB02",
        "Document met gegevens van de aanvrager\nen diens vertegenwoordiger.",
        0,
        0,
    ),
    # Afkorting die ook zinslot kan zijn: functie niet zeker (EB03).
    ("enz-slot-EB03", "Object met gegevens enz. Het wordt geregistreerd.", 0, 1),
    # Ingesloten citaat/titel: leestekens binnen het citaat vormen geen grens
    # van de buitenste zin (T17-herstel, def770-int01/2); haakjes blijven onzeker.
    (
        "ingesloten-citaat",
        "nota met de titel “Beleid. Uitvoering” van de minister.",
        0,
        0,
    ),
    (
        "ingesloten-vraagtitel",
        "rapport met de titel ‘Wie betaalt?’ van de commissie.",
        0,
        0,
    ),
    ("kleine-letter-na-punt", "Afgebakend object. heeft vaste vorm.", 0, 1),
    ("alinea-zonder-punt", "Afgebakend object\n\nHeeft vaste vorm", 0, 1),
    # Reviewbevinding 2: onvoldoende context om de grens uit te sluiten
    # (afkorting gevolgd door een getal; losse hoofdletter gevolgd door een
    # zinsbeginwoord) = zichtbaar onzeker, nooit stil één zin.
    ("enz-cijfer-review", "Object met gegevens enz. 3 velden zijn verplicht.", 0, 1),
    ("categorie-A-review", "Object in categorie A. Het wordt geregistreerd.", 0, 1),
    ("categorie-A-werkwoord", "Object in categorie A. Heeft een vaste vorm.", 0, 1),
    ("categorie-A-zelfstnw", "Object in categorie A. Registratie is verplicht.", 0, 1),
    ("titel-met-naam", "Document op naam van dr. Smit en mr. De Boer.", 0, 0),
    ("afkorting-voor-getal", "boete van ca. 3 procent per jaar.", 0, 0),
    # Tweede zin met noodzakelijk onderscheidend kenmerk blijft een tweede zin (EB04).
    (
        "tweede-zin-differentia-EB04",
        "Voertuig voor personenvervoer. Het heeft ten hoogste acht zitplaatsen.",
        1,
        0,
    ),
]


#: Citaatbeleid (herstel-20260924-v1/algemeen-citaatbesluit-v1.md, contract
#: /8): een kleine-lettervoortzetting na een citaatslot is altijd onzeker. De
#: oorspronkelijke tuple in SEGMENTATIEGEVALLEN blijft als historische
#: verwachting staan; dit is de geldende (zeker, onzeker).
CITAATBESLUIT = {"ingesloten-vraagtitel": (0, 1)}


class TestSegmentatie:
    @pytest.mark.parametrize(
        ("tekst", "zeker", "onzeker"),
        [
            pytest.param(t, *CITAATBESLUIT.get(i, (z, o)), id=i)
            for i, t, z, o in SEGMENTATIEGEVALLEN
        ],
    )
    def test_functionele_zinsgrenzen(self, tekst, zeker, onzeker):
        seg = _segmenteer(tekst)
        assert seg is not None
        assert len(seg.zekere_grenzen) == zeker, seg
        assert len(seg.onzekere_grenzen) == onzeker, seg

    def test_opsomming_met_opsommingstekens_is_onzeker_niet_zeker(self):
        seg = _segmenteer("sanctie bestaande uit:\n- gevangenisstraf\n- geldboete")
        assert not seg.zekere_grenzen
        assert seg.onzekere_grenzen, "lijststructuur mag niet stil wegvallen"

    def test_geheel_geciteerde_kern_telt_inhoudelijk(self):
        """E08/EB01: aanhalingstekens rond de hele kern maken twee zinnen niet één."""
        seg = _segmenteer("“Afgebakend object. Heeft vaste vorm.”")
        assert len(seg.zekere_grenzen) == 1
        assert seg.geheel_geciteerd is True
        gewoon = _segmenteer("Afgebakend object. Heeft vaste vorm.")
        assert gewoon.geheel_geciteerd is False

    def test_lege_tekst_is_niet_beoordeelbaar(self):
        assert _segmenteer("") is None
        assert _segmenteer("   \n ") is None

    @pytest.mark.parametrize(
        ("tekst", "fragmenten"),
        [
            ("Wat is dit? Afgebakend object.", ("dit?", "Afgebakend")),
            ("Afgebakend object. Heeft vaste vorm.", ("object.", "Heeft")),
            ("Object met gegevens enz. Het wordt geregistreerd.", ("enz.", "Het")),
            ("Object in categorie A. Heeft een vaste vorm.", ("A.", "Heeft")),
            ("Object in categorie A. Registratie is verplicht.", ("A.", "Registratie")),
        ],
    )
    def test_grens_draagt_passage_en_positie(self, tekst, fragmenten):
        seg = _segmenteer(tekst)
        grens = (seg.zekere_grenzen or seg.onzekere_grenzen)[0]
        for fragment in fragmenten:
            assert fragment in grens.passage, grens
        assert tekst[grens.positie] in ".?!"
        assert grens.grond


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    if request.param.startswith("cached_manager"):
        from toetsregels.cached_manager import get_cached_toetsregel_manager
        from toetsregels.rule_cache import get_rule_cache

        get_rule_cache().clear_cache()
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


async def _valideer(svc, tekst: str, begrip: str = "object") -> dict:
    return await svc.validate_definition(
        begrip=begrip, text=tekst, ontologische_categorie=None, context={}
    )


def _int01_violations(res: dict) -> list[dict]:
    return [v for v in res.get("violations", []) if v.get("code") == "INT-01"]


def _deelstatussen(res: dict) -> dict[str, str]:
    return {p["id"]: p["status"] for p in res["rule_results"]["INT-01"]["parts"]}


def _int01_reviewreden(res: dict) -> str:
    return next(r["reason"] for r in res["review_required"] if r["rule_id"] == "INT-01")


class TestServiceUitkomst:
    """Beide laadpaden (ToetsregelManager en RuleCache-keten)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tekst",
        [
            ASTRA_GOED,
            "Object dat gegevens bevat.",
            "Object die gegevens bevat.",
            "Document op naam van dr. Smit.",
            "Veelhoek met precies\ndrie zijden.",
        ],
        ids=["E01", "E02", "E03", "E04", "E07-omloop"],
    )
    async def test_een_zin_is_deelbevinding_geen_groene_regel(self, svc, tekst):
        res = await _valideer(svc, tekst)
        assert res["rule_statuses"]["INT-01"] == "review_required"
        assert "INT-01" not in res["passed_rules"]
        assert not _int01_violations(res)
        detail = res["rule_results"]["INT-01"]
        assert detail["status"] == "review_required"
        assert detail["score"] is None
        assert _deelstatussen(res) == {
            "zinsstructuur": "pass",
            "compactheid": "review_required",
            "begrijpelijkheid": "review_required",
        }
        # Reviewbevinding 3: twee aparte onderdelen met een eigen reden.
        redenen = {d["id"]: d["reason"] for d in res["rule_results"]["INT-01"]["parts"]}
        assert redenen["compactheid"].startswith("Compactheid is nog niet")
        assert redenen["begrijpelijkheid"].startswith("Begrijpelijkheid is nog niet")
        assert "doelgroep" in redenen["begrijpelijkheid"]
        assert "doelgroep" not in redenen["compactheid"]
        reden = _int01_reviewreden(res)
        assert "Eén definitieformulering vastgesteld" in reden
        assert (
            "Compactheid en begrijpelijkheid zijn nog niet inhoudelijk beoordeeld"
            in reden
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("tekst", "passage"),
        [
            ("Wat is dit? Afgebakend object.", "dit? Afgebakend"),
            ("Afgebakend object. Heeft vaste vorm.", "object. Heeft"),
            (ASTRA_FOUT, "maken. In tegenstelling"),
        ],
        ids=["E05", "E06", "astra-fout"],
    )
    async def test_tweede_zin_faalt_met_passage_en_reden(self, svc, tekst, passage):
        res = await _valideer(svc, tekst)
        assert res["rule_statuses"]["INT-01"] == "fail"
        (violation,) = _int01_violations(res)
        assert passage in violation["message"]
        assert "één zin" in violation["message"]
        assert "Compactheid en begrijpelijkheid" in violation["message"]
        # K3: bestaande lage waarschuwingszwaarte, geen cijfer.
        assert violation["severity"] == "warning"
        assert violation["severity_level"] == "low"
        assert "Verboden patroon" not in violation["message"]
        # De suggestie behoudt differentia, namen en negaties en herschrijft
        # niet stil; geen woordvermijdingsadvies meer.
        suggestie = violation["suggestion"]
        assert "kenmerken" in suggestie
        assert "negaties" in suggestie
        assert "en/maar/of" not in suggestie
        delen = _deelstatussen(res)
        assert delen["zinsgrens_1"] == "fail"
        assert delen["compactheid"] == "review_required"
        assert delen["begrijpelijkheid"] == "review_required"
        assert "zinsstructuur" not in delen
        evidence = res["rule_results"]["INT-01"]["parts"][0]["evidence"]
        assert passage in evidence

    @pytest.mark.asyncio
    async def test_onzekere_grens_is_open_met_passage(self, svc):
        res = await _valideer(svc, "Object met gegevens enz. Het wordt geregistreerd.")
        assert res["rule_statuses"]["INT-01"] == "review_required"
        assert not _int01_violations(res)
        delen = _deelstatussen(res)
        assert delen["zinsgrens_onzeker_1"] == "review_required"
        reden = _int01_reviewreden(res)
        assert "Zinsgrens onzeker bij" in reden
        assert "enz. Het" in reden

    @pytest.mark.asyncio
    async def test_geheel_geciteerde_kern_c35_bewust_beoordelen(self, svc):
        res = await _valideer(svc, "“Afgebakend object. Heeft vaste vorm.”")
        assert res["rule_statuses"]["INT-01"] == "fail"
        delen = _deelstatussen(res)
        assert delen["broncitaat"] == "review_required"
        citaatdeel = next(
            p for p in res["rule_results"]["INT-01"]["parts"] if p["id"] == "broncitaat"
        )
        assert "niet automatisch" in citaatdeel["action"]
        assert "parafrase" in citaatdeel["action"]

    @pytest.mark.asyncio
    async def test_lege_tekst_niet_beoordeeld(self, svc):
        res = await _valideer(svc, "")
        assert res["rule_statuses"]["INT-01"] == "not_evaluated"
        assert not _int01_violations(res)
        assert "INT-01" not in res["passed_rules"]

    @pytest.mark.asyncio
    async def test_geen_score_en_geen_zelfstandige_blokkade(self, svc):
        res = await _valideer(svc, "Afgebakend object. Heeft vaste vorm.")
        gate = res.get("acceptance_gate") or {}
        assert "INT-01" not in " ".join(map(str, gate.get("reasons") or []))
        assert "INT-01" not in " ".join(map(str, gate.get("gates_failed") or []))
        from services.validation.modular_validation_service import (
            _ACCEPTATIE_BLOKKEERDERS,
        )

        assert "INT-01" not in _ACCEPTATIE_BLOKKEERDERS

    @pytest.mark.asyncio
    async def test_int01_bereikt_geen_automatisch_herstel(self, svc):
        """DEF-638 blijft uit: een INT-01-bevinding start geen tekstherstel."""
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        res = await _valideer(svc, "Afgebakend object. Heeft vaste vorm.")
        herstelbaar = DefinitionOrchestratorV2._herstelbare_overtredingen(res)
        assert not [v for v in herstelbaar if v.get("code") == "INT-01"]

    @pytest.mark.asyncio
    async def test_buurregels_behouden(self, svc):
        """ESS-04 en de oordeelregels rond INT-01 blijven ongewijzigd open."""
        res = await _valideer(svc, ASTRA_GOED, begrip="transitie-eis")
        statussen = res["rule_statuses"]
        for code in ("ESS-04", "INT-03", "INT-06", "STR-08", "STR-09", "ESS-01"):
            assert statussen[code] == "review_required", code
        ess04 = next(r for r in res["review_required"] if r["rule_id"] == "ESS-04")
        assert ess04["reason"].startswith("ESS-04 — Toetsbaarheid:")
        # INT-09 (opsomming) blijft een automatische regel met eigen oordeel.
        assert statussen["INT-09"] in ("pass", "fail")


class TestRecordEnPatronen:
    def test_record_volgt_astra_zonder_woordlijst(self):
        data = json.loads(REGELPAD.read_text(encoding="utf-8"))
        assert "herkenbaar_patronen" not in data
        assert data["type"] == "gehele definitie"
        assert "begrijpelijk" in data["uitleg"]
        assert data["goede_voorbeelden"] == [ASTRA_GOED]
        assert data["foute_voorbeelden"] == [ASTRA_FOUT]
        contract = data["runtime_contract"]
        assert contract["evaluator"] == "sentence_boundary"
        assert contract["score_policy"] == "excluded_from_score"
        assert contract["automation_status"] == "automated"
        assert contract["executability"] == "deterministic"
        assert contract["example_pair_policy"] == "review_policy"
        assert contract["example_pair_issue"] == "DEF-770"
        assert "Opsommingen, bijzinnen" not in data["toelichting"]

    def test_aanvullende_patronen_bevatten_geen_int01(self):
        from validation.additional_patterns import get_additional_patterns

        assert not get_additional_patterns("INT-01")

    @pytest.mark.asyncio
    async def test_voorbeeldpaar_via_beide_laadpaden(self, svc):
        goed = await _valideer(svc, ASTRA_GOED, begrip="transitie-eis")
        fout = await _valideer(svc, ASTRA_FOUT, begrip="transitie-eis")
        assert _deelstatussen(goed)["zinsstructuur"] == "pass"
        assert goed["rule_statuses"]["INT-01"] == "review_required"
        assert fout["rule_statuses"]["INT-01"] == "fail"
