"""Dunne OO-wrapper zodat legacy-tests `from ai_toetser import Toetser`
   kunnen blijven gebruiken.
"""
from pathlib import Path
import json
from typing import Set

# standaard­pad naar verboden_woorden.json
_DEFAULT_JSON = Path(__file__).parents[1] / "config" / "verboden_woorden.json"

class Toetser:
    """Controleert of woorden op de verboden-lijst staan."""

    def __init__(self, json_path: str | Path = _DEFAULT_JSON) -> None:
        path = Path(json_path)

        # ↪︎ Zoeklogica voor relatieve paden uit tests
        if not path.is_absolute():
            candidates = [
                Path.cwd() / path,                       # ./config/…
                Path(__file__).parents[1] / path,        # src/config/…
            ]
            path = next((p for p in candidates if p.exists()), path)

        if not path.exists():
            raise FileNotFoundError(
                f"Verboden-woordenlijst niet gevonden: {json_path}"
            )

        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        woorden = data["verboden_woorden"] if isinstance(data, dict) else data
        self._set: Set[str] = {w.lower() for w in woorden}

    def is_verboden(self, woord: str) -> bool:
        return woord.lower() in self._set

    run = is_verboden  # alias voor oude tests