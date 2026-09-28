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


# --- voorwaarde: routes waarlangs zij behouden blijft of wegvalt ------------------------------


class TestVoorwaarde:
    def test_als_betekeniskenmerk_bevestigd_is_handmatig(self):
        """Aanvulling v2 (B2-rest): het M-kenmerkpad geeft nooit automatisch behouden."""
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
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["m_d"]["ok"] is False

    def test_als_kenmerknaam_bevestigd_is_handmatig(self):
        """Ook de frase in het kenmerklabel geeft geen automatisch behouden (v2)."""
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
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "handmatig_beoordelen"

    def test_m_kenmerk_niet_bevestigd_is_handmatig(self):
        """Aanvulling C2: de frase staat er, maar niet eenduidig als (a) of (b)."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_kern=[{"id": "M1", "kenmerk": "aanleiding", "waarde": "storing"}],
        )
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "handmatig_beoordelen"

    def test_in_buiten_bereik_is_handmatig(self):
        """Aanvulling C2: alleen buiten bereik is geen (a) of (b) → handmatig
        beoordelen; geen automatisch succes en niet automatisch kritiek."""
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
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "handmatig_beoordelen"

    def test_opgeheven_door_een_onvoorwaardelijk_antwoord_is_handmatig(self):
        """Naast een onvoorwaardelijk gelijk antwoord voegt de voorwaarde niets toe
        (zoals `_onverwerkte_voorwaarden`): niet eenduidig (a) → handmatig."""
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
        assert score["voorwaarde_status"] == "handmatig_beoordelen"

    def test_hoofdletterongevoelig(self):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["Bij STORING"]))
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_behouden"] is True


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


class TestVoorwaardestatus:
    """Codex-review deel B, bevinding B2 (aanvulling C2): geen succes op een woordtreffer."""

    def test_codex_reproductie_ook_zonder_storing_slaagt_niet(self):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, "ook zonder storing"), invoer, ORAKEL_E)
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["voorwaarde_behouden"] is False
        assert score["voorwaarde_status"] == "ontkend"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert oordeel["categorie"] == "kritiek"
        assert oordeel["kritiek"] == ["E: voorwaarde ontkend of opgeheven"]
        assert oordeel["m_d_telt"] is False

    def test_correcte_voorwaarde_in_het_doel_slaagt(self):
        """Regel 1 (v2): voorwaardelijke aanhef in `voorwaarden` + error/buiten_bereik."""
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        assert score["voorwaarde_status"] == "behouden"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["m_d_telt"]) == ("geslaagd", True)

    def test_weggevallen_voorwaarde_is_kritiek(self):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e(invoer, ("bevestigd", ["Uitleen:"])), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "weggevallen"
        assert score["voorwaarde_vermeldingen"] == []
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert oordeel["categorie"] == "kritiek"
        assert oordeel["kritiek"] == ["E: voorwaarde weggevallen"]

    def test_onduidelijke_formulering_is_handmatig_beoordelen(self):
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"]),
            buiten_bereik=[{"citaat": "bij storing", "reden": "voorwaardelijk"}],
        )
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert oordeel["categorie"] == "handmatig_beoordelen"
        assert oordeel["kritiek"] == []
        assert oordeel["m_d_telt"] is False
        assert oordeel["handmatig"] == ["E: voorwaarde niet eenduidig behouden"]

    @pytest.mark.parametrize(
        "voorwaarde",
        [
            "zonder storing",
            "niet bij storing",
            "geen storing vereist",
            "ongeacht storing",
            "ook zonder storing",
            "ook buiten storing",
            "altijd, ook bij storing",
            "ongeacht of er een storing is",
            "Ook ZONDER storing",
        ],
    )
    def test_markering_in_het_doel_is_ontkend(self, voorwaarde):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], [voorwaarde]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "ontkend"
        assert score["voorwaarde_behouden"] is False

    @pytest.mark.parametrize(
        "waarde", ["ook zonder storing", "niet bij storing", "altijd, ongeacht storing"]
    )
    def test_markering_in_een_m_kenmerk_is_ontkend(self, waarde):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, waarde), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "ontkend"

    def test_markering_wint_van_een_correcte_vermelding(self):
        """Eén ontkennende vermelding in (a) of (b) maakt de voorwaarde niet behouden."""
        invoer = _invoer(E_BRON)
        ruw = _e_met_m(invoer, "ook zonder storing")
        (k2,) = [a for a in ruw["antwoorden"]
                 if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"]  # fmt: skip
        k2["voorwaarden"] = ["bij storing"]
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_status"] == "ontkend"

    def test_markering_elders_ontkent_niet(self):
        """Een markering in een buiten-bereik-reden ontkent een correcte (a) niet."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer,
            ("bevestigd", ["Uitleen:"], ["bij storing"]),
            buiten_bereik=[
                {
                    "citaat": "bij storing",
                    "reden": "wat zonder storing geldt, staat niet in de bron",
                }
            ],
        )
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "behouden"
        assert score["voorwaarde_vermeldingen"][-1]["markering"] == ["niet", "zonder"]
        assert [v["plek"] for v in score["voorwaarde_vermeldingen"]] == [
            "doelvoorwaarde",
            "elders",
            "elders",
        ]

    def test_conservatief_niet_daarbuiten_telt_als_ontkend(self):
        """Gedocumenteerd risico (aanvulling C2): geen onterecht succes, wel mogelijk
        een onterechte kritieke run; de inhoudsreviewer ziet de vermelding."""
        invoer = _invoer(E_BRON)
        ruw = _e(
            invoer, ("bevestigd", ["Uitleen:"], ["alleen bij storing, niet daarbuiten"])
        )
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_status"] == "ontkend"

    def test_woorden_die_een_markering_bevatten_tellen_niet(self):
        """'nietig' of 'geenszins' is geen losse markering; alleen hele woorden tellen."""
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["bij storing (altijdgeldig)"]))
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_status"] == "behouden"

    def test_ontkend_met_buiten_bereik_is_niet_kritiek_en_telt_niet(self):
        md = {"uitkomst": "error", "fout": "buiten_bereik",
              "verwacht": ORAKEL_E["uitkomst"], "ok": True}  # fmt: skip
        score = {**bs.scoor(None, _invoer(E_BRON), ORAKEL_E), "m_d": md,
                 "voorwaarde_status": "ontkend", "voorwaarde_behouden": False}  # fmt: skip
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["kritiek"], oordeel["m_d_telt"]) == (
            "niet_geslaagd",
            [],
            False,
        )

    def test_vermeldingen_in_het_record(self):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, "ook zonder storing"), invoer, ORAKEL_E)
        assert score["voorwaarde_vermeldingen"] == [
            {"pad": "buiten_kern[0].waarde", "tekst": "ook zonder storing",
             "plek": "m_kenmerk", "markering": ["ook zonder", "zonder"]}
        ]  # fmt: skip
        json.dumps(score)


