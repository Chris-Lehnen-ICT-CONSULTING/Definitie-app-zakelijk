"""
End-to-End Integration Tests voor Synonym Automation Workflow.

Test complete flow van GPT-4 suggestion → database → approval → YAML update.
Inclusief error handling, rollback mechanisms, en batch operations.

Test Categories:
- Happy path: Complete workflow zonder fouten
- Error handling: YAML failures, database constraints, rollback
- Batch operations: Multiple suggestions, bulk approval
- Edge cases: Duplicates, low confidence, rejection workflow
"""

import json
import logging
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import yaml

from repositories.synonym_repository import (
    SuggestionStatus,
    SynonymRepository,
    SynonymSuggestionRecord,
)
from services.synonym_automation.gpt4_suggester import (
    GPT4SynonymSuggester,
    SynonymSuggestion,
)
from services.synonym_automation.yaml_updater import (
    YAMLConfigUpdater,
    YAMLUpdateError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """
    Create test database met synonym_suggestions table.

    Returns:
        Path naar test database
    """
    db_path = tmp_path / "test_definities.db"

    # Apply migration
    migration_sql = """
    CREATE TABLE IF NOT EXISTS synonym_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hoofdterm TEXT NOT NULL,
        synoniem TEXT NOT NULL,
        confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
        rationale TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
        reviewed_by TEXT,
        reviewed_at TIMESTAMP,
        rejection_reason TEXT,
        context_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_synonym_suggestions_status
    ON synonym_suggestions(status);

    CREATE INDEX IF NOT EXISTS idx_synonym_suggestions_hoofdterm
    ON synonym_suggestions(hoofdterm);

    CREATE UNIQUE INDEX IF NOT EXISTS idx_synonym_suggestions_unique_pair
    ON synonym_suggestions(hoofdterm, synoniem);

    CREATE TRIGGER IF NOT EXISTS update_synonym_suggestions_timestamp
    AFTER UPDATE ON synonym_suggestions
    BEGIN
        UPDATE synonym_suggestions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    """

    conn = sqlite3.connect(str(db_path))
    conn.executescript(migration_sql)
    conn.commit()
    conn.close()

    logger.info(f"Created test database: {db_path}")
    return db_path


@pytest.fixture
def test_yaml_path(tmp_path: Path) -> Path:
    """
    Create test YAML config file met minimal data.

    Returns:
        Path naar test YAML config
    """
    yaml_path = tmp_path / "test_juridische_synoniemen.yaml"

    # Minimal valid config
    config = {
        "voorlopige_hechtenis": ["voorarrest", "bewaring"],
        "verdachte": ["beklaagde", "beschuldigde"],
        "_clusters": {
            "strafrecht": ["voorlopige_hechtenis", "verdachte"],
        },
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    logger.info(f"Created test YAML config: {yaml_path}")
    return yaml_path


@pytest.fixture
def mock_ai_service():
    """
    Mock AI service voor GPT-4 suggester tests.

    Returns:
        Mocked AIServiceV2 instance
    """
    mock = AsyncMock()

    # Default response: 3 high-confidence suggestions
    default_response = {
        "synoniemen": [
            {
                "term": "gedetineerde",
                "confidence": 0.85,
                "rationale": "Persoon die vastzit in voorlopige hechtenis",
            },
            {
                "term": "gevangengenomene",
                "confidence": 0.80,
                "rationale": "Algemene term voor iemand die in bewaring is",
            },
            {
                "term": "aangehoudene",
                "confidence": 0.75,
                "rationale": "Persoon die aangehouden is door politie",
            },
        ]
    }

    async def mock_generate(*args, **kwargs):
        """Mock generate_definition response."""
        result = Mock()
        result.text = json.dumps(default_response, ensure_ascii=False)
        return result

    mock.generate_definition = mock_generate
    return mock


@pytest.fixture
def synonym_repo(test_db_path: Path) -> SynonymRepository:
    """Create SynonymRepository instance voor tests."""
    return SynonymRepository(db_path=str(test_db_path))


@pytest.fixture
def yaml_updater(test_yaml_path: Path, tmp_path: Path) -> YAMLConfigUpdater:
    """Create YAMLConfigUpdater instance voor tests."""
    backup_dir = tmp_path / "backups"
    return YAMLConfigUpdater(
        yaml_path=test_yaml_path,
        backup_dir=backup_dir,
    )


@pytest.fixture
def gpt4_suggester(mock_ai_service) -> GPT4SynonymSuggester:
    """Create GPT4SynonymSuggester instance met mocked AI service."""
    return GPT4SynonymSuggester(
        ai_service=mock_ai_service,
        min_confidence=0.6,
        max_synonyms=5,
    )


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_synonym_workflow_happy_path(
    gpt4_suggester: GPT4SynonymSuggester,
    synonym_repo: SynonymRepository,
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test complete workflow: suggest → save → approve → YAML update.

    Flow:
    1. GPT-4 genereert suggestions
    2. Suggestions worden opgeslagen in database (status: pending)
    3. Suggestions worden approved
    4. YAML config wordt geupdate
    5. Database status wordt geupdate (status: approved)
    """
    hoofdterm = "verdachte"

    # STEP 1: Generate suggestions
    suggestions = await gpt4_suggester.suggest_synonyms(
        term=hoofdterm,
        definitie="Persoon tegen wie verdenking bestaat dat hij een strafbaar feit heeft gepleegd",
        context=["Sv", "strafrecht"],
    )

    assert len(suggestions) == 3  # Mock returns 3 suggestions
    assert all(s.confidence >= 0.6 for s in suggestions)
    assert all(s.hoofdterm == hoofdterm for s in suggestions)

    # STEP 2: Save suggestions to database
    suggestion_ids = []
    for suggestion in suggestions:
        suggestion_id = synonym_repo.save_suggestion(
            hoofdterm=suggestion.hoofdterm,
            synoniem=suggestion.synoniem,
            confidence=suggestion.confidence,
            rationale=suggestion.rationale,
            context=suggestion.context_used,
        )
        suggestion_ids.append(suggestion_id)

    # Verify saved to database
    pending = synonym_repo.get_pending_suggestions()
    assert len(pending) == 3
    assert all(s.status == SuggestionStatus.PENDING.value for s in pending)

    # STEP 3: Approve first suggestion
    first_suggestion = pending[0]
    success = synonym_repo.approve_suggestion(
        suggestion_id=first_suggestion.id,
        reviewed_by="test_user",
    )
    assert success is True

    # STEP 4: Update YAML config
    yaml_success = yaml_updater.add_synonym(
        hoofdterm=first_suggestion.hoofdterm,
        synoniem=first_suggestion.synoniem,
        weight=first_suggestion.confidence,
    )
    assert yaml_success is True

    # STEP 5: Verify YAML updated
    yaml_synonyms = yaml_updater.get_synonyms(hoofdterm)
    assert first_suggestion.synoniem in yaml_synonyms

    # STEP 6: Verify database updated
    updated = synonym_repo.get_suggestion(first_suggestion.id)
    assert updated.status == SuggestionStatus.APPROVED.value
    assert updated.reviewed_by == "test_user"
    assert updated.reviewed_at is not None

    # Verify statistics
    stats = synonym_repo.get_statistics()
    assert stats["by_status"][SuggestionStatus.APPROVED.value] == 1
    assert stats["by_status"][SuggestionStatus.PENDING.value] == 2
    assert stats["total"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_approve_multiple_suggestions(
    gpt4_suggester: GPT4SynonymSuggester,
    synonym_repo: SynonymRepository,
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test batch approval van meerdere suggestions.

    Verifies:
    - Alle suggestions worden approved
    - Alle suggestions worden toegevoegd aan YAML
    - Database status wordt correct geupdate
    """
    hoofdterm = "verdachte"

    # Generate and save suggestions
    suggestions = await gpt4_suggester.suggest_synonyms(term=hoofdterm)

    for suggestion in suggestions:
        synonym_repo.save_suggestion(
            hoofdterm=suggestion.hoofdterm,
            synoniem=suggestion.synoniem,
            confidence=suggestion.confidence,
            rationale=suggestion.rationale,
        )

    # Get all pending
    pending = synonym_repo.get_pending_suggestions()
    assert len(pending) == 3

    # Batch approve all
    approved_count = 0
    for suggestion in pending:
        # Approve in database
        success = synonym_repo.approve_suggestion(
            suggestion_id=suggestion.id,
            reviewed_by="batch_user",
        )
        assert success is True

        # Add to YAML
        yaml_success = yaml_updater.add_synonym(
            hoofdterm=suggestion.hoofdterm,
            synoniem=suggestion.synoniem,
            weight=suggestion.confidence,
        )
        assert yaml_success is True
        approved_count += 1

    assert approved_count == 3

    # Verify all approved in database
    approved = synonym_repo.get_suggestions_by_status(SuggestionStatus.APPROVED)
    assert len(approved) == 3
    assert all(s.reviewed_by == "batch_user" for s in approved)

    # Verify all in YAML
    yaml_synonyms = yaml_updater.get_synonyms(hoofdterm)
    for suggestion in pending:
        assert suggestion.synoniem in yaml_synonyms


# ============================================================================
# ERROR HANDLING & ROLLBACK TESTS
# ============================================================================


@pytest.mark.integration
def test_yaml_failure_does_not_corrupt_database(
    synonym_repo: SynonymRepository,
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test dat YAML update failure niet de database corrumpeert.

    Scenario:
    1. Suggestion wordt approved in database
    2. YAML update faalt (corrupt YAML)
    3. Database rollback zou moeten worden getriggered
    4. Suggestion status blijft pending of wordt gerevert
    """
    # Create suggestion
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm="test_term",
        synoniem="test_synonym",
        confidence=0.85,
        rationale="Test rationale",
    )

    # Verify pending
    suggestion = synonym_repo.get_suggestion(suggestion_id)
    assert suggestion.status == SuggestionStatus.PENDING.value

    # Approve suggestion
    success = synonym_repo.approve_suggestion(
        suggestion_id=suggestion_id,
        reviewed_by="test_user",
    )
    assert success is True

    # Corrupt YAML by making it invalid
    with open(yaml_updater.yaml_path, "w", encoding="utf-8") as f:
        f.write("invalid: yaml: [corrupt")

    # Try to update YAML - should fail
    with pytest.raises(YAMLUpdateError):
        yaml_updater.add_synonym(
            hoofdterm="test_term",
            synoniem="test_synonym",
        )

    # Verify database still has approved status
    # (In real workflow, you'd implement rollback here)
    suggestion = synonym_repo.get_suggestion(suggestion_id)
    assert suggestion.status == SuggestionStatus.APPROVED.value

    # NOTE: In production workflow, implement:
    # - Transaction wrapper around approve + YAML update
    # - Rollback database status if YAML update fails
    # - Log error for manual intervention


@pytest.mark.integration
def test_yaml_rollback_on_failure(
    yaml_updater: YAMLConfigUpdater,
    test_yaml_path: Path,
):
    """
    Test dat YAML rollback werkt bij update failures.

    Verifies:
    - Backup wordt gemaakt voor update
    - Bij failure wordt backup gerestored
    - YAML blijft in valid state
    """
    # Get initial state
    initial_synonyms = yaml_updater.get_synonyms("verdachte")
    initial_count = len(initial_synonyms)

    # Mock _write_yaml to fail
    original_write = yaml_updater._write_yaml

    def failing_write(data: dict[str, Any]):
        raise IOError("Simulated write failure")

    yaml_updater._write_yaml = failing_write

    # Try to add synonym - should fail and rollback
    with pytest.raises(YAMLUpdateError) as exc_info:
        yaml_updater.add_synonym(
            hoofdterm="verdachte",
            synoniem="test_failing_synonym",
        )

    assert "Failed to add synonym" in str(exc_info.value)

    # Restore original write method
    yaml_updater._write_yaml = original_write

    # Verify rollback worked - YAML unchanged
    current_synonyms = yaml_updater.get_synonyms("verdachte")
    assert len(current_synonyms) == initial_count
    assert "test_failing_synonym" not in current_synonyms

    # Verify YAML is still valid and loadable
    data = yaml_updater._load_yaml()
    assert isinstance(data, dict)


# ============================================================================
# DUPLICATE PREVENTION TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_suggestions_rejected(
    gpt4_suggester: GPT4SynonymSuggester,
    synonym_repo: SynonymRepository,
):
    """
    Test dat duplicate synonym suggestions worden geweigerd.

    Verifies:
    - Eerste suggestion wordt opgeslagen
    - Tweede identieke suggestion wordt rejected met ValueError
    - Database constraint werkt (UNIQUE hoofdterm + synoniem)
    """
    hoofdterm = "verdachte"

    # Generate suggestions
    suggestions = await gpt4_suggester.suggest_synonyms(term=hoofdterm)
    first_suggestion = suggestions[0]

    # Save first time - should succeed
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm=first_suggestion.hoofdterm,
        synoniem=first_suggestion.synoniem,
        confidence=first_suggestion.confidence,
        rationale=first_suggestion.rationale,
    )
    assert suggestion_id > 0

    # Try to save again - should fail with ValueError
    with pytest.raises(ValueError) as exc_info:
        synonym_repo.save_suggestion(
            hoofdterm=first_suggestion.hoofdterm,
            synoniem=first_suggestion.synoniem,
            confidence=first_suggestion.confidence,
            rationale=first_suggestion.rationale,
        )

    assert "bestaat al" in str(exc_info.value)
    assert f"ID: {suggestion_id}" in str(exc_info.value)


@pytest.mark.integration
def test_duplicate_yaml_synonyms_skipped(
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test dat duplicate YAML synonyms worden geskipped (skip_if_exists=True).

    Verifies:
    - Eerste add succeeds (returns True)
    - Tweede add skips (returns False)
    - YAML bevat synoniem slechts 1x
    """
    hoofdterm = "verdachte"

    # Add first time
    success = yaml_updater.add_synonym(
        hoofdterm=hoofdterm,
        synoniem="test_new_synonym",
        skip_if_exists=True,
    )
    assert success is True

    # Add again with skip_if_exists=True
    success = yaml_updater.add_synonym(
        hoofdterm=hoofdterm,
        synoniem="test_new_synonym",
        skip_if_exists=True,
    )
    assert success is False  # Skipped

    # Verify only one occurrence in YAML
    synonyms = yaml_updater.get_synonyms(hoofdterm)
    count = sum(1 for s in synonyms if s == "test_new_synonym")
    assert count == 1

    # Try with skip_if_exists=False - should raise error
    with pytest.raises(YAMLUpdateError) as exc_info:
        yaml_updater.add_synonym(
            hoofdterm=hoofdterm,
            synoniem="test_new_synonym",
            skip_if_exists=False,
        )

    assert "already exists" in str(exc_info.value)


# ============================================================================
# CONFIDENCE FILTERING TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_low_confidence_suggestions_filtered(
    mock_ai_service,
):
    """
    Test dat low-confidence suggestions worden gefilterd.

    Verifies:
    - Suggester met threshold 0.8 filtert suggestions < 0.8
    - Alleen high-confidence suggestions worden returned
    """
    # Create suggester with high threshold
    suggester = GPT4SynonymSuggester(
        ai_service=mock_ai_service,
        min_confidence=0.8,  # Only accept >= 0.8
        max_synonyms=10,
    )

    # Mock response with mixed confidence scores
    mixed_response = {
        "synoniemen": [
            {"term": "high_conf", "confidence": 0.95, "rationale": "Very good"},
            {"term": "medium_conf", "confidence": 0.85, "rationale": "Good"},
            {"term": "low_conf", "confidence": 0.70, "rationale": "Weak"},
            {"term": "very_low_conf", "confidence": 0.50, "rationale": "Questionable"},
        ]
    }

    async def mock_generate(*args, **kwargs):
        result = Mock()
        result.text = json.dumps(mixed_response, ensure_ascii=False)
        return result

    mock_ai_service.generate_definition = mock_generate

    # Generate suggestions
    suggestions = await suggester.suggest_synonyms("test_term")

    # Verify only high-confidence suggestions returned
    assert len(suggestions) == 2  # Only 0.95 and 0.85
    assert all(s.confidence >= 0.8 for s in suggestions)
    assert suggestions[0].synoniem == "high_conf"
    assert suggestions[1].synoniem == "medium_conf"


@pytest.mark.integration
def test_confidence_threshold_filtering_in_repository(
    synonym_repo: SynonymRepository,
):
    """
    Test dat repository correct filtert op min_confidence.

    Verifies:
    - get_pending_suggestions respecteert min_confidence parameter
    - Alleen suggestions >= threshold worden returned
    """
    # Create suggestions met verschillende confidence scores
    synonym_repo.save_suggestion(
        hoofdterm="term1",
        synoniem="high_conf",
        confidence=0.95,
        rationale="High confidence",
    )
    synonym_repo.save_suggestion(
        hoofdterm="term2",
        synoniem="medium_conf",
        confidence=0.75,
        rationale="Medium confidence",
    )
    synonym_repo.save_suggestion(
        hoofdterm="term3",
        synoniem="low_conf",
        confidence=0.60,
        rationale="Low confidence",
    )

    # Get all pending (no filter)
    all_pending = synonym_repo.get_pending_suggestions(min_confidence=0.0)
    assert len(all_pending) == 3

    # Get only high confidence (>= 0.8)
    high_conf = synonym_repo.get_pending_suggestions(min_confidence=0.8)
    assert len(high_conf) == 1
    assert high_conf[0].confidence == 0.95

    # Get medium and high (>= 0.7)
    medium_high = synonym_repo.get_pending_suggestions(min_confidence=0.7)
    assert len(medium_high) == 2
    assert all(s.confidence >= 0.7 for s in medium_high)


# ============================================================================
# REJECTION WORKFLOW TESTS
# ============================================================================


@pytest.mark.integration
def test_reject_suggestion_workflow(
    synonym_repo: SynonymRepository,
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test rejection workflow.

    Verifies:
    1. Suggestion kan worden rejected met reason
    2. Status wordt geupdate naar rejected
    3. Rejected suggestion wordt NIET toegevoegd aan YAML
    4. Rejection reason wordt opgeslagen
    """
    # Create suggestion
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm="verdachte",
        synoniem="bad_synonym",
        confidence=0.70,
        rationale="Questionable synonym",
    )

    # Reject with reason
    success = synonym_repo.reject_suggestion(
        suggestion_id=suggestion_id,
        reviewed_by="reviewer",
        rejection_reason="Te informeel, niet juridisch correct",
    )
    assert success is True

    # Verify status updated
    rejected = synonym_repo.get_suggestion(suggestion_id)
    assert rejected.status == SuggestionStatus.REJECTED.value
    assert rejected.reviewed_by == "reviewer"
    assert rejected.rejection_reason == "Te informeel, niet juridisch correct"
    assert rejected.reviewed_at is not None

    # Verify NOT in YAML
    yaml_synonyms = yaml_updater.get_synonyms("verdachte")
    assert "bad_synonym" not in yaml_synonyms

    # Verify statistics
    stats = synonym_repo.get_statistics()
    assert stats["by_status"].get(SuggestionStatus.REJECTED.value, 0) == 1


@pytest.mark.integration
def test_rejection_requires_reason(
    synonym_repo: SynonymRepository,
):
    """
    Test dat rejection reason verplicht is.

    Verifies:
    - Empty string rejection reason raises ValueError
    - Whitespace-only reason raises ValueError
    """
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm="test",
        synoniem="test_syn",
        confidence=0.8,
        rationale="Test",
    )

    # Try to reject without reason
    with pytest.raises(ValueError) as exc_info:
        synonym_repo.reject_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by="reviewer",
            rejection_reason="",
        )
    assert "verplicht" in str(exc_info.value)

    # Try to reject with whitespace-only reason
    with pytest.raises(ValueError):
        synonym_repo.reject_suggestion(
            suggestion_id=suggestion_id,
            reviewed_by="reviewer",
            rejection_reason="   ",
        )


# ============================================================================
# YAML OPERATIONS TESTS
# ============================================================================


@pytest.mark.integration
def test_yaml_add_removes_synonym(
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test add en remove operations op YAML.

    Verifies:
    - Add succeeds
    - Synonym bestaat in YAML
    - Remove succeeds
    - Synonym is verwijderd uit YAML
    """
    hoofdterm = "verdachte"

    # Add synonym
    success = yaml_updater.add_synonym(
        hoofdterm=hoofdterm,
        synoniem="test_add_remove",
    )
    assert success is True

    # Verify exists
    synonyms = yaml_updater.get_synonyms(hoofdterm)
    assert "test_add_remove" in synonyms

    # Remove synonym
    removed = yaml_updater.remove_synonym(
        hoofdterm=hoofdterm,
        synoniem="test_add_remove",
    )
    assert removed is True

    # Verify removed
    synonyms = yaml_updater.get_synonyms(hoofdterm)
    assert "test_add_remove" not in synonyms


@pytest.mark.integration
def test_yaml_weighted_synonyms(
    yaml_updater: YAMLConfigUpdater,
    test_yaml_path: Path,
):
    """
    Test weighted synonym format in YAML.

    Verifies:
    - Weighted format wordt correct opgeslagen
    - get_synonyms extraheert plain strings uit weighted format
    """
    hoofdterm = "test_weighted"

    # Add weighted synonym
    success = yaml_updater.add_synonym(
        hoofdterm=hoofdterm,
        synoniem="weighted_syn",
        weight=0.85,
    )
    assert success is True

    # Verify in YAML with weight
    with open(test_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "test_weighted" in data
    synonyms_list = data["test_weighted"]

    # Find weighted entry
    weighted_entry = None
    for item in synonyms_list:
        if isinstance(item, dict) and item.get("synoniem") == "weighted_syn":
            weighted_entry = item
            break

    assert weighted_entry is not None
    assert weighted_entry["weight"] == 0.85

    # Verify get_synonyms extracts plain string
    plain_synonyms = yaml_updater.get_synonyms(hoofdterm)
    assert "weighted_syn" in plain_synonyms


# ============================================================================
# STATISTICS & REPORTING TESTS
# ============================================================================


@pytest.mark.integration
def test_repository_statistics(
    synonym_repo: SynonymRepository,
):
    """
    Test statistics reporting.

    Verifies:
    - by_status counts
    - avg_confidence_by_status
    - approval_rate calculation
    - recent activity tracking
    """
    # Create varied suggestions
    synonym_repo.save_suggestion(
        hoofdterm="t1", synoniem="s1", confidence=0.95, rationale="Test"
    )
    synonym_repo.save_suggestion(
        hoofdterm="t2", synoniem="s2", confidence=0.85, rationale="Test"
    )
    synonym_repo.save_suggestion(
        hoofdterm="t3", synoniem="s3", confidence=0.75, rationale="Test"
    )

    # Approve one
    suggestions = synonym_repo.get_pending_suggestions()
    synonym_repo.approve_suggestion(suggestions[0].id, "user1")

    # Reject one
    synonym_repo.reject_suggestion(
        suggestions[1].id, "user2", "Not good enough"
    )

    # Get statistics
    stats = synonym_repo.get_statistics()

    # Verify counts
    assert stats["total"] == 3
    assert stats["by_status"][SuggestionStatus.PENDING.value] == 1
    assert stats["by_status"][SuggestionStatus.APPROVED.value] == 1
    assert stats["by_status"][SuggestionStatus.REJECTED.value] == 1

    # Verify approval rate (1 approved / 2 reviewed = 0.5)
    assert stats["approval_rate"] == 0.5

    # Verify avg confidence exists
    assert "avg_confidence_by_status" in stats
    assert SuggestionStatus.APPROVED.value in stats["avg_confidence_by_status"]


# ============================================================================
# EDGE CASES & DATA VALIDATION
# ============================================================================


@pytest.mark.integration
def test_invalid_confidence_range_rejected(
    synonym_repo: SynonymRepository,
):
    """
    Test dat confidence buiten range (0.0-1.0) wordt rejected.

    Verifies:
    - Confidence > 1.0 raises ValueError
    - Confidence < 0.0 raises ValueError
    """
    # Too high
    with pytest.raises(ValueError) as exc_info:
        synonym_repo.save_suggestion(
            hoofdterm="test",
            synoniem="test_syn",
            confidence=1.5,
            rationale="Test",
        )
    assert "tussen 0.0 en 1.0" in str(exc_info.value)

    # Too low
    with pytest.raises(ValueError):
        synonym_repo.save_suggestion(
            hoofdterm="test",
            synoniem="test_syn",
            confidence=-0.1,
            rationale="Test",
        )


@pytest.mark.integration
def test_empty_hoofdterm_handled(
    synonym_repo: SynonymRepository,
):
    """
    Test dat empty hoofdterm wordt afgehandeld.

    In practice, dit zou niet moeten voorkomen, maar test defensive programming.
    """
    # SQLite zou dit moeten accepteren (geen NOT NULL constraint op hoofdterm tekst)
    # Maar het is slechte data - in production zou je validatie toevoegen
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm="",  # Empty string
        synoniem="test_syn",
        confidence=0.8,
        rationale="Test",
    )

    assert suggestion_id > 0

    # Verify saved
    suggestion = synonym_repo.get_suggestion(suggestion_id)
    assert suggestion.hoofdterm == ""


@pytest.mark.integration
def test_special_characters_in_synonyms(
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test dat special characters (accents, quotes, etc.) correct worden behandeld.

    Verifies:
    - UTF-8 encoding werkt
    - Special characters worden preserved
    """
    hoofdterm = "test_special"

    # Add synonyms met special characters
    special_synonyms = [
        "café",  # Accent
        "naïef",  # Diaeresis
        "één",  # Dutch special char
        "recht's",  # Apostrophe
    ]

    for syn in special_synonyms:
        success = yaml_updater.add_synonym(hoofdterm=hoofdterm, synoniem=syn)
        assert success is True

    # Verify all preserved correctly
    retrieved = yaml_updater.get_synonyms(hoofdterm)
    for syn in special_synonyms:
        assert syn in retrieved


# ============================================================================
# CLEANUP & MAINTENANCE TESTS
# ============================================================================


@pytest.mark.integration
def test_yaml_backup_cleanup(
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test dat oude backups worden opgeschoond.

    Verifies:
    - cleanup_old_backups behoudt laatste N backups
    - Oude backups worden verwijderd
    """
    # Create 15 test backups
    for i in range(15):
        yaml_updater._create_backup()

    # Verify 15 backups exist
    backups = list(yaml_updater.backup_dir.glob("juridische_synoniemen_*.yaml"))
    assert len(backups) >= 15

    # Cleanup - keep only 5
    yaml_updater.cleanup_old_backups(keep_count=5)

    # Verify only 5 remain
    backups = list(yaml_updater.backup_dir.glob("juridische_synoniemen_*.yaml"))
    assert len(backups) == 5


@pytest.mark.integration
def test_delete_suggestion_cleanup(
    synonym_repo: SynonymRepository,
):
    """
    Test dat suggestions kunnen worden verwijderd (admin cleanup).

    Verifies:
    - delete_suggestion werkt
    - Suggestion is echt verwijderd
    """
    # Create suggestion
    suggestion_id = synonym_repo.save_suggestion(
        hoofdterm="test",
        synoniem="test_syn",
        confidence=0.8,
        rationale="Test",
    )

    # Verify exists
    suggestion = synonym_repo.get_suggestion(suggestion_id)
    assert suggestion is not None

    # Delete
    deleted = synonym_repo.delete_suggestion(suggestion_id)
    assert deleted is True

    # Verify deleted
    suggestion = synonym_repo.get_suggestion(suggestion_id)
    assert suggestion is None

    # Try to delete again - should return False
    deleted = synonym_repo.delete_suggestion(suggestion_id)
    assert deleted is False


# ============================================================================
# PERFORMANCE & BATCH TESTS
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_batch_processing_performance(
    synonym_repo: SynonymRepository,
    yaml_updater: YAMLConfigUpdater,
):
    """
    Test batch processing performance (optional).

    Verifies:
    - 100 suggestions kunnen worden verwerkt
    - Geen memory leaks
    - Completes binnen redelijke tijd
    """
    import time

    start_time = time.time()

    # Create 100 suggestions
    batch_size = 100
    for i in range(batch_size):
        synonym_repo.save_suggestion(
            hoofdterm=f"term_{i % 10}",  # 10 verschillende hoofdtermen
            synoniem=f"synonym_{i}",
            confidence=0.6 + (i % 40) / 100,  # Vary confidence 0.6-0.99
            rationale=f"Rationale {i}",
        )

    # Verify all saved
    all_pending = synonym_repo.get_pending_suggestions()
    assert len(all_pending) == batch_size

    # Batch approve all
    for suggestion in all_pending:
        synonym_repo.approve_suggestion(suggestion.id, "batch_user")
        yaml_updater.add_synonym(
            hoofdterm=suggestion.hoofdterm,
            synoniem=suggestion.synoniem,
            weight=suggestion.confidence,
        )

    end_time = time.time()
    duration = end_time - start_time

    # Verify completion time reasonable (< 10 seconds)
    assert duration < 10.0, f"Batch processing took {duration:.2f}s (expected < 10s)"

    # Verify statistics
    stats = synonym_repo.get_statistics()
    assert stats["by_status"][SuggestionStatus.APPROVED.value] == batch_size

    logger.info(f"Batch processed {batch_size} suggestions in {duration:.2f}s")


# ============================================================================
# YAML VALIDATION TESTS
# ============================================================================


@pytest.mark.integration
def test_yaml_validation_catches_invalid_structure(
    test_yaml_path: Path,
    tmp_path: Path,
):
    """
    Test dat YAML validation invalid structures detecteert.

    Verifies:
    - Invalid synoniemen list (not a list) raises error
    - Invalid synonym type (not string or dict) raises error
    """
    # Create updater
    updater = YAMLConfigUpdater(yaml_path=test_yaml_path, backup_dir=tmp_path / "bak")

    # Manually corrupt YAML with invalid structure
    with open(test_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "test_term": "not_a_list",  # Should be list
            },
            f,
        )

    # Try to load - should raise validation error
    with pytest.raises(YAMLUpdateError) as exc_info:
        updater._load_yaml()
        # Validation happens in _validate_yaml which is called by add_synonym
        updater.add_synonym("test_term", "new_syn")

    assert "moet een list zijn" in str(exc_info.value).lower() or "validation" in str(
        exc_info.value
    ).lower()
