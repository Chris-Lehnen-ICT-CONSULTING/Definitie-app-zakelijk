"""Synonym registry synchronisatie service."""

import logging

from database.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SynonymSyncService:
    """Sync synoniemen naar de synonym registry (Architecture v3.1, PHASE 3.3)."""

    def __init__(self, db: DatabaseConnection, get_registry_fn=None):
        self._db = db
        self._get_registry_fn = get_registry_fn

    def sync_synonyms_to_registry(
        self,
        definitie_id: int,
        synoniemen: list[str],
        edited_by: str,
        get_definitie_fn=None,
    ):
        """Sync manual synoniemen naar registry (scoped to definitie_id).

        Args:
            definitie_id: ID van de definitie
            synoniemen: Lijst van synoniem termen
            edited_by: Wie de synoniemen heeft bewerkt
            get_definitie_fn: Callable om definitie op te halen (injected vanuit facade)
        """
        definitie = get_definitie_fn(definitie_id)
        if not definitie:
            logger.warning(f"Definitie {definitie_id} niet gevonden - sync skipped")
            return

        try:
            if self._get_registry_fn:
                registry = self._get_registry_fn()
            else:
                # Lazy fallback voor backward compat
                from src.services.container import get_container

                registry = get_container().synonym_registry()
        except Exception as e:
            logger.error(f"Failed to get synonym registry: {e}")
            raise

        # Input validation
        input_terms = set()
        skipped_terms = []
        validated_synonyms = []

        for syn in synoniemen:
            syn_normalized = syn.strip().lower()

            if not syn_normalized:
                skipped_terms.append(f"empty: '{syn}'")
                continue

            if len(syn_normalized) > 255:
                skipped_terms.append(
                    f"too long ({len(syn_normalized)} chars): '{syn_normalized[:50]}...'"
                )
                continue

            if syn_normalized in input_terms:
                skipped_terms.append(f"duplicate: '{syn}'")
                continue

            if not syn_normalized.replace(" ", "").replace("-", "").isalnum():
                logger.debug(f"Synonym contains special characters: '{syn_normalized}'")

            input_terms.add(syn_normalized)
            validated_synonyms.append(syn_normalized)

        if skipped_terms:
            logger.warning(
                f"Skipped {len(skipped_terms)} invalid synonyms for definitie {definitie_id}: "
                f"{', '.join(skipped_terms[:5])}"
            )

        if not validated_synonyms:
            logger.info(f"No valid synonyms to sync for definitie {definitie_id}")
            return

        try:
            group = registry.get_or_create_group(
                canonical_term=definitie.begrip, created_by=edited_by
            )

            existing = registry.get_group_members(
                group_id=group.id,
                filters={"definitie_id": definitie_id, "source": "manual"},
            )

            existing_terms = {m.term: m for m in existing}

            added_count = 0
            reactivated_count = 0
            deprecated_count = 0

            for syn_normalized in validated_synonyms:
                if syn_normalized in existing_terms:
                    member = existing_terms[syn_normalized]
                    if member.status == "deprecated":
                        registry.update_member_status(
                            member_id=member.id,
                            new_status="active",
                            reviewed_by=edited_by,
                        )
                        reactivated_count += 1
                        logger.debug(
                            f"Reactivated synonym '{syn_normalized}' for definitie {definitie_id}"
                        )
                else:
                    all_members_for_term = registry.get_group_members(
                        group_id=group.id,
                        filters={"source": "manual"},
                    )
                    term_exists_in_group = any(
                        m.term == syn_normalized for m in all_members_for_term
                    )

                    if term_exists_in_group:
                        logger.warning(
                            f"Synonym '{syn_normalized}' already exists in group {group.id}, "
                            f"skipping duplicate add for definitie {definitie_id}"
                        )
                        continue

                    try:
                        registry.add_group_member(
                            group_id=group.id,
                            term=syn_normalized,
                            weight=1.0,
                            status="active",
                            source="manual",
                            definitie_id=definitie_id,
                            created_by=edited_by,
                        )
                        added_count += 1
                        logger.debug(
                            f"Added manual synonym '{syn_normalized}' for definitie {definitie_id}"
                        )
                    except ValueError as e:
                        if "bestaat al" in str(e):
                            logger.warning(
                                f"Duplicate synonym '{syn_normalized}' detected during add: {e}"
                            )
                        else:
                            raise

            for term, member in existing_terms.items():
                if term not in input_terms and member.status == "active":
                    registry.update_member_status(
                        member_id=member.id,
                        new_status="deprecated",
                        reviewed_by=edited_by,
                    )
                    deprecated_count += 1
                    logger.debug(
                        f"Deprecated synonym '{term}' for definitie {definitie_id}"
                    )

            logger.info(
                f"Synced {len(validated_synonyms)} manual synonyms for definitie {definitie_id} "
                f"(added: {added_count}, reactivated: {reactivated_count}, deprecated: {deprecated_count})"
            )

        except Exception as e:
            logger.error(f"Synonym sync failed for definitie {definitie_id}: {e}")
            raise
