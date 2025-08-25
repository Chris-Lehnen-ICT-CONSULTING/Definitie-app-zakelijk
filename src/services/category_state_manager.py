"""Category state management - bridge tussen session state en services."""

import logging
from typing import Any

from models.category_models import DefinitionCategory
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class CategoryStateManager:
    """Beheer category state zonder direct session state access in UI."""

    @staticmethod
    def update_generation_result_category(
        generation_result: dict[str, Any], new_category: str
    ) -> dict[str, Any]:
        """Update category in generation result.

        Dit is een bridge functie die de session state update centraliseert.
        In de toekomst kan dit vervangen worden door events.
        """
        # Update de category in het result object
        generation_result["determined_category"] = new_category

        # Update session state (voorlopig nog nodig)
        SessionStateManager.set_value("last_generation_result", generation_result)

        logger.info(f"Category updated in generation result: {new_category}")

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
        """Clear category selector state."""
        SessionStateManager.set_value("show_category_selector", False)
