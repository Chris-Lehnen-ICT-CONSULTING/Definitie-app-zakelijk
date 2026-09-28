"""DEF-768 — bewijs via genummerde eenheden (`ess05-bewijsregels/6`, schema /3).

Grondslag: reports/DEF-768-AI-20260928-R17/oorzakenonderzoek-ess05-v1.md (optie O2).
Vooraf vastgelegde interpretaties: bewijs voor de mechaniek, niet voor modelgedrag.
"""

from __future__ import annotations

import copy

import pytest

from domain.ess05 import bewijsregels as br

pytestmark = [pytest.mark.unit]

DEFINITIE = (
    "tijdelijk en kosteloos ter beschikking stellen van apparatuur aan een "
    "medewerker, die de apparatuur daarna teruggeeft"
)
BRON = "source:doc:werkinstructie"
BUUR = "gebruiker:verhuur"
BUURMATERIAAL = f"neighbour:{BUUR}"
BRON_TEKST = (
    "Lokale testwerkinstructie, alleen voor deze test. "
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. "
    "Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan een "
    "medewerker; de medewerker geeft de apparatuur daarna terug. "
    "Verdere informatie over verhuur staat niet in deze werkinstructie."
)
BUUR_TEKST = (
    "tijdelijk ter beschikking stellen van apparatuur aan een medewerker, die de "
    "apparatuur daarna teruggeeft"
)
# Eenheden in promptvolgorde: neighbour:… (U1) vóór source:… (U2–U5).
U_BUUR, U_INLEIDING, U_UITLEEN, U_VERHUUR, U_VERDER = "U1", "U2", "U3", "U4", "U5"


def _invoer(onvolledig=()):
    return br.Vergelijkingsinvoer(
        term="uitleen",
        materiaal={
            "definition": DEFINITIE,
            "context": "organisatorische_context: Servicedesk ICT-middelen",
            BRON: BRON_TEKST,
            BUURMATERIAAL: BUUR_TEKST,
        },
        buren=((BUUR, "verhuur"),),
        onvolledig=frozenset(onvolledig),
    )


def _a(kenmerk, onderwerp, toestand, eenheden=()):
    return {
        "kenmerk_id": kenmerk, "onderwerp": onderwerp, "toestand": toestand,
        "voorwaarden": [], "context": "zaakcontext", "citaten": list(eenheden),
    }  # fmt: skip


def _ruw_a():
    """A: alle doelfeiten uit één Uitleen-eenheid (hergebruik), kosten verhuur onbesproken."""
    return {
        "schema_version": br.INTERPRETATIESCHEMA,
        "kern": {
            "bovenbegrip": "ter beschikking stellen van apparatuur",
            "kenmerken": [
                {"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk", "citaat": "tijdelijk"},
                {"id": "K2", "kenmerk": "kosten", "waarde": "kosteloos", "citaat": "kosteloos"},
                {"id": "K3", "kenmerk": "ontvanger", "waarde": "een medewerker",
                 "citaat": "aan een medewerker"},
                {"id": "K4", "kenmerk": "teruggave", "waarde": "de ontvanger geeft terug",
                 "citaat": "die de apparatuur daarna teruggeeft"},
            ],
        },
        "buiten_kern": [], "buurgroepen": [], "buiten_bereik": [],
        "antwoorden": [
            *(_a(k, "doel", "bevestigd", [U_UITLEEN]) for k in ("K1", "K2", "K3", "K4")),
            _a("K1", BUUR, "bevestigd", [U_BUUR, U_VERHUUR]),
            _a("K2", BUUR, "onbesproken"),
            _a("K3", BUUR, "bevestigd", [U_VERHUUR]),
            _a("K4", BUUR, "bevestigd", [U_BUUR]),
        ],
    }  # fmt: skip


def _met(ruw, kenmerk, onderwerp, eenheden):
    ruw = copy.deepcopy(ruw)
    for a in ruw["antwoorden"]:
        if (a["kenmerk_id"], a["onderwerp"]) == (kenmerk, onderwerp):
            a["citaten"] = list(eenheden)
    return ruw


class TestZinnen:
    def test_zinsgrenzen_zonder_witruimte(self):
        tekst = "  Eerste zin; met puntkomma. Tweede zin!  Derde zonder punt  "
        assert [tekst[s:e] for s, e in br.zinnen(tekst)] == [
            "Eerste zin; met puntkomma.", "Tweede zin!", "Derde zonder punt",
        ]  # fmt: skip

    def test_lege_tekst_heeft_geen_zinnen(self):
        assert br.zinnen("   ") == ()


