"""DEF-835 besluit 16 — contract def835-int02-assessment/4 met bronfuncties.

Bron: `goldset-voorbereiding/bronfuncties-ontwerp-v1.md` §2 en de keuzes van
Chris (07-10-2026): 1B, 2A, 3A, 4A, 5A, 6A en 7A.

Het model levert per passage een `kernvorm` en per grondbron (bevestigde
bedoeling, elk contextitem, elke bronpassage) één `function` met een
letterlijk citaat waar vereist, en als laatste zijn eigen `verdict`. De dienst
leidt de status mechanisch af:

1. `instruction` in de kern → fail (besluit 1, K1);
2. een beschrijvende bron naast een voorschrijvende of `not_a_criterion`-bron
   → review (`conflict`), tenzij de bedoeling met citaat naar gebrek beslecht
   (1B; nooit naar pass);
3. eensluidend → die kant; één voorschrift-bron vraagt een tweede signaal
   (kernvorm `obligation_form`/`discretion_form`, een `not_a_criterion`-bron
   of de bedoeling), anders review (3A); alleen `unclear` → review;
4. alles zwijgt → de kernvorm; `descriptive_act` zonder bedoeling → review
   (5A); `discretion_form` zonder bedoeling → de dienstregel van besluit 12.

Over passages: fail vóór review vóór pass; pass vraagt volledige dekking. De
dienst beslist (2A); een afwijking van het modelverdict staat in
`omzetting`, het modelverdict blijft in het oordeel. Bij een afgeleide review
een vaste vraag (4A). Synthetische invoer; geen goldset- of hold-outinhoud.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
import unicodedata
from typing import Any

import pytest

from domain.int02 import contract
from domain.int02.contract import (
    MELDING_E,
    MELDING_HISTORISCH,
    MELDING_O,
    MELDING_V,
    MELDING_VN,
    MELDING_VN_DISCRETIE,
    Configuratie,
    Uitvoering,
    beoordeel,
    bereken_binding,
    maak_invoer,
    toets_actualiteit,
)
from tests.fixtures.def835_int02_v4 import passage, uitvoer

pytestmark = [pytest.mark.unit]

V3 = "def835-int02-assessment/3"
V4 = "def835-int02-assessment/4"

KERN = "Melding die door de beheerder is vastgelegd in het register."
P = "door de beheerder is vastgelegd in het register"
P_KOP = "Melding die"
ORG = "Synthetische meldkamer"
B1 = "De beheerder legt elke melding vast in het register."
B2 = "Een melding telt mee als zij in het register staat."
B3 = "Ook een mondelinge melding valt onder het begrip."
BED_KENMERK = "Het begrip duidt een geregistreerde melding aan."
BED_OPDRACHT = "Opdracht aan de beheerder om te registreren."
BED_ZWIJGT = "De term komt voor in het meldprotocol."

CODES = {
    "C": "criterion",
    "D": "derivation",
    "A": "actor_prescription",
    "R": "discretionary_decision_rule",
    "N": "not_a_criterion",
    "O": "unclear",
    "O+": "unclear",
    "-": "not_addressed",
}


def _vraag(naam: str) -> str:
    waarde = getattr(contract, naam, None)
    if not isinstance(waarde, str):
        pytest.fail(f"domain.int02.contract.{naam} ontbreekt")
    return waarde


def _invoer(bedoeling: str | None = None, bronnen=(("B1", B1), ("B2", B2), ("B3", B3))):
    return maak_invoer(
        begrip="melding",
        kern=KERN,
        bedoeling=bedoeling,
        organisatorische_context=[ORG],
        juridische_context=[],
        wettelijke_basis=[],
        bronnen=[{"id": i, "tekst": t} for i, t in bronnen],
    )


def _tekst(invoer, sleutel: str) -> str:
    if sleutel == "bedoeling":
        return invoer.bedoeling
    if sleutel == "organisatorische_context/0":
        return invoer.organisatorische_context[0]
    return {f"bron/{b.id}": b.tekst for b in invoer.bronnen}[sleutel]


def _p(invoer, kernvorm: str, codes: dict[str, str] | None = None, quote: str = P):
    """Passage met bronfuncties in korte codes; het citaat is de hele brontekst
    (altijd letterlijk en uniek); `O` zonder citaat, `O+` met citaat."""
    functies = {}
    for sleutel, code in (codes or {}).items():
        citaat = None if code in ("O", "-") else _tekst(invoer, sleutel)
        functies[sleutel] = (CODES[code], citaat)
    return passage(invoer, quote, kernvorm, functies)


def _configuratie() -> Configuratie:
    return Configuratie(
        normhash=hashlib.sha256(b"testnorm def771-int02/2").hexdigest(),
        promptversie="def835-int02-prompt/testfixture",
        routeringshash=hashlib.sha256(b"testroutering").hexdigest(),
        provider="fake-provider",
        model="fake-model-1",
    )


def _doc(invoer, passages, verdict: str, *, actor: str = "ai", **velden):
    return beoordeel(
        invoer,
        _configuratie(),
        uitvoer(passages, verdict, **velden),
        Uitvoering(actor=actor, status="completed"),
    )


def _afleiding(document) -> str | None:
    oordeel = document.oordeel
    assert oordeel is not None, (document.status, document.foutcategorie)
    return oordeel["dienst"]["afleiding"]


def _dienstpassage(document, index: int = 0) -> dict[str, Any]:
    return document.oordeel["dienst"]["passages"][index]


def _vul(sjabloon: str, waarden: dict[str, str]) -> str:
    for sleutel, waarde in waarden.items():
        sjabloon = sjabloon.replace(sleutel, waarde)
    return sjabloon


def _o(reden: str, vraag: str) -> str:
    return _vul(
        MELDING_O,
        {"{ontbrekende of strijdige betekenisgrond}": reden, "{één vraag}": vraag},
    )


VERDICT = {
    "pass": "pass",
    "fail": "fail",
    "review_required": "insufficient_information",
}


def _zonder_omzetting(invoer, passages, status: str, **velden):
    """Beoordeel met het modelverdict dat bij `status` hoort (geen omzetting)."""
    document = _doc(invoer, passages, VERDICT[status], **velden)
    assert document.status == status, (document.status, document.foutcategorie)
    assert document.omzetting is None
    return document


# --- A. versie en grondbronnen -----------------------------------------------------


def test_contractversie_is_vier_en_drie_blijft_herleidbaar():
    assert contract.CONTRACTVERSIE == V4
    assert V3 in contract._BEKENDE_CONTRACTVERSIES
    binding = bereken_binding(_invoer(), _configuratie())
    assert binding.contractversie == V4


def test_grondbronnen_staan_in_vaste_volgorde():
    invoer = maak_invoer(
        begrip="b",
        kern="k",
        bedoeling="bedoeld",
        organisatorische_context=["o1", "o2"],
        juridische_context=["j1"],
        wettelijke_basis=["w1"],
        bronnen=[{"id": "B2", "tekst": "t"}, {"id": "B1", "tekst": "u"}],
    )
    assert contract.grondbronnen(invoer) == (
        "bedoeling",
        "organisatorische_context/0",
        "organisatorische_context/1",
        "juridische_context/0",
        "wettelijke_basis/0",
        "bron/B2",
        "bron/B1",
    )


def test_onbekende_bedoeling_begrip_en_kern_zijn_geen_grondbron():
    sleutels = contract.grondbronnen(_invoer(bedoeling=None))
    assert sleutels == (
        "organisatorische_context/0",
        "bron/B1",
        "bron/B2",
        "bron/B3",
    )
    assert "begrip" not in sleutels and "kern" not in sleutels


# --- B. structuur, volledigheid en citaten ---------------------------------------------


def _geldig() -> dict[str, Any]:
    invoer = _invoer()
    return uitvoer([_p(invoer, "descriptive_act", {"bron/B2": "C"})], "pass")


def _met(pad: tuple, waarde: Any) -> dict[str, Any]:
    data = _geldig()
    doel: Any = data
    for stap in pad[:-1]:
        doel = doel[stap]
    if waarde is ...:
        del doel[pad[-1]]
    else:
        doel[pad[-1]] = waarde
    return data


def _fout(respons, invoer=None):
    document = beoordeel(
        invoer or _invoer(),
        _configuratie(),
        respons,
        Uitvoering(actor="ai", status="completed"),
    )
    assert document.status == "error"
    assert document.oordeel is None
    return document.foutcategorie, document.foutdetail


def test_geldige_uitvoer_wordt_geaccepteerd():
    document = beoordeel(
        _invoer(),
        _configuratie(),
        _geldig(),
        Uitvoering(actor="ai", status="completed"),
    )
    assert (document.status, document.contractversie) == ("pass", V4)


@pytest.mark.parametrize(
    ("pad", "waarde"),
    [
        (("extra",), "x"),
        (("passages", 0, "kernvorm"), ...),
        (("passages", 0, "function"), "criterion"),
        (("passages", 0, "ground"), {"field": "kern", "ref": None, "quote": None}),
        (("passages", 0, "start"), 0),
        (("passages", 0, "kernvorm"), "imperative"),
        (("passages", 0, "kernvorm"), None),
        (("passages", 0, "bronfuncties"), {}),
        (("passages", 0, "bronfuncties", 0, "start"), 0),
        (("passages", 0, "bronfuncties", 0, "quote"), ...),
        (("passages", 0, "bronfuncties", 0, "function"), "niet_van_toepassing"),
        (("passages", 0, "bronfuncties", 0, "function"), "not_applicable"),
        (("passages", 0, "bronfuncties", 0, "bron"), 1),
        (("passages", 0, "bronfuncties", 0, "quote"), 1),
        (("verdict",), "voldoet"),
    ],
    ids=lambda w: repr(w)[:40],
)
def test_structureel_ongeldige_uitvoer_is_invalid_output(pad, waarde):
    assert _fout(_met(pad, waarde)) == ("invalid_output", None)


def test_uitvoer_in_vorm_drie_is_onder_vier_invalid_output():
    drie = {
        "verdict": "pass",
        "passages": [
            {
                "quote": P,
                "function": "criterion",
                "ground": {"field": "kern", "ref": None, "quote": None},
            }
        ],
        "reason": "r",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }
    assert _fout(drie) == ("invalid_output", None)


def test_ontbrekende_of_dubbele_grondbron_is_invalid_output():
    ontbreekt = _geldig()
    ontbreekt["passages"][0]["bronfuncties"].pop()
    assert _fout(ontbreekt) == ("invalid_output", None)
    dubbel = _geldig()
    bf = dubbel["passages"][0]["bronfuncties"]
    bf[-1] = dict(bf[0])
    assert _fout(dubbel) == ("invalid_output", None)
    # Ook als één van meer passages onvolledig is.
    invoer = _invoer()
    twee = uitvoer(
        [_p(invoer, "no_act", quote=P_KOP), _p(invoer, "descriptive_act")], "pass"
    )
    twee["passages"][1]["bronfuncties"].pop(0)
    assert _fout(twee) == ("invalid_output", None)


@pytest.mark.parametrize(
    "sleutel",
    [
        "bron/B9",
        "begrip",
        "kern",
        "organisatorische_context/5",
        "organisatorische_context/x",
        "bron/",
        "",
    ],
)
def test_onbekende_grondbron_is_niet_herleidbaar(sleutel):
    respons = _geldig()
    respons["passages"][0]["bronfuncties"][-1]["bron"] = sleutel
    assert _fout(respons) == ("invalid_citation", "grond_niet_herleidbaar")


def test_bedoeling_als_grondbron_bij_onbekende_bedoeling_is_niet_herleidbaar():
    invoer = _invoer(bedoeling=None)
    respons = uitvoer([_p(invoer, "no_act")], "pass")
    respons["passages"][0]["bronfuncties"].insert(
        0, {"bron": "bedoeling", "function": "not_addressed", "quote": None}
    )
    assert _fout(respons, invoer) == ("invalid_citation", "grond_niet_herleidbaar")


@pytest.mark.parametrize(
    "functie",
    [
        "criterion",
        "derivation",
        "actor_prescription",
        "discretionary_decision_rule",
        "not_a_criterion",
    ],
)
def test_richtinggevende_bronfunctie_zonder_citaat_is_invalid_output(functie):
    respons = _geldig()
    respons["passages"][0]["bronfuncties"][2] = {
        "bron": "bron/B2",
        "function": functie,
        "quote": None,
    }
    assert _fout(respons) == ("invalid_output", None)


@pytest.mark.parametrize("citaat", [B2, "", " "])
def test_zwijgende_bron_met_citaat_is_invalid_output(citaat):
    respons = _geldig()
    respons["passages"][0]["bronfuncties"][2] = {
        "bron": "bron/B2",
        "function": "not_addressed",
        "quote": citaat,
    }
    assert _fout(respons) == ("invalid_output", None)


def test_unclear_mag_zonder_en_met_letterlijk_citaat():
    invoer = _invoer()
    zonder = _doc(invoer, [_p(invoer, "descriptive_act", {"bron/B1": "O"})], "fail")
    met = _doc(invoer, [_p(invoer, "descriptive_act", {"bron/B1": "O+"})], "fail")
    assert zonder.status == met.status == "review_required"
    bf_zonder = zonder.oordeel["passages"][0]["bronfuncties"][1]
    bf_met = met.oordeel["passages"][0]["bronfuncties"][1]
    assert (bf_zonder["start"], bf_zonder["end"]) == (None, None)
    assert (bf_met["start"], bf_met["end"]) == (0, len(B1))


@pytest.mark.parametrize(
    ("citaat", "detail"),
    [
        ("Een melding telt mee", "niet_gevonden"),  # staat in B2, niet in B1
        ("e", "niet_uniek"),
        ("", "leeg"),
        ("de beheerder legt", "niet_gevonden"),  # geen normalisatie
    ],
)
def test_bronfunctiecitaat_moet_letterlijk_en_uniek_in_die_bron_staan(citaat, detail):
    respons = _geldig()
    respons["passages"][0]["bronfuncties"][1] = {
        "bron": "bron/B1",
        "function": "unclear" if citaat == "" else "actor_prescription",
        "quote": citaat,
    }
    assert _fout(respons) == ("invalid_citation", detail)


def test_passagecitaat_moet_letterlijk_en_uniek_in_de_kern_staan():
    respons = _geldig()
    respons["passages"][0]["quote"] = "niet in de kern"
    assert _fout(respons) == ("invalid_citation", "niet_gevonden")
    respons["passages"][0]["quote"] = "e"
    assert _fout(respons) == ("invalid_citation", "niet_uniek")


def test_posities_worden_afgeleid_voor_passage_en_bronfuncties():
    invoer = _invoer(bedoeling=BED_KENMERK)
    document = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bedoeling": "C", "bron/B2": "C"})],
        "pass",
    )
    oordeel = document.oordeel
    p = oordeel["passages"][0]
    assert (p["start"], p["end"]) == (KERN.index(P), KERN.index(P) + len(P))
    per_bron = {bf["bron"]: bf for bf in p["bronfuncties"]}
    assert (per_bron["bedoeling"]["start"], per_bron["bedoeling"]["end"]) == (
        0,
        len(BED_KENMERK),
    )
    assert (per_bron["bron/B2"]["start"], per_bron["bron/B2"]["end"]) == (0, len(B2))
    assert (per_bron["bron/B1"]["start"], per_bron["bron/B1"]["end"]) == (None, None)


@pytest.mark.parametrize(
    "wijziging",
    [
        {"verdict": "pass", "coverage": "partial"},
        {"verdict": "pass", "question": "Waarom?"},
        {"verdict": "pass", "uncertainty": "decisive"},
        {"verdict": "insufficient_information", "question": "Geen vraag."},
        {"verdict": "insufficient_information", "uncertainty": "none"},
        {"verdict": "fail", "question": "Een? Twee?"},
        {"verdict": "fail", "scope_reason": "buiten bereik"},
        {"verdict": "not_applicable", "scope_reason": "buiten bereik"},
        {"passages": [], "verdict": "fail"},
    ],
    ids=lambda w: repr(w)[:50],
)
def test_eigen_modelverdict_moet_intern_samenhangen(wijziging):
    respons = _geldig()
    if wijziging.get("verdict") == "insufficient_information":
        respons.update({"question": "Is dit een kenmerk?", "uncertainty": "decisive"})
    respons.update(wijziging)
    assert _fout(respons) == ("invalid_output", None)


def test_niet_van_toepassing_blijft_het_modeloordeel():
    respons = uitvoer(
        [], "not_applicable", scope_reason="Geen definitie maar een lijst."
    )
    document = beoordeel(
        _invoer(), _configuratie(), respons, Uitvoering(actor="ai", status="completed")
    )
    assert document.status == "not_applicable"
    assert document.omzetting is None
    assert _afleiding(document) == "niet_van_toepassing"


def test_volgorde_van_bronfuncties_wordt_niet_afgedwongen_de_afleiding_wel():
    invoer = _invoer()
    passages = [_p(invoer, "descriptive_act", {"bron/B1": "A", "bron/B3": "N"})]
    geordend = _doc(invoer, passages, "fail")
    omgekeerd_passages = json.loads(json.dumps(passages))
    omgekeerd_passages[0]["bronfuncties"].reverse()
    omgekeerd = _doc(invoer, omgekeerd_passages, "fail")
    assert geordend.status == omgekeerd.status == "fail"
    # De dragende grond volgt de vaste volgorde (B1 vóór B3), niet de modelvolgorde.
    assert _dienstpassage(geordend)["ground"] == _dienstpassage(omgekeerd)["ground"]
    assert _dienstpassage(omgekeerd)["ground"]["ref"] == "B1"


# --- C. beslisregel per tak -------------------------------------------------------------

# Stap 1 — een zelfstandig voorschrift in de kern blijft fail (besluit 1, K1).


def test_stap1_instructie_in_de_kern_is_fail_ook_als_alle_bronnen_zwijgen():
    invoer = _invoer()
    document = _zonder_omzetting(invoer, [_p(invoer, "instruction")], "fail")
    assert _afleiding(document) == "voorschrift_in_kern"
    dp = _dienstpassage(document)
    assert dp["function"] == "actor_prescription"
    assert dp["ground"]["field"] == "kern"
    assert document.melding == _vul(
        MELDING_VN,
        {"{passage}": P, "{handeling/afweging}": "een handeling", "{grond}": "de kern"},
    )


def test_stap1_gaat_voor_een_bronconflict_en_voor_beschrijvende_bronnen():
    invoer = _invoer()
    for codes in ({"bron/B2": "C"}, {"bron/B2": "C", "bron/B1": "A"}):
        document = _zonder_omzetting(invoer, [_p(invoer, "instruction", codes)], "fail")
        assert _afleiding(document) == "voorschrift_in_kern"


def test_stap1_draagt_de_eerste_voorschrijvende_bron_als_grond():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "instruction", {"bron/B1": "A"})], "fail"
    )
    assert document.melding == _vul(
        MELDING_VN,
        {
            "{passage}": P,
            "{handeling/afweging}": "een handeling",
            "{grond}": f"bronpassage B1 ('{B1}')",
        },
    )


# Stap 2 — strijdige betekenisgrond.


def test_stap2_beschrijvend_tegen_voorschrijvend_is_review_met_beide_citaten():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B1": "A", "bron/B2": "C"})],
        "review_required",
    )
    assert _afleiding(document) == "conflict"
    assert document.reden == "insufficient_information"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    reden = (
        f"Strijdige betekenisgrond voor '{P}': bronpassage B2 ('{B2}') gebruikt de "
        "inhoud als kenmerk van het begrip; bronpassage B1 ('"
        f"{B1}') stelt de inhoud als plicht of afweging van een actor; de "
        "bevestigde bedoeling beslist dat niet"
    )
    assert document.melding == _o(reden, _vraag("VRAAG_FUNCTIE"))


def test_stap2_not_a_criterion_tegen_criterion_is_conflict_6a():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C", "bron/B3": "N"})],
        "review_required",
    )
    assert _afleiding(document) == "conflict"
    assert "toont dat de inhoud geen kenmerk van het begrip is" in document.melding
    assert f"bronpassage B3 ('{B3}')" in document.melding


@pytest.mark.parametrize("bedoeling_code", ["A", "N"])
def test_1b_bedoeling_beslecht_een_conflict_naar_gebrek(bedoeling_code):
    invoer = _invoer(bedoeling=BED_OPDRACHT)
    codes = {"bedoeling": bedoeling_code, "bron/B2": "C", "bron/B1": "A"}
    document = _zonder_omzetting(invoer, [_p(invoer, "descriptive_act", codes)], "fail")
    assert _afleiding(document) == "bedoeling_beslist"
    dp = _dienstpassage(document)
    assert dp["function"] == "actor_prescription"
    assert dp["ground"] == {
        "field": "bedoeling",
        "ref": None,
        "quote": BED_OPDRACHT,
        "start": 0,
        "end": len(BED_OPDRACHT),
    }


@pytest.mark.parametrize("tegen", [{"bron/B1": "A"}, {"bron/B3": "N"}])
def test_1b_beschrijvende_bedoeling_beslecht_een_conflict_nooit_naar_pass(tegen):
    invoer = _invoer(bedoeling=BED_KENMERK)
    codes = {"bedoeling": "C", **tegen}
    for verdict in ("pass", "fail", "insufficient_information"):
        document = _doc(invoer, [_p(invoer, "descriptive_act", codes)], verdict)
        assert document.status == "review_required"
        assert _afleiding(document) == "conflict"


def test_stap2_conflict_gaat_voor_het_tweede_signaal_uit_de_kernvorm():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "obligation_form", {"bron/B1": "A", "bron/B2": "C"})],
        "review_required",
    )
    assert _afleiding(document) == "conflict"


# Stap 3 — één richting.


def test_stap3_alleen_beschrijvende_bronnen_is_pass_met_criterium():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", {"bron/B2": "C"})], "pass"
    )
    assert _afleiding(document) == "bronnen_beschrijvend"
    assert document.melding == _vul(
        MELDING_V,
        {
            "{passage}": P,
            "{criterium/afleiding/kenmerk}": "een criterium",
            "{grond}": f"bronpassage B2 ('{B2}')",
        },
    )


def test_stap3_afleiding_heet_een_afleiding_in_de_melding():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "no_act", {"bron/B2": "D"})], "pass"
    )
    assert "beschrijft een afleiding;" in document.melding


def test_stap3_open_bron_naast_beschrijvende_bron_telt_niet():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B1": "O", "bron/B2": "C"})],
        "pass",
    )
    assert _afleiding(document) == "bronnen_beschrijvend"


def test_stap3_moetvorm_met_bron_die_haar_als_kenmerk_aanwijst_is_pass():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "obligation_form", {"bron/B2": "C"})], "pass"
    )
    assert _afleiding(document) == "bronnen_beschrijvend"


@pytest.mark.parametrize(
    "codes",
    [{"bron/B1": "A"}, {"bron/B1": "A", "bron/B2": "O"}, {"bron/B1": "R"}],
    ids=["alleen-A", "A-en-open", "alleen-R"],
)
def test_3a_een_voorschriftbron_zonder_tweede_signaal_is_review(codes):
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", codes)], "review_required"
    )
    assert _afleiding(document) == "bronvoorschrift_niet_overgenomen"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    tekst = B1
    assert f"bronpassage B1 ('{tekst}')" in document.melding


def test_3a_zwijgende_bekende_bedoeling_is_geen_tweede_signaal():
    invoer = _invoer(bedoeling=BED_ZWIJGT)
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", {"bron/B1": "A"})], "review_required"
    )
    assert _afleiding(document) == "bronvoorschrift_niet_overgenomen"


@pytest.mark.parametrize(
    ("kernvorm", "codes", "functie", "grond"),
    [
        ("obligation_form", {"bron/B1": "A"}, "actor_prescription", "B1"),
        ("discretion_form", {"bron/B1": "R"}, "discretionary_decision_rule", "B1"),
        (
            "descriptive_act",
            {"bron/B1": "A", "bron/B3": "N"},
            "actor_prescription",
            "B1",
        ),
        (
            "descriptive_act",
            {"bron/B1": "R", "bron/B3": "N"},
            "discretionary_decision_rule",
            "B1",
        ),
    ],
    ids=["moetvorm", "discretievorm", "voorschrift-en-geen-kenmerk", "discretie-en-N"],
)
def test_3a_voorschriftbron_met_tweede_signaal_is_fail(kernvorm, codes, functie, grond):
    invoer = _invoer()
    document = _zonder_omzetting(invoer, [_p(invoer, kernvorm, codes)], "fail")
    assert _afleiding(document) == "voorschrift_bevestigd"
    dp = _dienstpassage(document)
    assert dp["function"] == functie
    assert (dp["ground"]["field"], dp["ground"]["ref"]) == ("bron", grond)
    if functie == "discretionary_decision_rule":
        assert document.melding.endswith(_vul(MELDING_VN_DISCRETIE, {"{citaat}": P}))


@pytest.mark.parametrize("extra", [{}, {"bron/B1": "A"}], ids=["alleen", "met-B1"])
def test_3a_bedoeling_die_het_voorschrift_zelf_draagt_is_tweede_signaal(extra):
    invoer = _invoer(bedoeling=BED_OPDRACHT)
    codes = {"bedoeling": "A", **extra}
    document = _zonder_omzetting(invoer, [_p(invoer, "descriptive_act", codes)], "fail")
    assert _afleiding(document) == "voorschrift_bevestigd"
    assert _dienstpassage(document)["ground"]["field"] == "bedoeling"


def test_6a_alleen_not_a_criterion_is_geen_fail():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", {"bron/B3": "N"})], "review_required"
    )
    assert _afleiding(document) == "bronvoorschrift_niet_overgenomen"
    assert "toont dat de inhoud geen kenmerk van het begrip is" in document.melding


def test_twee_voorschriftbronnen_zonder_ander_signaal_blijven_review():
    """Ontwerp §2.3: het tweede signaal is kernvorm, N-bron of bedoeling; een
    tweede G-bron telt niet (dat was optie 6B, niet gekozen)."""
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B1": "A", "bron/B2": "A"})],
        "review_required",
    )
    assert _afleiding(document) == "bronvoorschrift_niet_overgenomen"


@pytest.mark.parametrize("code", ["O", "O+"])
def test_stap3_alleen_open_bronnen_is_review(code):
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", {"bron/B1": code})], "review_required"
    )
    assert _afleiding(document) == "bronnen_open"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    assert "bronpassage B1" in document.melding


# Stap 4 — alle grondbronnen zwijgen.


@pytest.mark.parametrize("bedoeling", [None, BED_ZWIJGT])
def test_stap4_geen_handeling_is_pass_op_de_kern(bedoeling):
    invoer = _invoer(bedoeling=bedoeling)
    document = _zonder_omzetting(invoer, [_p(invoer, "no_act")], "pass")
    assert _afleiding(document) == "alleen_kern"
    assert document.melding == _vul(
        MELDING_V,
        {
            "{passage}": P,
            "{criterium/afleiding/kenmerk}": "een criterium",
            "{grond}": "de kern",
        },
    )


def test_5a_beschrijvende_handeling_zonder_grond_en_bedoeling_is_review():
    invoer = _invoer(bedoeling=None)
    for verdict in ("pass", "fail"):
        document = _doc(invoer, [_p(invoer, "descriptive_act")], verdict)
        assert document.status == "review_required"
        assert _afleiding(document) == "geen_grond_zonder_bedoeling"
        assert document.vraag == _vraag("VRAAG_FUNCTIE")


def test_5a_beschrijvende_handeling_met_bekende_zwijgende_bedoeling_is_pass():
    invoer = _invoer(bedoeling=BED_ZWIJGT)
    document = _zonder_omzetting(invoer, [_p(invoer, "descriptive_act")], "pass")
    assert _afleiding(document) == "alleen_kern"


def test_stap4_moetvorm_zonder_bronnen_is_fail():
    invoer = _invoer()
    document = _zonder_omzetting(invoer, [_p(invoer, "obligation_form")], "fail")
    assert _afleiding(document) == "voorschrift_in_kern"
    assert _dienstpassage(document)["function"] == "actor_prescription"


def test_stap4_discretievorm_zonder_bedoeling_is_de_dienstregel_van_besluit12():
    invoer = _invoer(bedoeling=None)
    document = _doc(invoer, [_p(invoer, "discretion_form")], "fail")
    assert document.status == "review_required"
    assert _afleiding(document) == "discretie_zonder_bedoeling"
    assert document.omzetting == "discretie_zonder_bedoeling"
    vraag = _vraag("VRAAG_DISCRETIE_ZONDER_BEDOELING")
    assert document.vraag == vraag
    reden = _vul(contract.REDEN_DISCRETIE_ZONDER_BEDOELING, {"{citaat}": P})
    assert document.melding == _o(reden, vraag)


def test_stap4_discretievorm_met_bekende_bedoeling_is_discretionaire_fail():
    invoer = _invoer(bedoeling=BED_ZWIJGT)
    document = _zonder_omzetting(invoer, [_p(invoer, "discretion_form")], "fail")
    assert _afleiding(document) == "voorschrift_in_kern"
    assert _dienstpassage(document)["function"] == "discretionary_decision_rule"
    assert MELDING_VN_DISCRETIE.split("'")[0] in document.melding


def test_open_context_gaat_voor_stap4():
    invoer = _invoer(bedoeling=BED_ZWIJGT)
    document = _doc(
        invoer,
        [_p(invoer, "no_act", {"organisatorische_context/0": "O"})],
        "insufficient_information",
    )
    assert _afleiding(document) == "bronnen_open"


# Over passages: fail vóór review vóór pass (SC-C-03); pass vraagt dekking.


def test_fail_gaat_voor_review_en_noemt_het_open_punt():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [
            _p(invoer, "instruction", quote=P_KOP),
            _p(invoer, "descriptive_act", {"bron/B1": "A"}),
        ],
        "fail",
    )
    assert _afleiding(document) == "voorschrift_in_kern"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    vn = _vul(
        MELDING_VN,
        {
            "{passage}": P_KOP,
            "{handeling/afweging}": "een handeling",
            "{grond}": "de kern",
        },
    )
    assert document.melding.startswith(
        vn + " Daarnaast onvoldoende informatie: Alleen "
    )
    assert document.melding.endswith(f"Vraag: {_vraag('VRAAG_FUNCTIE')}")


def test_review_gaat_voor_pass():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [
            _p(invoer, "no_act", quote=P_KOP),
            _p(invoer, "descriptive_act", {"bron/B1": "A", "bron/B2": "C"}),
        ],
        "review_required",
    )
    assert _afleiding(document) == "conflict"
    soorten = [p["uitkomst"] for p in document.oordeel["dienst"]["passages"]]
    assert soorten == ["beschrijvend", "review"]


def test_pass_vraagt_volledige_dekking():
    invoer = _invoer()
    document = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C"})],
        "fail",
        coverage="partial",
    )
    assert document.status == "review_required"
    assert _afleiding(document) == "onvolledige_dekking"
    assert document.vraag == _vraag("VRAAG_DEKKING")


def test_fail_is_niet_afhankelijk_van_de_dekking():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "instruction")], "fail", coverage="partial"
    )
    assert _afleiding(document) == "voorschrift_in_kern"


def test_melding_volgt_de_eerste_dragende_passage_in_de_kern():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer,
        [_p(invoer, "instruction"), _p(invoer, "instruction", quote=P_KOP)],
        "fail",
    )
    assert f"'{P_KOP}' schrijft" in document.melding


# --- D. keuze 2A: de dienst beslist, de afwijking is zichtbaar --------------------------


@pytest.mark.parametrize(
    ("kernvorm", "codes", "verdict", "status", "omzetting"),
    [
        (
            "descriptive_act",
            {"bron/B1": "A"},
            "fail",
            "review_required",
            "bronvoorschrift_niet_overgenomen",
        ),
        (
            "descriptive_act",
            {"bron/B1": "A", "bron/B2": "C"},
            "pass",
            "review_required",
            "conflict",
        ),
        ("descriptive_act", {"bron/B2": "C"}, "fail", "pass", "bronnen_beschrijvend"),
        ("instruction", {"bron/B2": "C"}, "pass", "fail", "voorschrift_in_kern"),
        ("instruction", {}, "insufficient_information", "fail", "voorschrift_in_kern"),
    ],
    ids=[
        "fail-naar-review",
        "pass-naar-review",
        "fail-naar-pass",
        "pass-naar-fail",
        "review-naar-fail",
    ],
)
def test_2a_omzetting_is_zichtbaar_en_het_modelverdict_blijft_bewaard(
    kernvorm, codes, verdict, status, omzetting
):
    invoer = _invoer()
    document = _doc(invoer, [_p(invoer, kernvorm, codes)], verdict)
    assert document.status == status
    assert document.omzetting == omzetting == _afleiding(document)
    assert document.oordeel["verdict"] == verdict
    assert document.oordeel["dienst"]["modelstatus"] == VERDICT_STATUS[verdict]


VERDICT_STATUS = {
    "pass": "pass",
    "fail": "fail",
    "insufficient_information": "review_required",
}


def test_2a_geen_omzetting_bij_gelijke_status_ook_niet_bij_eigen_modelvraag():
    invoer = _invoer()
    eigen = "Wat bedoelt de opsteller met deze zin?"
    document = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B1": "A"})],
        "insufficient_information",
        question=eigen,
    )
    assert document.status == "review_required"
    assert document.omzetting is None
    # 4A: de vaste vraag; de modelvraag blijft zichtbaar in het oordeel.
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    assert document.oordeel["question"] == eigen


def test_mens_beslist_zelf_zonder_omzetting():
    invoer = _invoer()
    fail = _doc(invoer, [_p(invoer, "instruction")], "fail", actor="human")
    assert (fail.status, fail.omzetting) == ("fail", None)
    eigen = "Is de registratie een kenmerk?"
    review = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C"})],
        "insufficient_information",
        actor="human",
        question=eigen,
    )
    assert (review.status, review.omzetting, review.vraag) == (
        "review_required",
        None,
        eigen,
    )


@pytest.mark.parametrize(
    ("kernvorm", "codes", "verdict"),
    [
        ("descriptive_act", {"bron/B1": "A", "bron/B2": "C"}, "pass"),
        ("descriptive_act", {"bron/B2": "C"}, "fail"),
        ("instruction", {}, "insufficient_information"),
    ],
    ids=["pass-tegen-conflict", "fail-zonder-gebrek", "review-met-gebrek"],
)
def test_mensoordeel_dat_tegen_de_bronfuncties_ingaat_is_invalid_output(
    kernvorm, codes, verdict
):
    invoer = _invoer()
    document = _doc(invoer, [_p(invoer, kernvorm, codes)], verdict, actor="human")
    assert (document.status, document.foutcategorie) == ("error", "invalid_output")


# --- E. keuze 4A: vaste vraag, bronnen en citaten in de reden -------------------------


@pytest.mark.parametrize(
    ("bedoeling", "kernvorm", "codes", "vraagnaam"),
    [
        (None, "descriptive_act", {"bron/B1": "A", "bron/B2": "C"}, "VRAAG_FUNCTIE"),
        (None, "descriptive_act", {"bron/B1": "A"}, "VRAAG_FUNCTIE"),
        (None, "descriptive_act", {"bron/B1": "O"}, "VRAAG_FUNCTIE"),
        (None, "descriptive_act", {}, "VRAAG_FUNCTIE"),
        (None, "discretion_form", {}, "VRAAG_DISCRETIE_ZONDER_BEDOELING"),
    ],
    ids=["conflict", "bronvoorschrift", "open", "geen-grond", "discretie"],
)
def test_4a_vaste_invoeronafhankelijke_vraag_per_reviewsoort(
    bedoeling, kernvorm, codes, vraagnaam
):
    vraag = _vraag(vraagnaam)
    assert vraag.count("?") == 1 and vraag.endswith("?")
    for begrip in ("melding", "ander begrip"):
        invoer = dataclasses.replace(_invoer(bedoeling=bedoeling), begrip=begrip)
        document = _doc(invoer, [_p(invoer, kernvorm, codes)], "fail")
        assert document.status == "review_required"
        assert document.vraag == vraag


def test_4a_vaste_vragen_verschillen_per_soort():
    vragen = {
        _vraag(n)
        for n in ("VRAAG_FUNCTIE", "VRAAG_DEKKING", "VRAAG_DISCRETIE_ZONDER_BEDOELING")
    }
    assert len(vragen) == 3


# --- F. hercontrole en manipulatie ----------------------------------------------------


def _omgezet():
    invoer = _invoer()
    document = _doc(invoer, [_p(invoer, "descriptive_act", {"bron/B1": "A"})], "fail")
    assert document.omzetting == "bronvoorschrift_niet_overgenomen"
    return invoer, document


def _niet_omgezet():
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, "descriptive_act", {"bron/B2": "C"})], "pass"
    )
    return invoer, document


def test_geldig_document_is_bij_hercontrole_het_bewaarde_oordeel():
    for invoer, document in (_omgezet(), _niet_omgezet()):
        actueel = toets_actualiteit(document, invoer, _configuratie())
        assert (actueel.status, actueel.reden, actueel.melding) == (
            document.status,
            document.reden,
            document.melding,
        )


def _gemanipuleerd(document, **velden):
    kopie = dataclasses.replace(document)
    for naam, waarde in velden.items():
        object.__setattr__(kopie, naam, waarde)
    return kopie


def _oordeel_met(document, wijzig) -> str:
    oordeel = document.oordeel
    wijzig(oordeel)
    return json.dumps(oordeel, ensure_ascii=False, sort_keys=True)


def _modelverdict(waarde):
    def wijzig(o):
        o["verdict"] = waarde

    return wijzig


def _dienstveld(sleutel, waarde):
    def wijzig(o):
        o["dienst"][sleutel] = waarde

    return wijzig


def _dienstfunctie(o):
    o["dienst"]["passages"][0]["function"] = "criterion"


def _zonder_dienst(o):
    del o["dienst"]


@pytest.mark.parametrize(
    "manipulatie",
    [
        lambda d: {"omzetting": None},
        lambda d: {"omzetting": "conflict"},
        lambda d: {"status": "fail"},
        lambda d: {"vraag": "Andere vraag?"},
        lambda d: {"oordeel_json": _oordeel_met(d, _modelverdict("pass"))},
        lambda d: {
            "oordeel_json": _oordeel_met(d, _modelverdict("insufficient_information"))
        },
        lambda d: {
            "oordeel_json": _oordeel_met(d, _dienstveld("afleiding", "conflict"))
        },
        lambda d: {
            "oordeel_json": _oordeel_met(
                d, _dienstveld("modelstatus", "review_required")
            )
        },
        lambda d: {"oordeel_json": _oordeel_met(d, _dienstfunctie)},
        lambda d: {"oordeel_json": _oordeel_met(d, _zonder_dienst)},
    ],
    ids=[
        "omzetting-weg",
        "andere-omzetting",
        "status",
        "vraag",
        "modelverdict-pass",
        "modelverdict-review",
        "afleiding",
        "modelstatus",
        "dienstfunctie",
        "dienstblok-weg",
    ],
)
def test_manipulatie_van_omgezet_document_is_error_bij_hercontrole(manipulatie):
    invoer, document = _omgezet()
    vals = _gemanipuleerd(document, **manipulatie(document))
    actueel = toets_actualiteit(vals, invoer, _configuratie())
    assert (actueel.status, actueel.melding) == ("error", MELDING_E)


@pytest.mark.parametrize(
    "velden",
    [
        lambda d: {"omzetting": "bronnen_beschrijvend"},
        lambda d: {"oordeel_json": _oordeel_met(d, _modelverdict("fail"))},
    ],
    ids=["omzetting-erbij", "modelverdict-fail-zonder-omzetting"],
)
def test_manipulatie_van_niet_omgezet_document_is_error_bij_hercontrole(velden):
    invoer, document = _niet_omgezet()
    vals = _gemanipuleerd(document, **velden(document))
    actueel = toets_actualiteit(vals, invoer, _configuratie())
    assert actueel.status == "error"


def test_document_bewaart_modeluitvoer_en_dienstafleiding_serialiseerbaar():
    _, document = _omgezet()
    data = json.loads(json.dumps(document.als_dict(), ensure_ascii=False))
    assert data["contractversie"] == V4
    assert data["omzetting"] == "bronvoorschrift_niet_overgenomen"
    oordeel = data["oordeel"]
    assert oordeel["verdict"] == "fail"
    assert set(oordeel) == {
        "passages",
        "reason",
        "question",
        "uncertainty",
        "coverage",
        "scope_reason",
        "verdict",
        "dienst",
    }
    assert set(oordeel["dienst"]) == {"afleiding", "modelstatus", "passages"}
    dp = oordeel["dienst"]["passages"][0]
    assert set(dp) == {
        "quote",
        "start",
        "end",
        "function",
        "ground",
        "uitkomst",
        "regel",
    }
    assert set(dp["ground"]) == {"field", "ref", "quote", "start", "end"}


# --- H. besluit 17: beslissende modelonzekerheid blokkeert een afgeleide pass -----------
#
# Chris (07-10-2026, optie A): meldt het model `uncertainty` = "decisive" en zou de
# dienst anders pass afleiden, dan wordt het review_required met een vaste vraag
# en de code `model_beslissend_onzeker`. Een afgeleid gebrek gaat voor (fail
# blijft fail). Het modeloordeel, met zijn eigen vraag, blijft in het document.

ONZEKER = "model_beslissend_onzeker"


def test_17_review_naar_pass_wordt_review_met_vaste_vraag():
    # Was 2A "review-naar-pass" (besluit 16); sinds besluit 17 geen pass meer.
    invoer = _invoer()
    eigen = "Is de registratie een kenmerk van de melding?"
    document = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C"})],
        "insufficient_information",
        question=eigen,
    )
    assert (document.status, document.reden) == (
        "review_required",
        "insufficient_information",
    )
    assert _afleiding(document) == contract.REGEL_MODEL_BESLISSEND_ONZEKER == ONZEKER
    # Status gelijk aan de modelstatus: geen omzetting (2A).
    assert document.omzetting is None
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    assert document.vraag in document.melding
    # Het modeloordeel blijft zichtbaar: eigen verdict, onzekerheid en vraag.
    oordeel = document.oordeel
    assert (oordeel["verdict"], oordeel["uncertainty"], oordeel["question"]) == (
        "insufficient_information",
        "decisive",
        eigen,
    )
    # De afgeleide kenmerkpassage staat er nog, met haar grond.
    assert _dienstpassage(document)["uitkomst"] == "beschrijvend"
    assert f"'{P}'" in document.melding and f"'{B2}'" in document.melding


@pytest.mark.parametrize(
    ("kernvorm", "codes"),
    [
        ("descriptive_act", {"bron/B2": "C"}),
        ("descriptive_act", {"bron/B2": "C", "bron/B3": "D"}),
        ("no_act", {}),
    ],
    ids=["kenmerkbron", "alle-bronnen-kenmerk", "alleen-kern"],
)
def test_17_fail_met_beslissende_onzekerheid_en_kenmerkgrond_wordt_review(
    kernvorm, codes
):
    invoer = _invoer()
    document = _doc(
        invoer, [_p(invoer, kernvorm, codes)], "fail", uncertainty="decisive"
    )
    assert document.status == "review_required"
    assert _afleiding(document) == ONZEKER
    # Afwijking van het modelverdict (fail → review): zichtbaar als omzetting.
    assert document.omzetting == ONZEKER
    assert document.oordeel["dienst"]["modelstatus"] == "fail"
    assert document.oordeel["verdict"] == "fail"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")


@pytest.mark.parametrize(
    ("kernvorm", "codes", "verdict"),
    [
        ("instruction", {"bron/B2": "C"}, "fail"),
        ("instruction", {}, "insufficient_information"),
        ("descriptive_act", {"bron/B1": "A", "bron/B3": "N"}, "fail"),
        ("obligation_form", {"bron/B1": "A"}, "insufficient_information"),
    ],
    ids=["kernvoorschrift", "kernvoorschrift-model-review", "G-en-N", "moetvorm-en-A"],
)
def test_17_beslissend_onzeker_met_aantoonbaar_gebrek_blijft_fail(
    kernvorm, codes, verdict
):
    invoer = _invoer()
    document = _doc(
        invoer, [_p(invoer, kernvorm, codes)], verdict, uncertainty="decisive"
    )
    assert document.status == "fail"
    assert _afleiding(document) != ONZEKER
    assert document.omzetting in (None, _afleiding(document))


def test_17_gebrek_gaat_voor_ook_naast_een_kenmerkpassage():
    invoer = _invoer()
    document = _doc(
        invoer,
        [
            _p(invoer, "descriptive_act", {"bron/B2": "C"}),
            _p(invoer, "instruction", quote=P_KOP),
        ],
        "fail",
        uncertainty="decisive",
    )
    assert document.status == "fail"
    assert _afleiding(document) == "voorschrift_in_kern"


@pytest.mark.parametrize("onzekerheid", ["none", "non_decisive"])
@pytest.mark.parametrize(
    ("kernvorm", "codes", "afleiding"),
    [
        ("descriptive_act", {"bron/B2": "C"}, "bronnen_beschrijvend"),
        ("no_act", {}, "alleen_kern"),
    ],
    ids=["kenmerkbron", "alleen-kern"],
)
def test_17_zonder_beslissende_onzekerheid_blijft_kenmerk_pass(
    kernvorm, codes, afleiding, onzekerheid
):
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, kernvorm, codes)], "pass", uncertainty=onzekerheid
    )
    assert _afleiding(document) == afleiding


def test_17_eigen_reviewgrond_gaat_voor_de_onzekerheidsregel():
    # Een afgeleide reviewpassage of onvolledige dekking houdt haar eigen code.
    invoer = _invoer()
    open_ = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B1": "A"})],
        "insufficient_information",
    )
    assert _afleiding(open_) == "bronvoorschrift_niet_overgenomen"
    dekking = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C"})],
        "insufficient_information",
        coverage="partial",
    )
    assert _afleiding(dekking) == "onvolledige_dekking"


def test_17_omgezet_document_is_bij_hercontrole_herleidbaar_en_manipulatie_error():
    invoer = _invoer()
    document = _doc(
        invoer,
        [_p(invoer, "descriptive_act", {"bron/B2": "C"})],
        "fail",
        uncertainty="decisive",
    )
    assert document.omzetting == ONZEKER
    actueel = toets_actualiteit(document, invoer, _configuratie())
    assert actueel.status == "review_required"
    assert (actueel.reden, actueel.melding) == (document.reden, document.melding)
    vervalst = _gemanipuleerd(document, status="pass", omzetting=None)
    assert toets_actualiteit(vervalst, invoer, _configuratie()).status == "error"

    def zeker(o):
        o["uncertainty"] = "none"

    zonder_twijfel = _gemanipuleerd(
        document, oordeel_json=_oordeel_met(document, zeker)
    )
    assert toets_actualiteit(zonder_twijfel, invoer, _configuratie()).status == "error"


@pytest.mark.parametrize(
    ("kernvorm", "verdict", "van", "naar"),
    [
        ("no_act", "pass", "none", "non_decisive"),
        ("instruction", "fail", "decisive", "none"),
    ],
    ids=["pass-none-naar-non_decisive", "kernvoorschrift-decisive-naar-none"],
)
def test_17_replay_toetst_samenhang_niet_de_echtheid_van_de_onzekerheid(
    kernvorm, verdict, van, naar
):
    # Herreview Codex P3: een gewijzigde onzekerheid die de uitkomst niet
    # verandert, blijft bij hercontrole geldig. Echtheid van het modelantwoord
    # is een zaak van de opslaglaag (DEF-626), niet van replay.
    invoer = _invoer()
    document = _zonder_omzetting(
        invoer, [_p(invoer, kernvorm)], verdict, uncertainty=van
    )

    def anders(o):
        o["uncertainty"] = naar

    gewijzigd = _gemanipuleerd(document, oordeel_json=_oordeel_met(document, anders))
    actueel = toets_actualiteit(gewijzigd, invoer, _configuratie())
    assert (actueel.status, actueel.melding) == (document.status, document.melding)


# --- I. P1 (Codex-review): een lege of alleen-witruimtebron draagt geen oordeel -------


def _witruimte_invoer(tekst: str = " "):
    return _invoer(bronnen=(("B1", tekst),))


def test_witruimtebron_als_kenmerkgrond_is_niet_herleidbaar():
    # Reproductie Codex P1: bedoeling onbekend, descriptive_act, context zwijgt,
    # B1 = " " als criterion met citaat " " gaf pass.
    invoer = _witruimte_invoer()
    functies = {"bron/B1": ("criterion", " ")}
    document = _doc(invoer, [passage(invoer, P, "descriptive_act", functies)], "pass")
    assert (document.status, document.foutcategorie, document.foutdetail) == (
        "error",
        "invalid_citation",
        "grond_niet_herleidbaar",
    )


@pytest.mark.parametrize("tekst", ["", " ", "\t\n "])
@pytest.mark.parametrize(
    "functie",
    ["criterion", "actor_prescription", "not_a_criterion", "unclear"],
)
def test_lege_bron_draagt_geen_enkele_functie(tekst, functie):
    invoer = _witruimte_invoer(tekst)
    citaat = None if functie == "unclear" else (tekst or None)
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": (functie, citaat)})],
        "fail",
    )
    assert document.status == "error"
    if citaat is not None or functie == "unclear":
        assert document.foutcategorie == "invalid_citation"
        assert document.foutdetail == "grond_niet_herleidbaar"


def test_lege_bron_mag_zwijgen():
    # Volledigheid blijft gelden: de lege bron zwijgt, de kern beslist (5A).
    invoer = _witruimte_invoer()
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act")],
        "insufficient_information",
    )
    assert document.status == "review_required"
    assert _afleiding(document) == "geen_grond_zonder_bedoeling"


@pytest.mark.parametrize("citaat", [" ", "  ", "\t"])
def test_citaat_van_alleen_witruimte_is_leeg_ook_in_een_gevulde_bron(citaat):
    # Een uniek witruimtecitaat in een gevulde bron toont geen functie.
    invoer = _invoer(bronnen=(("B1", "Registratie\tverplicht  hier."),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", citaat)})],
        "pass",
    )
    assert (document.status, document.foutcategorie, document.foutdetail) == (
        "error",
        "invalid_citation",
        "leeg",
    )


# --- J. P1-rest (herreview Codex): inhoudsloze tekst draagt geen oordeel ---------------
#
# Betekenisdragend = minstens één zichtbare letter: Unicode-categorie L*, zonder de
# onzichtbare Hangul-fillers (herreview 2). Alleen cijfers is niet betekenisdragend.
# Geldt in de /4-route voor elk passagecitaat, elk grondcitaat en elke grondbron
# die een functie draagt (bron, bedoeling, contextitem).

#: Hangul-fillers U+115F, U+1160, U+3164, U+FFA0: categorie Lo, renderen als leeg.
FILLERS = [chr(c) for c in (0x115F, 0x1160, 0x3164, 0xFFA0)]
#: Egyptische hiërogliefen FULL BLANK en HALF BLANK (Lo), ook leeg.
BLANCO = [chr(c) for c in (0x13441, 0x13442)]
ONZICHTBAAR = [*FILLERS, *BLANCO]
CIJFERS = ["7", "٣", "12"]
INHOUDSLOOS = ["...", "—", ".", " - ", "\t\t", "\n\n", "?!", *ONZICHTBAAR, *CIJFERS]
INHOUDSLOOS_ZONDER_WITRUIMTE = ["...", "—", ".", "?!", "-–—", *ONZICHTBAAR, *CIJFERS]
CITAAT_INHOUDSLOOS = ["...", "—", "\t", "\n", " - ", *ONZICHTBAAR, "7"]
F = chr(0x1160)  # HANGUL JUNGSEONG FILLER, de reproductie van Codex
LEEG = " ".join(ONZICHTBAAR)  # elk onzichtbaar teken precies één keer


def _uitslag(document) -> tuple[str, str | None, str | None]:
    return (document.status, document.foutcategorie, document.foutdetail)


def test_reproductie_codex_a_grondcitaat_punt_draagt_geen_pass():
    # Zonder grond is dit review_required (5A); met `criterion` op alleen "." was
    # het pass.
    invoer = _invoer(bronnen=(("B1", "Registratie is verplicht."),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", ".")})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


def test_reproductie_codex_b_tab_als_passage_draagt_geen_pass():
    invoer = dataclasses.replace(_invoer(), kern="Melding\tdie is vastgelegd.")
    document = _doc(invoer, [passage(invoer, "\t", "no_act")], "pass")
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


def test_reproductie_codex_2_filler_als_grondcitaat_draagt_geen_pass():
    invoer = _invoer(bronnen=(("B1", f"Registratie is{F} verplicht."),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", F)})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


def test_reproductie_codex_2_filler_als_passage_draagt_geen_pass():
    invoer = dataclasses.replace(_invoer(), kern=f"Melding{F}die is vastgelegd.")
    document = _doc(invoer, [passage(invoer, F, "no_act")], "pass")
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


def test_reproductie_codex_2_filler_als_bedoeling_draagt_geen_pass():
    invoer = _invoer(bedoeling=F)
    document = _doc(invoer, [_p(invoer, "descriptive_act")], "pass")
    assert document.status == "review_required"
    assert _afleiding(document) == "geen_grond_zonder_bedoeling"


def test_reproductie_codex_2_alleen_cijfers_als_grondcitaat_draagt_geen_pass():
    # Zonder grond is dit review (5A); "7" uit "Artikel 7." maakte er pass van.
    invoer = _invoer(bronnen=(("B1", "Artikel 7."),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", "7")})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


@pytest.mark.parametrize("tekst", INHOUDSLOOS)
def test_inhoudsloze_bron_draagt_geen_functie(tekst):
    invoer = _invoer(bronnen=(("B1", tekst),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", tekst)})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "grond_niet_herleidbaar")


@pytest.mark.parametrize("tekst", INHOUDSLOOS_ZONDER_WITRUIMTE)
def test_inhoudsloze_bedoeling_draagt_geen_functie(tekst):
    invoer = _invoer(bedoeling=tekst)
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bedoeling": ("criterion", tekst)})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "grond_niet_herleidbaar")


@pytest.mark.parametrize("tekst", INHOUDSLOOS_ZONDER_WITRUIMTE)
def test_inhoudsloos_contextitem_draagt_geen_functie(tekst):
    invoer = dataclasses.replace(_invoer(), organisatorische_context=(tekst,))
    functies = {"organisatorische_context/0": ("actor_prescription", tekst)}
    document = _doc(
        invoer,
        [passage(invoer, P, "obligation_form", functies)],
        "fail",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "grond_niet_herleidbaar")


@pytest.mark.parametrize("tekst", INHOUDSLOOS)
def test_inhoudsloze_bron_mag_wel_zwijgen(tekst):
    invoer = _invoer(bronnen=(("B1", tekst),))
    document = _doc(
        invoer, [passage(invoer, P, "descriptive_act")], "insufficient_information"
    )
    assert _afleiding(document) == "geen_grond_zonder_bedoeling"


@pytest.mark.parametrize("tekst", INHOUDSLOOS_ZONDER_WITRUIMTE)
def test_inhoudsloze_bedoeling_telt_in_stap4_als_onbekend(tekst):
    # Alle grondbronnen zwijgen. Een bedoeling zonder zichtbare letter maakt
    # een beschrijvende handeling niet tot pass (5A) en een discretievorm niet
    # tot fail (besluit 12): zij geldt als onbekend.
    invoer = _invoer(bedoeling=tekst)
    for verdict in ("pass", "fail"):
        document = _doc(invoer, [_p(invoer, "descriptive_act")], verdict)
        assert document.status == "review_required"
        assert _afleiding(document) == "geen_grond_zonder_bedoeling"
    document = _doc(invoer, [_p(invoer, "discretion_form")], "fail")
    assert document.status == "review_required"
    assert _afleiding(document) == "discretie_zonder_bedoeling"


@pytest.mark.parametrize("citaat", CITAAT_INHOUDSLOOS)
def test_inhoudsloos_grondcitaat_in_gevulde_bron_is_leeg(citaat):
    bron = f"Registratie... verplicht —\tals\nwel - hier {LEEG} artikel 7"
    invoer = _invoer(bronnen=(("B1", bron),))
    document = _doc(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", citaat)})],
        "pass",
    )
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


@pytest.mark.parametrize("citaat", CITAAT_INHOUDSLOOS)
def test_inhoudsloos_passagecitaat_in_de_kern_is_leeg(citaat):
    kern = f"Melding... die —\tals\nwel - is {LEEG} per artikel 7 vastgelegd."
    invoer = dataclasses.replace(_invoer(), kern=kern)
    document = _doc(invoer, [passage(invoer, citaat, "no_act")], "pass")
    assert _uitslag(document) == ("error", "invalid_citation", "leeg")


def test_niet_ascii_letter_is_wel_betekenisdragend():
    # "é" is één letter (Unicode); als passage, als bron en als citaat geldig.
    invoer = dataclasses.replace(
        _invoer(bronnen=(("B1", "é"),)), kern="Café dat open is."
    )
    document = _zonder_omzetting(
        invoer,
        [passage(invoer, "é", "descriptive_act", {"bron/B1": ("criterion", "é")})],
        "pass",
    )
    assert _afleiding(document) == "bronnen_beschrijvend"


@pytest.mark.parametrize(
    ("bron", "citaat"),
    [
        ("Zie artikel 7.", "artikel 7"),
        ("Η εγγραφή is verplicht.", "εγγραφή"),
        ("Регистрация is verplicht.", "Регистрация"),
    ],
    ids=["artikel-7", "grieks", "cyrillisch"],
)
def test_citaat_met_een_zichtbare_letter_is_geldig(bron, citaat):
    invoer = _invoer(bronnen=(("B1", bron),))
    document = _zonder_omzetting(
        invoer,
        [passage(invoer, P, "descriptive_act", {"bron/B1": ("criterion", citaat)})],
        "pass",
    )
    assert _afleiding(document) == "bronnen_beschrijvend"


@pytest.mark.parametrize(
    "tekst", ["é", "a", "ß", "日", "α", "Ω", "ж", "Я", "artikel 7", f"{F}a"]
)
def test_betekenisdragend_heeft_een_zichtbare_letter(tekst):
    assert contract._betekenisdragend(tekst) is True
    assert contract._betekenisdragend(f"—{tekst}…") is True


@pytest.mark.parametrize(
    "tekst",
    [
        *["", " ", "...", "—", "\t\n", "?!", "_", None, 7],
        *CIJFERS,
        "7.",
        *ONZICHTBAAR,
        "".join(ONZICHTBAAR),
        f"{F} 7",
    ],
)
def test_niet_betekenisdragend(tekst):
    assert contract._betekenisdragend(tekst) is False


def test_blanco_hierogliefen_zijn_wat_hun_naam_zegt():
    assert [unicodedata.name(t) for t in BLANCO] == [
        "EGYPTIAN HIEROGLYPH FULL BLANK",
        "EGYPTIAN HIEROGLYPH HALF BLANK",
    ]
    assert {unicodedata.category(t) for t in ONZICHTBAAR} == {"Lo"}


def test_onzichtbare_letters_zijn_alle_letters_met_filler_of_blank_in_de_naam():
    # Borging tegen een Unicode-update: elke letter (L*) die naar zijn naam een
    # opvulteken of blanco is, staat in de constante, en omgekeerd.
    gevonden = set()
    for code in range(sys.maxunicode + 1):
        teken = chr(code)
        naam = unicodedata.name(teken, "")
        if unicodedata.category(teken).startswith("L") and (
            "FILLER" in naam or "BLANK" in naam
        ):
            gevonden.add(teken)
    assert gevonden == contract.ONZICHTBARE_LETTERS == set(ONZICHTBAAR)


@pytest.mark.parametrize(
    ("invoer", "passages"),
    [
        (
            _invoer(bronnen=(("B1", "Registratie is verplicht."),)),
            lambda i: [
                passage(i, P, "descriptive_act", {"bron/B1": ("criterion", ".")})
            ],
        ),
        (
            dataclasses.replace(_invoer(), kern="Melding\tdie is vastgelegd."),
            lambda i: [passage(i, "\t", "no_act")],
        ),
        (
            _invoer(bronnen=(("B1", f"Registratie is{F} verplicht."),)),
            lambda i: [passage(i, P, "descriptive_act", {"bron/B1": ("criterion", F)})],
        ),
        (
            dataclasses.replace(_invoer(), kern=f"Melding{F}die is vastgelegd."),
            lambda i: [passage(i, F, "no_act")],
        ),
        (_invoer(bedoeling=F), lambda i: [_p(i, "descriptive_act")]),
        (
            _invoer(bronnen=(("B1", "Artikel 7."),)),
            lambda i: [
                passage(i, P, "descriptive_act", {"bron/B1": ("criterion", "7")})
            ],
        ),
    ],
    ids=[
        "grondcitaat-punt",
        "passage-tab",
        "grondcitaat-filler",
        "passage-filler",
        "bedoeling-filler",
        "grondcitaat-cijfer",
    ],
)
def test_vervalst_consistent_pass_document_is_error_bij_hercontrole(
    monkeypatch, invoer, passages
):
    """Een document zoals de code vóór dit herstel het zou maken (volledig
    consistent, status pass) is bij hercontrole niet herleidbaar."""
    monkeypatch.setattr(contract, "_betekenisdragend", lambda tekst: True)
    vervalst = _doc(invoer, passages(invoer), "pass")
    assert vervalst.status == "pass"  # testopzet: de oude, te ruime controle
    monkeypatch.undo()
    actueel = toets_actualiteit(vervalst, invoer, _configuratie())
    assert actueel.status == "error"


# --- G. migratie /3 → /4 ----------------------------------------------------------------


def _drie_uitvoer(functie: str, veld: str = "kern") -> dict[str, Any]:
    verdict = "fail" if functie in contract.GEBREK else "pass"
    return {
        "verdict": verdict,
        "passages": [
            {
                "quote": P,
                "function": functie,
                "ground": {"field": veld, "ref": None, "quote": None},
            }
        ],
        "reason": "Synthetisch /3-oordeel.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


def _drie_document(functie: str, bedoeling: str | None = None):
    invoer = _invoer(bedoeling=bedoeling)
    document = contract._beoordeel(
        invoer,
        _configuratie(),
        _drie_uitvoer(functie),
        Uitvoering(actor="ai", status="completed"),
        V3,
    )
    assert document.contractversie == V3
    return invoer, document


@pytest.mark.parametrize(
    ("functie", "status", "omzetting"),
    [
        ("criterion", "pass", None),
        ("actor_prescription", "fail", None),
        (
            "discretionary_decision_rule",
            "review_required",
            "discretie_zonder_bedoeling",
        ),
    ],
)
def test_bewaard_drie_document_blijft_herleidbaar_en_wordt_historisch(
    functie, status, omzetting
):
    invoer, document = _drie_document(functie)
    assert (document.status, document.omzetting) == (status, omzetting)
    actueel = toets_actualiteit(document, invoer, _configuratie())
    assert (actueel.status, actueel.reden, actueel.melding) == (
        "review_required",
        "historical",
        MELDING_HISTORISCH,
    )


def test_gemanipuleerd_drie_document_is_error():
    invoer, document = _drie_document("discretionary_decision_rule")
    vals = _gemanipuleerd(document, omzetting=None)
    assert toets_actualiteit(vals, invoer, _configuratie()).status == "error"


def test_drie_document_dat_als_vier_wordt_opgegeven_is_error():
    invoer, document = _drie_document("criterion")
    vals = _gemanipuleerd(
        document,
        contractversie=V4,
        binding=bereken_binding(invoer, _configuratie()),
    )
    assert toets_actualiteit(vals, invoer, _configuratie()).status == "error"


# --- K. besluit 19 (keuze 1A): een kaal bron-ID wordt de canonieke sleutel ---------------
#
# Uitslag v8, G060: het model schreef "B1" en "B2" in plaats van "bron/B1" en
# "bron/B2". Onder /4 leest de dienst een kaal ID als "bron/<id>" als de
# sleutel zelf geen grondbron is, geen gereserveerde vorm heeft ("bedoeling",
# "<contextveld>/…", "bron/…") en precies één bron dat ID heeft. Het bewaarde
# oordeel bevat alleen canonieke sleutels.


def _kaal(respons, ids=("B1", "B2", "B3")) -> dict[str, Any]:
    """Dezelfde uitvoer met kale bron-ID's ("B1" in plaats van "bron/B1")."""
    kopie = json.loads(json.dumps(respons))
    for p in kopie["passages"]:
        for bf in p["bronfuncties"]:
            if bf["bron"].startswith("bron/") and bf["bron"][len("bron/") :] in ids:
                bf["bron"] = bf["bron"][len("bron/") :]
    return kopie


