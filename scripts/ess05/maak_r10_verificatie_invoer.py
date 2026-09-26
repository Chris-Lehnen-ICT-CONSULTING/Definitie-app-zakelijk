"""DEF-768 R10 — verifier-only-invoer V7: zes R8-controles plus het R9-C5-concept.

Besluit Chris 26-09 (`logs/def768/ronde10-herproefgoedkeuring-v1.json`) op
`logs/def768/bewijsherstel-vervolgproef-voorstel-v1.md`. Regels (fail-closed,
geen reparatie, geen herlabeling):

- **zes R8-items** — uit de bevroren R8-invoer (gepinde hash). Elk item wordt
  met dezelfde itembouw als de migratie (`migreer_r7_naar_v2.invoeritem`)
  opnieuw gebonden aan de huidige code; alleen `verificatieprompt_sha256` mag
  daarbij veranderen (verify/3). Geval, materiaal, concept, controles, soort,
  foutdragers en bron blijven exact die van R8;
- **V-N4** — het ongewijzigde concept uit het echte R9-callrecord (R720,
  gepinde hash), met het geval exact uit de R9-ontwikkelselectie. De code leidt
  het concept opnieuw af uit het bewaarde ruwe antwoord (`valideer_antwoord`)
  en weigert elke afwijking van het bewaarde concept, de concepthash of de
  materiaalhashes. Foutdrager is `claim:C5` (inference op C1 en C4 met de
  deelzin over het gedeelde eindpunt), volgens de onafhankelijke
  inhoudscontrole en het inhoudelijke stopbesluit (beide op hash gepind).

    .venv/bin/python scripts/ess05/maak_r10_verificatie_invoer.py [--doel P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import migreer_r7_naar_v2 as mig
import proefinvoer as pi

R8_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R8"
R9_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R9"
R10_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R10"
R8_VINVOER = R8_MAP / "verificatie-invoer-v1.json"
R8_VINVOER_SHA256 = "ddece7dbbdf928be8c89aca819e110ea0e8ad6e45aaf6ce582fe27c7528d155c"
R9_CALLRECORD = (
    R9_MAP
    / "ontwikkeling-20260926T055126989046Z"
    / "calls"
    / "001-ontwikkeling-R720.json"
)
R9_CALLRECORD_SHA256 = (
    "8995634a5615828a03300b8274fc535ffe49ca1f64b2badd71ccffeb6c7a0a8c"
)
R9_SELECTIE = R9_MAP / "ontwikkelselectie-v1.json"
R9_SELECTIE_SHA256 = "4e11ebe579ba9852217951fdf21466dc3131f2ba925f49fb7114b242eef3439d"
INHOUDSCONTROLE = (
    PROJECT_ROOT / "logs" / "def768" / "ronde9-r720-inhoudscontrole-result-v1.md"
)
INHOUDSCONTROLE_SHA256 = (
    "e520ee2aed691ac9b3aef23224688e31ef15e8cbef40f7d53c029dc18abc6b80"
)
STOPBESLUIT = R9_MAP / "inhoudelijke-stop-v1.json"
STOPBESLUIT_SHA256 = "0766cbbede67808e733f73b99a44e28586f76b82db6e80b75f64da985f03d23b"
DOEL = R10_MAP / "verificatie-invoer-v1.json"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
N4_ID = "V-N4"
N4_FOUTDRAGER = "claim:C5"
#: De vastgestelde fout (inhoudscontrole): C5 volgt uit C1 en C4, maar stelt ook
#: dit; de premissen dragen die deelzin niet.
_N4_CLAIM, _N4_PREMISSEN = "C5", ["C1", "C4"]
_N4_DEELZIN = "het gedeelde eindpunt op de oorspronkelijke laadplaats grenst niets af"
_PROMPTVELD = "verificatieprompt_sha256"


class MakerfoutError(RuntimeError):
    """Bron of afleiding voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _rel(pad: Path) -> str:
    return str(Path(pad).resolve().relative_to(PROJECT_ROOT))


def _gepind(pad: Path, verwacht: str, naam: str) -> bytes:
    try:
        inhoud = Path(pad).read_bytes()
    except OSError as exc:
        msg = f"{naam} {pad} ontbreekt of is onleesbaar: {exc}"
        raise MakerfoutError(msg) from exc
    if _sha(inhoud) != verwacht:
        msg = f"{naam} {Path(pad).name} wijkt af van de gepinde hash {verwacht}"
        raise MakerfoutError(msg)
    return inhoud


