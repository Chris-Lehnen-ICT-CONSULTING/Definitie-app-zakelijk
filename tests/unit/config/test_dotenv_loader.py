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

import os
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


def test_opt_out_via_env_var(monkeypatch, tmp_path):
    """Tests kunnen het laden volledig uitzetten voor hermeticiteit."""
    env = tmp_path / ".env"
    env.write_text("DEF573_UIT=uit_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("DEF573_UIT", raising=False)
    monkeypatch.setenv("DEFINITIE_DISABLE_DOTENV", "1")
    assert load_project_dotenv(pad=env) is False
    assert "DEF573_UIT" not in os.environ


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


# --- Consistentie-guard over de entry-points --------------------------------


def _bron(relatief: str) -> str:
    wortel = Path(__file__).resolve().parents[3]
    return (wortel / relatief).read_text(encoding="utf-8")


def test_geen_losse_load_dotenv_aanroepen_meer():
    """Eén plek bepaalt de override-keuze.

    Een losse `load_dotenv(override=True)` ergens anders zou de divergentie uit
    DEF-573 opnieuw introduceren, zonder dat een test faalt.
    """
    for pad in ("src/main.py", "src/config/config_manager.py"):
        bron = _bron(pad)
        assert "load_dotenv(" not in bron, (
            f"{pad} roept load_dotenv() direct aan — gebruik load_project_dotenv() "
            "zodat de override-keuze op één plek staat (DEF-573)"
        )
        assert "load_project_dotenv" in bron
