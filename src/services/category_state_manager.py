"""Category state helpers — UI-vrije dict-mutaties."""

import logging
from typing import Any

from models.category_models import DefinitionCategory

logger = logging.getLogger(__name__)


class CategoryStateManager:
    """Beheer categorieveld in generation_result als pure helper."""

    @staticmethod
    def update_generation_result_category(
        generation_result: dict[str, Any], new_category: str
    ) -> dict[str, Any]:
        """Update category in generation result.

        Pure helper: muteert alleen het doorgegeven generation_result dict.
        """
        generation_result["determined_category"] = new_category
        logger.info(f"Category set on generation_result: {new_category}")
        return generation_result

    @staticmethod
    def get_current_category(
        generation_result: dict[str, Any],
    ) -> DefinitionCategory | None:
        """Get current category uit generation result."""
        category_code = generation_result.get("determined_category")
        if category_code:
            return DefinitionCategory.from_code(category_code)
        return None

    @staticmethod
    def clear_category_selector():
        """No-op placeholder; UI beheert eigen session state."""
        return
