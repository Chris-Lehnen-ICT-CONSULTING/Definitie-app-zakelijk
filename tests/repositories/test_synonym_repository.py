"""
Tests voor SynonymRepository.

Test coverage:
- CRUD operations (create, read, update, delete)
- Status workflow (pending → approved/rejected)
- Filtering (status, hoofdterm, confidence)
- Statistics
- Duplicate prevention
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.repositories.synonym_repository import (
    SuggestionStatus,
    SynonymRepository,
    SynonymSuggestionRecord,
)


class TestSynonymSuggestionRecord:
    """Tests voor SynonymSuggestionRecord dataclass."""

    def test_record_creation(self):
        """Test basis record creation."""
        record = SynonymSuggestionRecord(
            hoofdterm="voorlopige hechtenis",
            synoniem="voorarrest",
            confidence=0.95,
            rationale="Juridisch synoniem",
        )

        assert record.hoofdterm == "voorlopige hechtenis"
        assert record.synoniem == "voorarrest"
        assert record.confidence == 0.95
        assert record.status == SuggestionStatus.PENDING.value

    def test_record_to_dict(self):
        """Test conversion to dictionary."""
        record = SynonymSuggestionRecord(
            hoofdterm="verdachte",
            synoniem="beklaagde",
            confidence=0.90,
            rationale="Procesfase-specifiek",
        )

        result = record.to_dict()

        assert result["hoofdterm"] == "verdachte"
        assert result["synoniem"] == "beklaagde"
        assert result["confidence"] == 0.90

    def test_context_dict_operations(self):
        """Test context data get/set operations."""
        record = SynonymSuggestionRecord(
            hoofdterm="test",
            synoniem="test2",
            confidence=0.8,
            rationale="test",
        )

        # Set context
        context = {"model": "gpt-4-turbo", "temperature": 0.3}
        record.set_context(context)

        # Get context
        retrieved = record.get_context_dict()
        assert retrieved["model"] == "gpt-4-turbo"
        assert retrieved["temperature"] == 0.3

    def test_context_dict_empty(self):
        """Test empty context returns empty dict."""
        record = SynonymSuggestionRecord(
            hoofdterm="test",
            synoniem="test2",
            confidence=0.8,
            rationale="test",
        )

        assert record.get_context_dict() == {}


class TestSynonymRepository:
    """Tests voor SynonymRepository."""

    @pytest.fixture
    def repo(self, test_db_path):
        """Create repository with test database and apply migration."""
        # Apply synonym_suggestions migration
        migration_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "add_synonym_suggestions_table.sql"
        )

        with sqlite3.connect(test_db_path) as conn:
            with open(migration_path, encoding="utf-8") as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)

        return SynonymRepository(db_path=test_db_path)

    def test_save_suggestion(self, repo):
        """Test saving a new suggestion."""
        suggestion_id = repo.save_suggestion(
            hoofdterm="voorlopige hechtenis",
            synoniem="voorarrest",
            confidence=0.95,
            rationale="Juridisch correct synoniem voor tijdelijke vrijheidsbeneming",
            context={"model": "gpt-4-turbo", "temperature": 0.3},
        )

        assert suggestion_id > 0

        # Verify saved
        suggestion = repo.get_suggestion(suggestion_id)
        assert suggestion is not None
        assert suggestion.hoofdterm == "voorlopige hechtenis"
        assert suggestion.synoniem == "voorarrest"
        assert suggestion.confidence == 0.95
        assert suggestion.status == SuggestionStatus.PENDING.value

    def test_save_suggestion_duplicate_raises_error(self, repo):
        """Test dat duplicate suggestions een error geven."""
        repo.save_suggestion(
            hoofdterm="verdachte",
            synoniem="beklaagde",
            confidence=0.90,
            rationale="Test",
        )

        # Probeer duplicate
        with pytest.raises(ValueError, match="bestaat al"):
            repo.save_suggestion(
                hoofdterm="verdachte",
                synoniem="beklaagde",
                confidence=0.85,
                rationale="Duplicate test",
            )

    def test_save_suggestion_invalid_confidence_raises_error(self, repo):
        """Test dat invalide confidence een error geeft."""
        with pytest.raises(ValueError, match="tussen 0.0 en 1.0"):
            repo.save_suggestion(
                hoofdterm="test",
                synoniem="test2",
                confidence=1.5,  # Out of range
                rationale="Test",
            )

    def test_get_suggestion_not_found(self, repo):
        """Test dat get_suggestion None returnt voor non-existent ID."""
        result = repo.get_suggestion(99999)
        assert result is None

    def test_get_pending_suggestions(self, repo):
        """Test ophalen van pending suggestions."""
        # Save multiple suggestions
        repo.save_suggestion("term1", "syn1", 0.95, "rationale1")
        repo.save_suggestion("term2", "syn2", 0.80, "rationale2")
        repo.save_suggestion("term3", "syn3", 0.65, "rationale3")

        # Get all pending
        pending = repo.get_pending_suggestions()
        assert len(pending) == 3

        # Get with min confidence filter
        high_conf = repo.get_pending_suggestions(min_confidence=0.85)
        assert len(high_conf) == 1
        assert high_conf[0].confidence == 0.95

    def test_get_pending_suggestions_with_hoofdterm_filter(self, repo):
        """Test filtering pending suggestions by hoofdterm."""
        repo.save_suggestion("term1", "syn1", 0.95, "rationale1")
        repo.save_suggestion("term1", "syn2", 0.90, "rationale2")
        repo.save_suggestion("term2", "syn3", 0.85, "rationale3")

        # Filter by hoofdterm
        term1_suggestions = repo.get_pending_suggestions(hoofdterm_filter="term1")
        assert len(term1_suggestions) == 2
        assert all(s.hoofdterm == "term1" for s in term1_suggestions)

    def test_get_pending_suggestions_with_limit(self, repo):
        """Test limit parameter works."""
        for i in range(5):
            repo.save_suggestion(f"term{i}", f"syn{i}", 0.9, "rationale")

        limited = repo.get_pending_suggestions(limit=2)
        assert len(limited) == 2

    def test_approve_suggestion(self, repo):
        """Test approving a suggestion."""
        suggestion_id = repo.save_suggestion("test", "test2", 0.95, "rationale")

        # Approve
        success = repo.approve_suggestion(suggestion_id, "curator1")
        assert success

        # Verify status changed
        suggestion = repo.get_suggestion(suggestion_id)
        assert suggestion.status == SuggestionStatus.APPROVED.value
        assert suggestion.reviewed_by == "curator1"
        assert suggestion.reviewed_at is not None

    def test_reject_suggestion(self, repo):
        """Test rejecting a suggestion."""
        suggestion_id = repo.save_suggestion("test", "test2", 0.95, "rationale")

        # Reject
        success = repo.reject_suggestion(suggestion_id, "curator1", "Te algemeen")
        assert success

        # Verify status changed
        suggestion = repo.get_suggestion(suggestion_id)
        assert suggestion.status == SuggestionStatus.REJECTED.value
        assert suggestion.reviewed_by == "curator1"
        assert suggestion.rejection_reason == "Te algemeen"
        assert suggestion.reviewed_at is not None

    def test_reject_suggestion_requires_reason(self, repo):
        """Test dat reject een reason vereist."""
        suggestion_id = repo.save_suggestion("test", "test2", 0.95, "rationale")

        with pytest.raises(ValueError, match="verplicht"):
            repo.reject_suggestion(suggestion_id, "curator1", "")

    def test_approve_nonexistent_suggestion_returns_false(self, repo):
        """Test dat approve False returnt voor non-existent suggestion."""
        success = repo.approve_suggestion(99999, "curator1")
        assert not success

    def test_get_suggestions_by_status(self, repo):
        """Test filtering by status."""
        # Create suggestions with different statuses
        id1 = repo.save_suggestion("t1", "s1", 0.95, "r1")
        id2 = repo.save_suggestion("t2", "s2", 0.90, "r2")
        id3 = repo.save_suggestion("t3", "s3", 0.85, "r3")

        repo.approve_suggestion(id1, "curator1")
        repo.reject_suggestion(id2, "curator1", "Too general")

        # Get by status
        approved = repo.get_suggestions_by_status(SuggestionStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].id == id1

        rejected = repo.get_suggestions_by_status(SuggestionStatus.REJECTED)
        assert len(rejected) == 1
        assert rejected[0].id == id2

        pending = repo.get_suggestions_by_status(SuggestionStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == id3

    def test_get_statistics(self, repo):
        """Test statistics generation."""
        # Create test data
        id1 = repo.save_suggestion("t1", "s1", 0.95, "r1")
        id2 = repo.save_suggestion("t2", "s2", 0.90, "r2")
        id3 = repo.save_suggestion("t3", "s3", 0.85, "r3")
        repo.save_suggestion("t4", "s4", 0.80, "r4")

        repo.approve_suggestion(id1, "curator1")
        repo.approve_suggestion(id2, "curator1")
        repo.reject_suggestion(id3, "curator1", "Test")

        stats = repo.get_statistics()

        # Check counts
        assert stats["total"] == 4
        assert stats["by_status"]["approved"] == 2
        assert stats["by_status"]["rejected"] == 1
        assert stats["by_status"]["pending"] == 1

        # Check approval rate (2 approved / 3 reviewed = 0.666...)
        assert 0.65 < stats["approval_rate"] < 0.67

    def test_get_suggestions_for_hoofdterm(self, repo):
        """Test getting all suggestions for a specific hoofdterm."""
        # Create multiple suggestions for same hoofdterm
        repo.save_suggestion("verdachte", "beklaagde", 0.95, "r1")
        repo.save_suggestion("verdachte", "beschuldigde", 0.90, "r2")
        repo.save_suggestion("vonnis", "uitspraak", 0.85, "r3")

        # Get suggestions for 'verdachte'
        suggestions = repo.get_suggestions_for_hoofdterm("verdachte")
        assert len(suggestions) == 2
        assert all(s.hoofdterm == "verdachte" for s in suggestions)

        # Verify sorted by confidence DESC
        assert suggestions[0].confidence >= suggestions[1].confidence

    def test_delete_suggestion(self, repo):
        """Test deleting a suggestion."""
        suggestion_id = repo.save_suggestion("test", "test2", 0.95, "rationale")

        # Delete
        success = repo.delete_suggestion(suggestion_id)
        assert success

        # Verify deleted
        suggestion = repo.get_suggestion(suggestion_id)
        assert suggestion is None

    def test_delete_nonexistent_suggestion_returns_false(self, repo):
        """Test dat delete False returnt voor non-existent suggestion."""
        success = repo.delete_suggestion(99999)
        assert not success

    def test_context_data_persistence(self, repo):
        """Test dat context data correct opgeslagen en opgehaald wordt."""
        context = {
            "model": "gpt-4-turbo",
            "temperature": 0.3,
            "definitie": "Test definitie",
        }

        suggestion_id = repo.save_suggestion(
            hoofdterm="test",
            synoniem="test2",
            confidence=0.90,
            rationale="Test rationale",
            context=context,
        )

        # Retrieve and verify context
        suggestion = repo.get_suggestion(suggestion_id)
        retrieved_context = suggestion.get_context_dict()

        assert retrieved_context["model"] == "gpt-4-turbo"
        assert retrieved_context["temperature"] == 0.3
        assert retrieved_context["definitie"] == "Test definitie"

    def test_timestamps_are_set(self, repo):
        """Test dat created_at en updated_at automatisch gezet worden."""
        suggestion_id = repo.save_suggestion("test", "test2", 0.95, "rationale")

        suggestion = repo.get_suggestion(suggestion_id)

        assert suggestion.created_at is not None
        assert suggestion.updated_at is not None
        assert isinstance(suggestion.created_at, datetime)
        assert isinstance(suggestion.updated_at, datetime)

    def test_pending_suggestions_ordered_by_confidence_desc(self, repo):
        """Test dat pending suggestions gesorteerd worden op confidence DESC."""
        repo.save_suggestion("t1", "s1", 0.75, "r1")
        repo.save_suggestion("t2", "s2", 0.95, "r2")
        repo.save_suggestion("t3", "s3", 0.85, "r3")

        pending = repo.get_pending_suggestions()

        # Verify descending confidence order
        assert pending[0].confidence == 0.95
        assert pending[1].confidence == 0.85
        assert pending[2].confidence == 0.75


class TestIntegration:
    """Integration tests voor complete workflow."""

    @pytest.fixture
    def repo(self, test_db_path):
        """Create repository with test database and apply migration."""
        # Apply synonym_suggestions migration
        migration_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "database"
            / "migrations"
            / "add_synonym_suggestions_table.sql"
        )

        with sqlite3.connect(test_db_path) as conn:
            with open(migration_path, encoding="utf-8") as f:
                migration_sql = f.read()
                conn.executescript(migration_sql)

        return SynonymRepository(db_path=test_db_path)

    def test_complete_approval_workflow(self, repo):
        """Test complete workflow: save → review → approve → verify."""
        # Step 1: Save suggestion
        suggestion_id = repo.save_suggestion(
            hoofdterm="voorlopige hechtenis",
            synoniem="voorarrest",
            confidence=0.95,
            rationale="Juridisch correct synoniem",
            context={"model": "gpt-4-turbo"},
        )

        # Step 2: Verify pending
        pending = repo.get_pending_suggestions()
        assert len(pending) == 1
        assert pending[0].id == suggestion_id

        # Step 3: Approve
        repo.approve_suggestion(suggestion_id, "curator_chris")

        # Step 4: Verify no longer pending
        pending_after = repo.get_pending_suggestions()
        assert len(pending_after) == 0

        # Step 5: Verify in approved list
        approved = repo.get_suggestions_by_status(SuggestionStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].id == suggestion_id
        assert approved[0].reviewed_by == "curator_chris"

    def test_complete_rejection_workflow(self, repo):
        """Test complete workflow: save → review → reject → verify."""
        # Save suggestion
        suggestion_id = repo.save_suggestion(
            "verdachte", "crimineel", 0.70, "Mogelijk te pejoratief"
        )

        # Reject with reason
        repo.reject_suggestion(
            suggestion_id, "curator_chris", "Te pejoratief, niet juridisch neutraal"
        )

        # Verify rejected
        rejected = repo.get_suggestions_by_status(SuggestionStatus.REJECTED)
        assert len(rejected) == 1
        assert rejected[0].id == suggestion_id
        assert rejected[0].rejection_reason == "Te pejoratief, niet juridisch neutraal"

    def test_batch_processing_workflow(self, repo):
        """Test batch processing van multiple suggestions."""
        # Simulate batch GPT-4 generation
        batch_suggestions = [
            ("voorlopige hechtenis", "voorarrest", 0.95, "Juridisch synoniem"),
            ("voorlopige hechtenis", "bewaring", 0.90, "Sterk synoniem"),
            ("verdachte", "beklaagde", 0.90, "Procesfase synoniem"),
            ("vonnis", "uitspraak", 0.85, "Algemeen synoniem"),
        ]

        # Save all
        suggestion_ids = []
        for hoofdterm, synoniem, conf, rat in batch_suggestions:
            sid = repo.save_suggestion(hoofdterm, synoniem, conf, rat)
            suggestion_ids.append(sid)

        # Verify all pending
        pending = repo.get_pending_suggestions()
        assert len(pending) == 4

        # Approve high confidence ones (>= 0.90)
        for suggestion in pending:
            if suggestion.confidence >= 0.90:
                repo.approve_suggestion(suggestion.id, "curator_auto")

        # Verify approval stats
        stats = repo.get_statistics()
        assert stats["by_status"]["approved"] == 3  # 0.95, 0.90, 0.90
        assert stats["by_status"]["pending"] == 1  # 0.85
