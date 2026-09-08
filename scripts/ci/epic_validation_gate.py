#!/usr/bin/env python3
"""Fail-closed EPIC/US-validatiegate (DEF-665).

De inline shellstappen in `epic-validation.yml` waren leeg-groen: zonder
treffers laat bash de literal glob staan, `[ -f "$file" ]` is onwaar, de lus doet
niets en de stap meldt `✅` met status 0. De ID-controle onderdrukte bovendien de
fout van `grep` bij nul bestanden, en de rapportstap schreef drie vinkjes los van
de werkelijke uitkomsten.

Deze gate meet in plaats daarvan. Beide scopes zijn verplicht en moeten
werkelijke, reguliere bestanden binnen de root bevatten; de frontmatter wordt
echt als YAML geparseerd; alle vijf de verplichte velden moeten een niet-lege
waarde hebben; ID's moeten uniek zijn en elke story moet naar een bestaande epic
verwijzen.

Publiek contract:
    exit 0 = beide scopes gevuld en alles geldig
    exit 1 = geldige scan met bevindingen
    exit 2 = ongeldige scan (ontbrekende of lege scope, onleesbaar bestand,
             misvormde frontmatter) — nooit stil groen

Belangrijk: in de huidige repository bestaat `docs/epics/` wel, maar staat er
geen enkel `EPIC-*.md` in (alleen een implementatiegids), en ontbreekt
`docs/stories/` volledig. De juiste, eerlijke uitkomst is hier dus exit 2 met
reden `epics_scope_empty`. Die wordt niet weggeschreven met een uitzondering of
verzonnen planningsdata; of die scope er hoort te zijn, is een openstaande
beleidskeuze en geen zaak van deze gate.

Stdout draagt precies één JSON-document met metadata: root, tellingen, status,
reden en de bevindingen (soort, pad, veld). Géén frontmatterwaarden — ook geen
ID's of epic-verwijzingen, want dat zijn vrije velden die van alles kunnen
bevatten. ID's worden uitsluitend intern vergeleken. Nooit bestandsinhoud, nooit
een rauwe exceptie of traceback.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn

import yaml

ROOT = Path(__file__).resolve().parents[2]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INVALID = 2

EPIC_MAP = "docs/epics"
EPIC_PATROON = "EPIC-*.md"
STORY_MAP = "docs/stories"
STORY_PATROON = "US-*.md"

#: Exact de velden uit de oorspronkelijke workflow.
EPIC_VELDEN = ("id", "title", "status", "owner", "priority")
STORY_VELDEN = ("id", "epic", "title", "status", "priority")


class GateError(Exception):
    """Ongeldige scan; draagt uitsluitend een vaste, veilige reden."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _ongeldig(reden: str) -> NoReturn:
    raise GateError(reden)


def _scope(submap: str, patroon: str, missend: str, leeg: str) -> list[Path]:
    """Werkelijke, niet-lege lijst reguliere bestanden binnen de root."""
    map_ = ROOT / submap
    if map_.is_symlink() or not map_.is_dir():
        _ongeldig(missend)
    try:
        paden = sorted(
            pad for pad in map_.glob(patroon) if pad.is_file() and not pad.is_symlink()
        )
    except OSError:
        _ongeldig("scope_unreadable")
    if not paden:
        _ongeldig(leeg)

    wortel = ROOT.resolve()
    for pad in paden:
        try:
            echt = pad.resolve(strict=True)
        except OSError:
            _ongeldig("scope_unreadable")
        if wortel not in echt.parents:
            _ongeldig("scope_escape")
    return paden


def _lees(pad: Path) -> str:
    try:
        return pad.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        _ongeldig("unreadable")


def _frontmatter(tekst: str) -> dict:
    """Parseer de YAML-frontmatter; elke afwijking is een ongeldige scan."""
    regels = tekst.splitlines()
    if not regels or regels[0].strip() != "---":
        _ongeldig("frontmatter_missing")

    blok = None
    for index in range(1, len(regels)):
        if regels[index].strip() == "---":
            blok = "\n".join(regels[1:index])
            break
    if blok is None:
        _ongeldig("frontmatter_unterminated")

    try:
        data = yaml.safe_load(blok)
    except yaml.YAMLError:
        _ongeldig("frontmatter_invalid")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        _ongeldig("frontmatter_invalid")
    return data


