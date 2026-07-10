"""Gedeelde, idempotente .env-loader (DEF-573).

Twee problemen die deze module oplost:

1. **Override-divergentie.** `main.py` deed `load_dotenv(override=True)` (.env wint
   van de shell), `ConfigManager` deed `load_dotenv(..., override=False)` (shell
   wint). Dezelfde app gedroeg zich dus anders afhankelijk van het entry-point:
   via home vs. directe navigatie naar een subpagina.

2. **Test-hermeticiteit.** `load_dotenv` muteert `os.environ` bij elke
   `ConfigManager()`-constructie. Een test die juist wil toetsen dat een key
   ontbreekt, vindt hem alsnog — uit `.env` van de ontwikkelaar. Lokaal groen,
   in CI rood (of andersom).
"""

import ast
import logging
import os
import threading
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from config import dotenv_loader
from config.dotenv_loader import load_project_dotenv, project_dotenv_path


@pytest.fixture(autouse=True)
def _reset_guard(monkeypatch):
    """Isoleer de loader-state rond elke test.

    De once-guard is module-state. Bovendien zet `tests/unit/conftest.py` de
    opt-out aan voor de hele unit-suite; deze tests toetsen juist het laadgedrag
    en heffen hem daarom lokaal op (de opt-out-test zet hem zelf weer).
    """
    monkeypatch.delenv(dotenv_loader.DISABLE_ENV_VAR, raising=False)
    dotenv_loader._geladen = False
    yield
    dotenv_loader._geladen = False


def test_pad_is_deterministisch_ongeacht_cwd(monkeypatch, tmp_path):
    """Geen find_dotenv()-stackwalk: het pad hangt niet van de CWD af."""
    verwacht = project_dotenv_path()
    monkeypatch.chdir(tmp_path)
    assert project_dotenv_path() == verwacht
    assert verwacht.name == ".env"


def test_laadt_niet_over_bestaande_env_vars_heen(monkeypatch, tmp_path):
    """override=False: expliciet gezette env-vars (CI, shell, tests) winnen."""
    env = tmp_path / ".env"
    env.write_text("DEF573_TESTVAR=uit_dotenv\n", encoding="utf-8")
    monkeypatch.setenv("DEF573_TESTVAR", "uit_shell")
    load_project_dotenv(pad=env)
    assert os.environ["DEF573_TESTVAR"] == "uit_shell"


