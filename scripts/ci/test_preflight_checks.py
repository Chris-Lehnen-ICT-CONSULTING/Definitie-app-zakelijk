#!/usr/bin/env python3
"""Regressietests voor de repository-preflight (DEF-737).

Hermetisch, in de lijn van `test_tool_gates.py`: standaard-library `unittest` +
`subprocess`, dummy-bronbestanden in verse tijdelijke mappen, en een
gecontroleerde PATH die alleen bevat wat de preflight nodig heeft. Geen
app-imports, geen conftest, geen netwerk, geen providers, geen database, geen
echte projectbron.

Voor elke geldige scan draaien de échte `rg` en `git` op dummy-fixtures, zodat de
selectie- en statussemantiek van die tools niet wordt verzonnen. Nagemaakte
tools worden uitsluitend gebruikt om foutpaden af te dwingen: een `rg` die
meteen faalt, een `rg` die treffers meldt én daarna alsnog een fout rapporteert
(een gemodelleerde uitkomst — geen echte leesfout op een filesystem), en een
`git` die niet-nul teruggeeft.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd of
opgeruimd. HOME komt in deze suite nergens voor: het wordt niet gelezen, niet
gewijzigd en niet vervangen. De subprocessen krijgen een omgeving zónder HOME,
en git leest geen globale of systeemconfig. Dat is meteen het bewijs voor de
onafhankelijkheid van een persoonlijk script buiten de repository.

Secrets vallen buiten deze gate en dus buiten deze suite: die worden beoordeeld
door de verplichte gitleaks-gate in `.github/workflows/security.yml` (DEF-522).
Wat hier getoetst wordt, is dat de preflight er niet meer op blokkeert.

Publiek contract van de preflight:
    exit 0 = geldige scan, geaccepteerd (waarschuwingen mogen)
    exit 1 = geldige scan, blokkerende bevinding
    exit 2 = ongeldige scan (scope, tool, git of I/O) — nooit stil groen

Metadata-uitvoer waar de tests op steunen. Nooit broncode, nooit rauwe
tool-stderr; uitsluitend categorie, pad en telling:
    preflight: root=<absoluut pad>
    preflight: BLOCK <categorie> ...
    preflight: WARN <categorie> ...
    preflight: workflow=<DOCUMENT|HOTFIX|FULL_TDD|ANALYSIS>
    preflight: error=<code>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "ci" / "preflight_checks.py"

RG = shutil.which("rg")
GIT = shutil.which("git")
TIMEOUT = 60

#: Komt in fixture-broncode en in nagemaakte tool-stderr; mag nooit in de
#: preflight-uitvoer belanden.
MARKER = "DEF737-MARKER"

# Categorienamen in de uitvoer. De implementatie deelt deze namen; ze zijn het
# enige waarop een test kan zien wélke controle vuurde. Zonder die scheiding
# bewijst een exitcode alleen dát er iets afging, niet wat.
BLOK_STREAMLIT = "services-streamlit"
BLOK_UI_IMPORT = "services-ui-import"
BLOK_ASYNCIO = "services-asyncio-run"
BLOK_REPOSITORY = "ui-repository-import"

#: Categorieën die deze gate niet meer kent. De brede geheimpatronen zijn
#: vervallen ten gunste van de verplichte gitleaks-gate in
#: `.github/workflows/security.yml`; hier hoort geen van beide nog te blokkeren.
VERVALLEN_CATEGORIEEN = ("api-key", "password")

WARN_ORG = "organizational-context"
WARN_LEGAL = "legal-context"
WARN_ORCHESTRATOR = "validation-orchestrator-v1"
WARN_MARKERS = "todo-marker"
WARN_DUPLICATE = "duplicate-import"
WARN_DIFF = "diff-size"

SCHOON = "def f():\n    return None\n"
SCHONE_REGELS = "x = 1\n"

STREAMLIT_BRON = f"import streamlit as st  # {MARKER}\n"
UI_IMPORT_BRON = f"from ui.panel import toon  # {MARKER}\n"
ASYNCIO_RUN_BRON = f"asyncio.run(hoofd())  # {MARKER}\n"
REPOSITORY_IMPORT_BRON = f"from src.repositories.definitie import Repo  # {MARKER}\n"

# Bron die eruitziet als een hardgecodeerd geheim. De preflight hoort hier niet
# meer op te blokkeren; de verplichte gitleaks-gate beoordeelt secrets. Veldnaam
# en waarde blijven uit delen samengesteld: een letterlijke `<veld> = "<waarde>"`
# zou deze testbron zelf tot bevinding maken zodra een secret-scan eroverheen
# loopt. De waarden zijn dummy's en geen echte credentials.
_SLEUTELVELD = "api" + "_key"
_WACHTWOORDVELD = "pass" + "word"
_DUMMYWAARDE = "Dummy" + "0" * 4
SLEUTEL_BRON = f'{_SLEUTELVELD} = "{_DUMMYWAARDE}"  # {MARKER}\n'
WACHTWOORD_BRON = f'{_WACHTWOORDVELD} = "{_DUMMYWAARDE}"  # {MARKER}\n'

ORG_CONTEXT_BRON = "organizational_context = {}\n"
LEGAL_CONTEXT_BRON = "legal_context = {}\n"
ORCHESTRATOR_BRON = "gebruik = ValidationOrchestrator(bron)\n"
# Ook gesplitst: los geschreven zou deze regel dit testbestand tot een
# permanente waarschuwing in de echte repo maken.
MARKER_BRON = "# " + "TO" + "DO: dummy-markering voor de waarschuwingstest\n"

IMPORTREGEL = "import os\n"


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan.

    Het pad wordt gecanonicaliseerd: op macOS geeft `mkdtemp` een `/var/...`
    alias terug, terwijl de preflight haar root via `resolve()` als
    `/private/var/...` rapporteert.
    """
    return Path(tempfile.mkdtemp(prefix=f"def737-{prefix}-")).resolve()


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _bindir(*, rg: str | None = None, git: str | None = None) -> Path:
    """Gecontroleerde PATH-map met hoogstens `rg` en `git`.

    Zo is "tool ontbreekt" deterministisch op elk platform: een `rg` of `git`
    in `/usr/bin` kan hier niet meeliften. `grep` blijft bewust afwezig, zodat
    een stille terugval op een andere zoektool zichtbaar wordt.
    """
    d = _new_dir("bin")
    if rg is not None:
        _write_exec(d / "rg", f'#!/bin/sh\nexec "{rg}" "$@"\n')
    if git is not None:
        _write_exec(d / "git", f'#!/bin/sh\nexec "{git}" "$@"\n')
    return d


