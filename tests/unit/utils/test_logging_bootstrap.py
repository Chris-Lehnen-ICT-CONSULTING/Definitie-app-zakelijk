"""Tests voor de gedeelde logging-bootstrap (DEF-571).

Achtergrond: `install_pii_redaction_filter()` werd alleen vanuit `main.py`
aangeroepen. Streamlit draait `main.py` NIET bij directe navigatie naar een
subpagina (dezelfde root-cause als DEF-572), waardoor de PII-redactie op
`/synonym_admin` ontbrak — juist de pagina die de synoniem-term logt.
"""

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


def test_bootstrap_redigeert_pii_uit_child_logger(schone_root, caplog):
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

    child = logging.getLogger("test.bootstrap.child")
    child.warning("AI-call mislukt voor '%s'", "user@example.com")

    assert stream, "er is niets gelogd"
    assert "user@example.com" not in stream[-1]
    assert "[REDACTED]" in stream[-1]


# --- Duurzaamheids-guard ----------------------------------------------------

_SRC = Path(__file__).resolve().parents[3] / "src"


def _entrypoint_bestanden() -> list[Path]:
    """Alle bestanden die als zelfstandig entrypoint kunnen draaien.

    Streamlit-subpagina's (main.py draait daar niet) plus modules met een
    eigen `if __name__ == "__main__"`-runner, zoals de FastAPI-app. Elk
    daarvan configureert zijn eigen logging — of lekt PII.
    """
    entrypoints = [p for p in (_SRC / "pages").glob("*.py") if p.name != "__init__.py"]
    entrypoints.append(_SRC / "main.py")
    for module in (_SRC / "api").glob("*.py"):
        if 'if __name__ == "__main__"' in module.read_text(encoding="utf-8"):
            entrypoints.append(module)
    return sorted(entrypoints)


def test_er_zijn_entrypoints_gevonden():
    # Vangnet: als het pad verschuift, moet de guard hieronder niet stil slagen.
    gevonden = _entrypoint_bestanden()
    assert (
        len(gevonden) >= 4
    ), f"te weinig entrypoints ({gevonden}) — guard zou vacuüm slagen"


@pytest.mark.parametrize("entrypoint", _entrypoint_bestanden(), ids=lambda p: p.name)
def test_elk_entrypoint_roept_logging_bootstrap_aan(entrypoint):
    """Elk entrypoint moet zijn eigen logging configureren.

    Streamlit draait main.py niet bij directe navigatie naar een subpagina, en
    de FastAPI-app draait in een eigen proces. Zonder deze aanroep ontbreekt de
    PII-redactie daar. Deze guard faalt zodra iemand een nieuw entrypoint
    toevoegt zonder bootstrap.
    """
    bron = entrypoint.read_text(encoding="utf-8")
    assert "ensure_logging_configured()" in bron, (
        f"{entrypoint.name} roept ensure_logging_configured() niet aan — "
        "PII-redactie ontbreekt in dit entrypoint (DEF-571)"
    )
