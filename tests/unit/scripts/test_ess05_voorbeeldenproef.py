"""Tests voor scripts/ess05/voorbeeldenproef.py (DEF-768, ESS-05).

Geen netwerk en geen modelaanroep: alles draait op de stub of op nepclients.
De goldset komt uit een fixture-kopie (logs/ is niet getrackt).
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import socket
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "def768_voorbeeldenproef", _REPO / "scripts" / "ess05" / "voorbeeldenproef.py"
)
proef = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = proef
_SPEC.loader.exec_module(proef)

GOLDSET = _REPO / "tests" / "fixtures" / "def768_voorbeeldenproef_goldset_v1.json"
ITEMS = {i["id"]: i for i in json.loads(GOLDSET.read_text("utf-8"))["definities"]}

DB_278 = (
    "Soort  \nrechtsbijstandverlener die als advocaat optreedt voor een verdachte "
    "in een strafvorderlijke procedure op grond van een keuze door de verdachte of "
    "een aanwijzing door het bestuur van de raad voor rechtsbijstand "
    "[Bron 1] [Bron 2] [Bron 3]."
)
DB_40 = (
    "- Ontologische categorie: soort\nEcht, eigen, geldig en gekwalificeerd "
    "document met unieke identificerende persoonsgebonden kenmerken.\n\n"
    "Toelichting: De relatie met identiteitsmiddel is met deze definitie niet "
    "gelegd. Middelen zijn breder dan documenten (dit is een subset van middel)."
)


@pytest.fixture
def geen_netwerk(monkeypatch):
    def weiger(*_args, **_kwargs):
        msg = "netwerk is verboden in deze test"
        raise AssertionError(msg)

    monkeypatch.setattr(socket, "socket", weiger)
    monkeypatch.setattr(socket, "create_connection", weiger)


def _nee(nr, citaat="advocaat optreedt"):
    return {"nr": nr, "valt_onder": "nee", "citaat": citaat, "toelichting": ""}


# --- stap 0: schoonmaken -----------------------------------------------------


def test_schoonmaken_echte_tekst_db278():
    assert ITEMS["db-278"]["definitie_db"] == DB_278
    # Markers weg, witruimte samengevoegd, geen spatie vóór de punt.
    assert proef.maak_schoon(DB_278) == (
        "rechtsbijstandverlener die als advocaat optreedt voor een verdachte in een "
        "strafvorderlijke procedure op grond van een keuze door de verdachte of een "
        "aanwijzing door het bestuur van de raad voor rechtsbijstand."
    )


def test_bronmarker_voegt_geen_woorden_samen():
    assert proef.maak_schoon("persoon [Bron 1]die handelt") == "persoon die handelt"


def test_bronmarker_voor_leesteken_laat_geen_spatie_achter():
    assert proef.maak_schoon("persoon [Bron 1].") == "persoon."


@pytest.mark.parametrize(
    ("tekst", "verwacht"),
    [
        ("a , b ; c : d )", "a, b; c: d)"),
        ("( a\n.", "( a."),
    ],
)
def test_geen_witruimte_voor_leestekens(tekst, verwacht):
    assert proef.maak_schoon(tekst) == verwacht


def test_schoonmaken_echte_tekst_db40():
    assert ITEMS["db-40"]["definitie_db"] == DB_40
    assert proef.maak_schoon(DB_40) == (
        "Echt, eigen, geldig en gekwalificeerd document met unieke identificerende "
        "persoonsgebonden kenmerken."
    )


def test_schoonmaken_vetregel_en_soort_alleen_als_eerste_regel():
    tekst = "**Definitie**\nPersoon  die\n  iets doet.\nSoort"
    assert proef.maak_schoon(tekst) == "Persoon die iets doet. Soort"


def test_schoonmaken_laat_gewone_tekst_ongemoeid():
    tekst = ITEMS["db-277"]["definitie_db"]
    assert proef.maak_schoon(tekst) == tekst


# --- citaatcontrole ----------------------------------------------------------


@pytest.mark.parametrize(
    ("citaat", "verwacht"),
    [
        ("als advocaat optreedt", True),
        ("ALS   Advocaat\noptreedt", True),
        ("  verdachte in een  ", True),
        ("als advocaat optreden", False),
        ("advocaat voor een verdachte", False),  # niet aaneengesloten
        ('"als advocaat optreedt"', False),  # geen reparatie van aanhalingstekens
        ("", False),
        ("   ", False),
        (None, False),
    ],
)
def test_citaatcontrole(citaat, verwacht):
    schoon = proef.maak_schoon(DB_278)
    assert proef.citaat_staat_in(citaat, schoon) is verwacht


# --- uitkomstregels ----------------------------------------------------------


def test_uitkomst_onbruikbaar_gaat_voor_alles():
    u = proef.bepaal_uitkomst("B mist nr 2", None, "x")
    assert (u.uitkomst, u.onbruikbaar) == ("twijfel", True)
    assert u.reden == "uitvoer onbruikbaar: B mist nr 2"


def test_uitkomst_ja_geeft_voldoet_niet_en_noemt_gevallen():
    oordelen = [
        _nee(1),
        {"nr": 2, "valt_onder": "ja", "citaat": "", "toelichting": ""},
        {"nr": 3, "valt_onder": "onzeker", "citaat": "", "toelichting": ""},
        {"nr": 4, "valt_onder": "ja", "citaat": None, "toelichting": ""},
    ]
    u = proef.bepaal_uitkomst(None, oordelen, proef.maak_schoon(DB_278))
    assert u.uitkomst == "voldoet niet"
    assert u.gevallen_ja == (2, 4)
    assert "nr 2, 4" in u.reden


def test_uitkomst_onzeker_geeft_twijfel():
    oordelen = [
        _nee(1),
        {"nr": 2, "valt_onder": "onzeker", "citaat": "", "toelichting": ""},
    ]
    u = proef.bepaal_uitkomst(None, oordelen, proef.maak_schoon(DB_278))
    assert (u.uitkomst, u.onbruikbaar, u.gevallen_onzeker) == ("twijfel", False, (2,))


def test_uitkomst_nee_zonder_letterlijk_citaat_geeft_twijfel():
    oordelen = [_nee(1), _nee(2, citaat="optreedt als advocaat")]
    u = proef.bepaal_uitkomst(None, oordelen, proef.maak_schoon(DB_278))
    assert (u.uitkomst, u.citaat_ongeldig) == ("twijfel", (2,))


def test_uitkomst_alles_nee_met_geldig_citaat_geeft_voldoet():
    oordelen = [_nee(1), _nee(2, citaat="STRAFVORDERLIJKE  procedure")]
    u = proef.bepaal_uitkomst(None, oordelen, proef.maak_schoon(DB_278))
    assert (u.uitkomst, u.onbruikbaar) == ("voldoet", False)


# --- parsing -----------------------------------------------------------------


@pytest.mark.parametrize(
    "tekst",
    [
        "geen json",
        '```json\n{"verwante_begrippen": []}\n```',
        '{"verwante_begrippen": [',
    ],
)
def test_onparseerbare_a_is_onbruikbaar(tekst):
    gevallen, fout = proef.parse_a(tekst)
    assert gevallen is None
    assert fout.startswith("A is geen geldige JSON")


def _a_json(*aantallen_gevallen):
    """A-antwoord met per verwant begrip het opgegeven aantal gevallen."""
    return json.dumps(
        {
            "verwante_begrippen": [
                {
                    "begrip": f"verwant-{b}",
                    "reden_verwant": "r",
                    "gevallen": [
                        {"geval": f"geval {b}.{g}", "waarom_niet_doelbegrip": "w"}
                        for g in range(n)
                    ],
                }
                for b, n in enumerate(aantallen_gevallen)
            ]
        }
    )


@pytest.mark.parametrize(
    ("aantallen", "fout"),
    [
        ((2,), "A levert 1 verwante begrippen, vereist 2 tot 5"),
        ((1,) * 6, "A levert 6 verwante begrippen, vereist 2 tot 5"),
        ((1, 0), "A: verwant begrip 2 heeft 0 gevallen, vereist 1 of 2"),
        ((3, 1), "A: verwant begrip 1 heeft 3 gevallen, vereist 1 of 2"),
    ],
)
def test_a_buiten_bandbreedte_is_onbruikbaar(aantallen, fout):
    assert proef.parse_a(_a_json(*aantallen)) == (None, fout)


@pytest.mark.parametrize("aantallen", [(1, 1), (2,) * 5])
def test_a_binnen_bandbreedte_is_bruikbaar(aantallen):
    gevallen, fout = proef.parse_a(_a_json(*aantallen))
    assert fout is None
    assert len(gevallen) == sum(aantallen)


def test_a_onbruikbaar_geeft_uitkomst_onbruikbaar(tmp_path):
    """Een afwijkende bandbreedte leidt tot twijfel/onbruikbaar, zonder B."""
    aanroepen = []

    def client(systeem, gebruiker):
        aanroepen.append(systeem)
        return proef.Antwoord(_a_json(2), 10, 10)  # 1 begrip met 2 gevallen

    record = proef.verwerk_item(ITEMS["db-277"], client, proef.Budget())
    assert (record["uitkomst"], record["onbruikbaar"]) == ("twijfel", True)
    assert record["reden"] == (
        "uitvoer onbruikbaar: A levert 1 verwante begrippen, vereist 2 tot 5"
    )
    assert aanroepen == [proef.SYSTEEM_A]


def test_afgekapte_a_meldt_max_tokens_en_blijft_onbruikbaar():
    def client(systeem, gebruiker):
        return proef.Antwoord('{"verwante_begrippen":[{"beg', 10, 8000, "max_tokens")

    record = proef.verwerk_item(ITEMS["db-277"], client, proef.Budget())
    assert (record["uitkomst"], record["onbruikbaar"]) == ("twijfel", True)
    assert record["reden"].startswith(
        "uitvoer onbruikbaar: A afgekapt op max_tokens (A is geen geldige JSON"
    )
    assert record["aanroep_a"]["stop_reason"] == "max_tokens"
    assert "aanroep_b" not in record


def test_afgekapte_b_meldt_max_tokens_en_blijft_onbruikbaar():
    def client(systeem, gebruiker):
        if systeem == proef.SYSTEEM_A:
            return proef.Antwoord(_a_json(1, 1), 10, 10, "end_turn")
        return proef.Antwoord('{"oordelen":[{"nr":1,"valt_on', 10, 8000, "max_tokens")

    record = proef.verwerk_item(ITEMS["db-277"], client, proef.Budget())
    assert (record["uitkomst"], record["onbruikbaar"]) == ("twijfel", True)
    assert record["reden"].startswith(
        "uitvoer onbruikbaar: B afgekapt op max_tokens (B is geen geldige JSON"
    )


def test_geen_afkapmelding_zonder_max_tokens():
    def client(systeem, gebruiker):
        return proef.Antwoord("geen json", 10, 10, "end_turn")

    record = proef.verwerk_item(ITEMS["db-277"], client, proef.Budget())
    assert "afgekapt" not in record["reden"]
    assert record["reden"].startswith("uitvoer onbruikbaar: A is geen geldige JSON")


def test_uitvoer_gaat_naar_v2_en_goldset_blijft_in_v1():
    basis = _REPO / "logs" / "def768"
    assert proef.PROEFVERSIE == "v2"
    v1_goldset = basis / "voorbeeldenproef-v1" / "goldset-v1.json"
    assert basis / "voorbeeldenproef-v2" == proef.UITVOERBASIS
    assert v1_goldset == proef.GOLDSET_PAD
    for functie in (proef.voer_echt_uit, proef.vergelijk):
        standaard = inspect.signature(functie).parameters["basis"].default
        assert standaard == proef.UITVOERBASIS


def test_a_buiten_schema_is_onbruikbaar():
    tekst = json.dumps({"verwante_begrippen": [{"begrip": "x", "gevallen": []}] * 2})
    gevallen, fout = proef.parse_a(tekst)
    assert gevallen is None
    assert "reden_verwant" in fout


def test_a_nummert_doorlopend_vanaf_een():
    gevallen, fout = proef.parse_a(proef.StubClient()._antwoord_a())
    assert fout is None
    assert [g["nr"] for g in gevallen] == [1, 2, 3]
    assert [g["verwant_begrip"] for g in gevallen] == [
        "stub-verwant-1",
        "stub-verwant-1",
        "stub-verwant-2",
    ]


@pytest.mark.parametrize(
    ("oordelen", "fout_bevat"),
    [
        ([_nee(1)], "B mist nr 2"),
        ([_nee(1), {**_nee(2), "valt_onder": "misschien"}], "onbekende waarde"),
        ([_nee(1), {**_nee(2), "valt_onder": "Nee"}], "onbekende waarde"),
        ([_nee(1), _nee(1)], "dubbel"),
        ([_nee(1), _nee(2), _nee(3)], "onbekend nr 3"),
        ([_nee(1), {"nr": 2, "valt_onder": "nee"}], "'nee' zonder niet-leeg"),
        ([_nee(1), _nee(2, citaat="  ")], "'nee' zonder niet-leeg"),
        ([_nee(1), _nee(2, citaat=None)], "'nee' zonder niet-leeg"),
        ([_nee(1), {"nr": 2, "valt_onder": "ja", "citaat": 5}], "geen tekst"),
        ([_nee(1), {**_nee(2), "toelichting": ["x"]}], "geen tekst"),
        ([_nee(1), {**_nee(2), "nr": "2"}], "geen geheel getal"),
    ],
)
def test_b_buiten_schema_is_onbruikbaar(oordelen, fout_bevat):
    resultaat, fout = proef.parse_b(json.dumps({"oordelen": oordelen}), 2)
    assert resultaat is None
    assert fout_bevat in fout


def test_onparseerbare_b_is_onbruikbaar():
    resultaat, fout = proef.parse_b("```json\n{}\n```", 2)
    assert resultaat is None
    assert fout.startswith("B is geen geldige JSON")


def test_b_accepteert_null_citaat_en_sorteert():
    tekst = json.dumps(
        {
            "oordelen": [
                {"nr": 2, "valt_onder": "ja", "citaat": None, "toelichting": None},
                _nee(1),
            ]
        }
    )
    resultaat, fout = proef.parse_b(tekst, 2)
    assert fout is None
    assert [o["nr"] for o in resultaat] == [1, 2]


def test_b_minimaal_geldig_antwoord():
    """Alleen nr en valt_onder, plus citaat bij 'nee'; geen toelichting."""
    tekst = json.dumps(
        {
            "oordelen": [
                {"nr": 1, "valt_onder": "ja"},
                {"nr": 2, "valt_onder": "nee", "citaat": "als advocaat optreedt"},
                {"nr": 3, "valt_onder": "onzeker"},
            ]
        }
    )
    oordelen, fout = proef.parse_b(tekst, 3)
    assert fout is None
    assert oordelen[0] == {
        "nr": 1,
        "valt_onder": "ja",
        "citaat": None,
        "toelichting": None,
    }
    u = proef.bepaal_uitkomst(fout, oordelen, proef.maak_schoon(DB_278))
    assert (u.uitkomst, u.onbruikbaar) == ("voldoet niet", False)

    zonder_ja = json.dumps(
        {
            "oordelen": [
                {"nr": 1, "valt_onder": "nee", "citaat": "als advocaat optreedt"},
                {"nr": 2, "valt_onder": "nee", "citaat": "strafvorderlijke procedure"},
            ]
        }
    )
    oordelen, fout = proef.parse_b(zonder_ja, 2)
    u = proef.bepaal_uitkomst(fout, oordelen, proef.maak_schoon(DB_278))
    assert u.uitkomst == "voldoet"


def test_prompt_b_vraagt_citaat_alleen_bij_nee():
    assert (
        'Geef "citaat" alleen bij "nee"; "toelichting" is optioneel:'
        in proef.SJABLOON_B
    )


# --- prompts -----------------------------------------------------------------


def test_prompt_a_exacte_tekst_met_verwant_begrip():
    assert proef.bouw_prompt_a(ITEMS["astra-fout"]) == (
        "Begrip: onttrekking\n"
        "Context: organisatorisch: onbekend; juridisch: onbekend\n"
        "Neem in elk geval dit verwante begrip op: ontvluchting\n"
        "\n"
        "Opdracht:\n"
        "1. Noem 2 tot 5 verwante begrippen die in deze context met 'onttrekking' "
        "verward kunnen worden of deels dezelfde gevallen dekken. Geen bovenbegrip, "
        "geen onderbegrip, geen synoniem.\n"
        "2. Geef per verwant begrip 1 of 2 concrete, korte gevallen (één zin) die "
        "volgens de gangbare betekenis wél onder het verwante begrip vallen en níet "
        "onder 'onttrekking'. Geen gevallen die onder beide vallen.\n"
        "3. Gebruik je algemene kennis en domeinkennis. Geef bij elk geval in één "
        "zin waarom het niet onder 'onttrekking' valt, in termen van de gangbare "
        "betekenis.\n"
        "\n"
        "Antwoord uitsluitend met JSON, zonder tekst eromheen:\n"
        '{"verwante_begrippen":[{"begrip":"...","reden_verwant":"...","gevallen":'
        '[{"geval":"...","waarom_niet_doelbegrip":"..."}]}]}'
    )


def test_prompt_a_zonder_verwant_laat_regel_weg_en_vult_context():
    prompt = proef.bouw_prompt_a(ITEMS["db-271"])
    assert "Neem in elk geval" not in prompt
    assert prompt.startswith(
        "Begrip: taakstraf\n"
        "Context: organisatorisch: Reclassering, CJIB; juridisch: Strafrecht\n\n"
        "Opdracht:"
    )


@pytest.mark.parametrize("item_id", list(ITEMS))
def test_aanroep_a_bevat_de_definitietekst_niet(item_id):
    item = ITEMS[item_id]
    prompt = proef.bouw_prompt_a(item)
    assert proef.maak_schoon(item["definitie_db"]) not in prompt
    assert item["definitie_db"] not in prompt
    assert "Definitie" not in prompt


def test_aanroep_b_bevat_geen_verwant_begrip_en_geen_waarom(tmp_path):
    stub = proef.StubClient(scenarios=("voldoet",))
    proef.voer_proef_uit(GOLDSET, tmp_path / "uit", stub, modus="droog")
    b_prompts = [p for s, p in stub.prompts if s == proef.SYSTEEM_B]
    assert len(b_prompts) == len(ITEMS)
    for prompt in b_prompts:
        assert "Stubgeval een." in prompt
        for verboden in ("stub-verwant", "stub-waarom", "stub-reden", "verwant_begrip"):
            assert verboden not in prompt
    gevallen = json.loads(b_prompts[0].split("Gevallen:\n")[1].split("\n\n")[0])
    assert gevallen[0] == {"nr": 1, "geval": "Stubgeval een."}
    assert all(set(g) == {"nr", "geval"} for g in gevallen)


def test_aanroep_b_bevat_schone_definitie():
    gevallen = [
        {"nr": 1, "geval": "g", "verwant_begrip": "v", "waarom_niet_doelbegrip": "w"}
    ]
    schoon = proef.maak_schoon(DB_278)
    prompt = proef.bouw_prompt_b(ITEMS["db-278"], schoon, gevallen)
    assert f'Definitie: "{schoon}"' in prompt
    assert "[Bron" not in prompt
    assert "Soort" not in prompt


# --- budget ------------------------------------------------------------------


def test_budgetstop_op_aantal_aanroepen(tmp_path):
    budget = proef.Budget(max_aanroepen=3)
    s = proef.voer_proef_uit(
        GOLDSET, tmp_path / "uit", proef.StubClient(), "droog", budget=budget
    )
    assert s["aantal_aanroepen"] == 3
    uitkomsten = [i["uitkomst"] for i in s["items"]]
    # Item 1 volledig (A+B); item 2 alleen A, B geblokkeerd; rest niet gedraaid.
    assert uitkomsten[0] == "voldoet"
    assert uitkomsten[1:] == ["niet gedraaid"] * 9
    assert s["budget"]["stopreden"] == "maximum van 3 aanroepen bereikt"
    item2 = json.loads((tmp_path / "uit" / "item-02-db-365.json").read_text("utf-8"))
    assert "aanroep_a" in item2
    assert "aanroep_b" not in item2


def test_budgetstop_op_kosten_blijft_onder_plafond_van_drie_dollar(tmp_path):
    """Elke aanroep kost USD 0,20 (8000 uitvoertokens): stop na 14 aanroepen."""
    stub = proef.StubClient(scenarios=("voldoet",))

    def duur(systeem, gebruiker):
        antwoord = stub(systeem, gebruiker)
        return proef.Antwoord(antwoord.tekst, 0, proef.MAX_TOKENS, "end_turn")

    s = proef.voer_proef_uit(GOLDSET, tmp_path / "uit", duur, "droog")
    # Na 14: 2,80 + bovengrens (~0,20) > 3,00; na 13: 2,60 + ~0,20 <= 3,00.
    assert s["aantal_aanroepen"] == 14
    assert s["kosten_bekend_usd"] == "2.800000"
    assert s["kosten_bekend_nusd"] <= proef.PLAFOND_NUSD
    assert "boven plafond USD 3.000000" in s["budget"]["stopreden"]
    assert s["aantal_niet_gedraaid"] == 3


def test_budget_en_limieten_standaardwaarden():
    budget = proef.Budget()
    assert budget.max_aanroepen == 25
    assert proef.MAX_TOKENS == 8000
    assert proef.usd(budget.plafond_nusd) == "3.000000"
    assert proef.usd(budget.marge_nusd) == "0.150000"
    assert proef.kosten_nusd(1_000_000, 0) == 5_000_000_000
    assert proef.kosten_nusd(0, 1_000_000) == 25_000_000_000


def test_budget_grens_is_exclusief():
    budget = proef.Budget(plafond_nusd=1_000, marge_nusd=150)
    budget.kosten_nusd = 850
    assert budget.mag_aanroepen(0) is True
    budget.kosten_nusd = 851
    assert budget.mag_aanroepen(0) is False


def test_bovengrens_aanroep_rondt_tekens_gedeeld_door_twee_naar_boven_af():
    # 3 tekens -> 2 invoertokens; plus 8000 uitvoertokens tegen 5/25 USD per M.
    assert proef.bovengrens_nusd("ab", "c") == 2 * 5_000 + 8000 * 25_000
    assert proef.bovengrens_nusd("ab", "cd") == 2 * 5_000 + 8000 * 25_000


def test_bovengrens_blokkeert_waar_alleen_de_marge_zou_doorlaten():
    budget = proef.Budget()
    budget.kosten_nusd = 2_800_000_000  # USD 2,80: 2,80 + 0,15 <= 3,00
    lang = "x" * 100_000  # 50.000 invoer (0,25) + 8000 uitvoer (0,20) = USD 0,45
    assert proef.bovengrens_nusd("", lang) == 450_000_000
    assert budget.mag_aanroepen(0) is True  # alleen de marge: zou doorgaan
    assert budget.mag_aanroepen(proef.bovengrens_nusd("", lang)) is False
    assert "bovengrens aanroep USD 0.450000" in budget.stopreden


def test_bovengrens_slaat_een_te_dure_aanroep_over_in_de_run(tmp_path):
    goldset = tmp_path / "goldset.json"
    item = {**ITEMS["db-277"], "begrip": "x" * 100_000}
    goldset.write_text(json.dumps({"definities": [item]}), "utf-8")
    budget = proef.Budget()
    budget.kosten_nusd = 2_800_000_000
    aanroepen = []

    def client(systeem, gebruiker):
        aanroepen.append(systeem)
        return proef.StubClient()(systeem, gebruiker)

    s = proef.voer_proef_uit(goldset, tmp_path / "uit", client, "droog", budget)
    assert aanroepen == []
    assert s["items"][0]["uitkomst"] == "niet gedraaid"
    assert "bovengrens aanroep" in s["budget"]["stopreden"]


def test_aanroepfout_stopt_zonder_herhaalpoging(tmp_path):
    aanroepen = []

    def faalt(systeem, gebruiker):
        aanroepen.append(systeem)
        msg = "APIConnectionError: verbinding mislukt"
        raise proef.AanroepError(msg)

    s = proef.voer_proef_uit(GOLDSET, tmp_path / "uit", faalt, "droog")
    assert len(aanroepen) == 1
    assert s["aantal_niet_gedraaid"] == 10
    assert "aanroep mislukt" in s["budget"]["stopreden"]
    assert s["kosten_volledig"] is False


def test_ontbrekende_usage_stopt_de_run_en_kosten_zijn_niet_volledig(tmp_path):
    def zonder_usage(systeem, gebruiker):
        return proef.Antwoord(
            tekst=proef.StubClient()._antwoord_a(),
            invoer_tokens=None,
            uitvoer_tokens=None,
        )

    s = proef.voer_proef_uit(GOLDSET, tmp_path / "uit", zonder_usage, "droog")
    assert s["aantal_aanroepen"] == 1
    assert "usage ontbreekt" in s["budget"]["stopreden"]
    assert s["kosten_volledig"] is False
    assert s["kosten_bekend_usd"] == "0.000000"
    assert "kosten_usd" not in s
    md = (tmp_path / "uit" / "samenvatting.md").read_text("utf-8")
    assert "- Kosten: totaal onbekend; bekend deel USD 0.000000" in md
    assert "(volledig)" not in md
    item = json.loads((tmp_path / "uit" / "item-01-db-277.json").read_text("utf-8"))
    assert item["aanroep_a"]["kosten_usd"] is None


def test_kosten_volledig_bij_bekende_usage(tmp_path):
    s = proef.voer_proef_uit(GOLDSET, tmp_path / "uit", proef.StubClient(), "droog")
    assert s["kosten_volledig"] is True
    assert int(s["kosten_bekend_nusd"]) > 0
    md = (tmp_path / "uit" / "samenvatting.md").read_text("utf-8")
    assert f"- Kosten: USD {s['kosten_bekend_usd']} (volledig)" in md


# --- echte modus zonder netwerk ----------------------------------------------


def test_echt_weigert_bestaande_run_map(tmp_path):
    (tmp_path / "run-1").mkdir()
    fabriek_aangeroepen = []
    with pytest.raises(proef.ProefError, match="run-map bestaat al"):
        proef.voer_echt_uit(
            1,
            tmp_path / "bestaat-niet.env",
            basis=tmp_path,
            goldset_pad=GOLDSET,
            client_fabriek=fabriek_aangeroepen.append,
        )
    assert fabriek_aangeroepen == []
    assert list((tmp_path / "run-1").iterdir()) == []


def test_droog_weigert_bestaande_uitmap(tmp_path):
    (tmp_path / "uit").mkdir()
    with pytest.raises(proef.ProefError, match="bestaat al"):
        proef.voer_proef_uit(GOLDSET, tmp_path / "uit", proef.StubClient(), "droog")


def test_echt_leest_alleen_de_sleutel_en_schrijft_hem_nergens(tmp_path, geen_netwerk):
    sleutel = "sk-ant-geheim-0123456789"
    env = tmp_path / ".env"
    env.write_text(
        f"OPENAI_API_KEY=anders\n# ANTHROPIC_API_KEY=commentaar\n"
        f'export ANTHROPIC_API_KEY="{sleutel}"\nANDERS=1\n',
        "utf-8",
    )
    ontvangen = []

    def fabriek(api_sleutel):
        ontvangen.append(api_sleutel)
        return proef.StubClient()

    s = proef.voer_echt_uit(
        2, env, basis=tmp_path / "basis", goldset_pad=GOLDSET, client_fabriek=fabriek
    )
    assert ontvangen == [sleutel]
    assert s["modus"] == "echt run 2"
    for pad in (tmp_path / "basis" / "run-2").iterdir():
        assert sleutel not in pad.read_text("utf-8")


def test_sleutel_ontbreekt_in_env(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=x\nANTHROPIC_API_KEY=\n", "utf-8")
    with pytest.raises(proef.ProefError, match="ontbreekt of is leeg"):
        proef.lees_api_sleutel(env)


def test_inlinecommentaar_na_ongequote_sleutel_geweigerd_voor_run_map(tmp_path):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-test-geheim # uitleg\n", "utf-8")
    fabriek_aangeroepen = []
    with pytest.raises(proef.ProefError, match="inlinecommentaar") as fout:
        proef.voer_echt_uit(
            1,
            env,
            basis=tmp_path / "basis",
            goldset_pad=GOLDSET,
            client_fabriek=fabriek_aangeroepen.append,
        )
    assert "sk-ant-test-geheim" not in str(fout.value)
    assert fabriek_aangeroepen == []
    assert not (tmp_path / "basis" / "run-1").exists()


@pytest.mark.parametrize(
    ("regel", "verwacht"),
    [
        ('ANTHROPIC_API_KEY="sk-ant-test" # uitleg', "sk-ant-test"),
        ("ANTHROPIC_API_KEY='sk-ant-test'", "sk-ant-test"),
        ('ANTHROPIC_API_KEY="sk-ant # binnen quotes"', "sk-ant # binnen quotes"),
        ("ANTHROPIC_API_KEY=sk-ant-test", "sk-ant-test"),
        ("ANTHROPIC_API_KEY=sk-ant#geen-commentaar", "sk-ant#geen-commentaar"),
    ],
)
def test_env_quotes_blijven_werken(tmp_path, regel, verwacht):
    env = tmp_path / ".env"
    env.write_text(regel + "\n", "utf-8")
    assert proef.lees_api_sleutel(env) == verwacht


@pytest.mark.parametrize(
    "regel",
    ['ANTHROPIC_API_KEY="sk-ant-geheim', 'ANTHROPIC_API_KEY="sk-ant-geheim" extra'],
)
def test_env_ongeldige_quotes_geweigerd_zonder_waarde(tmp_path, regel):
    env = tmp_path / ".env"
    env.write_text(regel + "\n", "utf-8")
    with pytest.raises(proef.ProefError, match="ongeldige quotes") as fout:
        proef.lees_api_sleutel(env)
    assert "sk-ant-geheim" not in str(fout.value)


def test_echte_client_negeert_anthropic_base_url_uit_omgeving(monkeypatch):
    """Het echte SDK-verzoek gaat naar de vaste URL, niet naar de omgevingswaarde."""
    anthropic = pytest.importorskip("anthropic")
    httpx = pytest.importorskip("httpx")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://kwaadaardig.example")
    verzoeken = []

    def onderschep(verzoek):
        verzoeken.append(verzoek)
        return httpx.Response(
            200,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-5",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "geheim denkwerk",
                        "signature": "sig",
                    },
                    {"type": "text", "text": "{}"},
                ],
                "stop_reason": "max_tokens",
                "stop_sequence": None,
                "usage": {"input_tokens": 7, "output_tokens": 8000},
            },
        )

    echte_klasse = anthropic.Anthropic

    def met_onderschepping(**kwargs):
        transport = httpx.MockTransport(onderschep)
        return echte_klasse(**kwargs, http_client=httpx.Client(transport=transport))

    monkeypatch.setattr(anthropic, "Anthropic", met_onderschepping)
    client = proef.EchteClient("sk-ant-test")
    record = proef._roep(client, proef.Budget(), "systeem", "gebruiker")

    assert len(verzoeken) == 1
    assert str(verzoeken[0].url) == "https://api.anthropic.com/v1/messages"
    assert verzoeken[0].headers["x-api-key"] == "sk-ant-test"
    body = json.loads(verzoeken[0].content)
    assert body["model"] == "claude-opus-5"
    assert body["max_tokens"] == 8000
    assert "temperature" not in body
    assert record["usage"] == {"input_tokens": 7, "output_tokens": 8000}
    # Alleen bloktypen en stop_reason vastgelegd; denktekst nergens.
    assert record["bloktypen"] == ["thinking", "text"]
    assert record["stop_reason"] == "max_tokens"
    assert record["ruw"] == "{}"
    assert "geheim denkwerk" not in json.dumps(record)


def test_echte_client_verbergt_sleutel_in_foutmelding():
    client = proef.EchteClient.__new__(proef.EchteClient)
    client._sleutel = "sk-ant-geheim"

    class _Faalt:
        class messages:  # noqa: N801 - bootst SDK-attribuut na
            @staticmethod
            def create(**kwargs):
                assert "temperature" not in kwargs
                assert kwargs["model"] == "claude-opus-5"
                assert kwargs["max_tokens"] == 8000
                msg = "fout met sk-ant-geheim erin"
                raise RuntimeError(msg)

    client._client = _Faalt()
    with pytest.raises(proef.AanroepError) as fout:
        client("s", "g")
    assert "sk-ant-geheim" not in str(fout.value)
    assert "RuntimeError" in str(fout.value)


def test_echte_client_zet_max_retries_nul(monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    gezien = {}

    class _Nep:
        def __init__(self, **kwargs):
            gezien.update(kwargs)

    monkeypatch.setattr(anthropic, "Anthropic", _Nep)
    proef.EchteClient("sk-test")
    assert gezien["max_retries"] == 0
    assert gezien["base_url"] == "https://api.anthropic.com"


# --- samenvatting en vergelijk -----------------------------------------------


def _record(item_id, chris, uitkomst, onbruikbaar=False):
    return {
        "id": item_id,
        "begrip": "b",
        "oordeel_chris": chris,
        "uitkomst": uitkomst,
        "onbruikbaar": onbruikbaar,
        "reden": "r",
    }


def test_telling_onterecht_voldoet():
    records = [
        _record("a", "voldoet", "voldoet"),
        _record("b", "twijfel", "voldoet"),
        _record("c", "voldoet niet", "voldoet"),
        _record("d", "voldoet niet", "twijfel", onbruikbaar=True),
        _record("e", "twijfel", "twijfel", onbruikbaar=True),
        _record("f", "voldoet", "niet gedraaid"),
    ]
    s = proef.vat_samen(records, proef.Budget(), {})
    assert s["onterecht_voldoet"] == 2
    assert s["onterecht_voldoet_ids"] == ["b", "c"]
    assert s["aantal_gelijk"] == 2
    assert s["gelijk_waarvan_onbruikbaar"] == 1
    assert s["aantal_onbruikbaar"] == 2
    assert s["aantal_niet_gedraaid"] == 1


def _schrijf_run(basis, n, uitkomsten):
    pad = basis / f"run-{n}"
    pad.mkdir(parents=True)
    samenvatting = {
        "goldset_sha256": "g",
        "sjabloon_a_sha256": "a",
        "sjabloon_b_sha256": "b",
        "items": [{"id": i, "uitkomst": u} for i, u in uitkomsten.items()],
    }
    (pad / "samenvatting.json").write_text(json.dumps(samenvatting), "utf-8")


def test_vergelijk_telt_gelijke_uitkomsten(tmp_path):
    _schrijf_run(
        tmp_path,
        1,
        {"x": "voldoet", "y": "twijfel", "z": "niet gedraaid", "w": "voldoet niet"},
    )
    _schrijf_run(
        tmp_path,
        2,
        {
            "x": "voldoet",
            "y": "voldoet niet",
            "z": "niet gedraaid",
            "w": "voldoet niet",
        },
    )
    assert proef.main(["--vergelijk", "--basis", str(tmp_path)]) == 0
    resultaat = json.loads((tmp_path / "vergelijking.json").read_text("utf-8"))
    assert resultaat["aantal_gelijk"] == 2
    assert resultaat["aantal_items"] == 4
    assert [i["gelijk"] for i in resultaat["items"]] == [True, False, False, True]
    assert resultaat["zelfde_goldset"] is True
    assert resultaat["criteria"] == proef.CRITERIA
    # Een tweede vergelijking overschrijft niets.
    assert proef.main(["--vergelijk", "--basis", str(tmp_path)]) == 2


def test_vergelijk_koppelt_op_id_ongeacht_volgorde(tmp_path):
    _schrijf_run(tmp_path, 1, {"x": "voldoet", "y": "twijfel", "z": "voldoet niet"})
    _schrijf_run(tmp_path, 2, {"z": "voldoet niet", "x": "twijfel", "y": "twijfel"})
    resultaat = proef.vergelijk(tmp_path)
    assert resultaat["aantal_gelijk"] == 2
    assert [(i["id"], i["gelijk"]) for i in resultaat["items"]] == [
        ("x", False),
        ("y", True),
        ("z", True),
    ]


def test_vergelijk_weigert_andere_itemverzameling(tmp_path):
    _schrijf_run(tmp_path, 1, {"x": "voldoet", "y": "twijfel"})
    _schrijf_run(tmp_path, 2, {"x": "voldoet", "q": "twijfel"})
    with pytest.raises(proef.ProefError, match="niet dezelfde items"):
        proef.vergelijk(tmp_path)


def test_vergelijk_weigert_zonder_tweede_run(tmp_path):
    _schrijf_run(tmp_path, 1, {"x": "voldoet"})
    assert proef.main(["--vergelijk", "--basis", str(tmp_path)]) == 2


def test_cli_weigert_echt_met_eigen_uitmap(tmp_path):
    with pytest.raises(SystemExit):
        proef.main(["--echt", "--run", "1", "--uitmap", str(tmp_path)])


# --- droogrun van begin tot eind ---------------------------------------------


def test_droogrun_van_begin_tot_eind(tmp_path, geen_netwerk):
    uitmap = tmp_path / "droog"
    code = proef.main(["--droog", "--uitmap", str(uitmap), "--goldset", str(GOLDSET)])
    assert code == 0
    bestanden = sorted(p.name for p in uitmap.iterdir())
    assert len([b for b in bestanden if b.startswith("item-")]) == 10
    assert {"samenvatting.json", "samenvatting.md"} <= set(bestanden)

    s = json.loads((uitmap / "samenvatting.json").read_text("utf-8"))
    assert [i["uitkomst"] for i in s["items"]] == [
        "voldoet",  # alles nee, citaat met afwijkende hoofdletters/witruimte
        "voldoet niet",  # minimaal B-antwoord: ja zonder citaat/toelichting
        "twijfel",  # onzeker
        "twijfel",  # citaat niet letterlijk
        "twijfel",  # A afgekapt op max_tokens
        "twijfel",  # A met 1 verwant begrip (bandbreedte 2-5)
        "twijfel",  # B mist nr
        "twijfel",  # B onbekende waarde
        "voldoet",  # astra-fout: onterecht voldoet
        "twijfel",  # B in codeblok: onparseerbaar
    ]
    assert s["aantal_onbruikbaar"] == 5
    assert s["onterecht_voldoet_ids"] == ["astra-fout"]
    assert s["aantal_aanroepen"] == 18  # 2 items zonder B (A onbruikbaar)
    assert s["criteria"] == (
        "succes: ≥ 8/10 gelijk aan goldset, 0 onterecht voldoet; "
        "stabiliteit (vergelijk): ≥ 8/10 gelijk tussen run 1 en run 2"
    )
    assert s["model"] == "claude-opus-5"
    assert s["temperatuur"] == "niet gezet (API-standaard gebruikt)"
    assert s["goldset_sha256"] == proef.sha256_bestand(GOLDSET)
    assert len(s["sjabloon_a_sha256"]) == len(s["sjabloon_b_sha256"]) == 64
    assert s["modus"] == "droog"
    assert s["kosten_volledig"] is True
    assert s["sjabloon_b_sha256"] == proef.sha256_tekst(proef.SJABLOON_B)

    item2 = json.loads((uitmap / "item-02-db-365.json").read_text("utf-8"))
    assert item2["oordelen"][0]["citaat"] is None
    assert item2["oordelen"][0]["toelichting"] is None
    item6 = json.loads((uitmap / "item-06-db-140.json").read_text("utf-8"))
    assert "1 verwante begrippen, vereist 2 tot 5" in item6["reden"]
    assert s["proefversie"] == "v2"
    item5 = json.loads((uitmap / "item-05-db-142.json").read_text("utf-8"))
    assert "A afgekapt op max_tokens" in item5["reden"]
    assert item5["aanroep_a"]["stop_reason"] == "max_tokens"
    assert item5["aanroep_a"]["bloktypen"] == ["thinking", "text"]
    assert item2["aanroep_b"]["bloktypen"] == ["text"]
    md = (uitmap / "samenvatting.md").read_text("utf-8")
    assert md.startswith("# ESS-05 voorbeeldenproef v2 — droog")

    item = json.loads((uitmap / "item-03-db-278.json").read_text("utf-8"))
    for veld in ("systeem", "prompt", "ruw", "usage", "kosten_usd"):
        assert veld in item["aanroep_a"]
        assert veld in item["aanroep_b"]
    assert item["definitie_schoon"] == proef.maak_schoon(DB_278)
    assert item["gevallen"][0]["waarom_niet_doelbegrip"] == "stub-waarom-1"
    assert item["oordelen"][0]["valt_onder"] == "onzeker"
    assert item["uitkomst"] == "twijfel"
    assert item["reden"] == "onzeker: nr 1"

    md = (uitmap / "samenvatting.md").read_text("utf-8")
    assert s["criteria"] in md
    assert "| astra-fout | onttrekking | voldoet niet | voldoet | nee |" in md
