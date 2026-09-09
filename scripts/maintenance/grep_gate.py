#!/usr/bin/env python3
"""Fail-closed grep-gate voor legacy contextpatronen (DEF-665).

De vorige shell-implementatie loste de root op naar `scripts/` en las elke
niet-nul rg-status als "schoon". Een ontbrekend zoekpad (rg-status 2) werd
daardoor als groen gerapporteerd: de gate scande in de praktijk niets.

Deze implementatie draait uitsluitend op ripgrep — geen afwijkende
grep-terugval — en bewijst eerst de scope voordat er wordt gezocht:

1. de root komt uit `__file__`, nooit uit de werkmap;
2. per scope levert `rg --files --null` een NUL-afgesloten, unieke, niet-lege
   selectie van `.py`-bestanden die na resolve binnen de root en binnen de
   gevraagde scope liggen;
3. de zoekopdracht draait op precies die bestanden, zodat selectie en zoekactie
   niet uiteen kunnen lopen;
4. status en resultaat moeten elkaar bevestigen: rg-status 0 zonder treffer en
   rg-status 1 mét treffer zijn beide ongeldig, net als een stream zonder
   afsluitend `summary`-record.

Publiek contract:
    exit 0 = geldige scan, geaccepteerd
    exit 1 = geldige scan, blokkerende bevinding
    exit 2 = ongeldige scan — nooit stil groen

De uitvoer bevat uitsluitend metadata: toolversie, root, aantallen en per
blokkerende bevinding het pad, regelnummer en aantal. Nooit broncoderegels,
nooit rauwe tool-stderr en nooit een traceback.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("grep_gate_baseline.json")

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_INVALID = 2

#: `context: str` maar niet `context: list[str]`.
CONTEXT_STR = r"context\s*:\s*str(\W|$)"

#: Eén rule-id voor de handhaafde scopes, zodat de baseline in beide geldt.
ENFORCED_RULE = "context-str"

#: UI valt buiten de advisory-patronen; de suggestiestrings in context_adapter
#: zijn alleen voor het session_state-patroon een bekende bron van vals alarm.
#: De optionele repo-brede handhaving houdt bewust haar oorspronkelijke,
#: bredere scope inclusief UI.
UI_UIT = "!src/ui/**"
ADAPTER_UIT = "!src/services/context/context_adapter.py"

ADVISORY = (
    (
        "session-state-context",
        r"st\.session_state\.(juridische_context|organisatorische_context|wettelijke_basis)",
        (UI_UIT, ADAPTER_UIT),
    ),
    ("context-str-src", CONTEXT_STR, (UI_UIT,)),
    (
        "legacy-orchestrator-import",
        r"from orchestration import orchestrator",
        (UI_UIT,),
    ),
    ("context-dict-creation", r"context_dict\s*=\s*\{", (UI_UIT,)),
)

#: De volledige recordsoorten van het rg JSON-Lines-protocol.
_RECORD_SOORTEN = frozenset({"begin", "end", "match", "context", "summary"})
_BASELINE_KEYS = frozenset({"rule", "path", "line", "text", "count"})
_VERSIE_PATROON = re.compile(r"^ripgrep (\d+\.\d+(?:\.\d+)?)")
_STATS_VELDEN = (
    "searches",
    "searches_with_match",
    "bytes_searched",
    "matched_lines",
    "matches",
)
_CHUNK = 200
_TIMEOUT = 300


class GateError(Exception):
    """Ongeldige scan; draagt uitsluitend een vaste, veilige reden."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _log(bericht: str) -> None:
    print(f"grep-gate: {bericht}", flush=True)


def _child_env() -> dict[str, str]:
    """Ambient rg-configuratie mag de scope of de patronen niet verleggen."""
    env = {k: v for k, v in os.environ.items() if k != "RIPGREP_CONFIG_PATH"}
    env["LC_ALL"] = "C"
    return env


