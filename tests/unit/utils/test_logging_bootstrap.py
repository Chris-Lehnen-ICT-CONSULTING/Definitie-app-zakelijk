"""Tests voor de gedeelde logging-bootstrap (DEF-571).

Achtergrond: `install_pii_redaction_filter()` werd alleen vanuit `main.py`
aangeroepen. Streamlit draait `main.py` NIET bij directe navigatie naar een
subpagina (dezelfde root-cause als DEF-572), waardoor de PII-redactie op
`/synonym_admin` ontbrak — juist de pagina die de synoniem-term logt.
"""

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

import logging

from utils.logging_bootstrap import ensure_logging_configured
from utils.logging_filters import PIIRedactingFilter


@pytest.fixture
def schone_root():
    """Isoleer de root-logger: bewaar en herstel handlers rond elke test."""
    root = logging.getLogger()
    originele_handlers = list(root.handlers)
    origineel_level = root.level
    root.handlers = []
    try:
        yield root
    finally:
        root.handlers = originele_handlers
        root.setLevel(origineel_level)


def _filters(root: logging.Logger) -> list[PIIRedactingFilter]:
    return [
        f for h in root.handlers for f in h.filters if isinstance(f, PIIRedactingFilter)
    ]


def test_bootstrap_maakt_handler_aan_als_die_ontbreekt():
    """Kern: install_pii_redaction_filter() is een no-op zonder handlers.

    Draait in een schoon subprocess: pytest hangt zelf een LogCaptureHandler op
    de root-logger, waardoor het 'geen handlers'-geval in-process niet na te
    bootsen is — en de test het echte productiegedrag zou maskeren.
    """
    import subprocess
    import sys as _sys

    repo_root = Path(__file__).resolve().parents[3]
    script = (
        "import logging;"
        "assert not logging.getLogger().handlers, 'root had al handlers';"
        "from utils.logging_bootstrap import ensure_logging_configured;"
        "from utils.logging_filters import PIIRedactingFilter;"
        "ensure_logging_configured();"
        "hs = logging.getLogger().handlers;"
        "assert hs, 'geen handler aangemaakt';"
        "assert all(any(isinstance(f, PIIRedactingFilter) for f in h.filters) for h in hs);"
        "print('OK')"
    )
    resultaat = subprocess.run(
        [_sys.executable, "-c", script],
        cwd=repo_root,
        env={"PYTHONPATH": str(repo_root / "src"), "PATH": ""},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,  # returncode wordt hieronder expliciet geassert
    )
    assert resultaat.returncode == 0, resultaat.stderr
    assert "OK" in resultaat.stdout


def test_bootstrap_installeert_pii_filter_op_elke_handler(schone_root):
    ensure_logging_configured()
    for handler in schone_root.handlers:
        assert any(isinstance(f, PIIRedactingFilter) for f in handler.filters)


def test_bootstrap_is_idempotent(schone_root):
    ensure_logging_configured()
    aantal_na_eerste = len(_filters(schone_root))
    ensure_logging_configured()
    ensure_logging_configured()
    assert len(_filters(schone_root)) == aantal_na_eerste


def test_bootstrap_respecteert_bestaande_handlers(schone_root):
    # Als er al een handler is (bv. door Streamlit of dictConfig), mag de
    # bootstrap die niet vervangen — alleen de filter eraan hangen.
    eigen = logging.StreamHandler()
    schone_root.addHandler(eigen)
    ensure_logging_configured()
    assert eigen in schone_root.handlers
    assert any(isinstance(f, PIIRedactingFilter) for f in eigen.filters)


def test_bootstrap_redigeert_pii_uit_child_logger(schone_root):
    # End-to-end: een child-logger (getLogger(__name__)) die een e-mailadres
    # als %s-argument logt, mag dat niet ongeredigeerd doorlaten.
    ensure_logging_configured()
    stream: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            stream.append(self.format(record))

    capture = _Capture()
    schone_root.addHandler(capture)
    ensure_logging_configured()  # filter ook op de nieuwe handler

    # PIIRedactingFilter muteert het record in-place, dus een eerdere handler
    # zou de redactie al gedaan kunnen hebben. Assert daarom expliciet dat de
    # capture-handler zélf de filter kreeg — anders bewijst deze test niets.
    assert any(isinstance(f, PIIRedactingFilter) for f in capture.filters)

    child = logging.getLogger("test.bootstrap.child")
    child.warning("AI-call mislukt voor '%s'", "user@example.com")

    assert stream, "er is niets gelogd"
    assert "user@example.com" not in stream[-1]
    assert "[REDACTED]" in stream[-1]


def test_bootstrap_is_fail_safe_bij_kapotte_filter(schone_root, monkeypatch):
    """Logging mag de applicatie nooit breken (gedrag verhuisd uit main.py).

    Zonder deze test wordt het verwijderen van de try/except niet betrapt.
    """
    from utils import logging_bootstrap

    def _boom(*_args, **_kwargs):
        raise RuntimeError("filter kapot")

    monkeypatch.setattr(logging_bootstrap, "install_pii_redaction_filter", _boom)
    ensure_logging_configured()  # mag niet raisen


def test_bootstrap_logt_error_als_redactie_faalt(schone_root, monkeypatch, caplog):
    from utils import logging_bootstrap

    def _boom(*_args, **_kwargs):
        raise RuntimeError("filter kapot")

    monkeypatch.setattr(logging_bootstrap, "install_pii_redaction_filter", _boom)
    with caplog.at_level(logging.ERROR):
        ensure_logging_configured()
    assert "gevoelige data" in caplog.text.lower()


