"""DEF-768 — beperkte ESS-05-bewijsregels (`ess05-bewijsregels/4`), puur domein.

Contract: docs/technisch/ess05-bewijsregels-contract-v4.md (v2 verwerkt de
contractreview logs/def768/bewijsregels-contractreview-result-v1.md, K1–K4; v3
de K4-rest uit bewijsregels-contractreview-result-v2.md; v4 het R16-herstel uit
bewijsregels-r16-uitvoerreview-result-v1.md: onderwerpbinding en controlescope).
De interpretaties hier zijn vooraf vastgelegde, gecontroleerde feiten: bewijs
voor de geldigheidscontroles en afleidingsregels, niet voor modelinterpretatie
(die toetst de mechanismeproef afzonderlijk).

Drie varianten van hetzelfde begripspaar (uitleen/verhuur):
A — doel tijdelijk + kosteloos, buur tijdelijk, kosten in het volledige
    relevante materiaal onbesproken → kosten onbekend, geldig open oordeel;
B — dezelfde situatie zonder de noodzakelijke dekking → error;
C — buur permanent (niet tijdelijk), kosten onbekend → afgrenzing op duur.
"""

from __future__ import annotations

import copy

import pytest

from domain.ess05 import bewijsregels as br
from domain.ess05.lokale_controle import OMVANG_FRAGMENT, OMVANG_VOLLEDIG

pytestmark = [pytest.mark.unit]

DEFINITIE = (
    "tijdelijk en kosteloos ter beschikking stellen van apparatuur aan een "
    "medewerker, die de apparatuur daarna teruggeeft"
)
BRON = "source:doc:werkinstructie"
BUUR = "gebruiker:verhuur"
BUURMATERIAAL = f"neighbour:{BUUR}"
BRON_A = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Verhuur: de "
    "servicedesk stelt apparatuur tijdelijk ter beschikking aan een medewerker; de "
    "medewerker geeft de apparatuur daarna terug. Verdere informatie over verhuur "
    "staat niet in deze werkinstructie."
)
BUUR_A = (
    "tijdelijk ter beschikking stellen van apparatuur aan een medewerker, die de "
    "apparatuur daarna teruggeeft"
)
BRON_C = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Verhuur: de "
    "servicedesk stelt apparatuur permanent ter beschikking aan een medewerker. "
    "Verdere informatie over verhuur staat niet in deze werkinstructie."
)
BUUR_C = "permanent ter beschikking stellen van apparatuur aan een medewerker"
#: v4: broncitaten in een bron met meer dan één begrip noemen hun onderwerp.
DOELCITAAT = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker"
)
TERUGGAVE_DOEL = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug."
)


def _invoer(bron=BRON_A, buur=BUUR_A, *, onvolledig=(), definitie=DEFINITIE, extra=None,
            buren=((BUUR, "verhuur"),)):  # fmt: skip
    materiaal = {
        "definition": definitie,
        "context": "organisatorische_context: Servicedesk ICT-middelen",
        BRON: bron,
        BUURMATERIAAL: buur,
        **(extra or {}),
    }
    return br.Vergelijkingsinvoer(
        term="uitleen",
        materiaal=materiaal,
        buren=tuple(buren),
        onvolledig=frozenset(onvolledig),
    )


def _kern():
    return {
        "bovenbegrip": "ter beschikking stellen van apparatuur",
        "kenmerken": [
            {"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk", "citaat": "tijdelijk"},
            {"id": "K2", "kenmerk": "kosten", "waarde": "kosteloos", "citaat": "kosteloos"},
            {"id": "K3", "kenmerk": "ontvanger", "waarde": "een medewerker",
             "citaat": "aan een medewerker"},
            {"id": "K4", "kenmerk": "teruggave", "waarde": "de ontvanger geeft terug",
             "citaat": "die de apparatuur daarna teruggeeft"},
        ],
    }  # fmt: skip


def _a(kenmerk, onderwerp, toestand, citaten=(), *, voorwaarden=(), context="algemeen"):
    return {
        "kenmerk_id": kenmerk,
        "onderwerp": onderwerp,
        "toestand": toestand,
        "voorwaarden": list(voorwaarden),
        "context": context,
        "citaten": [{"material_id": m, "citaat": c} for m, c in citaten],
    }


def _groep(gid, buur, omschrijving, citaten):
    return {
        "id": gid,
        "buur": buur,
        "omschrijving": omschrijving,
        "citaten": [{"material_id": m, "citaat": c} for m, c in citaten],
    }


def _ruw(kern, antwoorden, *, buiten_kern=(), groepen=(), buiten_bereik=()):
    return {
        "schema_version": br.INTERPRETATIESCHEMA,
        "kern": kern,
        "buiten_kern": list(buiten_kern),
        "buurgroepen": list(groepen),
        "buiten_bereik": list(buiten_bereik),
        "antwoorden": list(antwoorden),
    }


def _doelantwoorden():
    return [
        _a("K1", "doel", "bevestigd", [(BRON, DOELCITAAT)]),
        _a("K2", "doel", "bevestigd", [(BRON, DOELCITAAT)]),
        _a("K3", "doel", "bevestigd", [(BRON, DOELCITAAT)]),
        _a("K4", "doel", "bevestigd", [(BRON, TERUGGAVE_DOEL)]),
    ]


def _interpretatie_a():
    return _ruw(_kern(), [
        *_doelantwoorden(),
        _a("K1", BUUR, "bevestigd", [(BUURMATERIAAL, "tijdelijk ter beschikking")]),
        _a("K2", BUUR, "onbesproken"),
        _a("K3", BUUR, "bevestigd", [(BUURMATERIAAL, "aan een medewerker")]),
        _a("K4", BUUR, "bevestigd", [(BUURMATERIAAL, "die de apparatuur daarna teruggeeft")]),
    ])  # fmt: skip


def _interpretatie_c():
    return _ruw(_kern(), [
        *_doelantwoorden(),
        _a("K1", BUUR, "ontkend", [(BUURMATERIAAL, "permanent ter beschikking")]),
        _a("K2", BUUR, "onbesproken"),
        _a("K3", BUUR, "bevestigd", [(BUURMATERIAAL, "aan een medewerker")]),
        _a("K4", BUUR, "onbesproken"),
    ])  # fmt: skip


def _zonder(antwoorden, kenmerk, onderwerp):
    return [
        a
        for a in antwoorden
        if (a["kenmerk_id"], a["onderwerp"]) != (kenmerk, onderwerp)
    ]


def _vervang(ruw, kenmerk, onderwerp, *nieuw):
    ruw = copy.deepcopy(ruw)
    ruw["antwoorden"] = [*_zonder(ruw["antwoorden"], kenmerk, onderwerp), *nieuw]
    return ruw


def _fout(ruw, invoer) -> br.BewijsregelfoutError:
    with pytest.raises(br.BewijsregelfoutError) as fout:
        br.valideer_interpretatie(ruw, invoer)
    uitkomst = br.bepaal(ruw, invoer)
    assert uitkomst.uitkomst == "error"
    assert uitkomst.fout.soort == fout.value.soort
    return fout.value


def _aspect(uitkomst, kenmerk, buur=0):
    return next(a for a in uitkomst.buren[buur].aspecten if a.kenmerk == kenmerk)


# --- de drie varianten -------------------------------------------------------------------


