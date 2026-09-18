"""
DefinitionRepository service implementatie.

Deze service is verantwoordelijk voor het opslaan en ophalen van definities
uit de database met een clean interface.
"""

import json
import logging
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from copy import deepcopy
from datetime import datetime
from typing import Any, cast

# Import bestaande repository voor backward compatibility
from database.definitie_repository import (
    UNSET,
    Bronhelpers,
    Bronmetadatatoepassing,
    DefinitieRecord,
    DefinitieRepository as LegacyRepository,
    DefinitieStatus,
    SourceType,
    Unset,
    Voorstelreservering,
    Voorsteltoepassing,
)
from database.models import (
    KANDIDAATSTADIA,
    SOURCE_EVIDENCE_HISTORY_KEY,
    SOURCE_EVIDENCE_KEY,
    SOURCE_PROPOSALS_KEY,
    TOELICHTING_SCHEIDING,
    bouw_bronbewijs,
    serialiseer_generatieregistratie,
    splits_definitietekst,
)
from domain.categorie_herkomst import (
    lees_keuze_invoer,
)
from domain.context.normalisatie import (
    canoniseer_contextlijst,
    contextsleutel,
    lees_contextwaarden,
)
from services.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
    DefinitionServiceError,
    DuplicateDefinitionError,
    RepositoryError,
)
from services.interfaces import (
    Definition,
    DefinitionRepositoryInterface,
    DuplicateCandidate,
)

logger = logging.getLogger(__name__)

# DEF-469: vaste veilige meldingen; de oorzaak reist mee via `raise ... from e`.
MELDING_NIET_BEVESTIGD = (
    "Opslaan niet bevestigd; ververs de definitie en probeer opnieuw."
)
MELDING_DATABASEFOUT = "Databasefout tijdens opslaan; de wijziging is niet bevestigd."

__all__ = [
    "Bronhelpers",
    "Bronmetadatatoepassing",
    "DefinitionRepository",
    "Voorstelreservering",
    "Voorsteltoepassing",
    "bronnen_uit_metadata",
]


def bronnen_uit_metadata(metadata: dict[str, Any] | None) -> list[Any] | None:
    """De aangeleverde bronlijst uit `Definition.metadata`, of None (sleutel afwezig).

    `provenance_sources` is de canonieke sleutel, `sources` de legacy-alias
    (kerncontract C §1, freeze punt 2). Eén van beide volstaat; zijn beide
    aanwezig, dan moeten ze inhoudelijk gelijk zijn — anders wordt er geen
    keuze gemaakt maar gesloten geweigerd (`ValueError`). `None` als waarde
    telt als afwezig; niets wordt verzonnen.
    """
    if not metadata:
        return None
    kandidaten = {
        sleutel: metadata[sleutel]
        for sleutel in ("provenance_sources", "sources")
        if metadata.get(sleutel) is not None
    }
    if not kandidaten:
        return None
    for sleutel, waarde in kandidaten.items():
        if not isinstance(waarde, list):
            msg = f"{sleutel} moet een lijst zijn (gekregen: {type(waarde).__name__})"
            raise ValueError(msg)
    if len(kandidaten) == 2 and (
        kandidaten["provenance_sources"] != kandidaten["sources"]
    ):
        msg = (
            "provenance_sources en sources verschillen; de bronset is ambigu en "
            "wordt niet opgeslagen (fail-closed)"
        )
        raise ValueError(msg)
    return cast(list[Any], next(iter(kandidaten.values())))


def _bewijsinvoer_uit_metadata(metadata: dict[str, Any]) -> dict[str, Any] | None:
    """De structurele `source_evidence`-invoer voor de DB-laag, of None."""
    bronnen = bronnen_uit_metadata(metadata)
    if bronnen is None:
        return None
    return {
        "sources": deepcopy(bronnen),
        "source_receipt": deepcopy(metadata.get("source_receipt")),
        "source_assessment": deepcopy(metadata.get("source_assessment")),
        "peildatum": metadata.get("peildatum"),
        "generation_id": metadata.get("generation_id"),
        "generated_at": metadata.get("generated_at") or metadata.get("generation_time"),
        "tekststadia": {
            veld: metadata.get(veld)
            for veld in KANDIDAATSTADIA
            if metadata.get(veld) is not None
        },
    }


def _voeg_bewijsinvoer_toe(
    updates: dict[str, Any], metadata: dict[str, Any] | None
) -> None:
    """Zet de structurele `source_evidence`-invoer in `updates` als de metadata die draagt."""
    if not metadata:
        return
    bewijsinvoer = _bewijsinvoer_uit_metadata(metadata)
    if bewijsinvoer is not None:
        updates["source_evidence"] = bewijsinvoer


#: DEF-751 B2: de invoersleutel voor de herkomst van een categorie bij een
#: NIEUW record (`Definition.metadata`, generatieroute): alleen herkomst
#: manual/model + reasoning/scores, nooit een actor. Voor een bestaand record
#: is er geen metadata-transport: een menselijke keuze loopt uitsluitend via
#: `DefinitionRepository.save_met_categoriekeuze` → `record_category_choice`.
CATEGORY_CHOICE_INPUT_KEY = "category_choice_input"


