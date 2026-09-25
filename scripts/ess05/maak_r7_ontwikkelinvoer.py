"""DEF-768 ronde 7 — T-ontwikkelselectie vóór betaalde calls (alleen T).

Besluit Chris 25-09 (reports/DEF-768-AI-20260925-R6/uitkomst-en-vervolg-v1.md,
concreet vervolgvoorstel, 'ja'): één ontwikkelronde op bekende diagnostische
data, uitsluitend T; geen G-invoer.

- T (9): R614 tweemaal (R614 en R614-D2: dezelfde bronrecordinhoud, alleen
  een eigen technische pogingidentiteit met expliciete bronbinding in
  `ontwikkel_ids`), R610, R620, R606 uit de R6-eindset; R514, R508, R504,
  R516 uit de R5-eindset. Bron, labels en intentie ongewijzigd; geen
  parafrase, geen tuning, geen aanvullende duplicaten. Het id gaat niet naar
  het model (geen modelveld): beide R614-pogingen krijgen dezelfde modelinvoer.

Bekende ontwikkeldata, geen onafhankelijke gold.

    .venv/bin/python scripts/ess05/maak_r7_ontwikkelinvoer.py [--t-doel PAD]

Het doel wordt nooit overschreven; bronhashes moeten exact de vastgelegde zijn.
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

R5_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R5"
R6_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R6"
R7_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R7"
#: Bronnen (alleen lezen) met vastgelegde hash.
T_R6 = R6_MAP / "onafhankelijke-eindset-v1.json"
T_R6_SHA256 = "10b8b6809ff9481387f0e8a20cd4a4faff66009a30c6a9c3ea69188b7a8c585f"
T_R5 = R5_MAP / "onafhankelijke-eindset-v1.json"
T_R5_SHA256 = "83f1637f4b076e122a32d284e58b79d1b976b0cf67aae8fc2bc713ab41c99e4c"
T_DOEL = R7_MAP / "ontwikkelselectie-v1.json"

#: (ontwikkel-id, bron, oorsprong-id) in de vastgelegde volgorde.
T_PLAN = (
    ("R614", "r6", "R614"),
    ("R614-D2", "r6", "R614"),
    ("R514", "r5", "R514"),
    ("R508", "r5", "R508"),
    ("R504", "r5", "R504"),
    ("R516", "r5", "R516"),
    ("R610", "r6", "R610"),
    ("R620", "r6", "R620"),
    ("R606", "r6", "R606"),
)
_ONTWIKKEL_IDS = {nieuw: oud for nieuw, _, oud in T_PLAN if nieuw != oud}
T_SCHEMA = "def768-r7-ontwikkelselectie/1"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
BESLUIT = (
    "DEF-768 ronde 7 (R6 uitkomst-en-vervolg-v1 §concreet vervolgvoorstel, "
    "akkoord Chris 25-09)"
)
T_STATUS = (
    "bekende ontwikkeldata: diagnostische R6- en R5-eindgevallen (R614 "
    "tweemaal, R614-D2 als technische pogingidentiteit); geen holdout, geen "
    "acceptatieset, geen onafhankelijke gold"
)


class SelectiefoutError(RuntimeError):
    """Bron of uitvoer voldoet niet (fail-closed, niets geschreven)."""


def oorsprong_id(ontwikkel_id: str) -> str:
    """Het bron-id achter een ontwikkel-id (R614-D2 → R614)."""
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
    r6_bytes: bytes, r5_bytes: bytes, *, bron_pad: str
) -> dict[str, Any]:
    """Negen ontwikkelgevallen, elk exact het bronrecord (alleen id technisch)."""
    bronnen = {
        "r6": _per_id(_bron(r6_bytes, T_R6_SHA256, "R6-eindset")["gevallen"]),
        "r5": _per_id(_bron(r5_bytes, T_R5_SHA256, "R5-eindset")["gevallen"]),
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
                "r6": _bronverwijzing(T_R6, T_R6_SHA256),
                "r5": _bronverwijzing(T_R5, T_R5_SHA256),
            },
            "bron_pad_aanroep": bron_pad,
            "plan": [{"id": n, "bron": b, "oorsprong_id": o} for n, b, o in T_PLAN],
            "ontwikkel_ids": dict(_ONTWIKKEL_IDS),
            "bewerking": (
                "elk geval byte-voor-byte gelijk aan het bronrecord als JSON; "
                "inhoud en labels ongewijzigd; alleen R614-D2 draagt een eigen "
                "technisch id (oorsprong R614), dat niet naar het model gaat"
            ),
            "auteur": AUTEUR,
            "besluit": BESLUIT,
        },
        "gevallen": [_kopie(bronnen[b][o], n) for n, b, o in T_PLAN],
    }


def controleer_t_selectie(
    selectie: dict[str, Any], r6_bytes: bytes, r5_bytes: bytes
) -> None:
    """Elk geval exact gelijk aan zijn bron, zonder lek in de instructie."""
    bronnen = {
        "r6": _per_id(json.loads(r6_bytes)["gevallen"]),
        "r5": _per_id(json.loads(r5_bytes)["gevallen"]),
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
    prompts = {}
    for geval in selectie["gevallen"]:
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        pi.controleer_afscherming(geval, prompt.teksten, norm)
        prompts[geval["id"]] = prompt.sha256
    for nieuw, oud in _ONTWIKKEL_IDS.items():
        if prompts[nieuw] != prompts[oud]:
            msg = f"{nieuw}: modelinvoer wijkt af van {oud}"
            raise SelectiefoutError(msg)


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
    t_bronnen = (T_R6.read_bytes(), T_R5.read_bytes())
    selectie = maak_t_selectie(*t_bronnen, bron_pad="standaard")
    controleer_t_selectie(selectie, *t_bronnen)
    t_sha = _schrijf(args.t_doel, selectie)
    sys.stdout.write(f"{args.t_doel} sha256={t_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