def _g060_tegenhanger(invoer) -> list[dict[str, Any]]:
    """Synthetisch, naar het patroon van G060: beschrijvende kern; B1 stelt het
    handelen als plicht, B2 gebruikt het als kenmerk (stap 2, conflict)."""
    return [_p(invoer, "descriptive_act", {"bron/B1": "A", "bron/B2": "C"})]


def _ruw(invoer, respons):
    return beoordeel(
        invoer, _configuratie(), respons, Uitvoering(actor="ai", status="completed")
    )


def _sleutels(document) -> list[list[str]]:
    return [
        [bf["bron"] for bf in p["bronfuncties"]] for p in document.oordeel["passages"]
    ]


@pytest.mark.parametrize("verdict", ["insufficient_information", "pass", "fail"])
def test_19_g060_tegenhanger_met_kale_ids_is_review_conflict(verdict):
    invoer = _invoer()
    canoniek = uitvoer(_g060_tegenhanger(invoer), verdict)
    kaal = _kaal(canoniek, ("B1", "B2"))
    assert [bf["bron"] for bf in kaal["passages"][0]["bronfuncties"]] == [
        "organisatorische_context/0",
        "B1",
        "B2",
        "bron/B3",
    ]
    document = _ruw(invoer, kaal)
    assert document.status == "review_required", (
        document.foutcategorie,
        document.foutdetail,
    )
    assert _afleiding(document) == "conflict"
    assert document.reden == "insufficient_information"
    assert document.vraag == _vraag("VRAAG_FUNCTIE")
    assert f"bronpassage B1 ('{B1}')" in document.melding
    assert f"bronpassage B2 ('{B2}')" in document.melding
    # Het bewaarde oordeel is canoniek en gelijk aan dat van de juiste sleutels.
    assert _sleutels(document) == [list(contract.grondbronnen(invoer))]
    assert document == _ruw(invoer, canoniek)