class TestDrieVarianten:
    def test_a_kosten_onbekend_geeft_geldig_open_oordeel(self):
        uitkomst = br.bepaal(_interpretatie_a(), _invoer())
        assert (uitkomst.uitkomst, uitkomst.fout) == ("review_required", None)
        (buur,) = uitkomst.buren
        assert buur.oordeel == "open"
        assert (
            _aspect(uitkomst, "kosten").aspect,
            _aspect(uitkomst, "kosten").reden,
        ) == (
            "onbeslist",
            "onbekend",
        )
        assert _aspect(uitkomst, "duur").aspect == "gedeeld"

    def test_b_onvolledig_relevant_materiaal_is_error_geen_informatiegebrek(self):
        fout = _fout(_interpretatie_a(), _invoer(onvolledig={BRON}))
        assert fout.soort == "dekking_ontbreekt"
        assert "K2" in str(fout)

    def test_b_ontbrekend_verplicht_bewijsdoel_is_error(self):
        ruw = copy.deepcopy(_interpretatie_a())
        ruw["antwoorden"] = _zonder(ruw["antwoorden"], "K2", BUUR)
        fout = _fout(ruw, _invoer())
        assert fout.soort == "doeldekking_onvolledig"
        assert "K2" in str(fout) and BUUR in str(fout)

    def test_c_afgrenzing_op_duur_kosten_blijven_onbekend(self):
        uitkomst = br.bepaal(_interpretatie_c(), _invoer(BRON_C, BUUR_C))
        assert uitkomst.uitkomst == "pass"
        assert uitkomst.buren[0].oordeel == "onderscheiden"
        duur, kosten = _aspect(uitkomst, "duur"), _aspect(uitkomst, "kosten")
        assert (duur.aspect, kosten.aspect, kosten.reden) == (
            "afgrenzend",
            "onbeslist",
            "onbekend",
        )
        tekst = br.render(uitkomst)
        assert "duur" in tekst and "kosten" in tekst
        assert "stelt het aangeleverde materiaal niet vast" in tekst


# --- K1: geldigheid vóór elke inhoudelijke aggregatie ------------------------------------


