"""DEF-768 B1 — bewijsscorer M-a…M-d voor interpretatieproeven (alleen evaluatie).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B1:
de zeven plangevallen (A juist, A met de inleiding als bewijs, D blind
hergebruik, E met en zonder voorwaarde, onzin, F7). Aanvulling van de
opdracht: de scorer geeft ook bij ongeldige modeluitvoer (niet-dict
antwoorden, niet-lijst citaten, onbekende eenheid, …) nooit een exception.
Aanvulling v4 (besluit optie 2): het voorwaardeoordeel bij E is altijd van
Chris; `eindoordeel` combineert het proefoordeel met het oordeelbestand.

A is exact het geval van R17-item A (H3, inline; gelijkheid met de git-ignored
R17-invoer in `TestBron`); D en E zijn SYNTHETISCH, GEEN
MODELUITVOER (bronteksten uit het plan). Alle interpretaties hier zijn
vooraf opgesteld, geen modeluitvoer. Geen netwerk.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.scripts.test_def768_r16_bewijsregelproef import H3

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))
sys.path.insert(0, str(ROOT / "src"))

import bewijsscorer as bs
import migreer_r7_naar_v2 as mig

from domain.ess05 import bewijsregels as br

R17_INVOER = ROOT / "reports" / "DEF-768-AI-20260928-R17" / "bewijsregel-invoer-v1.json"
INLEIDING = (
    "Lokale testwerkinstructie van de Servicedesk ICT-middelen, alleen voor deze "
    "beoordelingstest."
)
#: Plan B2, item D (SYNTHETISCH, GEEN MODELUITVOER).
D_BRON = (
    f"{INLEIDING} Uitleen: de servicedesk stelt apparatuur tijdelijk ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Voor uitleen "
    "betaalt de medewerker niets. Verhuur: de servicedesk stelt apparatuur tijdelijk "
    "ter beschikking aan een medewerker; de medewerker geeft de apparatuur daarna "
    "terug. Voor verhuur betaalt de medewerker een vergoeding."
)
#: Plan B2, item E (SYNTHETISCH, GEEN MODELUITVOER).
E_BRON = (
    f"{INLEIDING} Uitleen: bij storing stelt de servicedesk apparatuur tijdelijk en "
    "kosteloos ter beschikking aan een medewerker; de medewerker geeft de apparatuur "
    "daarna terug. Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Verdere "
    "informatie over verhuur staat niet in deze werkinstructie."
)
BUUR = bs.BUURBESCHRIJVING

#: Orakels in de structuur van aanvulling C3 (Codex-review B3/B4): per feit
#: `vereist` (minstens één genoemde eenheid) en `toegestaan` (context erbij).
ORAKEL_A = {
    "kenmerken": {
        "tijdelijk": {
            "doel": {"toestand": ["bevestigd"], "vereist": ["Uitleen:"], "toegestaan": []},
            "verhuur": {"toestand": ["bevestigd"], "vereist": ["Verhuur:", BUUR],
                        "toegestaan": []},
        },
        "kosteloos": {
            "doel": {"toestand": ["bevestigd"], "vereist": ["Uitleen:"], "toegestaan": []},
            "verhuur": {"toestand": ["onbesproken"], "vereist": [], "toegestaan": [],
                        "f7": ["ontkend"]},
        },
    },
    "dragend": ["kosteloos"],
    "uitkomst": ["review_required"],
}  # fmt: skip
ORAKEL_D = {
    "kenmerken": {
        "kosteloos": {
            "doel": {"toestand": ["bevestigd"], "vereist": ["Voor uitleen betaalt"],
                     "toegestaan": ["Uitleen:"]},
            "verhuur": {"toestand": ["ontkend"], "vereist": ["Voor verhuur betaalt"],
                        "toegestaan": ["Verhuur:", BUUR]},
        }
    },
    "dragend": ["kosteloos"],
    "uitkomst": ["pass"],
}  # fmt: skip
ORAKEL_E = {
    "kenmerken": {},
    "dragend": [],
    # Aanvulling v4 (besluit optie 2): het voorwaardeoordeel is altijd van Chris.
    "voorwaarde": "storing",
    # Aanvulling v2 (B2-rest): alleen de onverwerkte voorwaardelijke doeleis.
    "uitkomst": ["error/buiten_bereik"],
}
KERN = {
    "bovenbegrip": "ter beschikking stellen van apparatuur",
    "kenmerken": [
        {"id": "K1", "kenmerk": "duur", "waarde": "tijdelijk", "citaat": "tijdelijk"},
        {
            "id": "K2",
            "kenmerk": "vergoeding",
            "waarde": "kosteloos",
            "citaat": "kosteloos",
        },
        {
            "id": "K3",
            "kenmerk": "ontvanger",
            "waarde": "een medewerker",
            "citaat": "aan een medewerker",
        },
        {
            "id": "K4",
            "kenmerk": "teruggave",
            "waarde": "de medewerker geeft terug",
            "citaat": "die de apparatuur daarna teruggeeft",
        },
    ],
}


def _geval(bron: str | None = None) -> dict:
    """Het geval van R17-item A (H3, inline: de R17-invoer is git-ignored; gelijkheid
    zie TestBron), desgewenst met een andere bronsnippet (D/E)."""
    geval = copy.deepcopy(H3)
    if bron is not None:
        geval["bronnen"][0]["snippet"] = bron
    return geval


def _invoer(bron: str | None = None) -> br.Vergelijkingsinvoer:
    geval = _geval(bron)
    materiaal, buren, _ = mig.verificatiemateriaal(geval)
    return br.Vergelijkingsinvoer(
        term=geval["begrip"],
        materiaal=materiaal,
        buren=tuple((b.id, b.term) for b in buren),
    )


def _u(invoer: br.Vergelijkingsinvoer, prefix: str) -> str:
    """Het ene eenheidsnummer waarvan de tekst met `prefix` begint (BUUR: buurbeschrijving)."""
    treffers = [
        u
        for u, r in invoer.eenheden().items()
        if (
            r.material_id.startswith("neighbour:")
            if prefix == BUUR
            else invoer.materiaal[r.material_id][r.start : r.end].startswith(prefix)
        )
    ]
    assert len(treffers) == 1, (prefix, treffers)
    return treffers[0]


def _ruw(invoer, doel, verhuur, *, buiten_kern=(), buiten_bereik=()) -> dict:
    """Een interpretatie (/3); doel/verhuur: kid -> (toestand, prefixen[, voorwaarden])."""
    buur = invoer.buren[0][0]
    antwoorden = []
    for onderwerp, per_kenmerk in (("doel", doel), (buur, verhuur)):
        for kid, spec in per_kenmerk.items():
            toestand, prefixen, *rest = spec
            antwoorden.append(
                {
                    "kenmerk_id": kid,
                    "onderwerp": onderwerp,
                    "toestand": toestand,
                    "voorwaarden": list(rest[0]) if rest else [],
                    "context": "zaakcontext",
                    "citaten": [_u(invoer, p) for p in prefixen],
                }
            )
    return {
        "schema_version": br.INTERPRETATIESCHEMA,
        "kern": copy.deepcopy(KERN),
        "buiten_kern": list(buiten_kern),
        "buurgroepen": [],
        "buiten_bereik": list(buiten_bereik),
        "antwoorden": antwoorden,
    }


_UITLEEN4 = {k: ("bevestigd", ["Uitleen:"]) for k in ("K1", "K2", "K3", "K4")}


def _a_juist(invoer):
    """A met hergebruik: de Uitleen-eenheid draagt K1–K4 van het doel."""
    return _ruw(
        invoer,
        _UITLEEN4,
        {
            "K1": ("bevestigd", ["Verhuur:", BUUR]),
            "K2": ("onbesproken", []),
            "K3": ("bevestigd", ["Verhuur:"]),
            "K4": ("bevestigd", [BUUR]),
        },
    )


def _d_juist(invoer, kosteloos_doel=("Voor uitleen betaalt",)):
    return _ruw(
        invoer,
        {**_UITLEEN4, "K2": ("bevestigd", list(kosteloos_doel))},
        {
            "K1": ("bevestigd", ["Verhuur:", BUUR]),
            "K2": ("ontkend", ["Voor verhuur betaalt"]),
            "K3": ("bevestigd", ["Verhuur:"]),
            "K4": ("bevestigd", ["Verhuur:"]),
        },
    )


_E_VERHUUR = {
    "K1": ("bevestigd", ["Verhuur:", BUUR]),
    "K2": ("onbesproken", []),
    "K3": ("bevestigd", ["Verhuur:"]),
    "K4": ("bevestigd", [BUUR]),
}


def _e(invoer, k2_doel, **extra):
    return _ruw(invoer, {**_UITLEEN4, "K2": k2_doel}, _E_VERHUUR, **extra)


def _alles_onwaar(score):
    assert score["m_b_dragend_ok"] is False
    assert score["m_c_dragend_ok"] is False
    assert score["m_d"]["ok"] is False


# --- de zeven plangevallen ------------------------------------------------------------------


class TestPlangevallen:
    def test_a_juist_met_hergebruik(self):
        invoer = _invoer()
        score = bs.scoor(_a_juist(invoer), invoer, ORAKEL_A)
        assert score["m_d"] == {
            "uitkomst": "review_required",
            "fout": None,
            "verwacht": ["review_required"],
            "ok": True,
        }
        assert score["m_b_dragend_ok"] is True
        assert score["m_c_dragend_ok"] is True
        assert score["m_a"] == {"items": 7, "fouten": []}
        assert score["f7_afwijkingen"] == []
        assert score["voorwaarde_behouden"] is None

    def test_a_inleiding_als_bewijs_voor_kosteloos(self):
        """De uitkomst lijkt goed, maar het bewijs draagt het dragende feit niet."""
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"
        ]
        k2["citaten"] = [_u(invoer, "Lokale testwerkinstructie")]
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is False
        assert score["m_c_dragend_ok"] is True
        (feit,) = [
            f
            for f in score["feiten"]
            if (f["kernwoord"], f["onderwerp"]) == ("kosteloos", "doel")
        ]
        assert feit["eenheden"] == [INLEIDING]
        assert feit["draagt"] is False

    def test_d_juist(self):
        invoer = _invoer(D_BRON)
        score = bs.scoor(_d_juist(invoer), invoer, ORAKEL_D)
        assert score["m_d"]["uitkomst"] == "pass"
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is True
        assert score["m_c_dragend_ok"] is True
        assert score["m_a"]["fouten"] == []

    def test_d_blind_hergebruik(self):
        """De Uitleen-eenheid noemt in D geen kosten: hergebruik draagt kosteloos niet."""
        invoer = _invoer(D_BRON)
        score = bs.scoor(_d_juist(invoer, ("Uitleen:",)), invoer, ORAKEL_D)
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is False
        assert score["m_c_dragend_ok"] is True

    def test_e_met_voorwaarde_wacht_op_chris(self):
        """Aanvulling v4: ook de juiste voorwaarde is nooit automatisch behouden."""
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        assert score["m_d"]["ok"] is True

    def test_e_voorwaarde_weggevallen(self):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e(invoer, ("bevestigd", ["Uitleen:"])), invoer, ORAKEL_E)
        assert score["m_d"]["uitkomst"] == "review_required"
        # Aanvulling v2: review_required is voor E geen toegestane uitkomst meer.
        assert score["m_d"]["ok"] is False
        assert score["voorwaarde_behouden"] is False

    def test_onzin_geen_exception_alles_onwaar(self):
        invoer = _invoer()
        score = bs.scoor({"x": 1}, invoer, ORAKEL_A)
        _alles_onwaar(score)
        assert score["m_d"]["uitkomst"] == "error"
        score_e = bs.scoor({"x": 1}, _invoer(E_BRON), ORAKEL_E)
        assert score_e["m_d"]["ok"] is False
        assert score_e["voorwaarde_behouden"] is False

    def test_f7_verhuur_kosteloos_ontkend(self):
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"
        ]
        k2.update(toestand="ontkend", citaten=[_u(invoer, BUUR)])
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["f7_afwijkingen"] == ["kosteloos/verhuur: ['ontkend']"]
        assert score["m_d"]["uitkomst"] == "pass"
        assert score["m_d"]["ok"] is False


# --- aanvulling: nooit een exception bij ongeldige modeluitvoer -------------------------------

_ONGELDIG_RUW = [
    None,
    1,
    "tekst",
    [],
    [{"antwoorden": []}],
    {"antwoorden": 1},
    {"antwoorden": {"a": 1}},
    {"antwoorden": "U3"},
    {"antwoorden": [1, "x", None, []]},
    {"kern": 1, "antwoorden": []},
    {"kern": {"kenmerken": 1}},
    {"kern": {"kenmerken": [1, None, "K1"]}},
    {"kern": {"kenmerken": [{"citaat": "kosteloos"}]}},
    {"kern": {"kenmerken": [{"id": ["K2"], "citaat": "kosteloos"}]}},
    {"kern": {"kenmerken": [{"id": {"x": 1}, "citaat": ["kosteloos"]}]}},
    {"buiten_kern": 1, "antwoorden": [{"voorwaarden": 1}]},
    {"buiten_kern": [1, {"waarde": "storing"}], "antwoorden": []},
    {"buiten_kern": [{"id": ["M1"], "waarde": "storing"}], "antwoorden": []},
    {"buiten_bereik": 1},
    {"buiten_bereik": [1, {"citaat": ["storing"]}]},
]


class TestOngeldigeInvoer:
    @pytest.mark.parametrize("ruw", _ONGELDIG_RUW, ids=repr)
    @pytest.mark.parametrize("orakel", [ORAKEL_A, ORAKEL_D, ORAKEL_E], ids="ADE")
    def test_ongeldige_structuur_geeft_geen_exception(self, ruw, orakel):
        invoer = _invoer()
        score = bs.scoor(ruw, invoer, orakel)
        assert score["m_d"]["ok"] is False
        json.dumps(score)  # het record moet serialiseerbaar zijn
        if orakel["kenmerken"]:
            assert score["m_b_dragend_ok"] is False
            assert score["m_c_dragend_ok"] is False
        if "voorwaarde" in orakel:
            assert score["voorwaarde_behouden"] is False

    def _a_met_k2_doel(self, invoer, **wijziging):
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"
        ]
        k2.update(wijziging)
        return ruw

    @pytest.mark.parametrize(
        "citaten",
        [{}, {"U3": 1}, 3, "U3", None, ("U3",)],
        ids=repr,
    )
    def test_niet_lijst_citaten_draagt_niet(self, citaten):
        invoer = _invoer()
        ruw = self._a_met_k2_doel(invoer, citaten=citaten)
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_b_dragend_ok"] is False
        assert score["m_d"]["ok"] is False
        json.dumps(score)

    @pytest.mark.parametrize(
        "eenheid",
        ["U99", "u3", "", 3, None, ["U3"], {"U": 3}, {"material_id": "x"}],
        ids=repr,
    )
    def test_onbekende_of_ongeldige_eenheid_draagt_niet(self, eenheid):
        invoer = _invoer()
        ruw = self._a_met_k2_doel(invoer, citaten=[_u(invoer, "Uitleen:"), eenheid])
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_b_dragend_ok"] is False
        assert score["m_d"]["ok"] is False
        json.dumps(score)

    def test_onbesproken_met_ongeldige_citaten_draagt_niet(self):
        """Verwacht zonder eenheden (onbesproken): alleen een echte lege lijst draagt."""
        invoer = _invoer()
        orakel = copy.deepcopy(ORAKEL_A)
        orakel["dragend"] = ["kosteloos"]
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"
        ]
        k2["citaten"] = {}
        score = bs.scoor(ruw, invoer, orakel)
        assert score["m_b_dragend_ok"] is False

    @pytest.mark.parametrize("toestand", [["bevestigd"], {"x": 1}, 1, None], ids=repr)
    def test_ongeldige_toestand(self, toestand):
        invoer = _invoer()
        ruw = self._a_met_k2_doel(invoer, toestand=toestand)
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_c_dragend_ok"] is False
        assert score["m_d"]["ok"] is False
        json.dumps(score)

    @pytest.mark.parametrize("veld", ["kenmerk_id", "onderwerp"])
    @pytest.mark.parametrize("waarde", [["K2"], {"x": 1}], ids=repr)
    def test_niet_hashbare_sleutel_in_een_volledig_antwoord(self, veld, waarde):
        """`bepaal` zelf kan hierop een TypeError geven; de scorer vangt dat af."""
        invoer = _invoer()
        ruw = self._a_met_k2_doel(invoer, **{veld: waarde})
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_d"]["ok"] is False
        assert score["m_b_dragend_ok"] is False
        json.dumps(score)

    @pytest.mark.parametrize("voorwaarden", [1, "storing", [["storing"]], {"a": 1}])
    def test_ongeldige_voorwaarden(self, voorwaarden):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"]))
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"
        ]
        k2["voorwaarden"] = voorwaarden
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is False
        json.dumps(score)


# --- voorwaarde bij E: altijd een menselijk oordeel (aanvulling v4, besluit optie 2) --------


def _e_met_m(invoer, waarde, *, kenmerk="aanleiding", toestand="bevestigd"):
    """E met de voorwaarde als M-kenmerk (buiten_kern), met een doelantwoord."""
    ruw = _e(
        invoer,
        ("bevestigd", ["Uitleen:"]),
        buiten_kern=[{"id": "M1", "kenmerk": kenmerk, "waarde": waarde}],
    )
    ruw["antwoorden"].append(
        {
            "kenmerk_id": "M1",
            "onderwerp": "doel",
            "toestand": toestand,
            "voorwaarden": [],
            "context": "zaakcontext",
            "citaten": [_u(invoer, "Uitleen:")] if toestand != "onbesproken" else [],
        }
    )
    ruw["antwoorden"].append(
        {
            "kenmerk_id": "M1",
            "onderwerp": invoer.buren[0][0],
            "toestand": "onbesproken",
            "voorwaarden": [],
            "context": "zaakcontext",
            "citaten": [],
        }
    )
    return ruw


def _v(*voorwaarden):
    """E met deze voorwaarden op het doelantwoord van K2."""
    return lambda i: _e(i, ("bevestigd", ["Uitleen:"], list(voorwaarden)))


def _m(waarde, kenmerk="aanleiding"):
    return lambda i: _e_met_m(i, waarde, kenmerk=kenmerk)


def _m_naast_bij_storing(waarde, kenmerk):
    """Hercontrole v3: een exacte doelvoorwaarde plus een verwijzend M-kenmerk."""

    def maak(invoer):
        ruw = _e_met_m(invoer, waarde, kenmerk=kenmerk)
        (k2,) = [a for a in ruw["antwoorden"]
                 if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"]  # fmt: skip
        k2["voorwaarden"] = ["bij storing"]
        return ruw

    return maak


H = "handmatig_beoordelen"
N = "niet_geslaagd"
#: Elk tegenvoorbeeld uit de Codex-review en de drie hercontroles, plus de juiste
#: formulering: (naam, ruwe interpretatie, categorie). De categorie volgt alleen
#: uit de deterministische uitkomst: error/buiten_bereik → wachten op Chris,
#: anders automatisch niet geslaagd. Geen enkele slaagt automatisch.
E_VOORBEELDEN = [
    # review deel B (B2)
    ("M: ook zonder storing", _m("ook zonder storing"), N),
    # hercontrole v1 (B2-rest)
    ("M: onafhankelijk van storing", _m("onafhankelijk van storing"), N),
    ("M: storing is irrelevant", _m("storing is irrelevant"), N),
    ("M: storing is optioneel", _m("storing is optioneel"), N),
    ("M: alleen bij storing", _m("alleen bij storing"), N),
    # hercontrole v2 (B2-rest-2)
    ("V: bij afwezigheid van storing", _v("bij afwezigheid van storing"), H),
    ("V: als storing ontbreekt", _v("als storing ontbreekt"), H),
    ("V: bij storing of op verzoek", _v("bij storing of op verzoek"), H),
    ("V: bij de storingsdienst", _v("bij de storingsdienst"), H),
    # hercontrole v3 (B2-rest-3): combinaties naast een exacte formulering
    ("V: bij storing + deze voorwaarde is optioneel",
     _v("bij storing", "deze voorwaarde is optioneel"), H),
    ("V: bij storing + als storing ontbreekt",
     _v("bij storing", "als storing ontbreekt"), H),
    ("V: bij storing + of op verzoek", _v("bij storing", "of op verzoek"), H),
    ("V: bij storing + M: geldigheid van deze voorwaarde = optioneel",
     _m_naast_bij_storing("optioneel", "geldigheid van deze voorwaarde"), H),
    # de juiste formulering: ook die slaagt nooit automatisch
    ("V: bij storing", _v("bij storing"), H),
    ("V:   Bij  STORING. ", _v("  Bij  STORING. "), H),
    ("V: in geval van een storing", _v("in geval van een storing"), H),
    # ontkenning, alleen buiten bereik en weggevallen: geen automatische status meer
    ("V: niet bij storing", _v("niet bij storing"), H),
    ("buiten bereik", lambda i: _e(i, ("bevestigd", ["Uitleen:"]),
                                  buiten_bereik=[{"citaat": "bij storing",
                                                  "reden": "voorwaardelijk"}]), H),
    ("weggevallen", lambda i: _e(i, ("bevestigd", ["Uitleen:"])), N),
]  # fmt: skip
_IDS = [n for n, _, _ in E_VOORBEELDEN]
_WACHT = [(n, m) for n, m, c in E_VOORBEELDEN if c == H]


def _a_runs(n: int) -> list[dict]:
    """n echte, geslaagde niet-E-runs (A juist, gescoord)."""
    invoer = _invoer()
    oordeel = bs.runoordeel(bs.scoor(_a_juist(invoer), invoer, ORAKEL_A), ORAKEL_A)
    assert oordeel["categorie"] == "geslaagd"
    return [{"sleutel": f"interpretatie|A|{i}", **oordeel} for i in range(n)]


def _e_runs(ruwen) -> list[dict]:
    """E-runs (gescoord) met de sha256 van hun uitvoer, zoals de oordeelroute ze leest."""
    invoer = _invoer(E_BRON)
    runs = []
    for i, maak in enumerate(ruwen, start=1):
        ruw = maak(invoer)
        runs.append(
            {
                "sleutel": f"interpretatie|E|{i}",
                **bs.runoordeel(bs.scoor(ruw, invoer, ORAKEL_E), ORAKEL_E),
                "e_uitvoer_sha256": hashlib.sha256(
                    json.dumps(ruw, ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
            }
        )
    return runs


class TestVoorwaardeMenselijk:
    """Aanvulling v4: E krijgt nooit een automatische voorwaardestatus of -succes."""

    @pytest.mark.parametrize(("naam", "maak", "categorie"), E_VOORBEELDEN, ids=_IDS)
    def test_status_altijd_handmatig_beoordelen(self, naam, maak, categorie):
        invoer = _invoer(E_BRON)
        score = bs.scoor(maak(invoer), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        assert score["voorwaarde_behouden"] is False
        assert "voorwaarde_vermeldingen" not in score

    @pytest.mark.parametrize(("naam", "maak", "categorie"), E_VOORBEELDEN, ids=_IDS)
    def test_nooit_automatisch_geslaagd(self, naam, maak, categorie):
        invoer = _invoer(E_BRON)
        oordeel = bs.runoordeel(bs.scoor(maak(invoer), invoer, ORAKEL_E), ORAKEL_E)
        assert oordeel["categorie"] == categorie
        assert oordeel["m_d_telt"] is False
        assert oordeel["voorwaarde_behouden"] is False
        assert oordeel["voorwaarde_status"] == "handmatig_beoordelen"
        assert oordeel["kritiek"] == []
        assert oordeel["handmatig"] == ([bs.HANDMATIG_E] if categorie == H else [])

    @pytest.mark.parametrize(
        "uitkomst",
        [("review_required", None), ("pass", None), ("fail", None), ("error", "citaat"),
         (None, "exception:ValueError")],
    )  # fmt: skip
    def test_m_d_fout_in_e_blijft_automatisch_niet_geslaagd(
        self, uitkomst, monkeypatch
    ):
        """Deterministisch strenger: zonder error/buiten_bereik is E niet geslaagd,
        ook met de juiste formulering; Chris hoeft die run niet te redden."""
        monkeypatch.setattr(bs, "_uitkomst", lambda ruw, invoer: uitkomst)
        invoer = _invoer(E_BRON)
        score = bs.scoor(_v("bij storing")(invoer), invoer, ORAKEL_E)
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["m_d_telt"], oordeel["handmatig"]) == (
            "niet_geslaagd",
            False,
            [],
        )

    def test_scorestatus_stuurt_het_runoordeel_niet(self):
        """Ook een score die 'behouden' zou claimen, geeft geen automatisch succes."""
        invoer = _invoer(E_BRON)
        score = bs.scoor(_v("bij storing")(invoer), invoer, ORAKEL_E)
        for status in ("behouden", "ontkend", "weggevallen", "iets anders"):
            nep = {**score, "voorwaarde_status": status, "voorwaarde_behouden": True}
            oordeel = bs.runoordeel(nep, ORAKEL_E)
            assert (oordeel["categorie"], oordeel["m_d_telt"]) == (H, False)
            assert oordeel["voorwaarde_behouden"] is False

    def test_zonder_interpretatie(self):
        oordeel = bs.runoordeel(None, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["voorwaarde_behouden"]) == (
            "geen_interpretatie",
            False,
        )

    @pytest.mark.parametrize(
        "naam",
        ["MARKERINGEN", "AANHEF", "VOORWAARDESTATUSSEN", "_markeringen", "_normaliseer",
         "_voorwaardestatus", "_controleer_formuleringen", "_teksten"],
    )  # fmt: skip
    def test_lexicale_regels_zijn_verwijderd(self, naam):
        assert not hasattr(bs, naam)

    @pytest.mark.parametrize(
        "veld",
        [{"voorwaarde_formuleringen": ["bij storing"]},
         {"voorwaarde_vereist_voor": ["error/buiten_bereik"]}],
    )  # fmt: skip
    def test_oude_orakelvelden_zijn_een_orakelfout(self, veld):
        with pytest.raises(bs.OrakelfoutError, match="velden"):
            bs.controleer_orakel({**ORAKEL_E, **veld}, _invoer(E_BRON))

    def test_geregistreerd_orakel_is_geldig(self):
        bs.controleer_orakel(ORAKEL_E, _invoer(E_BRON))


class TestProefMetE:
    @pytest.mark.parametrize(("naam", "maak"), _WACHT, ids=[n for n, _ in _WACHT])
    def test_negen_goed_plus_drie_e_wacht_op_chris(self, naam, maak):
        uit = bs.proefoordeel(_a_runs(9) + _e_runs([maak] * 3))
        assert uit["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert (uit["m_d_juist"], uit["e_voorwaarde_behouden"]) == (9, [0, 3])
        assert [h["redenen"] for h in uit["handmatig_beoordelen"]] == [
            [bs.HANDMATIG_E]
        ] * 3

    @pytest.mark.parametrize(("naam", "maak", "categorie"), E_VOORBEELDEN, ids=_IDS)
    def test_nooit_12_van_12_automatisch(self, naam, maak, categorie):
        uit = bs.proefoordeel(_a_runs(9) + _e_runs([maak] * 3))
        assert uit["oordeel"] != "geslaagd"
        assert uit["m_d_juist"] == 9
        assert uit["e_voorwaarde_behouden"] == [0, 3]

    def test_e_met_m_d_fout_geeft_tussengebied_zonder_wachten(self):
        uit = bs.proefoordeel(_a_runs(9) + _e_runs([_m("storing is optioneel")] * 3))
        assert uit["oordeel"] == "tussengebied"
        assert uit["handmatig_beoordelen"] == []


# --- eindoordeel: proefoordeel + oordeelbestand van Chris (aanvulling v4) ---------------------


def _oordelen(runs, statussen, **over):
    e_runs = [r for r in runs if r["voorwaarde_behouden"] is not None]
    return {
        "schema": bs.E_OORDEELSCHEMA,
        "oordelen": [
            {"run": r["sleutel"], "e_uitvoer_sha256": r["e_uitvoer_sha256"],
             "status": s, "beoordelaar": "Chris Lehnen", "datum": "2026-09-30", **over}
            for r, s in zip(e_runs, statussen, strict=True)
        ],
    }  # fmt: skip


def _niet_e_runs() -> list[dict]:
    """A, C en D × herhaling 1–3 (aanvulling v5: de sleutels van de echte proef),
    elk met het geslaagde runoordeel van A."""
    (a,) = _a_runs(1)
    return [
        {**a, "sleutel": f"interpretatie|{n}|{h}"} for n in "ACD" for h in (1, 2, 3)
    ]


def _proef(*makers):
    return _niet_e_runs() + _e_runs(makers or [_v("bij storing")] * 3)


class TestEindoordeel:
    def test_drie_keer_behouden_is_geslaagd(self):
        runs = _proef()
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden"] * 3))
        assert uit["oordeel"] == "geslaagd"
        assert (uit["m_d_juist"], uit["e_voorwaarde_behouden"]) == (12, [3, 3])
        assert uit["handmatig_beoordelen"] == []
        assert [e["status"] for e in uit["e_oordelen"]] == ["behouden"] * 3
        assert uit["regel"] == bs.EINDREGEL

    def test_een_ontkend_is_niet_geslaagd(self):
        runs = _proef()
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden", "ontkend", "behouden"]))
        assert uit["oordeel"] != "geslaagd"
        assert uit["e_voorwaarde_behouden"] == [2, 3]
        assert uit["categorieen"]["niet_geslaagd"] == 1

    def test_een_weggevallen_is_kritiek_en_afgekeurd(self):
        runs = _proef()
        uit = bs.eindoordeel(
            runs, _oordelen(runs, ["behouden", "behouden", "weggevallen"])
        )
        assert uit["oordeel"] == "afgekeurd"
        assert uit["kritiek"] == [{"sleutel": "interpretatie|E|3",
                                   "redenen": [bs.KRITIEK_WEGGEVALLEN]}]  # fmt: skip

    def test_codex_combinatie_met_drie_keer_behouden_slaagt_alleen_door_chris(self):
        """Het oordeel ligt bij Chris: de scorer beslist niet, ook niet 'nee'."""
        maak = _v("bij storing", "deze voorwaarde is optioneel")
        runs = _proef(maak, maak, maak)
        assert bs.proefoordeel(runs)["oordeel"] == "wacht_op_handmatige_beoordeling"
        uit = bs.eindoordeel(runs, _oordelen(runs, ["ontkend"] * 3))
        assert uit["oordeel"] != "geslaagd"

    def test_m_d_fout_blijft_niet_geslaagd_ook_bij_behouden(self):
        runs = _proef(_v("bij storing"), _v("bij storing"), _m("alleen bij storing"))
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden"] * 3))
        assert uit["oordeel"] != "geslaagd"
        assert uit["m_d_juist"] == 11
        assert uit["e_voorwaarde_behouden"] == [2, 3]

    @pytest.mark.parametrize("status", ["ontkend", "weggevallen"])
    def test_m_d_fout_met_ontkend_of_weggevallen_is_kritiek(self, status):
        """C2 blijft gelden, nu op het menselijke oordeel: ontkend is kritiek tenzij
        error/buiten_bereik; weggevallen altijd."""
        runs = _proef(_v("bij storing"), _v("bij storing"), _m("storing is optioneel"))
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden", "behouden", status]))
        assert uit["oordeel"] == "afgekeurd"

    def test_automatische_kritiek_blijft(self):
        runs = _proef()
        runs[0] = {
            **runs[0],
            "categorie": "kritiek",
            "kritiek": ["pass/fail bij M-b onwaar"],
        }
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden"] * 3))
        assert uit["oordeel"] == "afgekeurd"

    def test_invoer_wordt_niet_gewijzigd(self):
        runs = _proef()
        kopie = copy.deepcopy(runs)
        bs.eindoordeel(runs, _oordelen(runs, ["behouden"] * 3))
        assert runs == kopie

    def test_e_zonder_uitvoer_heeft_geen_oordeel_nodig(self):
        runs = _proef()
        runs[-1] = {"sleutel": "interpretatie|E|3", **bs.runoordeel(None, ORAKEL_E),
                    "e_uitvoer_sha256": None}  # fmt: skip
        uit = bs.eindoordeel(runs, _oordelen(runs[:-1], ["behouden"] * 2))
        assert uit["oordeel"] != "geslaagd"
        assert uit["e_voorwaarde_behouden"] == [2, 3]

    def test_ontbrekend_oordeel_geweigerd(self):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        del data["oordelen"][1]
        with pytest.raises(bs.OordeelfoutError, match="ontbreekt"):
            bs.eindoordeel(runs, data)

    def test_dubbel_oordeel_geweigerd(self):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        data["oordelen"].append(dict(data["oordelen"][0]))
        with pytest.raises(bs.OordeelfoutError, match="dubbel"):
            bs.eindoordeel(runs, data)

    @pytest.mark.parametrize("run", ["interpretatie|E|4", "interpretatie|A|0"])
    def test_onbekende_run_geweigerd(self, run):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        data["oordelen"].append({**data["oordelen"][0], "run": run})
        with pytest.raises(bs.OordeelfoutError, match="onbekende run"):
            bs.eindoordeel(runs, data)

    def test_afwijkende_hash_geweigerd(self):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        data["oordelen"][2]["e_uitvoer_sha256"] = "0" * 64
        with pytest.raises(bs.OordeelfoutError, match="sha256 wijkt af"):
            bs.eindoordeel(runs, data)

    @pytest.mark.parametrize(
        ("over", "melding"),
        [({"status": "misschien"}, "status"),
         ({"status": "handmatig_beoordelen"}, "status"),
         ({"beoordelaar": ""}, "beoordelaar"),
         ({"beoordelaar": 3}, "beoordelaar"),
         ({"datum": "30-09-2026"}, "datum"),
         ({"datum": "2026-02-30"}, "datum"),
         ({"extra": 1}, "velden")],
    )  # fmt: skip
    def test_ongeldig_oordeel_geweigerd(self, over, melding):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        data["oordelen"][0].update(over)
        with pytest.raises(bs.OordeelfoutError, match=melding):
            bs.eindoordeel(runs, data)

    @pytest.mark.parametrize(
        "data",
        [{}, [], {"schema": "anders", "oordelen": []},
         {"schema": "def768-ess05-e-oordeel/1", "oordelen": "x"},
         {"schema": "def768-ess05-e-oordeel/1", "oordelen": [], "extra": 1}],
    )  # fmt: skip
    def test_ongeldig_oordeelbestand_geweigerd(self, data):
        with pytest.raises(bs.OordeelfoutError):
            bs.eindoordeel(_proef(), data)

    def test_ontbrekend_veld_geweigerd(self):
        runs = _proef()
        data = _oordelen(runs, ["behouden"] * 3)
        del data["oordelen"][0]["beoordelaar"]
        with pytest.raises(bs.OordeelfoutError, match="velden"):
            bs.eindoordeel(runs, data)


PROEF_E = ("interpretatie|E|1", "interpretatie|E|2", "interpretatie|E|3")


def _leeg_oordeel() -> dict:
    return {"schema": bs.E_OORDEELSCHEMA, "oordelen": []}


class TestRunverzameling:
    """Codex-hercontrole v4, B5 en B6 (aanvulling v5): `eindoordeel` weigert
    tenzij de runs precies A/C/D/E × herhaling 1–3 zijn, uniek en met E-metadata
    die bij de E-sleutel past; E volgt uit de vaste proefstructuur."""

    def test_proefstructuur(self):
        assert (
            tuple(f"interpretatie|{n}|{h}" for n in "ACDE" for h in (1, 2, 3))
            == bs.PROEFSLEUTELS
        )
        assert bs.E_SLEUTELS == PROEF_E
        assert len(bs.PROEFSLEUTELS) == bs.RUNS_VERWACHT

    def test_codex_e1_driemaal_met_een_oordeel_geweigerd(self):
        """B5: 9 A/C/D + E1 driemaal, één oordeel voor E1 gaf geslaagd, M-d 12, E 3/3."""
        (e1,) = _e_runs([_v("bij storing")])
        runs = _niet_e_runs() + [e1, dict(e1), dict(e1)]
        data = _oordelen([e1], ["behouden"])
        with pytest.raises(bs.OordeelfoutError, match="dubbele run"):
            bs.eindoordeel(runs, data)

    def test_codex_twaalf_niet_e_runs_met_leeg_oordeel_geweigerd(self):
        """B5: twaalf niet-E-runs plus een leeg oordeelbestand gaf geslaagd."""
        with pytest.raises(bs.OordeelfoutError, match="runs"):
            bs.eindoordeel(_a_runs(12), _leeg_oordeel())

    def test_twaalf_niet_e_runs_onder_de_juiste_sleutels_geweigerd(self):
        (a,) = _a_runs(1)
        runs = [{**a, "sleutel": s} for s in bs.PROEFSLEUTELS]
        with pytest.raises(bs.OordeelfoutError, match="strijdig"):
            bs.eindoordeel(runs, _leeg_oordeel())

    @pytest.mark.parametrize(
        "over",
        [{"voorwaarde_behouden": None, "voorwaarde_status": None, "categorie": "geslaagd",
          "m_d_telt": True, "handmatig": []},
         {"categorie": "geslaagd", "m_d_telt": True, "handmatig": []},
         {"voorwaarde_behouden": True},
         {"e_uitvoer_sha256": None}],
        ids=["als-niet-e", "geslaagd", "behouden", "zonder-hash"],
    )  # fmt: skip
    def test_codex_gewijzigde_e_metadata_geweigerd(self, over):
        """B6 (directe route): E-metadata die niet bij een E-run past."""
        runs = _proef()
        runs[10] = {**runs[10], **over}
        data = _oordelen(runs[:10] + runs[11:], ["behouden"] * 2)
        with pytest.raises(bs.OordeelfoutError, match="strijdig"):
            bs.eindoordeel(runs, data)
        with pytest.raises(bs.OordeelfoutError, match="strijdig"):
            bs.eindoordeel(runs, _leeg_oordeel())

    @pytest.mark.parametrize(
        "over",
        [{"voorwaarde_behouden": False}, {"voorwaarde_status": "handmatig_beoordelen"},
         {"e_uitvoer_sha256": "a" * 64}, {"handmatig": [bs.HANDMATIG_E]}],
    )  # fmt: skip
    def test_e_metadata_op_een_niet_e_run_geweigerd(self, over):
        runs = _proef()
        runs[4] = {**runs[4], **over}
        with pytest.raises(bs.OordeelfoutError, match="strijdig"):
            bs.eindoordeel(runs, _oordelen(runs[9:], ["behouden"] * 3))

    def test_ontbrekende_run_geweigerd(self):
        runs = _proef()
        del runs[4]
        with pytest.raises(bs.OordeelfoutError, match="ontbrekende runs"):
            bs.eindoordeel(runs, _oordelen(runs[8:], ["behouden"] * 3))

    @pytest.mark.parametrize("sleutel", ["interpretatie|E|4", "interpretatie|B|1",
                                         "bewijsregels|A|1"])  # fmt: skip
    def test_onbekende_run_geweigerd(self, sleutel):
        runs = _proef()
        runs.append({**runs[0], "sleutel": sleutel})
        with pytest.raises(bs.OordeelfoutError, match="onbekende runs"):
            bs.eindoordeel(runs, _oordelen(runs[9:12], ["behouden"] * 3))

    def test_e_vervangt_een_andere_run_geweigerd(self):
        """Elf echte runs plus E1 onder de sleutel van D3: strijdig."""
        runs = _proef()
        runs[8] = {**runs[9], "sleutel": "interpretatie|D|3"}
        with pytest.raises(bs.OordeelfoutError, match="strijdig"):
            bs.eindoordeel(runs, _oordelen(runs[9:], ["behouden"] * 3))

    @pytest.mark.parametrize("runs", [None, "x", {}, [1], [{"sleutel": 3}]])
    def test_ongeldige_runs_geweigerd(self, runs):
        with pytest.raises(bs.OordeelfoutError, match="runs"):
            bs.eindoordeel(runs, _leeg_oordeel())

    def test_geslaagd_vereist_drie_verschillende_beoordeelde_e_runs(self):
        runs = _proef()
        uit = bs.eindoordeel(runs, _oordelen(runs, ["behouden"] * 3))
        assert uit["oordeel"] == "geslaagd"
        assert [e["run"] for e in uit["e_oordelen"]] == list(bs.E_SLEUTELS)
        assert [e["e_uitvoer_sha256"] for e in uit["e_oordelen"]] == [
            r["e_uitvoer_sha256"] for r in runs[9:]
        ]


# --- orakelstructuur vereist/toegestaan (Codex-review B3/B4, aanvulling C3) -----------------


def _d(invoer, doel_k2, verhuur_k2):
    """D met eigen citaten (prefixen) voor K2 bij doel en bij verhuur."""
    ruw = _d_juist(invoer, doel_k2)
    (k2,) = [a for a in ruw["antwoorden"]
             if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"]  # fmt: skip
    k2["citaten"] = [_u(invoer, p) for p in verhuur_k2]
    return ruw


def _kosteloos(score, onderwerp):
    (feit,) = [f for f in score["feiten"]
               if (f["kernwoord"], f["onderwerp"]) == ("kosteloos", onderwerp)]  # fmt: skip
    return feit


class TestOrakelstructuur:
    def test_b3_d_alleen_buurbeschrijving_bij_verhuur_niet_geslaagd(self):
        """Codex-reproductie B3: de buurbeschrijving noemt geen vergoeding."""
        invoer = _invoer(D_BRON)
        score = bs.scoor(
            _d(invoer, ("Voor uitleen betaalt",), (BUUR,)), invoer, ORAKEL_D
        )
        assert score["m_d"]["uitkomst"] == "pass"
        assert _kosteloos(score, "verhuur")["draagt"] is False
        assert score["m_b_dragend_ok"] is False
        oordeel = bs.runoordeel(score, ORAKEL_D)
        assert oordeel["categorie"] != "geslaagd"
        assert oordeel["kritiek"] == ["pass/fail bij M-b onwaar"]

    def test_b3_d_verhuur_betaalzin_met_context_geslaagd(self):
        invoer = _invoer(D_BRON)
        ruw = _d(invoer, ("Voor uitleen betaalt",),
                 ("Verhuur:", "Voor verhuur betaalt", BUUR))  # fmt: skip
        score = bs.scoor(ruw, invoer, ORAKEL_D)
        assert _kosteloos(score, "verhuur")["draagt"] is True
        assert bs.runoordeel(score, ORAKEL_D)["categorie"] == "geslaagd"

    def test_b4_d_uitleenzin_plus_betaalzin_geslaagd(self):
        """Codex-reproductie B4: de Uitleen-zin ondersteunt 'de medewerker'."""
        invoer = _invoer(D_BRON)
        ruw = _d(
            invoer, ("Uitleen:", "Voor uitleen betaalt"), ("Voor verhuur betaalt",)
        )
        score = bs.scoor(ruw, invoer, ORAKEL_D)
        assert score["m_d"]["uitkomst"] == "pass"
        assert _kosteloos(score, "doel")["draagt"] is True
        assert score["m_b_dragend_ok"] is True
        assert bs.runoordeel(score, ORAKEL_D)["categorie"] == "geslaagd"

    def test_b4_d_blind_hergebruik_niet_geslaagd(self):
        """Alleen toegestane context, geen vereiste eenheid: M-b onwaar."""
        invoer = _invoer(D_BRON)
        score = bs.scoor(
            _d(invoer, ("Uitleen:",), ("Voor verhuur betaalt",)), invoer, ORAKEL_D
        )
        assert _kosteloos(score, "doel")["draagt"] is False
        oordeel = bs.runoordeel(score, ORAKEL_D)
        assert oordeel["categorie"] == "kritiek"

    def test_b4_d_alleen_context_bij_verhuur_niet_geslaagd(self):
        invoer = _invoer(D_BRON)
        ruw = _d(invoer, ("Voor uitleen betaalt",), ("Verhuur:", BUUR))
        assert bs.scoor(ruw, invoer, ORAKEL_D)["m_b_dragend_ok"] is False

    def test_b4_eenheid_buiten_vereist_en_toegestaan_draagt_niet(self):
        invoer = _invoer(D_BRON)
        ruw = _d(invoer, ("Voor uitleen betaalt", "Lokale testwerkinstructie"),
                 ("Voor verhuur betaalt",))  # fmt: skip
        assert _kosteloos(bs.scoor(ruw, invoer, ORAKEL_D), "doel")["draagt"] is False

    @pytest.mark.parametrize("prefixen", [("Verhuur:",), (BUUR,), ("Verhuur:", BUUR)])
    def test_a_tijdelijk_verhuur_elk_vereist_prefix_draagt(self, prefixen):
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k1,) = [a for a in ruw["antwoorden"]
                 if a["kenmerk_id"] == "K1" and a["onderwerp"] != "doel"]  # fmt: skip
        k1["citaten"] = [_u(invoer, p) for p in prefixen]
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        (feit,) = [f for f in score["feiten"]
                   if (f["kernwoord"], f["onderwerp"]) == ("tijdelijk", "verhuur")]  # fmt: skip
        assert feit["draagt"] is True

    @pytest.mark.parametrize(
        ("wijzig", "melding"),
        [
            (lambda v: v.update(eenheden=["Uitleen:"]), "velden"),
            (lambda v: v.pop("vereist"), "velden"),
            (lambda v: v.pop("toegestaan"), "velden"),
            (lambda v: v.update(vereist="Uitleen:"), "vereist"),
            (lambda v: v.update(toegestaan=[1]), "toegestaan"),
            (lambda v: v.update(toegestaan=["Voor uitleen betaalt"]), "zowel"),
            (lambda v: v.update(toestand="bevestigd"), "toestand"),
            (lambda v: v.update(f7="ontkend"), "f7"),
        ],
    )
    def test_controleer_orakel_weigert_een_onjuiste_feitstructuur(
        self, wijzig, melding
    ):
        orakel = copy.deepcopy(ORAKEL_D)
        wijzig(orakel["kenmerken"]["kosteloos"]["doel"])
        with pytest.raises(bs.OrakelfoutError, match=melding):
            bs.controleer_orakel(orakel, _invoer(D_BRON))

    def test_controleer_orakel_accepteert_de_vier_orakels(self):
        for orakel, bron in ((ORAKEL_A, None), (ORAKEL_D, D_BRON), (ORAKEL_E, E_BRON)):
            bs.controleer_orakel(orakel, _invoer(bron) if bron else _invoer())


# --- F7 apart van M-b/M-c ---------------------------------------------------------------------


class TestF7:
    def test_f7_telt_niet_als_bewijs_of_toestandsfout_zonder_f7(self):
        """Deel C: F7 is niet geslaagd en niet kritiek; de maten zonder F7 blijven waar."""
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"
        ]
        k2.update(toestand="ontkend", citaten=[_u(invoer, BUUR)])
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_b_dragend_ok"] is False
        assert score["m_c_dragend_ok"] is False
        assert score["m_b_dragend_ok_zonder_f7"] is True
        assert score["m_c_dragend_ok_zonder_f7"] is True

    def test_zonder_f7_gelijk_als_er_geen_f7_is(self):
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"
        ]
        k2["citaten"] = [_u(invoer, "Lokale testwerkinstructie")]
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["f7_afwijkingen"] == []
        assert score["m_b_dragend_ok_zonder_f7"] is False
        assert score["m_c_dragend_ok_zonder_f7"] is True

    def test_andere_verkeerde_toestand_is_geen_f7(self):
        invoer = _invoer()
        ruw = _a_juist(invoer)
        (k2,) = [
            a
            for a in ruw["antwoorden"]
            if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"
        ]
        k2.update(toestand="bevestigd", citaten=[_u(invoer, "Verhuur:")])
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["f7_afwijkingen"] == []
        assert score["m_c_dragend_ok_zonder_f7"] is False


class TestKenmerkherkenning:
    def test_dubbelzinnig_kernwoord_draagt_niet(self):
        """Twee kernkenmerken met hetzelfde kernwoord: geen toewijzing, dus onwaar."""
        invoer = _invoer()
        ruw = _a_juist(invoer)
        ruw["kern"]["kenmerken"][0]["citaat"] = "tijdelijk en kosteloos"
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_b_dragend_ok"] is False
        assert score["m_c_dragend_ok"] is False

    def test_nummering_van_het_model_maakt_niet_uit(self):
        invoer = _invoer()
        ruw = _a_juist(invoer)
        omnummer = {"K1": "K4", "K2": "K3", "K3": "K2", "K4": "K1"}
        for k in ruw["kern"]["kenmerken"]:
            k["id"] = omnummer[k["id"]]
        for a in ruw["antwoorden"]:
            a["kenmerk_id"] = omnummer[a["kenmerk_id"]]
        score = bs.scoor(ruw, invoer, ORAKEL_A)
        assert score["m_b_dragend_ok"] is True
        assert score["m_c_dragend_ok"] is True
        assert score["m_d"]["ok"] is True


@pytest.mark.skipif(not R17_INVOER.is_file(), reason="git-ignored R17-invoer ontbreekt")
class TestBron:
    def test_inline_geval_is_exact_r17_item_a(self):
        data = json.loads(R17_INVOER.read_text(encoding="utf-8"))
        (a,) = [i for i in data["items"] if i["id"] == "A"]
        assert _geval() == a["geval"]