def _echte_tools() -> Path:
    assert RG, "ripgrep is vereist voor deze preflighttests (CI installeert het)"
    assert GIT, "git is vereist voor deze preflighttests"
    return _bindir(rg=RG, git=GIT)


def _rg_faalt(rc: int) -> Path:
    """Nagemaakte `rg` die meteen faalt; geen verzonnen uitvoersemantiek."""
    d = _bindir(rg=None, git=GIT)
    _write_exec(d / "rg", f'#!/bin/sh\necho "{MARKER}" >&2\nexit {rc}\n')
    return d


def _rg_treffer_en_fout() -> Path:
    """`rg` die treffers meldt én daarna een fout rapporteert.

    Dit is een argument- en statuscontract-test, geen bewezen leesfout op een
    echt filesystem: de fake veroorzaakt geen I/O-probleem, hij modelleert de
    uitkomst ervan. Wat hij wél vastlegt, is dat status 2 zwaarder weegt dan de
    trefferregels die eraan voorafgingen.

    Bij `-q` geeft de fake juist succes terug. Zonder die tak zou de test ook
    slagen wanneer de gate weer `-q` zou meegeven — terwijl `-q` bij de eerste
    treffer stopt en met status 0 afsluit, waardoor een fout verderop in de
    scope nooit gezien wordt. Nu maakt die terugkeer de test rood.
    """
    d = _bindir(rg=None, git=GIT)
    _write_exec(
        d / "rg",
        "#!/bin/sh\n"
        'for arg in "$@"; do\n'
        '  case "$arg" in\n'
        "    -q|--quiet) exit 0 ;;\n"
        "  esac\n"
        "done\n"
        "echo 'src/services/zoek.py:1:treffer'\n"
        f'echo "{MARKER}" >&2\n'
        "exit 2\n",
    )
    return d