class TestK1GeldigheidVoorInhoud:
    def test_bewezen_afgrenzing_plus_ontbrekende_dekking_is_error(self):
        # C: duur grenst af, maar kosten/teruggave staan 'onbesproken' over een
        # onvolledig gebonden bron. Dat verplichte bewijs ontbreekt: error.
        fout = _fout(_interpretatie_c(), _invoer(BRON_C, BUUR_C, onvolledig={BRON}))
        assert fout.soort == "dekking_ontbreekt"

    def test_bewezen_fail_bij_buur_x_plus_ontbrekend_bewijs_bij_buur_y_is_error(self):
        uitleen = "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos"
        verhuur = "Verhuur: tijdelijk en tegen betaling"
        definitie = "tijdelijk ter beschikking stellen van apparatuur"
        bron = ("Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter "
                "beschikking. Verhuur: tijdelijk en tegen betaling ter beschikking.")  # fmt: skip
        ander = "gebruiker:reservering"
        invoer = br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={
                "definition": definitie,
                BRON: bron,
                BUURMATERIAAL: "tijdelijk ter beschikking stellen",
                f"neighbour:{ander}": "vastleggen van apparatuur",
            },
            buren=((BUUR, "verhuur"), (ander, "reservering")),
            onvolledig=frozenset({f"neighbour:{ander}"}),
        )
        ruw = _ruw(
            {"bovenbegrip": "ter beschikking stellen van apparatuur",
             "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                            "citaat": "tijdelijk"}]},
            [
                _a("K1", "doel", "bevestigd", [(BRON, uitleen)]),
                _a("M1", "doel", "bevestigd", [(BRON, uitleen)]),
                _a("K1", BUUR, "bevestigd", [(BRON, verhuur)]),
                _a("M1", BUUR, "ontkend", [(BRON, verhuur)]),
                _a("K1", ander, "onbesproken"),
                _a("M1", ander, "onbesproken"),
            ],
            buiten_kern=[{"id": "M1", "kenmerk": "kosten", "waarde": "kosteloos"}],
        )  # fmt: skip
        # Zonder het onvolledige materiaal zou verhuur een bewezen fail zijn.
        volledig = br.Vergelijkingsinvoer(
            term=invoer.term, materiaal=invoer.materiaal, buren=invoer.buren
        )
        assert br.bepaal(ruw, volledig).uitkomst == "fail"
        assert _fout(ruw, invoer).soort == "dekking_ontbreekt"

    def test_buiten_bereik_gaat_voor_een_bewezen_afgrenzing(self):
        ruw = copy.deepcopy(_interpretatie_c())
        ruw["buiten_bereik"] = [
            {"citaat": "aan een medewerker", "reden": "relatie met gedeeld argument"}
        ]
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "buiten_bereik"


# --- K2: geen fail zonder bewezen niet-afgrenzing -----------------------------------------


class TestK2GeenFailZonderBewijs:
    DEF = "tijdelijk ter beschikking stellen van apparatuur"
    UITLEEN = "Uitleen: apparatuur tijdelijk en kosteloos"

    def _invoer(self, bron, buurtekst="ter beschikking stellen van apparatuur"):
        return br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": self.DEF, BRON: bron, BUURMATERIAAL: buurtekst},
            buren=((BUUR, "verhuur"),),
        )

    def _ruw(self, *buurantwoorden, groepen=()):
        return _ruw(
            {"bovenbegrip": "ter beschikking stellen van apparatuur",
             "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                            "citaat": "tijdelijk"}]},
            [
                _a("K1", "doel", "bevestigd", [(BRON, self.UITLEEN)]),
                _a("M1", "doel", "bevestigd", [(BRON, self.UITLEEN)]),
                *buurantwoorden,
            ],
            buiten_kern=[{"id": "M1", "kenmerk": "kosten", "waarde": "kosteloos"}],
            groepen=groepen,
        )  # fmt: skip

    def test_betaalde_buur_met_onbekende_duur_is_open_geen_fail(self):
        bron = ("Uitleen: apparatuur tijdelijk en kosteloos ter beschikking. Verhuur: "
                "apparatuur tegen betaling ter beschikking.")  # fmt: skip
        uitkomst = br.bepaal(
            self._ruw(
                _a("K1", BUUR, "onbesproken"),
                _a(
                    "M1",
                    BUUR,
                    "ontkend",
                    [(BRON, "Verhuur: apparatuur tegen betaling")],
                ),
            ),
            self._invoer(bron),
        )
        assert uitkomst.uitkomst == "review_required"
        assert uitkomst.buren[0].oordeel == "open"
        assert "duur" in br.render(uitkomst)

    def test_conflicterende_duur_is_evenmin_bewezen_niet_afgrenzend(self):
        bron = ("Uitleen: apparatuur tijdelijk en kosteloos ter beschikking. Verhuur: "
                "apparatuur tegen betaling ter beschikking. Verhuur is tijdelijk. "
                "Verhuur is permanent.")  # fmt: skip
        uitkomst = br.bepaal(
            self._ruw(
                _a("K1", BUUR, "bevestigd", [(BRON, "Verhuur is tijdelijk.")]),
                _a("K1", BUUR, "ontkend", [(BRON, "Verhuur is permanent.")]),
                _a(
                    "M1",
                    BUUR,
                    "ontkend",
                    [(BRON, "Verhuur: apparatuur tegen betaling")],
                ),
            ),
            self._invoer(bron),
        )
        assert uitkomst.uitkomst == "review_required"
        assert (_aspect(uitkomst, "duur").reden) == "conflict"

    def test_tijdelijke_betaalde_buur_is_een_bewezen_tegengeval(self):
        bron = ("Uitleen: apparatuur tijdelijk en kosteloos ter beschikking. Verhuur: "
                "apparatuur tijdelijk en tegen betaling ter beschikking.")  # fmt: skip
        verhuur = "Verhuur: apparatuur tijdelijk en tegen betaling"
        uitkomst = br.bepaal(
            self._ruw(
                _a("K1", BUUR, "bevestigd", [(BRON, verhuur)]),
                _a("M1", BUUR, "ontkend", [(BRON, verhuur)]),
            ),
            self._invoer(bron),
        )
        assert uitkomst.uitkomst == "fail"
        assert uitkomst.buren[0].oordeel == "niet_onderscheiden"
        assert "mist" in br.render(uitkomst)


# --- K3: woorddekking is alleen een tekstcontrole -----------------------------------------


class TestK3Tekstdekking:
    DEF = "persoon die uitsluitend eigen aanvragen goedkeurt"

    def _invoer(self):
        return br.Vergelijkingsinvoer(
            term="goedkeurder",
            materiaal={
                "definition": self.DEF,
                BRON: "Een goedkeurder keurt uitsluitend eigen aanvragen goed.",
                BUURMATERIAAL: "persoon die aanvragen van anderen goedkeurt",
            },
            buren=((BUUR, "beoordelaar"),),
        )

    def _verlies(self):
        # Eén citaat dekt de hele rest, maar de waarde laat 'uitsluitend eigen' weg.
        return _ruw(
            {"bovenbegrip": "persoon",
             "kenmerken": [{"id": "K1", "kenmerk": "handeling",
                            "waarde": "keurt aanvragen goed",
                            "citaat": "die uitsluitend eigen aanvragen goedkeurt"}]},
            [
                _a("K1", "doel", "bevestigd", [(BRON, "keurt uitsluitend eigen aanvragen goed")]),
                _a("K1", BUUR, "bevestigd", [(BUURMATERIAAL, "aanvragen van anderen goedkeurt")]),
            ],
        )  # fmt: skip

    def test_woorddekking_slaagt_ook_bij_een_verloren_beperking(self):
        # Bewijst dat tekstdekking geen semantische volledigheid certificeert.
        interpretatie = br.valideer_interpretatie(self._verlies(), self._invoer())
        assert [k.waarde for k in interpretatie.kern] == ["keurt aanvragen goed"]

    def test_kerncontrole_toetst_het_fragment_niet_de_volledigheid(self):
        interpretatie = br.valideer_interpretatie(self._verlies(), self._invoer())
        eenheden = {
            e.naam: e for e in br.controle_eenheden(interpretatie, self._invoer())
        }
        uitspraak = eenheden["kern"].pakket.inhoud["uitspraak"]
        assert "'die uitsluitend eigen aanvragen goedkeurt'" in uitspraak
        assert "precies" in uitspraak and "beperking" in uitspraak
        # Geen vrije volledigheids- of afgrenzingsclaim onder het sjabloon.
        for vrij in (
            "geen ander kenmerk",
            "geen andere kenmerken",
            "onderscheid",
            "grenst",
        ):
            assert vrij not in uitspraak
        (citaat,) = eenheden["kern"].pakket.inhoud["citaten"]
        assert citaat["omvang"] == OMVANG_VOLLEDIG

    def test_gedeclareerde_constructie_buiten_bereik_is_expliciet_error(self):
        ruw = copy.deepcopy(self._verlies())
        ruw["buiten_bereik"] = [
            {"citaat": "uitsluitend eigen aanvragen",
             "reden": "relatie tussen persoon en eigen aanvraag"}
        ]  # fmt: skip
        fout = _fout(ruw, self._invoer())
        assert fout.soort == "buiten_bereik"

    def test_buiten_bereik_citaat_moet_letterlijk_bestaan(self):
        ruw = copy.deepcopy(self._verlies())
        ruw["buiten_bereik"] = [{"citaat": "verzonnen tekst", "reden": "x"}]
        assert _fout(ruw, self._invoer()).soort == "citaatfout"


# --- K4: beschreven deelgroepen blijven zichtbaar -------------------------------------------


class TestK4Buurgroepen:
    DEF = "tijdelijk ter beschikking stellen van apparatuur"
    BRON_K4 = (
        "Uitleen: apparatuur tijdelijk en kosteloos ter beschikking. Verhuur gebeurt "
        "altijd tegen betaling. Verhuur is soms permanent. Verhuur is soms tijdelijk."
    )
    GEMENGD = "Verhuur is soms permanent. Verhuur is soms tijdelijk."

    def _invoer(self, bron=BRON_K4):
        return br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": self.DEF, BRON: bron,
                       BUURMATERIAAL: "ter beschikking stellen tegen betaling"},
            buren=((BUUR, "verhuur"),),
        )  # fmt: skip

    def _ruw(self, buur_duur, groepen, groepantwoorden):
        return _ruw(
            {"bovenbegrip": "ter beschikking stellen van apparatuur",
             "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                            "citaat": "tijdelijk"}]},
            [
                _a("K1", "doel", "bevestigd", [(BRON, "Uitleen: apparatuur tijdelijk en kosteloos")]),
                _a("M1", "doel", "bevestigd", [(BRON, "Uitleen: apparatuur tijdelijk en kosteloos")]),
                buur_duur,
                _a("M1", BUUR, "ontkend", [(BRON, "Verhuur gebeurt altijd tegen betaling")]),
                *groepantwoorden,
            ],
            buiten_kern=[{"id": "M1", "kenmerk": "kosten", "waarde": "kosteloos"}],
            groepen=groepen,
        )  # fmt: skip

    def _gemengd(self):
        return _a("K1", BUUR, "gemengd", [(BRON, self.GEMENGD)])

    def _groepen(self):
        return [
            _groep(
                "G1", BUUR, "permanente verhuur", [(BRON, "Verhuur is soms permanent")]
            ),
            _groep(
                "G2", BUUR, "tijdelijke verhuur", [(BRON, "Verhuur is soms tijdelijk")]
            ),
        ]

    def test_tijdelijk_betaald_blijft_tegengeval_ondanks_uitgesloten_permanent(self):
        ruw = self._ruw(self._gemengd(), self._groepen(), [
            _a("K1", "G1", "ontkend", [(BRON, "Verhuur is soms permanent")]),
            _a("M1", "G1", "ontkend", [(BRON, "Verhuur gebeurt altijd tegen betaling")]),
            _a("K1", "G2", "bevestigd", [(BRON, "Verhuur is soms tijdelijk")]),
            _a("M1", "G2", "ontkend", [(BRON, "Verhuur gebeurt altijd tegen betaling")]),
        ])  # fmt: skip
        uitkomst = br.bepaal(ruw, self._invoer())
        assert uitkomst.uitkomst == "fail"
        (buur,) = uitkomst.buren
        assert buur.oordeel == "niet_onderscheiden"
        assert {g.id: g.oordeel for g in buur.groepen} == {
            BUUR: "onbeslist",
            "G1": "afgegrensd",
            "G2": "tegengeval",
        }
        tekst = br.render(uitkomst)
        assert "tijdelijke verhuur" in tekst and "mist" in tekst

    def test_gemengd_zonder_beide_kanten_is_inconsistent(self):
        ruw = self._ruw(self._gemengd(), self._groepen()[:1], [
            _a("K1", "G1", "ontkend", [(BRON, "Verhuur is soms permanent")]),
            _a("M1", "G1", "ontkend", [(BRON, "Verhuur gebeurt altijd tegen betaling")]),
        ])  # fmt: skip
        assert _fout(ruw, self._invoer()).soort == "inconsistent"

    def test_deelgroep_die_uniforme_buurtoestand_tegenspreekt_is_inconsistent(self):
        ruw = self._ruw(self._gemengd(), self._groepen(), [
            _a("K1", "G1", "ontkend", [(BRON, "Verhuur is soms permanent")]),
            _a("M1", "G1", "bevestigd", [(BRON, "Verhuur is soms permanent")]),
            _a("K1", "G2", "bevestigd", [(BRON, "Verhuur is soms tijdelijk")]),
            _a("M1", "G2", "ontkend", [(BRON, "Verhuur gebeurt altijd tegen betaling")]),
        ])  # fmt: skip
        assert _fout(ruw, self._invoer()).soort == "inconsistent"

    def test_voorwaarde_aan_buurzijde_hoort_in_een_deelgroep(self):
        ruw = self._ruw(
            _a("K1", BUUR, "ontkend", [(BRON, "Verhuur is soms permanent")], voorwaarden=["bij storing"]),
            [], [],
        )  # fmt: skip
        assert _fout(ruw, self._invoer()).soort == "schemafout"

    def test_voorwaarde_blijft_als_deelgroep_zichtbaar(self):
        bron = self.BRON_K4 + " Bij storing is verhuur tijdelijk."
        groepen = [
            _groep(
                "G1", BUUR, "verhuur bij storing", [(BRON, "Bij storing is verhuur")]
            ),
        ]
        ruw = self._ruw(
            _a("K1", BUUR, "deels", [(BRON, "Bij storing is verhuur tijdelijk.")]),
            groepen,
            [
                _a(
                    "K1",
                    "G1",
                    "bevestigd",
                    [(BRON, "Bij storing is verhuur tijdelijk.")],
                ),
                _a(
                    "M1",
                    "G1",
                    "ontkend",
                    [(BRON, "Verhuur gebeurt altijd tegen betaling")],
                ),
            ],
        )
        uitkomst = br.bepaal(ruw, self._invoer(bron))
        # Het storingsgeval ligt binnen de hele kern en buiten de doelbetekenis.
        assert uitkomst.uitkomst == "fail"
        assert "verhuur bij storing" in br.render(uitkomst)
        interpretatie = br.valideer_interpretatie(ruw, self._invoer(bron))
        eenheden = {
            e.naam: e for e in br.controle_eenheden(interpretatie, self._invoer(bron))
        }
        assert (
            "verhuur bij storing" in eenheden[f"buur:{BUUR}"].pakket.inhoud["uitspraak"]
        )

    def test_twee_gemengde_kenmerken_expliciet_buiten_bereik(self):
        definitie = "tijdelijk en kosteloos ter beschikking stellen van apparatuur"
        bron = ("Uitleen: tijdelijk en kosteloos ter beschikking. Verhuur is soms "
                "permanent en soms tijdelijk. Verhuur is soms betaald en soms kosteloos.")  # fmt: skip
        invoer = br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": definitie, BRON: bron, BUURMATERIAAL: "verhuren"},
            buren=((BUUR, "verhuur"),),
        )
        kern = {
            "bovenbegrip": "ter beschikking stellen van apparatuur",
            "kenmerken": [
                {"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk", "citaat": "tijdelijk"},
                {"id": "K2", "kenmerk": "kosten", "waarde": "kosteloos", "citaat": "kosteloos"},
            ],
        }  # fmt: skip
        groepen = [
            _groep(
                "G1",
                BUUR,
                "permanente verhuur",
                [(BRON, "Verhuur is soms permanent")],
            ),
            _groep("G2", BUUR, "betaalde verhuur", [(BRON, "Verhuur is soms betaald")]),
        ]
        ruw = _ruw(kern, [
            _a("K1", "doel", "bevestigd", [(BRON, "Uitleen: tijdelijk en kosteloos")]),
            _a("K2", "doel", "bevestigd", [(BRON, "Uitleen: tijdelijk en kosteloos")]),
            _a("K1", BUUR, "gemengd", [(BRON, "Verhuur is soms permanent en soms tijdelijk")]),
            _a("K2", BUUR, "gemengd", [(BRON, "Verhuur is soms betaald en soms kosteloos")]),
            _a("K1", "G1", "ontkend", [(BRON, "Verhuur is soms permanent")]),
            _a("K2", "G1", "onbesproken"),
            _a("K1", "G2", "onbesproken"),
            _a("K2", "G2", "ontkend", [(BRON, "Verhuur is soms betaald")]),
        ], groepen=groepen)  # fmt: skip
        assert _fout(ruw, invoer).soort == "buiten_bereik"

    def test_deelgroep_zonder_eigen_citaat_geweigerd(self):
        ruw = self._ruw(
            self._gemengd(), [_groep("G1", BUUR, "permanente verhuur", [])], []
        )
        assert _fout(ruw, self._invoer()).soort == "schemafout"

    def test_deelgroep_van_onbekende_buur_geweigerd(self):
        groepen = [
            _groep(
                "G1",
                "gebruiker:onbekend",
                "iets",
                [(BRON, "Verhuur is soms permanent")],
            )
        ]
        ruw = self._ruw(self._gemengd(), groepen, [])
        assert _fout(ruw, self._invoer()).soort == "schemafout"


