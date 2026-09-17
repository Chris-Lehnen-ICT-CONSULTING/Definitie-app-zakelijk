"""
DefinitieRepository - Facade voor de database laag (DEF-389).

Delegeert naar gefocuste sub-modules. Alle publieke symbolen worden
ge-re-exporteerd voor backward compatibility.
"""

import logging
import sqlite3
from collections.abc import Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.definitie_crud import (
    UNSET,
    Bronhelpers,
    DefinitieCrudRepository,
    Unset,
)
from database.definitie_duplicates import (
    DefinitieDuplicateRepository,
    DuplicaatKandidaatRij,
)
from database.definitie_import_export import DefinitieImportExportRepository
from database.definitie_search import DefinitieSearchRepository
from database.models import (
    DefinitieRecord,
    DefinitieStatus,
    DuplicateMatch,
    SourceType,
    VaststelconflictError,
    VoorbeeldenRecord,
    Voorstelreservering,
    Voorsteltoepassing,
)
from database.synonym_sync import SynonymSyncService
from database.voorbeelden_repository import VoorbeeldenRepository
from domain.ontological_categories import OntologischeCategorie

__all__ = [
    "UNSET",
    "Bronhelpers",
    "DefinitieRecord",
    "DefinitieRepository",
    "DefinitieStatus",
    "DuplicateMatch",
    "SourceType",
    "Unset",
    "VaststelconflictError",
    "VoorbeeldenRecord",
    "Voorstelreservering",
    "Voorsteltoepassing",
    "clear_repository_singleton",
    "get_definitie_repository",
    "validate_and_get_repository",
]

logger = logging.getLogger(__name__)