def _run(argv: list[str], reason: str) -> subprocess.CompletedProcess:
    """Vaste, begrensde aanroep; uitvoer blijft bytes tot expliciet decoderen."""
    try:
        return subprocess.run(
            argv,
            cwd=str(ROOT),
            env=_child_env(),
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise GateError(reason) from None


def _decode(rauw: bytes, reason: str) -> str:
    try:
        return rauw.decode("utf-8")
    except UnicodeDecodeError:
        raise GateError(reason) from None


def _rg_pad() -> str:
    pad = shutil.which("rg")
    if not pad:
        raise GateError("ripgrep_missing")
    return pad


def _rg_versie(rg: str) -> str:
    """Alleen een echte ripgrep-versieregel telt als bewijs van de tool.

    Er wordt uitsluitend het semantische versienummer teruggegeven; de
    resterende stdout (buildvlaggen en dergelijke) blijft buiten de log.
    """
    klaar = _run([rg, "--version"], "rg_version_failed")
    if klaar.returncode != 0:
        raise GateError("rg_version_failed")
    regels = _decode(klaar.stdout, "rg_version_decode").splitlines()
    treffer = _VERSIE_PATROON.match(regels[0].strip()) if regels else None
    if treffer is None:
        raise GateError("rg_version_invalid")
    return treffer.group(1)


def _veilig_pad(pad: str) -> bool:
    if not pad.endswith(".py") or pad.startswith(("/", "~")):
        return False
    delen = Path(pad).parts
    return bool(delen) and ".." not in delen


def _selecteer(rg: str, scope: str, globs: tuple[str, ...]) -> list[str]:
    """Bewijs de scope: NUL-afgesloten, uniek, binnen root én binnen de scope.

    De include-glob staat bewust vóór de negatieve globs: andersom zou `*.py`
    een eerder uitgesloten pad opnieuw kunnen binnenhalen.
    """
    scope_pad = ROOT / scope
    if scope_pad.is_symlink() or not scope_pad.is_dir():
        raise GateError("scope_root")

    argv = [rg, "--files", "--null", "-g", "*.py"]
    for glob in globs:
        argv += ["-g", glob]
    argv += ["--", scope]

    klaar = _run(argv, "rg_files_failed")
    if klaar.returncode not in (0, 1):
        raise GateError("rg_files_status")

    rauw = _decode(klaar.stdout, "rg_files_decode")
    if klaar.returncode == 1:
        if rauw:
            raise GateError("rg_status_mismatch")
        raise GateError("empty_selection")
    if not rauw.endswith("\0"):
        raise GateError("rg_files_truncated")

    paden = rauw.split("\0")[:-1]
    if not paden or any(not pad for pad in paden):
        raise GateError("empty_selection")
    if len(set(paden)) != len(paden):
        raise GateError("selection_duplicate")

    wortel = ROOT.resolve()
    voorvoegsel = scope.rstrip("/") + "/"
    for pad in paden:
        if not _veilig_pad(pad) or not pad.startswith(voorvoegsel):
            raise GateError("selection_path")
        try:
            echt = (ROOT / pad).resolve(strict=True)
        except OSError:
            raise GateError("selection_missing") from None
        if not echt.is_file():
            raise GateError("selection_missing")
        if wortel not in echt.parents:
            raise GateError("selection_escape")
    return sorted(paden)


def _lees_pad(record: dict, toegestaan: set[str]) -> None:
    """`begin`, `end` en `context` dragen een pad; dat moet in de brok zitten."""
    data = record.get("data")
    if not isinstance(data, dict):
        raise GateError("rg_json_schema")
    pad_veld = data.get("path")
    if not isinstance(pad_veld, dict):
        raise GateError("rg_json_schema")
    if not isinstance(pad_veld.get("text"), str) or pad_veld["text"] not in toegestaan:
        raise GateError("rg_json_path")


def _lees_summary(record: dict) -> dict[str, int]:
    """Een geldige afsluiting draagt volledige, niet-negatieve tellingen.

    Bij nul treffers zijn die tellingen legitiem allemaal nul — er wordt hier
    dus geen positieve `searches` geëist. Wat wél moet: de structuur is er en de
    getallen kloppen met wat er aan match-records langskwam.
    """
    data = record.get("data")
    if not isinstance(data, dict):
        raise GateError("rg_json_schema")
    stats = data.get("stats")
    if not isinstance(stats, dict):
        raise GateError("rg_json_schema")

    getallen: dict[str, int] = {}
    for veld in _STATS_VELDEN:
        waarde = stats.get(veld)
        if not isinstance(waarde, int) or isinstance(waarde, bool) or waarde < 0:
            raise GateError("rg_json_schema")
        getallen[veld] = waarde
    return getallen


def _lees_match(record: dict, toegestaan: set[str]) -> tuple[str, int, str, int]:
    data = record.get("data")
    if not isinstance(data, dict):
        raise GateError("rg_json_schema")
    pad_veld = data.get("path")
    regel_veld = data.get("lines")
    if not isinstance(pad_veld, dict) or not isinstance(regel_veld, dict):
        raise GateError("rg_json_schema")

    pad = pad_veld.get("text")
    tekst = regel_veld.get("text")
    regelnummer = data.get("line_number")
    submatches = data.get("submatches")
    if not isinstance(pad, str) or pad not in toegestaan:
        raise GateError("rg_json_path")
    if not isinstance(tekst, str):
        raise GateError("rg_json_schema")
    if (
        not isinstance(regelnummer, int)
        or isinstance(regelnummer, bool)
        or regelnummer < 1
    ):
        raise GateError("rg_json_schema")
    if not isinstance(submatches, list) or not submatches:
        raise GateError("rg_json_schema")
    for sub in submatches:
        if not isinstance(sub, dict):
            raise GateError("rg_json_schema")
        begin, eind = sub.get("start"), sub.get("end")
        if (
            not isinstance(begin, int)
            or isinstance(begin, bool)
            or not isinstance(eind, int)
            or isinstance(eind, bool)
            or begin < 0
            or eind <= begin
        ):
            raise GateError("rg_json_schema")
    return pad, regelnummer, tekst.rstrip("\r\n"), len(submatches)


def _zoek(
    rg: str, patroon: str, bestanden: list[str]
) -> list[tuple[str, int, str, int]]:
    """Zoek op precies de geselecteerde bestanden en toets het rg-protocol."""
    treffers: list[tuple[str, int, str, int]] = []
    for start in range(0, len(bestanden), _CHUNK):
        brok = bestanden[start : start + _CHUNK]
        toegestaan = set(brok)
        klaar = _run([rg, "--json", "-e", patroon, "--", *brok], "rg_search_failed")
        if klaar.returncode not in (0, 1):
            raise GateError("rg_search_status")

        records = []
        for regel in _decode(klaar.stdout, "rg_search_decode").splitlines():
            if not regel.strip():
                raise GateError("rg_json_invalid")
            try:
                record = json.loads(regel)
            except ValueError:
                raise GateError("rg_json_invalid") from None
            if (
                not isinstance(record, dict)
                or record.get("type") not in _RECORD_SOORTEN
            ):
                raise GateError("rg_json_schema")
            records.append(record)

        # Zonder precies één afsluitend `summary`-record is de stream afgebroken;
        # een lege stream is dus nooit bewijs van een voltooide, schone scan.
        stats: dict[str, int] | None = None
        brok_treffers: list[tuple[str, int, str, int]] = []
        for index, record in enumerate(records):
            soort = record["type"]
            if soort == "summary":
                if stats is not None or index != len(records) - 1:
                    raise GateError("rg_json_truncated")
                stats = _lees_summary(record)
            elif soort == "match":
                brok_treffers.append(_lees_match(record, toegestaan))
            else:
                _lees_pad(record, toegestaan)
        if stats is None:
            raise GateError("rg_json_truncated")

        if (klaar.returncode == 0) != bool(brok_treffers):
            raise GateError("rg_status_mismatch")
        if stats["matched_lines"] != len(brok_treffers):
            raise GateError("rg_stats_mismatch")
        if stats["matches"] != sum(treffer[3] for treffer in brok_treffers):
            raise GateError("rg_stats_mismatch")
        treffers.extend(brok_treffers)
    return treffers


def _laad_baseline() -> dict[tuple[str, str, int, str], int]:
    """Strikt gevalideerde, expliciet gereviewde schuld — nooit automatisch.

    Een ontbrekend bestand betekent: geen enkele legacy-bevinding geaccepteerd.
    Een ongeldig bestand blokkeert, ook wanneer er niets gevonden wordt.
    """
    if not BASELINE_PATH.exists():
        return {}
    try:
        rauw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        raise GateError("baseline_unreadable") from None

    if not isinstance(rauw, dict) or set(rauw) != {"version", "entries"}:
        raise GateError("baseline_schema")
    versie = rauw["version"]
    if not isinstance(versie, int) or isinstance(versie, bool) or versie != 1:
        raise GateError("baseline_schema")
    if not isinstance(rauw["entries"], list):
        raise GateError("baseline_schema")

    kaart: dict[tuple[str, str, int, str], int] = {}
    gezien: set[tuple[str, str, int]] = set()
    for post in rauw["entries"]:
        if not isinstance(post, dict) or set(post) != _BASELINE_KEYS:
            raise GateError("baseline_schema")
        rule, pad, regel = post["rule"], post["path"], post["line"]
        tekst, aantal = post["text"], post["count"]
        if rule != ENFORCED_RULE:
            raise GateError("baseline_rule")
        if (
            not isinstance(pad, str)
            or not pad.startswith("src/")
            or not _veilig_pad(pad)
        ):
            raise GateError("baseline_path")
        if not isinstance(regel, int) or isinstance(regel, bool) or regel < 1:
            raise GateError("baseline_line")
        if not isinstance(tekst, str) or not tekst.strip():
            raise GateError("baseline_text")
        if not isinstance(aantal, int) or isinstance(aantal, bool) or aantal < 1:
            raise GateError("baseline_count")
        if (rule, pad, regel) in gezien:
            raise GateError("baseline_duplicate")
        gezien.add((rule, pad, regel))
        kaart[(rule, pad, regel, tekst)] = aantal
    return kaart


def _vlag(naam: str) -> bool:
    """Alleen de gedocumenteerde waarden; een typefout schakelt niets uit."""
    waarde = os.environ.get(naam)
    if waarde is None:
        return False
    if waarde not in ("true", "false"):
        raise GateError("enforce_flag")
    return waarde == "true"


def _handhaaf(rg: str, baseline: dict, repo_breed: bool) -> int:
    # De repo-brede handhaving behoudt haar oorspronkelijke scope: `src` in zijn
    # geheel, dus inclusief UI. Hier wordt niets versmald.
    scopes: list[tuple[str, str, tuple[str, ...]]] = [("enforced", "src/services", ())]
    if repo_breed:
        scopes.append(("repo-wide", "src", ()))

    gevonden: dict[tuple[str, int, str], int] = {}
    for label, scope, globs in scopes:
        bestanden = _selecteer(rg, scope, globs)
        _log(f"{label} scope files={len(bestanden)}")
        for pad, regel, tekst, aantal in _zoek(rg, CONTEXT_STR, bestanden):
            sleutel = (pad, regel, tekst)
            gevonden[sleutel] = max(gevonden.get(sleutel, 0), aantal)

    # Geaccepteerde schuld die verdwijnt of krimpt hoort expliciet omlaag te
    # gaan. Stil laten staan zou de baseline met de werkelijkheid laten meelopen
    # zonder review, en dat is een ongeldige meting — geen schone scan. Entries
    # buiten de gescande scopes blijven buiten beschouwing; die dwingen geen
    # extra scan af.
    actieve_voorvoegsels = tuple(scope.rstrip("/") + "/" for _l, scope, _g in scopes)
    verouderd: list[tuple[str, int]] = []
    for (_rule, pad, regel, tekst), toegestaan in sorted(baseline.items()):
        if not pad.startswith(actieve_voorvoegsels):
            continue
        if gevonden.get((pad, regel, tekst), 0) < toegestaan:
            verouderd.append((pad, regel))
    if verouderd:
        _log(f"stale baseline entries={len(verouderd)}")
        for pad, regel in verouderd:
            _log(f"stale rule={ENFORCED_RULE} path={pad} line={regel}")
        raise GateError("baseline_stale")

    gebaselined = 0
    blokkerend: list[tuple[str, int, int]] = []
    for (pad, regel, tekst), aantal in sorted(gevonden.items()):
        toegestaan = baseline.get((ENFORCED_RULE, pad, regel, tekst))
        if toegestaan is not None and aantal == toegestaan:
            gebaselined += 1
        else:
            blokkerend.append((pad, regel, aantal))

    _log(f"baselined={gebaselined}")
    _log(f"baseline entries={len(baseline)}")
    _log(f"blocking findings={len(blokkerend)}")
    for pad, regel, aantal in blokkerend:
        _log(f"blocking rule={ENFORCED_RULE} path={pad} line={regel} count={aantal}")
    return EXIT_BLOCK if blokkerend else EXIT_OK


def _draai() -> int:
    if not (ROOT / "src").is_dir():
        raise GateError("layout")

    rg = _rg_pad()
    _log(f"rg={_rg_versie(rg)}")
    _log(f"root={ROOT}")

    handhaven = _vlag("ENFORCE_GREP_GATE")
    repo_breed = _vlag("ENFORCE_REPO_WIDE")
    baseline = _laad_baseline()

    _log(f"scope files={len(_selecteer(rg, 'src', (UI_UIT,)))}")

    advies = 0
    for _naam, patroon, globs in ADVISORY:
        advies += len(_zoek(rg, patroon, _selecteer(rg, "src", globs)))
    _log(f"advisory findings={advies}")

    if not handhaven:
        _log("enforced=skipped")
        return EXIT_OK
    return _handhaaf(rg, baseline, repo_breed)


def main() -> int:
    try:
        return _draai()
    except GateError as fout:
        _log(f"invalid reason={fout.reason}")
        return EXIT_INVALID


if __name__ == "__main__":
    sys.exit(main())
