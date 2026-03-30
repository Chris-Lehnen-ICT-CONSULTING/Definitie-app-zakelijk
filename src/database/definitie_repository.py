"""
DefinitieRepository - Facade voor de database laag (DEF-389).

Delegeert naar gefocuste sub-modules. Alle publieke symbolen worden
ge-re-exporteerd voor backward compatibility.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_crud import DefinitieCrudRepository
from database.definitie_duplicates import DefinitieDuplicateRepository
from database.definitie_import_export import DefinitieImportExportRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import (
    DefinitieRecord,
    DefinitieStatus,
    DuplicateMatch,
    SourceType,
    VoorbeeldenRecord,
)
from database.synonym_sync import SynonymSyncService
from database.voorbeelden_repository import VoorbeeldenRepository
from domain.ontological_categories import OntologischeCategorie

__all__ = [
    "DefinitieRecord",
    "DefinitieRepository",
    "DefinitieStatus",
    "DuplicateMatch",
    "SourceType",
    "VoorbeeldenRecord",
    "clear_repository_singleton",
    "get_definitie_repository",
    "validate_and_get_repository",
]

logger = logging.getLogger(__name__)


class DefinitieRepository:
    """Facade — delegeert naar gefocuste sub-repositories."""

    def __init__(self, db_path: str = "data/definities.db"):
        self.db_path = db_path
        self._db = DatabaseConnection(db_path)
        self._db.init_database()
        self._audit = AuditHelpers(self._db)
        self._duplicates = DefinitieDuplicateRepository(self._db, self._audit)
        self._search = DefinitieSearchRepository(self._db, self._audit)
        self._crud = DefinitieCrudRepository(
            self._db, self._audit, self._duplicates, self._search
        )
        self._import_export = DefinitieImportExportRepository(self._db, self._audit)
        self._synonym_sync = SynonymSyncService(
            self._db, get_registry_fn=self._get_synonym_registry
        )
        self._voorbeelden = VoorbeeldenRepository(self._db, self._synonym_sync)

    @staticmethod
    def _get_synonym_registry():
        """Lazy registry lookup — houdt database laag vrij van service imports."""
        from src.services.container import get_container

        return get_container().synonym_registry()

    # === Backward-compat: connection access ===
    def _get_connection(self, timeout: float = 30.0) -> sqlite3.Connection:
        return self._db.get_connection(timeout)

    def _has_legacy_columns(self) -> bool:
        return self._db.has_legacy_columns()

    @staticmethod
    def _has_legacy_columns_in_conn(conn: sqlite3.Connection) -> bool:
        return AuditHelpers.has_legacy_columns_in_conn(conn)

    @staticmethod
    def _build_insert_columns(
        record: DefinitieRecord, wb_value: str, include_legacy: bool
    ) -> tuple[list[str], list[Any]]:
        return AuditHelpers.build_insert_columns(record, wb_value, include_legacy)

    def _init_database(self):
        self._db.init_database()

    def _split_sql_statements(self, sql: str) -> list[str]:
        return self._db.split_sql_statements(sql)

    # === CRUD ===
    def create_definitie(
        self, record: DefinitieRecord, allow_duplicate: bool = False
    ) -> int:
        return self._crud.create_definitie(record, allow_duplicate)

    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        return self._crud.get_definitie(definitie_id)

    def find_definitie(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        status: DefinitieStatus | None = None,
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> DefinitieRecord | None:
        return self._crud.find_definitie(
            begrip,
            organisatorische_context,
            juridische_context,
            status,
            categorie,
            wettelijke_basis,
        )

    def update_definitie(
        self, definitie_id: int, updates: dict[str, Any], updated_by: str | None = None
    ) -> bool:
        return self._crud.update_definitie(definitie_id, updates, updated_by)

    def change_status(
        self,
        definitie_id: int,
        new_status: DefinitieStatus,
        changed_by: str | None = None,
        notes: str | None = None,
    ) -> bool:
        return self._crud.change_status(definitie_id, new_status, changed_by, notes)

    def get_all(self) -> list[DefinitieRecord]:
        return self._crud.get_all()

    def get_by_status(self, status: str) -> list[DefinitieRecord]:
        return self._crud.get_by_status(status)

    # === Search ===
    def search_definities(
        self,
        query: str | None = None,
        categorie: OntologischeCategorie | None = None,
        organisatorische_context: str | None = None,
        status: DefinitieStatus | None = None,
        limit: int | None = 100,
    ) -> list[DefinitieRecord]:
        return self._search.search_definities(
            query,
            categorie,
            organisatorische_context,
            status,
            limit,
        )

    # === Duplicates ===
    def find_duplicates(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: str | None = None,
        wettelijke_basis: list[str] | None = None,
    ) -> list[DuplicateMatch]:
        return self._duplicates.find_duplicates(
            begrip,
            organisatorische_context,
            juridische_context,
            categorie,
            wettelijke_basis,
        )

    def count_exact_by_context(
        self,
        *,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        wettelijke_basis: list[str] | None = None,
    ) -> int:
        return self._duplicates.count_exact_by_context(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            wettelijke_basis=wettelijke_basis,
        )

    # === Import/Export ===
    def get_statistics(self) -> dict[str, Any]:
        return self._import_export.get_statistics()

    def export_to_json(
        self, file_path: str, filters: dict[str, Any] | None = None
    ) -> int:
        return self._import_export.export_to_json(
            file_path,
            filters,
            search_fn=self.search_definities,
        )

    def import_from_json(
        self, file_path: str, import_by: str | None = None
    ) -> tuple[int, int, list[str]]:
        return self._import_export.import_from_json(
            file_path,
            import_by,
            create_fn=self.create_definitie,
        )

    # === Audit helpers (backward compat) ===
    def _row_to_record(self, row: sqlite3.Row) -> DefinitieRecord:
        return self._audit.row_to_record(row)

    def _log_geschiedenis(
        self,
        definitie_id: int,
        wijziging_type: str,
        gewijzigd_door: str | None = None,
        reden: str | None = None,
    ):
        self._audit.log_geschiedenis(
            definitie_id, wijziging_type, gewijzigd_door, reden
        )

    def _log_import_export(
        self,
        operatie_type: str,
        bestand_pad: str,
        verwerkt: int,
        succesvol: int,
        gefaald: int,
    ):
        self._audit.log_import_export(
            operatie_type, bestand_pad, verwerkt, succesvol, gefaald
        )

    # === Voorbeelden ===
    def save_voorbeelden(
        self,
        definitie_id: int,
        voorbeelden_dict: dict[str, list[str]],
        generation_model: str | None = None,
        generation_params: dict[str, Any] | None = None,
        gegenereerd_door: str = "system",
        voorkeursterm: str | None = None,
    ) -> list[int]:
        return self._voorbeelden.save_voorbeelden(
            definitie_id,
            voorbeelden_dict,
            generation_model,
            generation_params,
            gegenereerd_door,
            voorkeursterm,
            get_definitie_fn=self.get_definitie,
        )

    def get_voorbeelden(
        self,
        definitie_id: int,
        voorbeeld_type: str | None = None,
        actief_only: bool = True,
    ) -> list[VoorbeeldenRecord]:
        return self._voorbeelden.get_voorbeelden(
            definitie_id, voorbeeld_type, actief_only
        )

    def get_voorbeelden_by_type(self, definitie_id: int) -> dict[str, list[str]]:
        return self._voorbeelden.get_voorbeelden_by_type(definitie_id)

    def get_voorkeursterm(self, definitie_id: int) -> str | None:
        return self._voorbeelden.get_voorkeursterm(definitie_id)

    def beoordeel_voorbeeld(
        self,
        voorbeeld_id: int,
        beoordeeling: str,
        beoordeeling_notities: str = "",
        beoordeeld_door: str = "user",
    ) -> bool:
        return self._voorbeelden.beoordeel_voorbeeld(
            voorbeeld_id,
            beoordeeling,
            beoordeeling_notities,
            beoordeeld_door,
        )

    def delete_voorbeelden(
        self, definitie_id: int, voorbeeld_type: str | None = None
    ) -> int:
        return self._voorbeelden.delete_voorbeelden(definitie_id, voorbeeld_type)

    # === Synonym sync (backward compat) ===
    def _sync_synonyms_to_registry(
        self, definitie_id: int, synoniemen: list[str], edited_by: str
    ):
        self._synonym_sync.sync_synonyms_to_registry(
            definitie_id,
            synoniemen,
            edited_by,
            get_definitie_fn=self.get_definitie,
        )


# === Singleton pattern ===
_repository_singleton: DefinitieRepository | None = None


def _validate_repository_connection(repo: DefinitieRepository) -> bool:
    """Validate that the repository's database connection is still alive."""
    try:
        with repo._get_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Repository connection validation failed: {e}")
        return False


