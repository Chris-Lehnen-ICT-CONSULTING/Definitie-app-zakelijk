"""
Modulaire Toetsregel Loader

Laadt toetsregels uit zowel JSON configuratie als Python validatie modules.
Elke toetsregel kan zijn eigen Python module hebben voor complexe validatie logica.
"""

import importlib.util
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ModularToetsregelLoader:
    """Loader voor modulaire toetsregels met JSON + Python combinatie."""

    def __init__(self, regels_dir: str | None = None):
        """
        Initialiseer de modulaire loader.

        Args:
            regels_dir: Directory met toetsregel bestanden
        """
        if regels_dir is None:
            # Default naar config/toetsregels/regels
            current_dir = Path(__file__).parent
            self.regels_dir = current_dir / "regels"
        else:
            self.regels_dir = Path(regels_dir)

        self.loaded_modules = {}
        self.loaded_configs = {}

    def load_regel(self, regel_id: str) -> dict[str, Any]:
        """
        Laad een toetsregel met zowel JSON config als Python module.

        Args:
            regel_id: ID van de regel (bijv. 'ESS-03')

        Returns:
            Dictionary met regel configuratie en validator
        """
        # Normaliseer regel ID (ESS-03 -> ESS_03 voor Python module)
        module_name = regel_id.replace("-", "_")

        # Laad JSON configuratie
        json_path = self.regels_dir / f"{regel_id}.json"
        if not json_path.exists():
            logger.warning(
                f"JSON configuratie niet gevonden voor {regel_id}: {json_path}"
            )
            return None

        with open(json_path, encoding="utf-8") as f:
            config = json.load(f)

        # Basis regel data
        regel_data = {
            "id": regel_id,
            "config": config,
            "validator": None,
            "validate_func": None,
        }

        # Probeer Python module te laden
        py_path = self.regels_dir / f"{module_name}.py"
        if py_path.exists():
            try:
                # Dynamisch laden van Python module
                spec = importlib.util.spec_from_file_location(module_name, py_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Zoek validator class of functie
                if hasattr(module, "create_validator"):
                    # Module heeft factory functie
                    validator = module.create_validator()
                    regel_data["validator"] = validator
                    regel_data["validate_func"] = validator.validate
                    logger.info(f"Geladen validator class voor {regel_id}")

                elif hasattr(module, f"validate_{module_name.lower()}"):
                    # Module heeft directe validatie functie
                    validate_func = getattr(module, f"validate_{module_name.lower()}")
                    regel_data["validate_func"] = validate_func
                    logger.info(f"Geladen validatie functie voor {regel_id}")

                elif hasattr(module, f"{module_name}Validator"):
                    # Module heeft validator class
                    validator_class = getattr(module, f"{module_name}Validator")
                    validator = validator_class(config)
                    regel_data["validator"] = validator
                    regel_data["validate_func"] = validator.validate
                    logger.info(f"Geladen {module_name}Validator voor {regel_id}")

                # Cache de module
                self.loaded_modules[regel_id] = module

            except Exception as e:
                logger.warning(f"Kon Python module niet laden voor {regel_id}: {e}")

        # Als geen Python module, gebruik fallback validator
        if not regel_data["validate_func"]:
            regel_data["validate_func"] = self._create_fallback_validator(config)

        # Cache configuratie
        self.loaded_configs[regel_id] = regel_data

        return regel_data

    def _create_fallback_validator(self, config: dict[str, Any]) -> Callable:
        """
        Maak een basis validator functie voor regels zonder Python module.

        Args:
            config: Regel configuratie uit JSON

        Returns:
            Validator functie
        """
        import re

        def fallback_validate(
            definitie: str, begrip: str, context: dict | None = None
        ) -> tuple[bool, str, float]:
            """Basis pattern matching validator."""
            regel_id = config.get("id", "UNKNOWN")
            patterns = config.get("herkenbaar_patronen", [])

            # Simpele pattern matching
            gevonden = False
            for pattern in patterns:
                try:
                    if re.search(pattern, definitie, re.IGNORECASE):
                        gevonden = True
                        break
                except re.error:
                    logger.warning(f"Ongeldig regex patroon in {regel_id}: {pattern}")

            if gevonden:
                return True, f"✔️ {regel_id}: Patroon gevonden", 1.0
            uitleg = config.get("uitleg", "Regel niet voldaan")
            return False, f"❌ {regel_id}: {uitleg}", 0.0

        return fallback_validate

    def get_available_regels(self) -> list[str]:
        """
        Haal lijst van beschikbare regel IDs op.

        Returns:
            Lijst met regel IDs (bijv. ['ESS-03', 'CON-01', ...])
        """
        available = []

        # Scan regels directory voor JSON bestanden
        if self.regels_dir.exists():
            for json_file in self.regels_dir.glob("*.json"):
                regel_id = json_file.stem
                # Filter systeem bestanden
                if not regel_id.startswith("_"):
                    available.append(regel_id)

        return sorted(available)

    def load_all_regels(self) -> dict[str, dict[str, Any]]:
        """
        Laad alle beschikbare toetsregels.

        Returns:
            Dictionary met alle geladen regels
        """
        alle_regels = {}

        # Vind alle JSON bestanden
        for json_file in self.regels_dir.glob("*.json"):
            regel_id = json_file.stem

            # Skip __init__ of andere systeem bestanden
            if regel_id.startswith("_"):
                continue

            regel_data = self.load_regel(regel_id)
            if regel_data:
                alle_regels[regel_id] = regel_data

        logger.info(f"Totaal {len(alle_regels)} toetsregels geladen")
        return alle_regels

    def validate_with_regel(
        self, regel_id: str, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer een definitie met een specifieke regel.

        Args:
            regel_id: ID van de toetsregel
            definitie: Te valideren definitie
            begrip: Het begrip
            context: Optionele context

        Returns:
            Tuple van (succes, melding, score)
        """
        # Laad regel als nog niet geladen
        if regel_id not in self.loaded_configs:
            regel_data = self.load_regel(regel_id)
            if not regel_data:
                return False, f"❌ Regel {regel_id} niet gevonden", 0.0
        else:
            regel_data = self.loaded_configs[regel_id]

        # Gebruik de validate functie
        validate_func = regel_data.get("validate_func")
        if validate_func:
            return validate_func(definitie, begrip, context)
        return False, f"❌ Geen validator voor {regel_id}", 0.0

    def get_generation_hints(self, regel_id: str) -> list[str]:
        """
        Haal generatie hints op voor een regel.

        Args:
            regel_id: ID van de toetsregel

        Returns:
            Lijst met generatie hints
        """
        if regel_id not in self.loaded_configs:
            self.load_regel(regel_id)

        regel_data = self.loaded_configs.get(regel_id, {})
        validator = regel_data.get("validator")

        if validator and hasattr(validator, "get_generation_hints"):
            return validator.get_generation_hints()

        # Fallback: gebruik goede voorbeelden uit config
        config = regel_data.get("config", {})
        voorbeelden = config.get("goede_voorbeelden", [])
        if voorbeelden:
            return [f"Volg dit voorbeeld: {voorbeeld}" for voorbeeld in voorbeelden[:2]]

        return []


# Singleton instance
_loader_instance = None


def get_modular_loader() -> ModularToetsregelLoader:
    """Haal de globale modulaire loader op."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ModularToetsregelLoader()
    return _loader_instance


# Convenience functies
def load_all_toetsregels() -> dict[str, dict[str, Any]]:
    """Laad alle toetsregels met hun validators."""
    return get_modular_loader().load_all_regels()


def validate_met_regel(
    regel_id: str, definitie: str, begrip: str, context: dict | None = None
) -> tuple[bool, str, float]:
    """Valideer met een specifieke regel."""
    return get_modular_loader().validate_with_regel(
        regel_id, definitie, begrip, context
    )