def _contract() -> dict[str, str]:
    from domain.ess05 import bewijs
    from services.validation.ess05_assessment_service import Ess05AssessmentService
    from services.validation.ess05_verification_service import (
        Ess05VerificationService,
    )

    return {
        "prompt_version": Ess05AssessmentService.PROMPT_VERSION,
        "verification_prompt_version": Ess05VerificationService.PROMPT_VERSION,
        "answer_schema_version": bewijs.ANTWOORDSCHEMA,
        "concept_schema_version": bewijs.CONCEPTSCHEMA,
        "verification_schema_version": bewijs.VERIFICATIESCHEMA,
    }


def herbind_r8_item(item: Mapping[str, Any], norm: Mapping[str, str]) -> dict:
    """Eén R8-item, opnieuw gebonden: alleen de verificatieprompthash mag wijzigen."""
    nieuw = mig.invoeritem(
        item["id"],
        item["soort"],
        item["geval"],
        item["concept"],
        item["foutdragende_items"],
        item["bron"],
        norm,
    )
    if list(nieuw) != list(item) or any(
        nieuw[k] != item[k] for k in item if k != _PROMPTVELD
    ):
        msg = f"{item['id']}: herbinding wijzigt meer dan {_PROMPTVELD}"
        raise MakerfoutError(msg)
    uit = dict(item)
    uit[_PROMPTVELD] = nieuw[_PROMPTVELD]
    return uit


def historisch_oordeel(
    doc: Mapping[str, Any], foutdrager: str = N4_FOUTDRAGER
) -> dict[str, Any]:
    """Het echte verifieroordeel over de foutdrager, ongewijzigd (geen herlabeling)."""
    checks = [c for c in doc["verification"]["checks"] if c.get("item") == foutdrager]
    if len(checks) != 1:
        msg = f"geen eenduidig historisch verifieroordeel over {foutdrager}"
        raise MakerfoutError(msg)
    return {
        "item": foutdrager,
        "outcome": checks[0]["outcome"],
        "finding": checks[0].get("finding"),
        "verification_raw_response_sha256": doc["verification_raw_response_sha256"],
    }


def herafgeleid_concept(
    record: Mapping[str, Any],
    geval: Mapping[str, Any],
    norm: Mapping[str, str],
    ronde: str,
) -> dict[str, Any]:
    """Het bewaarde concept van een echt callrecord, alleen na exacte herafleiding.

    Ruw antwoord, geval en materiaal moeten bij de vastgelegde hashes horen, en
    de afleiding uit het ruwe antwoord moet exact het bewaarde concept en zijn
    hash opleveren; anders geen item (geen reparatie). De echte R9/R10-
    antwoorden zijn historisch `ess05-answer/1`: de afleiding gebruikt die
    vastgelegde versie expliciet, nooit het actuele antwoordschema.
    """
    from domain.ess05.bewijs import ANTWOORDSCHEMA_1
    from domain.ess05.contract import valideer_antwoord

    doc = record["beoordelingsdocument"]
    ruw = record["ruw_antwoord"]
    afleiding = doc["concept_derivation"]
    if afleiding.get("answer_schema_version") != ANTWOORDSCHEMA_1:
        msg = f"{ronde}: de afleiding is geen historisch {ANTWOORDSCHEMA_1}-antwoord"
        raise MakerfoutError(msg)
    if not (
        _sha(ruw)
        == record["ruw_antwoord_sha256"]
        == doc["raw_response_sha256"]
        == afleiding["raw_response_sha256"]
    ):
        msg = f"{ronde}: het ruwe antwoord hoort niet bij de vastgelegde hashes"
        raise MakerfoutError(msg)
    if pi.sha_json(geval) != record["geval_sha256"]:
        msg = f"{ronde}: het geval uit de ontwikkelselectie is niet dat van het callrecord"
        raise MakerfoutError(msg)
    materiaal, buren, _ = mig.verificatiemateriaal(geval, norm)
    if {m: _sha(t) for m, t in materiaal.items()} != afleiding["material"]:
        msg = f"{ronde}: het materiaal wijkt af van de materiaalhashes van de afleiding"
        raise MakerfoutError(msg)
    afgeleid, fouten = valideer_antwoord(
        json.loads(ruw), materiaal, buren, schema=ANTWOORDSCHEMA_1
    )
    concept = doc["concept"]
    if (
        afgeleid is None
        or afgeleid.data != concept
        or afgeleid.hash != afleiding["concept_hash"]
    ):
        msg = f"{ronde}: het bewaarde concept is niet de afleiding uit het ruwe antwoord ({fouten})"
        raise MakerfoutError(msg)
    return concept