class TestK4VoorwaardelijkeDoeleis:
    """Tegenvoorbeeld uit logs/def768/bewijsregels-contractreview-result-v2.md (K4-rest).

    Doel: tijdelijke uitgifte; bij storing is toestemming vereist. Kern: tijdelijk.
    Buur: storingsuitgifte zonder toestemming, soms tijdelijk en soms permanent.
    De tijdelijke storingsuitgifte ligt binnen de kern en buiten het doelbegrip;
    onder v2 viel de voorwaardelijke eis buiten d_F en werd die groep `gedeeld`
    (split → pass). Dit mag nooit pass worden.
    """

    DEF = "tijdelijk ter beschikking stellen van apparatuur"
    STORING = "gebruiker:storingsuitgifte"
    BRON_S = (
        "Uitleen: de servicedesk stelt apparatuur tijdelijk ter beschikking. Bij storing "
        "is voor uitleen toestemming van de teamleider vereist. Storingsuitgifte gebeurt "
        "zonder toestemming. Storingsuitgifte is soms permanent. Storingsuitgifte is "
        "soms tijdelijk."
    )
    EIS = "Bij storing is voor uitleen toestemming van de teamleider vereist"

    def _invoer(self):
        return br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": self.DEF, BRON: self.BRON_S,
                       f"neighbour:{self.STORING}": "apparatuur uitgeven bij een storing"},
            buren=((self.STORING, "storingsuitgifte"),),
        )  # fmt: skip

    def _ruw(self):
        s = self.STORING
        zonder = (BRON, "Storingsuitgifte gebeurt zonder toestemming")
        return _ruw(
            {"bovenbegrip": "ter beschikking stellen van apparatuur",
             "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                            "citaat": "tijdelijk"}]},
            [
                _a("K1", "doel", "bevestigd",
                   [(BRON, "Uitleen: de servicedesk stelt apparatuur tijdelijk ter")]),
                _a("M1", "doel", "bevestigd", [(BRON, self.EIS)], voorwaarden=["bij storing"]),
                _a("K1", s, "gemengd", [(BRON, "Storingsuitgifte is soms permanent. Storingsuitgifte is soms tijdelijk.")]),
                _a("M1", s, "ontkend", [zonder]),
                _a("K1", "G1", "ontkend", [(BRON, "Storingsuitgifte is soms permanent")]),
                _a("M1", "G1", "ontkend", [zonder]),
                _a("K1", "G2", "bevestigd", [(BRON, "Storingsuitgifte is soms tijdelijk")]),
                _a("M1", "G2", "ontkend", [zonder]),
            ],
            buiten_kern=[{"id": "M1", "kenmerk": "toestemming", "waarde": "vereist"}],
            groepen=[
                _groep("G1", s, "permanente storingsuitgifte", [(BRON, "Storingsuitgifte is soms permanent")]),
                _groep("G2", s, "tijdelijke storingsuitgifte", [(BRON, "Storingsuitgifte is soms tijdelijk")]),
            ],
        )  # fmt: skip

    def test_tegenvoorbeeld_wordt_nooit_pass(self):
        uitkomst = br.bepaal(self._ruw(), self._invoer())
        assert uitkomst.uitkomst != "pass"
        assert uitkomst.uitkomst == "error"
        assert uitkomst.fout.soort == "buiten_bereik"

    def test_voorwaardelijke_eis_blijft_met_tekst_en_citaat_zichtbaar(self):
        fout = _fout(self._ruw(), self._invoer())
        assert "M1 (toestemming: vereist)" in fout.melding
        assert "bij storing" in fout.melding and self.EIS in fout.melding
        tekst = br.render(br.bepaal(self._ruw(), self._invoer()))
        assert "bij storing" in tekst and self.EIS in tekst
        assert "Dit zegt niets over de definitie" in tekst

    def test_zelfde_geval_zonder_voorwaarde_is_fail(self):
        # Controle dat het tegenvoorbeeld zelf discrimineert: zonder de voorwaarde
        # is toestemming een doeleis en is de tijdelijke storingsuitgifte een tegengeval.
        ruw = _vervang(
            self._ruw(), "M1", "doel", _a("M1", "doel", "bevestigd", [(BRON, self.EIS)])
        )
        uitkomst = br.bepaal(ruw, self._invoer())
        assert uitkomst.uitkomst == "fail"
        groepen = {g.id: g.oordeel for g in uitkomst.buren[0].groepen}
        assert groepen["G2"] == "tegengeval"


class TestRoloverlap:
    DEF = "persoon met een actuele lening bij de instelling"
    WERKNEMER = "gebruiker:werknemer"

    def _invoer(self, bron):
        return br.Vergelijkingsinvoer(
            term="lener",
            materiaal={
                "definition": self.DEF,
                BRON: bron,
                f"neighbour:{self.WERKNEMER}": "persoon met een arbeidsovereenkomst",
            },
            buren=((self.WERKNEMER, "werknemer"),),
        )

    def _ruw(self, buurantwoord, groepen=(), groepantwoorden=()):
        return _ruw(
            {"bovenbegrip": "persoon",
             "kenmerken": [{"id": "K1", "kenmerk": "relatie",
                            "waarde": "heeft een actuele lening bij de instelling",
                            "citaat": "met een actuele lening bij de instelling"}]},
            [
                _a("K1", "doel", "bevestigd",
                   [(BRON, "Een lener heeft een actuele lening bij de instelling.")]),
                buurantwoord,
                *groepantwoorden,
            ],
            groepen=groepen,
        )  # fmt: skip

    #: Oorspronkelijke fixture (R16-H-01): een geldige overlappassage noemt beide begrippen.
    BRON_SPLITS = (
        "Een lener heeft een actuele lening bij de instelling. Niet elke werknemer heeft "
        "een lening; een werknemer kan ook lener zijn."
    )
    OVERLAP = "een werknemer kan ook lener zijn"

    def test_overlap_mag_via_splitsing_op_een_kenmerk(self):
        groepen = [
            _groep("G1", self.WERKNEMER, "werknemer zonder lening",
                   [(BRON, "Niet elke werknemer heeft een lening")]),
            _groep("G2", self.WERKNEMER, "werknemer die ook lener is",
                   [(BRON, self.OVERLAP)]),
        ]  # fmt: skip
        ruw = self._ruw(
            _a("K1", self.WERKNEMER, "gemengd", [(BRON, "Niet elke werknemer heeft een lening")]),
            groepen,
            [
                _a("K1", "G1", "ontkend", [(BRON, "Niet elke werknemer heeft een lening")]),
                _a("K1", "G2", "bevestigd", [(BRON, self.OVERLAP)]),
            ],
        )  # fmt: skip
        uitkomst = br.bepaal(ruw, self._invoer(self.BRON_SPLITS))
        assert uitkomst.uitkomst == "pass"
        assert {g.id: g.oordeel for g in uitkomst.buren[0].groepen} == {
            self.WERKNEMER: "onbeslist",
            "G1": "afgegrensd",
            "G2": "gedeeld",
        }
        assert "gedeelde gevallen" in br.render(uitkomst)

    def test_alleen_een_bevestigd_deel_is_geen_afgrenzing_en_geen_fail(self):
        bron = "Een lener heeft een actuele lening bij de instelling. Sommige werknemers hebben een lening."
        groepen = [_groep("G1", self.WERKNEMER, "werknemer met lening",
                          [(BRON, "Sommige werknemers hebben een lening.")])]  # fmt: skip
        ruw = self._ruw(
            _a("K1", self.WERKNEMER, "deels", [(BRON, "Sommige werknemers hebben een lening.")]),
            groepen,
            [_a("K1", "G1", "bevestigd", [(BRON, "Sommige werknemers hebben een lening.")])],
        )  # fmt: skip
        uitkomst = br.bepaal(ruw, self._invoer(bron))
        assert uitkomst.uitkomst == "review_required"


# --- N2-tegenmodel: alleen als synthetische afleidingstest -------------------------------


class TestN2Tegenmodel:
    DEF = "tijdelijk ter beschikking stellen van apparatuur"

    def _invoer(self):
        return br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={
                "definition": self.DEF,
                "meaning": "Uitleen is tijdelijk ter beschikking stellen van apparatuur.",
                BUURMATERIAAL: "permanent ter beschikking stellen van apparatuur",
            },
            buren=((BUUR, "verhuur"),),
        )

    def _ruw(self, *buurantwoorden):
        return _ruw(
            {"bovenbegrip": "ter beschikking stellen van apparatuur",
             "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                            "citaat": "tijdelijk"}]},
            [_a("K1", "doel", "bevestigd", [("meaning", "Uitleen is tijdelijk")]),
             *buurantwoorden],
        )  # fmt: skip

    def test_alleen_de_n2_premissen_dekken_het_duurdoel_niet(self):
        assert _fout(self._ruw(), self._invoer()).soort == "doeldekking_onvolledig"

    def test_tegenmodel_geeft_afgrenzing_op_duur(self):
        ruw = self._ruw(
            _a("K1", BUUR, "ontkend", [(BUURMATERIAAL, "permanent ter beschikking")])
        )
        assert br.bepaal(ruw, self._invoer()).uitkomst == "pass"

    @pytest.mark.parametrize(
        "veld", ["conclusie", "geldig", "geldige_afgrenzing", "uitkomst"]
    )
    def test_vrij_conclusieveld_of_geldigheidsvlag_geweigerd(self, veld):
        ruw = self._ruw(_a("K1", BUUR, "onbesproken"))
        ruw[veld] = "het materiaal beschrijft geen verhuurgeval buiten uitleen"
        fout = _fout(ruw, self._invoer())
        assert fout.soort == "schemafout" and veld in str(fout)

    def test_onbesproken_duur_levert_nooit_een_insluitingsconclusie(self):
        uitkomst = br.bepaal(self._ruw(_a("K1", BUUR, "onbesproken")), self._invoer())
        assert uitkomst.uitkomst == "review_required"
        tekst = br.render(uitkomst).casefold()
        for verboden in ("valt binnen", "geen geval buiten", "buiten uitleen"):
            assert verboden not in tekst


# --- dekking en scope ------------------------------------------------------------------------


class TestDekking:
    def test_verborgen_extra_conjunctie_in_de_kern_geweigerd(self):
        ruw = _interpretatie_a()
        ruw["kern"]["kenmerken"] = [
            k for k in ruw["kern"]["kenmerken"] if k["id"] != "K2"
        ]
        ruw["antwoorden"] = [a for a in ruw["antwoorden"] if a["kenmerk_id"] != "K2"]
        fout = _fout(ruw, _invoer())
        assert fout.soort == "kerndekking_onvolledig" and "kosteloos" in str(fout)

    def test_disjunctie_buiten_de_ondersteunde_taal(self):
        definitie = DEFINITIE.replace(
            "tijdelijk en kosteloos", "tijdelijk of kosteloos"
        )
        fout = _fout(_interpretatie_a(), _invoer(definitie=definitie))
        assert fout.soort == "kerndekking_onvolledig" and "'of'" in str(fout)

    def test_onbesproken_bindt_het_volledige_relevante_materiaal(self):
        interpretatie = br.valideer_interpretatie(_interpretatie_a(), _invoer())
        eenheden = {e.naam: e for e in br.controle_eenheden(interpretatie, _invoer())}
        citaten = eenheden[f"buur:{BUUR}"].pakket.inhoud["citaten"]
        volledig = {c["citaat"] for c in citaten if c["omvang"] == OMVANG_VOLLEDIG}
        assert {BRON_A, BUUR_A} <= volledig
        assert any(c["omvang"] == OMVANG_FRAGMENT for c in citaten)

    def test_elk_feit_noemt_zijn_eigen_citaat(self):
        interpretatie = br.valideer_interpretatie(_interpretatie_a(), _invoer())
        eenheden = {e.naam: e for e in br.controle_eenheden(interpretatie, _invoer())}
        pakket = eenheden[f"buur:{BUUR}"].pakket
        uitspraak = pakket.inhoud["uitspraak"]
        nummers = {c["id"] for c in pakket.inhoud["citaten"]}
        feiten = uitspraak.split("Volgens de citaten:", 1)[1]
        assert feiten.count("(B") == 4  # vier kenmerken, elk met eigen route
        assert all(n in uitspraak for n in nummers)

    def test_onbesproken_met_eigen_citaten_geweigerd(self):
        ruw = _vervang(
            _interpretatie_a(), "K2", BUUR,
            {**_a("K2", BUUR, "onbesproken"),
             "citaten": [{"material_id": BUURMATERIAAL, "citaat": "tijdelijk"}]},
        )  # fmt: skip
        assert _fout(ruw, _invoer()).soort == "schemafout"

    def test_onbesproken_naast_ander_antwoord_geweigerd(self):
        ruw = _vervang(
            _interpretatie_a(), "K1", BUUR,
            _a("K1", BUUR, "onbesproken"),
            _a("K1", BUUR, "bevestigd", [(BUURMATERIAAL, "tijdelijk ter beschikking")]),
        )  # fmt: skip
        assert _fout(ruw, _invoer()).soort == "schemafout"

    def test_niet_letterlijk_citaat_geweigerd(self):
        ruw = _vervang(
            _interpretatie_a(), "K1", BUUR,
            _a("K1", BUUR, "bevestigd", [(BUURMATERIAAL, "kortstondig ter beschikking")]),
        )  # fmt: skip
        assert _fout(ruw, _invoer()).soort == "citaatfout"

    def test_leeg_bereik_is_door_de_app_vastgesteld_open(self):
        invoer = br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": DEFINITIE, BUURMATERIAAL: BUUR_A},
            buren=((BUUR, "verhuur"),),
        )
        ruw = _interpretatie_a()
        ruw["antwoorden"] = [
            *(_a(k, "doel", "onbesproken") for k in ("K1", "K2", "K3", "K4")),
            *(a for a in ruw["antwoorden"] if a["onderwerp"] == BUUR),
        ]
        assert br.bepaal(ruw, invoer).uitkomst == "review_required"
        interpretatie = br.valideer_interpretatie(ruw, invoer)
        namen = [e.naam for e in br.controle_eenheden(interpretatie, invoer)]
        assert "doel" not in namen


