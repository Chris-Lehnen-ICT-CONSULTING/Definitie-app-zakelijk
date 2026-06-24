"""Delegatie-tests voor ServiceContextAdapter (DEF-439).

De adapter riep niet-bestaande ContextManager-methodes aan
(`get_current_context`, `get_merged_context`). Deze tests borgen dat de
adapter het echte contract gebruikt: `get_context() -> ContextData | None`
geserialiseerd via `to_dict()`.
"""

from unittest.mock import Mock

import pytest

from services.context.context_adapter import ServiceContextAdapter

pytestmark = [pytest.mark.unit]


def _manager_with_context(data: dict | None):
    manager = Mock()
    if data is None:
        manager.get_context.return_value = None
    else:
        ctx = Mock()
        ctx.to_dict.return_value = data
        manager.get_context.return_value = ctx
    return manager


def test_get_context_serialiseert_contextdata():
    manager = _manager_with_context({"organisatie": "Gemeente X"})
    adapter = ServiceContextAdapter(context_manager=manager)

    assert adapter.get_context() == {"organisatie": "Gemeente X"}
    manager.get_context.assert_called_once()


def test_get_context_zonder_context_geeft_lege_dict():
    adapter = ServiceContextAdapter(context_manager=_manager_with_context(None))
    assert adapter.get_context() == {}


def test_get_merged_context_voegt_additional_toe():
    manager = _manager_with_context({"organisatie": "Gemeente X", "wet_context": "AVG"})
    adapter = ServiceContextAdapter(context_manager=manager)

    merged = adapter.get_merged_context({"organisatie": "Override"})

    assert merged == {"organisatie": "Override", "wet_context": "AVG"}
