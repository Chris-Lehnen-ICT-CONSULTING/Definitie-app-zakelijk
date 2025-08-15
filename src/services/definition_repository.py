"""
DefinitionRepository service implementatie.

Deze service is verantwoordelijk voor het opslaan en ophalen van definities
uit de database met een clean interface.
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from services.interfaces import DefinitionRepositoryInterface, Definition

# Import bestaande repository voor backward compatibility
from database.definitie_repository import (
    DefinitieRepository as LegacyRepository,
    DefinitieRecord,
    DefinitieStatus,
    SourceType,
)

logger = logging.getLogger(__name__)


class DefinitionRepository(DefinitionRepositoryInterface):
    """
    Service voor definitie opslag en retrieval.

    Deze implementatie wraps de bestaande DefinitieRepository en
    maakt het herbruikbaar als een focused service met de nieuwe interface.
    """

    def __init__(self, db_path: str = "definities.db"):
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

        # Converteer Definition naar DefinitieRecord
        record = self._definition_to_record(definition)

        try:
            # Gebruik legacy repository voor opslag
            if definition.id:
                # Update bestaande
                self.legacy_repo.update_definitie(definition.id, record)
                return definition.id
            else:
                # Maak nieuwe
                new_id = self.legacy_repo.create_definitie(record)
                return new_id

        except Exception as e:
            logger.error(f"Fout bij opslaan definitie: {e}")
            raise

    def get(self, definition_id: int) -> Optional[Definition]:
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

    def search(self, query: str, limit: int = 10) -> List[Definition]:
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
            # Converteer naar record
            record = self._definition_to_record(definition)

            # Update via legacy repo
            self.legacy_repo.update_definitie(definition_id, record)
            return True

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

    # Additional repository methods

    def find_by_begrip(self, begrip: str) -> Optional[Definition]:
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

    def find_duplicates(self, definition: Definition) -> List[Definition]:
        """
        Vind mogelijke duplicaten van een definitie.

        Args:
            definition: Definitie om duplicaten voor te vinden

        Returns:
            Lijst van mogelijke duplicaten
        """
        try:
            # Gebruik legacy duplicate detection
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

    def get_by_status(self, status: str, limit: int = 50) -> List[Definition]:
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

    # Private helper methods

    def _definition_to_record(self, definition: Definition) -> DefinitieRecord:
        """Converteer Definition naar DefinitieRecord."""
        record = DefinitieRecord(
            id=definition.id,
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=definition.categorie or "proces",
            organisatorische_context=definition.context or "",
            juridische_context=(
                definition.metadata.get("juridische_context")
                if definition.metadata
                else None
            ),
            status=(
                definition.metadata.get("status", DefinitieStatus.DRAFT.value)
                if definition.metadata
                else DefinitieStatus.DRAFT.value
            ),
            source_type=SourceType.GENERATED.value,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

        # Voeg extra metadata toe indien aanwezig
        if definition.metadata:
            if "validation_score" in definition.metadata:
                record.validation_score = definition.metadata["validation_score"]
            if "source_reference" in definition.metadata:
                record.source_reference = definition.metadata["source_reference"]
            if "created_by" in definition.metadata:
                record.created_by = definition.metadata["created_by"]

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

        definition = Definition(
            id=record.id,
            begrip=record.begrip,
            definitie=definitie_text,
            toelichting=toelichting,
            bron=record.source_reference,
            context=record.organisatorische_context,
            categorie=record.categorie,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata={
                "status": record.status,
                "juridische_context": record.juridische_context,
                "validation_score": record.validation_score,
                "source_type": record.source_type,
                "created_by": record.created_by,
                "version_number": record.version_number,
            },
        )

        # Parse eventuele JSON velden
        if record.validation_issues:
            try:
                definition.metadata["validation_issues"] = json.loads(
                    record.validation_issues
                )
            except:
                pass

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
                try:
                    value = datetime.fromisoformat(value)
                except:
                    pass

            record_data[col_name] = value

        return DefinitieRecord(**record_data)

    # Statistics methods

    def get_stats(self) -> Dict[str, Any]:
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

        except:
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
