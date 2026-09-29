"""DEF-768 robuustheidsronde — de drie echte P1-antwoorden door de app-route (stubs).

De spy geeft als interpretatie exact de ruwe P1-respons terug; elke lokale
controle antwoordt `supported`. Dat bewijst wat de nieuwe regels met déze
modeluitvoer doen (document, notities, replay, melding), niet de modelkwaliteit.
Geen netwerk, geen echte aanroep.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from domain.ess03.contract import Intentie
from domain.ess05 import contract as ec
from services.validation import ess05_bewijsregel_service as bs
from tests.unit.validation.test_def768_bewijsregel_service import _SpyAI

pytestmark = [pytest.mark.unit]

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / ("def768_p1_echte_antwoorden_v1.json")
)
P1 = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]


def _beoordeel(rid: str):
    r = P1[rid]
    dienst = bs.Ess05BewijsregelService.voor_app(_SpyAI(r["ruwe_respons"]))
    intentie = Intentie(**r["intentie"])
    buren = ec.normaliseer_buren(r["buren"])
    document = asyncio.run(
        dienst.assess(
            r["begrip"], r["definitie"], r["contexten"], [], buren=buren,
            intentie=intentie, uitgesloten_termen=(), correlation_id=f"p1-{rid}",
        )
    )  # fmt: skip
    uitkomst = ec.beoordeel_onderscheid(
        r["begrip"], r["definitie"], r["contexten"], [], intentie=intentie,
        buren=r["buren"], assessment=document,
        binding=ec.binding_uit_dict(dienst.binding().als_dict()),
    )  # fmt: skip
    return document, uitkomst


def test_277_geen_betekenisfout_meer_notities_in_het_document():
    document, uitkomst = _beoordeel("277")
    assert document["status"] == "assessed"
    notities = document["interpretation"]["notes"]
    assert [n.split(" ", 1)[0] for n in notities] == ["M1", "M2"]
    assert uitkomst.status == ec.STATUS_OPEN
    assert uitkomst.review["assessment"]["applied"] is True


def test_365_zonder_voorwaarden_geen_schemafout_meer():
    document, uitkomst = _beoordeel("365")
    assert document["status"] == "assessed"
    assert len(document["interpretation"]["notes"]) == 2
    assert uitkomst.status in (ec.STATUS_OPEN, ec.STATUS_FAIL, ec.STATUS_PASS)
    assert uitkomst.review["assessment"]["applied"] is True


def test_278_ruis_niet_meer_in_de_dekkingsfout():
    # De ruwe 278-respons hoort bij de oude tekst; de eerlijke uitkomst is nu
    # review_required. Wat overblijft: het buiten_bereik-deel van de definitie
    # telt niet mee in de kerndekking (geen ruis meer: 'Soort', 'Bron').
    document, uitkomst = _beoordeel("278")
    assert document["status"] == "error"
    melding = document["error"]["message"]
    assert "'Soort'" not in melding and "'Bron'" not in melding
    assert uitkomst.status == ec.STATUS_OPEN
    assert uitkomst.parts[0].reason.startswith(
        "De AI kon dit niet betrouwbaar automatisch beoordelen; beoordeel handmatig."
    )


def test_prompt_krijgt_de_geneutraliseerde_definitie():
    r = P1["278"]
    ai = _SpyAI(r["ruwe_respons"])
    dienst = bs.Ess05BewijsregelService.voor_app(ai)
    asyncio.run(
        dienst.assess(
            r["begrip"], r["definitie"], r["contexten"], [],
            buren=ec.normaliseer_buren(r["buren"]),
            intentie=Intentie(**r["intentie"]), uitgesloten_termen=(),
        )
    )  # fmt: skip
    prompt = ai.aanroepen[0]["prompt"]
    assert "Soort" not in prompt and "[Bron" not in prompt
    assert ">rechtsbijstandverlener die als advocaat optreedt" in prompt
