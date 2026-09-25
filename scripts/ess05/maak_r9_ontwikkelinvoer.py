"""DEF-768 ronde 9 — T-ontwikkelinvoer van de gerichte herproef (alleen R720).

Besluit Chris (26-09, `logs/def768/ronde9-herproefgoedkeuring-v1.json`) op
`logs/def768/offsetherstel-vervolgproef-voorstel-v1.md`: de ontwikkelpoort
bevestigt de R8-afleverfout op het geval waar hij optrad, R720, met beide
modelstappen. Het geval komt exact uit de vastgelegde R8-ontwikkelselectie;
bron, labels en intentie ongewijzigd; geen andere gevallen, geen parafrase.

Bekende ontwikkeldata, geen onafhankelijke gold.

    .venv/bin/python scripts/ess05/maak_r9_ontwikkelinvoer.py [--t-doel PAD]

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

R8_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R8"
R9_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R9"
#: Bron (alleen lezen) met vastgelegde hash: de R8-ontwikkelselectie.
BRON = R8_MAP / "ontwikkelselectie-v1.json"
BRON_SHA256 = "d07846942171801e9e31dbd6b372023e4e1ba322a024ff2354430cec1fd291f0"
T_DOEL = R9_MAP / "ontwikkelselectie-v1.json"
#: Uitsluitend het geval van de R8-afleverfout (besluit 26-09).
T_PLAN = ("R720",)
T_SCHEMA = "def768-r9-ontwikkelselectie/1"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = (
    "DEF-768 R9 (besluit Chris 26-09, ronde9-herproefgoedkeuring-v1.json): "
    "gerichte bevestiging van de R8-afleverfout op R720, twee modelstappen"
)
T_STATUS = (
    "bekende ontwikkeldata: het R8-geval R720 van de afleverfout; geen holdout, "
    "geen acceptatieset, geen onafhankelijke gold"
)


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _per_id(bron_bytes: bytes) -> dict[str, dict[str, Any]]:
    if _sha(bron_bytes) != BRON_SHA256:
        msg = (
            f"R8-selectie: bronhash {_sha(bron_bytes)} is niet de vastgelegde "
            f"{BRON_SHA256}"
        )
        raise SelectiefoutError(msg)
    return {g["id"]: g for g in json.loads(bron_bytes)["gevallen"]}


def maak_t_selectie(bron_bytes: bytes, *, bron_pad: str) -> dict[str, Any]:
    """Alleen R720, exact het bronrecord uit de R8-selectie."""
    bron = _per_id(bron_bytes)
    ontbrekend = [i for i in T_PLAN if i not in bron]
    if ontbrekend:
        msg = f"selectie ongeldig (ontbrekend {ontbrekend})"
        raise SelectiefoutError(msg)
    return {
        "schema": T_SCHEMA,
        "status": T_STATUS,
        "herkomst": {
            "bronnen": {
                "r8_selectie": {
                    "pad": str(BRON.relative_to(PROJECT_ROOT)),
                    "sha256": BRON_SHA256,
                }
            },
            "bron_pad_aanroep": bron_pad,
            "plan": list(T_PLAN),
            "bewerking": (
                "het geval byte-voor-byte gelijk aan het bronrecord als JSON; "
                "inhoud, labels en id ongewijzigd"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [json.loads(json.dumps(bron[i])) for i in T_PLAN],
    }


def controleer_t_selectie(selectie: dict[str, Any], bron_bytes: bytes) -> None:
    """Exact het plan, elk geval gelijk aan zijn bron, zonder lek in de instructie."""
    bron = _per_id(bron_bytes)
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
    bron = BRON.read_bytes()
    selectie = maak_t_selectie(bron, bron_pad="standaard")
    controleer_t_selectie(selectie, bron)
    t_sha = _schrijf(args.t_doel, selectie)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
