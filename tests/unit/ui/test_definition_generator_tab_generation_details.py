"""Regressietests voor DEF-455 (DEF-452 fase 2a).

`_render_generation_details` leest nu de canonieke `UIResponseDict`-keys:
- Verwerkingstijd uit `metadata["duration"]` (was dode read `processing_time` → altijd 0.0).
- Violations uit `validation_details["violations"]` (was dode read `toetsresultaten` →
  tegel rendde nooit omdat de key niet in `UIResponseDict` bestaat).

De methode gebruikt geen `self`-attributen, dus we instantieren via `object.__new__`
om de database-/service-dependencies in `__init__` te vermijden.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ui.components.definition_generator_tab import DefinitionGeneratorTab

pytestmark = pytest.mark.unit


def _make_tab() -> DefinitionGeneratorTab:
    """Construeer de tab zonder __init__ (geen DB-/service-deps nodig)."""
    return object.__new__(DefinitionGeneratorTab)


def _agent_result(duration: float, violations: int) -> dict[str, Any]:
    """Minimale canonieke UIResponseDict-shape voor de detail-render."""
    return {
        "success": True,
        "definitie_origineel": "x",
        "definitie_gecorrigeerd": "x",
        "final_score": 0.8,
        "validation_details": {
            "overall_score": 0.8,
            "is_acceptable": True,
            "violations": [
                {
                    "rule_id": f"R{i}",
                    "severity": "low",
                    "description": "d",
                    "suggestion": None,
                }
                for i in range(violations)
            ],
            "passed_rules": [],
        },
        "voorbeelden": {},
        "metadata": {"duration": duration},
        "sources": [],
    }


def _metric_calls(mock_st: MagicMock) -> list[tuple[Any, ...]]:
    return [call.args for call in mock_st.metric.call_args_list]


def test_verwerkingstijd_uses_metadata_duration() -> None:
    """Verwerkingstijd toont metadata['duration'], niet de dode 'processing_time'."""
    tab = _make_tab()
    agent_result = _agent_result(duration=2.5, violations=0)

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    assert ("Verwerkingstijd", "2.5s") in _metric_calls(mock_st)


def test_violations_uses_validation_details_violations() -> None:
    """Violations-tegel telt validation_details['violations'] (was nooit gerenderd)."""
    tab = _make_tab()
    agent_result = _agent_result(duration=0.0, violations=3)

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    assert ("Violations", 3) in _metric_calls(mock_st)


def test_processing_time_key_is_not_read() -> None:
    """Legacy 'processing_time'-key wordt genegeerd; metadata.duration is leidend."""
    tab = _make_tab()
    agent_result = _agent_result(duration=1.2, violations=0)
    # Een achtergebleven legacy-key mag het resultaat niet beïnvloeden.
    agent_result["processing_time"] = 99.9

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    calls = _metric_calls(mock_st)
    assert ("Verwerkingstijd", "1.2s") in calls
    assert ("Verwerkingstijd", "99.9s") not in calls


def test_violations_zero_renders_zero() -> None:
    """Bij een lege violations-lijst toont de tegel expliciet 0 (rendert nu altijd)."""
    tab = _make_tab()
    agent_result = _agent_result(duration=0.0, violations=0)

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    assert ("Violations", 0) in _metric_calls(mock_st)


def test_missing_duration_defaults_to_zero() -> None:
    """metadata.duration is NotRequired (total=False) → ontbreken geeft 0.0s, geen crash."""
    tab = _make_tab()
    agent_result = _agent_result(duration=0.0, violations=0)
    agent_result["metadata"] = {}  # geen duration-key

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    assert ("Verwerkingstijd", "0.0s") in _metric_calls(mock_st)


def test_legacy_toetsresultaten_key_is_ignored() -> None:
    """Legacy 'toetsresultaten'-key beïnvloedt de Violations-telling niet."""
    tab = _make_tab()
    agent_result = _agent_result(duration=0.0, violations=2)
    # Achtergebleven legacy-key met afwijkend aantal mag niet leidend zijn.
    agent_result["toetsresultaten"] = list(range(99))

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(agent_result)

    calls = _metric_calls(mock_st)
    assert ("Violations", 2) in calls
    assert ("Violations", 99) not in calls