class TestEenheden:
    def test_nummering_volgt_promptvolgorde_en_slaat_definitie_en_context_over(self):
        invoer = _invoer()
        teksten = {
            u: invoer.materiaal[r.material_id][r.start : r.end]
            for u, r in invoer.eenheden().items()
        }
        assert teksten[U_BUUR] == BUUR_TEKST
        assert teksten[U_UITLEEN].startswith("Uitleen:")
        assert teksten[U_UITLEEN].endswith("daarna terug.")
        assert teksten[U_VERHUUR].startswith("Verhuur:")
        assert {r.material_id for r in invoer.eenheden().values()} == {
            BRON,
            BUURMATERIAAL,
        }

    def test_herhaalde_tekst_in_twee_zinnen_is_niet_dubbelzinnig(self):
        # R16-klasse: de teruggaafzin staat twee keer letterlijk; eenheden zijn uniek.
        assert br.bepaal(_ruw_a(), _invoer()).uitkomst == "review_required"


class TestHergebruik:
    def test_een_eenheid_draagt_vier_doelfeiten(self):
        uitkomst = br.bepaal(_ruw_a(), _invoer())
        assert (uitkomst.uitkomst, uitkomst.fout) == ("review_required", None)

    def test_hergebruik_blijft_in_de_controle_een_bewijsplaats(self):
        invoer = _invoer()
        interpretatie = br.valideer_interpretatie(_ruw_a(), invoer)
        doel = next(
            e for e in br.controle_eenheden(interpretatie, invoer) if e.naam == "doel"
        )
        fragmenten = [
            c for c in doel.pakket.inhoud["citaten"] if c["omvang"] == "fragment"
        ]
        assert [c["citaat"][:8] for c in fragmenten] == ["Uitleen:"]
        assert doel.pakket.inhoud["uitspraak"].count("(B1)") == 4


class TestVerplichtBewijs:
    def test_positief_antwoord_zonder_eenheid_is_schemafout(self):
        ruw = _met(_ruw_a(), "K3", "doel", [])
        assert br.bepaal(ruw, _invoer()).fout.soort == "schemafout"

    def test_onbekende_eenheid_is_citaatfout(self):
        ruw = _met(_ruw_a(), "K1", "doel", ["U99"])
        assert br.bepaal(ruw, _invoer()).fout.soort == "citaatfout"

    def test_letterlijk_citaatobject_is_geen_eenheid(self):
        ruw = _met(_ruw_a(), "K1", "doel", [{"material_id": BRON, "citaat": "Uitleen"}])
        assert br.bepaal(ruw, _invoer()).fout.soort == "citaatfout"


class TestOnderwerp:
    @pytest.mark.parametrize("eenheid", [U_VERHUUR, U_VERDER])
    def test_eenheid_die_alleen_verhuur_noemt_is_geen_uitleenbewijs(self, eenheid):
        fout = br.bepaal(_met(_ruw_a(), "K2", "doel", [eenheid]), _invoer()).fout
        assert fout.soort == "onderwerpfout" and "verhuur" in fout.melding

    def test_uitleeneenheid_is_geen_verhuurbewijs(self):
        fout = br.bepaal(_met(_ruw_a(), "K1", BUUR, [U_UITLEEN]), _invoer()).fout
        assert fout.soort == "onderwerpfout"

    def test_buurbeschrijving_is_geen_doelbewijs(self):
        fout = br.bepaal(_met(_ruw_a(), "K1", "doel", [U_BUUR]), _invoer()).fout
        assert fout.soort == "onderwerpfout"

    def test_eenheid_zonder_begripsnaam_gaat_door_naar_de_controle(self):
        # Grens (contract v6): of de inleiding kosteloosheid draagt, beslist de
        # semantische controle, niet de code.
        ruw = _met(_ruw_a(), "K2", "doel", [U_INLEIDING])
        assert br.bepaal(ruw, _invoer()).uitkomst == "review_required"

    def test_eenheid_met_beide_namen_gaat_door(self):
        bron = BRON_TEKST + " Uitleen en verhuur zijn beide tijdelijk."
        invoer = br.Vergelijkingsinvoer(
            "uitleen", {**_invoer().materiaal, BRON: bron}, ((BUUR, "verhuur"),)
        )
        ruw = _met(_ruw_a(), "K1", "doel", ["U6"])
        assert br.bepaal(ruw, invoer).uitkomst == "review_required"


class TestDekkingOngewijzigd:
    def test_onbesproken_over_onvolledige_bron_blijft_dekking_ontbreekt(self):
        fout = br.bepaal(_ruw_a(), _invoer(onvolledig=[BRON])).fout
        assert fout.soort == "dekking_ontbreekt"