class DefinitieRepository:
    """Facade — delegeert naar gefocuste sub-repositories."""

    def __init__(
        self,
        db_path: str = "data/definities.db",
        *,
        bronhelpers: Bronhelpers | None = None,
    ):
        self.db_path = db_path
        self._db = DatabaseConnection(db_path)
        self._db.init_database()
        self._audit = AuditHelpers(self._db)
        self._duplicates = DefinitieDuplicateRepository(self._db, self._audit)
        self._search = DefinitieSearchRepository(self._db, self._audit)
        self._crud = DefinitieCrudRepository(
            self._db,
            self._audit,
            self._duplicates,
            self._search,
            bronhelpers=bronhelpers,
        )
        self._import_export = DefinitieImportExportRepository(self._db, self._audit)
        self._synonym_sync = SynonymSyncService(
            self._db, get_registry_fn=self._get_synonym_registry
        )
        self._voorbeelden = VoorbeeldenRepository(self._db, self._synonym_sync)

    @staticmethod
    def _get_synonym_registry() -> Any:
        """Lazy registry lookup — houdt database laag vrij van service imports."""
        from services.container import get_container

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

    def _init_database(self) -> None:
        self._db.init_database()

    def _split_sql_statements(self, sql: str) -> list[str]:
        return self._db.split_sql_statements(sql)

    # === CRUD ===
    def create_definitie(
        self,
        record: DefinitieRecord,
        allow_duplicate: bool = False,
        duplicate_reason: str | None = None,
        *,
        categoriekeuze: Mapping[str, Any] | None = None,
    ) -> int:
        return self._crud.create_definitie(
            record, allow_duplicate, duplicate_reason, categoriekeuze=categoriekeuze
        )

    def record_category_choice(
        self,
        definitie_id: int,
        updates: Mapping[str, Any],
        *,
        waarde: str | None,
        herkomst: str,
        actor: str | None,
        actor_source: str | None,
        updated_by: str | None,
        expected_version: int,
    ) -> bool:
        """Expliciet commando voor een menselijke categoriekeuze (DEF-751 B2)."""
        return self._crud.record_category_choice(
            definitie_id,
            updates,
            waarde=waarde,
            herkomst=herkomst,
            actor=actor,
            actor_source=actor_source,
            updated_by=updated_by,
            expected_version=expected_version,
        )

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
        *,
        ketenpartners: list[str] | None = None,
        ufo_categorie: str | Unset | None = UNSET,
        expected_version: int | None = None,
    ) -> bool:
        return self._crud.change_status(
            definitie_id,
            new_status,
            changed_by,
            notes,
            ketenpartners=ketenpartners,
            ufo_categorie=ufo_categorie,
            expected_version=expected_version,
        )

    # === Contextcontract en vaststelinvariant (DEF-622) ===
    def find_leidende_definitie(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any = "",
        wettelijke_basis: Any = None,
        *,
        eigen_id: int | None = None,
    ) -> DefinitieRecord | None:
        """Het vastgestelde, leidende record voor begrip + volledige context."""
        return self._crud.find_leidende_definitie(
            begrip,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            eigen_id=eigen_id,
        )

    def set_context_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Leg de CON-01-expertbeoordeling van de naamfunctie vast.

        ``expected_version`` is de recordversie die de beoordelaar beoordeeld
        heeft; wijkt de opgeslagen versie af, dan wordt niets geschreven.
        """
        return self._crud.set_context_review(
            definitie_id, review, updated_by, expected_version=expected_version
        )

    # === Bronbewijs, CON-02-uitzondering en voorstellen (DEF-743) ===
    def set_source_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Leg de CON-02-deskundigenuitzondering vast (platte getypeerde vorm)."""
        return self._crud.set_source_review(
            definitie_id, review, updated_by, expected_version=expected_version
        )

    def set_source_assessment(
        self,
        definitie_id: int,
        assessment: dict[str, Any],
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Vervang de AI-bronbeoordeling in het actuele bewijs (herbeoordeling)."""
        return self._crud.set_source_assessment(
            definitie_id, assessment, updated_by, expected_version=expected_version
        )

    def reserve_source_proposal(
        self, definitie_id: int, *, updated_by: str, expected_version: int
    ) -> Voorstelreservering:
        return self._crud.reserve_source_proposal(
            definitie_id, updated_by=updated_by, expected_version=expected_version
        )

    def record_source_proposal_outcome(
        self,
        definitie_id: int,
        proposal_id: str,
        outcome: dict[str, Any],
        *,
        updated_by: str,
        expected_version: int,
    ) -> bool:
        return self._crud.record_source_proposal_outcome(
            definitie_id,
            proposal_id,
            outcome,
            updated_by=updated_by,
            expected_version=expected_version,
        )

    def apply_source_proposal(
        self,
        definitie_id: int,
        proposal_id: str,
        *,
        updated_by: str,
        expected_version: int,
        validation: dict[str, Any],
        source_assessment: dict[str, Any] | None = None,
    ) -> Voorsteltoepassing:
        return self._crud.apply_source_proposal(
            definitie_id,
            proposal_id,
            updated_by=updated_by,
            expected_version=expected_version,
            validation=validation,
            source_assessment=source_assessment,
        )

    def set_source_proposal_status(
        self,
        definitie_id: int,
        proposal_id: str,
        status: str,
        updated_by: str,
        *,
        expected_version: int,
        note: str | None = None,
    ) -> bool:
        return self._crud.set_source_proposal_status(
            definitie_id,
            proposal_id,
            status,
            updated_by,
            expected_version=expected_version,
            note=note,
        )

    # === Transactiegrens (DEF-482) ===
    def transaction(
        self, timeout: float = 30.0
    ) -> AbstractContextManager[sqlite3.Connection]:
        """Expliciete transactie op de thread-local connectie; nesting sluit aan."""
        return self._db.transaction(timeout)

    def in_transaction(self) -> bool:
        """True als de huidige thread al een transactie open heeft."""
        return bool(self._db.get_connection().in_transaction)

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

    def find_active_by_begrip(self, begrip: str) -> list[DuplicaatKandidaatRij]:
        """Alle actieve kandidaten met dit begrip, gepagineerd (DEF-672)."""
        return self._duplicates.find_active_by_begrip(begrip)

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
        # DEF-751 B2: een geïmporteerd record krijgt herkomst `import`; een
        # keuze-event in het bestand wordt niet als keuze overgenomen.
        return self._import_export.import_from_json(
            file_path,
            import_by,
            create_fn=lambda record: self.create_definitie(
                record, categoriekeuze={"origin": "import"}
            ),
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
