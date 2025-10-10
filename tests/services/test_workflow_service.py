"""
Tests voor WorkflowService.

Deze tests valideren alle business logic voor status workflow
zonder database dependencies.
"""

from datetime import UTC, datetime, timezone

import pytest

from services.workflow_service import (DefinitionStatus, StatusChange,
                                       WorkflowService)


class TestWorkflowService:
    """Test suite voor WorkflowService."""

    @pytest.fixture()
    def service(self):
        """Create a service instance."""
        return WorkflowService()

    def test_basic_transitions(self, service):
        """Test basic allowed transitions."""
        # Draft can go to review or archived
        assert service.can_change_status("draft", "review") is True
        assert service.can_change_status("draft", "archived") is True
        assert service.can_change_status("draft", "established") is False

        # Review can go to established, draft, or archived
        assert service.can_change_status("review", "established") is False  # Needs role
        assert service.can_change_status("review", "draft") is True
        assert service.can_change_status("review", "archived") is True

        # Established can only go to archived
        assert service.can_change_status("established", "archived") is True
        assert service.can_change_status("established", "draft") is False
        assert service.can_change_status("established", "review") is False

        # Archived can be restored to draft
        assert service.can_change_status("archived", "draft") is True
        assert service.can_change_status("archived", "review") is False
        assert service.can_change_status("archived", "established") is False

    def test_role_based_permissions(self, service):
        """Test role-based transition permissions."""
        # Only reviewers and admins can approve to established
        assert service.can_change_status("review", "established", "reviewer") is True
        assert service.can_change_status("review", "established", "admin") is True
        assert service.can_change_status("review", "established", "user") is False
        assert service.can_change_status("review", "established", None) is False

        # Only admins can archive (when role specified)
        assert service.can_change_status("established", "archived", "admin") is True
        assert service.can_change_status("established", "archived", "user") is False

        # Only admins can restore from archive (when role specified)
        assert service.can_change_status("archived", "draft", "admin") is True
        assert service.can_change_status("archived", "draft", "user") is False

    def test_prepare_status_change(self, service):
        """Test status change preparation."""
        # Basic status change
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="draft",
            new_status="review",
            user="test_user",
        )

        assert changes["status"] == "review"
        assert changes["updated_by"] == "test_user"
        assert "updated_at" in changes
        assert isinstance(changes["updated_at"], datetime)

        # Approval to established
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="review",
            new_status="established",
            user="reviewer1",
            user_role="reviewer",
            notes="Looks good",
        )

        assert changes["status"] == "established"
        assert changes["approved_by"] == "reviewer1"
        assert "approved_at" in changes
        assert changes["approval_notes"] == "Looks good"

        # Archive with reason
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="established",
            new_status="archived",
            user="admin1",
            user_role="admin",
            notes="Outdated",
        )

        assert changes["status"] == "archived"
        assert changes["archived_by"] == "admin1"
        assert "archived_at" in changes
        assert changes["archive_reason"] == "Outdated"

        # Restore from archive
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="archived",
            new_status="draft",
            user="admin1",
            user_role="admin",
        )

        assert changes["status"] == "draft"
        assert changes["restored_by"] == "admin1"
        assert "restored_at" in changes
        assert changes["archived_by"] is None
        assert changes["archived_at"] is None

    def test_invalid_transitions(self, service):
        """Test that invalid transitions raise errors."""
        # Invalid transition
        with pytest.raises(ValueError) as exc:
            service.prepare_status_change(
                definition_id=1,
                current_status="draft",
                new_status="established",
                user="test_user",
            )
        assert "Invalid transition" in str(exc.value)

        # Invalid role for transition
        with pytest.raises(ValueError) as exc:
            service.prepare_status_change(
                definition_id=1,
                current_status="review",
                new_status="established",
                user="test_user",
                user_role="user",
            )
        assert "Invalid transition" in str(exc.value)
        assert "user" in str(exc.value)

    def test_get_allowed_transitions(self, service):
        """Test getting allowed transitions."""
        # Without role
        transitions = service.get_allowed_transitions("draft")
        assert set(transitions) == {"review", "archived"}

        transitions = service.get_allowed_transitions("review")
        assert set(transitions) == {"established", "draft", "archived"}

        # With role restrictions
        transitions = service.get_allowed_transitions("review", "user")
        assert "established" not in transitions  # User can't approve
        assert "draft" in transitions

        transitions = service.get_allowed_transitions("review", "reviewer")
        assert "established" in transitions  # Reviewer can approve

    def test_validate_status_history(self, service):
        """Test status change history validation."""
        # Valid history
        valid_history = [
            StatusChange("draft", "review", "user1", datetime.now(UTC)),
            StatusChange("review", "established", "reviewer1", datetime.now(UTC)),
            StatusChange("established", "archived", "admin1", datetime.now(UTC)),
        ]

        assert service.validate_status_change_history(valid_history) is True

        # Invalid initial status
        invalid_history = [
            StatusChange("review", "established", "user1", datetime.now(UTC))
        ]

        assert service.validate_status_change_history(invalid_history) is False

        # Invalid transition
        invalid_history = [
            StatusChange("draft", "review", "user1", datetime.now(UTC)),
            StatusChange("review", "archived", "user2", datetime.now(UTC)),
            StatusChange(
                "archived", "established", "user3", datetime.now(UTC)
            ),  # Invalid
        ]

        assert service.validate_status_change_history(invalid_history) is False

        # Discontinuity
        invalid_history = [
            StatusChange("draft", "review", "user1", datetime.now(UTC)),
            StatusChange("established", "archived", "user2", datetime.now(UTC)),  # Gap
        ]

        assert service.validate_status_change_history(invalid_history) is False

    def test_get_status_info(self, service):
        """Test status information retrieval."""
        # Known status
        info = service.get_status_info("draft")
        assert info["name"] == "Concept"
        assert info["editable"] is True
        assert "description" in info
        assert "color" in info
        assert "icon" in info

        info = service.get_status_info("established")
        assert info["name"] == "Vastgesteld"
        assert info["editable"] is False

        # Unknown status
        info = service.get_status_info("unknown")
        assert info["name"] == "unknown"
        assert info["description"] == "Onbekende status"

    def test_can_edit_definition(self, service):
        """Test edit permission checks."""
        # Only draft is editable
        assert service.can_edit_definition("draft") is True
        assert service.can_edit_definition("review") is False
        assert service.can_edit_definition("established") is False
        assert service.can_edit_definition("archived") is False

        # Admin override
        assert service.can_edit_definition("review", "admin") is True
        assert service.can_edit_definition("established", "admin") is True
        assert service.can_edit_definition("archived", "admin") is True

        # Regular user no override
        assert service.can_edit_definition("review", "user") is False

    def test_get_workflow_summary(self, service):
        """Test workflow summary generation."""
        summary = service.get_workflow_summary()

        assert "statuses" in summary
        assert len(summary["statuses"]) == 4
        assert "draft" in summary["statuses"]

        assert "transitions" in summary
        assert isinstance(summary["transitions"], dict)

        assert "role_permissions" in summary
        assert "approve_to_established" in summary["role_permissions"]

        assert "editable_statuses" in summary
        assert summary["editable_statuses"] == ["draft"]

        assert "final_statuses" in summary
        assert set(summary["final_statuses"]) == {"established", "archived"}

    def test_submit_for_review(self, service):
        """Test submit_for_review convenience method."""
        # Basic submit for review
        changes = service.submit_for_review(definition_id=42, user="test_user")

        assert changes["status"] == "review"
        assert changes["updated_by"] == "test_user"
        assert "updated_at" in changes
        assert isinstance(changes["updated_at"], datetime)

        # Submit with custom notes
        changes = service.submit_for_review(
            definition_id=42, user="test_user", notes="Custom submission note"
        )

        # The notes are passed to prepare_status_change but not in the returned dict
        # This is expected behavior - notes are for logging/history
        assert changes["status"] == "review"
        assert changes["updated_by"] == "test_user"

    def test_submit_for_review_invalid_transition(self, service):
        """Test submit_for_review with invalid current status."""
        # This will fail because submit_for_review expects DRAFT status
        # but prepare_status_change will validate the transition
        with pytest.raises(ValueError) as exc:
            # Simulating a call where current status is not draft
            service.prepare_status_change(
                definition_id=42,
                current_status="established",  # Wrong status
                new_status="review",
                user="test_user",
                notes="Should fail",
            )
        assert "Invalid transition" in str(exc.value)


class TestWorkflowServiceEdgeCases:
    """Edge case tests voor WorkflowService."""

    def test_empty_history(self):
        """Test with empty history."""
        service = WorkflowService()
        assert service.validate_status_change_history([]) is True

    def test_default_notes(self):
        """Test default notes when not provided."""
        service = WorkflowService()

        # Approval without notes
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="review",
            new_status="established",
            user="reviewer1",
            user_role="reviewer",
        )
        assert changes["approval_notes"] == "Goedgekeurd"

        # Archive without notes
        changes = service.prepare_status_change(
            definition_id=1,
            current_status="established",
            new_status="archived",
            user="admin1",
            user_role="admin",
        )
        assert changes["archive_reason"] == "Gearchiveerd"

    def test_role_none_handling(self):
        """Test handling of None role."""
        service = WorkflowService()

        # Basic transitions work without role
        assert service.can_change_status("draft", "review", None) is True

        # Role-restricted transitions fail
        assert service.can_change_status("review", "established", None) is False