def test_19_alle_bron_ids_kaal_en_meer_passages():
    invoer = _invoer()
    canoniek = uitvoer(
        [
            _p(invoer, "no_act", {"bron/B2": "C"}, quote=P_KOP),
            _p(invoer, "descriptive_act", {"bron/B2": "C", "bron/B3": "C"}),
        ],
        "pass",
    )
    document = _ruw(invoer, _kaal(canoniek))
    assert (document.status, _afleiding(document)) == ("pass", "bronnen_beschrijvend")
    assert _sleutels(document) == [list(contract.grondbronnen(invoer))] * 2
    assert document == _ruw(invoer, canoniek)


@pytest.mark.parametrize(
    "sleutel",
    [
        "B9",
        "b1",
        " B1",
        "B1 ",
        "B11",
        "B",
        "1",
        "bron/b1",
        "Bron/B1",
        "bron B1",
        "bron:B1",
        "/B1",
        "bron//B1",
        "bron/bron/B1",
        "bedoeling/B1",
        "organisatorische_context/B1",
        "bron/B9",
    ],
)
def test_19_onbekend_id_en_elke_andere_afwijkende_sleutel_blijft_niet_herleidbaar(
    sleutel,
):
    invoer = _invoer()
    respons = uitvoer(_g060_tegenhanger(invoer), "insufficient_information")
    (b1,) = [
        bf for bf in respons["passages"][0]["bronfuncties"] if bf["bron"] == "bron/B1"
    ]
    b1["bron"] = sleutel
    assert _fout(respons, invoer) == ("invalid_citation", "grond_niet_herleidbaar")