def _git_faalt(rc: int = 128) -> Path:
    """Nagemaakte `git` die niet-nul teruggeeft; een scan zonder oordeel."""
    d = _bindir(rg=RG, git=None)
    _write_exec(d / "git", f'#!/bin/sh\necho "{MARKER}" >&2\nexit {rc}\n')
    return d


def _basis_env() -> dict[str, str]:
    """Isolerende omgeving zonder HOME en zonder globale of systeem-gitconfig.

    HOME staat er bewust niet in — niet leeg, niet vervangen, niet verwezen. De
    uitkomst hangt daardoor niet af van de persoonlijke instellingen van wie de
    tests draait, en een preflight die stiekem een script uit een homedir zou
    zoeken heeft hier niets om op terug te vallen.
    """
    return {
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "Preflight Fixture",
        "GIT_AUTHOR_EMAIL": "preflight@example.invalid",
        "GIT_COMMITTER_NAME": "Preflight Fixture",
        "GIT_COMMITTER_EMAIL": "preflight@example.invalid",
    }


def _gate_env(bindir: Path) -> dict[str, str]:
    """De omgeving waarin de preflight zelf draait."""
    env = _basis_env()
    env["PATH"] = str(bindir)
    return env


def _git(repo: Path, *args: str) -> None:
    """Fixture-git via het echte binary, buiten de beperkte PATH van de gate om."""
    assert GIT, "git is vereist voor deze preflighttests"
    env = _basis_env()
    env["PATH"] = str(Path(GIT).parent)
    voltooid = subprocess.run(
        [GIT, *args],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    assert voltooid.returncode == 0, f"fixture-git faalde: {args} -> {voltooid.stderr}"


def _schrijf(root: Path, relpad: str, inhoud: str) -> None:
    doel = root / relpad
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")


def _repo(
    *,
    services: tuple[tuple[str, str], ...] = (("schoon.py", SCHOON),),
    ui: tuple[tuple[str, str], ...] = (("paneel.py", SCHOON),),
    extra: tuple[tuple[str, str], ...] = (),
    layout: str = "normaal",
    git: bool = True,
) -> Path:
    """Verse dummy-projectlayout; desgewenst een git-werkboom met één commit."""
    root = _new_dir("repo")

    if layout != "geen-src":
        (root / "src").mkdir(parents=True)
        if layout == "geen-python":
            _schrijf(root, "src/LEESMIJ.md", "geen python hier\n")
        else:
            _schrijf(root, "src/module.py", SCHOON)
            if layout != "geen-services":
                for naam, inhoud in services:
                    _schrijf(root, f"src/services/{naam}", inhoud)
            if layout != "geen-ui":
                for naam, inhoud in ui:
                    _schrijf(root, f"src/ui/{naam}", inhoud)

    for relpad, inhoud in extra:
        _schrijf(root, relpad, inhoud)

    if git:
        _git(root, "-c", "init.defaultBranch=main", "init")
        _git(root, "add", "-A")
        # `--allow-empty`: de layouts zonder bronbestanden hebben niets te
        # committen, en zonder deze vlag strandde de fixture daar op git in
        # plaats van de gate te draaien — dan toetst zo een geval niets.
        _git(root, "commit", "-m", "fixture", "--allow-empty")
    return root


def _run(
    repo: Path,
    bindir: Path,
    *,
    geef_pad: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Draai de preflight vanuit een werkmap die bewust niet de repo-root is."""
    elders = _new_dir("elders")
    env = _gate_env(bindir)
    if extra_env:
        env.update(extra_env)
    argv = [sys.executable, str(CLI)]
    if geef_pad:
        argv.append(str(repo))
    return subprocess.run(
        argv,
        cwd=str(repo if not geef_pad else elders),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _uit(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


class TestPreflightBlokkerend(unittest.TestCase):
    """Elke blokkerende categorie moet zelfstandig rood kunnen maken."""

    def test_schone_repo_is_geldig_en_groen(self):
        proc = _run(_repo(), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: BLOCK" not in uitvoer, uitvoer

    def test_root_komt_uit_argument_niet_uit_werkmap(self):
        repo = _repo()
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert (
            f"preflight: root={repo}" in uitvoer
        ), "de root hoort uit het argument te komen, niet uit cwd"

    def test_zonder_argument_geldt_de_werkmap(self):
        repo = _repo()
        proc = _run(repo, _echte_tools(), geef_pad=False)
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: root={repo}" in uitvoer, uitvoer

    def test_services_scans_blokkeren_elk_afzonderlijk(self):
        gevallen = (
            (BLOK_STREAMLIT, STREAMLIT_BRON),
            (BLOK_UI_IMPORT, UI_IMPORT_BRON),
            (BLOK_ASYNCIO, ASYNCIO_RUN_BRON),
        )
        for categorie, bron in gevallen:
            with self.subTest(categorie=categorie):
                repo = _repo(services=(("verdacht.py", bron),))
                proc = _run(repo, _echte_tools())
                uitvoer = _uit(proc)

                assert proc.returncode == 1, uitvoer
                assert f"preflight: BLOCK {categorie}" in uitvoer, uitvoer

    def test_ui_repository_import_blokkeert(self):
        repo = _repo(ui=(("paneel.py", REPOSITORY_IMPORT_BRON),))
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert f"preflight: BLOCK {BLOK_REPOSITORY}" in uitvoer, uitvoer

    def test_geheimpatronen_blokkeren_niet_meer_maar_imports_wel(self):
        """De taakverdeling: secrets bij de gitleaks-gate, lagen bij de preflight.

        Beide brede geheimpatronen zijn hier vervallen. Ze scanden het hele
        project op vorm alleen, terwijl de verplichte gate in
        `.github/workflows/security.yml` werkboom én historie beoordeelt. Deze
        fixture draagt allebei de vormen én een laagoverschrijdende import, zodat
        één run laat zien dat het eerste doorgelaten wordt en het tweede nog
        steeds blokkeert.

        Geen equivalentieclaim: de twee gates vinden niet hetzelfde.
        """
        repo = _repo(
            services=(("verdacht.py", STREAMLIT_BRON),),
            extra=(("hulp/instellingen.py", SLEUTEL_BRON + WACHTWOORD_BRON),),
        )
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert f"preflight: BLOCK {BLOK_STREAMLIT}" in uitvoer, uitvoer
        for categorie in VERVALLEN_CATEGORIEEN:
            assert f"preflight: BLOCK {categorie}" not in uitvoer, uitvoer

    def test_geheimvorm_alleen_laat_de_gate_groen(self):
        """Zonder andere bevinding is een geheimvorm geen blokkade meer.

        De test hierboven draait op exit 1 door de import; zonder dit geval zou
        een gate die de patronen stilletjes terugbrengt daar niet opvallen.
        """
        repo = _repo(extra=(("hulp/instellingen.py", SLEUTEL_BRON + WACHTWOORD_BRON),))
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: BLOCK" not in uitvoer, uitvoer

    def test_gerichte_scans_blijven_binnen_hun_eigen_scope(self):
        """Buiten de eigen map mag hetzelfde patroon juist niets blokkeren.

        `import streamlit` hoort thuis in de UI-laag, en de repository-import is
        alleen in de UI verboden. Zonder deze test zou een scan die per ongeluk
        het hele project bestrijkt groen blijven in de tests en de rest van de
        codebase onterecht blokkeren.
        """
        gevallen = (
            ("streamlit in ui", {"ui": (("paneel.py", STREAMLIT_BRON),)}),
            (
                "repository-import in services",
                {"services": (("dienst.py", REPOSITORY_IMPORT_BRON),)},
            ),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(**kwargs), _echte_tools())
                uitvoer = _uit(proc)

                assert proc.returncode == 0, uitvoer
                assert "preflight: BLOCK" not in uitvoer, uitvoer

    def test_alle_categorieen_worden_gecontroleerd_niet_alleen_de_eerste(self):
        """Een treffer in de eerste categorie mag de rest niet overslaan.

        De oorspronkelijke inline-variant telde bevindingen met `((counter++))`
        onder `set -e`, waardoor de eerste ophoging vanaf nul het script
        afbrak. Blijft die vroege afbreking staan, dan rapporteert de gate maar
        één categorie en verdwijnt de rest ongezien.
        """
        repo = _repo(
            services=(("verdacht.py", STREAMLIT_BRON + ASYNCIO_RUN_BRON),),
            ui=(("paneel.py", REPOSITORY_IMPORT_BRON),),
        )
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        for categorie in (BLOK_STREAMLIT, BLOK_ASYNCIO, BLOK_REPOSITORY):
            assert f"preflight: BLOCK {categorie}" in uitvoer, (categorie, uitvoer)

    def test_eigen_gatebron_blokkeert_niet(self):
        """De gate mag niet aanslaan op zijn eigen definities.

        Dat gebeurde eerder wel: een categorienaam stond op dezelfde regel als
        het patroon dat naar diezelfde tekst zocht, en de scan vond zo zijn
        eigen tabel — een permanente blocker die niets over de codebase zei.
        De patronen in kwestie zijn inmiddels vervallen, maar de regel geldt
        onverminderd voor wat er nog staat en voor wat er bij komt.

        Getoetst op een kopie in een dummyrepo, niet op de echte projectboom —
        die draagt bestaande, legitieme bevindingen die hier niets bewijzen en
        deze test onterecht rood zouden maken.
        """
        repo = _repo()
        doel = repo / "scripts" / "ci"
        doel.mkdir(parents=True)
        for bron in (CLI, Path(__file__).resolve()):
            shutil.copy2(bron, doel / bron.name)

        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: BLOCK" not in uitvoer, (
            "de gate blokkeert op zijn eigen bron; categorienaam en patroon "
            f"horen niet samen een treffer te vormen\n{uitvoer}"
        )

    def test_gatebron_alleen_geeft_geen_enkele_bevinding(self):
        """Ook geen wáárschuwing op de eigen bron — alleen de gate gekopieerd.

        De test hierboven zet de testbron ernaast, en die draagt bewust
        waarschuwingsfixtures; hij kan dus niets zeggen over WARN-treffers. Een
        toelichting in de gate die een patroon voluit spelde, telde daardoor
        onopgemerkt mee in elke echte scan.
        """
        repo = _repo()
        doel = repo / "scripts" / "ci"
        doel.mkdir(parents=True)
        shutil.copy2(CLI, doel / CLI.name)

        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: BLOCK" not in uitvoer, uitvoer
        assert "preflight: WARN" not in uitvoer, (
            "de gate vindt zichzelf; een patroon staat voluit in zijn eigen "
            f"bron\n{uitvoer}"
        )

    def test_bevinding_lekt_geen_broncode(self):
        repo = _repo(services=(("verdacht.py", STREAMLIT_BRON),))
        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert MARKER not in uitvoer, "geen broncode-regels in de preflight-uitvoer"


class TestPreflightWaarschuwingen(unittest.TestCase):
    """Waarschuwingen informeren; ze mogen de uitkomst nooit rood maken."""

    def test_advies_patronen_waarschuwen_maar_blokkeren_niet(self):
        gevallen = (
            (WARN_ORG, ORG_CONTEXT_BRON),
            (WARN_LEGAL, LEGAL_CONTEXT_BRON),
            (WARN_ORCHESTRATOR, ORCHESTRATOR_BRON),
            (WARN_MARKERS, MARKER_BRON),
        )
        for categorie, bron in gevallen:
            with self.subTest(categorie=categorie):
                repo = _repo(extra=(("hulp/oud.py", bron),))
                proc = _run(repo, _echte_tools())
                uitvoer = _uit(proc)

                assert proc.returncode == 0, uitvoer
                assert f"preflight: WARN {categorie}" in uitvoer, uitvoer

    def test_zesmaal_dezelfde_import_waarschuwt(self):
        extra = tuple(
            (f"src/dubbel{n}.py", IMPORTREGEL + SCHONE_REGELS) for n in range(6)
        )
        proc = _run(_repo(extra=extra), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DUPLICATE}" in uitvoer, uitvoer

    def test_vijfmaal_dezelfde_import_waarschuwt_niet(self):
        """De grens ligt boven vijf; precies vijf is nog gewoon gedeelde stdlib."""
        extra = tuple(
            (f"src/dubbel{n}.py", IMPORTREGEL + SCHONE_REGELS) for n in range(5)
        )
        proc = _run(_repo(extra=extra), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DUPLICATE}" not in uitvoer, uitvoer

    def test_duplicaten_vergelijken_de_regel_exact(self):
        """Trailing whitespace hoort bij de regel, net als in de bestaande check.

        Een `rstrip()` zou varianten die alleen in witruimte verschillen op één
        hoop gooien en zo een waarschuwing melden die er niet was.
        """
        gevallen = (
            (
                "zes keer dezelfde regel met een trailing tab",
                tuple((f"src/tab{n}.py", "import os\t\n") for n in range(6)),
                True,
            ),
            (
                "drie met en drie zonder trailing spatie",
                tuple(
                    (f"src/mix{n}.py", "import os \n" if n < 3 else IMPORTREGEL)
                    for n in range(6)
                ),
                False,
            ),
        )
        for naam, extra, verwacht in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(extra=extra), _echte_tools())
                uitvoer = _uit(proc)

                assert proc.returncode == 0, uitvoer
                aanwezig = f"preflight: WARN {WARN_DUPLICATE}" in uitvoer
                assert aanwezig is verwacht, uitvoer

    def test_prefix_telt_ook_zonder_spatie_na_import(self):
        """`^import` is breder dan `import `; die grens hoort behouden te blijven."""
        extra = tuple((f"src/breed{n}.py", "importlib.reload(mod)\n") for n in range(6))
        proc = _run(_repo(extra=extra), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DUPLICATE}" in uitvoer, uitvoer

    def test_import_voorbij_regel_twintig_telt_niet_mee(self):
        """Alleen de kop van een bestand geldt als importblok."""
        diep = SCHONE_REGELS * 25 + IMPORTREGEL
        extra = tuple((f"src/diep{n}.py", diep) for n in range(6))
        proc = _run(_repo(extra=extra), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DUPLICATE}" not in uitvoer, uitvoer


class TestPreflightGitDiff(unittest.TestCase):
    """De diffmeting adviseert en waarschuwt, maar vraagt nooit om toestemming."""

    def test_schone_werkboom_is_geen_scanfout(self):
        proc = _run(_repo(), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: error=" not in uitvoer, "geen diff is 0/0, geen fout"
        assert f"preflight: WARN {WARN_DIFF}" not in uitvoer, uitvoer

    def test_veel_gewijzigde_bestanden_waarschuwen(self):
        extra = tuple((f"src/mod{n}.py", SCHONE_REGELS) for n in range(6))
        repo = _repo(extra=extra)
        for n in range(6):
            _schrijf(repo, f"src/mod{n}.py", SCHONE_REGELS * 2)

        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DIFF}" in uitvoer, uitvoer

    def test_veel_gewijzigde_regels_waarschuwen(self):
        repo = _repo(extra=(("src/groot.py", SCHONE_REGELS),))
        _schrijf(repo, "src/groot.py", SCHONE_REGELS * 120)

        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"preflight: WARN {WARN_DIFF}" in uitvoer, uitvoer

    def test_workflowadvies_volgt_de_omvang_van_de_diff(self):
        """De vier adviezen, elk via het kenmerk dat ze onderscheidt.

        De volgorde is load-bearing: één gewijzigd markdownbestand valt óók
        binnen de hotfix-conditie (klein en zonder nieuwe bestanden), dus dit
        bewijst tegelijk dat DOCUMENT vóór HOTFIX wordt beoordeeld.
        """
        verwacht = {
            "document": "DOCUMENT",
            "hotfix": "HOTFIX",
            "full_tdd_nieuw_bestand": "FULL_TDD",
            "full_tdd_veel_bestanden": "FULL_TDD",
            "analysis": "ANALYSIS",
        }
        for geval, advies in verwacht.items():
            with self.subTest(geval=geval):
                extra = tuple((f"src/mod{n}.py", SCHONE_REGELS) for n in range(4)) + (
                    ("docs/leesmij.md", "# titel\n"),
                )
                repo = _repo(extra=extra)

                if geval == "document":
                    _schrijf(repo, "docs/leesmij.md", "# titel\n\nextra alinea\n")
                elif geval == "hotfix":
                    _schrijf(repo, "src/mod0.py", SCHONE_REGELS * 3)
                elif geval == "full_tdd_nieuw_bestand":
                    # `add -N` (intent-to-add) laat een nieuw bestand in de
                    # werkboom-tegen-index-diff verschijnen zonder de inhoud te
                    # stagen; een volledige `git add` zou het er juist uit halen.
                    _schrijf(repo, "src/nieuw.py", SCHONE_REGELS)
                    _git(repo, "add", "-N", "src/nieuw.py")
                elif geval == "full_tdd_veel_bestanden":
                    for n in range(4):
                        _schrijf(repo, f"src/mod{n}.py", SCHONE_REGELS * 16)
                else:
                    for n in range(2):
                        _schrijf(repo, f"src/mod{n}.py", SCHONE_REGELS * 31)

                proc = _run(repo, _echte_tools())
                uitvoer = _uit(proc)

                assert proc.returncode == 0, uitvoer
                assert f"preflight: workflow={advies}" in uitvoer, uitvoer

    def test_gestagede_wijziging_telt_niet_mee(self):
        """De meting is werkboom tegen index, zonder `HEAD`.

        Wat al gestaged is, staat niet meer in die diff. Zou de gate tegen
        `HEAD` meten, dan zou deze fixture zes bestanden en ruim honderd regels
        melden — inclusief omvangswaarschuwing — terwijl er in de werkboom niets
        meer openstaat.
        """
        extra = tuple((f"src/mod{n}.py", SCHONE_REGELS) for n in range(6))
        repo = _repo(extra=extra)
        for n in range(6):
            _schrijf(repo, f"src/mod{n}.py", SCHONE_REGELS * 30)
        _git(repo, "add", "-A")

        proc = _run(repo, _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: diff files=0 lines=0 added=0" in uitvoer, uitvoer
        assert f"preflight: WARN {WARN_DIFF}" not in uitvoer, uitvoer

    def test_gitfout_is_een_ongeldige_scan(self):
        proc = _run(_repo(), _git_faalt())
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert "preflight: error=git" in uitvoer, uitvoer
        assert MARKER not in uitvoer, "geen rauwe git-stderr in de log"

    def test_map_zonder_werkboom_is_een_ongeldige_scan(self):
        proc = _run(_repo(git=False), _echte_tools())
        uitvoer = _uit(proc)

        assert (
            proc.returncode == 2
        ), f"zonder werkboom is er geen diffoordeel te vellen: {uitvoer}"


class TestPreflightOngeldigeScan(unittest.TestCase):
    """Zonder bewezen, niet-lege scope en werkende tools is er geen oordeel."""

    def test_ontbrekende_of_lege_scope_is_ongeldig(self):
        gevallen = (
            ("geen src", {"layout": "geen-src"}),
            ("geen python in src", {"layout": "geen-python"}),
            ("geen services-map", {"layout": "geen-services"}),
            ("lege services-map", {"services": ()}),
            ("geen ui-map", {"layout": "geen-ui"}),
            ("lege ui-map", {"ui": ()}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(**kwargs), _echte_tools())
                uitvoer = _uit(proc)

                assert (
                    proc.returncode == 2
                ), f"een lege of ontbrekende scope mag nooit groen zijn: {uitvoer}"
                assert "preflight: error=scope" in uitvoer, uitvoer

    def test_ontbrekend_projectpad_is_ongeldig(self):
        weg = _new_dir("weg") / "bestaat-niet"
        proc = _run(weg, _echte_tools())

        assert proc.returncode == 2, _uit(proc)

    def test_toolfout_is_ongeldig_en_lekt_niets(self):
        for rc in (2, 7):
            with self.subTest(rc=rc):
                proc = _run(_repo(), _rg_faalt(rc))
                uitvoer = _uit(proc)

                assert proc.returncode == 2, uitvoer
                assert "preflight: error=tool" in uitvoer, uitvoer
                assert MARKER not in uitvoer, "geen rauwe tool-stderr in de log"

    def test_treffers_met_toolfout_blijven_ongeldig(self):
        """Status 2 weegt zwaarder dan de trefferregels die eraan voorafgingen.

        Zou de gate op aanwezige uitvoer afgaan, dan werd een halve scan met een
        leesfout als blokkerende bevinding (exit 1) gerapporteerd — een geldig
        ogend oordeel op onvolledige gegevens.
        """
        proc = _run(_repo(), _rg_treffer_en_fout())
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert MARKER not in uitvoer, uitvoer

    def test_ontbrekende_tools_zijn_ongeldig(self):
        gevallen = (
            ("geen rg", _bindir(rg=None, git=GIT)),
            ("geen git", _bindir(rg=RG, git=None)),
            ("geen tools", _bindir()),
        )
        for naam, bindir in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(), bindir)

                assert (
                    proc.returncode == 2
                ), "zonder werkende tools is er geen scan, geen stille terugval"


class TestPreflightOnafhankelijk(unittest.TestCase):
    """De gate staat op zichzelf: geen persoonlijk script, geen HOME-terugval."""

    def test_omgeving_van_de_gate_kent_geen_home(self):
        """Opzetcontrole voor de test hieronder.

        Zonder deze controle zou een omgeving die HOME alsnog doorgeeft de
        onafhankelijkheidstest stilzwijgend waardeloos maken: hij zou groen
        blijven terwijl er wél een homedir beschikbaar was.
        """
        env = _gate_env(_new_dir("bin"))

        assert "HOME" not in env, env
        assert not any(sleutel.endswith("HOME") for sleutel in env), env

    def test_ripgrep_config_kan_de_scan_niet_versmallen(self):
        """Een ripgreprc uit de omgeving mag geen bestanden wegfilteren.

        `RIPGREP_CONFIG_PATH` kan globs toevoegen. Zonder `--no-config` zou deze
        fixture alle Python-bestanden uitsluiten: de blokkerende treffer valt
        weg en de scope raakt leeg, dus de gate zegt iets anders dan hij zonder
        die configuratie zou zeggen. De fixtureconfig staat in een verse
        tijdelijke map; persoonlijke configuratie wordt niet aangeraakt.
        """
        config = _new_dir("rgconfig") / "ripgreprc"
        config.write_text("--glob=!*.py\n", encoding="utf-8")
        repo = _repo(services=(("verdacht.py", STREAMLIT_BRON),))

        proc = _run(
            repo, _echte_tools(), extra_env={"RIPGREP_CONFIG_PATH": str(config)}
        )
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert f"preflight: BLOCK {BLOK_STREAMLIT}" in uitvoer, uitvoer

    def test_globale_gitconfig_wordt_niet_gelezen(self):
        """Git mag geen configuratie uit de omgeving betrekken.

        De fixture wijst `GIT_CONFIG_GLOBAL` naar een bestand met kapotte
        syntax: leest git het, dan faalt elk git-commando en wordt de scan
        ongeldig. De gate hoort zijn eigen `GIT_CONFIG_GLOBAL` te zetten, zodat
        dit bestand nooit meetelt.
        """
        kapot = _new_dir("gitconfig") / "config"
        kapot.write_text("[core\n", encoding="utf-8")

        proc = _run(
            _repo(), _echte_tools(), extra_env={"GIT_CONFIG_GLOBAL": str(kapot)}
        )
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: error=" not in uitvoer, uitvoer

    def test_draait_zonder_home_in_de_omgeving(self):
        """De ingecheckte gate mag niet leunen op een script buiten de repository.

        Op een CI-runner bestaat zo een persoonlijk script niet, en dan zou de
        preflight stilzwijgend iets anders doen dan lokaal. Hier is er geen
        homedir om op terug te vallen: de scan hoort gewoon te slagen.
        """
        proc = _run(_repo(), _echte_tools())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "preflight: error=" not in uitvoer, uitvoer


if __name__ == "__main__":
    unittest.main()
