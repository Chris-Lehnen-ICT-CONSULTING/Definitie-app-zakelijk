"""
SynonymWorkflow - Orchestration service voor complete suggest→approve→update workflow.

Deze service coördineert het complete synonym automation proces:
1. GPT-4 Suggestions → Database (pending)
2. Human Approval → Database (approved) + YAML Config Update
3. Rejection → Database (rejected) met reason logging

Features:
- End-to-end workflow orchestration
- Transactional approve met YAML update
- Rollback on YAML update failures
- Batch approval operations
- Comprehensive error handling en logging
"""

import logging
from typing import Any

from repositories.synonym_repository import (
    SuggestionStatus,
    SynonymRepository,
    SynonymSuggestionRecord,
)
from services.synonym_automation.gpt4_suggester import GPT4SynonymSuggester
from services.synonym_automation.yaml_updater import YAMLConfigUpdater, YAMLUpdateError

logger = logging.getLogger(__name__)


class SynonymWorkflowError(Exception):
    """Error bij workflow operaties."""


class SynonymWorkflow:
    """
    Orchestration service voor complete synonym workflow.

    Coördineert GPT4SynonymSuggester, SynonymRepository en YAMLConfigUpdater
    voor een seamless suggest→approve→update proces.
    """

    def __init__(
        self,
        suggester: GPT4SynonymSuggester | None = None,
        repository: SynonymRepository | None = None,
        yaml_updater: YAMLConfigUpdater | None = None,
        db_path: str = "data/definities.db",
        yaml_path: str = "config/juridische_synoniemen.yaml",
    ):
        """
        Initialize workflow with dependencies.

        Args:
            suggester: GPT4SynonymSuggester instance (creates default if None)
            repository: SynonymRepository instance (creates default if None)
            yaml_updater: YAMLConfigUpdater instance (creates default if None)
            db_path: Database path (used if repository is None)
            yaml_path: YAML config path (used if yaml_updater is None)
        """
        self.suggester = suggester or GPT4SynonymSuggester()
        self.repository = repository or SynonymRepository(db_path=db_path)
        self.yaml_updater = yaml_updater or YAMLConfigUpdater(yaml_path=yaml_path)

        logger.info("SynonymWorkflow initialized")

    async def suggest_synonyms(
        self,
        hoofdterm: str,
        confidence_threshold: float = 0.6,
        definitie: str | None = None,
        context: list[str] | None = None,
    ) -> list[SynonymSuggestionRecord]:
        """
        Genereer GPT-4 synoniem suggesties en sla op in database.

        Workflow:
        1. Vraag GPT-4 om synoniemen voor de hoofdterm
        2. Filter op confidence_threshold
        3. Sla alle suggestions op in database (status: pending)
        4. Return lijst van opgeslagen records voor review

        Args:
            hoofdterm: De juridische term om synoniemen voor te genereren
            confidence_threshold: Minimum confidence (default: 0.6)
            definitie: Optional definitie voor context
            context: Optional extra context (bijv. ["Sv", "strafrecht"])

        Returns:
            Lijst van SynonymSuggestionRecord objecten (pending status)

        Raises:
            SynonymWorkflowError: Bij GPT-4 of database fouten
        """
        logger.info(
            f"Starting suggestion workflow for '{hoofdterm}' "
            f"(threshold: {confidence_threshold})"
        )

        try:
            # Step 1: Genereer GPT-4 suggestions
            ai_suggestions = await self.suggester.suggest_synonyms(
                term=hoofdterm,
                definitie=definitie,
                context=context,
            )

            # Step 2: Filter op confidence threshold
            filtered = [
                s for s in ai_suggestions if s.confidence >= confidence_threshold
            ]

            logger.info(
                f"Generated {len(ai_suggestions)} suggestions, "
                f"{len(filtered)} passed threshold {confidence_threshold}"
            )

            # Step 3: Sla op in database
            saved_records = []
            for suggestion in filtered:
                try:
                    suggestion_id = self.repository.save_suggestion(
                        hoofdterm=suggestion.hoofdterm,
                        synoniem=suggestion.synoniem,
                        confidence=suggestion.confidence,
                        rationale=suggestion.rationale,
                        context=suggestion.context_used,
                    )

                    # Fetch saved record
                    record = self.repository.get_suggestion(suggestion_id)
                    if record:
                        saved_records.append(record)

                    logger.debug(
                        f"Saved suggestion {suggestion_id}: '{suggestion.synoniem}' "
                        f"(confidence: {suggestion.confidence:.2f})"
                    )

                except ValueError as e:
                    # Duplicate suggestion - log and continue
                    logger.warning(
                        f"Skipping duplicate suggestion '{suggestion.synoniem}': {e}"
                    )
                    continue

            logger.info(f"Saved {len(saved_records)} new suggestions for '{hoofdterm}'")
            return saved_records

        except Exception as e:
            error_msg = f"Failed to generate suggestions for '{hoofdterm}': {e}"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg) from e

    def approve_suggestion(self, suggestion_id: int, approved_by: str) -> bool:
        """
        Approve een suggestion: update database + add to YAML config.

        Workflow (transactional met rollback):
        1. Haal suggestion op uit database
        2. Voeg synoniem toe aan YAML config
        3. Bij YAML error: rollback (geen database update)
        4. Bij success: update database status naar approved

        Args:
            suggestion_id: ID van de suggestion
            approved_by: Wie de approval uitvoert (user identifier)

        Returns:
            True als succesvol approved en toegevoegd aan YAML

        Raises:
            SynonymWorkflowError: Bij niet-bestaande suggestion
            YAMLUpdateError: Bij YAML update fouten (database niet geupdate)
        """
        logger.info(f"Approving suggestion {suggestion_id} by {approved_by}")

        # Step 1: Haal suggestion op
        suggestion = self.repository.get_suggestion(suggestion_id)
        if not suggestion:
            error_msg = f"Suggestion {suggestion_id} not found"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        # Verify status is pending
        if suggestion.status != SuggestionStatus.PENDING.value:
            error_msg = f"Suggestion {suggestion_id} is not pending (status: {suggestion.status})"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        try:
            # Step 2: Add to YAML config (this can fail - no DB update yet)
            yaml_success = self.yaml_updater.add_synonym(
                hoofdterm=suggestion.hoofdterm,
                synoniem=suggestion.synoniem,
                weight=suggestion.confidence,  # Use confidence as weight
                skip_if_exists=True,
            )

            if not yaml_success:
                logger.warning(
                    f"Synonym '{suggestion.synoniem}' already exists in YAML, "
                    f"marking as approved anyway"
                )

            # Step 3: Update database status (only if YAML succeeded)
            db_success = self.repository.approve_suggestion(
                suggestion_id=suggestion_id,
                reviewed_by=approved_by,
            )

            if db_success:
                logger.info(
                    f"Successfully approved suggestion {suggestion_id}: "
                    f"'{suggestion.hoofdterm}' → '{suggestion.synoniem}'"
                )
                return True
            # This shouldn't happen, but handle gracefully
            logger.error(
                f"Database update failed for suggestion {suggestion_id} "
                f"after YAML update"
            )
            return False

        except YAMLUpdateError as e:
            # YAML update failed - don't update database
            error_msg = (
                f"Failed to update YAML config for suggestion {suggestion_id}: {e}"
            )
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg) from e

    def reject_suggestion(
        self, suggestion_id: int, rejected_by: str, reason: str | None = None
    ) -> bool:
        """
        Reject een suggestion met optional reason.

        Args:
            suggestion_id: ID van de suggestion
            rejected_by: Wie de rejection uitvoert
            reason: Optional rejection reason (recommended)

        Returns:
            True als succesvol rejected

        Raises:
            SynonymWorkflowError: Bij niet-bestaande suggestion of missing reason
        """
        logger.info(f"Rejecting suggestion {suggestion_id} by {rejected_by}")

        # Haal suggestion op
        suggestion = self.repository.get_suggestion(suggestion_id)
        if not suggestion:
            error_msg = f"Suggestion {suggestion_id} not found"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        # Verify status is pending
        if suggestion.status != SuggestionStatus.PENDING.value:
            error_msg = f"Suggestion {suggestion_id} is not pending (status: {suggestion.status})"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        # Require rejection reason
        if not reason or not reason.strip():
            error_msg = "Rejection reason is required"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        try:
            success = self.repository.reject_suggestion(
                suggestion_id=suggestion_id,
                reviewed_by=rejected_by,
                rejection_reason=reason,
            )

            if success:
                logger.info(
                    f"Successfully rejected suggestion {suggestion_id}: "
                    f"'{suggestion.synoniem}' (reason: {reason})"
                )

            return success

        except Exception as e:
            error_msg = f"Failed to reject suggestion {suggestion_id}: {e}"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg) from e

    def batch_approve(
        self, suggestion_ids: list[int], approved_by: str
    ) -> dict[str, Any]:
        """
        Approve meerdere suggestions in één batch.

        Process:
        - Approve elke suggestion individueel
        - Continue on errors (best-effort)
        - Return detailed stats over successes/failures

        Args:
            suggestion_ids: Lijst van suggestion IDs om te approven
            approved_by: Wie de batch approval uitvoert

        Returns:
            Dictionary met:
            - approved: aantal succesvol approved
            - failed: aantal gefaald
            - errors: lijst van error messages
            - approved_ids: lijst van succesvol approved IDs
            - failed_ids: lijst van gefaalde IDs
        """
        logger.info(
            f"Starting batch approval of {len(suggestion_ids)} suggestions "
            f"by {approved_by}"
        )

        stats = {
            "approved": 0,
            "failed": 0,
            "errors": [],
            "approved_ids": [],
            "failed_ids": [],
        }

        for suggestion_id in suggestion_ids:
            try:
                success = self.approve_suggestion(
                    suggestion_id=suggestion_id,
                    approved_by=approved_by,
                )

                if success:
                    stats["approved"] += 1
                    stats["approved_ids"].append(suggestion_id)
                else:
                    stats["failed"] += 1
                    stats["failed_ids"].append(suggestion_id)
                    stats["errors"].append(
                        f"Suggestion {suggestion_id}: Approval returned False"
                    )

            except Exception as e:
                stats["failed"] += 1
                stats["failed_ids"].append(suggestion_id)
                stats["errors"].append(f"Suggestion {suggestion_id}: {e!s}")
                logger.warning(
                    f"Failed to approve suggestion {suggestion_id} in batch: {e}"
                )

        logger.info(
            f"Batch approval complete: {stats['approved']} approved, "
            f"{stats['failed']} failed"
        )

        return stats

    def get_pending_suggestions(
        self,
        hoofdterm_filter: str | None = None,
        min_confidence: float = 0.0,
        limit: int | None = None,
    ) -> list[SynonymSuggestionRecord]:
        """
        Haal pending suggestions op voor review.

        Args:
            hoofdterm_filter: Filter op specifieke hoofdterm (optional)
            min_confidence: Minimum confidence threshold (default: 0.0)
            limit: Maximum aantal resultaten (optional)

        Returns:
            Lijst van SynonymSuggestionRecord objecten
        """
        return self.repository.get_pending_suggestions(
            hoofdterm_filter=hoofdterm_filter,
            min_confidence=min_confidence,
            limit=limit,
        )

    def revert_to_pending(self, suggestion_id: int, reverted_by: str) -> bool:
        """
        Revert een approved/rejected suggestion terug naar pending.

        Voor APPROVED suggestions:
        - Verwijder synoniem uit YAML config
        - Reset status naar pending in database

        Voor REJECTED suggestions:
        - Reset status naar pending in database

        Args:
            suggestion_id: ID van de suggestion
            reverted_by: Wie de revert uitvoert

        Returns:
            True als succesvol gerevert

        Raises:
            SynonymWorkflowError: Bij niet-bestaande suggestion of fouten
        """
        logger.info(f"Reverting suggestion {suggestion_id} to pending by {reverted_by}")

        # Haal suggestion op
        suggestion = self.repository.get_suggestion(suggestion_id)
        if not suggestion:
            error_msg = f"Suggestion {suggestion_id} not found"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg)

        # Check if already pending
        if suggestion.status == SuggestionStatus.PENDING.value:
            logger.info(f"Suggestion {suggestion_id} is already pending")
            return True

        # If approved, remove from YAML first
        if suggestion.status == SuggestionStatus.APPROVED.value:
            logger.info(
                f"Suggestion {suggestion_id} was approved, removing from YAML config"
            )
            try:
                yaml_removed = self.yaml_updater.remove_synonym(
                    hoofdterm=suggestion.hoofdterm,
                    synoniem=suggestion.synoniem,
                )

                if yaml_removed:
                    logger.info(
                        f"Removed '{suggestion.synoniem}' from YAML for '{suggestion.hoofdterm}'"
                    )
                else:
                    logger.warning(
                        f"Synoniem '{suggestion.synoniem}' not found in YAML "
                        f"(may have been manually removed), continuing with revert"
                    )

            except YAMLUpdateError as e:
                error_msg = (
                    f"Failed to remove synonym from YAML during revert "
                    f"for suggestion {suggestion_id}: {e}"
                )
                logger.error(error_msg)
                raise SynonymWorkflowError(error_msg) from e

        # Revert status to pending in database
        try:
            success = self.repository.revert_to_pending(
                suggestion_id=suggestion_id,
                reverted_by=reverted_by,
            )

            if success:
                logger.info(
                    f"Successfully reverted suggestion {suggestion_id} to pending: "
                    f"'{suggestion.hoofdterm}' → '{suggestion.synoniem}'"
                )
                return True
            logger.error(f"Database revert failed for suggestion {suggestion_id}")
            return False

        except Exception as e:
            error_msg = f"Failed to revert suggestion {suggestion_id}: {e}"
            logger.error(error_msg)
            raise SynonymWorkflowError(error_msg) from e

    def get_statistics(self) -> dict[str, Any]:
        """
        Haal workflow statistieken op.

        Returns:
            Dictionary met statistieken over suggestions
        """
        return self.repository.get_statistics()
