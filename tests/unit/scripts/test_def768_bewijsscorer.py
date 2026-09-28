"""DEF-768 B1 — bewijsscorer M-a…M-d voor interpretatieproeven (alleen evaluatie).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B1:
de zeven plangevallen (A juist, A met de inleiding als bewijs, D blind
hergebruik, E met en zonder voorwaarde, onzin, F7). Aanvulling van de
opdracht: de scorer geeft ook bij ongeldige modeluitvoer (niet-dict
antwoorden, niet-lijst citaten, onbekende eenheid, …) nooit een exception.

A is exact het geval van R17-item A (H3, inline; gelijkheid met de git-ignored
R17-invoer in `TestBron`); D en E zijn SYNTHETISCH, GEEN
MODELUITVOER (bronteksten uit het plan). Alle interpretaties hier zijn
vooraf opgesteld, geen modeluitvoer. Geen netwerk.
"""

from __future__ import annotations

import copy
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

ORAKEL_A = {
    "kenmerken": {
        "tijdelijk": {
            "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
            "verhuur": {"toestand": ["bevestigd"], "eenheden": ["Verhuur:", BUUR]},
        },
        "kosteloos": {
            "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
            "verhuur": {"toestand": ["onbesproken"], "eenheden": [], "f7": ["ontkend"]},
        },
    },
    "dragend": ["kosteloos"],
    "uitkomst": ["review_required"],
}
ORAKEL_D = {
    "kenmerken": {
        "kosteloos": {
            "doel": {"toestand": ["bevestigd"], "eenheden": ["Voor uitleen betaalt"]},
            "verhuur": {
                "toestand": ["ontkend"],
                "eenheden": ["Voor verhuur betaalt", BUUR],
            },
        }
    },
    "dragend": ["kosteloos"],
    "uitkomst": ["pass"],
}
ORAKEL_E = {
    "kenmerken": {},
    "dragend": [],
    "voorwaarde": "storing",
    "uitkomst": ["error/buiten_bereik", "review_required"],
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

    def test_e_voorwaarde_behouden(self):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is True
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        assert score["m_d"]["ok"] is True

    def test_e_voorwaarde_weggevallen(self):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e(invoer, ("bevestigd", ["Uitleen:"])), invoer, ORAKEL_E)
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["m_d"]["ok"] is True
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


# --- voorwaarde: routes waarlangs zij behouden blijft of wegvalt ------------------------------


class TestVoorwaarde:
    def test_als_betekeniskenmerk_bevestigd(self):
        """Plan B2: de voorwaarde als M-kenmerk, in het doel bevestigd."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_kern=[
                {"id": "M1", "kenmerk": "aanleiding", "waarde": "bij storing"}
            ],
        )
        ruw["antwoorden"].append(
            {
                "kenmerk_id": "M1",
                "onderwerp": "doel",
                "toestand": "bevestigd",
                "voorwaarden": [],
                "context": "zaakcontext",
                "citaten": [_u(invoer, "Uitleen:")],
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
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is True
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["m_d"]["ok"] is True

    def test_als_kenmerknaam_bevestigd(self):
        """Afwijking van de plancode: de frase mag ook in het kenmerklabel staan."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_kern=[{"id": "M1", "kenmerk": "bij storing", "waarde": "ja"}],
        )
        ruw["antwoorden"].append(
            {
                "kenmerk_id": "M1",
                "onderwerp": "doel",
                "toestand": "bevestigd",
                "voorwaarden": [],
                "context": "zaakcontext",
                "citaten": [_u(invoer, "Uitleen:")],
            }
        )
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_behouden"] is True

    def test_m_kenmerk_niet_bevestigd_behoudt_niets(self):
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_kern=[{"id": "M1", "kenmerk": "aanleiding", "waarde": "storing"}],
        )
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_behouden"] is False

    def test_in_buiten_bereik(self):
        """Afwijking van de plancode: een voorwaarde die het model buiten bereik
        plaatst, is niet weggevallen (anders telt een juiste run als kritiek)."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_bereik=[
                {
                    "citaat": "bij storing",
                    "reden": "kosteloos alleen onder een voorwaarde",
                }
            ],
        )
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        assert score["voorwaarde_behouden"] is True

    def test_opgeheven_door_een_onvoorwaardelijk_antwoord(self):
        """Afwijking van de plancode: naast een onvoorwaardelijk gelijk antwoord voegt
        de voorwaarde niets toe (zoals `_onverwerkte_voorwaarden`): weggevallen."""
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"]))
        ruw["antwoorden"].append(
            {
                "kenmerk_id": "K2",
                "onderwerp": "doel",
                "toestand": "bevestigd",
                "voorwaarden": ["bij storing"],
                "context": "zaakcontext",
                "citaten": [_u(invoer, "Uitleen:")],
            }
        )
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["voorwaarde_behouden"] is False

    def test_hoofdletterongevoelig(self):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["Bij STORING"]))
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_behouden"] is True


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