def get_definitie_repository(db_path: str | None = None) -> DefinitieRepository:
    """Haal gedeelde repository instance op (singleton pattern)."""
    global _repository_singleton

    if _repository_singleton is not None:
        if db_path is not None:
            current_path = getattr(_repository_singleton, "db_path", None)
            if current_path and Path(db_path).resolve() != Path(current_path).resolve():
                logger.warning(
                    f"get_definitie_repository called with db_path='{db_path}' "
                    f"but singleton already exists with path='{current_path}'. "
                    "Returning existing singleton. Use clear_repository_singleton() first if needed."
                )
        return _repository_singleton

    if not db_path:
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / "data" / "definities.db")

    _repository_singleton = DefinitieRepository(db_path)
    logger.info(f"DefinitieRepository singleton created: {db_path}")

    return _repository_singleton


def clear_repository_singleton() -> None:
    """Clear de repository singleton (voor testing/development)."""
    global _repository_singleton
    if _repository_singleton is not None:
        logger.info("DefinitieRepository singleton cleared")
        _repository_singleton = None


def validate_and_get_repository(db_path: str | None = None) -> DefinitieRepository:
    """Get repository with connection validation."""
    if _repository_singleton is not None:
        if not _validate_repository_connection(_repository_singleton):
            logger.info("Stale repository connection detected, reinitializing...")
            clear_repository_singleton()

    return get_definitie_repository(db_path)
