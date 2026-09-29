"""DEF-768 robuustheidsronde, punt 4 — eerlijke melding in de app (stubs, offline).

Besluit Chris 29-09: is de modeluitvoer inhoudelijk onbruikbaar (schema-,
citaat-, dekkings-, betekenis-, onderwerp- of geldigheidsfout in de
interpretatie, of een lokale controle die niet `supported` geeft), dan toont de
app REVIEW_REQUIRED met "De AI kon dit niet betrouwbaar automatisch
beoordelen; beoordeel handmatig." plus een korte reden, niet "Technisch
probleem". ERROR blijft voor echte technische storingen (netwerk, timeout,
providerweigering, transport, budget/teller). ESS-05 blijft zonder cijfer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from domain.ess05 import contract as ec
from domain.ess05.lokale_controle import CONTROLE_ITEM, LOKAAL_VERIFICATIESCHEMA
from services.validation import ess05_bewijsregel_service as bs
from tests.unit.validation.test_def768_bewijsregel_service import _SpyAI
from tests.unit.validation.test_def768_ess05_app_aansluiting import (
    BUUR_C,
    _buur,
    _spy,
    _valideer,
)
from ui.components.validation_view import _review_regels

pytestmark = [pytest.mark.unit]

ZIN = "De AI kon dit niet betrouwbaar automatisch beoordelen; beoordeel handmatig."
BUREN = [_buur(BUUR_C)]


class _ControleAntwoord(_SpyAI):
    """Interpretatie als de spy; elke controle krijgt een vast (ander) antwoord."""

    def __init__(self, interpretatie, *, controle_tekst=None, controle_fout=None):
        super().__init__(interpretatie)
        self.controle_tekst = controle_tekst
        self.controle_fout = controle_fout

    async def generate_definition(self, **kwargs):
        if kwargs["task_type"] == bs.Ess05BewijsregelService.TASK_TYPE:
            return await super().generate_definition(**kwargs)
        self.aanroepen.append(kwargs)
        if self.controle_fout is not None:
            raise self.controle_fout
        return SimpleNamespace(
            text=self.controle_tekst, model="spy-model", cached=False,
            tokens_used=10, metadata={"stop_reason": "end_turn"},
        )  # fmt: skip


def _ess05(run) -> dict:
    return run.resultaat["rule_results"]["ESS-05"]


def _spy_met(wijzig):
    ai = _spy("pass", BUREN)
    wijzig(ai.interpretatie)
    return ai


def _onbekende_eenheid(ruw):
    for a in ruw["antwoorden"]:
        if a["citaten"]:
            a["citaten"] = ["U99"]
            return


ONBRUIKBAAR = {
    "malformed_response": lambda: _SpyAI("geen json"),
    "schemafout": lambda: _spy_met(lambda r: r.pop("buurgroepen")),
    "citaatfout": lambda: _spy_met(_onbekende_eenheid),
    "kerndekking_onvolledig": lambda: _spy_met(lambda r: r["kern"]["kenmerken"].pop()),
    "semantische_controle_mislukt": lambda: _spy(
        "pass", BUREN, controle=lambda naam: "unsupported"
    ),
    "controle_packet_hash_mismatch": lambda: _ControleAntwoord(
        _spy("pass", BUREN).interpretatie,
        controle_tekst=json.dumps(
            {
                "schema_version": LOKAAL_VERIFICATIESCHEMA,
                "packet_hash": "0" * 64,
                "checks": [
                    {"item": CONTROLE_ITEM, "outcome": "supported", "finding": "x"}
                ],
            }
        ),
    ),
}

TECHNISCH = {
    "unknown": lambda: _SpyAI({}, fout=RuntimeError("storing")),
    "timeout": lambda: _SpyAI({}, fout=TimeoutError()),
    "controle_unknown": lambda: _ControleAntwoord(
        _spy("pass", BUREN).interpretatie, controle_fout=RuntimeError("storing")
    ),
}


@pytest.mark.parametrize("soort", sorted(ONBRUIKBAAR))
def test_onbruikbare_modeluitvoer_is_review_required_met_uitleg(monkeypatch, soort):
    run = _valideer(monkeypatch, "pass", BUREN, ai=ONBRUIKBAAR[soort]())
    document = run.resultaat["ess05_assessment"]
    assert (document["status"], document["error"]["type"]) == ("error", soort)
    assert run.resultaat["rule_statuses"]["ESS-05"] == "review_required"
    detail = _ess05(run)
    reden = detail["parts"][0]["reason"]
    assert reden.startswith(ZIN)
    assert "Reden:" in reden and soort in reden
    assert "technisch" not in reden.casefold()
    assert detail["parts"][0]["action"] != ec._ACTIE_FOUT
    regels = _review_regels(detail["review"])
    assert any("niet bruikbaar" in r for r in regels)
    assert not any("technisch mislukt" in r for r in regels)
    assert detail["review"]["assessment"]["unusable"] is True


@pytest.mark.parametrize("soort", sorted(TECHNISCH))
def test_echte_technische_storing_blijft_error(monkeypatch, soort):
    run = _valideer(monkeypatch, "pass", BUREN, ai=TECHNISCH[soort]())
    document = run.resultaat["ess05_assessment"]
    assert (document["status"], document["error"]["type"]) == ("error", soort)
    assert run.resultaat["rule_statuses"]["ESS-05"] == "error"
    detail = _ess05(run)
    assert not detail["parts"][0]["reason"].startswith(ZIN)
    assert detail["review"]["assessment"]["unusable"] is False
    assert any("technisch mislukt" in r for r in _review_regels(detail["review"]))


def test_zonder_cijfer(monkeypatch):
    run = _valideer(monkeypatch, "pass", BUREN, ai=_SpyAI("geen json"))
    assert "ESS-05" not in (run.resultaat.get("detailed_scores") or {})
    assert _ess05(run).get("score") is None


@pytest.mark.parametrize(
    "soort", ["timeout", "rate_limit", "connection", "unknown", "truncated_response",
              "refusal", "input_truncated", "neighbour_lookup", "invalid_neighbours",
              "controle_timeout", "controle_refusal", "controle_connection"],
)  # fmt: skip
def test_technische_soorten_zijn_niet_onbruikbaar(soort):
    assert not ec.onbruikbare_modeluitvoer(_foutdocument(soort))


def _foutdocument(soort: str, versie: str = "ess05/3") -> dict:
    return {
        "contract_version": versie,
        "status": "error",
        "error": {"type": soort, "message": "x", "phase": "interpretation"},
    }


def test_elke_geldigheidsfout_van_de_bewijsregels_is_onbruikbaar():
    # Driftbewaking: elke soort die bewijsregels.py kan geven, is ingedeeld.
    bron = (
        Path(__file__).resolve().parents[3] / "src/domain/ess05/bewijsregels.py"
    ).read_text(encoding="utf-8")
    soorten = set(re.findall(r'_fout\(\s*"([a-z_]+)"', bron))
    assert {"schemafout", "citaatfout", "kerndekking_onvolledig"} <= soorten
    for soort in soorten:
        assert ec.onbruikbare_modeluitvoer(_foutdocument(soort)), soort


def test_alleen_voor_de_bewijsregelroute():
    assert ec.onbruikbare_modeluitvoer(_foutdocument("schemafout"))
    assert not ec.onbruikbare_modeluitvoer(_foutdocument("schemafout", "ess05/2"))
    assert not ec.onbruikbare_modeluitvoer({**_foutdocument("x"), "status": "assessed"})