def _ontbrekende_velden(data: dict, vereist: tuple[str, ...]) -> list[str]:
    """Een veld telt alleen mee met een niet-lege waarde."""
    return [
        veld
        for veld in vereist
        if data.get(veld) is None or not str(data[veld]).strip()
    ]


def _bevinding(kind: str, pad: str, veld: str) -> dict:
    """Alleen soort, pad en veldnaam; nooit de waarde uit de frontmatter."""
    return {"kind": kind, "path": pad, "field": veld}


def _verzamel(
    paden: list[Path],
    vereist: tuple[str, ...],
    bevindingen: list[dict],
) -> tuple[list[str], list[dict]]:
    """Lees één scope; geef de unieke ID's plus de gelezen frontmatter terug."""
    ids: list[str] = []
    gezien: set[str] = set()
    documenten: list[dict] = []
    for pad in paden:
        relatief = pad.relative_to(ROOT).as_posix()
        data = _frontmatter(_lees(pad))
        documenten.append({"path": relatief, "data": data})

        ontbreekt = _ontbrekende_velden(data, vereist)
        for veld in ontbreekt:
            bevindingen.append(_bevinding("missing_field", relatief, veld))
        if "id" in ontbreekt:
            continue

        waarde = str(data["id"]).strip()
        if waarde in gezien:
            bevindingen.append(_bevinding("duplicate_id", relatief, "id"))
            continue
        gezien.add(waarde)
        ids.append(waarde)
    return ids, documenten


def _draai(staat: dict) -> None:
    epics = _scope(EPIC_MAP, EPIC_PATROON, "epics_scope_missing", "epics_scope_empty")
    staat["counts"]["epics"] = len(epics)
    stories = _scope(
        STORY_MAP, STORY_PATROON, "stories_scope_missing", "stories_scope_empty"
    )
    staat["counts"]["stories"] = len(stories)

    bevindingen: list[dict] = staat["findings"]
    # De ID's blijven bewust lokaal: ze worden hier vergeleken, maar verlaten de
    # gate niet — het zijn vrije frontmatterwaarden.
    epic_ids, _ = _verzamel(epics, EPIC_VELDEN, bevindingen)
    _, storydocumenten = _verzamel(stories, STORY_VELDEN, bevindingen)

    bekend = set(epic_ids)
    for document in storydocumenten:
        verwijzing = document["data"].get("epic")
        if verwijzing is None or not str(verwijzing).strip():
            continue
        if str(verwijzing).strip() not in bekend:
            bevindingen.append(
                _bevinding("unknown_epic_reference", document["path"], "epic")
            )


def _publiceer(staat: dict, status: str, code: int, reden: str | None) -> int:
    """Precies één JSON-document op stdout; nooit een vals succes."""
    rapport = {
        "gate": "epic-validation",
        "status": status,
        "exit_code": code,
        "reason": reden,
        "root": str(ROOT),
        "counts": staat["counts"],
        "findings": staat["findings"],
    }
    print(json.dumps(rapport, indent=2, sort_keys=True, ensure_ascii=True))
    return code


def main() -> int:
    staat: dict = {"counts": {"epics": 0, "stories": 0}, "findings": []}
    try:
        _draai(staat)
    except GateError as fout:
        return _publiceer(staat, "invalid", EXIT_INVALID, fout.reason)
    except Exception:
        # Buitengrens: wat hier ontsnapt kan bestandsinhoud dragen, dus alleen
        # de vaste reden naar buiten — nooit een traceback.
        return _publiceer(staat, "invalid", EXIT_INVALID, "unexpected_failure")

    if staat["findings"]:
        return _publiceer(staat, "findings", EXIT_FINDINGS, None)
    return _publiceer(staat, "ok", EXIT_OK, None)


if __name__ == "__main__":
    sys.exit(main())
