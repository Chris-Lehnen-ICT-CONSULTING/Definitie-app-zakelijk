"""Tests voor scripts/ess05/voorbeeldenproef.py (DEF-768, ESS-05).

Geen netwerk en geen modelaanroep: alles draait op de stub of op nepclients.
De goldset komt uit een fixture-kopie (logs/ is niet getrackt).
"""

from __future__ import annotations

import importlib.util
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
    assert proef.maak_schoon(DB_278) == (
        "rechtsbijstandverlener die als advocaat optreedt voor een verdachte in een "
        "strafvorderlijke procedure op grond van een keuze door de verdachte of een "
        "aanwijzing door het bestuur van de raad voor rechtsbijstand."
    )


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


def test_a_met_minder_dan_twee_gevallen_is_onbruikbaar():
    tekst = json.dumps(
        {
            "verwante_begrippen": [
                {
                    "begrip": "ontvluchting",
                    "reden_verwant": "r",
                    "gevallen": [{"geval": "g", "waarom_niet_doelbegrip": "w"}],
                }
            ]
        }
    )
    assert proef.parse_a(tekst) == (None, "A levert 1 geval(len), minimaal 2 vereist")


def test_a_buiten_schema_is_onbruikbaar():
    tekst = json.dumps({"verwante_begrippen": [{"begrip": "x", "gevallen": []}]})
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
        ([_nee(1), {"nr": 2, "valt_onder": "nee"}], "mist 'citaat'"),
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


def test_budgetstop_op_kosten(tmp_path):
    budget = proef.Budget(plafond_nusd=proef.STAPMARGE_NUSD + 1)
    s = proef.voer_proef_uit(
        GOLDSET, tmp_path / "uit", proef.StubClient(), "droog", budget=budget
    )
    assert s["aantal_aanroepen"] == 1
    assert s["aantal_niet_gedraaid"] == 10
    assert "boven plafond" in s["budget"]["stopreden"]


def test_budget_standaardwaarden():
    budget = proef.Budget()
    assert budget.max_aanroepen == 25
    assert proef.usd(budget.plafond_nusd) == "2.000000"
    assert proef.usd(budget.marge_nusd) == "0.150000"
    assert proef.kosten_nusd(1_000_000, 0) == 5_000_000_000
    assert proef.kosten_nusd(0, 1_000_000) == 25_000_000_000


def test_budget_grens_is_exclusief():
    budget = proef.Budget(plafond_nusd=1_000, marge_nusd=150)
    budget.kosten_nusd = 850
    assert budget.mag_aanroepen() is True
    budget.kosten_nusd = 851
    assert budget.mag_aanroepen() is False


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


def test_ontbrekende_usage_stopt_de_run(tmp_path):
    def zonder_usage(systeem, gebruiker):
        return proef.Antwoord(
            tekst=proef.StubClient()._antwoord_a(),
            invoer_tokens=None,
            uitvoer_tokens=None,
        )

    s = proef.voer_proef_uit(GOLDSET, tmp_path / "uit", zonder_usage, "droog")
    assert s["aantal_aanroepen"] == 1
    assert "usage ontbreekt" in s["budget"]["stopreden"]


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


def test_echte_client_verbergt_sleutel_in_foutmelding():
    client = proef.EchteClient.__new__(proef.EchteClient)
    client._sleutel = "sk-ant-geheim"

    class _Faalt:
        class messages:  # noqa: N801 - bootst SDK-attribuut na
            @staticmethod
            def create(**kwargs):
                assert "temperature" not in kwargs
                assert kwargs["model"] == "claude-opus-5"
                assert kwargs["max_tokens"] == 2000
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
        "voldoet niet",
        "twijfel",  # onzeker
        "twijfel",  # citaat niet letterlijk
        "twijfel",  # A onparseerbaar
        "twijfel",  # A < 2 gevallen
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