# --- B2-rest (Codex-hercontrole, aanvulling v2): alleen regel 1 geeft behouden --------------

#: De drie tegenvoorbeelden uit de Codex-hercontrole.
CODEX_REST = [
    "onafhankelijk van storing",
    "storing is irrelevant",
    "storing is optioneel",
]
#: De markeringen van aanvulling v1, zonder de drie die v2 toevoegt.
MARKERINGEN_V1 = tuple(
    m for m in bs.MARKERINGEN if m not in ("onafhankelijk", "irrelevant", "optioneel")
)
AANHEFFEN = ["bij", "alleen bij", "uitsluitend bij", "in geval van", "als", "wanneer",
             "indien", "mits"]  # fmt: skip


def _a_runs(n: int) -> list[dict]:
    """n echte, geslaagde niet-E-runs (A juist, gescoord)."""
    invoer = _invoer()
    oordeel = bs.runoordeel(bs.scoor(_a_juist(invoer), invoer, ORAKEL_A), ORAKEL_A)
    assert oordeel["categorie"] == "geslaagd"
    return [{"sleutel": f"interpretatie|A|{i}", **oordeel} for i in range(n)]


def _e_runs(ruwen) -> list[dict]:
    invoer = _invoer(E_BRON)
    return [
        {"sleutel": f"interpretatie|E|{i}",
         **bs.runoordeel(bs.scoor(ruw(invoer), invoer, ORAKEL_E), ORAKEL_E)}
        for i, ruw in enumerate(ruwen, start=1)
    ]  # fmt: skip


