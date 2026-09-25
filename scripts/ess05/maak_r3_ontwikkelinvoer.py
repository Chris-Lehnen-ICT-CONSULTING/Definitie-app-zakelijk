"""DEF-768 ronde 3 — T-ontwikkelselectie en G-ontwikkelinvoer vóór betaalde calls.

Besluit Chris 24-09 (reports/DEF-768-AI-20260924-R2/uitkomst-en-vervolg-v2.md,
derde herstelvoorstel):

- T: zeven R2-eindgevallen exact gekopieerd (R215, R220, R209, R203, R214,
  R208, R217; labels, bron en tekst ongewijzigd) plus twee zelfontworpen
  positieve voorstelgevallen: de bron noemt expliciet een zelfstandige
  zustersoort met hetzelfde genus, er is geen burenlijst. Bekende
  ontwikkeldata van de uitvoerder, geen onafhankelijke gold.
- G: de vier R2-G-invoeren exact als diagnose, alleen de actuele variant,
  technisch gebonden aan de huidige ESS-05-G-instructie in de code.

    .venv/bin/python scripts/ess05/maak_r3_ontwikkelinvoer.py \\
        [--t-bron PAD] [--g-bron PAD] [--t-doel PAD] [--g-doel PAD]

Doelen worden nooit overschreven; bronhashes moeten exact de vastgelegde zijn.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import proefinvoer as pi

R2_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R2"
R3_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R3"
T_BRON = R2_MAP / "onafhankelijke-eindset-v1.json"
T_BRON_SHA256 = "6ec7394a21e76c2ab5a4aaa64d6b92eea1e51cc71c1cbc64b323bafe783315f7"
G_BRON = R2_MAP / "onafhankelijke-g-invoer-v1.json"
G_BRON_SHA256 = "068b441253f4a9171dd2f8388901c7fe590fb99dfc4e65adca41de2dd507ba5a"
T_DOEL = R3_MAP / "ontwikkelselectie-v1.json"
G_DOEL = R3_MAP / "g-ontwikkelinvoer-v1.json"

#: Besluit ronde 3: de zeven bekende diagnostische R2-gevallen.
KOPIE_IDS = ("R215", "R220", "R209", "R203", "R214", "R208", "R217")
T_SCHEMA = "def768-r3-ontwikkelselectie/1"
G_SCHEMA = "def768-ess05-g-invoer/2"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = "DEF-768 ronde 3 (uitkomst-en-vervolg-v2, akkoord Chris 24-09)"
T_STATUS = (
    "bekende ontwikkeldata: zeven diagnostische R2-eindgevallen en twee door de "
    "uitvoerder ontworpen positieve voorstelgevallen; geen holdout, geen "
    "acceptatieset, geen onafhankelijke gold"
)
G_STATUS = (
    "bekende ontwikkeldata: de vier R2-G-invoeren als diagnose; geen holdout, "
    "geen acceptatieset, geen onafhankelijke gold"
)


def _context(organisatie: str) -> dict[str, list[str]]:
    return {
        "organisatorische_context": [organisatie],
        "juridische_context": [],
        "wettelijke_basis": [],
    }


#: Positief voorstelgeval: de bron noemt zelf een zelfstandige zustersoort met
#: hetzelfde genus; de kern grenst op het brongegeven af, er zijn geen buren.
#: Verwacht review_required: zonder bevestigde buren geen pass; een voorstel
#: van de genoemde zuster is relevant en brongedragen.
POSITIEF: tuple[dict[str, Any], ...] = (
    {
        "id": "R3P1",
        "doel": (
            "Een brongedragen zusterbegrip met hetzelfde genus voorstellen wanneer "
            "geen buur is aangeleverd."
        ),
        "parafrase": False,
        "begrip": "dagvergunning",
        "tekst": "visvergunning die toestemming geeft om op één kalenderdag te vissen",
        "toelichting": None,
        "categorie": None,
        "context": _context("Fictieve visvereniging Rindel"),
        "bronnen": [
            {
                "provider": "documents",
                "doc_id": "synthetisch-R3P1",
                "title": "Synthetische domeinafspraak Rindel",
                "snippet": (
                    "Rindel geeft twee soorten visvergunningen uit. Een "
                    "dagvergunning geeft toestemming om op één kalenderdag te "
                    "vissen. Een seizoensvergunning geeft toestemming om het hele "
                    "visseizoen te vissen."
                ),
            }
        ],
        "buren": [],
        "verwacht": "review_required",
        "verwacht_per_buur": [],
        "grond": (
            "Kern met genus en afgrenzende duur. Geen bevestigde buren, dus geen "
            "pass. De bron noemt zelf de tweede soort vergunning met hetzelfde "
            "genus; dat voorstel is relevant en brongedragen, niet verzonnen."
        ),
        "toegestane_vraag": (
            "Vraag of de andere vergunningssoort van de vereniging als verwant "
            "begrip bevestigd moet worden."
        ),
    },
    {
        "id": "R3P2",
        "doel": (
            "Een brongedragen zusterbegrip met hetzelfde genus voorstellen wanneer "
            "geen buur is aangeleverd."
        ),
        "parafrase": False,
        "begrip": "wrakboei",
        "tekst": "markeringsboei die de plaats van een gezonken vaartuig markeert",
        "toelichting": None,
        "categorie": None,
        "context": _context("Fictieve havendienst Merel"),
        "bronnen": [
            {
                "provider": "documents",
                "doc_id": "synthetisch-R3P2",
                "title": "Synthetische domeinafspraak Merel",
                "snippet": (
                    "De havendienst Merel legt twee soorten markeringsboeien uit. "
                    "Een wrakboei markeert de plaats van een gezonken vaartuig. "
                    "Een ankerboei markeert de plaats van een uitgebracht anker."
                ),
            }
        ],
        "buren": [],
        "verwacht": "review_required",
        "verwacht_per_buur": [],
        "grond": (
            "Kern met genus en afgrenzend object van de markering. Geen bevestigde "
            "buren, dus geen pass. De bron noemt zelf de tweede boeisoort met "
            "hetzelfde genus; dat voorstel is relevant en brongedragen."
        ),
        "toegestane_vraag": (
            "Vraag of de andere boeisoort van de havendienst als verwant begrip "
            "bevestigd moet worden."
        ),
    },
)
#: Het zusterbegrip dat elk positief geval uit zijn bron hoort te dragen.
VERWACHTE_ZUSTERS = {"R3P1": "seizoensvergunning", "R3P2": "ankerboei"}


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _controleer_bron(bron_bytes: bytes, verwacht: str) -> dict[str, Any]:
    if _sha(bron_bytes) != verwacht:
        msg = f"bronhash {_sha(bron_bytes)} is niet de vastgelegde {verwacht}"
        raise SelectiefoutError(msg)
    return json.loads(bron_bytes)


def maak_t_selectie(bron_bytes: bytes, *, bron_pad: str) -> dict[str, Any]:
    """Zeven exacte kopieën + twee positieve voorstelgevallen."""
    bron = _controleer_bron(bron_bytes, T_BRON_SHA256)
    per_id = {g["id"]: g for g in bron["gevallen"]}
    ontbrekend = [i for i in KOPIE_IDS if i not in per_id]
    if ontbrekend:
        msg = f"selectie ongeldig (ontbrekend {ontbrekend})"
        raise SelectiefoutError(msg)
    nieuw = [copy.deepcopy(g) for g in POSITIEF]
    return {
        "schema": T_SCHEMA,
        "status": T_STATUS,
        "herkomst": {
            "bron": bron_pad,
            "bron_sha256": T_BRON_SHA256,
            "bron_schema": bron.get("schema"),
            "bron_status": bron.get("status"),
            "gekopieerde_ids": list(KOPIE_IDS),
            "bewerking_kopie": (
                "alleen selectie; elk gekopieerd geval byte-voor-byte gelijk als JSON"
            ),
            "nieuwe_ids": [g["id"] for g in nieuw],
            "nieuwe_gevallen": (
                "zelfontworpen door de uitvoerder na inzage van de R2-uitkomst; "
                "bekende ontwikkeldata, geen onafhankelijke gold"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [copy.deepcopy(per_id[i]) for i in KOPIE_IDS] + nieuw,
    }


def controleer_t_selectie(selectie: dict[str, Any], bron_bytes: bytes) -> None:
    """Kopieën exact, nieuwe gevallen geldig en zonder labellek."""
    bron = {g["id"]: g for g in json.loads(bron_bytes)["gevallen"]}
    herkomst = selectie["herkomst"]
    ids = [g["id"] for g in selectie["gevallen"]]
    if ids != [*herkomst["gekopieerde_ids"], *herkomst["nieuwe_ids"]]:
        msg = "volgorde of ids van de gevallen wijken af van de herkomst"
        raise SelectiefoutError(msg)
    for geval in selectie["gevallen"][: len(herkomst["gekopieerde_ids"])]:
        if json.dumps(geval, sort_keys=True) != json.dumps(
            bron[geval["id"]], sort_keys=True
        ):
            msg = f"{geval['id']} wijkt af van de bron"
            raise SelectiefoutError(msg)
    if "herhaal_ids" in selectie:
        msg = "een ontwikkelselectie heeft geen herhaal_ids"
        raise SelectiefoutError(msg)
    pi.valideer_gevallenbestand(selectie, herhaal_vereist=False)
    from services.validation.ess05_assessment_service import laad_ess05_norm

    norm = laad_ess05_norm()
    for geval in selectie["gevallen"]:
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        pi.controleer_afscherming(geval, prompt.teksten, norm)


def maak_g_invoer(bron_bytes: bytes, *, bron_pad: str) -> dict[str, Any]:
    """De vier R2-G-invoeren exact; actueel gebonden aan de huidige instructie."""
    bron = _controleer_bron(bron_bytes, G_BRON_SHA256)
    if len(bron["invoeren"]) != 4:
        msg = f"verwacht 4 R2-G-invoeren, gekregen {len(bron['invoeren'])}"
        raise SelectiefoutError(msg)
    actueel = pi.huidige_g_instructie()
    return {
        "schema": G_SCHEMA,
        "status": G_STATUS,
        "synthetisch": bron.get("synthetisch", True),
        "invoeren": copy.deepcopy(bron["invoeren"]),
        "g_teksten": {
            "basis": copy.deepcopy(bron["g_teksten"]["basis"]),
            "actueel": {
                "herkomst": (
                    "R3 appinstructie; werkboom na geautoriseerd derde "
                    "herstelvoorstel, runner verifieert SHA"
                ),
                "sha256": _sha(actueel.encode("utf-8")),
            },
        },
        "herkomst": {
            "bron": bron_pad,
            "bron_sha256": G_BRON_SHA256,
            "bron_status": bron.get("status"),
            "invoer_ids": [i["id"] for i in bron["invoeren"]],
            "bewerking": (
                "invoeren en basis-G-tekst exact gekopieerd; alleen de actuele "
                "G-binding, status en herkomst zijn nieuw"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
    }


def _schrijf(doel: Path, data: dict[str, Any]) -> str:
    tekst = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    return _sha(tekst.encode("utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t-bron", type=Path, default=T_BRON)
    p.add_argument("--g-bron", type=Path, default=G_BRON)
    p.add_argument("--t-doel", type=Path, default=T_DOEL)
    p.add_argument("--g-doel", type=Path, default=G_DOEL)
    args = p.parse_args(argv)
    if args.t_doel.exists() or args.g_doel.exists():
        msg = f"doel bestaat al: {args.t_doel} of {args.g_doel}"
        raise FileExistsError(msg)
    t_bytes = args.t_bron.read_bytes()
    selectie = maak_t_selectie(t_bytes, bron_pad=str(args.t_bron))
    controleer_t_selectie(selectie, t_bytes)
    g = maak_g_invoer(args.g_bron.read_bytes(), bron_pad=str(args.g_bron))
    t_sha = _schrijf(args.t_doel, selectie)
    g_sha = _schrijf(args.g_doel, g)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n{args.g_doel} sha256={g_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
