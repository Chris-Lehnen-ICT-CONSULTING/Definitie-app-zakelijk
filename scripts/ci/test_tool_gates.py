#!/usr/bin/env python3
"""Regressietests voor de grep-gate (DEF-665).

Hermetisch: standaard-library `unittest` + `subprocess`, dummy-bronbestanden in
verse tijdelijke mappen, en een gecontroleerde PATH die alleen bevat wat de gate
nodig heeft. Geen app-imports, geen conftest, geen netwerk, geen echte
projectbron.

Voor de geldige scans draait de échte ripgrep op dummy-fixtures, zodat de
selectie- en statussemantiek van de tool niet wordt verzonnen. Nagemaakte `rg`'s
worden uitsluitend gebruikt om toolfouten af te dwingen: één die al bij
`--version` faalt, één die niets opsomt, en één die versie en bestandsopsomming
echt afhandelt maar de zoekfase stuurt.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd of
opgeruimd.

Publiek contract van de gate:
    exit 0 = geldige scan, geaccepteerd
    exit 1 = geldige scan, blokkerende bevinding
    exit 2 = ongeldige scan (scope, tool, config of I/O) — nooit stil groen

Metadata-uitvoer waar de tests op steunen (nooit broncode of rauwe toolfouten):
    grep-gate: rg=<versienummer>
    grep-gate: root=<absoluut pad>
    grep-gate: scope files=<n>
    grep-gate: advisory findings=<n>
    grep-gate: baselined=<n>
    grep-gate: blocking findings=<n>
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_SH = REPO_ROOT / "scripts" / "maintenance" / "grep_gate.sh"
GATE_PY = REPO_ROOT / "scripts" / "maintenance" / "grep_gate.py"

RG = shutil.which("rg")
#: De launcher roept `dirname` extern aan; zonder wrapper zou een regressietest
#: op een ontbrekend hulpprogramma stuklopen in plaats van op het gedrag.
DIRNAME = shutil.which("dirname")
TIMEOUT = 60

#: Komt in fixture-broncode en in nagemaakte tool-stderr; mag nooit in de
#: gate-uitvoer belanden.
MARKER = "DEF665-MARKER"

#: Rule-id van de handhaafde scopes; gelijk aan grep_gate.ENFORCED_RULE.
RULE = "context-str"

# Dummy-legacybestand met precies één `context: str` op regel 4.
LEGACY_EEN = (
    '"""Dummy legacy fixture (DEF-665)."""\n'  # 1
    "\n"  # 2
    "\n"  # 3
    "def eerste(context: str) -> None:\n"  # 4
    "    return None\n"  # 5
)
LEGACY_EEN_REGEL = 4
LEGACY_EEN_TEKST = "def eerste(context: str) -> None:"

# Zelfde bestand plus een tweede voorkomen met identieke tekst op regel 8.
LEGACY_TWEE = LEGACY_EEN + (
    "\n"  # 6
    "\n"  # 7
    "def eerste(context: str) -> None:\n"  # 8
    "    return None\n"  # 9
)

# Eén regel met twee treffers van hetzelfde patroon, voor de telling.
TWEE_OP_EEN_REGEL = (
    "def m(context: str, other_context: str) -> None:\n    return None\n"
)
TWEE_TEKST = "def m(context: str, other_context: str) -> None:"

SCHOON_SERVICE = "def f() -> None:\n    return None\n"
GEMARKEERD_SERVICE = f"def g(context: str) -> None:  # {MARKER}\n    return None\n"
CONTEXT_STR_BESTAND = "def h(context: str) -> None:\n    return None\n"


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan.

    Het pad wordt gecanonicaliseerd: op macOS geeft `mkdtemp` een `/var/...`
    alias terug, terwijl de gate haar root via `resolve()` als
    `/private/var/...` rapporteert.
    """
    return Path(tempfile.mkdtemp(prefix=f"def665-{prefix}-")).resolve()


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _bindir(*, rg: str | None) -> Path:
    """Gecontroleerde PATH-map: `dirname`, `python3` en desgewenst `rg`.

    Zo is "tool ontbreekt" deterministisch op elk platform: een `rg` in
    `/usr/bin` kan hier niet meeliften. `grep` blijft bewust afwezig, zodat de
    oude grep-terugval niet stilzwijgend inspringt.
    """
    assert DIRNAME, "dirname is vereist voor het gate-entrypoint"
    d = _new_dir("bin")
    _write_exec(d / "dirname", f'#!/bin/sh\nexec "{DIRNAME}" "$@"\n')
    _write_exec(d / "python3", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    if rg is not None:
        _write_exec(d / "rg", f'#!/bin/sh\nexec "{rg}" "$@"\n')
    return d


def _echte_rg_bin() -> Path:
    assert RG, "ripgrep is vereist voor deze gatetests (CI installeert het)"
    return _bindir(rg=RG)


def _rg_faalt_bij_versie(rc: int) -> Path:
    """Nagemaakte `rg` die meteen faalt; geen verzonnen uitvoersemantiek."""
    d = _bindir(rg=None)
    _write_exec(d / "rg", f'#!/bin/sh\necho "{MARKER}" >&2\nexit {rc}\n')
    return d


def _rg_met_zoekuitvoer(rc: int, payload: str = "") -> Path:
    """Versie en bestandsopsomming zijn echt; alleen de zoekfase is gestuurd."""
    assert RG, "ripgrep is vereist voor deze gatetests (CI installeert het)"
    d = _bindir(rg=None)
    _write_exec(
        d / "rg",
        "#!/bin/sh\n"
        'for a in "$@"; do\n'
        '  if [ "$a" = "--version" ]; then'
        ' echo "ripgrep 9.9.9 (rev deadbeef)"; exit 0; fi\n'
        "done\n"
        'for a in "$@"; do\n'
        f'  if [ "$a" = "--files" ]; then exec "{RG}" "$@"; fi\n'
        "done\n"
        f"printf '%s' '{payload}'\n"
        f'echo "{MARKER}" >&2\n'
        f"exit {rc}\n",
    )
    return d


def _rg_lege_opsomming(rc: int) -> Path:
    """Versie slaagt echt, maar de bestandsopsomming levert niets op."""
    d = _bindir(rg=None)
    _write_exec(
        d / "rg",
        "#!/bin/sh\n"
        'for a in "$@"; do\n'
        '  if [ "$a" = "--version" ]; then echo "ripgrep 9.9.9"; exit 0; fi\n'
        "done\n"
        f"exit {rc}\n",
    )
    return d


def _summary(*, matched_lines: int = 0, matches: int = 0, searches: int = 0) -> str:
    """Geldig afsluitend rg-record; bij nul treffers zijn alle tellers nul."""
    return json.dumps(
        {
            "type": "summary",
            "data": {
                "stats": {
                    "searches": searches,
                    "searches_with_match": 0,
                    "bytes_searched": 0,
                    "matched_lines": matched_lines,
                    "matches": matches,
                }
            },
        }
    )


def _repo(
    *,
    layout: str = "normaal",
    services: tuple[tuple[str, str], ...] = (("clean.py", SCHOON_SERVICE),),
    example: str = "x = 1\n",
    ui: str | None = None,
    extra: tuple[tuple[str, str], ...] = (),
    baseline: object | None = None,
) -> Path:
    """Verse repo-layout met uitsluitend de gate-entrypoints en dummybron."""
    root = _new_dir("repo")
    maint = root / "scripts" / "maintenance"
    maint.mkdir(parents=True)
    shutil.copy2(GATE_SH, maint / GATE_SH.name)
    if GATE_PY.exists():
        shutil.copy2(GATE_PY, maint / GATE_PY.name)
    if baseline is not None:
        inhoud = (
            baseline if isinstance(baseline, str) else json.dumps(baseline, indent=2)
        )
        (maint / "grep_gate_baseline.json").write_text(inhoud, encoding="utf-8")

    if layout == "geen-src":
        return root

    (root / "src").mkdir(parents=True)
    if layout == "geen-python":
        (root / "src" / "LEESMIJ.md").write_text("geen python hier\n", encoding="utf-8")
        return root

    (root / "src" / "example.py").write_text(example, encoding="utf-8")
    for naam, inhoud in extra:
        doel = root / "src" / naam
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_text(inhoud, encoding="utf-8")
    if ui is not None:
        (root / "src" / "ui").mkdir(parents=True, exist_ok=True)
        (root / "src" / "ui" / "panel.py").write_text(ui, encoding="utf-8")

    if layout == "geen-services":
        return root
    (root / "src" / "services").mkdir(parents=True, exist_ok=True)
    for naam, inhoud in services:
        (root / "src" / "services" / naam).write_text(inhoud, encoding="utf-8")
    return root


def _baseline_entries(*posten: tuple[str, int, str, int]) -> dict:
    """Baseline die pad, rule-id, regel, exacte regeltekst en aantal bindt."""
    return {
        "version": 1,
        "entries": [
            {"rule": RULE, "path": pad, "line": regel, "text": tekst, "count": aantal}
            for pad, regel, tekst, aantal in posten
        ],
    }


def _baseline(pad: str, regel: int, tekst: str, aantal: int = 1) -> dict:
    return _baseline_entries((pad, regel, tekst, aantal))


def _run(
    repo: Path, bindir: Path, *, enforce: str = "true"
) -> subprocess.CompletedProcess:
    """Draai de gate vanuit een werkmap die bewust niet de repo-root is."""
    elders = _new_dir("elders")
    env = {
        "PATH": str(bindir),
        "LC_ALL": "C",
        "LANG": "C",
        "HOME": str(elders),
        "PY": sys.executable,
        "ENFORCE_GREP_GATE": enforce,
    }
    return subprocess.run(
        ["/bin/bash", str(repo / "scripts" / "maintenance" / GATE_SH.name)],
        cwd=str(elders),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _uit(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


class TestGrepGate(unittest.TestCase):
    """De gate mag nooit groen zijn zonder bewezen, niet-lege scope."""

    def test_root_komt_uit_entrypoint_niet_uit_werkmap(self):
        repo = _repo()
        proc = _run(repo, _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert (
            f"grep-gate: root={repo}" in uitvoer
        ), "de root hoort uit het entrypoint te komen, niet uit cwd of scripts/"

    def test_geldige_niet_lege_schone_scan_wordt_geaccepteerd(self):
        proc = _run(_repo(), _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        treffer = re.search(r"grep-gate: scope files=(\d+)", uitvoer)
        assert treffer is not None, f"scope moet aantoonbaar zijn: {uitvoer}"
        assert int(treffer.group(1)) >= 1, "een lege selectie is geen schone scan"

    def test_enforced_treffer_blokkeert_zonder_broncode_in_log(self):
        repo = _repo(services=(("marked.py", GEMARKEERD_SERVICE),))
        proc = _run(repo, _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert MARKER not in uitvoer, "geen broncode-regels in de gate-uitvoer"

    def test_advisory_treffer_blokkeert_niet_maar_wordt_geteld(self):
        proc = _run(_repo(example="context_dict = {}\n"), _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert (
            "grep-gate: advisory findings=1" in uitvoer
        ), "advisory-patronen blijven rapporterend, maar wel geteld"

    def test_ui_en_buiten_services_treffers_blokkeren_niet(self):
        repo = _repo(
            ui=CONTEXT_STR_BESTAND,
            extra=(("buiten.py", CONTEXT_STR_BESTAND),),
        )
        proc = _run(repo, _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert (
            "grep-gate: blocking findings=0" in uitvoer
        ), "de handhaafde selectie blijft binnen src/services"

    def test_ontbrekende_of_lege_scope_is_ongeldig(self):
        gevallen = (
            ("geen src", {"layout": "geen-src"}),
            ("geen python in src", {"layout": "geen-python"}),
            ("geen services-map", {"layout": "geen-services"}),
            ("lege services-map", {"services": ()}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(**kwargs), _echte_rg_bin())
                assert (
                    proc.returncode == 2
                ), "een lege of ontbrekende scope mag nooit groen zijn"

    def test_lege_bestandsopsomming_is_ongeldig(self):
        for rc in (0, 1):
            with self.subTest(rc=rc):
                proc = _run(_repo(), _rg_lege_opsomming(rc))
                assert (
                    proc.returncode == 2
                ), "zonder werkelijk geselecteerde bestanden is er geen scan"

    def test_toolfout_bij_versie_is_ongeldig_en_lekt_niets(self):
        for rc in (2, 7):
            with self.subTest(rc=rc):
                proc = _run(_repo(), _rg_faalt_bij_versie(rc))
                uitvoer = _uit(proc)
                assert proc.returncode == 2, uitvoer
                assert MARKER not in uitvoer, "geen rauwe tool-stderr in de log"

    def test_toolfout_of_onbruikbaar_protocol_tijdens_zoekfase_is_ongeldig(self):
        gevallen = (
            ("status 2", 2, ""),
            ("status 7", 7, ""),
            ("status 0 zonder uitvoer", 0, ""),
            ("status 0 met onbruikbare uitvoer", 0, "niet-json"),
            ("samenvatting zonder data", 1, '{"type":"summary"}'),
            (
                "samenvatting met ongeldig teltype",
                1,
                (
                    '{"type":"summary","data":{"stats":{"searches":"x",'
                    '"searches_with_match":0,"bytes_searched":0,'
                    '"matched_lines":0,"matches":0}}}'
                ),
            ),
            ("status 0 met nul-treffer-samenvatting", 0, _summary()),
        )
        for naam, rc, payload in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(), _rg_met_zoekuitvoer(rc, payload))
                uitvoer = _uit(proc)
                assert (
                    proc.returncode == 2
                ), "status, samenvatting en records moeten elkaar bevestigen"
                assert MARKER not in uitvoer, "geen rauwe tool-stderr in de log"

    def test_geldige_nul_treffer_samenvatting_wordt_geaccepteerd(self):
        """Een echte no-match-stream telt alles op nul; dat is geen fout."""
        proc = _run(_repo(), _rg_met_zoekuitvoer(1, _summary()))
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "grep-gate: rg=9.9.9" in uitvoer, "log alleen het versienummer"

    def test_ontbrekende_rg_is_ongeldig(self):
        proc = _run(_repo(), _bindir(rg=None))

        assert (
            proc.returncode == 2
        ), "zonder rg is er geen scan; geen afwijkende grep-terugval"

    def test_onbekende_enforce_vlag_is_ongeldig(self):
        proc = _run(_repo(), _echte_rg_bin(), enforce="ture")

        assert (
            proc.returncode == 2
        ), "een typefout mag de handhaving niet stil uitschakelen"

    def test_exacte_baseline_accepteert_bekend_voorkomen(self):
        repo = _repo(
            services=(("legacy.py", LEGACY_EEN),),
            baseline=_baseline(
                "src/services/legacy.py", LEGACY_EEN_REGEL, LEGACY_EEN_TEKST
            ),
        )
        proc = _run(repo, _echte_rg_bin())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "grep-gate: baselined=1" in uitvoer, uitvoer

    def test_nieuw_voorkomen_in_gebaselined_bestand_blokkeert(self):
        repo = _repo(
            services=(("legacy.py", LEGACY_TWEE),),
            baseline=_baseline(
                "src/services/legacy.py", LEGACY_EEN_REGEL, LEGACY_EEN_TEKST
            ),
        )
        proc = _run(repo, _echte_rg_bin())

        assert (
            proc.returncode == 1
        ), "een tweede voorkomen met dezelfde tekst mag niet meeliften"

    def test_verouderde_baseline_is_ongeldig(self):
        """Geaccepteerde schuld die verdwijnt of krimpt moet expliciet omlaag.

        Stil blijven staan zou de baseline laten meegroeien met de werkelijkheid
        zonder review; dat is een ongeldige meting, geen schone scan.
        """
        gevallen = (
            ("bevinding verdwenen", (("legacy.py", SCHOON_SERVICE),), 1),
            ("bestand verdwenen", (("clean.py", SCHOON_SERVICE),), 1),
            ("aantal gedaald", (("legacy.py", LEGACY_EEN),), 2),
        )
        for naam, services, aantal in gevallen:
            with self.subTest(naam=naam):
                repo = _repo(
                    services=services,
                    baseline=_baseline(
                        "src/services/legacy.py",
                        LEGACY_EEN_REGEL,
                        LEGACY_EEN_TEKST,
                        aantal,
                    ),
                )
                proc = _run(repo, _echte_rg_bin())
                assert (
                    proc.returncode == 2
                ), "een verouderde baseline vraagt om expliciete verlaging"

    def test_toegenomen_aantal_op_gebaselinde_regel_blokkeert(self):
        repo = _repo(
            services=(("dubbel.py", TWEE_OP_EEN_REGEL),),
            baseline=_baseline("src/services/dubbel.py", 1, TWEE_TEKST, 1),
        )
        proc = _run(repo, _echte_rg_bin())

        assert (
            proc.returncode == 1
        ), "meer treffers op dezelfde regel dan gebaselined blokkeert"

    def test_baseline_buiten_actieve_scope_forceert_geen_scan(self):
        repo = _repo(
            ui=CONTEXT_STR_BESTAND,
            baseline=_baseline("src/ui/panel.py", 1, "def h(context: str) -> None:"),
        )
        proc = _run(repo, _echte_rg_bin())

        assert (
            proc.returncode == 0
        ), "een entry buiten de handhaafde scope dwingt geen extra scan af"

    def test_ongeldige_baseline_blokkeert_ook_zonder_treffers(self):
        gevallen = (
            ("kapotte json", "{ geen json"),
            ("onbekend veld", {"version": 1, "entries": [], "extra": True}),
            (
                "dubbele identiteit",
                {
                    "version": 1,
                    "entries": [
                        {
                            "rule": RULE,
                            "path": "src/services/legacy.py",
                            "line": 4,
                            "text": LEGACY_EEN_TEKST,
                            "count": 1,
                        },
                        {
                            "rule": RULE,
                            "path": "src/services/legacy.py",
                            "line": 4,
                            "text": LEGACY_EEN_TEKST,
                            "count": 2,
                        },
                    ],
                },
            ),
            ("versie als boolean", {"version": True, "entries": []}),
        )
        for naam, inhoud in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(baseline=inhoud), _echte_rg_bin())
                assert (
                    proc.returncode == 2
                ), "een ongeldige baseline blokkeert, ook bij een schone scan"


if __name__ == "__main__":
    unittest.main()
