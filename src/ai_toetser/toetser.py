"""Dunne OO-wrapper zodat legacy-tests `from ai_toetser import Toetser`
kunnen blijven gebruiken.

Deze module biedt een eenvoudige wrapper klasse voor het controleren
van verboden woorden in definities voor backwards compatibility.
"""

import json  # JSON bestand verwerking
from pathlib import Path  # Pad manipulatie voor bestand toegang

# Standaardpad naar verboden_woorden.json - relatief ten opzichte van dit bestand
_DEFAULT_JSON = Path(__file__).parents[1] / "config" / "verboden_woorden.json"


class Toetser:
    """Controleert of woorden op de verboden-lijst staan.

    Legacy wrapper klasse voor het controleren van verboden woorden
    in gegenereerde definities. Laadt verboden woorden uit JSON bestand.
    """

    def __init__(self, json_path: str | Path = _DEFAULT_JSON) -> None:
        """Initialiseer toetser met verboden woorden lijst.

        Args:
            json_path: Pad naar JSON bestand met verboden woorden

        Raises:
            FileNotFoundError: Als het verboden woorden bestand niet gevonden wordt
        """
        # Converteer naar Path object voor gemakkelijke manipulatie
        path = Path(json_path)

        # Zoeklogica voor relatieve paden uit tests - probeer verschillende locaties
        if not path.is_absolute():
            candidates = [
                Path.cwd() / path,  # Huidige directory + pad
                Path(__file__).parents[1] / path,  # src directory + pad
            ]
            # Gebruik eerste bestaande pad uit candidates
            path = next((p for p in candidates if p.exists()), path)

        # Controleer of bestand bestaat
        if not path.exists():
            msg = f"Verboden-woordenlijst niet gevonden: {json_path}"
            raise FileNotFoundError(msg)

        # Laad JSON data uit bestand met UTF-8 encoding
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        # Haal woorden lijst uit data (ondersteunt zowel dict als lijst formaat)
        woorden = data["verboden_woorden"] if isinstance(data, dict) else data
        # Converteer alle woorden naar lowercase voor case-insensitive vergelijking
        self._set: set[str] = {w.lower() for w in woorden}

    def is_verboden(self, woord: str) -> bool:
        """Controleer of een woord op de verboden lijst staat.

        Args:
            woord: Het woord om te controleren

        Returns:
            True als het woord verboden is, False anders
        """
        # Converteer naar lowercase en controleer of het in de set staat
        return woord.lower() in self._set

    run = is_verboden  # Alias voor oude tests - voor backwards compatibility
