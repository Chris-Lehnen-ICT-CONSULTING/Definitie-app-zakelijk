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


# ------------------------------------------------- DEF-621: geen vals oordeel


def _onbepaald_result() -> dict[str, Any]:
    """UIResponseDict zoals de Generator hem krijgt bij een incomplete regelset.

    De nullen in `final_score` en `overall_score` zijn fail-closed
    placeholders, geen kwaliteitsoordeel. Het onderscheid zit uitsluitend in
    `validation_details["validation_status"]`.
    """
    resultaat = _agent_result(duration=1.0, violations=0)
    resultaat["final_score"] = 0.0
    resultaat["validation_details"] = {
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "validation_status": "validation_unknown",
        "unknown_reason": "ruleset_incomplete",
        "validation_readiness": {
            "ready": False,
            "expected_total": 53,
            "loaded_total": 7,
            "missing_rule_ids": ["CON-01"],
            "unexpected_rule_ids": [],
        },
    }
    return resultaat


def _status_teksten(mock_st: MagicMock) -> list[str]:
    teksten: list[str] = []
    for api in ("success", "warning", "info", "error", "markdown", "write"):
        teksten += [str(call.args[0]) for call in getattr(mock_st, api).call_args_list]
    return teksten


def test_generatiestatus_toont_geen_score_bij_validation_unknown() -> None:
    """Zonder oordeel mag er geen cijfer staan - ook niet 0.00.

    De statusregel meldde "(Score: 0.00)" op de placeholder. Dat leest als
    "deze definitie scoort nul", terwijl er geen enkele toetsregel is
    gedraaid.
    """
    tab = _make_tab()

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        tab._render_generation_status(_onbepaald_result())

    teksten = _status_teksten(mock_st)
    assert teksten, "statusregel rendert niets"
    assert not any("0.00" in t for t in teksten), teksten
    assert not any("score" in t.lower() for t in teksten), teksten
    # De generatie zelf is wel geslaagd; dat mag gemeld blijven worden.
    assert any("gegenereerd" in t.lower() for t in teksten), teksten


def test_generatiestatus_toont_score_bij_validated() -> None:
    """De positieve regressie: het normale pad blijft ongewijzigd."""
    tab = _make_tab()
    resultaat = _agent_result(duration=1.0, violations=0)
    resultaat["final_score"] = 0.82
    resultaat["validation_details"]["validation_status"] = "validated"

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        tab._render_generation_status(resultaat)

    teksten = _status_teksten(mock_st)
    assert any("Score: 0.82" in t for t in teksten), teksten


def test_generatiedetails_tonen_geen_finale_score_bij_validation_unknown() -> None:
    """De metric "Finale Score" toonde dezelfde placeholder als een cijfer."""
    tab = _make_tab()

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(_onbepaald_result())

    calls = _metric_calls(mock_st)
    labels = [c[0] for c in calls if c]
    assert "Finale Score" not in labels, calls
    assert not any("0.00" in str(c[1]) for c in calls if len(c) > 1), calls
    # De overige tegels blijven staan; alleen het oordeel verdwijnt.
    assert ("Verwerkingstijd", "1.0s") in calls, calls


def test_generatiedetails_tonen_finale_score_bij_validated() -> None:
    """Positieve regressie op de detailtegels."""
    tab = _make_tab()
    resultaat = _agent_result(duration=1.0, violations=0)
    resultaat["final_score"] = 0.82
    resultaat["validation_details"]["validation_status"] = "validated"

    with patch("ui.components.definition_generator_tab.st") as mock_st:
        mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
        tab._render_generation_details(resultaat)

    assert ("Finale Score", "0.82") in _metric_calls(mock_st)


def test_validatiesectie_geeft_de_discriminator_door() -> None:
    """De gedeelde renderer moet het volledige genormaliseerde dict krijgen.

    Zonder `validation_status` kan de gedeelde early return niet vuren en
    toont de Generator alsnog een score.
    """
    tab = _make_tab()
    tab.validation_renderer = MagicMock()
    resultaat = _onbepaald_result()

    with patch("ui.components.definition_generator_tab.st"):
        tab._render_validation_section(resultaat)

    doorgegeven = tab.validation_renderer.render_validation_results.call_args.args[0]
    assert doorgegeven["validation_status"] == "validation_unknown"
    assert doorgegeven["validation_readiness"]["loaded_total"] == 7
