"""DEF-768 ronde 5 — T-ontwikkelselectie en G-ontwikkelinvoer vóór betaalde calls.

Besluit Chris 25-09 (reports/DEF-768-AI-20260924-R4/uitkomst-en-vervolg-v1.md,
concreet vervolgvoorstel, 'ja akkoord'): één ontwikkelronde op bekende
diagnostische data.

- T (9): R410, R411, R414, R409, R412, R417, R403 uit de R4-eindset; R313 uit
  de R3-eindset; R3P1 uit de R3-ontwikkelselectie. Bron, labels en intentie
  ongewijzigd; geen parafrase, geen tuning, geen nieuwe ids.
- G (4): R4G1 uit de R4-G-eindinvoer v2 (verliesvrij gesegmenteerd) tweemaal
  (R4G1, R4G1-D2: alleen het id verschilt), R3G3 uit de oorspronkelijke
  R3-G-invoer, R2G4 uit de oorspronkelijke R2-G-invoer. Invoeren en de
  basis-G-tekst (oorspronkelijke git-HEAD-tekst) exact; alleen de actuele
  G-binding is nieuw.

Bekende ontwikkeldata, geen onafhankelijke gold.

    .venv/bin/python scripts/ess05/maak_r5_ontwikkelinvoer.py [--t-doel PAD] [--g-doel PAD]

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
R4_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R4"
R5_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R5"
#: Bronnen (alleen lezen) met vastgelegde hash.
T_R4 = R4_MAP / "onafhankelijke-eindset-v1.json"
T_R4_SHA256 = "9338e61bc4b79938abc2583d9bd97c299a6e0f39f4eae880d5c8ff415e95afda"
T_R3 = R3_MAP / "onafhankelijke-eindset-v1.json"
T_R3_SHA256 = "d550688338ac023c61f6403d57986830679c8840979b1fb49610213f4b05cc44"
T_R3_SELECTIE = R3_MAP / "ontwikkelselectie-v1.json"
T_R3_SELECTIE_SHA256 = (
    "994b2129592dfbfddce0cb3cbbbe0aadd6c03348529a269e4fc7409397d7df38"
)
G_R4 = R4_MAP / "onafhankelijke-g-invoer-v2.json"
G_R4_SHA256 = "0d383f9539b0575516e24f222a6888b1edf23b42975e39ebe7910d3739e894a2"
G_R3 = R3_MAP / "onafhankelijke-g-invoer-v1.json"
G_R3_SHA256 = "ebbd0202370f24f0545b7df1f3d42a783c664dfce669a7f1e1c81b90c5a4b84e"
G_R2 = R2_MAP / "onafhankelijke-g-invoer-v1.json"
G_R2_SHA256 = "068b441253f4a9171dd2f8388901c7fe590fb99dfc4e65adca41de2dd507ba5a"
#: Oorspronkelijke git-HEAD-tekst van de ESS-05-instructieregel (basisvariant).
BASIS_SHA256 = "7becf15d09c7c508adb5a011b992b2c1bbc38529a38a3238869b71cbd4e107b8"
T_DOEL = R5_MAP / "ontwikkelselectie-v1.json"
G_DOEL = R5_MAP / "g-ontwikkelinvoer-v1.json"

#: (ontwikkel-id, bron, oorsprong-id) in afrekenvolgorde.
T_PLAN = (
    ("R410", "r4", "R410"),
    ("R411", "r4", "R411"),
    ("R414", "r4", "R414"),
    ("R409", "r4", "R409"),
    ("R412", "r4", "R412"),
    ("R417", "r4", "R417"),
    ("R403", "r4", "R403"),
    ("R313", "r3", "R313"),
    ("R3P1", "r3_selectie", "R3P1"),
)
G_PLAN = (
    ("R4G1", "r4", "R4G1"),
    ("R4G1-D2", "r4", "R4G1"),
    ("R3G3", "r3", "R3G3"),
    ("R2G4", "r2", "R2G4"),
)
_ONTWIKKEL_IDS = {nieuw: oud for nieuw, _, oud in (*T_PLAN, *G_PLAN) if nieuw != oud}
T_SCHEMA = "def768-r5-ontwikkelselectie/1"
G_SCHEMA = "def768-ess05-g-invoer/2"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = (
    "DEF-768 ronde 5 (R4 uitkomst-en-vervolg-v1 §concreet vervolgvoorstel, "
    "akkoord Chris 25-09)"
)
T_STATUS = (
    "bekende ontwikkeldata: diagnostische R4-eindgevallen, R313 uit de "
    "R3-eindset en R3P1 uit de R3-ontwikkelselectie; geen holdout, geen "
    "acceptatieset, geen onafhankelijke gold"
)
G_STATUS = (
    "bekende ontwikkeldata: diagnostische R4-/R3-/R2-G-invoeren (R4G1 tweemaal); "
    "geen holdout, geen acceptatieset, geen onafhankelijke gold"
)


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def oorsprong_id(ontwikkel_id: str) -> str:
    """Het bron-id achter een ontwikkel-id (R4G1-D2 → R4G1)."""
    return _ONTWIKKEL_IDS.get(ontwikkel_id, ontwikkel_id)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bron(data: bytes, verwacht: str, naam: str) -> dict[str, Any]:
    if _sha(data) != verwacht:
        msg = f"{naam}: bronhash {_sha(data)} is niet de vastgelegde {verwacht}"
        raise SelectiefoutError(msg)
    return json.loads(data)


def _kopie(record: dict[str, Any], ontwikkel_id: str) -> dict[str, Any]:
    kopie = copy.deepcopy(record)
    kopie["id"] = ontwikkel_id
    return kopie


def _per_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {i["id"]: i for i in items}


def _bronverwijzing(pad: Path, sha: str) -> dict[str, str]:
    return {"pad": str(pad.relative_to(PROJECT_ROOT)), "sha256": sha}


def maak_t_selectie(
    r4_bytes: bytes, r3_bytes: bytes, r3_selectie_bytes: bytes, *, bron_pad: str
) -> dict[str, Any]:
    """Negen ontwikkelgevallen, elk exact het bronrecord."""
    bronnen = {
        "r4": _per_id(_bron(r4_bytes, T_R4_SHA256, "R4-eindset")["gevallen"]),
        "r3": _per_id(_bron(r3_bytes, T_R3_SHA256, "R3-eindset")["gevallen"]),
        "r3_selectie": _per_id(
            _bron(r3_selectie_bytes, T_R3_SELECTIE_SHA256, "R3-ontwikkelselectie")[
                "gevallen"
            ]
        ),
    }
    ontbrekend = [o for _, b, o in T_PLAN if o not in bronnen[b]]
    if ontbrekend:
        msg = f"selectie ongeldig (ontbrekend {ontbrekend})"
        raise SelectiefoutError(msg)
    return {
        "schema": T_SCHEMA,
        "status": T_STATUS,
        "herkomst": {
            "bronnen": {
                "r4": _bronverwijzing(T_R4, T_R4_SHA256),
                "r3": _bronverwijzing(T_R3, T_R3_SHA256),
                "r3_selectie": _bronverwijzing(T_R3_SELECTIE, T_R3_SELECTIE_SHA256),
            },
            "bron_pad_aanroep": bron_pad,
            "plan": [{"id": n, "bron": b, "oorsprong_id": o} for n, b, o in T_PLAN],
            "ontwikkel_ids": {n: o for n, _, o in T_PLAN if n != o},
            "bewerking": (
                "elk geval byte-voor-byte gelijk aan het bronrecord als JSON; "
                "inhoud, labels en ids ongewijzigd"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [_kopie(bronnen[b][o], n) for n, b, o in T_PLAN],
    }


def controleer_t_selectie(
    selectie: dict[str, Any],
    r4_bytes: bytes,
    r3_bytes: bytes,
    r3_selectie_bytes: bytes,
) -> None:
    """Elk geval exact gelijk aan zijn bron, zonder lek in de instructie."""
    bronnen = {
        "r4": _per_id(json.loads(r4_bytes)["gevallen"]),
        "r3": _per_id(json.loads(r3_bytes)["gevallen"]),
        "r3_selectie": _per_id(json.loads(r3_selectie_bytes)["gevallen"]),
    }
    if [g["id"] for g in selectie["gevallen"]] != [n for n, _, _ in T_PLAN]:
        msg = "volgorde of ids van de gevallen wijken af van het plan"
        raise SelectiefoutError(msg)
    for geval, (n, b, o) in zip(selectie["gevallen"], T_PLAN, strict=True):
        if json.dumps(geval, sort_keys=True) != json.dumps(
            _kopie(bronnen[b][o], n), sort_keys=True
        ):
            msg = f"{n} wijkt af van bronrecord {o}"
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


def maak_g_invoer(
    r4_bytes: bytes, r3_bytes: bytes, r2_bytes: bytes, *, bron_pad: str
) -> dict[str, Any]:
    """Vier G-invoeren exact; alleen de actuele G-binding en ontwikkel-id zijn nieuw."""
    data = {
        "r4": _bron(r4_bytes, G_R4_SHA256, "R4-G-invoer v2"),
        "r3": _bron(r3_bytes, G_R3_SHA256, "R3-G-invoer"),
        "r2": _bron(r2_bytes, G_R2_SHA256, "R2-G-invoer"),
    }
    basis = data["r2"]["g_teksten"]["basis"]
    for naam, bron in data.items():
        if bron["g_teksten"]["basis"] != basis:
            msg = f"basis-G-tekst van {naam} wijkt af van de oorspronkelijke"
            raise SelectiefoutError(msg)
    if basis["sha256"] != BASIS_SHA256 or (
        _sha(basis["tekst"].encode("utf-8")) != BASIS_SHA256
    ):
        msg = "basis-G-tekst is niet de oorspronkelijke git-HEAD-tekst"
        raise SelectiefoutError(msg)
    bronnen = {naam: _per_id(bron["invoeren"]) for naam, bron in data.items()}
    actueel = pi.huidige_g_instructie()
    return {
        "schema": G_SCHEMA,
        "status": G_STATUS,
        "synthetisch": True,
        "invoeren": [_kopie(bronnen[b][o], n) for n, b, o in G_PLAN],
        "g_teksten": {
            "basis": copy.deepcopy(basis),
            "actueel": {
                "herkomst": (
                    "R5 appinstructie; werkboom na geautoriseerd gericht vervolg "
                    "(R4-E04), runner verifieert SHA"
                ),
                "sha256": _sha(actueel.encode("utf-8")),
            },
        },
        "herkomst": {
            "bronnen": {
                "r4": _bronverwijzing(G_R4, G_R4_SHA256),
                "r3": _bronverwijzing(G_R3, G_R3_SHA256),
                "r2": _bronverwijzing(G_R2, G_R2_SHA256),
            },
            "bron_pad_aanroep": bron_pad,
            "plan": [{"id": n, "bron": b, "oorsprong_id": o} for n, b, o in G_PLAN],
            "ontwikkel_ids": {n: o for n, _, o in G_PLAN if n != o},
            "bewerking": (
                "invoeren en basis-G-tekst exact gekopieerd (R4G1 met de "
                "verliesvrije segmentatie uit v2); alleen het id van de "
                "ontwikkelkopie, de actuele G-binding, status en herkomst zijn nieuw"
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
    p.add_argument("--t-doel", type=Path, default=T_DOEL)
    p.add_argument("--g-doel", type=Path, default=G_DOEL)
    args = p.parse_args(argv)
    if args.t_doel.exists() or args.g_doel.exists():
        msg = f"doel bestaat al: {args.t_doel} of {args.g_doel}"
        raise FileExistsError(msg)
    t_bronnen = (T_R4.read_bytes(), T_R3.read_bytes(), T_R3_SELECTIE.read_bytes())
    selectie = maak_t_selectie(*t_bronnen, bron_pad="standaard")
    controleer_t_selectie(selectie, *t_bronnen)
    g = maak_g_invoer(
        G_R4.read_bytes(), G_R3.read_bytes(), G_R2.read_bytes(), bron_pad="standaard"
    )
    t_sha = _schrijf(args.t_doel, selectie)
    g_sha = _schrijf(args.g_doel, g)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n{args.g_doel} sha256={g_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
