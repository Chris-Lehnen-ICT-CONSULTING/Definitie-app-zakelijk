"""Besluit 19 — offline herbeoordeling van de 22 ruwe v8-antwoorden (ontwikkeling).

Hulpcontrole, geen onderdeel van de testsuite. Leest alleen
`kwalificatieproef-v8/ontwikkeling-resultaat.json` en `ontwikkeling-bundel.json`
(geen hold-out, geen netwerk). Beoordeelt elk ruw antwoord opnieuw met de huidige
contractcode en vergelijkt met de status uit v8.

Verwacht: alleen G060 verandert (error → review_required via conflict, door de
alias); alle andere 21 houden hun v8-status, ook G045 (pass) en G050 (review).
"""

import hashlib
import json
from pathlib import Path

from domain.int02.contract import Configuratie, Uitvoering, beoordeel, maak_invoer

V8 = Path(__file__).resolve().parents[2] / "goldset-freeze-v1" / "kwalificatieproef-v8"


def _herbeoordeel() -> dict[str, tuple[str, str, str | None, str | None]]:
    resultaat = json.loads((V8 / "ontwikkeling-resultaat.json").read_text("utf-8"))
    bundel = json.loads((V8 / "ontwikkeling-bundel.json").read_text("utf-8"))
    payloads = {g["id"]: json.loads(g["payload"]) for g in bundel["gevallen"]}
    configuratie = Configuratie(
        normhash=hashlib.sha256(b"replay").hexdigest(),
        promptversie="def835-int02-prompt/5",
        routeringshash=hashlib.sha256(b"replay").hexdigest(),
        provider="replay",
        model="replay",
    )
    uit = {}
    for geval in resultaat["gevallen"]:
        gid = geval["id"]
        (bericht,) = payloads[gid]["messages"]
        invoer = maak_invoer(**json.loads(bericht["content"])["invoer"])
        antwoord = json.loads(bundel["antwoorden"][gid])
        modeluitvoer = json.loads(antwoord["content"][0]["text"])
        document = beoordeel(
            invoer,
            configuratie,
            modeluitvoer,
            Uitvoering(actor="ai", status="completed"),
        )
        afleiding = document.oordeel["dienst"]["afleiding"] if document.oordeel else None
        uit[gid] = (geval["status"], document.status, afleiding, document.foutdetail)
    return uit


def test_alleen_g060_verandert_en_wordt_review_conflict():
    uit = _herbeoordeel()
    assert len(uit) == 22
    veranderd = {gid: v for gid, v in uit.items() if v[0] != v[1]}
    assert veranderd == {
        "G060": ("error", "review_required", "conflict", None),
    }, veranderd
    assert uit["G045"][:3] == ("pass", "pass", "bronnen_beschrijvend")
    assert uit["G050"][:3] == ("review_required", "review_required", "conflict")
