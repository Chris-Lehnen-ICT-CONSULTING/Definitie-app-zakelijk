"""DEF-768 R11 — verifier-only-invoer V8: V7 opnieuw gebonden plus het R10-C3-concept.

Besluit Chris 26-09 ("akkoord", `logs/def768/ronde11-herproefgoedkeuring-v1.json`)
op `logs/def768/c3-herstel-vervolgproef-voorstel-v1.md`. Regels (fail-closed,
geen reparatie, geen herlabeling):

- **zeven V7-items** — uit de bevroren R10-invoer V7 (gepinde hash): de zes
  R8-controles en V-N4 (het ongewijzigde R9-C5-concept, foutdrager
  `claim:C5`). Elk item wordt met dezelfde itembouw opnieuw gebonden aan de
  huidige code (`maak_r10_verificatie_invoer.herbind_r8_item`); alleen
  `verificatieprompt_sha256` mag daarbij veranderen (verify/4). Geval,
  materiaal, concept, controles, soort, foutdragers en bron blijven exact die
  van V7;
- **V-N5** — het ongewijzigde concept uit het echte R10-callrecord (R720,
  gepinde hash), met het geval exact uit de R9-ontwikkelselectie. De code leidt
  het concept opnieuw af uit het bewaarde ruwe antwoord en weigert elke
  afwijking (`herafgeleid_concept`). Foutdrager is `claim:C3` (materiaalclaim
  met alleen E7, die ook "onderling worden vergeleken" stelt; dat staat in de
  ongeciteerde volgende bronzin), volgens de onafhankelijke inhoudscontrole en
  het inhoudelijke stopbesluit (beide op hash gepind).

Een V-fase accepteert een fout item alleen bij een semantische weigering op
zijn foutdrager; een schemaweigering is geen detectie (`_v_acceptatie`).

    .venv/bin/python scripts/ess05/maak_r11_verificatie_invoer.py [--doel P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import maak_r10_verificatie_invoer as mk10
import migreer_r7_naar_v2 as mig
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = ["MakerfoutError", "maak_verificatie_invoer", "main", "n5_item"]

R10_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R10"
R11_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R11"
V7 = R10_MAP / "verificatie-invoer-v1.json"
V7_SHA256 = "4eee1c703894d572c5c4a32664abfc5c3203d14bcf5ba994f51e06e5abf63c4d"
R10_CALLRECORD = (
    R10_MAP
    / "ontwikkeling-20260926T104115270789Z"
    / "calls"
    / "001-ontwikkeling-R720.json"
)
R10_CALLRECORD_SHA256 = (
    "c4f8be4093eb76349c6d09ba18f25569d22c1942d907afef569b328ef245a975"
)
R9_SELECTIE = mk10.R9_SELECTIE
R9_SELECTIE_SHA256 = mk10.R9_SELECTIE_SHA256
INHOUDSCONTROLE = (
    PROJECT_ROOT / "logs" / "def768" / "ronde10-r720-inhoudscontrole-result-v1.md"
)
INHOUDSCONTROLE_SHA256 = (
    "353944a1969738b986853f6cbce858b75fbdcf93063c47958e236883c93f4fd5"
)
STOPBESLUIT = R10_MAP / "inhoudelijke-stop-v1.json"
STOPBESLUIT_SHA256 = "96093ac846be54e1e3bf7d9ebf8731fe0a6175e2692a2ef68c8dbc0ea58972c4"
DOEL = R11_MAP / "verificatie-invoer-v1.json"
AUTEUR = mk10.AUTEUR
N5_ID = "V-N5"
N5_FOUTDRAGER = "claim:C3"
#: De vastgestelde fout (inhoudscontrole): C3 citeert alleen E7, maar stelt ook
#: deze deelzin; die staat in de ongeciteerde volgende bronzin.
_N5_CLAIM, _N5_BEWIJS = "C3", ["E7"]
_N5_DEELZIN = "die onderling worden vergeleken"
_PROMPTVELD = "verificatieprompt_sha256"


def n5_item(
    record: Mapping[str, Any],
    geval: Mapping[str, Any],
    bron: Mapping[str, Any],
    norm: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """V-N5: het bewaarde R10-concept, alleen na exacte herafleiding uit het ruwe antwoord."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    norm = laad_ess05_norm() if norm is None else norm
    concept = mk10.herafgeleid_concept(record, geval, norm, "R10")
    c3 = [c for c in concept["claims"] if c["id"] == _N5_CLAIM]
    if (
        len(c3) != 1
        or c3[0]["role"] != "material"
        or c3[0]["evidence"] != _N5_BEWIJS
        or _N5_DEELZIN not in c3[0]["text"]
    ):
        msg = f"R10: {_N5_CLAIM} is niet de vastgestelde materiaalclaim op {_N5_BEWIJS}"
        raise MakerfoutError(msg)
    return mig.invoeritem(N5_ID, "fout", geval, concept, [N5_FOUTDRAGER], bron, norm)


