"""RED-tests voor de gemengde bronblokkade van ``scripts/backup_restore.py`` (DEF-666).

`restore_backup` en `clean_old_backups` moeten bij de bron dicht, terwijl de
DEF-663-backupcreatie en -verificatie blijven werken. De bestaande 26 tests in
`test_backup_restore_script.py` blijven byte-identiek en gelden als het
gezaghebbende positieve bewijs; hier staat alleen wat daar niet in zit.

VEILIGHEID — hard contract
--------------------------
Elke test doet eerst een kleine, onafhankelijke structurele controle op de bron.
Ontbreekt de blokkade, dan faalt de test dáár — vóór het laden van de module en
vóór elke aanroep van de gevaarlijke code. De methodetests draaien op een
niet-geïnitialiseerd exemplaar met vijandige attributen, zodat een te late
blokkade zich meldt als een assertiefout en niet als echte I/O. De CLI draait
uitsluitend in een verse tijdelijke werkmap met expliciete tijdelijke paden.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = [pytest.mark.unit]

SENTINEL = "DEF-666-QUARANTINE-GUARD"
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "backup_restore.py"
BLOCKED_ACTIONS = ("clean", "restore")
CHILD_TIMEOUT_SECONDS = 60
STRIPPED_ENV = ("PYTHONSTARTUP", "PYTHONPATH", "PYTHONHOME", "PYTHONOPTIMIZE")

#: Niet-lege inhoud, zodat een aanraking van de database zichtbaar wordt. Een
#: leeg bestand zou een overschrijving met niets kunnen verbergen.
DB_SENTINEL = b"DEF-666-DB-SENTINEL: deze bytes mogen niet wijzigen\n"


# ---------------------------------------------------------------------------
# Structurele hulpjes (lezen alleen; voeren nooit iets uit)
# ---------------------------------------------------------------------------


def _tree() -> ast.Module:
    return ast.parse(SCRIPT.read_text(encoding="utf-8"))


def _named(body: list[ast.stmt], kind: type, name: str):
    for node in body:
        if isinstance(node, kind) and node.name == name:
            return node
    pytest.fail(f"{name} niet gevonden in scripts/backup_restore.py")


def _calls(node: ast.AST, owner: str | None, attribute: str) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Attribute):
            continue
        if child.func.attr != attribute:
            continue
        if owner is None:
            return True
        if isinstance(child.func.value, ast.Name) and child.func.value.id == owner:
            return True
    return False


def _is_docstring(node: ast.stmt) -> bool:
    """Alleen een echte stringconstante telt als docstring.

    Elk ander `ast.Expr` is een uitdrukking die bij aanroep draait; die mag
    nooit stilzwijgend worden overgeslagen bij het zoeken naar de blokkade.
    """
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_constant_sentinel_raise(node: ast.stmt) -> bool:
    """``raise RuntimeError("<sentinel>: ...")`` met één stringconstante."""
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
        and message.value.startswith(f"{SENTINEL}: ")
    )


def _require_method_guard(name: str) -> None:
    """Precheck: de methode begint onvoorwaardelijk met de blokkade."""
    manager = _named(_tree().body, ast.ClassDef, "DatabaseBackupManager")
    body = _named(manager.body, ast.FunctionDef, name).body
    index = 1 if body and _is_docstring(body[0]) else 0
    if index >= len(body) or not _is_constant_sentinel_raise(body[index]):
        pytest.fail(
            f"{name}: eerste statement na de docstring is geen onvoorwaardelijke "
            f'raise RuntimeError("{SENTINEL}: ...") met statische diagnose'
        )


def _is_action_rejection(node: ast.stmt) -> bool:
    """``if args.action in (...): parser.error("<sentinel>: ...")``."""
    if not isinstance(node, ast.If) or node.orelse or len(node.body) != 1:
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    left = test.left
    if not (
        isinstance(test.ops[0], ast.In)
        and isinstance(left, ast.Attribute)
        and left.attr == "action"
        and isinstance(left.value, ast.Name)
        and left.value.id == "args"
    ):
        return False
    container = test.comparators[0]
    if not isinstance(container, (ast.Tuple, ast.List, ast.Set)):
        return False
    # Elk element moet een stringconstante zijn. Filteren zou een aanroep of
    # berekende waarde in de set stilzwijgend accepteren; die kan bijwerkingen
    # hebben en de afgewezen verzameling ongemerkt verschuiven.
    constants = [
        element.value
        for element in container.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    ]
    if len(constants) != len(container.elts):
        return False
    if set(constants) != set(BLOCKED_ACTIONS):
        return False
    statement = node.body[0]
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return False
    call = statement.value
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "error"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "parser"
        and not call.keywords
        and len(call.args) == 1
        and isinstance(call.args[0], ast.Constant)
        and isinstance(call.args[0].value, str)
        and call.args[0].value.startswith(f"{SENTINEL}: ")
    )


def _require_cli_guard() -> None:
    """Precheck: afwijzing staat direct ná parse_args en vóór elke mkdir."""
    body = _named(_tree().body, ast.FunctionDef, "main").body
    parse = next(
        (
            i
            for i, s in enumerate(body)
            if isinstance(s, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "args" for t in s.targets)
            and _calls(s, "parser", "parse_args")
        ),
        -1,
    )
    if parse < 0 or parse + 1 >= len(body):
        pytest.fail("main() mist `args = parser.parse_args()` met een opvolger")
    if not _is_action_rejection(body[parse + 1]):
        pytest.fail(
            "het statement direct na parse_args() wijst niet exact "
            f"{sorted(BLOCKED_ACTIONS)} af via parser.error() met een constante "
            f"{SENTINEL}-diagnose"
        )
    mkdir = next((i for i, s in enumerate(body) if _calls(s, None, "mkdir")), -1)
    if mkdir <= parse + 1:
        pytest.fail("de eerste mkdir in main() staat niet ná de afwijzing")


def _import_executed_nodes(tree: ast.Module) -> list[ast.AST]:
    """Knopen die bij het importeren van dít bestand daadwerkelijk draaien.

    Bewust geen algemene analyse: er wordt alleen niet afgedaald in functie- en
    lambdalichamen, omdat die pas bij aanroep draaien — precies de plek waar de
    logbestandconfiguratie hoort te staan. Decorators en standaardwaarden van
    een functie worden wél bij import geëvalueerd en tellen dus mee, net als
    klasselichamen.
    """
    collected: list[ast.AST] = []
    stack: list[ast.AST] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.extend(node.decorator_list)
            stack.extend(node.args.defaults)
            stack.extend(d for d in node.args.kw_defaults if d is not None)
            continue
        if isinstance(node, ast.Lambda):
            continue
        collected.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return collected


def _require_import_is_write_free() -> None:
    for node in _import_executed_nodes(_tree()):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"basicConfig", "FileHandler"}:
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "logging":
            pytest.fail(
                f"logging.{node.func.attr} draait bij import en maakt dan een "
                "logbestand aan; die configuratie hoort in main(), ná de "
                "afwijzing van de geblokkeerde acties"
            )


# ---------------------------------------------------------------------------
# Uitvoeringshulpjes
# ---------------------------------------------------------------------------


def _tree_snapshot(directory: Path) -> dict[str, str]:
    """Recursieve, inhoudsgevoelige momentopname van een tijdelijke map.

    Namen alleen volstaan niet: het wijzigen van een bestaand bestand moet net
    zo goed opvallen als het aanmaken van een nieuw bestand.
    """
    snapshot: dict[str, str] = {}
    for entry in sorted(directory.rglob("*")):
        key = entry.relative_to(directory).as_posix()
        if entry.is_symlink():
            snapshot[key] = f"symlink:{os.readlink(entry)}"
        elif entry.is_dir():
            snapshot[key] = "dir"
        else:
            snapshot[key] = f"file:{hashlib.sha256(entry.read_bytes()).hexdigest()}"
    return snapshot


class _Vijandig:
    """Elke aanraking is een fout, dus een te late blokkade doet geen I/O."""

    def __getattr__(self, name: str):
        raise AssertionError(f"blokkade te laat: .{name} werd benaderd")

    def __fspath__(self) -> str:
        raise AssertionError("blokkade te laat: het pad werd omgezet")


def _load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Laad het script in een verse werkmap, zonder bytecode achter te laten."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    spec = importlib.util.spec_from_file_location("backup_restore_def666", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_cli(argv: list[str], cwd: Path, db: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(SCRIPT),
            *argv,
            "--db-path",
            str(db),
            "--backup-dir",
            str(cwd / "backups"),
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("methode", ["restore_backup", "clean_old_backups"])
def test_gevaarlijke_methode_weigert_voor_elke_aanraking(
    methode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _require_method_guard(methode)  # ontbreekt de blokkade: hier stoppen
    module = _load(tmp_path, monkeypatch)
    manager = object.__new__(module.DatabaseBackupManager)
    manager.db_path = _Vijandig()
    manager.backup_dir = _Vijandig()
    manager.compress = True

    argumenten = (_Vijandig(),) if methode == "restore_backup" else ()
    with pytest.raises(RuntimeError, match=SENTINEL):
        getattr(manager, methode)(*argumenten)

    assert list(tmp_path.iterdir()) == []


def test_import_maakt_geen_logbestand_aan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Importeren mag niets schrijven, ook niet zonder bestaande `logs/`-map."""
    _require_import_is_write_free()
    module = _load(tmp_path, monkeypatch)

    assert hasattr(module, "DatabaseBackupManager")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("actie", "opties"),
    [
        ("restore", []),
        ("restore", ["--no-safety-backup"]),
        ("clean", []),
        ("clean", ["--dry-run"]),
        ("clean", ["--days", "1", "--keep-minimum", "1"]),
    ],
    ids=[
        "restore",
        "restore-zonder-safety",
        "clean",
        "clean-dry-run",
        "clean-retentie",
    ],
)
def test_cli_weigert_geblokkeerde_actie_voor_elke_mapaanmaak(
    actie: str, opties: list[str], tmp_path: Path
):
    _require_cli_guard()  # ontbreekt de grens: hier stoppen, geen CLI starten
    db = tmp_path / "definities.db"
    db.write_bytes(DB_SENTINEL)
    positioneel = [str(tmp_path / "archief.db.gz")] if actie == "restore" else []
    before = _tree_snapshot(tmp_path)

    result = _run_cli([actie, *positioneel, *opties], tmp_path, db)

    assert result.returncode != 0
    assert SENTINEL in result.stderr
    assert not (tmp_path / "logs").exists(), "logmap aangemaakt vóór de afwijzing"
    assert not (tmp_path / "backups").exists(), "backupmap aangemaakt vóór de afwijzing"
    assert db.read_bytes() == DB_SENTINEL, "de database is aangeraakt"
    assert _tree_snapshot(tmp_path) == before, "bijwerking vóór de afwijzing"


def test_veilige_cli_acties_blijven_werken(tmp_path: Path):
    """Positieve controle: `list` en `verify` overleven de bronblokkade."""
    _require_cli_guard()
    db = tmp_path / "definities.db"
    db.write_bytes(DB_SENTINEL)

    listing = _run_cli(["list"], tmp_path, db)
    assert listing.returncode == 0
    assert "No backups found" in listing.stdout
    assert (tmp_path / "backups").is_dir()
    assert db.read_bytes() == DB_SENTINEL, "opsommen mag de database niet aanraken"

    kapot = tmp_path / "kapot.db"
    kapot.write_bytes(b"geen geldige sqlite-database")
    verify = _run_cli(["verify", str(kapot)], tmp_path, db)
    assert verify.returncode == 1
    assert "invalid" in verify.stdout.lower()