class DefinitionRepository(DefinitionRepositoryInterface):
    """
    Service voor definitie opslag en retrieval.

    Deze implementatie wraps de bestaande DefinitieRepository en
    maakt het herbruikbaar als een focused service met de nieuwe interface.
    """

    def __init__(
        self,
        db_path: str = "data/definities.db",
        *,
        bronhelpers: Bronhelpers | None = None,
    ):
        """
        Initialiseer de DefinitionRepository.

        Args:
            db_path: Pad naar de SQLite database
            bronhelpers: alleen voor isolatie in tests; productie gebruikt de
                echte kernhelpers van `domain.sources` (DEF-743)
        """
        # Zonder seam blijft de aanroep exact de bestaande (bestaande tests
        # leggen de constructoraanroep vast).
        self.legacy_repo = (
            LegacyRepository(db_path)
            if bronhelpers is None
            else LegacyRepository(db_path, bronhelpers=bronhelpers)
        )
        self.db_path = db_path
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }

        # DuplicateDetectionService removed - was dead code (DEF-176)

        logger.info(f"DefinitionRepository geïnitialiseerd met database: {db_path}")

    def save(self, definition: Definition) -> int:
        """
        Sla een definitie op in de repository.

        Args:
            definition: Op te slaan definitie

        Returns:
            ID van de opgeslagen definitie. Binnen een open transactie bevestigt
            dit alleen uitvoering; pas de buitenste eigenaar commit (DEF-469).

        Raises:
            DuplicateDefinitionError: Als definitie al bestaat
            DatabaseConstraintError: Bij database constraint violations
            DatabaseConnectionError: Bij database verbindingsproblemen
            RepositoryError: Bij andere repository fouten
        """

        def melding(technisch: str) -> str:
            # DEF-469: het update-pad geeft een vaste veilige tekst (de oorzaak
            # reist mee via `from e`); het create-pad behoudt zijn detailtekst.
            return MELDING_DATABASEFOUT if definition.id else technisch

        try:
            # Gebruik legacy repository voor opslag
            if definition.id:
                # Update bestaande via updates-dict (legacy repo verwacht dict)
                updates = self._definition_to_updates(definition)
                updated_by = None
                if definition.metadata and "updated_by" in definition.metadata:
                    updated_by = definition.metadata["updated_by"]
                ok = self.legacy_repo.update_definitie(
                    definition.id, updates, updated_by
                )
                if not ok:  # False/None = niet bevestigd, nooit een succes-ID
                    raise RepositoryError(
                        "save_update", definition.begrip, MELDING_NIET_BEVESTIGD
                    )
                if not self.in_transaction():  # genest: nog geen duurzaam succes
                    self._stats["total_saves"] += 1
                    logger.info(
                        f"Updated definition '{definition.begrip}' (ID: {definition.id})"
                    )
                return cast(int, definition.id)

            # Maak nieuwe
            # Converteer Definition naar DefinitieRecord
            record = self._definition_to_record(definition)
            # Bypass duplicate guard indien expliciet toegestaan via metadata.
            # DEF-622 (besluit 5): de bijbehorende reden reist mee naar de
            # audit; de DB-laag weigert een geforceerd duplicaat zonder reden.
            allow_duplicate = False
            duplicate_reason: str | None = None
            try:
                if definition.metadata and bool(
                    definition.metadata.get("force_duplicate")
                ):
                    allow_duplicate = True
                    reden = definition.metadata.get("force_duplicate_reason")
                    duplicate_reason = reden if isinstance(reden, str) else None
            except (KeyError, TypeError, AttributeError) as e:
                logger.debug(
                    f"force_duplicate check failed for '{definition.begrip}': {e}"
                )
                allow_duplicate = False

            # DEF-751 B2: de herkomst van de categorie volgens deze route;
            # de persistentielaag bouwt het event (nooit met actor).
            result_id = self.legacy_repo.create_definitie(
                record,
                allow_duplicate=allow_duplicate,
                duplicate_reason=duplicate_reason,
                categoriekeuze=self._categoriekeuze_voor_nieuw_record(
                    definition.metadata or {}
                ),
            )

            if not result_id or result_id <= 0:
                raise RepositoryError(
                    operation="create",
                    begrip=definition.begrip,
                    message=f"Invalid ID returned: {result_id}",
                )

            if not self.in_transaction():  # genest: nog geen duurzaam succes
                self._stats["total_saves"] += 1
                logger.info(
                    f"Created definition '{definition.begrip}' (ID: {result_id}, "
                    f"categorie: {definition.categorie})"
                )
            return cast(int, result_id)

        except ValueError as e:
            # Legacy repo raises ValueError for duplicates
            if "bestaat al" in str(e).lower() or "already exists" in str(e).lower():
                raise DuplicateDefinitionError(
                    begrip=definition.begrip, message=str(e)
                ) from e
            # Other ValueErrors
            raise RepositoryError(
                operation="save", begrip=definition.begrip, message=str(e)
            ) from e

        except sqlite3.IntegrityError as e:
            error_msg = str(e).lower()
            if "not null" in error_msg or "null constraint" in error_msg:
                # Extract field name from error message
                field = "unknown"
                if "categorie" in error_msg:
                    field = "categorie"
                raise DatabaseConstraintError(
                    field=field,
                    begrip=definition.begrip,
                    message=melding(
                        f"NOT NULL constraint failed for field '{field}': {e}"
                    ),
                ) from e
            if "unique" in error_msg or "duplicate" in error_msg:
                raise DuplicateDefinitionError(
                    begrip=definition.begrip,
                    message=melding(f"Definition already exists: {e}"),
                ) from e
            # Other integrity errors
            raise DatabaseConstraintError(
                field="unknown",
                begrip=definition.begrip,
                message=melding(f"Database constraint violated: {e}"),
            ) from e

        except sqlite3.OperationalError as e:
            logger.error(f"Database connection failed for '{definition.begrip}': {e}")
            raise DatabaseConnectionError(
                db_path=self.db_path, message=melding(f"Database unavailable: {e}")
            ) from e

        except (
            DuplicateDefinitionError,
            DatabaseConstraintError,
            DatabaseConnectionError,
            RepositoryError,
        ):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.exception(
                f"Unexpected error saving '{definition.begrip}': {e}", exc_info=True
            )
            raise RepositoryError(
                operation="save",
                begrip=definition.begrip,
                message=melding(f"Unexpected error: {e}"),
            ) from e

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
            Lijst van gevonden definities (lege lijst = 0 matches).

        Raises:
            RepositoryError: bij een backend-fout. DEF-469: search faalt bewust
                fail-closed (raise) i.p.v. stil [] terug te geven, zodat callers
                (o.a. DUP_01) een DB-fout van "niets gevonden" kunnen onderscheiden.
                Let op: `update`/`delete` behouden hun bool value-contract — die
                hebben geen prod-callers die een fout-vs-False-onderscheid nodig
                hebben (zie DEF-469 caller-audit).
        """
        self._stats["total_searches"] += 1

        try:
            # Gebruik legacy search.
            # DEF-439: de DB-laag DefinitieRepository exposeert `search_definities`
            # met parameter `query` — niet `search(search_term=...)`. Het oude
            # aanroep-pad gooide stil AttributeError → search() gaf altijd [].
            results = self.legacy_repo.search_definities(query=query, limit=limit)

            # Converteer records naar definitions
            definitions = []
            for record in results:
                definition = self._record_to_definition(record)
                if definition:
                    definitions.append(definition)

            return definitions

        except Exception as e:
            # DEF-469: NIET stil een lege lijst teruggeven — dan kan de aanroeper
            # (o.a. de duplicaat-toetsregel DUP_01) een DB-fout niet van "niets
            # gevonden" onderscheiden en zou een duplicaat ongemerkt passeren.
            # Re-raise als typed RepositoryError zodat de aanroeper fail-closed kan.
            raise RepositoryError("search", query) from e

    def save_met_categoriekeuze(
        self,
        definition: Definition,
        *,
        herkomst: str,
        actor: str | None,
        actor_source: str | None,
        updated_by: str | None,
    ) -> int:
        """Sla een bestaand record op mét een menselijke categoriekeuze
        (editor-opslaan/toepassen) — het expliciete commando (DEF-751 B2).

        Alle veldwijzigingen, de categorie en het keuze-event landen in één
        UPDATE met de versie van de getoonde kandidaat
        (`metadata["version_number"]`) als optimistic lock. Zonder die versie
        of bij een tussentijdse wijziging: `RepositoryError`, niets geschreven.
        """
        if not definition.id:
            msg = "save_met_categoriekeuze vereist een bestaand record (id)"
            raise RepositoryError("save_choice", definition.begrip, msg)
        versie = (definition.metadata or {}).get("version_number")
        if not isinstance(versie, int) or isinstance(versie, bool):
            msg = (
                "save_met_categoriekeuze vereist de recordversie van de getoonde "
                "kandidaat (metadata.version_number)"
            )
            raise RepositoryError("save_choice", definition.begrip, msg)
        updates = self._definition_to_updates(definition)
        updates.pop("version_number", None)
        updates.pop("categorie", None)
        try:
            ok = self.legacy_repo.record_category_choice(
                definition.id,
                updates,
                waarde=definition.categorie or None,
                herkomst=herkomst,
                actor=actor,
                actor_source=actor_source,
                updated_by=updated_by,
                expected_version=versie,
            )
        except ValueError as e:
            raise RepositoryError("save_choice", definition.begrip, str(e)) from e
        if not ok:
            raise RepositoryError(
                "save_choice", definition.begrip, MELDING_NIET_BEVESTIGD
            )
        return cast(int, definition.id)

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
            # Converteer naar updates-dict (legacy verwacht dict)
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
            # Gebruik legacy delete (soft delete via status).
            # DEF-439: update_definitie(id, updates: dict) — niet (id, record).
            record = self.legacy_repo.get_definitie(definition_id)
            if record:
                self.legacy_repo.update_definitie(
                    definition_id, {"status": DefinitieStatus.ARCHIVED.value}
                )
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
            True bij bevestigde delete; False alleen bij ontbrekend ID. Opslag-/
            commitfouten worden typed (DEF-469); genest bevestigt True uitvoering.
        """
        sql = "DELETE FROM definities WHERE id = ?"
        with self.transaction() as conn:
            cursor = conn.execute(sql, (definition_id,))
        return cursor.rowcount > 0

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

    def find_duplicate_candidates(self, begrip: str) -> list[DuplicateCandidate]:
        """Actieve definities die met dit begrip kunnen botsen (DEF-672).

        Twee stappen, bewust gescheiden: de database begrenst op begrip en
        status, en de contextvergelijking gebeurt daarna op genormaliseerde
        sleutels. In SQL vergelijken zou op de ruwe, ordegevoelige JSON-string
        gebeuren — precies waarom de oude controle nooit matchte.

        De normalisatie gebeurt hier, bij het lezen, zodat bestaande records
        met een niet-canonieke schrijfwijze gewoon worden herkend en er geen
        datamigratie nodig is.
        """
        return [
            DuplicateCandidate(
                id=rij.id,
                status=rij.status,
                categorie=rij.categorie,
                organisatorische_context=contextsleutel(
                    self._contextwaarden(rij.organisatorische_context)
                ),
                juridische_context=contextsleutel(
                    self._contextwaarden(rij.juridische_context)
                ),
                wettelijke_basis=contextsleutel(
                    self._contextwaarden(rij.wettelijke_basis)
                ),
            )
            for rij in self.legacy_repo.find_active_by_begrip(begrip)
        ]

    @staticmethod
    def _contextwaarden(opgeslagen: Any) -> list[str]:
        """Lees een opgeslagen contextveld terug als losse waarden.

        Dunne laag over de gedeelde lezer `lees_contextwaarden` (DEF-622), zodat
        lookup, duplicaatcontrole en servicelaag dezelfde waarden zien.
        """
        return lees_contextwaarden(opgeslagen)

    def find_duplicates(self, definition: Definition) -> list[Definition]:
        """
        Vind mogelijke duplicaten van een definitie.

        Args:
            definition: Definitie om duplicaten voor te vinden

        Returns:
            Lijst van mogelijke duplicaten
        """
        try:
            # Use database-level duplicate detection (exact + synonym match)
            # DuplicateDetectionService removed - was dead code (DEF-176)
            # DEF-439: find_duplicates verwacht losse velden, geen record.
            # org/jur-context zijn op de record reeds JSON-strings (DB-formaat).
            record = self._definition_to_record(definition)
            matches = self.legacy_repo.find_duplicates(
                begrip=record.begrip,
                organisatorische_context=record.organisatorische_context,
                juridische_context=record.juridische_context or "",
                categorie=record.categorie,
            )

            duplicates = []
            for match in matches:
                dup_def = self._record_to_definition(match.definitie_record)
                if dup_def:
                    duplicates.append(dup_def)

            return duplicates

        except Exception as e:
            # DEF-469: NIET stil een lege lijst teruggeven — dan kan de aanroeper
            # een DB-fout niet van "geen duplicaten" onderscheiden en glipt een
            # duplicaat door als uniek record (data-integriteit). Re-raise als
            # typed RepositoryError zodat de aanroeper fail-closed kan afbreken.
            # Loggen gebeurt bij de aanroeper (met volledige exception-chain via
            # `from e`); hier dubbel loggen zou alleen ruis geven.
            raise RepositoryError("find_duplicates", definition.begrip) from e

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
            # DEF-439: DB-laag get_by_status(status) kent geen limit-arg;
            # begrens in Python.
            records = self.legacy_repo.get_by_status(status)[:limit]

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
        self, begrip: str, context: dict[str, Any] | None = None
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
                    (begrip, org_context, jur_context, categorie),
                )

                row = cursor.fetchone()
                if row:
                    draft_id = row[0]
                    logger.info(
                        f"Found existing draft {draft_id} for begrip='{begrip}', "
                        f"categorie={categorie}"
                    )
                    return cast(int, draft_id)

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
                        context.get("created_by", "system"),
                    ),
                )

                conn.commit()
                draft_id = cursor.lastrowid

                logger.info(
                    f"Created new draft {draft_id} for begrip='{begrip}', "
                    f"categorie={categorie}"
                )
                return cast(int, draft_id)

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
                        (begrip, org_context, jur_context, categorie),
                    )
                    row = cursor.fetchone()
                    if row:
                        return cast(int, row[0])
            raise

    # set_duplicate_service() removed - was dead code (DEF-176)
    # _get_all_definitions() removed - was dead code (DEF-176)

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
            return cast(
                dict[str, list[str]],
                self.legacy_repo.get_voorbeelden_by_type(definitie_id),  # type: ignore[attr-defined]
            )
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
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug(
                f"source_type extraction failed for '{definition.begrip}': {e}"
            )

        # DEF-751 B2 (schemaversie 4): geen label = NULL. De vroegere
        # DEF-53-default "proces" is vervallen; niets wordt verzonnen.
        category_value = (
            definition.categorie
            or getattr(definition, "ontologische_categorie", None)
            or None
        )
        logger.debug(
            f"Category mapping: categorie={definition.categorie}, "
            f"ontologische_categorie={getattr(definition, 'ontologische_categorie', None)}, "
            f"final={category_value}"
        )

        record = DefinitieRecord(
            id=definition.id,
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=category_value,
            ufo_categorie=getattr(definition, "ufo_categorie", None),
            toelichting_proces=getattr(definition, "toelichting_proces", None),
            # DEF-672: canoniek opslaan via dezelfde normalisatie die de
            # vergelijking gebruikt — getrimd, zonder lege waarden, ontdubbeld
            # en deterministisch gesorteerd. Bewust zónder casefold: dat zou
            # "DJI" als "dji" in de database en dus in de UI zetten. Herkenning
            # van bestaande, niet-canonieke waarden komt van de normalisatie bij
            # het lezen (`find_duplicate_candidates`), niet van de vorm op disk.
            organisatorische_context=_json.dumps(
                canoniseer_contextlijst(definition.organisatorische_context),
                ensure_ascii=False,
            ),
            juridische_context=_json.dumps(
                canoniseer_contextlijst(definition.juridische_context),
                ensure_ascii=False,
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
            # DEF-672: dezelfde canonieke vorm als de andere twee contextvelden.
            # `set_wettelijke_basis` sorteert en ontdubbelt daarna nog eens; op
            # een reeds canonieke lijst is dat idempotent, dus het bestaande
            # opslagformaat verschuift niet.
            wb_list = canoniseer_contextlijst(definition.wettelijke_basis)
            record.set_wettelijke_basis(wb_list)
        except Exception as exc:  # pragma: no cover - unexpected edge cases
            logger.warning(
                "Kon wettelijke basis normaliseren voor '%s': %s",
                definition.begrip,
                exc,
            )
            record.wettelijke_basis = "[]"

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
                    record.imported_from = str(
                        definition.metadata["imported_from"]  # type: ignore[attr-defined]
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.debug(
                        "Kon imported_from niet casten naar string voor '%s': %s",
                        definition.begrip,
                        exc,
                    )

        # DEF-151 + DEF-743: promptregistratie en bronbewijs in dezelfde
        # generatieregistratie (helper; geen gedragswijziging). DEF-751: de
        # categoriekeuze voegt de persistentielaag toe (`create_definitie`).
        record.generation_prompt_data = self._generatieregistratie_voor_record(
            definition.metadata or {}, definition.begrip, record
        )

        # Voeg toelichting toe aan definitie tekst indien aanwezig
        if definition.toelichting:
            record.definitie = (
                f"{definition.definitie}{TOELICHTING_SCHEIDING} "
                f"{definition.toelichting}"
            )

        return record

    @staticmethod
    def _promptregistratie(metadata: dict[str, Any], begrip: str) -> dict[str, Any]:
        """De DEF-151-promptregistratie uit de metadata, of {} (ook bij fout)."""
        # DEF-151: Store generation prompt data as JSON
        # Extract relevant metadata for prompt storage
        prompt_data: dict[str, Any] = {}
        if "prompt_text" in metadata or "prompt_template" in metadata:
            try:
                prompt_data = {
                    "prompt": metadata.get("prompt_text")
                    or metadata.get("prompt_template"),
                    "model": metadata.get("model", "unknown"),
                    "temperature": metadata.get("temperature"),
                    "tokens_used": metadata.get("tokens_used", 0),
                    "tokens_prompt": metadata.get("tokens_prompt"),
                    "tokens_completion": metadata.get("tokens_completion"),
                    "created_at": metadata.get("generated_at")
                    or metadata.get("generation_time"),
                    # DEF-622 (besluit tekstvergelijking): de echte
                    # tekststadia per record, in de bestaande
                    # generatieregistratie (geen schemawijziging).
                    "definitie_kern_geextraheerd": metadata.get(
                        "definitie_kern_geextraheerd"
                    ),
                    "definitie_eindtekst": metadata.get("definitie_eindtekst"),
                    "tekst_na_generatie_aangepast": metadata.get(
                        "tekst_na_generatie_aangepast"
                    ),
                    # DEF-751 stap 2: het gebruikersantwoord op een gemeld
                    # betekenisconflict, herleidbaar als bedoeling (geen
                    # bronfeit, geen oordeel); alleen als het er was.
                    "betekenisverduidelijking": metadata.get(
                        "betekenisverduidelijking"
                    ),
                }
                # Only store non-None values
                prompt_data = {k: v for k, v in prompt_data.items() if v is not None}
                # Serialisatie als proef: een niet-serialiseerbare
                # promptregistratie blijft (zoals voorheen) een warning.
                json.dumps(prompt_data, ensure_ascii=False)
            except Exception as exc:
                logger.warning(
                    "Could not serialize generation prompt data for '%s': %s",
                    begrip,
                    exc,
                )
                prompt_data = {}
        return prompt_data

    def _generatieregistratie_voor_record(
        self, metadata: dict[str, Any], begrip: str, record: DefinitieRecord
    ) -> str | None:
        """De `generation_prompt_data`-JSON voor een nieuw record, of None.

        DEF-743: het bronbewijs (bronset, kwitantie, AI-beoordeling,
        kandidaatstadia, peildatum) in dezelfde generatieregistratie —
        ook zónder promptregistratie. Anders dan de promptdata is dit
        bewijs: een serialisatiefout laat de opslag falen (ValueError →
        RepositoryError), er wordt nooit stil bronbewijs weggelaten.

        DEF-751 B2: de categoriekeuze zelf wordt hier niet gebouwd — dat doet
        de persistentielaag op basis van `categoriekeuze` (zie `save`), zodat
        een event in aangeleverde metadata/JSON nooit als keuze meereist.
        """
        prompt_data = self._promptregistratie(metadata, begrip)
        bewijsinvoer = _bewijsinvoer_uit_metadata(metadata)
        if bewijsinvoer is not None:
            prompt_data[SOURCE_EVIDENCE_KEY] = bouw_bronbewijs(
                begrip=record.begrip,
                definitie_tekst=splits_definitietekst(record.definitie or "")[0],
                contexten=record.get_contextlijsten(),
                sources=bewijsinvoer["sources"],
                source_receipt=bewijsinvoer["source_receipt"],
                source_assessment=bewijsinvoer["source_assessment"],
                peildatum=bewijsinvoer["peildatum"],
                origin="generation",
                version_number=record.version_number,
                recorded_by=record.created_by,
                generation_id=bewijsinvoer["generation_id"],
                generated_at=bewijsinvoer["generated_at"],
                tekststadia=bewijsinvoer["tekststadia"],
            )
            prompt_data[SOURCE_EVIDENCE_HISTORY_KEY] = []
            prompt_data[SOURCE_PROPOSALS_KEY] = []
        if not prompt_data:
            return None
        return serialiseer_generatieregistratie(prompt_data)

    @staticmethod
    def _categoriekeuze_voor_nieuw_record(
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """De herkomst van de categorie voor `create_definitie`, of None.

        De invoer (`category_choice_input`) is onbevestigd: alleen herkomst
        manual/model + reasoning/scores worden gelezen (`lees_keuze_invoer`),
        nooit een actor. Zonder invoer géén event (herkomst onbekend, of
        `absent` bij een label-loos record; niets verzonnen). Het event zelf
        bouwt de persistentielaag.
        """
        invoer = lees_keuze_invoer(metadata.get(CATEGORY_CHOICE_INPUT_KEY))
        if invoer is None:
            return None
        keuze: dict[str, Any] = dict(invoer)
        generation_id = metadata.get("generation_id")
        if generation_id:
            keuze["generation_id"] = str(generation_id)
        return keuze

    def get_generation_prompt_data(self, definition_id: int) -> dict | None:
        """
        Get generation prompt data for a definition.

        Args:
            definition_id: ID of the definition

        Returns:
            Dictionary with prompt data or None if not available
        """
        import json as _json

        try:
            # Get record from legacy repository
            with self.legacy_repo._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT generation_prompt_data FROM definities WHERE id = ?",
                    (definition_id,),
                )
                row = cursor.fetchone()

                if row and row[0]:
                    return cast(dict[Any, Any], _json.loads(row[0]))
                return None
        except Exception as exc:
            logger.debug(
                f"Could not load generation prompt data for ID {definition_id}: {exc}"
            )
            return None

    def van_record(self, record: DefinitieRecord) -> Definition:
        """De canonieke recordadapter: één al gelezen record naar Definition.

        Voor aanroepers die het record zelf al hebben gelezen en dezelfde
        snapshot in beide vormen nodig hebben (DEF-622, K3: getoonde selectie
        en validatie uit dezelfde lezing).
        """
        return self._record_to_definition(record)

    def _record_to_definition(self, record: DefinitieRecord) -> Definition:
        """Converteer DefinitieRecord naar Definition."""
        # Split definitie en toelichting indien aanwezig — dezelfde
        # tekstbasis als het CON-01-contract op het record (DEF-622, K4).
        definitie_text, toelichting = splits_definitietekst(record.definitie or "")

        import json as _json

        # Parse context JSON arrays (safe fallbacks)
        def _parse_list(val: Any) -> list[Any]:
            try:
                if not val:
                    return []
                return list(_json.loads(val)) if isinstance(val, str) else list(val)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning("JSON list parsing failed for value %r: %s", val, e)
                return []

        definition = Definition(
            id=record.id,
            begrip=record.begrip,
            definitie=definitie_text,
            toelichting=toelichting,
            toelichting_proces=getattr(record, "toelichting_proces", None),
            bron=record.source_reference,
            organisatorische_context=_parse_list(record.organisatorische_context),
            juridische_context=_parse_list(record.juridische_context),
            wettelijke_basis=record.get_wettelijke_basis_list(),
            categorie=record.categorie,
            ufo_categorie=getattr(record, "ufo_categorie", None),
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

        # DEF-439: metadata is dataclass-typed dict|None; __post_init__ zet het
        # naar {} maar mypy ziet dat niet — narrow expliciet vóór indexed writes.
        if definition.metadata is None:
            definition.metadata = {}

        # Parse eventuele JSON velden
        if record.validation_issues:
            with suppress(json.JSONDecodeError, ValueError):
                definition.metadata["validation_issues"] = json.loads(
                    record.validation_issues
                )
            # DEF-622 (B-07): de vastgelegde CON-01-expertbeoordeling reist
            # als eigen sleutel mee, zodat de validatie haar kan toepassen en
            # de UI haar kan tonen. Zij bindt via haar vingerafdruk aan de
            # exacte tekst/context/term; een gewijzigd concept hergebruikt
            # haar dus niet.
            review = record.get_context_review()
            if review is not None:
                definition.metadata["context_review"] = review

        # DEF-151: Restore generation prompt data from database
        if record.generation_prompt_data:
            with suppress(json.JSONDecodeError, ValueError):
                definition.metadata["generation_prompt_data"] = json.loads(
                    record.generation_prompt_data
                )

        # DEF-743: het opgeslagen bronbewijs onder exact de sleutels van het
        # kerncontract. `provenance_sources` (canoniek) en `sources` (alias)
        # krijgen elk een eigen deepcopy van dezelfde opgeslagen lijst; de
        # deskundigenuitzondering is expliciet None wanneer zij ontbreekt.
        # Zonder bewijs ontbreken de bronsleutels: niets wordt verzonnen, en
        # de statusvelden maken "alleen korte verwijzing" of "afwezig" expliciet.
        self._herstel_bronbewijs(record, definition.metadata)

        # DEF-751 B2: de categoriekeuze (event, afgeleide status, historie)
        # onder eigen leessleutels — nooit onder de invoersleutel, zodat
        # openen + opslaan geen tweede event maakt.
        definition.metadata["category_choice"] = record.get_category_choice()
        definition.metadata["category_choice_status"] = (
            record.get_category_choice_status()
        )
        definition.metadata["category_choice_history"] = (
            record.get_category_choice_history()
        )

        # DEF-156: Load voorbeelden from database and populate metadata
        # This ensures voorbeelden persist when loading definitions in Bewerk tab
        try:
            # DEF-439: record.id is int|None; skip voorbeelden bij ontbrekend id.
            voorbeelden_db = (
                self.get_voorbeelden_by_type(record.id) if record.id is not None else {}
            )
            if voorbeelden_db and any(voorbeelden_db.values()):
                # Canonicalize DB keys to UI-expected format
                # DB uses: sentence, practical, counter, synonyms, antonyms, explanation
                # UI expects: voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen, toelichting
                from utils.example_formatters import canonicalize_examples

                canonicalized = canonicalize_examples(voorbeelden_db)
                definition.metadata["voorbeelden"] = canonicalized
                logger.debug(
                    f"Loaded voorbeelden for definitie {record.id}: "
                    f"{sum(len(v) if isinstance(v, list) else 0 for v in canonicalized.values())} items"
                )
        except Exception as e:
            # Don't fail if voorbeelden loading fails - just log warning
            logger.warning(f"Could not load voorbeelden for definitie {record.id}: {e}")

        return definition

    @staticmethod
    def _herstel_bronbewijs(record: DefinitieRecord, metadata: dict[str, Any]) -> None:
        """Zet het opgeslagen bronbewijs terug in `Definition.metadata` (DEF-743)."""
        metadata["source_reference"] = record.source_reference
        metadata["source_evidence_status"] = record.get_source_evidence_status()
        metadata["source_review"] = record.get_source_review()
        metadata["source_review_status"] = record.get_source_review_status()
        metadata["source_evidence_history"] = record.get_source_evidence_history()
        metadata["source_review_history"] = record.get_source_review_history()
        metadata["source_proposals"] = record.get_source_proposals()
        bewijs = record.get_source_evidence()
        if bewijs is None:
            return
        # Reviewbevinding 2: de expliciete generatie-id (kern C) komt terug
        # zodat een bewerking dezelfde generatie blijft; nooit verzonnen.
        if isinstance(bewijs.get("generation_id"), str) and bewijs["generation_id"]:
            metadata["generation_id"] = bewijs["generation_id"]
        bronnen = bewijs.get("sources") or []
        metadata["sources"] = deepcopy(bronnen)
        metadata["provenance_sources"] = deepcopy(bronnen)
        metadata["source_receipt"] = deepcopy(bewijs.get("source_receipt"))
        metadata["source_assessment"] = deepcopy(bewijs.get("source_assessment"))
        metadata["peildatum"] = bewijs.get("peildatum")
        metadata["source_evidence"] = bewijs

    # ===== Bronbewijs, CON-02-uitzondering en voorstellen (DEF-743) =====
    def set_source_review(
        self,
        definitie_id: int,
        review: dict[str, Any] | None,
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> bool:
        """Leg de CON-02-deskundigenuitzondering vast (freeze punt 1, platte vorm).

        ``expected_version`` is de beoordeelde recordversie (optimistic lock);
        de vingerafdruk wordt over het opgeslagen record herberekend en de
        inhoudelijke eisen komen van de kernhelper `valideer_bronreview`.
        """
        return self.legacy_repo.set_source_review(
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
        return self.legacy_repo.set_source_assessment(
            definitie_id, assessment, updated_by, expected_version=expected_version
        )

    def vul_bronmetadata_aan(
        self,
        definitie_id: int,
        doc_id: str,
        metadata: dict[str, Any],
        updated_by: str | None = None,
        *,
        expected_version: int,
    ) -> Bronmetadatatoepassing:
        """Zet opgegeven bronmetadata op de documentpassages van het bewijs (DEF-808)."""
        return self.legacy_repo.vul_bronmetadata_aan(
            definitie_id,
            doc_id,
            metadata,
            updated_by,
            expected_version=expected_version,
        )

    def reserve_source_proposal(
        self, definitie_id: int, *, updated_by: str, expected_version: int
    ) -> Voorstelreservering:
        """Reserveer de ene voorstelpoging van deze generatie (vóór de modelaanroep)."""
        return self.legacy_repo.reserve_source_proposal(
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
        """Leg de uitkomst (`proposed`/`blocked`/`error`) van de reservering vast."""
        return self.legacy_repo.record_source_proposal_outcome(
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
        """Pas een voorgesteld voorstel atomair toe met het volledige validatieresultaat."""
        return self.legacy_repo.apply_source_proposal(
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
        """Sluit een voorgesteld voorstel af (`rejected`/`superseded`)."""
        return self.legacy_repo.set_source_proposal_status(
            definitie_id,
            proposal_id,
            status,
            updated_by,
            expected_version=expected_version,
            note=note,
        )

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager voor database connecties."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_record(
        self, row: sqlite3.Row, description: Sequence[Any]
    ) -> DefinitieRecord:
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
        stats: dict[str, Any] = self._stats.copy()

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
                cursor.execute("""
                    SELECT status, COUNT(*)
                    FROM definities
                    GROUP BY status
                """)
                stats["by_status"] = {row[0]: row[1] for row in cursor.fetchall()}

        except sqlite3.Error as exc:
            logger.warning("Kon repository statistieken niet ophalen: %s", exc)
        except Exception:  # pragma: no cover - unexpected failure
            logger.exception("Onverwachte fout bij ophalen repositorystatistieken")

        return stats

    def reset_stats(self) -> None:
        """Reset de statistieken."""
        self._stats = {
            "total_saves": 0,
            "total_searches": 0,
            "total_updates": 0,
            "total_deletes": 0,
        }

    # ===== Contextcontract en vaststelinvariant (DEF-622) =====
    def find_leidende_definitie(
        self,
        begrip: str,
        organisatorische_context: Any,
        juridische_context: Any = "",
        wettelijke_basis: Any = None,
        *,
        eigen_id: int | None = None,
    ) -> DefinitieRecord | None:
        """Het vastgestelde, leidende record met dezelfde identiteit.

        Identiteit = begrip + volledige genormaliseerde context, ongeacht
        categorie (B-03/B-10). `eigen_id` telt niet mee. Dezelfde signatuur
        als de DB-facade, zodat aanroepers die (DEF-439) de DB-laag
        annoteren maar runtime deze laag krijgen, één aanroep hebben.
        """
        return self.legacy_repo.find_leidende_definitie(
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
        """Leg de CON-01-expertbeoordeling van de naamfunctie vast (B-07).

        ``expected_version`` is de beoordeelde recordversie (optimistic lock).
        """
        return self.legacy_repo.set_context_review(
            definitie_id, review, updated_by, expected_version=expected_version
        )

    # ===== Legacy compatibility surface for workflow/UI =====
    def get_definitie(self, definitie_id: int) -> DefinitieRecord | None:
        """Pass-through naar legacy repository (compat met bestaande callers)."""
        try:
            return self.legacy_repo.get_definitie(definitie_id)
        except Exception as e:
            if self.in_transaction():
                # DEF-482: binnen een transactie zou `None` een databasefout
                # als "niet gevonden"/versieconflict maskeren.
                raise
            logger.warning(f"get_definitie failed for ID {definitie_id}: {e}")
            return None

    def update_definitie(
        self, definitie_id: int, updates: dict[str, Any], updated_by: str | None = None
    ) -> bool:
        """Pass-through update voor compatibiliteit."""
        try:
            return cast(
                bool,
                self.legacy_repo.update_definitie(definitie_id, updates, updated_by),
            )
        except Exception as e:
            if self.in_transaction():
                raise  # DEF-482: zie change_status
            logger.error(f"update_definitie failed for ID {definitie_id}: {e}")
            return False

    def change_status(
        self,
        definitie_id: int,
        new_status: "DefinitieStatus",
        changed_by: str | None = None,
        notes: str | None = None,
        *,
        ketenpartners: list[str] | None = None,
        ufo_categorie: str | Unset | None = UNSET,
        expected_version: int | None = None,
    ) -> bool:
        """Pass-through statuswijziging voor compatibiliteit met workflowservice."""
        try:
            return cast(
                bool,
                self.legacy_repo.change_status(
                    definitie_id,
                    new_status,
                    changed_by,
                    notes,
                    ketenpartners=ketenpartners,
                    ufo_categorie=ufo_categorie,
                    expected_version=expected_version,
                ),
            )
        except Exception as e:
            if self.in_transaction():
                # DEF-482: binnen een lopende transactie maskeert `False` een
                # deelresultaat (de aanroeper zou zijn eigen onbevestigde write
                # kunnen herlezen en er een versieconflict uit afleiden).
                raise
            logger.error(
                f"change_status failed for ID {definitie_id} to {new_status}: {e}"
            )
            return False

    # ===== Transactiegrens (DEF-482) =====
    @contextmanager
    def transaction(self, timeout: float = 30.0) -> Iterator[sqlite3.Connection]:
        """Servicegrens rond de thread-local DB-transactie (nesting, één COMMIT
        en rollback volgen het DB-contract). Ruwe SQLite-fouten, ook uit een
        latere COMMIT, worden typed met vaste melding; getypeerde fouten en
        programmeerfouten lopen ongewijzigd door (DEF-469)."""
        try:
            with self.legacy_repo.transaction(timeout) as conn:
                yield conn
        except (DefinitionServiceError, sqlite3.ProgrammingError):
            raise
        except sqlite3.DatabaseError as e:
            # Geen exceptiontekst/traceback: die kan vrije persoonsdata bevatten.
            code = getattr(e, "sqlite_errorcode", None)
            code = code if isinstance(code, int) else None
            origin = e.__traceback__
            while origin is not None and origin.tb_next is not None:
                origin = origin.tb_next
            diagnose = {
                "operation": "transaction",
                "error_type": type(e).__name__,
                "sqlite_errorcode": code,
                "origin": origin.tb_frame.f_code.co_name if origin else None,
            }
            logger.error(
                "Database transaction failed: %s (SQLite code: %s; origin: %s)",
                diagnose["error_type"],
                code,
                diagnose["origin"],
                extra=diagnose,
            )
            if isinstance(e, sqlite3.OperationalError):
                raise DatabaseConnectionError(self.db_path, MELDING_DATABASEFOUT) from e
            if isinstance(e, sqlite3.IntegrityError):
                raise DatabaseConstraintError(
                    "unknown", "", MELDING_DATABASEFOUT
                ) from e
            raise RepositoryError("transaction", message=MELDING_DATABASEFOUT) from e

    def in_transaction(self) -> bool:
        """True als de huidige thread al een transactie open heeft."""
        return self.legacy_repo.in_transaction()

    # ===== Helpers =====
    def _definition_to_updates(self, definition: Definition) -> dict[str, Any]:
        """Converteer Definition naar updates-dict voor legacy update_definitie()."""
        import json as _json

        updates: dict[str, Any] = {}
        if definition.begrip is not None:
            updates["begrip"] = definition.begrip
        if definition.definitie is not None:
            updates["definitie"] = definition.definitie
        if definition.categorie is not None:
            updates["categorie"] = definition.categorie
        # UFO-categorie (inclusief None om te kunnen leegmaken)
        updates["ufo_categorie"] = getattr(definition, "ufo_categorie", None)
        # Procesmatige velden
        updates["toelichting_proces"] = getattr(definition, "toelichting_proces", None)
        # Contextvelden (JSON strings). DEF-672: dezelfde canonieke vorm als bij
        # `save()`. Deze tak omzeilde de normalisatie volledig, waardoor een
        # bijgewerkte definitie ongesorteerd, ongetrimd en met duplicaten in de
        # database belandde — en dus niet meer als duplicaat werd herkend.
        updates["organisatorische_context"] = _json.dumps(
            canoniseer_contextlijst(definition.organisatorische_context),
            ensure_ascii=False,
        )
        updates["juridische_context"] = _json.dumps(
            canoniseer_contextlijst(definition.juridische_context),
            ensure_ascii=False,
        )
        try:
            # De `None`-tak is in de praktijk onbereikbaar: `Definition.__post_init__`
            # zet `wettelijke_basis=None` om naar `[]`, wat `test_none_wettelijke_basis
            # _becomes_empty_array` ook vastlegt. Hij blijft staan voor een object dat
            # het veld ná constructie op None zet; dan is `NULL` de juiste kolomwaarde.
            updates["wettelijke_basis"] = (
                None
                if definition.wettelijke_basis is None
                else _json.dumps(
                    canoniseer_contextlijst(definition.wettelijke_basis),
                    ensure_ascii=False,
                )
            )
        except Exception as exc:
            logger.warning(
                "Kon wettelijke_basis serialiseren voor update van '%s': %s",
                definition.begrip,
                exc,
            )
            updates["wettelijke_basis"] = None
        # Embed toelichting in definitietekst indien aanwezig (consistent met create)
        try:
            if definition.toelichting and str(definition.toelichting).strip():
                base = updates.get("definitie", definition.definitie or "")
                if base is None:
                    base = ""
                # Voorkom dubbele embed: _record_to_definition levert definitie zonder 'Toelichting:'
                # dus we kunnen veilig toevoegen
                updates["definitie"] = (
                    f"{base}{TOELICHTING_SCHEIDING} "
                    f"{str(definition.toelichting).strip()}"
                )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.debug(
                "Kon toelichting embedden voor '%s': %s",
                definition.begrip,
                exc,
            )

        # Extra velden
        if definition.metadata and "status" in definition.metadata:
            updates["status"] = definition.metadata["status"]

        # DEF-743: nieuwe bronbewijs-invoer reist als structurele sleutel mee;
        # de DB-laag voegt haar ónder de schrijflock samen met het opgeslagen
        # bewijs (gelijk = geen wijziging; anders historie + nieuw). Sleutel
        # afwezig = bewijs onaangeraakt. Conflicterende aliassen: ValueError
        # (→ RepositoryError), niets geschreven.
        _voeg_bewijsinvoer_toe(updates, definition.metadata)
        # DEF-751 B2 (reviewbevinding 3): de versie die de aanroeper vóór
        # zich had (`metadata["version_number"]`, gezet bij laden en door de
        # editor) reist mee tot de uiteindelijke UPDATE als optimistic lock:
        # een tussentijdse wijziging is dan een conflict, geen terugschrijven
        # van verouderde velden. Een generiek metadata-blok kan géén
        # categoriekeuze meedragen; dat kan alleen `record_category_choice`.
        versie = (definition.metadata or {}).get("version_number")
        if isinstance(versie, int) and not isinstance(versie, bool):
            updates["version_number"] = versie
        return updates
