"""Besluit 22 — offline wat-als: de 93 bewaarde antwoorden opnieuw beoordeeld.

Hulpcontrole, geen onderdeel van de testsuite. Leest alleen:

- `kwalificatieproef-v8/` en `kwalificatieproef-v9/`: `regressie-bundel.json`,
  `regressie-resultaat.json`, `ontwikkeling-bundel.json` en
  `ontwikkeling-resultaat.json` (22 + 3 + 17 + 3 antwoorden);
- `variatiemeting-v9/live-v1/calls.jsonl` (48 antwoorden), met de invoer uit
  `goldset-freeze-v1/ontwikkeling-v1.json`.

Geen hold-out (elk pad wordt vóór het openen op de naam getoetst), geen
netwerk. Elk ruw antwoord wordt met de huidige contractcode opnieuw beoordeeld
en vergeleken met de bewaarde status, afleiding en omzetting.

Verwacht (besluit 22, R1 en R2): precies vier wijzigingen, alle vier van pass
naar review_required met de omzettingscode van R1 of R2:

- G050 v9 en G050 meting h1 call 17 (R1, `discretie_nooit_pass`);
- G060 meting h1 call 22 en h2 call 46 (R2, `onduidelijk_naast_kenmerk`).

Daarnaast verandert G060 uit v8 (error → review_required via `conflict`); dat
is besluit 19 (alias voor een kaal bron-ID), al vastgelegd in
`replay_v8_besluit19_test.py`. Verder verandert niets, ook G045 uit v8 niet
(blijft pass: B1 `criterion`, B2 zwijgt).
"""

import hashlib
import json
from pathlib import Path

from domain.int02.contract import Configuratie, Uitvoering, beoordeel, maak_invoer

G = Path(__file__).resolve().parents[2]
FREEZE = G / "goldset-freeze-v1"
CALLS = G / "variatiemeting-v9" / "live-v1" / "calls.jsonl"
VERBODEN = ("holdout", "hold-out", "hold_out")
R1 = "discretie_nooit_pass"
R2 = "onduidelijk_naast_kenmerk"


def _lees(pad: Path) -> str:
    assert not any(deel in pad.name.lower() for deel in VERBODEN), pad
    return pad.read_text("utf-8")


def _configuratie() -> Configuratie:
    return Configuratie(
        normhash=hashlib.sha256(b"replay").hexdigest(),
        promptversie="def835-int02-prompt/6",
        routeringshash=hashlib.sha256(b"replay").hexdigest(),
        provider="replay",
        model="replay",
    )


def _opnieuw(invoer, ruw: str) -> tuple[str, str | None, str | None]:
    """(status, afleiding, omzetting) van een ruw API-antwoord onder de huidige code."""
    modeluitvoer = json.loads(json.loads(ruw)["content"][0]["text"])
    document = beoordeel(
        invoer,
        _configuratie(),
        modeluitvoer,
        Uitvoering(actor="ai", status="completed"),
    )
    afleiding = document.oordeel["dienst"]["afleiding"] if document.oordeel else None
    return document.status, afleiding, document.omzetting


def _bewaard_document(document: dict) -> tuple[str, str | None, str | None]:
    oordeel = document.get("oordeel") or {}
    afleiding = (oordeel.get("dienst") or {}).get("afleiding")
    return document["status"], afleiding, document.get("omzetting")


def _proefantwoorden():
    """(sleutel, bewaard, opnieuw) voor de 45 antwoorden uit v8 en v9."""
    for proef in ("kwalificatieproef-v8", "kwalificatieproef-v9"):
        for fase in ("regressie", "ontwikkeling"):
            map_ = FREEZE / proef
            bundel = json.loads(_lees(map_ / f"{fase}-bundel.json"))
            resultaat = json.loads(_lees(map_ / f"{fase}-resultaat.json"))
            payloads = {g["id"]: json.loads(g["payload"]) for g in bundel["gevallen"]}
            for geval in resultaat["gevallen"]:
                gid = geval["id"]
                (bericht,) = payloads[gid]["messages"]
                invoer = maak_invoer(**json.loads(bericht["content"])["invoer"])
                bewaard = _bewaard_document(geval["document"])
                assert bewaard[0] == geval["status"]
                opnieuw = _opnieuw(invoer, bundel["antwoorden"][gid])
                yield f"{proef[-2:]}-{fase}/{gid}", bewaard, opnieuw


def _ontwikkelinvoer() -> dict:
    data = json.loads(_lees(FREEZE / "ontwikkeling-v1.json"))
    invoer = {}
    for item in data["gevallen"]:
        geval = item["geval"]
        invoer[item["id"]] = maak_invoer(
            begrip=geval["begrip"],
            kern=geval["kern"],
            bedoeling=geval["bedoeling"],
            **geval["context"],
            bronnen=[{"id": b["id"], "tekst": b["tekst"]} for b in geval["bronnen"]],
        )
    return invoer


def _meetantwoorden():
    """(sleutel, bewaard, opnieuw) voor de 48 calls van de variatiemeting."""
    invoer = _ontwikkelinvoer()
    for regel in _lees(CALLS).splitlines():
        call = json.loads(regel)
        bewaard = (call["status"], call["afleiding"], call["omzetting"])
        opnieuw = _opnieuw(invoer[call["geval"]], call["ruw_antwoord"])
        sleutel = f"meting-h{call['herhaling']}/call{call['call']}/{call['geval']}"
        yield sleutel, bewaard, opnieuw


def _alles() -> dict[str, tuple[tuple, tuple]]:
    uit = {}
    for sleutel, bewaard, opnieuw in (*_proefantwoorden(), *_meetantwoorden()):
        assert sleutel not in uit, sleutel
        uit[sleutel] = (bewaard, opnieuw)
    return uit


def test_precies_de_vier_wijzigingen_van_besluit_22():
    uit = _alles()
    assert len(uit) == 93
    assert sum(k.startswith("meting-") for k in uit) == 48
    veranderd = {k: v for k, v in uit.items() if v[0] != v[1]}
    assert veranderd == {
        # Besluit 19 (alias), al eerder vastgelegd; geen besluit 22.
        "v8-ontwikkeling/G060": (
            ("error", None, None),
            ("review_required", "conflict", "conflict"),
        ),
        # R1: kernvorm discretion_form wordt nooit pass.
        "v9-ontwikkeling/G050": (
            ("pass", "bronnen_beschrijvend", None),
            ("review_required", R1, R1),
        ),
        "meting-h1/call17/G050": (
            ("pass", "bronnen_beschrijvend", None),
            ("review_required", R1, R1),
        ),
        # R2: unclear naast criterion wordt geen pass.
        "meting-h1/call22/G060": (
            ("pass", "bronnen_beschrijvend", None),
            ("review_required", R2, R2),
        ),
        "meting-h2/call46/G060": (
            ("pass", "bronnen_beschrijvend", None),
            ("review_required", R2, R2),
        ),
    }, veranderd


def test_g045_uit_v8_blijft_de_bekende_false_pass():
    uit = _alles()
    assert uit["v8-ontwikkeling/G045"] == (
        ("pass", "bronnen_beschrijvend", None),
        ("pass", "bronnen_beschrijvend", None),
    )