# --- betaald / kosteloos / onbekend, equivalentie en conflict ------------------------------


BUUR_BETAALD = BUUR_A.replace("aan een medewerker", "tegen betaling aan een medewerker")


class TestKennisstanden:
    @pytest.mark.parametrize(
        ("antwoord", "aspect", "uitkomst"),
        [
            (_a("K2", BUUR, "ontkend", [(BUURMATERIAAL, "tegen betaling")]),
             "afgrenzend", "pass"),
            (_a("K2", BUUR, "bevestigd", [(BUURMATERIAAL, "tegen betaling")]),
             "gedeeld", "review_required"),
            (_a("K2", BUUR, "onbesproken"), "onbeslist", "review_required"),
        ],
    )  # fmt: skip
    def test_drie_kennisstanden_blijven_uit_elkaar(self, antwoord, aspect, uitkomst):
        ruw = _vervang(_interpretatie_a(), "K2", BUUR, antwoord)
        resultaat = br.bepaal(ruw, _invoer(buur=BUUR_BETAALD))
        assert _aspect(resultaat, "kosten").aspect == aspect
        assert resultaat.uitkomst == uitkomst

    def test_equivalente_formulering_zonder_het_woord(self):
        definitie = DEFINITIE.replace("kosteloos", "zonder vergoeding")
        ruw = _interpretatie_a()
        ruw["kern"]["kenmerken"][1]["citaat"] = "zonder vergoeding"
        ruw = _vervang(
            ruw,
            "K2",
            BUUR,
            _a("K2", BUUR, "ontkend", [(BUURMATERIAAL, "tegen betaling")]),
        )
        uitkomst = br.bepaal(ruw, _invoer(buur=BUUR_BETAALD, definitie=definitie))
        assert "kosteloos" not in definitie
        assert uitkomst.uitkomst == "pass"
        assert _aspect(uitkomst, "kosten").aspect == "afgrenzend"

    def test_tegengestelde_broninformatie_wordt_zichtbaar_conflict(self):
        bron = BRON_A.replace(
            "Verdere informatie", "Verhuur is altijd betaald. Verdere informatie"
        )
        buur = BUUR_A.replace("aan een medewerker", "kosteloos aan een medewerker")
        ruw = _vervang(
            _interpretatie_a(), "K2", BUUR,
            _a("K2", BUUR, "bevestigd", [(BUURMATERIAAL, "kosteloos aan een medewerker")]),
            _a("K2", BUUR, "ontkend", [(BRON, "Verhuur is altijd betaald.")]),
        )  # fmt: skip
        uitkomst = br.bepaal(ruw, _invoer(bron=bron, buur=buur))
        assert _aspect(uitkomst, "kosten").reden == "conflict"
        assert uitkomst.uitkomst == "review_required"
        assert "tegenstrijdig" in br.render(uitkomst)


