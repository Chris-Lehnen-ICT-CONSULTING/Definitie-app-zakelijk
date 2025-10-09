"""
YAML Config Updater voor automatische synonym updates.

Deze service biedt safe YAML updates met:
- Automatische backups
- Validation
- Rollback bij fouten
- Duplicate detection
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


class YAMLUpdateError(Exception):
    """Error bij YAML update operaties."""


class YAMLConfigUpdater:
    """
    Service voor het updaten van juridische_synoniemen.yaml.

    Biedt safe updates met backup, validation en rollback.
    """

    def __init__(
        self,
        yaml_path: str | Path = "config/juridische_synoniemen.yaml",
        backup_dir: str | Path = "config/backups",
    ):
        """
        Initialize YAML config updater.

        Args:
            yaml_path: Pad naar juridische_synoniemen.yaml
            backup_dir: Directory voor backups
        """
        if not YAML_AVAILABLE:
            msg = "PyYAML is not installed. Run: pip install pyyaml"
            raise ImportError(msg)

        self.yaml_path = Path(yaml_path)
        self.backup_dir = Path(backup_dir)

        # Ensure directories exist
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        if not self.yaml_path.exists():
            msg = f"YAML config niet gevonden: {self.yaml_path}"
            raise FileNotFoundError(msg)

    def _create_backup(self) -> Path:
        """
        Maak backup van huidige YAML config.

        Returns:
            Path naar backup bestand
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"juridische_synoniemen_{timestamp}.yaml"

        shutil.copy2(self.yaml_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        return backup_path

    def _load_yaml(self) -> dict[str, Any]:
        """
        Laad YAML config.

        Returns:
            Dictionary met YAML data

        Raises:
            YAMLUpdateError: Bij parsing fouten
        """
        try:
            with open(self.yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                msg = "YAML root moet een dictionary zijn"
                raise YAMLUpdateError(msg)

            return data

        except yaml.YAMLError as e:
            msg = f"YAML parsing error: {e}"
            raise YAMLUpdateError(msg) from e
        except Exception as e:
            msg = f"Error loading YAML: {e}"
            raise YAMLUpdateError(msg) from e

    def _write_yaml(self, data: dict[str, Any]):
        """
        Schrijf YAML config.

        Args:
            data: Dictionary om weg te schrijven

        Raises:
            YAMLUpdateError: Bij write fouten
        """
        try:
            with open(self.yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,  # Behoud volgorde
                    width=100,  # Line width voor leesbaarheid
                )

            logger.info(f"Successfully wrote YAML to {self.yaml_path}")

        except Exception as e:
            msg = f"Error writing YAML: {e}"
            raise YAMLUpdateError(msg) from e

    def _validate_yaml(self, data: dict[str, Any]):
        """
        Valideer YAML data structure.

        Args:
            data: Dictionary om te valideren

        Raises:
            YAMLUpdateError: Bij validation fouten
        """
        # Check dat het een dictionary is
        if not isinstance(data, dict):
            msg = "YAML data moet een dictionary zijn"
            raise YAMLUpdateError(msg)

        # Check voor reserved keys (clusters, metadata)
        reserved_keys = {"_clusters", "_metadata"}

        # Valideer hoofdtermen (non-reserved keys)
        for hoofdterm, synoniemen in data.items():
            # Skip reserved sections
            if hoofdterm in reserved_keys:
                continue

            # Synoniemen moet een list zijn
            if not isinstance(synoniemen, list):
                msg = (
                    f"Synoniemen voor '{hoofdterm}' moet een list zijn, "
                    f"niet {type(synoniemen).__name__}"
                )
                raise YAMLUpdateError(msg)

            # Elk synoniem moet string of dict zijn (weighted format)
            for idx, syn in enumerate(synoniemen):
                if not isinstance(syn, str | dict):
                    msg = (
                        f"Synoniem {idx} voor '{hoofdterm}' heeft invalide type: "
                        f"{type(syn).__name__}"
                    )
                    raise YAMLUpdateError(msg)

                # Als dict, check required keys
                if isinstance(syn, dict) and "synoniem" not in syn:
                    msg = (
                        f"Weighted synoniem {idx} voor '{hoofdterm}' "
                        f"mist 'synoniem' key"
                    )
                    raise YAMLUpdateError(msg)

        logger.debug("YAML validation passed")

    def _normalize_hoofdterm(self, hoofdterm: str) -> str:
        """
        Normaliseer hoofdterm voor YAML key.

        Spaces worden underscores voor consistency met bestaande data.

        Args:
            hoofdterm: De hoofdterm

        Returns:
            Genormaliseerde hoofdterm
        """
        # Strip first, then replace spaces with underscores
        return hoofdterm.strip().replace(" ", "_")

    def add_synonym(
        self,
        hoofdterm: str,
        synoniem: str,
        weight: float | None = None,
        skip_if_exists: bool = True,
    ) -> bool:
        """
        Voeg synoniem toe aan YAML config.

        Args:
            hoofdterm: De hoofdterm (spaces worden underscores)
            synoniem: Het synoniem om toe te voegen
            weight: Optional weight voor weighted format (0.0-1.0)
            skip_if_exists: Skip als synoniem al bestaat (default: True)

        Returns:
            True als synoniem toegevoegd, False als al bestond

        Raises:
            YAMLUpdateError: Bij update fouten
        """
        # Normalize hoofdterm
        normalized_hoofdterm = self._normalize_hoofdterm(hoofdterm)

        # Create backup
        backup_path = self._create_backup()

        try:
            # Load current data
            data = self._load_yaml()

            # Initialize hoofdterm list if not exists
            if normalized_hoofdterm not in data:
                data[normalized_hoofdterm] = []

            synoniemen_list = data[normalized_hoofdterm]

            # Check for duplicates
            existing_synoniemen = set()
            for item in synoniemen_list:
                if isinstance(item, str):
                    existing_synoniemen.add(item.lower())
                elif isinstance(item, dict):
                    existing_synoniemen.add(item["synoniem"].lower())

            if synoniem.lower() in existing_synoniemen:
                if skip_if_exists:
                    logger.info(
                        f"Synoniem '{synoniem}' already exists for '{hoofdterm}', skipping"
                    )
                    return False
                msg = f"Synoniem '{synoniem}' already exists for '{hoofdterm}'"
                raise YAMLUpdateError(msg)

            # Add synoniem
            if weight is not None:
                # Weighted format
                if not (0.0 <= weight <= 1.0):
                    msg = f"Weight moet tussen 0.0 en 1.0 zijn: {weight}"
                    raise ValueError(msg)

                synoniemen_list.append({"synoniem": synoniem, "weight": weight})
                logger.info(
                    f"Added weighted synoniem '{synoniem}' (weight: {weight:.2f}) "
                    f"to '{hoofdterm}'"
                )
            else:
                # Plain string format
                synoniemen_list.append(synoniem)
                logger.info(f"Added synoniem '{synoniem}' to '{hoofdterm}'")

            # Validate before writing
            self._validate_yaml(data)

            # Write updated data
            self._write_yaml(data)

            return True

        except Exception as e:
            # Rollback on error
            logger.error(f"Error adding synonym, rolling back: {e}")
            self._restore_backup(backup_path)
            msg = f"Failed to add synonym: {e}"
            raise YAMLUpdateError(msg) from e

    def remove_synonym(self, hoofdterm: str, synoniem: str) -> bool:
        """
        Verwijder synoniem uit YAML config.

        Args:
            hoofdterm: De hoofdterm
            synoniem: Het synoniem om te verwijderen

        Returns:
            True als synoniem verwijderd, False als niet gevonden

        Raises:
            YAMLUpdateError: Bij update fouten
        """
        normalized_hoofdterm = self._normalize_hoofdterm(hoofdterm)

        # Create backup
        backup_path = self._create_backup()

        try:
            # Load current data
            data = self._load_yaml()

            # Check if hoofdterm exists
            if normalized_hoofdterm not in data:
                logger.warning(f"Hoofdterm '{hoofdterm}' not found in YAML")
                return False

            synoniemen_list = data[normalized_hoofdterm]

            # Find and remove synoniem
            found = False
            new_list = []

            for item in synoniemen_list:
                # Check both plain string and weighted format
                if isinstance(item, str):
                    if item.lower() != synoniem.lower():
                        new_list.append(item)
                    else:
                        found = True
                elif isinstance(item, dict):
                    if item["synoniem"].lower() != synoniem.lower():
                        new_list.append(item)
                    else:
                        found = True

            if not found:
                logger.warning(
                    f"Synoniem '{synoniem}' not found for '{hoofdterm}', skipping"
                )
                return False

            # Update data
            data[normalized_hoofdterm] = new_list

            # Validate before writing
            self._validate_yaml(data)

            # Write updated data
            self._write_yaml(data)

            logger.info(f"Removed synoniem '{synoniem}' from '{hoofdterm}'")
            return True

        except Exception as e:
            # Rollback on error
            logger.error(f"Error removing synonym, rolling back: {e}")
            self._restore_backup(backup_path)
            msg = f"Failed to remove synonym: {e}"
            raise YAMLUpdateError(msg) from e

    def get_synonyms(self, hoofdterm: str) -> list[str]:
        """
        Haal synoniemen op voor een hoofdterm.

        Args:
            hoofdterm: De hoofdterm

        Returns:
            List van synoniemen (plain strings)
        """
        normalized_hoofdterm = self._normalize_hoofdterm(hoofdterm)

        data = self._load_yaml()

        if normalized_hoofdterm not in data:
            return []

        synoniemen_list = data[normalized_hoofdterm]
        result = []

        for item in synoniemen_list:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(item["synoniem"])

        return result

    def _restore_backup(self, backup_path: Path):
        """
        Restore from backup.

        Args:
            backup_path: Pad naar backup bestand
        """
        try:
            shutil.copy2(backup_path, self.yaml_path)
            logger.info(f"Restored from backup: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            msg = f"Rollback failed: {e}"
            raise YAMLUpdateError(msg) from e

    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Cleanup oude backups (behoud alleen laatste N).

        Args:
            keep_count: Aantal backups om te behouden
        """
        # Get all backup files
        backups = sorted(
            self.backup_dir.glob("juridische_synoniemen_*.yaml"), reverse=True
        )

        # Remove old backups
        for backup in backups[keep_count:]:
            try:
                backup.unlink()
                logger.debug(f"Deleted old backup: {backup}")
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup}: {e}")

        logger.info(
            f"Cleanup complete: kept {min(len(backups), keep_count)} backups, "
            f"deleted {max(0, len(backups) - keep_count)}"
        )
