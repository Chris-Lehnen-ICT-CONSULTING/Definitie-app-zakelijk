"""Voorbeelden management repository."""

import logging
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from database.db_connection import DatabaseConnection
from database.models import VoorbeeldenRecord
from database.synonym_sync import SynonymSyncService
from models.voorbeelden_validation import validate_save_voorbeelden_input

logger = logging.getLogger(__name__)


class VoorbeeldenRepository:
    """Repository voor voorbeelden (zinnen, praktijk, tegen, synoniemen, etc.)."""

    def __init__(self, db: DatabaseConnection, synonym_sync: SynonymSyncService):
        self._db = db
        self._synonym_sync = synonym_sync

    def save_voorbeelden(
        self,
        definitie_id: int,
        voorbeelden_dict: dict[str, list[str]],
        generation_model: str | None = None,
        generation_params: dict[str, Any] | None = None,
        gegenereerd_door: str = "system",
        voorkeursterm: str | None = None,
        get_definitie_fn=None,
    ) -> list[int]:
        """Sla voorbeelden op voor een definitie.

        Args:
            get_definitie_fn: Callable om definitie op te halen (voor synonym sync)
        """
        logger.info(f"Saving voorbeelden voor definitie {definitie_id}")

        # DEF-74: Validate input using Pydantic schema
        try:
            validated = validate_save_voorbeelden_input(
                definitie_id=definitie_id,
                voorbeelden_dict=voorbeelden_dict,
                generation_model=generation_model,
                generation_params=generation_params,
                gegenereerd_door=gegenereerd_door,
                voorkeursterm=voorkeursterm,
            )
            voorbeelden_dict = validated.voorbeelden_dict
            definitie_id = validated.definitie_id
            gegenereerd_door = validated.gegenereerd_door
        except ValidationError as e:
            logger.error(
                f"❌ Validation failed for definitie {definitie_id}: {e}",
                exc_info=True,
                extra={
                    "definitie_id": definitie_id,
                    "error_details": e.errors(),
                    "error_count": len(e.errors()),
                },
            )
            raise

        # Safety guard
        try:
            total_new = 0
            for _k, _v in (voorbeelden_dict or {}).items():
                if isinstance(_v, list):
                    total_new += len([x for x in _v if str(x).strip()])
            if total_new == 0:
                logger.info(
                    "No new examples provided for definitie %s — skipping overwrite",
                    definitie_id,
                )
                return []
        except Exception as e:
            logger.debug(
                f"Voorbeelden structuur parsing gefaald voor definitie {definitie_id}: {e}"
            )

        with self._db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                saved_ids = []

                cursor.execute(
                    """
                    UPDATE definitie_voorbeelden
                    SET actief = FALSE, bijgewerkt_op = CURRENT_TIMESTAMP
                    WHERE definitie_id = ? AND actief = TRUE
                """,
                    (definitie_id,),
                )

                def _normalize_type(tp: str) -> str:
                    t = (tp or "").strip().lower()
                    mapping = {
                        "voorbeeldzinnen": "sentence",
                        "zinnen": "sentence",
                        "voorbeeldzin": "sentence",
                        "sentences": "sentence",
                        "sentence": "sentence",
                        "example_sentences": "sentence",
                        "praktijkvoorbeelden": "practical",
                        "praktijk": "practical",
                        "praktijkvoorbeeld": "practical",
                        "practical_examples": "practical",
                        "practical": "practical",
                        "tegenvoorbeelden": "counter",
                        "tegen": "counter",
                        "counterexamples": "counter",
                        "counter": "counter",
                        "synoniemen": "synonyms",
                        "synonym": "synonyms",
                        "synonyms": "synonyms",
                        "antoniemen": "antonyms",
                        "antonym": "antonyms",
                        "antonyms": "antonyms",
                        "toelichting": "explanation",
                        "uitleg": "explanation",
                        "notes": "explanation",
                        "comment": "explanation",
                        "explanation": "explanation",
                    }
                    return mapping.get(t, t)

                for voorbeeld_type, examples in voorbeelden_dict.items():
                    norm_type = _normalize_type(voorbeeld_type)
                    if not examples:
                        continue

                    for idx, voorbeeld_tekst in enumerate(examples, 1):
                        if not voorbeeld_tekst.strip():
                            continue

                        record = VoorbeeldenRecord(
                            definitie_id=definitie_id,
                            voorbeeld_type=norm_type,
                            voorbeeld_tekst=voorbeeld_tekst.strip(),
                            voorbeeld_volgorde=idx,
                            gegenereerd_door=gegenereerd_door,
                            generation_model=generation_model,
                            actief=True,
                        )

                        if generation_params:
                            record.set_generation_parameters(generation_params)

                        cursor.execute(
                            """
                            SELECT id FROM definitie_voorbeelden
                            WHERE definitie_id = ? AND voorbeeld_type = ? AND voorbeeld_volgorde = ?
                        """,
                            (
                                record.definitie_id,
                                record.voorbeeld_type,
                                record.voorbeeld_volgorde,
                            ),
                        )

                        existing = cursor.fetchone()
                        if existing:
                            cursor.execute(
                                """
                                UPDATE definitie_voorbeelden
                                SET voorbeeld_tekst = ?, actief = TRUE,
                                    gegenereerd_door = ?, generation_model = ?,
                                    generation_parameters = ?,
                                    bijgewerkt_op = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """,
                                (
                                    record.voorbeeld_tekst,
                                    record.gegenereerd_door,
                                    record.generation_model,
                                    record.generation_parameters,
                                    existing[0],
                                ),
                            )
                            saved_ids.append(existing[0])
                        else:
                            cursor.execute(
                                """
                                INSERT INTO definitie_voorbeelden (
                                    definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                                    gegenereerd_door, generation_model, generation_parameters, actief,
                                    aangemaakt_op, bijgewerkt_op
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """,
                                (
                                    record.definitie_id,
                                    record.voorbeeld_type,
                                    record.voorbeeld_tekst,
                                    record.voorbeeld_volgorde,
                                    record.gegenereerd_door,
                                    record.generation_model,
                                    record.generation_parameters,
                                    record.actief,
                                ),
                            )
                            saved_ids.append(cursor.lastrowid)

                        logger.debug(
                            f"Saved {voorbeeld_type} voorbeeld {idx}: {voorbeeld_tekst[:50]}..."
                        )

                conn.commit()

                # Voorkeursterm persistency
                try:
                    if voorkeursterm:
                        cursor.execute(
                            "UPDATE definities SET voorkeursterm = ? WHERE id = ?",
                            (voorkeursterm.strip(), definitie_id),
                        )
                        conn.commit()
                    else:
                        cursor.execute(
                            "UPDATE definities SET voorkeursterm = NULL WHERE id = ?",
                            (definitie_id,),
                        )
                        conn.commit()
                except Exception as e:
                    logger.warning(
                        f"Voorkeursterm update gefaald voor definitie {definitie_id}: {e}. "
                        f"Eerdere per-row waarde blijft behouden.",
                        extra={
                            "component": "definitie_repository",
                            "operation": "update_voorkeursterm",
                            "definitie_id": definitie_id,
                            "error_type": type(e).__name__,
                        },
                    )

                # PHASE 3.3: Sync synoniemen naar registry
                synoniemen = voorbeelden_dict.get("synoniemen", [])
                if synoniemen:
                    try:
                        self._synonym_sync.sync_synonyms_to_registry(
                            definitie_id=definitie_id,
                            synoniemen=synoniemen,
                            edited_by=gegenereerd_door,
                            get_definitie_fn=get_definitie_fn,
                        )
                    except Exception as e:
                        logger.warning(f"Synonym sync to registry failed: {e}")

                logger.info(f"Successfully saved {len(saved_ids)} voorbeelden")
                return saved_ids

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to save voorbeelden: {e}")
                raise

    def get_voorbeelden(
        self,
        definitie_id: int,
        voorbeeld_type: str | None = None,
        actief_only: bool = True,
    ) -> list[VoorbeeldenRecord]:
        """Haal voorbeelden op voor een definitie."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                       gegenereerd_door, generation_model, generation_parameters, actief,
                       beoordeeld, beoordeeling, beoordeeling_notities, beoordeeld_door,
                       beoordeeld_op, aangemaakt_op, bijgewerkt_op
                FROM definitie_voorbeelden
                WHERE definitie_id = ?
            """
            params: list[Any] = [definitie_id]

            if voorbeeld_type:
                query += " AND voorbeeld_type = ?"
                params.append(voorbeeld_type)

            if actief_only:
                query += " AND actief = TRUE"

            query += " ORDER BY voorbeeld_type, voorbeeld_volgorde"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            voorbeelden = []
            for row in rows:
                record = VoorbeeldenRecord(
                    id=row["id"],
                    definitie_id=row["definitie_id"],
                    voorbeeld_type=row["voorbeeld_type"],
                    voorbeeld_tekst=row["voorbeeld_tekst"],
                    voorbeeld_volgorde=row["voorbeeld_volgorde"],
                    is_voorkeursterm=False,
                    gegenereerd_door=row["gegenereerd_door"],
                    generation_model=row["generation_model"],
                    generation_parameters=row["generation_parameters"],
                    actief=bool(row["actief"]),
                    beoordeeld=bool(row["beoordeeld"]),
                    beoordeeling=row["beoordeeling"],
                    beoordeeling_notities=row["beoordeeling_notities"],
                    beoordeeld_door=row["beoordeeld_door"],
                    beoordeeld_op=(
                        datetime.fromisoformat(row["beoordeeld_op"])
                        if row["beoordeeld_op"]
                        else None
                    ),
                    aangemaakt_op=(
                        datetime.fromisoformat(row["aangemaakt_op"])
                        if row["aangemaakt_op"]
                        else None
                    ),
                    bijgewerkt_op=(
                        datetime.fromisoformat(row["bijgewerkt_op"])
                        if row["bijgewerkt_op"]
                        else None
                    ),
                )
                voorbeelden.append(record)

            return voorbeelden

    def get_voorbeelden_by_type(self, definitie_id: int) -> dict[str, list[str]]:
        """Haal voorbeelden op gegroepeerd per type."""
        voorbeelden_records = self.get_voorbeelden(definitie_id)

        voorbeelden_dict: dict[str, list[str]] = {}
        for record in voorbeelden_records:
            if record.voorbeeld_type not in voorbeelden_dict:
                voorbeelden_dict[record.voorbeeld_type] = []
            voorbeelden_dict[record.voorbeeld_type].append(record.voorbeeld_tekst)

        return voorbeelden_dict

    def get_voorkeursterm(self, definitie_id: int) -> str | None:
        """Haal de voorkeursterm op voor een definitie."""
        with self._db.get_connection() as conn:
            try:
                cur = conn.execute(
                    "SELECT voorkeursterm FROM definities WHERE id = ?",
                    (definitie_id,),
                )
                row = cur.fetchone()
                if row:
                    vt = row[0]
                    if vt and str(vt).strip():
                        return str(vt)
            except Exception as e:
                logger.warning(
                    f"Voorkeursterm ophalen gefaald voor definitie {definitie_id}: {e}"
                )

        return None

    def beoordeel_voorbeeld(
        self,
        voorbeeld_id: int,
        beoordeeling: str,
        beoordeeling_notities: str = "",
        beoordeeld_door: str = "user",
    ) -> bool:
        """Beoordeel een voorbeeld."""
        if beoordeeling not in ["goed", "matig", "slecht"]:
            msg = "Beoordeeling moet 'goed', 'matig' of 'slecht' zijn"
            raise ValueError(msg)

        with self._db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE definitie_voorbeelden
                    SET beoordeeld = TRUE, beoordeeling = ?, beoordeeling_notities = ?,
                        beoordeeld_door = ?, beoordeeld_op = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        beoordeeling,
                        beoordeeling_notities,
                        beoordeeld_door,
                        voorbeeld_id,
                    ),
                )

                conn.commit()

                if cursor.rowcount > 0:
                    logger.info(
                        f"Voorbeeld {voorbeeld_id} beoordeeld als '{beoordeeling}'"
                    )
                    return True
                logger.warning(f"Voorbeeld {voorbeeld_id} niet gevonden")
                return False

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to beoordeel voorbeeld {voorbeeld_id}: {e}")
                raise

    def delete_voorbeelden(
        self, definitie_id: int, voorbeeld_type: str | None = None
    ) -> int:
        """Verwijder voorbeelden voor een definitie."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            if voorbeeld_type:
                cursor.execute(
                    """
                    DELETE FROM definitie_voorbeelden
                    WHERE definitie_id = ? AND voorbeeld_type = ?
                """,
                    (definitie_id, voorbeeld_type),
                )
            else:
                cursor.execute(
                    """
                    DELETE FROM definitie_voorbeelden
                    WHERE definitie_id = ?
                """,
                    (definitie_id,),
                )

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(
                f"Deleted {deleted_count} voorbeelden voor definitie {definitie_id}"
            )
            return deleted_count
