"""DEF-770 T24-uitvoerhelper (runplan-t24-g24-v3 §2) — observeert, oordeelt niet.

Per variant één aanroep, tegen een exacte `git archive`-tar van die commit:

    <venv-python> -B t24_uitvoer.py --repo <bron.tar> --input <gevallen.json> \\
        --output <nieuw.json> [--werkmap <nieuwe map>] [--verwachte-commit <sha>]

Invoer: JSON-lijst van gevallen met precies de sleutels
id, stratum, begrip, tekst, herkomst, rationale. De tekst gaat ongewijzigd
naar de service en de opslag; `herkomst` en `rationale` worden alleen
doorgeschreven. Er is geen verwacht label en er wordt niets gescoord.

Per geval en per laadpad (ToetsregelManager, CachedToetsregelManager), via
`ModularValidationService(manager, None, None).validate_definition` zoals
proef-na-implementatie-v3: de ruwe INT-01-uitkomst (rule_statuses,
rule_results met onderdelen, evidence, positie en reden), INT-01 in
passed_rules, INT-01-violations en -review_required en de dekking. Daarna de
gewone repositoryroute op een verse sqlite per geval: `create_definitie` en
teruglezen met een nieuwe repository. Ontbreekt iets in een variant (bijv.
`get_int01_beoordeling` in de oude), dan staat er "niet aanwezig"; een
uitzondering wordt als type + boodschap vastgelegd, niet opgevangen tot een
uitkomst.

Offline: de offline-gate uit de uitgepakte boom staat aan vóór de eerste
applicatie-import (netwerk, dotenv en databases buiten de sessie geweigerd;
dummy-keys). Er wordt geen model aangeroepen.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import effectproef_bron as eb

VELDEN = ("id", "stratum", "begrip", "tekst", "herkomst", "rationale")
REGEL = "INT-01"
MODULES = (
    "tests.offline_bootstrap",
    "services.validation.modular_validation_service",
    "toetsregels.manager",
    "toetsregels.cached_manager",
    "database.definitie_repository",
    "database.models",
    "domain.int01.zinsgrenzen",
    "domain.int01.opslag",
    "services.validation.evaluators.sentence_boundary",
)


def lees_gevallen(pad: Path) -> list[dict[str, str]]:
    gevallen = json.loads(pad.read_text(encoding="utf-8"))
    if not isinstance(gevallen, list) or not gevallen:
        raise SystemExit("invoer moet een niet-lege JSON-lijst zijn")
    gezien: set[str] = set()
    for i, g in enumerate(gevallen):
        if not isinstance(g, dict) or set(g) != set(VELDEN):
            raise SystemExit(f"geval {i}: sleutels moeten exact {VELDEN} zijn")
        if not all(isinstance(g[v], str) for v in VELDEN):
            raise SystemExit(f"geval {i}: alle velden moeten tekst zijn")
        if g["id"] in gezien:
            raise SystemExit(f"geval {i}: dubbel id {g['id']!r}")
        gezien.add(g["id"])
    return gevallen


def _fout(exc: BaseException) -> dict[str, str]:
    return {
        "type": type(exc).__name__,
        "boodschap": str(exc),
        "traceback_laatste_regel": traceback.format_exc().strip().splitlines()[-1],
    }


def _is_int01(item: Any) -> bool:
    return isinstance(item, dict) and REGEL in (item.get("rule_id"), item.get("code"))


def int01_uit_resultaat(res: dict[str, Any]) -> dict[str, Any]:
    """Alleen doorgeven wat de service teruggeeft; ontbreken heet ontbreken."""
    statussen = res.get("rule_statuses")
    resultaten = res.get("rule_results")
    return {
        "contractversie": res.get("version", eb.NIET_AANWEZIG),
        "rule_status": (
            statussen.get(REGEL, eb.NIET_AANWEZIG)
            if isinstance(statussen, dict)
            else eb.NIET_AANWEZIG
        ),
        "rule_result": (
            resultaten.get(REGEL, eb.NIET_AANWEZIG)
            if isinstance(resultaten, dict)
            else eb.NIET_AANWEZIG
        ),
        "in_passed_rules": REGEL in (res.get("passed_rules") or []),
        "violations_int01": [v for v in res.get("violations") or [] if _is_int01(v)],
        "review_required_int01": (
            [r for r in res["review_required"] if _is_int01(r)]
            if isinstance(res.get("review_required"), list)
            else eb.NIET_AANWEZIG
        ),
        "evaluation_coverage": res.get("evaluation_coverage", eb.NIET_AANWEZIG),
        "is_acceptable": res.get("is_acceptable", eb.NIET_AANWEZIG),
        "overall_score": res.get("overall_score", eb.NIET_AANWEZIG),
    }


async def valideer(gevallen: list[dict[str, str]]) -> list[dict[str, Any]]:
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.cached_manager import CachedToetsregelManager
    from toetsregels.manager import ToetsregelManager

    rijen = []
    for route, maak in (
        ("manager", ToetsregelManager),
        ("cache", CachedToetsregelManager),
    ):
        svc = ModularValidationService(maak(), None, None)
        for g in gevallen:
            rij: dict[str, Any] = {"id": g["id"], "laadpad": route}
            try:
                res = await svc.validate_definition(
                    begrip=g["begrip"], text=g["tekst"], context={}
                )
                rij["int01"] = int01_uit_resultaat(res)
            except Exception as exc:  # vastleggen, niet verzinnen
                rij["fout"] = _fout(exc)
            rijen.append(rij)
    return rijen


def opslag(gevallen: list[dict[str, str]], werk: Path) -> list[dict[str, Any]]:
    from database.definitie_repository import DefinitieRecord, DefinitieRepository

    rijen = []
    for i, g in enumerate(gevallen):
        pad = werk / "data" / f"geval-{i:03d}.db"  # verse sqlite per geval
        rij: dict[str, Any] = {"id": g["id"], "db": pad.name}
        try:
            did = DefinitieRepository(str(pad)).create_definitie(
                DefinitieRecord(
                    begrip=g["begrip"], definitie=g["tekst"], categorie="type"
                )
            )
            gelezen = DefinitieRepository(str(pad)).get_definitie(did)
            rij["definitie_id"] = did
            rij["teruggelezen_tekst_identiek"] = (
                gelezen is not None and gelezen.definitie == g["tekst"]
            )
            lezer = getattr(gelezen, "get_int01_beoordeling", None)
            rij["int01_beoordeling"] = lezer() if callable(lezer) else eb.NIET_AANWEZIG
        except Exception as exc:
            rij["fout"] = _fout(exc)
        rijen.append(rij)
    return rijen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", type=Path, required=True, help="git-archive-tar")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--werkmap", type=Path, help="nieuwe map (default: <output>.werk)")
    p.add_argument("--verwachte-commit")
    a = p.parse_args()

    # Alle externe paden absoluut maken vóór activeer_bron (chdir naar de
    # sessie): anders wijzen relatieve paden daarna naar de tijdelijke werkboom.
    uit = a.output.resolve()
    invoer = a.input.resolve()
    repo = a.repo.resolve()
    werkmap = (a.werkmap or uit.with_name(uit.name + ".werk")).resolve()
    if uit.exists():
        raise SystemExit(f"{uit} bestaat al; kies een nieuwe naam")
    invoer_bytes = invoer.read_bytes()
    gevallen = lees_gevallen(invoer)
    binding = eb.bronbinding(repo, a.verwachte_commit)

    werkmap.mkdir(exist_ok=False)
    bron = werkmap / "bron"
    uitpak = eb.pak_uit(repo, bron)
    offline = eb.activeer_bron(bron, werkmap / "sessie")
    logging.disable(logging.CRITICAL)

    service = asyncio.run(valideer(gevallen))
    opgeslagen = opslag(gevallen, Path.cwd())
    rapport = {
        "soort": "DEF-770 T24 uitvoer (observatie, geen labels of scores)",
        "script_sha256": eb.sha256_bestand(Path(__file__).resolve()),
        "helper_sha256": eb.sha256_bestand(Path(eb.__file__).resolve()),
        "python": sys.version,
        "bron": {
            **binding,
            **uitpak,
            "sleutelbestanden_sha256": eb.sleutelhashes(bron),
        },
        "moduleherkomst": eb.herkomstcontrole(bron, MODULES),
        "offline_gate_actief": offline.gate_is_actief(),
        "invoer": {
            "pad": str(invoer),
            "sha256": eb.sha256_bytes(invoer_bytes),
            "aantal": len(gevallen),
        },
        "gevallen": gevallen,
        "service": service,
        "opslag": opgeslagen,
        "fouten": sum("fout" in r for r in service + opgeslagen),
    }
    digest = eb.schrijf_nieuw(uit, rapport)
    print(f"uitvoer {uit}")
    print(f"sha256 {digest}")
    print(f"commit {binding['commit']} fouten {rapport['fouten']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