def test_19_kaal_id_en_canonieke_sleutel_samen_is_een_dubbele_grondbron():
    """Geen dubbelzinnige mapping: "B1" naast "bron/B1" telt als dubbel."""
    invoer = _invoer()
    respons = uitvoer(_g060_tegenhanger(invoer), "insufficient_information")
    (b2,) = [
        bf for bf in respons["passages"][0]["bronfuncties"] if bf["bron"] == "bron/B2"
    ]
    # Zwijgend, zodat alleen de sleutel telt (geen citaat uit B2 in B1).
    b2.update(bron="B1", function="not_addressed", quote=None)
    assert _fout(respons, invoer) == ("invalid_output", None)


@pytest.mark.parametrize(
    ("bron_id", "sleutel"),
    [
        ("bedoeling", "bedoeling"),
        ("juridische_context/0", "juridische_context/0"),
        ("wettelijke_basis/1", "wettelijke_basis/1"),
        ("bron/B1", "bron/B1"),
    ],
    ids=["bedoeling", "contextvorm", "basisvorm", "bronvorm"],
)
def test_19_gereserveerde_sleutelvorm_wordt_nooit_als_bron_gelezen(bron_id, sleutel):
    """Een bron-ID met de vorm van een andere grondbronsleutel: het model kan
    met die sleutel iets anders bedoelen. Geen alias; de juiste sleutel
    `bron/<id>` werkt wel. De bedoeling is onbekend en de contextlijsten zijn
    leeg, dus de sleutel is zelf geen grondbron."""
    invoer = _invoer(bedoeling=None, bronnen=((bron_id, B1), ("B2", B2)))
    assert sleutel not in contract.grondbronnen(invoer)
    juist = uitvoer(
        [_p(invoer, "descriptive_act", {f"bron/{bron_id}": "A", "bron/B2": "C"})],
        "insufficient_information",
    )
    assert _ruw(invoer, juist).status == "review_required"
    for bf in juist["passages"][0]["bronfuncties"]:
        if bf["bron"] == f"bron/{bron_id}":
            bf["bron"] = sleutel
    assert _fout(juist, invoer) == ("invalid_citation", "grond_niet_herleidbaar")