def maak_verificatie_invoer(
    *,
    v7: Path = V7,
    callrecord: Path = R10_CALLRECORD,
    selectie: Path = R9_SELECTIE,
    inhoudscontrole: Path = INHOUDSCONTROLE,
    stopbesluit: Path = STOPBESLUIT,
) -> dict[str, Any]:
    """V8: zeven opnieuw gebonden V7-items en V-N5, met bron- en hashbinding."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    vorige = json.loads(mk10._gepind(v7, V7_SHA256, "V7"))
    record = json.loads(
        mk10._gepind(callrecord, R10_CALLRECORD_SHA256, "R10-callrecord")
    )
    gevallen = json.loads(
        mk10._gepind(selectie, R9_SELECTIE_SHA256, "R9-ontwikkelselectie")
    )["gevallen"]
    mk10._gepind(inhoudscontrole, INHOUDSCONTROLE_SHA256, "inhoudscontrole")
    mk10._gepind(stopbesluit, STOPBESLUIT_SHA256, "stopbesluit")
    if vorige.get("schema") != mig.INVOERSCHEMA or len(vorige.get("items") or []) != 7:
        msg = f"V7 heeft niet het schema {mig.INVOERSCHEMA} met zeven items"
        raise MakerfoutError(msg)
    if len(gevallen) != 1 or gevallen[0].get("id") != record.get("geval_id"):
        msg = "R9-ontwikkelselectie bevat niet uitsluitend het geval van het callrecord"
        raise MakerfoutError(msg)
    norm = laad_ess05_norm()
    doc = record["beoordelingsdocument"]
    bron = {
        "callrecord": mk10._rel(R10_CALLRECORD),
        "callrecord_sha256": R10_CALLRECORD_SHA256,
        "sleutel": record["sleutel"],
        "seq": record["seq"],
        "ruw_antwoord": record["ruw_antwoord"],
        "ruw_antwoord_sha256": record["ruw_antwoord_sha256"],
        "prompt_version": doc["prompt_version"],
        "verification_prompt_version": doc["verification_prompt_version"],
        "concept_derivation": doc["concept_derivation"],
        "historisch_verifieroordeel": mk10.historisch_oordeel(doc, N5_FOUTDRAGER),
        "ontwikkelselectie": {
            "pad": mk10._rel(R9_SELECTIE),
            "sha256": R9_SELECTIE_SHA256,
        },
        "inhoudscontrole": {
            "pad": mk10._rel(INHOUDSCONTROLE),
            "sha256": INHOUDSCONTROLE_SHA256,
        },
        "inhoudelijke_stop": {
            "pad": mk10._rel(STOPBESLUIT),
            "sha256": STOPBESLUIT_SHA256,
        },
    }
    items = [mk10.herbind_r8_item(item, norm) for item in vorige["items"]]
    items.append(n5_item(record, gevallen[0], bron, norm))
    return {
        "schema": mig.INVOERSCHEMA,
        "status": (
            "verifier-only-invoer R11 (V8): zeven V7-items ongewijzigd behalve "
            f"{_PROMPTVELD} (verify/4); {N5_ID} is het ongewijzigde R10-R720-concept "
            f"met foutdrager {N5_FOUTDRAGER} volgens de onafhankelijke inhoudscontrole"
        ),
        "herkomst": {
            "r10_verificatie_invoer": {
                "pad": mk10._rel(V7),
                "sha256": V7_SHA256,
                "herkomst": vorige["herkomst"],
            },
            "regels": "scripts/ess05/maak_r11_verificatie_invoer.py (moduledocstring)",
            "contract": mk10._contract(),
            "auteur": AUTEUR,
        },
        "items": items,
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    args = p.parse_args(argv)
    if args.doel.exists():
        msg = f"doel bestaat al: {args.doel}"
        raise FileExistsError(msg)
    invoer = maak_verificatie_invoer()
    tekst = json.dumps(invoer, ensure_ascii=False, indent=2) + "\n"
    args.doel.parent.mkdir(parents=True, exist_ok=True)
    with args.doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{args.doel} sha256={mk10._sha(tekst)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