class TestVoorwaardeRest:
    @pytest.mark.parametrize("waarde", CODEX_REST)
    def test_codex_voorbeelden_in_een_m_kenmerk_slagen_niet(self, waarde):
        """Regel 2: met de markeringen van v2 zijn ze ontkend (kritiek); nooit geslaagd."""
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, waarde), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "ontkend"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert oordeel["categorie"] != "geslaagd"
        assert oordeel["m_d_telt"] is False

    @pytest.mark.parametrize("waarde", CODEX_REST)
    def test_structureel_ook_zonder_de_nieuwe_woorden_nooit_behouden(
        self, waarde, monkeypatch
    ):
        """De fix hangt niet af van de woordenlijst: met de v1-lijst is het
        M-kenmerkpad handmatig_beoordelen, niet geslaagd."""
        monkeypatch.setattr(bs, "MARKERINGEN", MARKERINGEN_V1)
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, waarde), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["m_d_telt"]) == (
            "handmatig_beoordelen",
            False,
        )

    @pytest.mark.parametrize(
        "waarde",
        ["alleen bij storing", "bij storing", "storing", "los van storing",
         "storing doet er weinig toe"],
    )  # fmt: skip
    def test_m_kenmerk_zonder_markering_is_handmatig(self, waarde):
        invoer = _invoer(E_BRON)
        score = bs.scoor(_e_met_m(invoer, waarde), invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        assert bs.runoordeel(score, ORAKEL_E)["categorie"] == "handmatig_beoordelen"

    def test_m_kenmerk_naast_een_juiste_doelvoorwaarde_is_handmatig(self):
        """Conservatief: twee routes tegelijk is twijfel, dus handmatig."""
        invoer = _invoer(E_BRON)
        ruw = _e_met_m(invoer, "bij storing")
        (k2,) = [a for a in ruw["antwoorden"]
                 if a["kenmerk_id"] == "K2" and a["onderwerp"] == "doel"]  # fmt: skip
        k2["voorwaarden"] = ["bij storing"]
        assert (
            bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_status"]
            == "handmatig_beoordelen"
        )

    @pytest.mark.parametrize("aanhef", AANHEFFEN)
    def test_elke_voorwaardelijke_aanhef_in_voorwaarden_is_behouden(self, aanhef):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], [f"  {aanhef.upper()} storing"]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        assert score["voorwaarde_status"] == "behouden"
        assert bs.runoordeel(score, ORAKEL_E)["categorie"] == "geslaagd"

    @pytest.mark.parametrize(
        "voorwaarde",
        ["storing", "tijdens een storing", "de storing", "storing aanwezig"],
    )
    def test_frase_zonder_voorwaardelijke_aanhef_is_handmatig(self, voorwaarde):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], [voorwaarde]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["m_d_telt"], oordeel["kritiek"]) == (
            "handmatig_beoordelen",
            False,
            [],
        )

    @pytest.mark.parametrize("voorwaarde", CODEX_REST)
    def test_codex_voorbeelden_in_voorwaarden_zijn_ontkend(self, voorwaarde):
        """Ontkend; bij error/buiten_bereik niet kritiek (regel C2 'zoals nu'), wel
        niet geslaagd en M-d telt niet."""
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], [voorwaarde]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "ontkend"
        assert (score["m_d"]["uitkomst"], score["m_d"]["fout"]) == (
            "error",
            "buiten_bereik",
        )
        oordeel = bs.runoordeel(score, ORAKEL_E)
        assert (oordeel["categorie"], oordeel["m_d_telt"]) == ("niet_geslaagd", False)

    def test_aanhef_met_markering_is_ontkend(self):
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["als er geen storing is"]))
        assert bs.scoor(ruw, invoer, ORAKEL_E)["voorwaarde_status"] == "ontkend"

    @pytest.mark.parametrize(
        "uitkomst", [("review_required", None), ("pass", None), ("error", "citaat")]
    )
    def test_behouden_alleen_met_de_onverwerkte_doeleis(self, uitkomst, monkeypatch):
        """Regel 1: zonder error/buiten_bereik is een juiste aanhef twijfel → handmatig."""
        monkeypatch.setattr(bs, "_uitkomst", lambda ruw, invoer: uitkomst)
        invoer = _invoer(E_BRON)
        ruw = _e(invoer, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, invoer, ORAKEL_E)
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        assert bs.runoordeel(score, ORAKEL_E)["categorie"] == "handmatig_beoordelen"

    def test_proefoordeel_drie_codex_e_runs_niet_geslaagd(self):
        """Hercontrole: drie E-runs met 'onafhankelijk van storing' gaven 12/12 geslaagd."""
        runs = _a_runs(9) + _e_runs([lambda i: _e_met_m(i, CODEX_REST[0])] * 3)
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] != "geslaagd"
        assert uit["oordeel"] == "afgekeurd"
        assert uit["e_voorwaarde_behouden"] == [0, 3]

    def test_proefoordeel_drie_handmatige_e_runs_niet_geslaagd(self, monkeypatch):
        """Ook zonder de nieuwe woorden (v1-lijst): handmatig, dus nooit geslaagd."""
        monkeypatch.setattr(bs, "MARKERINGEN", MARKERINGEN_V1)
        runs = _a_runs(9) + _e_runs([lambda i, w=w: _e_met_m(i, w) for w in CODEX_REST])
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] == "wacht_op_handmatige_beoordeling"
        assert uit["m_d_juist"] == 9
        assert uit["e_voorwaarde_behouden"] == [0, 3]
        assert len(uit["handmatig_beoordelen"]) == 3

    def test_proefoordeel_drie_juiste_e_runs_geslaagd(self):
        runs = _a_runs(9) + _e_runs(
            [lambda i: _e(i, ("bevestigd", ["Uitleen:"], ["bij storing"]))] * 3
        )
        uit = bs.proefoordeel(runs)
        assert uit["oordeel"] == "geslaagd"
        assert uit["e_voorwaarde_behouden"] == [3, 3]


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
