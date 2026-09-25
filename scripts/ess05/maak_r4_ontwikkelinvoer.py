"""DEF-768 ronde 4 — T-ontwikkelselectie en G-ontwikkelinvoer vóór betaalde calls.

Besluit Chris 24-09 (reports/DEF-768-AI-20260924-R3/uitkomst-en-vervolg-v1.md,
gericht vervolg): één ontwikkelronde op bekende diagnostische data.

- T (9): R308, R312, R313 uit de R3-eindset; twee inhoudelijk exacte R313-
  kopieën met een eigen ontwikkel-id (R313-D2, R313-D3), zodat R313 driemaal
  wordt afgerekend; R302 (echte rol-overlap) en R320 (geen ongegronde
  registratiebuur) uit de R3-eindset; R3P1 en R3P2 (positieve
  zustervoorstellen) uit de R3-ontwikkelselectie. Bron, labels en intentie
  ongewijzigd; alleen het id van de twee kopieën verschilt.
- G (4): R3G3 tweemaal (R3G3, R3G3-D2) en R3G1 uit de R3-G-eindinvoer, R2G4
  uit de R2-G-invoer; invoeren exact, alleen de actuele G-binding is nieuw.

Bekende ontwikkeldata, geen onafhankelijke gold.

    .venv/bin/python scripts/ess05/maak_r4_ontwikkelinvoer.py [--t-doel PAD] [--g-doel PAD]

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
#: Bronnen (alleen lezen) met vastgelegde hash.
T_EINDSET = R3_MAP / "onafhankelijke-eindset-v1.json"
T_EINDSET_SHA256 = "d550688338ac023c61f6403d57986830679c8840979b1fb49610213f4b05cc44"
T_SELECTIE = R3_MAP / "ontwikkelselectie-v1.json"
T_SELECTIE_SHA256 = "994b2129592dfbfddce0cb3cbbbe0aadd6c03348529a269e4fc7409397d7df38"
G_R3 = R3_MAP / "onafhankelijke-g-invoer-v1.json"
G_R3_SHA256 = "ebbd0202370f24f0545b7df1f3d42a783c664dfce669a7f1e1c81b90c5a4b84e"
G_R2 = R2_MAP / "onafhankelijke-g-invoer-v1.json"
G_R2_SHA256 = "068b441253f4a9171dd2f8388901c7fe590fb99dfc4e65adca41de2dd507ba5a"
T_DOEL = R4_MAP / "ontwikkelselectie-v1.json"
G_DOEL = R4_MAP / "g-ontwikkelinvoer-v1.json"

#: (ontwikkel-id, bron, oorsprong-id) in afrekenvolgorde.
T_PLAN = (
    ("R308", "eindset", "R308"),
    ("R312", "eindset", "R312"),
    ("R313", "eindset", "R313"),
    ("R313-D2", "eindset", "R313"),
    ("R313-D3", "eindset", "R313"),
    ("R302", "eindset", "R302"),
    ("R3P1", "selectie", "R3P1"),
    ("R3P2", "selectie", "R3P2"),
    ("R320", "eindset", "R320"),
)
G_PLAN = (
    ("R3G3", "r3", "R3G3"),
    ("R3G3-D2", "r3", "R3G3"),
    ("R2G4", "r2", "R2G4"),
    ("R3G1", "r3", "R3G1"),
)
_ONTWIKKEL_IDS = {nieuw: oud for nieuw, _, oud in (*T_PLAN, *G_PLAN) if nieuw != oud}
T_SCHEMA = "def768-r4-ontwikkelselectie/1"
G_SCHEMA = "def768-ess05-g-invoer/2"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = "DEF-768 ronde 4 (R3 uitkomst-en-vervolg-v1 §vervolg, akkoord Chris 24-09)"
T_STATUS = (
    "bekende ontwikkeldata: diagnostische R3-eindgevallen (R313 driemaal) en "
    "bekende R3-ontwikkelgevallen; geen holdout, geen acceptatieset, geen "
    "onafhankelijke gold"
)
G_STATUS = (
    "bekende ontwikkeldata: diagnostische R3-/R2-G-invoeren (R3G3 tweemaal); geen "
    "holdout, geen acceptatieset, geen onafhankelijke gold"
)


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def oorsprong_id(ontwikkel_id: str) -> str:
    """Het bron-id achter een ontwikkel-id (R313-D2 → R313)."""
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


def maak_t_selectie(
    eindset_bytes: bytes, selectie_bytes: bytes, *, bron_pad: str
) -> dict[str, Any]:
    """Negen ontwikkelgevallen; alleen het id van de R313-kopieën is nieuw."""
    bronnen = {
        "eindset": _per_id(
            _bron(eindset_bytes, T_EINDSET_SHA256, "R3-eindset")["gevallen"]
        ),
        "selectie": _per_id(
            _bron(selectie_bytes, T_SELECTIE_SHA256, "R3-ontwikkelselectie")["gevallen"]
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
                "eindset": {
                    "pad": str(T_EINDSET.relative_to(PROJECT_ROOT)),
                    "sha256": T_EINDSET_SHA256,
                },
                "selectie": {
                    "pad": str(T_SELECTIE.relative_to(PROJECT_ROOT)),
                    "sha256": T_SELECTIE_SHA256,
                },
            },
            "bron_pad_aanroep": bron_pad,
            "plan": [{"id": n, "bron": b, "oorsprong_id": o} for n, b, o in T_PLAN],
            "ontwikkel_ids": {n: o for n, _, o in T_PLAN if n != o},
            "bewerking": (
                "elk geval byte-voor-byte gelijk aan het bronrecord als JSON; "
                "alleen het id van de ontwikkelkopieën verschilt"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [_kopie(bronnen[b][o], n) for n, b, o in T_PLAN],
    }


def controleer_t_selectie(
    selectie: dict[str, Any], eindset_bytes: bytes, selectie_bytes: bytes
) -> None:
    """Elk geval exact gelijk aan zijn bron (behalve het ontwikkel-id), zonder lek."""
    bronnen = {
        "eindset": _per_id(json.loads(eindset_bytes)["gevallen"]),
        "selectie": _per_id(json.loads(selectie_bytes)["gevallen"]),
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


def maak_g_invoer(r3_bytes: bytes, r2_bytes: bytes, *, bron_pad: str) -> dict[str, Any]:
    """Vier G-invoeren exact; alleen de actuele G-binding en ontwikkel-ids zijn nieuw."""
    r3 = _bron(r3_bytes, G_R3_SHA256, "R3-G-invoer")
    r2 = _bron(r2_bytes, G_R2_SHA256, "R2-G-invoer")
    if r3["g_teksten"]["basis"] != r2["g_teksten"]["basis"]:
        msg = "basis-G-tekst van R2 en R3 verschilt"
        raise SelectiefoutError(msg)
    bronnen = {"r3": _per_id(r3["invoeren"]), "r2": _per_id(r2["invoeren"])}
    actueel = pi.huidige_g_instructie()
    return {
        "schema": G_SCHEMA,
        "status": G_STATUS,
        "synthetisch": True,
        "invoeren": [_kopie(bronnen[b][o], n) for n, b, o in G_PLAN],
        "g_teksten": {
            "basis": copy.deepcopy(r3["g_teksten"]["basis"]),
            "actueel": {
                "herkomst": (
                    "R4 appinstructie; werkboom na geautoriseerd gericht vervolg "
                    "(R3G3), runner verifieert SHA"
                ),
                "sha256": _sha(actueel.encode("utf-8")),
            },
        },
        "herkomst": {
            "bronnen": {
                "r3": {
                    "pad": str(G_R3.relative_to(PROJECT_ROOT)),
                    "sha256": G_R3_SHA256,
                },
                "r2": {
                    "pad": str(G_R2.relative_to(PROJECT_ROOT)),
                    "sha256": G_R2_SHA256,
                },
            },
            "bron_pad_aanroep": bron_pad,
            "plan": [{"id": n, "bron": b, "oorsprong_id": o} for n, b, o in G_PLAN],
            "ontwikkel_ids": {n: o for n, _, o in G_PLAN if n != o},
            "bewerking": (
                "invoeren en basis-G-tekst exact gekopieerd; alleen het id van de "
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
    eindset, selectie_bron = T_EINDSET.read_bytes(), T_SELECTIE.read_bytes()
    selectie = maak_t_selectie(eindset, selectie_bron, bron_pad="standaard")
    controleer_t_selectie(selectie, eindset, selectie_bron)
    g = maak_g_invoer(G_R3.read_bytes(), G_R2.read_bytes(), bron_pad="standaard")
    t_sha = _schrijf(args.t_doel, selectie)
    g_sha = _schrijf(args.g_doel, g)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n{args.g_doel} sha256={g_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
