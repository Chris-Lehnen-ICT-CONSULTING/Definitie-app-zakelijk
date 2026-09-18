"""DEF-751 B1 — geen stille PROCES in de generatiehandler.

Patroon test_def622_context_voor_generatie: echte `DefinitionGenerationHandler`
met geïnjecteerde `st`/`SessionStateManager`. Een handmatige keuze of een
modelvoorstel buiten de vier generatiecategorieën viel vóór B1 stil terug op
PROCES — zowel in de duplicaatvoorcontrole als in de modelaanroep. Nu stopt
de handler vóór checker en model met een begrijpelijke melding; een geldige
keuze reist exact door. Herkomst (handmatig/model) wordt niet als bevestiging
opgeslagen — dat is B2.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from domain.ontological_categories import OntologischeCategorie
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]

CONTEXT = {"organisatorische_context": ["DJI"], "wettelijke_basis": ["Regeling Z"]}


def _handler() -> DefinitionGenerationHandler:
    return DefinitionGenerationHandler(
        checker=MagicMock(), definition_service=MagicMock(), repository=MagicMock()
    )


def _sessie(**waarden):
    sessie = {
        "generation_options": {
            "force_generate": True,
            "force_duplicate": True,
            "force_duplicate_reason": "reden",
            "model": "x",
        },
        **waarden,
    }
    sm = MagicMock()
    sm.get_value = Mock(side_effect=lambda k, d=None: sessie.get(k, d))
    return sm


@pytest.mark.parametrize(
    ("sessiewaarden", "verwacht_in_melding"),
    [
        ({"manual_ontological_category": "ENT"}, "ENT"),
        (
            {"manual_ontological_category": "Kind", "determined_category": "type"},
            "Kind",
        ),
        ({"determined_category": "Kind"}, "Kind"),
        ({"determined_category": "ENT"}, "ENT"),
    ],
    ids=[
        "handmatig-ENT",
        "handmatig-wint-van-voorstel",
        "voorstel-Kind",
        "voorstel-ENT",
    ],
)
def test_ongeldige_categorie_stopt_voor_checker_en_model(
    sessiewaarden, verwacht_in_melding
):
    handler = _handler()
    mock_st = MagicMock()
    mock_st.error = Mock()
    sm = _sessie(**sessiewaarden)

    handler.handle_definition_generation("keurmerk", CONTEXT, _st=mock_st, _sm=sm)

    mock_st.error.assert_called_once()
    melding = mock_st.error.call_args[0][0]
    assert verwacht_in_melding in melding
    assert "proces" not in melding.split("(")[0].lower()  # geen PROCES-suggestie vooraf
    assert "type, proces, resultaat, exemplaar" in melding
    handler.checker.check_before_generation.assert_not_called()
    handler.definition_service.generate_definition.assert_not_called()
    # Eenmalige force-opties zijn verbruikt (zelfde regel als de contextgate).
    sm.set_value.assert_any_call("generation_options", {"model": "x"})


@pytest.mark.parametrize(
    ("sessiewaarden", "verwacht"),
    [
        ({"manual_ontological_category": "TYPE"}, OntologischeCategorie.TYPE),
        ({"manual_ontological_category": "exemplaar"}, OntologischeCategorie.EXEMPLAAR),
        (
            {
                "manual_ontological_category": "RESULTAAT",
                "determined_category": "proces",
            },
            OntologischeCategorie.RESULTAAT,
        ),
        ({"determined_category": "type"}, OntologischeCategorie.TYPE),
        ({"determined_category": "RESULTAAT"}, OntologischeCategorie.RESULTAAT),
    ],
    ids=[
        "handmatig-TYPE",
        "handmatig-exemplaar",
        "handmatig-boven-voorstel",
        "voorstel-type",
        "voorstel-RESULTAAT",
    ],
)
def test_geldige_keuze_reist_exact_door_naar_duplicaatvoorcontrole(
    sessiewaarden, verwacht
):
    handler = _handler()
    mock_st = MagicMock()
    mock_st.error = Mock()
    mock_st.button = Mock(return_value=False)  # geen keuze in de duplicaatdialoog
    mock_st.columns.side_effect = lambda spec, **kw: [MagicMock(), MagicMock()]
    sm = _sessie(**sessiewaarden)
    sm.get_value = Mock(
        side_effect=lambda k, d=None: {
            **sessiewaarden,
            "generation_options": {"model": "x"},  # niet geforceerd → checker draait
        }.get(k, d)
    )
    # De checker meldt een bestaande definitie: de handler stopt daar (geen model).
    handler.checker.check_before_generation.return_value = MagicMock(
        action="SHOW_EXISTING", existing_definitie=None
    )

    handler.handle_definition_generation("keurmerk", CONTEXT, _st=mock_st, _sm=sm)

    mock_st.error.assert_not_called()
    handler.checker.check_before_generation.assert_called_once()
    assert (
        handler.checker.check_before_generation.call_args.kwargs["categorie"]
        is verwacht
    )
    handler.definition_service.generate_definition.assert_not_called()
