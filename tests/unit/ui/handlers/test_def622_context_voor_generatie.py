"""DEF-622 vervolgcriteria — de UI vraagt om context vóór een nieuwe generatie.

CON-GT-001 / CW-GEN-05: zonder minimaal één inhoudelijke waarde in de drie
contextlijsten start de generatie-handler geen duplicaatcontrole en geen
modelaanroep; de gebruiker krijgt de vraag om context. De eenmalige
force-opties worden daarbij verbruikt (zelfde regel als bij een ongeldig
begrip, reviewbevinding D3). De harde grens zelf ligt in de orchestrator
(`test_def622_generatiegrens.py`); dit is de zichtbare UI-kant.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]


def _handler() -> DefinitionGenerationHandler:
    return DefinitionGenerationHandler(
        checker=MagicMock(), definition_service=MagicMock(), repository=MagicMock()
    )


@pytest.mark.parametrize(
    "context_data",
    [
        {},
        {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        },
        {"organisatorische_context": ["", "  "], "juridische_context": [None]},
    ],
    ids=["ontbreekt", "leeg", "alleen-witruimte"],
)
def test_zonder_context_vraagt_de_handler_om_context_en_genereert_niet(context_data):
    handler = _handler()
    mock_st = MagicMock()
    mock_st.error = Mock()
    mock_sm = MagicMock()
    sessie = {
        "determined_category": "TYPE",
        "generation_options": {
            "force_generate": True,
            "force_duplicate": True,
            "force_duplicate_reason": "reden",
            "model": "x",
        },
    }
    mock_sm.get_value = Mock(side_effect=lambda k, d=None: sessie.get(k, d))

    handler.handle_definition_generation(
        "keurmerk", context_data, _st=mock_st, _sm=mock_sm
    )

    mock_st.error.assert_called_once()
    melding = mock_st.error.call_args[0][0].lower()
    assert "minimaal één contextwaarde" in melding
    assert "organisatorisch" in melding and "wettelijke basis" in melding
    mock_st.spinner.assert_not_called()
    handler.checker.check_before_generation.assert_not_called()
    handler.definition_service.generate_definition.assert_not_called()
    handler.repository.assert_not_called()
    # De eenmalige force-opties zijn verbruikt; overige opties blijven.
    mock_sm.set_value.assert_any_call("generation_options", {"model": "x"})


def test_met_context_passeert_de_contextgate():
    """Met één inhoudelijke waarde blokkeert de contextgate niet: de handler
    gaat door naar de duplicaatvoorcontrole. DEF-751 B2: zonder classificatie
    (alleen wettelijke basis) loopt dat labelvrij (categorie None), er is geen
    classificatiegate meer en geen verzonnen PROCES."""
    handler = _handler()
    mock_st = MagicMock()
    mock_st.error = Mock()
    mock_st.button = Mock(return_value=False)
    mock_st.columns.side_effect = lambda spec, **kw: [MagicMock(), MagicMock()]
    mock_sm = MagicMock()
    mock_sm.get_value = Mock(return_value=None)  # geen classificatie
    handler.checker.check_before_generation.return_value = MagicMock(
        action="SHOW_EXISTING", existing_definitie=None
    )

    handler.handle_definition_generation(
        "keurmerk",
        {"organisatorische_context": [], "wettelijke_basis": ["Regeling Z"]},
        _st=mock_st,
        _sm=mock_sm,
    )

    mock_st.error.assert_not_called()
    handler.checker.check_before_generation.assert_called_once()
    assert handler.checker.check_before_generation.call_args.kwargs["categorie"] is None