# --- onderwerp, rol en context ---------------------------------------------------------------


class TestOnderwerpEnContext:
    def test_doelbetekenis_mag_de_definitie_niet_als_bron_gebruiken(self):
        ruw = _vervang(
            _interpretatie_c(), "K1", "doel",
            _a("K1", "doel", "bevestigd", [("definition", "tijdelijk")]),
        )  # fmt: skip
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "onderwerpfout"

    def test_beschrijving_van_een_andere_buur_geweigerd(self):
        ander = "neighbour:gebruiker:verkoop"
        invoer = _invoer(BRON_C, BUUR_C, extra={ander: "permanent overdragen"})
        ruw = _vervang(
            _interpretatie_c(), "K1", BUUR,
            _a("K1", BUUR, "ontkend", [(ander, "permanent overdragen")]),
        )  # fmt: skip
        assert _fout(ruw, invoer).soort == "onderwerpfout"

    def test_onbekend_onderwerp_geweigerd(self):
        ruw = copy.deepcopy(_interpretatie_c())
        ruw["antwoorden"].append(_a("K1", "gebruiker:onbekend", "onbesproken"))
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "schemafout"

    def test_feit_uit_andere_context_niet_combineerbaar(self):
        ruw = _vervang(
            _interpretatie_c(), "K1", BUUR,
            _a("K1", BUUR, "ontkend", [(BUURMATERIAAL, "permanent ter beschikking")],
               context="andere"),
        )  # fmt: skip
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "contextfout"

    def test_voorwaardelijke_doelbetekenis_expliciet_buiten_bereik(self):
        # v3 (K4-rest): een voorwaardelijke doeleis wordt niet verwerkt en ook niet
        # stil onbekend gemaakt; ze gaat als buiten_bereik mét tekst en citaat terug.
        ruw = _vervang(
            _interpretatie_c(), "K1", "doel",
            _a("K1", "doel", "bevestigd", [(BRON, DOELCITAAT)],
               voorwaarden=["alleen voor vaste medewerkers"]),
        )  # fmt: skip
        fout = _fout(ruw, _invoer(BRON_C, BUUR_C))
        assert fout.soort == "buiten_bereik"
        assert "alleen voor vaste medewerkers" in fout.melding
        assert DOELCITAAT in fout.melding and "K1 (duur: tijdelijk)" in fout.melding
        tekst = br.render(br.bepaal(ruw, _invoer(BRON_C, BUUR_C)))
        assert "alleen voor vaste medewerkers" in tekst

    def test_voorwaardelijke_ontkenning_in_doel_ook_buiten_bereik(self):
        ruw = _vervang(
            _interpretatie_c(), "K4", "doel",
            _a("K4", "doel", "bevestigd", [(BRON, TERUGGAVE_DOEL)]),
            _a("K4", "doel", "ontkend", [(BRON, DOELCITAAT)], voorwaarden=["bij verlies"]),
        )  # fmt: skip
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "buiten_bereik"

    def test_voorwaarde_naast_gelijke_onvoorwaardelijke_eis_is_verwerkt(self):
        # De eis geldt al zonder voorwaarde; de voorwaardelijke herhaling voegt niets toe.
        ruw = _vervang(
            _interpretatie_c(), "K1", "doel",
            _a("K1", "doel", "bevestigd", [(BRON, DOELCITAAT)]),
            _a("K1", "doel", "bevestigd", [(BRON, TERUGGAVE_DOEL)],
               voorwaarden=["alleen voor vaste medewerkers"]),
        )  # fmt: skip
        uitkomst = br.bepaal(ruw, _invoer(BRON_C, BUUR_C))
        assert uitkomst.uitkomst == "pass"
        assert _aspect(uitkomst, "duur").aspect == "afgrenzend"

    def test_gemengd_alleen_voor_de_hele_buur(self):
        ruw = _vervang(
            _interpretatie_c(), "K1", "doel",
            _a("K1", "doel", "gemengd", [(BRON, DOELCITAAT)]),
        )  # fmt: skip
        assert _fout(ruw, _invoer(BRON_C, BUUR_C)).soort == "schemafout"

    def test_kenmerken_worden_alleen_per_kenmerk_gecombineerd(self):
        ruw = _vervang(
            _interpretatie_a(), "K4", BUUR,
            _a("K4", BUUR, "ontkend", [(BUURMATERIAAL, "die de apparatuur daarna teruggeeft")]),
        )  # fmt: skip
        ruw = _vervang(ruw, "K4", "doel", _a("K4", "doel", "onbesproken"))
        uitkomst = br.bepaal(ruw, _invoer())
        assert _aspect(uitkomst, "duur").aspect == "gedeeld"
        assert _aspect(uitkomst, "teruggave").reden == "doelbetekenis_niet_vastgesteld"
        assert uitkomst.uitkomst == "review_required"


