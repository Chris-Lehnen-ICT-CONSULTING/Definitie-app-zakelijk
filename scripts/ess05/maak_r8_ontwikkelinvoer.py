"""DEF-768 ronde 8 — T-ontwikkelselectie vóór betaalde calls (ADR-003-keten).

Leidende rootcorrectie op livevervolg-proefvoorstel-technisch-v1 §3: de
ontwikkelpoort draait op drie R7-eindgevallen, elk met beide modelstappen
(conceptoordeel en semantische verificatie): R720, R715 en R717, exact uit de
R7-eindset. Bron, labels en intentie ongewijzigd; geen parafrase, geen
tuning, geen duplicaten.

Bekende ontwikkeldata, geen onafhankelijke gold.

    .venv/bin/python scripts/ess05/maak_r8_ontwikkelinvoer.py [--t-doel PAD]

Het doel wordt nooit overschreven; de bronhash moet exact de vastgelegde zijn.
"""

from __future__ import annotations

import argparse
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

R7_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R7"
R8_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R8"
#: Bron (alleen lezen) met vastgelegde hash.
T_R7 = R7_MAP / "onafhankelijke-eindset-v1.json"
T_R7_SHA256 = "9b239e2c1b462f1e2235f9085ff85b82b5957506389d7db2f9b8b841692ee31b"
T_DOEL = R8_MAP / "ontwikkelselectie-v1.json"
#: De ontwikkelgevallen in vastgelegde volgorde (rootcorrectie).
T_PLAN = ("R720", "R715", "R717")
T_SCHEMA = "def768-r8-ontwikkelselectie/1"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = (
    "DEF-768 livevervolg (opdracht integratie en gesloten proefvoorbereiding, "
    "25-09): ontwikkelpoort op R720, R715 en R717, elk twee modelstappen"
)
T_STATUS = (
    "bekende ontwikkeldata: drie diagnostische R7-eindgevallen; geen holdout, "
    "geen acceptatieset, geen onafhankelijke gold"
)


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _per_id(r7_bytes: bytes) -> dict[str, dict[str, Any]]:
    if _sha(r7_bytes) != T_R7_SHA256:
        msg = f"R7-eindset: bronhash {_sha(r7_bytes)} is niet de vastgelegde {T_R7_SHA256}"
        raise SelectiefoutError(msg)
    return {g["id"]: g for g in json.loads(r7_bytes)["gevallen"]}


def maak_t_selectie(r7_bytes: bytes, *, bron_pad: str) -> dict[str, Any]:
    """Drie ontwikkelgevallen, elk exact het bronrecord."""
    bron = _per_id(r7_bytes)
    ontbrekend = [i for i in T_PLAN if i not in bron]
    if ontbrekend:
        msg = f"selectie ongeldig (ontbrekend {ontbrekend})"
        raise SelectiefoutError(msg)
    return {
        "schema": T_SCHEMA,
        "status": T_STATUS,
        "herkomst": {
            "bronnen": {
                "r7": {
                    "pad": str(T_R7.relative_to(PROJECT_ROOT)),
                    "sha256": T_R7_SHA256,
                }
            },
            "bron_pad_aanroep": bron_pad,
            "plan": list(T_PLAN),
            "bewerking": (
                "elk geval byte-voor-byte gelijk aan het bronrecord als JSON; "
                "inhoud, labels en id ongewijzigd"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [json.loads(json.dumps(bron[i])) for i in T_PLAN],
    }


def controleer_t_selectie(selectie: dict[str, Any], r7_bytes: bytes) -> None:
    """Elk geval exact gelijk aan zijn bron, zonder lek in de instructie."""
    bron = _per_id(r7_bytes)
    if [g["id"] for g in selectie["gevallen"]] != list(T_PLAN):
        msg = "volgorde of ids van de gevallen wijken af van het plan"
        raise SelectiefoutError(msg)
    for geval in selectie["gevallen"]:
        if json.dumps(geval, sort_keys=True) != json.dumps(
            bron[geval["id"]], sort_keys=True
        ):
            msg = f"{geval['id']} wijkt af van zijn bronrecord"
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


def _schrijf(doel: Path, data: dict[str, Any]) -> str:
    tekst = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    return _sha(tekst.encode("utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t-doel", type=Path, default=T_DOEL)
    args = p.parse_args(argv)
    if args.t_doel.exists():
        msg = f"doel bestaat al: {args.t_doel}"
        raise FileExistsError(msg)
    bron = T_R7.read_bytes()
    selectie = maak_t_selectie(bron, bron_pad="standaard")
    controleer_t_selectie(selectie, bron)
    t_sha = _schrijf(args.t_doel, selectie)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
