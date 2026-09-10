#!/usr/bin/env python3
"""Tests voor de bronblokkades van de quarantaine (DEF-666).

Hermetisch: standaard-library `unittest` + `subprocess`. Geen app-imports, geen
conftest, geen netwerk, geen externe pakketten. Tijdelijke mappen blijven
bewust staan; er wordt niets verwijderd.

Scope van deze suite is uitsluitend de **bron**: de 49 bestanden uit
`scripts/ci/quarantine_manifest.json` dragen een blokkade die vóór hun eerste
bijwerking ligt. De manifestintegriteit en de automatische ingangen horen bij de
checker en staan in `test_quarantine_integrity.py`.

Verwachte blokkadevormen
------------------------
Python  eerste uitvoerbare statement, ná docstring en echte future-imports:
        ``raise RuntimeError("<sentinel>: <pad> ...")`` met één stringconstante.
Shell   exact twee regels direct na de shebang: een vaste `printf` naar stderr
        en ``return 92 2>/dev/null || exit 92`` (sourcen stopt, aanroeper leeft).
Make    eerste betekenisvolle regel: een zelfstandige ``$(error ...)`` op kolom 0.

VEILIGHEID — hard contract
--------------------------
Er draait nooit ongeblokkeerde originele toolcode. Elke gedragstest doet eerst
de kleine, lokale statische controle op het échte bestand. Faalt die, dan stopt
de subtest daar en wordt er niets gestart: een ontbrekende blokkade faalt dus
uitsluitend structureel. Pas na die controle draait een **verse kopie van exact
die bytes** in een verse tijdelijke werkmap, met begrensde looptijd en een
opgeschoonde omgeving. Mapmomentopnames tonen aan dat er geen bijwerking is.

`scripts/backup_restore.py` is gemengd: alleen zijn identiteit wordt hier
getoetst. Zijn methode- en CLI-grenzen staan in
`tests/unit/scripts/test_backup_restore_def666.py`.

De assertie-stijl volgt de overige `scripts/ci`-suites: gewone `assert` voor
uitkomsten. De Make-doelen draaien deze bestanden met `-I`, wat `PYTHONOPTIMIZE`
uit de omgeving negeert. Dat beschermt níet tegen een uitdrukkelijk meegegeven
`-O` op de commandoregel; dan verdwijnen die asserts wel. De drie
uitvoeringsvoorwaarden (`assert_python_guard`, `assert_shell_guard`,
`assert_make_guard`) gebruiken daarom een expliciete `raise AssertionError`,
want zij zijn de poort die verhindert dat ongeblokkeerde originele code draait.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "scripts" / "ci" / "quarantine_manifest.json"

SENTINEL = "DEF-666-QUARANTINE-GUARD"
GUARD_EXIT_STATUS = 92
CHILD_TIMEOUT_SECONDS = 60

#: Opstartvariabelen die een kindproces stiekem code kunnen laten laden.
STRIPPED_ENV = (
    "BASH_ENV",
    "ENV",
    "SHELLOPTS",
    "BASHOPTS",
    "CDPATH",
    "MAKEFLAGS",
    "MAKEFILES",
    "PYTHONSTARTUP",
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONOPTIMIZE",
    "PYTHONINSPECT",
    "PYTHONWARNINGS",
)

PYTHON_MODULE_PATHS = (
    "scripts/analyse/hernoem-naar-nederlands.py",
    "scripts/analysis/analyze_dependencies.py",
    "scripts/architecture-tools/architecture_sync.py",
    "scripts/archive_data.py",
    "scripts/docs/fix_links.py",
    "scripts/docs/fix_requirements_frontmatter.py",
    "scripts/docs/generate_source_tree.py",
    "scripts/docs/normalize_all_frontmatter.py",
    "scripts/docs/normalize_documentation.py",
    "scripts/docs/translate_docs_to_dutch.py",
    "scripts/docs/translate_to_dutch.py",
    "scripts/docs/update_traceability.py",
    "scripts/export_baseline_definitions.py",
    "scripts/fix_definities_old_fk.py",
    "scripts/fix_unicode_chars.py",
    "scripts/import_from_txt_exports.py",
    "scripts/maintenance/cleanup_nan_contexts.py",
    "scripts/maintenance/document_cleanup.py",
    "scripts/maintenance/fix_broken_links.py",
    "scripts/maintenance/fix_requirements.py",
    "scripts/maintenance/fix_requirements_v2.py",
    "scripts/maintenance/fix_smart_compliance.py",
    "scripts/maintenance/fix_translation_issues.py",
    "scripts/maintenance/remove_history_tab.py",
    "scripts/maintenance/remove_legacy_methods.py",
    "scripts/migrate_data.py",
    "scripts/migrate_synonym_tables.py",
    "scripts/migrate_synonyms_to_registry.py",
    "scripts/recover_voorbeelden.py",
    "scripts/restore_orphaned_voorbeelden.py",
    "scripts/testing/verify_history_removal.py",
    "scripts/update_us_titles.py",
    "scripts/validate_synonym_registry.py",
)

SHELL_PATHS = (
    "docs/archiveer-simpel.sh",
    "docs/reorganize-docs.sh",
    "scripts/analysis/agent_scoreboard.sh",
    "scripts/deployment/multiagent.sh",
    "scripts/deployment/setup-ai-review.sh",
    "scripts/deployment/setup_ai_review.sh",
    "scripts/docs/renumber_requirements.sh",
    "scripts/docs/restructure_backlog.sh",
    "scripts/hooks/run_black_changed.sh",
    "scripts/hooks/run_ruff_changed.sh",
    "scripts/maintenance/clean_openai_keys.sh",
    "scripts/maintenance/remove_history_tab.sh",
    "scripts/testing/quick_verify_history_removal.sh",
    "scripts/testing/verify_history_removal.sh",
)

MAKE_PATH = "scripts/testing/Makefile.history_removal"
MIXED_PATH = "scripts/backup_restore.py"
ALL_PATHS = frozenset(PYTHON_MODULE_PATHS + SHELL_PATHS + (MAKE_PATH, MIXED_PATH))

SENTINEL_FILE = "SENTINEL_WRITTEN"


# --------------------------------------------------------------------------
# Kleine hulpjes
# --------------------------------------------------------------------------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def new_workdir(prefix: str) -> Path:
    """Verse tijdelijke map; blijft bewust staan als bewijsmateriaal."""
    return Path(tempfile.mkdtemp(prefix=f"def666-{prefix}-"))


def snapshot(directory: Path) -> dict[str, str]:
    """Recursieve, inhoudsgevoelige momentopname: relatief pad -> vingerafdruk.

    Namen alleen volstaan niet: het wijzigen van een bestaand bestand moet net
    zo goed opvallen als het aanmaken van een nieuw bestand.
    """
    result: dict[str, str] = {}
    for entry in sorted(directory.rglob("*")):
        key = entry.relative_to(directory).as_posix()
        if entry.is_symlink():
            result[key] = f"symlink:{os.readlink(entry)}"
        elif entry.is_dir():
            result[key] = "dir"
        else:
            result[key] = f"file:{hashlib.sha256(entry.read_bytes()).hexdigest()}"
    return result


def child_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}
    env["LC_ALL"] = "C"
    return env


def run_child(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=child_env(),
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise AssertionError(f"'{name}' is vereist voor deze gedragstest")
    return found


def expected_shell_guard(rel_path: str) -> tuple[str, str]:
    return (
        "printf '%s\\n' '" + SENTINEL + ": " + rel_path + " is bij de bron "
        "uitgeschakeld.' >&2",
        "return 92 2>/dev/null || exit 92",
    )


def expected_make_guard(rel_path: str) -> str:
    return f"$(error {SENTINEL}: {rel_path} is bij de bron uitgeschakeld)"


def copy_checked_bytes(raw: bytes, workdir: Path, name: str) -> Path:
    """Schrijf exact de bytes die de precheck heeft gezien.

    De bron wordt één keer van schijf gelezen; daarna wordt uitsluitend die
    buffer gecontroleerd, weggeschreven en uitgevoerd. Tussen de controle en de
    uitvoering kan er dus niets meer wisselen. Het origineel draait nooit.
    """
    target = workdir / name
    target.write_bytes(raw)
    return target


# --------------------------------------------------------------------------
# Lokale statische prechecks (moeten vóór elke uitvoering slagen)
# --------------------------------------------------------------------------


def python_guard_node(source: str) -> ast.stmt | None:
    """Eerste uitvoerbare statement na docstring en echte future-imports."""
    body = ast.parse(source).body
    index = 0
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        index = 1
    while index < len(body):
        node = body[index]
        if not isinstance(node, ast.ImportFrom) or node.module != "__future__":
            break
        index += 1
    return body[index] if index < len(body) else None


def is_constant_sentinel_raise(node: ast.stmt | None, prefix: str) -> bool:
    """``raise RuntimeError("<prefix>...")`` met precies één stringconstante.

    Een aanroep of samengestelde expressie als argument wordt geweigerd: die
    kan zelf een bijwerking hebben. Een `assert` wordt geweigerd omdat `-O` die
    verwijdert.
    """
    if not isinstance(node, ast.Raise) or node.cause is not None:
        return False
    exc = node.exc
    if not isinstance(exc, ast.Call) or exc.keywords or len(exc.args) != 1:
        return False
    if not isinstance(exc.func, ast.Name) or exc.func.id != "RuntimeError":
        return False
    message = exc.args[0]
    return (
        isinstance(message, ast.Constant)
        and isinstance(message.value, str)
        and message.value.startswith(prefix)
    )


def assert_python_guard(rel_path: str, source: str) -> None:
    """Voorwaarde die vóór élke uitvoering van een echte kopie moet slagen.

    Bewust een expliciete ``raise AssertionError`` en géén ``assert``: met een
    uitdrukkelijk meegegeven ``-O`` verdwijnt een assert uit de bytecode, en dan
    zou een ongeblokkeerd origineel alsnog worden uitgevoerd. Deze poort moet
    ook dan dichtblijven. Voor gewone uitkomstcontroles verderop geldt de
    normale `assert`-conventie van de `scripts/ci`-suites.
    """
    node = python_guard_node(source)
    if not is_constant_sentinel_raise(node, f"{SENTINEL}: {rel_path} "):
        gezien = type(node).__name__ if node is not None else "niets"
        raise AssertionError(
            f"{rel_path}: eerste uitvoerbare statement is geen canonieke "
            f'raise RuntimeError("{SENTINEL}: {rel_path} ...") maar {gezien}'
        )


def assert_shell_guard(rel_path: str, source: str) -> None:
    """Uitvoeringsvoorwaarde; expliciete raise, zie `assert_python_guard`."""
    lines = source.splitlines()
    if len(lines) < 3:
        raise AssertionError(f"{rel_path}: te kort voor de blokkade")
    if not lines[0].startswith("#!"):
        raise AssertionError(f"{rel_path}: regel 1 geen shebang")
    first, second = expected_shell_guard(rel_path)
    if lines[1] != first:
        raise AssertionError(f"{rel_path}: regel 2 niet de vaste printf")
    if lines[2] != second:
        raise AssertionError(f"{rel_path}: regel 3 niet return/exit 92")


def assert_make_guard(rel_path: str, source: str) -> None:
    """Uitvoeringsvoorwaarde; expliciete raise, zie `assert_python_guard`."""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line != expected_make_guard(rel_path):
            raise AssertionError(
                f"{rel_path}: eerste betekenisvolle regel is niet de zelfstandige "
                "$(error ...) op kolom 0"
            )
        return
    raise AssertionError(f"{rel_path}: geen betekenisvolle regel gevonden")


def exec_module_expecting_guard(spec, module, rel_path: str) -> str:
    """Voer de modulebody uit en geef de melding van de blokkade terug.

    Bytecode-schrijven staat uit: een `__pycache__` in de werkmap zou de
    inhoudsgevoelige momentopname vervuilen en een echte bijwerking maskeren.
    """
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except RuntimeError as exc:
        return str(exc)
    finally:
        sys.dont_write_bytecode = previous
    raise AssertionError(f"{rel_path}: de blokkade heeft de import niet gestopt")


# --------------------------------------------------------------------------
# 1. Identiteiten
# --------------------------------------------------------------------------


class TestInventoryIdentities(unittest.TestCase):
    """De 49 paden liggen vast en wijzen naar gewone bestanden."""

    def test_manifest_holds_exactly_the_forty_nine_frozen_paths(self):
        entries = json.loads(read_text(MANIFEST_PATH))["entries"]
        assert len(entries) == 49
        assert {e["path"] for e in entries} == set(ALL_PATHS)
        assert len(PYTHON_MODULE_PATHS) == 33
        assert len(SHELL_PATHS) == 14
        assert len(ALL_PATHS) == 49

    def test_every_source_is_a_regular_file(self):
        for rel_path in sorted(ALL_PATHS):
            with self.subTest(path=rel_path):
                path = REPO_ROOT / rel_path
                assert not path.is_symlink(), "symlink nooit toegestaan"
                assert path.is_file(), "bronbestand ontbreekt"


# --------------------------------------------------------------------------
# 2. Statische blokkadecontrole op de échte bron
# --------------------------------------------------------------------------


class TestSourceGuardsPresent(unittest.TestCase):
    """Elke bron draagt de blokkade op de eerste uitvoerbare positie."""

    def test_thirty_three_python_modules_carry_the_canonical_guard(self):
        for rel_path in PYTHON_MODULE_PATHS:
            with self.subTest(path=rel_path):
                assert_python_guard(rel_path, read_text(REPO_ROOT / rel_path))

    def test_fourteen_shell_scripts_carry_the_canonical_guard(self):
        for rel_path in SHELL_PATHS:
            with self.subTest(path=rel_path):
                assert_shell_guard(rel_path, read_text(REPO_ROOT / rel_path))

    def test_make_wrapper_carries_a_parse_time_guard(self):
        source = read_text(REPO_ROOT / MAKE_PATH)
        assert_make_guard(MAKE_PATH, source)
        for line in source.splitlines():
            if SENTINEL in line:
                assert not line.startswith(
                    "\t"
                ), "$(error ...) op een TAB-regel expandeert pas bij uitvoering"


# --------------------------------------------------------------------------
# 3. Gedrag van de geblokkeerde bron — pas ná de precheck
# --------------------------------------------------------------------------


class TestGuardedPythonBehaviour(unittest.TestCase):
    """CLI (ook onder -O) en import zijn dicht; er blijft niets gebonden."""

    def test_all_thirty_three_block_cli_and_import(self):
        for rel_path in PYTHON_MODULE_PATHS:
            with self.subTest(path=rel_path):
                raw = (REPO_ROOT / rel_path).read_bytes()
                source = raw.decode("utf-8")
                assert_python_guard(rel_path, source)  # geen guard -> geen run
                workdir = new_workdir("py")
                copy = copy_checked_bytes(raw, workdir, Path(rel_path).name)
                before = snapshot(workdir)

                for flags in (["-I", "-S", "-B"], ["-I", "-S", "-B", "-O"]):
                    with self.subTest(route=" ".join(flags)):
                        result = run_child([sys.executable, *flags, str(copy)], workdir)
                        assert result.returncode != 0, result.stdout
                        assert SENTINEL in result.stderr, result.stderr

                with self.subTest(route="importlib"):
                    tree = ast.parse(source)
                    bound: set[str] = set()
                    for node in tree.body:
                        if isinstance(
                            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                        ):
                            bound.add(node.name)
                        elif isinstance(node, ast.Assign):
                            bound.update(
                                t.id for t in node.targets if isinstance(t, ast.Name)
                            )
                    assert bound, "geen top-level naam gevonden"

                    name = "def666_probe"
                    spec = importlib.util.spec_from_file_location(name, copy)
                    assert spec is not None and spec.loader is not None
                    module = importlib.util.module_from_spec(spec)
                    melding = exec_module_expecting_guard(spec, module, rel_path)
                    assert SENTINEL in melding, melding
                    assert name not in sys.modules
                    for attribute in sorted(bound):
                        assert not hasattr(
                            module, attribute
                        ), f"{attribute} is toch gebonden na de mislukte import"

                assert snapshot(workdir) == before, "bijwerking gezien"


class TestGuardedShellBehaviour(unittest.TestCase):
    """Directe route stopt met 92; sourcen stopt zonder de aanroeper te doden."""

    def test_all_fourteen_block_direct_and_sourced_routes(self):
        bash = tool("bash")
        posix_sh = tool("sh")
        script = (
            '. "$1"; status=$?; printf "SOURCED_STATUS=%s\\n" "$status"; '
            'printf "CALLER_ALIVE\\n"'
        )
        for rel_path in SHELL_PATHS:
            with self.subTest(path=rel_path):
                raw = (REPO_ROOT / rel_path).read_bytes()
                assert_shell_guard(rel_path, raw.decode("utf-8"))
                workdir = new_workdir("sh")
                copy = copy_checked_bytes(raw, workdir, Path(rel_path).name)
                before = snapshot(workdir)

                for interpreter in (bash, posix_sh):
                    with self.subTest(route=Path(interpreter).name):
                        result = run_child([interpreter, str(copy)], workdir)
                        assert result.returncode == GUARD_EXIT_STATUS, result.stderr
                        assert SENTINEL in result.stderr, result.stderr

                with self.subTest(route="sourced"):
                    # De aanroeper eindigt bewust op 0; alleen de opgevangen
                    # status ván het sourcen bewijst de blokkade.
                    result = run_child([bash, "-c", script, "bash", str(copy)], workdir)
                    assert (
                        f"SOURCED_STATUS={GUARD_EXIT_STATUS}" in result.stdout
                    ), result.stdout
                    assert "CALLER_ALIVE" in result.stdout, result.stdout
                    assert SENTINEL in result.stderr, result.stderr

                assert snapshot(workdir) == before, "bijwerking gezien"


class TestGuardedMakeBehaviour(unittest.TestCase):
    """De wrapper faalt bij het inlezen, dus ook bij -n, -q en include."""

    def test_explicit_goal_dry_run_question_and_include_all_fail(self):
        make = tool("make")
        raw = (REPO_ROOT / MAKE_PATH).read_bytes()
        assert_make_guard(MAKE_PATH, raw.decode("utf-8"))

        for extra in (["help"], ["-n", "verify-history-removal"], ["-q", "help"]):
            with self.subTest(route=" ".join(extra)):
                workdir = new_workdir("make")
                copy = copy_checked_bytes(raw, workdir, "Makefile.history_removal")
                before = snapshot(workdir)
                result = run_child([make, "-f", str(copy), *extra], workdir)
                assert result.returncode != 0, result.stdout
                assert SENTINEL in result.stdout + result.stderr, result.stderr
                assert snapshot(workdir) == before, "bijwerking gezien"

        with self.subTest(route="include"):
            workdir = new_workdir("make-include")
            copy = copy_checked_bytes(raw, workdir, "Makefile.history_removal")
            (workdir / "Makefile").write_text(
                f"include {copy.name}\n\nharmless:\n\t@echo BEREIKT\n",
                encoding="utf-8",
            )
            before = snapshot(workdir)
            result = run_child([make, "harmless"], workdir)
            assert result.returncode != 0, result.stdout
            assert SENTINEL in result.stdout + result.stderr, result.stderr
            assert "BEREIKT" not in result.stdout, result.stdout
            assert snapshot(workdir) == before, "bijwerking gezien"


# --------------------------------------------------------------------------
# 4. Synthetisch: de guardvórm voorkomt de eerste schrijfactie
# --------------------------------------------------------------------------


class TestSyntheticGuardPreventsFirstWrite(unittest.TestCase):
    """Drie minimale nagemaakte tools met een onschuldige sentinelschrijfactie.

    Dit bewijst de vórm, niet een concreet echt bestand; daarvoor gelden de
    klassen hierboven.
    """

    def test_python_guard_prevents_the_write(self):
        workdir = new_workdir("synth-py")
        script = workdir / "tool.py"
        script.write_text(
            f'"""Synthetisch."""\nraise RuntimeError("{SENTINEL}: tool.py is bij '
            'de bron uitgeschakeld.")\nfrom pathlib import Path\n'
            f'Path("{SENTINEL_FILE}").write_text("bereikt", encoding="utf-8")\n',
            encoding="utf-8",
        )
        before = snapshot(workdir)
        result = run_child([sys.executable, "-I", "-S", "-B", str(script)], workdir)
        assert result.returncode != 0, result.stdout
        assert snapshot(workdir) == before

    def test_shell_guard_prevents_the_write(self):
        workdir = new_workdir("synth-sh")
        script = workdir / "tool.sh"
        first, second = expected_shell_guard("tool.sh")
        script.write_text(
            f"#!/usr/bin/env bash\n{first}\n{second}\ntouch {SENTINEL_FILE}\n",
            encoding="utf-8",
        )
        before = snapshot(workdir)
        result = run_child([tool("bash"), str(script)], workdir)
        assert result.returncode == GUARD_EXIT_STATUS, result.stderr
        assert snapshot(workdir) == before

    def test_make_guard_prevents_the_write(self):
        workdir = new_workdir("synth-mk")
        (workdir / "Makefile").write_text(
            f"{expected_make_guard('Makefile')}\n\nall:\n\t@touch {SENTINEL_FILE}\n",
            encoding="utf-8",
        )
        before = snapshot(workdir)
        result = run_child([tool("make"), "all"], workdir)
        assert result.returncode != 0, result.stdout
        assert snapshot(workdir) == before


if __name__ == "__main__":
    unittest.main(verbosity=2)
