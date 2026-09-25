"""Begrensde trace van de T/G-promptketen in een vers proces (DEF-768 R2-OC-01).

Testhulp (geen testmodule): `test_def768_r2_manifestcorrectie.py` start dit
script als subprocess, zodat profiler en open-spion vóór elke projectimport
actief zijn. Uitvoer: JSON op stdout.

Promptketen = (a) projectbestanden waarvan een functie (geen modulebody) wordt
aangeroepen tijdens de promptbouw, (b) elke uitgevoerde module onder
src/services/prompts/, (c) gelezen databestanden onder src/ en config/, en (d)
directe projectimports (AST) van de modules uit (b). Alleen src/ en config/.
Geen netwerk, geen model.
"""

from __future__ import annotations

import ast
import builtins
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
functies: set[str] = set()
modules: set[str] = set()
geopend: set[str] = set()
_actief = False


def _rel(pad: str) -> str | None:
    if pad.startswith("<"):
        return None
    try:
        p = Path(pad).resolve()
    except (OSError, ValueError):
        return None
    if ROOT in p.parents:
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("src/", "config/")):
            return rel
    return None


def _profiel(frame, event, arg):
    if event != "call":
        return
    rel = _rel(frame.f_code.co_filename)
    if not rel:
        return
    if frame.f_code.co_name == "<module>":
        modules.add(rel)
    elif _actief:
        functies.add(rel)


_open, _io_open = builtins.open, io.open


def _spion_open(file, *a, **k):
    if _actief and isinstance(file, str | Path):
        rel = _rel(str(file))
        if rel:
            geopend.add(rel)
    return _open(file, *a, **k)


builtins.open = _spion_open
io.open = _spion_open
sys.setprofile(_profiel)

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import asyncio
import json

import proefinvoer as pi


async def _bouw() -> None:
    global _actief
    from services.validation.ess05_assessment_service import laad_ess05_norm
    from toetsregels.rule_cache import get_rule_cache

    _actief = True  # het legen van de regelcache hoort bij de keten
    get_rule_cache().clear_cache()
    g = json.loads(
        (ROOT / "tests/fixtures/ess05/g_invoer_v2.json").read_text(encoding="utf-8")
    )
    for invoer in g["invoeren"]:
        await pi.bouw_g_prompt(invoer)
    pi.huidige_g_instructie()
    norm = laad_ess05_norm()
    t = json.loads(
        (ROOT / "tests/fixtures/ess05/ontwikkelgevallen_v1.json").read_text(
            encoding="utf-8"
        )
    )
    for geval in t["gevallen"]:
        pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
    _actief = False


asyncio.run(_bouw())
sys.setprofile(None)
builtins.open, io.open = _open, _io_open


def _resolve(naam: str) -> str | None:
    mod = (ROOT / "src").joinpath(*naam.split("."))
    for kandidaat in (mod.with_suffix(".py"), mod / "__init__.py"):
        if kandidaat.is_file():
            return kandidaat.relative_to(ROOT).as_posix()
    return None


prompts = {m for m in modules | functies if m.startswith("src/services/prompts/")}
statisch: set[str] = set()
for bron in prompts:
    for knoop in ast.walk(ast.parse((ROOT / bron).read_text("utf-8"))):
        namen: list[str] = []
        if isinstance(knoop, ast.ImportFrom) and knoop.module and knoop.level == 0:
            namen = [knoop.module] + [f"{knoop.module}.{a.name}" for a in knoop.names]
        elif isinstance(knoop, ast.Import):
            namen = [a.name for a in knoop.names]
        statisch.update(p for n in namen if (p := _resolve(n)))

import run_ess05_proef as runner

gedekt = set(runner.codemanifest()) | set(runner.BUITEN_CODEMANIFEST)
keten = functies | prompts | geopend | statisch
print(
    json.dumps(
        {
            "keten": sorted(keten),
            "niet_in_manifest": sorted(keten - gedekt),
            "alleen_statisch": sorted(statisch - functies - prompts - geopend),
        },
        indent=1,
        ensure_ascii=False,
    )
)