def test_bootstrap_configureert_structured_logging_als_env_aan_staat(
    schone_root, monkeypatch
):
    """STRUCTURED_LOGGING stond alleen in main.py — subpagina's kregen daardoor
    nooit de JSON-handler, precies dezelfde root-cause die deze module fixt."""
    from utils import logging_bootstrap

    aangeroepen: list[dict] = []
    monkeypatch.setenv("STRUCTURED_LOGGING", "true")
    monkeypatch.setattr(
        logging_bootstrap,
        "setup_structured_logging",
        lambda **kw: aangeroepen.append(kw),
    )
    ensure_logging_configured()
    assert aangeroepen, "structured logging niet geconfigureerd vanuit de bootstrap"
    assert aangeroepen[0]["enable_json"] is True


def test_bootstrap_slaat_structured_logging_over_als_env_uit_staat(
    schone_root, monkeypatch
):
    from utils import logging_bootstrap

    aangeroepen: list[dict] = []
    monkeypatch.setenv("STRUCTURED_LOGGING", "false")
    monkeypatch.setattr(
        logging_bootstrap,
        "setup_structured_logging",
        lambda **kw: aangeroepen.append(kw),
    )
    ensure_logging_configured()
    assert not aangeroepen


# --- Duurzaamheids-guard ----------------------------------------------------

_SRC = Path(__file__).resolve().parents[3] / "src"

# Wat telt als entrypoint: een map waarvan de modules zelfstandig draaien
# (Streamlit-pagina, FastAPI-app, CLI-tool), plus een paar losse scripts.
# Bewust NIET "elke module met een __main__-blok": veel library-modules
# (utils/resilience.py, validation/*) hebben een demo-blok en horen geen
# import-side-effect te krijgen.
_ENTRYPOINT_DIRS = ("pages", "api", "tools", "cli")
_LOSSE_ENTRYPOINTS = ("main.py", "database/migrate_database.py")

# Migraties draaien via migrate_database.py (dat wél bootstrapt) en loggen
# geen user-input. Expliciete waiver zodat de guard niet stil verwatert.
_BEWUST_ZONDER_BOOTSTRAP = {
    "v5_migration.py",
    "v6_migration.py",
    "v7_migration.py",
}


def _roept_bootstrap_aan(bron: str) -> bool:
    """True als de module `ensure_logging_configured()` op module-niveau aanroept.

    Bewust een AST-parse en geen substring-scan: `"ensure_logging_configured()"
    in bron` matcht ook een voorkomen in een comment, een docstring of een
    nooit-aangeroepen functie-body — dan zou de guard vacuüm slagen terwijl de
    PII-redactie ontbreekt.
    """
    boom = ast.parse(bron)
    for node in boom.body:  # alleen top-level: draait bij import/scriptstart
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "ensure_logging_configured"
        ):
            return True
    return False


def _entrypoint_bestanden() -> list[Path]:
    """Alle bestanden die als zelfstandig entrypoint draaien."""
    entrypoints: list[Path] = []
    for map_naam in _ENTRYPOINT_DIRS:
        entrypoints.extend(
            p
            for p in (_SRC / map_naam).glob("*.py")
            if p.name != "__init__.py" and p.name not in _BEWUST_ZONDER_BOOTSTRAP
        )
    entrypoints.extend(_SRC / naam for naam in _LOSSE_ENTRYPOINTS)
    return sorted(set(entrypoints))


def test_er_zijn_entrypoints_gevonden():
    # Vangnet tegen een vacuüm-slagende guard. De drempel ligt bewust bóven
    # pages(3) + main(1), zodat het wegvallen van een hele map opvalt.
    gevonden = {p.name for p in _entrypoint_bestanden()}
    assert len(gevonden) >= 6, f"te weinig entrypoints ({sorted(gevonden)})"
    assert "feature_status_api.py" in gevonden, "API-entrypoint valt uit de guard"
    assert "synonym_admin.py" in gevonden
    assert "definitie_manager.py" in gevonden, "CLI-tools vallen uit de guard"


def test_alle_entrypoint_paden_bestaan():
    # Een verschoven pad mag niet stil tot een lege lijst leiden.
    for pad in _entrypoint_bestanden():
        assert pad.is_file(), f"entrypoint-pad bestaat niet: {pad}"


@pytest.mark.parametrize("entrypoint", _entrypoint_bestanden(), ids=lambda p: p.name)
def test_elk_entrypoint_roept_logging_bootstrap_aan(entrypoint):
    """Elk entrypoint moet zijn eigen logging configureren.

    Streamlit draait main.py niet bij directe navigatie naar een subpagina, de
    FastAPI-app en de CLI-tools draaien in een eigen proces. Zonder deze
    aanroep ontbreekt de PII-redactie daar. Deze guard faalt zodra iemand een
    nieuw entrypoint toevoegt zonder bootstrap.
    """
    bron = entrypoint.read_text(encoding="utf-8")
    assert _roept_bootstrap_aan(bron), (
        f"{entrypoint.relative_to(_SRC)} roept ensure_logging_configured() niet "
        "op module-niveau aan — PII-redactie ontbreekt in dit entrypoint (DEF-571)"
    )


def test_guard_accepteert_geen_aanroep_in_comment_of_dode_code():
    """Mutatietest op de guard zelf: een substring-scan zou hier slagen."""
    assert not _roept_bootstrap_aan("# ensure_logging_configured()  # uitgezet")
    assert not _roept_bootstrap_aan(
        "def main():\n    ensure_logging_configured()\n"  # nooit aangeroepen
    )
    assert not _roept_bootstrap_aan('"""docstring ensure_logging_configured()"""')
    assert _roept_bootstrap_aan("ensure_logging_configured()")