# --- fail zonder kenmerk en weergave ---------------------------------------------------------


class TestFailEnWeergave:
    def test_kern_zonder_kenmerk_is_fail(self):
        invoer = br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={"definition": "ter beschikking stellen van apparatuur",
                       BUURMATERIAAL: BUUR_A},
            buren=((BUUR, "verhuur"),),
        )  # fmt: skip
        ruw = _ruw({"bovenbegrip": "ter beschikking stellen van apparatuur",
                    "kenmerken": []}, [])  # fmt: skip
        uitkomst = br.bepaal(ruw, invoer)
        assert uitkomst.uitkomst == "fail"
        assert "geen kenmerk" in br.render(uitkomst)

    def test_altijd_bereikzin_en_geen_insluiting(self):
        for ruw, invoer in (
            (_interpretatie_a(), _invoer()),
            (_interpretatie_c(), _invoer(BRON_C, BUUR_C)),
            (_interpretatie_a(), _invoer(onvolledig={BRON})),
        ):
            tekst = br.render(br.bepaal(ruw, invoer))
            assert br.BEREIKZIN in tekst
            assert "valt binnen" not in tekst.casefold()

    def test_open_zegt_alleen_wat_het_materiaal_niet_vaststelt(self):
        tekst = br.render(br.bepaal(_interpretatie_a(), _invoer()))
        assert "geen ontkenning" in tekst
        assert "geen uitspraak over andere mogelijke verschillen" in tekst

    def test_error_noemt_geen_oordeel_over_de_definitie(self):
        tekst = br.render(br.bepaal(_interpretatie_a(), _invoer(onvolledig={BRON})))
        assert tekst.startswith("Geen oordeel")


# --- R16-herstel: onderwerpbinding van broncitaten (v4) ----------------------------------------

UITLEENPASSAGE = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug."
)
VERHUURPASSAGE_A = (
    "Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan een "
    "medewerker; de medewerker geeft de apparatuur daarna terug."
)


