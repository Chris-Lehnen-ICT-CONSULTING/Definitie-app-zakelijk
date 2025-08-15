"""
JSON Validator Loader - Laadt individuele validators uit JSON/Python paren.

Deze module laadt validators dynamisch uit de config/toetsregels/regels directory
waar elke toetsregel bestaat uit een JSON configuratie en bijbehorende Python implementatie.
"""

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JSONValidatorLoader:
    """
    Loader voor individuele JSON/Python validator paren.

    Deze loader ondersteunt de flexibele architectuur waar elke
    toetsregel zijn eigen JSON en Python bestand heeft.
    """

    def __init__(self, regels_dir: Optional[str] = None):
        """
        Initialiseer de validator loader.

        Args:
            regels_dir: Directory met JSON/Python validator paren
        """
        if regels_dir is None:
            # Default naar de standaard locatie
            src_dir = Path(__file__).parent.parent
            self.regels_dir = src_dir / "toetsregels" / "regels"
        else:
            self.regels_dir = Path(regels_dir)

        self._validators_cache = {}
        self._json_cache = {}

        logger.info(
            f"JSONValidatorLoader geïnitialiseerd met directory: {self.regels_dir}"
        )

    def load_validator(self, regel_id: str) -> Optional[Any]:
        """
        Laad een specifieke validator.

        Args:
            regel_id: ID van de regel (bijv. 'CON-01')

        Returns:
            Validator instantie of None
        """
        # Check cache
        if regel_id in self._validators_cache:
            return self._validators_cache[regel_id]

        # Laad JSON config
        json_config = self.load_json_config(regel_id)
        if not json_config:
            logger.warning(f"Geen JSON configuratie gevonden voor {regel_id}")
            return None

        # Bepaal Python bestandsnaam (CON-01 -> CON_01.py)
        py_filename = regel_id.replace("-", "_") + ".py"
        # Python files zijn nu in validators directory
        validators_dir = self.regels_dir.parent / "validators"
        py_path = validators_dir / py_filename

        if not py_path.exists():
            logger.warning(f"Geen Python implementatie gevonden: {py_path}")
            return None

        try:
            # Dynamisch laden van Python module
            spec = importlib.util.spec_from_file_location(
                f"toetsregel_{regel_id}", py_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"toetsregel_{regel_id}"] = module
            spec.loader.exec_module(module)

            # Zoek validator class (conventie: {ID}Validator)
            class_name = f"{regel_id.replace('-', '')}Validator"
            validator_class = getattr(module, class_name, None)

            if validator_class is None:
                logger.error(f"Geen {class_name} gevonden in {py_path}")
                return None

            # Instantieer validator met JSON config
            validator = validator_class(json_config)

            # Cache voor hergebruik
            self._validators_cache[regel_id] = validator

            logger.debug(f"Validator {regel_id} succesvol geladen")
            return validator

        except Exception as e:
            logger.error(f"Fout bij laden validator {regel_id}: {e}")
            return None

    def load_json_config(self, regel_id: str) -> Optional[Dict[str, Any]]:
        """
        Laad JSON configuratie voor een regel.

        Args:
            regel_id: ID van de regel

        Returns:
            JSON configuratie als dict of None
        """
        if regel_id in self._json_cache:
            return self._json_cache[regel_id]

        json_path = self.regels_dir / f"{regel_id}.json"

        if not json_path.exists():
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Voeg ID toe aan config voor consistentie
            config["id"] = regel_id

            # Cache config
            self._json_cache[regel_id] = config

            return config

        except Exception as e:
            logger.error(f"Fout bij laden JSON voor {regel_id}: {e}")
            return None

    def get_all_regel_ids(self) -> List[str]:
        """
        Haal alle beschikbare regel IDs op.

        Returns:
            Lijst met regel IDs
        """
        regel_ids = []

        # Zoek alle JSON bestanden
        for json_file in self.regels_dir.glob("*.json"):
            if json_file.stem != "__init__":
                regel_ids.append(json_file.stem)

        return sorted(regel_ids)

    def validate_definitie(
        self,
        definitie: str,
        begrip: str,
        regel_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Valideer een definitie met de opgegeven regels.

        Args:
            definitie: Te valideren definitie
            begrip: Term die gedefinieerd wordt
            regel_ids: Lijst met regel IDs om te gebruiken (None = alle)
            context: Extra context informatie

        Returns:
            Lijst met validatie resultaten als strings
        """
        if regel_ids is None:
            regel_ids = self.get_all_regel_ids()

        results = []
        passed = 0
        failed = 0

        for regel_id in regel_ids:
            validator = self.load_validator(regel_id)

            if validator is None:
                results.append(f"⏭️ {regel_id}: Validator niet gevonden")
                continue

            try:
                # Roep validate aan (oude interface)
                success, message, score = validator.validate(definitie, begrip, context)

                # Format resultaat
                if success:
                    results.append(f"✅ {regel_id}: {message}")
                    passed += 1
                else:
                    results.append(f"❌ {regel_id}: {message}")
                    failed += 1

            except Exception as e:
                results.append(f"⚠️ {regel_id}: Fout tijdens validatie - {str(e)}")
                logger.error(f"Validatie fout voor {regel_id}: {e}")

        # Voeg samenvatting toe aan begin
        total = len(regel_ids)
        if total > 0:
            score_percentage = (passed / total) * 100
            summary = f"📊 **Toetsing Samenvatting**: {passed}/{total} regels geslaagd ({score_percentage:.1f}%)"
            if failed > 0:
                summary += f" | ❌ {failed} gefaald"
            results.insert(0, summary)

        return results


# Globale loader instantie
json_validator_loader = JSONValidatorLoader()