def n4_item(
    record: Mapping[str, Any],
    geval: Mapping[str, Any],
    bron: Mapping[str, Any],
    norm: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """V-N4: het bewaarde R9-concept, alleen na exacte herafleiding uit het ruwe antwoord."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    norm = laad_ess05_norm() if norm is None else norm
    concept = herafgeleid_concept(record, geval, norm, "R9")
    c5 = [c for c in concept["claims"] if c["id"] == _N4_CLAIM]
    if (
        len(c5) != 1
        or c5[0]["role"] != "inference"
        or c5[0]["premises"] != _N4_PREMISSEN
        or _N4_DEELZIN not in c5[0]["text"]
    ):
        msg = (
            f"R9: {_N4_CLAIM} is niet de vastgestelde gevolgtrekking op {_N4_PREMISSEN}"
        )
        raise MakerfoutError(msg)
    return mig.invoeritem(N4_ID, "fout", geval, concept, [N4_FOUTDRAGER], bron, norm)


def maak_verificatie_invoer(
    *,
    r8_vinvoer: Path = R8_VINVOER,
    callrecord: Path = R9_CALLRECORD,
    selectie: Path = R9_SELECTIE,
    inhoudscontrole: Path = INHOUDSCONTROLE,
    stopbesluit: Path = STOPBESLUIT,
) -> dict[str, Any]:
    """V7: zes opnieuw gebonden R8-items en V-N4, met bron- en hashbinding."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    r8 = json.loads(_gepind(r8_vinvoer, R8_VINVOER_SHA256, "R8-V-invoer"))
    record = json.loads(_gepind(callrecord, R9_CALLRECORD_SHA256, "R9-callrecord"))
    gevallen = json.loads(
        _gepind(selectie, R9_SELECTIE_SHA256, "R9-ontwikkelselectie")
    )["gevallen"]
    _gepind(inhoudscontrole, INHOUDSCONTROLE_SHA256, "inhoudscontrole")
    _gepind(stopbesluit, STOPBESLUIT_SHA256, "stopbesluit")
    if r8.get("schema") != mig.INVOERSCHEMA or len(r8.get("items") or []) != 6:
        msg = f"R8-V-invoer heeft niet het schema {mig.INVOERSCHEMA} met zes items"
        raise MakerfoutError(msg)
    if len(gevallen) != 1 or gevallen[0].get("id") != record.get("geval_id"):
        msg = "R9-ontwikkelselectie bevat niet uitsluitend het geval van het callrecord"
        raise MakerfoutError(msg)
    norm = laad_ess05_norm()
    doc = record["beoordelingsdocument"]
    bron = {
        "callrecord": _rel(R9_CALLRECORD),
        "callrecord_sha256": R9_CALLRECORD_SHA256,
        "sleutel": record["sleutel"],
        "seq": record["seq"],
        "ruw_antwoord": record["ruw_antwoord"],
        "ruw_antwoord_sha256": record["ruw_antwoord_sha256"],
        "prompt_version": doc["prompt_version"],
        "verification_prompt_version": doc["verification_prompt_version"],
        "concept_derivation": doc["concept_derivation"],
        "historisch_verifieroordeel": historisch_oordeel(doc),
        "ontwikkelselectie": {"pad": _rel(R9_SELECTIE), "sha256": R9_SELECTIE_SHA256},
        "inhoudscontrole": {
            "pad": _rel(INHOUDSCONTROLE),
            "sha256": INHOUDSCONTROLE_SHA256,
        },
        "inhoudelijke_stop": {"pad": _rel(STOPBESLUIT), "sha256": STOPBESLUIT_SHA256},
    }
    items = [herbind_r8_item(item, norm) for item in r8["items"]]
    items.append(n4_item(record, gevallen[0], bron, norm))
    return {
        "schema": mig.INVOERSCHEMA,
        "status": (
            "verifier-only-invoer R10 (V7): zes R8-items ongewijzigd behalve "
            f"{_PROMPTVELD} (verify/3); {N4_ID} is het ongewijzigde R9-R720-concept "
            f"met foutdrager {N4_FOUTDRAGER} volgens de onafhankelijke inhoudscontrole"
        ),
        "herkomst": {
            "r8_verificatie_invoer": {
                "pad": _rel(R8_VINVOER),
                "sha256": R8_VINVOER_SHA256,
                "herkomst": r8["herkomst"],
            },
            "regels": "scripts/ess05/maak_r10_verificatie_invoer.py (moduledocstring)",
            "contract": _contract(),
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
    sys.stdout.write(f"{args.doel} sha256={_sha(tekst)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