def test_19_alias_is_exact_en_hoofdlettergevoelig_zonder_verwarring():
    """Bronnen "B1" en "b1" naast elkaar: elk kaal ID gaat naar zijn eigen bron.
    Dubbele ID's kan de invoer niet bevatten, dus er is hooguit één treffer."""
    with pytest.raises(contract.Int02ContractError):
        _invoer(bronnen=(("B1", B1), ("B1", B2)))
    invoer = _invoer(bronnen=(("B1", B1), ("b1", B2)))
    canoniek = uitvoer(
        [_p(invoer, "descriptive_act", {"bron/B1": "A", "bron/b1": "C"})],
        "insufficient_information",
    )
    kaal = _kaal(canoniek, ("B1", "b1"))
    document = _ruw(invoer, kaal)
    assert document == _ruw(invoer, canoniek)
    assert _sleutels(document) == [["organisatorische_context/0", "bron/B1", "bron/b1"]]
    assert _afleiding(document) == "conflict"


def test_19_hercontrole_van_het_genormaliseerde_document_is_het_bewaarde_oordeel():
    invoer = _invoer()
    for verdict in ("insufficient_information", "fail"):
        document = _ruw(
            invoer, _kaal(uitvoer(_g060_tegenhanger(invoer), verdict), ("B1", "B2"))
        )
        actueel = toets_actualiteit(document, invoer, _configuratie())
        assert (actueel.status, actueel.reden, actueel.melding) == (
            "review_required",
            "insufficient_information",
            document.melding,
        )
        assert document.omzetting == (None if verdict != "fail" else "conflict")


