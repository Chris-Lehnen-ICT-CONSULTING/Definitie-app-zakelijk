"""
DefinitionRepository service implementatie.

Deze service is verantwoordelijk voor het opslaan en ophalen van definities
uit de database met een clean interface.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager, suppress
from datetime import datetime
from typing import Any

# Import bestaande repository voor backward compatibility
from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository as LegacyRepository,
    DefinitieStatus,
    SourceType,
)
from services.interfaces import Definition, DefinitionRepositoryInterface

logger = logging.getLogger(__name__)


class DefinitionRepository(DefinitionRepositoryInterface):
    """
    Service voor definitie opslag en retrieval.

    Deze implementatie wraps de bestaande DefinitieRepository en
    maakt het herbruikbaar als een focused service met de nieuwe interface.
    """

    def __init__(self, db_path: str = "data/definities.db"):
        """
        Initialiseer de DefinitionRepository.

        Args:
            db_path: Pad naar de SQLite database
        """
        self.legacy_repo = LegacyRepository(db_path)
        self.db_path = db_path
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }

        # Inject business services indien beschikbaar
        self._duplicate_service = None

        logger.info(f"DefinitionRepository geïnitialiseerd met database: {db_path}")

    def save(self, definition: Definition) -> int:
        """
        Sla een definitie op in de repository.

        Args:
            definition: Op te slaan definitie

        Returns:
            ID van de opgeslagen definitie

        Raises:
            sqlite3.Error: Bij database fouten
        """
        self._stats["total_saves"] += 1

        try:
            # Gebruik legacy repository voor opslag
            if definition.id:
                # Update bestaande via updates‑dict (legacy repo verwacht dict)
                updates = self._definition_to_updates(definition)
                updated_by = None
                if definition.metadata and "updated_by" in definition.metadata:
                    updated_by = definition.metadata["updated_by"]
                self.legacy_repo.update_definitie(definition.id, updates, updated_by)
                return definition.id
            # Maak nieuwe
            # Converteer Definition naar DefinitieRecord
            record = self._definition_to_record(definition)
            # Bypass duplicate guard indien expliciet toegestaan via metadata
            allow_duplicate = False
            try:
                if definition.metadata and bool(definition.metadata.get("force_duplicate")):
                    allow_duplicate = True
            except Exception:
                allow_duplicate = False
            return self.legacy_repo.create_definitie(record, allow_duplicate=allow_duplicate)

        except Exception as e:
            logger.error(f"Fout bij opslaan definitie: {e}")
            raise

    def get(self, definition_id: int) -> Definition | None:
        """
        Haal een definitie op basis van ID.

        Args:
            definition_id: ID van de definitie

        Returns:
            Definition indien gevonden, anders None
        """
        try:
            record = self.legacy_repo.get_definitie(definition_id)
            if record:
                return self._record_to_definition(record)
            return None
        except Exception as e:
            logger.error(f"Fout bij ophalen definitie {definition_id}: {e}")
            return None

    def search(self, query: str, limit: int = 10) -> list[Definition]:
        """
        Zoek definities op basis van een query.

        Args:
            query: Zoekterm
            limit: Maximum aantal resultaten

        Returns:
            Lijst van gevonden definities
        """
        self._stats["total_searches"] += 1

        try:
            # Gebruik legacy search
            results = self.legacy_repo.search(search_term=query, limit=limit)

            # Converteer records naar definitions
            definitions = []
            for record in results:
                definition = self._record_to_definition(record)
                if definition:
                    definitions.append(definition)

            return definitions

        except Exception as e:
            logger.error(f"Fout bij zoeken naar '{query}': {e}")
            return []

    def update(self, definition_id: int, definition: Definition) -> bool:
        """
        Update een bestaande definitie.

        Args:
            definition_id: ID van de te updaten definitie
            definition: Nieuwe definitie data

        Returns:
            True indien succesvol, anders False
        """
        self._stats["total_updates"] += 1

        try:
            # Converteer naar updates‑dict (legacy verwacht dict)
            updates = self._definition_to_updates(definition)

            updated_by = None
            if definition.metadata and "updated_by" in definition.metadata:
                updated_by = definition.metadata["updated_by"]

            # Update via legacy repo
            ok = self.legacy_repo.update_definitie(definition_id, updates, updated_by)
            return bool(ok)

        except Exception as e:
            logger.error(f"Fout bij updaten definitie {definition_id}: {e}")
            return False

    def delete(self, definition_id: int) -> bool:
        """
        Verwijder een definitie.

        Args:
            definition_id: ID van de te verwijderen definitie

        Returns:
            True indien succesvol, anders False
        """
        self._stats["total_deletes"] += 1

        try:
            # Gebruik legacy delete (soft delete via status)
            record = self.legacy_repo.get_definitie(definition_id)
            if record:
                record.status = DefinitieStatus.ARCHIVED.value
                self.legacy_repo.update_definitie(definition_id, record)
                return True
            return False

        except Exception as e:
            logger.error(f"Fout bij verwijderen definitie {definition_id}: {e}")
            return False

    def hard_delete(self, definition_id: int) -> bool:
        """
        Verwijder een definitie permanent (hard delete).

        Args:
            definition_id: ID van de te verwijderen definitie

        Returns:
            True indien succesvol, anders False
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM definities WHERE id = ?", (definition_id,))
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Fout bij hard delete definitie {definition_id}: {e}")
            return False

    # Additional repository methods

    def find_by_begrip(self, begrip: str) -> Definition | None:
        """
        Vind definitie op basis van exact begrip.

        Args:
            begrip: Het begrip om te zoeken

        Returns:
            Definition indien gevonden, anders None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM definities
                    WHERE begrip = ? AND status != ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """,
                    (begrip, DefinitieStatus.ARCHIVED.value),
                )

                row = cursor.fetchone()
                if row:
                    record = self._row_to_record(row, cursor.description)
                    return self._record_to_definition(record)
                return None

        except Exception as e:
            logger.error(f"Fout bij zoeken begrip '{begrip}': {e}")
            return None

    def find_duplicates(self, definition: Definition) -> list[Definition]:
        """
        Vind mogelijke duplicaten van een definitie.

        Args:
            definition: Definitie om duplicaten voor te vinden

        Returns:
            Lijst van mogelijke duplicaten
        """
        try:
            # Check if we have the new duplicate detection service
            if self._duplicate_service is not None:
                # Use new business logic service
                all_definitions = self._get_all_definitions()
                matches = self._duplicate_service.find_duplicates(
                    definition, all_definitions
                )

                # Return just the definitions
                return [match.definition for match in matches]
            # Fallback to legacy duplicate detection
            record = self._definition_to_record(definition)
            matches = self.legacy_repo.find_duplicates(record)

            duplicates = []
            for match in matches:
                dup_def = self._record_to_definition(match.definitie_record)
                if dup_def:
                    duplicates.append(dup_def)

            return duplicates

        except Exception as e:
            logger.error(f"Fout bij duplicaat detectie: {e}")
            return []

    def get_by_status(self, status: str, limit: int = 50) -> list[Definition]:
        """
        Haal definities op met een specifieke status.

        Args:
            status: Status om op te filteren (draft, review, established, archived)
            limit: Maximum aantal resultaten

        Returns:
            Lijst van definities met de gegeven status
        """
        try:
            records = self.legacy_repo.get_by_status(status, limit)

            definitions = []
            for record in records:
                definition = self._record_to_definition(record)
                if definition:
                    definitions.append(definition)

            return definitions

        except Exception as e:
            logger.error(f"Fout bij ophalen status '{status}': {e}")
            return []

    def get_or_create_draft(
        self,
        begrip: str,
        context: dict[str, Any] | None = None
    ) -> int:
        """
        Get existing draft or create new one for begrip+context combination.

        Ensures exactly one draft exists per unique begrip+context combination.
        This enables stateless editing without session state dependencies.

        Args:
            begrip: The term/concept being defined
            context: Dictionary with context information:
                - organisatorische_context: list[str]
                - juridische_context: list[str]
                - categorie: str (ontological category)

        Returns:
            ID of existing or newly created draft definition

        Note:
            Uses UNIQUE constraint on (begrip, organisatorische_context,
            juridische_context, categorie, status) to ensure uniqueness.
        """
        import json

        # Prepare context values
        context = context or {}
        org_context = json.dumps(sorted(context.get("organisatorische_context", [])))
        jur_context = json.dumps(sorted(context.get("juridische_context", [])))
        categorie = context.get("categorie", "OTH")  # Default to "OTH" (Other)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # First try to find existing draft
                cursor.execute(
                    """
                    SELECT id FROM definities
                    WHERE begrip = ?
                    AND organisatorische_context = ?
                    AND juridische_context = ?
                    AND categorie = ?
                    AND status = 'draft'
                    LIMIT 1
                    """,
                    (begrip, org_context, jur_context, categorie)
                )

                row = cursor.fetchone()
                if row:
                    draft_id = row[0]
                    logger.info(
                        f"Found existing draft {draft_id} for begrip='{begrip}', "
                        f"categorie={categorie}"
                    )
                    return draft_id

                # No existing draft found, create new one
                cursor.execute(
                    """
                    INSERT INTO definities (
                        begrip,
                        definitie,
                        organisatorische_context,
                        juridische_context,
                        categorie,
                        status,
                        created_at,
                        updated_at,
                        created_by
                    ) VALUES (?, ?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                    """,
                    (
                        begrip,
                        "",  # Empty definition for new draft
                        org_context,
                        jur_context,
                        categorie,
                        context.get("created_by", "system")
                    )
                )

                conn.commit()
                draft_id = cursor.lastrowid

                logger.info(
                    f"Created new draft {draft_id} for begrip='{begrip}', "
                    f"categorie={categorie}"
                )
                return draft_id

        except Exception as e:
            logger.error(f"Error in get_or_create_draft for '{begrip}': {e}")
            # If we hit a UNIQUE constraint violation, try to fetch again
            # (race condition protection)
            if "UNIQUE constraint failed" in str(e):
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT id FROM definities
                        WHERE begrip = ?
                        AND organisatorische_context = ?
                        AND juridische_context = ?
                        AND categorie = ?
                        AND status = 'draft'
                        LIMIT 1
                        """,
                        (begrip, org_context, jur_context, categorie)
                    )
                    row = cursor.fetchone()
                    if row:
                        return row[0]
            raise

    def set_duplicate_service(self, duplicate_service):
        """
        Inject the duplicate detection service.

        Args:
            duplicate_service: Instance of DuplicateDetectionService
        """
        self._duplicate_service = duplicate_service
        logger.info("DuplicateDetectionService injected into repository")

    def _get_all_definitions(self) -> list[Definition]:
        """
        Helper method to get all definitions for duplicate checking.

        Returns:
            List of all non-archived definitions
        """
        try:
            # Get all definitions except archived ones
            all_records = self.legacy_repo.search_definities(
                status=None,
                limit=1000,  # All statuses  # Reasonable limit
            )

            definitions = []
            for record in all_records:
                # Skip archived definitions
                if record.status != DefinitieStatus.ARCHIVED.value:
                    definition = self._record_to_definition(record)
                    if definition:
                        # Add status to definition object for duplicate service
                        definition.status = record.status
                        definitions.append(definition)

            return definitions

        except Exception as e:
            logger.error(f"Error fetching all definitions: {e}")
            return []

    # ===== Examples (voorbeelden) helpers - delegated to legacy repo =====
    def get_voorbeelden_by_type(self, definitie_id: int) -> dict[str, list[str]]:
        """Haal voorbeelden per type op via legacy repository.

        Args:
            definitie_id: ID van de definitie

        Returns:
            Dict met keys: 'voorbeeldzinnen', 'praktijkvoorbeelden', 'tegenvoorbeelden',
            'synoniemen', 'antoniemen' indien aanwezig; lege dict bij afwezigheid/fout.
        """
        try:
            return self.legacy_repo.get_voorbeelden_by_type(definitie_id)  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning(
                f"Legacy voorbeelden by type unavailable for definitie {definitie_id}: {e}"
            )
            return {}

    # Private helper methods

    def _definition_to_record(self, definition: Definition) -> DefinitieRecord:
        """Converteer Definition naar DefinitieRecord."""
        import json as _json
        # Bepaal bron type op basis van metadata (import vs generated)
        source_type_value = SourceType.GENERATED.value
        try:
            if definition.metadata and definition.metadata.get("source_type"):
                # Alleen toestaan als waarde overeenkomt met bekende SourceType opties
                st_val = str(definition.metadata.get("source_type")).lower()
                if st_val in {"generated", "imported", "manual"}:
                    source_type_value = st_val
        except Exception:
            pass

        record = DefinitieRecord(
            id=definition.id,
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=definition.categorie or "proces",
            organisatorische_context=_json.dumps(
                definition.organisatorische_context or [], ensure_ascii=False
            ),
            juridische_context=_json.dumps(
                definition.juridische_context or [], ensure_ascii=False
            ),
            status=(
                definition.metadata.get("status", DefinitieStatus.DRAFT.value)
                if definition.metadata
                else DefinitieStatus.DRAFT.value
            ),
            source_type=source_type_value,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

        # Wettelijke basis (JSON array)
        try:
            wb_list = list(definition.wettelijke_basis or [])
            # Normaliseer lijst naar gesorteerde, unieke waarden voor consistente opslag
            record.set_wettelijke_basis(wb_list)
        except Exception:
            # Laat default/None staan als iets misgaat
            pass

        # Voeg extra metadata toe indien aanwezig
        if definition.metadata:
            if "validation_score" in definition.metadata:
                record.validation_score = definition.metadata["validation_score"]
            if "source_reference" in definition.metadata:
                record.source_reference = definition.metadata["source_reference"]
            if "created_by" in definition.metadata:
                record.created_by = definition.metadata["created_by"]
            # Herkomst voor import
            if "imported_from" in definition.metadata:
                try:
                    record.imported_from = str(definition.metadata["imported_from"])  # type: ignore[attr-defined]
                except Exception:
                    pass

        # Voeg toelichting toe aan definitie tekst indien aanwezig
        if definition.toelichting:
            record.definitie = (
                f"{definition.definitie}\n\nToelichting: {definition.toelichting}"
            )

        return record

    def _record_to_definition(self, record: DefinitieRecord) -> Definition:
        """Converteer DefinitieRecord naar Definition."""
        # Split definitie en toelichting indien aanwezig
        definitie_text = record.definitie
        toelichting = None

        if "\n\nToelichting:" in definitie_text:
            parts = definitie_text.split("\n\nToelichting:", 1)
            definitie_text = parts[0]
            toelichting = parts[1].strip() if len(parts) > 1 else None

        import json as _json
        # Parse context JSON arrays (safe fallbacks)
        def _parse_list(val):
            try:
                if not val:
                    return []
                return list(_json.loads(val)) if isinstance(val, str) else list(val)
            except Exception:
                return []

        definition = Definition(
            id=record.id,
            begrip=record.begrip,
            definitie=definitie_text,
            toelichting=toelichting,
            bron=record.source_reference,
            organisatorische_context=_parse_list(record.organisatorische_context),
            juridische_context=_parse_list(record.juridische_context),
            wettelijke_basis=record.get_wettelijke_basis_list(),
            categorie=record.categorie,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata={
                "status": record.status,
                "validation_score": record.validation_score,
                "source_type": record.source_type,
                "created_by": record.created_by,
                "version_number": record.version_number,
            },
        )

        # Parse eventuele JSON velden
        if record.validation_issues:
            with suppress(json.JSONDecodeError, ValueError):
                definition.metadata["validation_issues"] = json.loads(
                    record.validation_issues
                )

        return definition

    @contextmanager
    def _get_connection(self):
        """Context manager voor database connecties."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_record(self, row: sqlite3.Row, description) -> DefinitieRecord:
        """Converteer database row naar DefinitieRecord."""
        # Map row naar record attributes
        record_data = {}
        for idx, col in enumerate(description):
            col_name = col[0]
            value = row[idx]

            # Converteer datetime strings
            if col_name.endswith("_at") and value:
                with suppress(ValueError, TypeError):
                    value = datetime.fromisoformat(value)

            record_data[col_name] = value

        return DefinitieRecord(**record_data)

    # Statistics methods

    def get_stats(self) -> dict[str, Any]:
        """Haal repository statistieken op."""
        stats = self._stats.copy()

        # Voeg database stats toe
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Tel totaal aantal definities
                cursor.execute(
                    "SELECT COUNT(*) FROM definities WHERE status != ?",
                    (DefinitieStatus.ARCHIVED.value,),
                )
                stats["total_definitions"] = cursor.fetchone()[0]

                # Tel per status
                cursor.execute(
                    """
                    SELECT status, COUNT(*)
                    FROM definities
                    GROUP BY status
                """
                )
                stats["by_status"] = dict(cursor.fetchall())

        except (sqlite3.Error, Exception):
            pass

        return stats

    def reset_stats(self) -> None:
        """Reset de statistieken."""
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }

    # ===== Legacy compatibility surface for workflow/UI =====
    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        """Pass‑through naar legacy repository (compat met bestaande callers)."""
        try:
            return self.legacy_repo.get_definitie(definitie_id)
        except Exception:
            return None

    def update_definitie(
        self, definitie_id: int, updates: dict[str, Any], updated_by: str | None = None
    ) -> bool:
        """Pass‑through update voor compatibiliteit."""
        try:
            return self.legacy_repo.update_definitie(definitie_id, updates, updated_by)
        except Exception:
            return False

    def change_status(
        self,
        definitie_id: int,
        new_status: "DefinitieStatus",
        changed_by: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Pass‑through statuswijziging voor compatibiliteit met workflowservice."""
        try:
            return self.legacy_repo.change_status(
                definitie_id, new_status, changed_by, notes
            )
        except Exception:
            return False

    # ===== Helpers =====
    def _definition_to_updates(self, definition: Definition) -> dict[str, Any]:
        """Converteer Definition naar updates‑dict voor legacy update_definitie()."""
        import json as _json
        updates: dict[str, Any] = {}
        if definition.begrip is not None:
            updates["begrip"] = definition.begrip
        if definition.definitie is not None:
            updates["definitie"] = definition.definitie
        if definition.categorie is not None:
            updates["categorie"] = definition.categorie
        # Contextvelden (JSON strings)
        updates["organisatorische_context"] = _json.dumps(
            definition.organisatorische_context or [], ensure_ascii=False
        )
        updates["juridische_context"] = _json.dumps(
            definition.juridische_context or [], ensure_ascii=False
        )
        try:
            updates["wettelijke_basis"] = (
                None
                if definition.wettelijke_basis is None
                else _json.dumps(list(definition.wettelijke_basis), ensure_ascii=False)
            )
        except Exception:
            updates["wettelijke_basis"] = None
        # Embed toelichting in definitietekst indien aanwezig (consistent met create)
        try:
            if definition.toelichting and str(definition.toelichting).strip():
                base = updates.get("definitie", definition.definitie or "")
                if base is None:
                    base = ""
                # Voorkom dubbele embed: _record_to_definition levert definitie zonder 'Toelichting:'
                # dus we kunnen veilig toevoegen
                updates["definitie"] = f"{base}\n\nToelichting: {str(definition.toelichting).strip()}"
        except Exception:
            pass

        # Extra velden
        if definition.metadata and "status" in definition.metadata:
            updates["status"] = definition.metadata["status"]
        return updates
