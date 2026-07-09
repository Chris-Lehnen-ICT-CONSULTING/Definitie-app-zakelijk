"""Gedeelde, idempotente `.env`-loader voor alle entry-points (DEF-573).

Waarom één plek:

* **Override-keuze.** `main.py` laadde met ``override=True`` (.env wint van de
  shell), `ConfigManager` met ``override=False`` (shell wint). Dezelfde app
  gedroeg zich dus anders afhankelijk van het entry-point — via de homepagina
  of via directe navigatie naar een Streamlit-subpagina, die `main.py` niet
  draait (DEF-572). Nu geldt overal ``override=False``: expliciet gezette
  env-vars (CI, Docker, shell, tests) leiden, `.env` vult alleen aan. Dat is
  ook het standaardgedrag van python-dotenv.

* **Test-hermeticiteit.** ``load_dotenv`` muteert ``os.environ``. Zonder guard
  deed elke ``ConfigManager()``-constructie dat opnieuw, waardoor een test die
  juist wil toetsen dát een key ontbreekt hem alsnog uit de `.env` van de
  ontwikkelaar vindt. De once-guard beperkt dit tot één keer per proces; met
  ``DEFINITIE_DISABLE_DOTENV=1`` kan een testrun het laden volledig uitzetten.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

#: Zet op "1" om het laden van .env volledig over te slaan (hermetische tests).
DISABLE_ENV_VAR = "DEFINITIE_DISABLE_DOTENV"

_geladen = False


def project_dotenv_path() -> Path:
    """Absoluut pad naar de `.env` in de project-root.

    Expliciet pad in plaats van ``find_dotenv()``: die loopt de directory-stack
    af vanaf de CWD en levert dus een ander bestand op naargelang waar het
    proces gestart is.
    """
    return Path(__file__).resolve().parents[2] / ".env"


def load_project_dotenv(pad: Path | None = None, force: bool = False) -> bool:
    """Laad de project-`.env` één keer per proces.

    Args:
        pad: Alternatief pad (voor tests). Default: de project-root-`.env`.
        force: Negeer de once-guard en laad opnieuw.

    Returns:
        True als er daadwerkelijk geladen is, anders False (guard actief,
        opt-out gezet, of bestand ontbreekt).
    """
    global _geladen

    if os.getenv(DISABLE_ENV_VAR) == "1":
        return False
    if _geladen and not force:
        return False

    env_path = pad if pad is not None else project_dotenv_path()
    if not env_path.is_file():
        logger.debug("Geen .env gevonden op %s", env_path)
        return False

    load_dotenv(env_path, override=False)
    _geladen = True
    return True


__all__ = ["DISABLE_ENV_VAR", "load_project_dotenv", "project_dotenv_path"]