def test_zet_ontbrekende_env_var_wel(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("DEF573_NIEUW=uit_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_NIEUW", raising=False)
    load_project_dotenv(pad=env)
    assert os.environ["DEF573_NIEUW"] == "uit_dotenv"


def test_is_idempotent_en_laadt_maar_een_keer(monkeypatch, tmp_path):
    """Once-guard: een tweede aanroep raakt os.environ niet meer aan.

    Zonder guard muteert elke `ConfigManager()`-constructie de omgeving.
    """
    env = tmp_path / ".env"
    env.write_text("DEF573_ONCE=eerste\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_ONCE", raising=False)
    assert load_project_dotenv(pad=env) is True
    os.environ["DEF573_ONCE"] = "handmatig_gewijzigd"
    assert load_project_dotenv(pad=env) is False
    assert os.environ["DEF573_ONCE"] == "handmatig_gewijzigd"


@pytest.mark.parametrize("waarde", ["1", "true", "TRUE", "yes", "on", " 1 "])
def test_opt_out_via_env_var(monkeypatch, tmp_path, waarde):
    """Tests kunnen het laden volledig uitzetten voor hermeticiteit.

    Meerdere waarheidswaarden: `DEFINITIE_DISABLE_DOTENV=true` deed voorheen
    stilzwijgend niets, wat een hermetische testrun ongemerkt onhermetisch maakt.
    """
    env = tmp_path / ".env"
    env.write_text("DEF573_UIT=uit_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_UIT", raising=False)
    monkeypatch.setenv(dotenv_loader.DISABLE_ENV_VAR, waarde)
    assert load_project_dotenv(pad=env) is False
    assert "DEF573_UIT" not in os.environ


@pytest.mark.parametrize("waarde", ["0", "false", "no", ""])
def test_opt_out_uit_laadt_wel(monkeypatch, tmp_path, waarde):
    env = tmp_path / ".env"
    env.write_text("DEF573_AAN=uit_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_AAN", raising=False)
    monkeypatch.setenv(dotenv_loader.DISABLE_ENV_VAR, waarde)
    assert load_project_dotenv(pad=env) is True


def test_meldt_welke_sleutels_zijn_overgeslagen(monkeypatch, tmp_path, caplog):
    """`override=False` is anders een stille verrassing: een stale shell-key wint
    van .env, zonder aanwijzing waar de sleutel vandaan kwam."""
    env = tmp_path / ".env"
    env.write_text(
        "DEF573_STALE=uit_dotenv\nDEF573_NIEUW=uit_dotenv\n", encoding="utf-8"
    )
    monkeypatch.setenv("DEF573_STALE", "uit_shell")
    monkeypatch.delenv("DEF573_NIEUW", raising=False)

    with caplog.at_level(logging.INFO, logger="config.dotenv_loader"):
        load_project_dotenv(pad=env)

    assert "DEF573_STALE" in caplog.text
    assert "DEF573_NIEUW" not in caplog.text, "alleen overgeslagen sleutels melden"
    # Nooit de waarden.
    assert "uit_shell" not in caplog.text
    assert "uit_dotenv" not in caplog.text


def test_gelijktijdig_laden_gebeurt_maar_een_keer(monkeypatch, tmp_path):
    """De once-guard was een check-then-set zonder lock; Streamlit is
    multi-threaded."""
    env = tmp_path / ".env"
    env.write_text("DEF573_RACE=waarde\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_RACE", raising=False)

    resultaten: list[bool] = []
    start = threading.Barrier(8)

    def _laad():
        start.wait()
        resultaten.append(load_project_dotenv(pad=env))

    threads = [threading.Thread(target=_laad) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(resultaten) == 1, f"meer dan één thread laadde: {resultaten}"
    assert os.environ["DEF573_RACE"] == "waarde"


def test_ontbrekend_bestand_is_geen_fout(tmp_path):
    """Een ontbrekende .env mag de app niet breken (CI heeft er geen)."""
    assert load_project_dotenv(pad=tmp_path / "bestaat-niet.env") is False


def test_force_negeert_de_guard(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("DEF573_FORCE=waarde\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_FORCE", raising=False)
    load_project_dotenv(pad=env)
    monkeypatch.delenv("DEF573_FORCE", raising=False)
    assert load_project_dotenv(pad=env, force=True) is True
    assert os.environ["DEF573_FORCE"] == "waarde"


# --- Consistentie-guard over heel src/ --------------------------------------

_SRC = Path(__file__).resolve().parents[3] / "src"

#: De enige module die `load_dotenv` mag aanroepen.
_TOEGESTAAN = {"dotenv_loader.py"}


def _roept_load_dotenv_aan(bron: str) -> bool:
    """True als de module `load_dotenv(...)` ergens aanroept.

    AST-parse en geen substring-scan: `"load_dotenv(" in bron` matcht ook een
    voorkomen in een comment of docstring (false positive), en zegt niets over
    andere bestanden (false negative). Precies die twee zwaktes hadden een
    eerdere guard in dit project.
    """
    for node in ast.walk(ast.parse(bron)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_dotenv"
        ):
            return True
    return False


def _src_modules() -> list[Path]:
    return sorted(p for p in _SRC.rglob("*.py") if p.name not in _TOEGESTAAN)


def test_er_zijn_src_modules_gevonden():
    # Vangnet: een verschoven pad mag de guard niet vacuüm laten slagen.
    assert len(_src_modules()) > 50


def test_geen_losse_load_dotenv_aanroepen_in_src():
    """Eén plek bepaalt de override-keuze.

    Een losse `load_dotenv(override=True)` ergens anders zou de divergentie uit
    DEF-573 opnieuw introduceren, zonder dat een test faalt. Dat gebeurde ook:
    `src/tools/rag_smoke_test.py` deed het nog, en de oude guard keek er niet naar.
    """
    overtreders = [
        p.relative_to(_SRC)
        for p in _src_modules()
        if _roept_load_dotenv_aan(p.read_text(encoding="utf-8"))
    ]
    assert not overtreders, (
        f"{overtreders} roept/roepen load_dotenv() direct aan — gebruik "
        "load_project_dotenv() zodat de override-keuze op één plek staat (DEF-573)"
    )


@pytest.mark.parametrize("pad", ["main.py", "config/config_manager.py"])
def test_entrypoints_gebruiken_de_gedeelde_loader(pad):
    bron = (_SRC / pad).read_text(encoding="utf-8")
    assert "load_project_dotenv" in bron


def test_guard_accepteert_geen_aanroep_in_comment_of_docstring():
    """Mutatietest op de guard zelf: een substring-scan zou hier slagen."""
    assert not _roept_load_dotenv_aan("# load_dotenv(override=True)")
    assert not _roept_load_dotenv_aan('"""docstring over load_dotenv(...)"""')
    assert _roept_load_dotenv_aan("load_dotenv(override=True)")
    assert _roept_load_dotenv_aan("def f():\n    load_dotenv()")