class TestOnderwerpbinding:
    """Een bron die ook een ander geregistreerd begrip noemt (uitleen én verhuur):
    een broncitaat noemt zijn eigen onderwerp als heel woord (tekstanker, v5).
    Een tweede begripsnaam mag; de naam bewijst geen inhoudelijke betrekking.

    Reviewerbevinding R16 (bewijsregels-r16-uitvoerreview-result-v1.md, punt 1 en 2):
    dezelfde woorden staan onder Uitleen en onder Verhuur; `material_id + citaat`
    bindt de bedoelde vindplaats niet aan haar onderwerp.
    """

    def test_herhaald_kort_citaat_blijft_citaatfout(self):
        # Geen eerste treffer kiezen, geen versoepeling van de unieke vindplaats.
        ruw = _vervang(
            _interpretatie_a(), "K3", "doel",
            _a("K3", "doel", "bevestigd", [(BRON, "aan een medewerker")]),
        )  # fmt: skip
        assert _fout(ruw, _invoer()).soort == "citaatfout"

    def test_verhuurteruggave_is_geen_uitleenbewijs(self):
        ruw = _vervang(
            _interpretatie_a(), "K4", "doel",
            _a("K4", "doel", "bevestigd", [(BRON, VERHUURPASSAGE_A)]),
        )  # fmt: skip
        fout = _fout(ruw, _invoer())
        assert fout.soort == "onderwerpfout" and "verhuur" in fout.melding

    def test_losse_teruggaafzin_zonder_onderwerp_geweigerd(self):
        # C: de teruggaafzin staat letterlijk maar één keer, maar zonder 'Uitleen'.
        ruw = _vervang(
            _interpretatie_c(), "K4", "doel",
            _a("K4", "doel", "bevestigd",
               [(BRON, "de medewerker geeft de apparatuur daarna terug")]),
        )  # fmt: skip
        fout = _fout(ruw, _invoer(BRON_C, BUUR_C))
        assert fout.soort == "onderwerpfout" and "uitleen" in fout.melding

    def test_benoemde_passage_bindt_onderwerp_en_verwijzing(self):
        ruw = _vervang(
            _interpretatie_c(), "K4", "doel",
            _a("K4", "doel", "bevestigd", [(BRON, UITLEENPASSAGE)]),
        )  # fmt: skip
        assert br.bepaal(ruw, _invoer(BRON_C, BUUR_C)).uitkomst == "pass"

    def test_citaat_met_beide_begrippen_gaat_naar_de_semantische_controle(self):
        # R16-H-01: geen verbod op een tweede begripsnaam. De naam is alleen een
        # tekstanker; of de passage inhoudelijk over uitleen gaat, toetst de controle.
        beide = UITLEENPASSAGE + " " + VERHUURPASSAGE_A
        ruw = _vervang(
            _interpretatie_a(),
            "K4",
            "doel",
            _a("K4", "doel", "bevestigd", [(BRON, beide)]),
        )
        interpretatie = br.valideer_interpretatie(ruw, _invoer())
        doel = _eenheden(interpretatie, _invoer())["doel"].pakket.inhoud
        assert beide in {c["citaat"] for c in doel["citaten"]}

    def test_samengestelde_begripsnaam_is_niet_de_kortere_naam(self):
        # R16-H-01: 'uitleenovereenkomst' is geen vermelding van 'uitleen' (geen
        # prefixverwarring), maar blijft een geldig anker voor zichzelf.
        overeenkomst = "gebruiker:uitleenovereenkomst"
        bron = (
            "Uitleen: apparatuur tijdelijk ter beschikking. "
            "Uitleenovereenkomst: tijdelijk recht op gebruik."
        )
        invoer = br.Vergelijkingsinvoer(
            term="uitleen",
            materiaal={
                "definition": "tijdelijk ter beschikking stellen van apparatuur",
                BRON: bron,
                f"neighbour:{overeenkomst}": "overeenkomst over gebruik",
            },
            buren=((overeenkomst, "uitleenovereenkomst"),),
        )

        def ruw(doelcitaat):
            return _ruw(
                {"bovenbegrip": "ter beschikking stellen van apparatuur",
                 "kenmerken": [{"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk",
                                "citaat": "tijdelijk"}]},
                [_a("K1", "doel", "bevestigd", [(BRON, doelcitaat)]),
                 _a("K1", overeenkomst, "bevestigd",
                    [(BRON, "Uitleenovereenkomst: tijdelijk recht op gebruik.")])],
            )  # fmt: skip

        assert br.valideer_interpretatie(ruw("Uitleen: apparatuur tijdelijk"), invoer)
        fout = _fout(ruw("Uitleenovereenkomst: tijdelijk recht"), invoer)
        assert fout.soort == "onderwerpfout" and "'uitleen'" in fout.melding

    def test_buurcitaat_uit_de_uitleenpassage_geweigerd(self):
        ruw = _vervang(
            _interpretatie_a(), "K1", BUUR,
            _a("K1", BUUR, "bevestigd", [(BRON, UITLEENPASSAGE)]),
        )  # fmt: skip
        assert _fout(ruw, _invoer()).soort == "onderwerpfout"

    def test_herhaalde_woorden_met_ontkenning(self):
        bron = (
            "Uitleen: de medewerker geeft de apparatuur terug. Verhuur: de medewerker "
            "geeft de apparatuur niet terug."
        )
        kort = _doelcitaat(_interpretatie_a(), "de medewerker geeft de apparatuur")
        assert _fout(kort, _invoer(bron)).soort == "citaatfout"
        verkeerd = _doelcitaat(
            _interpretatie_a(), "Verhuur: de medewerker geeft de apparatuur niet terug."
        )
        assert _fout(verkeerd, _invoer(bron)).soort == "onderwerpfout"
        goed = _doelcitaat(
            _interpretatie_a(), "Uitleen: de medewerker geeft de apparatuur terug."
        )
        assert br.valideer_interpretatie(goed, _invoer(bron)) is not None

    def test_herhaalde_woorden_met_voorwaarde_gaan_letterlijk_naar_de_controle(self):
        # De code ziet de voorwaarde niet als het model haar weglaat; de doelcontrole
        # krijgt haar wel letterlijk plus de eis 'geen voorwaardelijke afspraak'.
        # Of het model dan weigert, is modelafhankelijk (niet bewezen).
        bron = (
            "Uitleen: bij storing geeft de medewerker de apparatuur terug. Verhuur: de "
            "medewerker geeft de apparatuur terug."
        )
        ruw = _doelcitaat(
            _interpretatie_a(),
            "Uitleen: bij storing geeft de medewerker de apparatuur terug.",
        )
        interpretatie = br.valideer_interpretatie(ruw, _invoer(bron))
        doel = _eenheden(interpretatie, _invoer(bron))["doel"].pakket.inhoud
        assert any("bij storing" in c["citaat"] for c in doel["citaten"])
        assert "geen voorwaardelijke afspraak" in doel["uitspraak"]

    def test_bron_met_een_begrip_vraagt_geen_naam(self):
        # Grens van de regel: noemt de bron geen ander geregistreerd begrip, dan
        # bindt het materiaal zelf het onderwerp (de controle toetst de rest).
        ruw = _doelcitaat(_interpretatie_a(), "stelt apparatuur tijdelijk en kosteloos")
        assert br.bepaal(ruw, _invoer(UITLEENPASSAGE)).uitkomst == "review_required"


def _doelcitaat(ruw, citaat):
    """Alle doelantwoorden met één broncitaat (voor bronnen zonder de standaardtekst)."""
    ruw = copy.deepcopy(ruw)
    for a in ruw["antwoorden"]:
        if a["onderwerp"] == "doel":
            a["citaten"] = [{"material_id": BRON, "citaat": citaat}]
    return ruw


# --- R16-herstel: reikwijdte en domein van de controlepakketten (v4) ------------------------


def _eenheden(interpretatie, invoer) -> dict:
    return {e.naam: e for e in br.controle_eenheden(interpretatie, invoer)}


class TestControlescope:
    """Positieve definitieclaims worden getoetst binnen het gebonden domein.

    Reviewerbevinding R16 punt 2: het doelpakket verloor de volledige lokale
    bron en de vastgelegde context; het sjabloon claimde 'voor elk geval van
    uitleen' zonder domeinbeperking.
    """

    def _pakket(self, ruw, invoer, naam):
        interpretatie = br.valideer_interpretatie(ruw, invoer)
        return _eenheden(interpretatie, invoer)[naam].pakket.inhoud

    def test_doelpakket_draagt_volledige_bron_en_vastgelegde_context(self):
        doel = self._pakket(_interpretatie_a(), _invoer(), "doel")
        volledig = {
            c["citaat"] for c in doel["citaten"] if c["omvang"] == OMVANG_VOLLEDIG
        }
        assert BRON_A in volledig
        assert "organisatorische_context: Servicedesk ICT-middelen" in volledig

    def test_context_algemeen_laat_het_vastgelegde_domein_niet_vallen(self):
        ruw = copy.deepcopy(_interpretatie_a())
        assert all(a["context"] == "algemeen" for a in ruw["antwoorden"])
        doel = self._pakket(ruw, _invoer(), "doel")
        assert any(c["herkomst"] == "context" for c in doel["citaten"])
        assert "vastgelegde context" in doel["uitspraak"]

    def test_geen_universele_reikwijdte_buiten_het_materiaal(self):
        for naam in ("doel", f"buur:{BUUR}"):
            inhoud = self._pakket(_interpretatie_a(), _invoer(), naam)
            assert "elk geval" not in inhoud["uitspraak"]
            assert "bepaling" in inhoud["uitspraak"]
            assert "geen enkel voorval" in inhoud["uitspraak"]
            assert "niet daarbuiten" in inhoud["uitspraak"]

    def test_onbesproken_blijft_de_strenge_volledigheidscontrole(self):
        buur = self._pakket(_interpretatie_a(), _invoer(), f"buur:{BUUR}")
        assert "zegt over verhuur niets over kosten: kosteloos of het tegendeel" in (
            buur["uitspraak"]
        )
        volledig = {
            c["citaat"] for c in buur["citaten"] if c["omvang"] == OMVANG_VOLLEDIG
        }
        assert {BRON_A, BUUR_A} <= volledig

    def test_zonder_positief_feit_geen_bepalingszin(self):
        # Alleen onbesproken feiten: niets te binden aan een bepaling.
        ruw = copy.deepcopy(_interpretatie_c())
        ruw["antwoorden"] = [
            *_zonder(_zonder(ruw["antwoorden"], "K1", BUUR), "K3", BUUR),
            _a("K1", BUUR, "onbesproken"),
            _a("K3", BUUR, "onbesproken"),
        ]
        buur = self._pakket(ruw, _invoer(BRON_C, BUUR_C), f"buur:{BUUR}")
        assert "bepaling" not in buur["uitspraak"]