def test_19_bewaard_oordeel_met_kale_sleutel_is_error_bij_hercontrole():
    """Het bewaarde oordeel is altijd canoniek; een kale sleutel erin kan de
    dienst niet hebben gemaakt (manipulatie) en is niet herleidbaar."""
    invoer = _invoer()
    document = _ruw(
        invoer,
        _kaal(uitvoer(_g060_tegenhanger(invoer), "insufficient_information")),
    )
    assert document.status == "review_required"

    def kaal_in_oordeel(o):
        for p in o["passages"]:
            for bf in p["bronfuncties"]:
                if bf["bron"] == "bron/B1":
                    bf["bron"] = "B1"

    vals = _gemanipuleerd(
        document, oordeel_json=_oordeel_met(document, kaal_in_oordeel)
    )
    assert toets_actualiteit(vals, invoer, _configuratie()).status == "error"


def test_19_sleutels_van_bedoeling_en_context_blijven_ongewijzigd():
    """De alias raakt alleen bron-ID's; bedoeling en contextitems houden hun
    eigen sleutel, ook naast kale bron-ID's."""
    invoer = _invoer(bedoeling=BED_KENMERK)
    canoniek = uitvoer(
        [_p(invoer, "descriptive_act", {"bedoeling": "C", "bron/B2": "C"})], "pass"
    )
    document = _ruw(invoer, _kaal(canoniek))
    assert document.status == "pass"
    assert _sleutels(document) == [list(contract.grondbronnen(invoer))]
    assert document == _ruw(invoer, canoniek)