class TestDiagnose:
    def test_verzamelt_alle_fouten_zonder_te_stoppen(self):
        ruw = _met(_met(_ruw_a(), "K2", "doel", [U_VERHUUR]), "K3", "doel", [])
        ruw = _met(ruw, "K4", "doel", ["U99"])
        soorten = [(d.pad, d.soort) for d in br.bewijsdiagnose(ruw, _invoer())]
        assert soorten == [
            ("antwoorden[2]", "onderwerpfout"),
            ("antwoorden[3]", "schemafout"),
            ("antwoorden[4]", "citaatfout"),
        ]

    def test_geldige_interpretatie_heeft_geen_diagnose(self):
        assert br.bewijsdiagnose(_ruw_a(), _invoer()) == ()

    # --- robuustheid tegen ongeldige modeluitvoer (Codex-review deel A, bevinding 1) ---

    @staticmethod
    def _soorten(ruw):
        return [(d.pad, d.soort) for d in br.bewijsdiagnose(ruw, _invoer())]

    @pytest.mark.parametrize("veld", ["antwoorden", "buurgroepen"])
    @pytest.mark.parametrize("waarde", [1, {}, "U1", None])
    def test_niet_lijst_container_is_zelf_een_diagnose(self, veld, waarde):
        # Review-voorbeelden: `antwoorden: 1` en `buurgroepen: 1` gaven TypeError.
        ruw = {**_ruw_a(), veld: waarde}
        assert (veld, "schemafout") in self._soorten(ruw)

    @pytest.mark.parametrize("veld", ["antwoorden", "buurgroepen"])
    def test_ontbrekende_container_is_zelf_een_diagnose(self, veld):
        ruw = {k: v for k, v in _ruw_a().items() if k != veld}
        assert (veld, "schemafout") in self._soorten(ruw)

    @pytest.mark.parametrize("waarde", [{}, "", None, 0, "U1", {"U1": 1}])
    def test_onbesproken_met_niet_lijst_citaten_is_schemafout(self, waarde):
        # Review-voorbeeld: onbesproken met `citaten: {}` gaf een lege diagnose.
        ruw = copy.deepcopy(_ruw_a())
        ruw["antwoorden"][5]["citaten"] = waarde  # K2/verhuur, onbesproken
        assert self._soorten(ruw) == [("antwoorden[6]", "schemafout")]

    @pytest.mark.parametrize("waarde", ["U3", {"U3": 1}, None, 3])
    def test_positief_met_niet_lijst_citaten_is_schemafout(self, waarde):
        ruw = copy.deepcopy(_ruw_a())
        ruw["antwoorden"][0]["citaten"] = waarde  # K1/doel, bevestigd
        assert self._soorten(ruw) == [("antwoorden[1]", "schemafout")]

    @pytest.mark.parametrize("onderwerp", [["doel"], {"doel": 1}, None, 7])
    def test_ongeldig_of_ontbrekend_onderwerp_is_schemafout(self, onderwerp):
        ruw = copy.deepcopy(_ruw_a())
        if onderwerp is None:
            del ruw["antwoorden"][0]["onderwerp"]
        else:
            ruw["antwoorden"][0]["onderwerp"] = onderwerp
        assert self._soorten(ruw) == [("antwoorden[1]", "schemafout")]

    def test_onbekende_toestand_is_schemafout(self):
        ruw = copy.deepcopy(_ruw_a())
        ruw["antwoorden"][0]["toestand"] = ["bevestigd"]
        assert self._soorten(ruw) == [("antwoorden[1]", "schemafout")]

    @pytest.mark.parametrize(
        "groep",
        [
            {"id": ["G1"], "buur": BUUR, "citaten": [U_VERHUUR]},
            {"buur": BUUR, "citaten": [U_VERHUUR]},
            {"id": "G1", "buur": [BUUR], "citaten": [U_VERHUUR]},
            {"id": "G1", "citaten": [U_VERHUUR]},
            {"id": "G1", "buur": "doel", "citaten": [U_VERHUUR]},
            {"id": "G1", "buur": BUUR, "citaten": "U4"},
            {"id": "G1", "buur": BUUR, "citaten": []},
            "geen object",
        ],
    )
    def test_ongeldige_buurgroep_is_schemafout_zonder_exception(self, groep):
        ruw = {**copy.deepcopy(_ruw_a()), "buurgroepen": [groep]}
        assert self._soorten(ruw) == [("buurgroepen[1]", "schemafout")]

    def test_antwoord_over_een_ongeldige_groep_geeft_geen_exception(self):
        ruw = copy.deepcopy(_ruw_a())
        ruw["buurgroepen"] = [{"id": ["G1"], "buur": BUUR, "citaten": [U_VERHUUR]}]
        ruw["antwoorden"].append(
            {**ruw["antwoorden"][4], "onderwerp": "G1", "citaten": [U_VERHUUR]}
        )
        assert self._soorten(ruw) == [
            ("antwoorden[9]", "schemafout"),
            ("buurgroepen[1]", "schemafout"),
        ]

    def test_geldige_buurgroep_geeft_geen_diagnose(self):
        ruw = copy.deepcopy(_ruw_a())
        ruw["buurgroepen"] = [{"id": "G1", "buur": BUUR, "citaten": [U_VERHUUR]}]
        ruw["antwoorden"].append(
            {**ruw["antwoorden"][4], "onderwerp": "G1", "citaten": [U_VERHUUR]}
        )
        assert self._soorten(ruw) == []
