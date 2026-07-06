"""Regressietests voor DEF-524: resultaat-rendering crasht bij gefaalde generatie.

Twee samenhangende defecten op het faalpad:
1. `ServiceAdapter._create_failure_response` retourneert een gedeeltelijke
   UIResponseDict (zonder `validation_details`/`final_score`/`definitie_origineel`/
   `sources`), terwijl `_render_generation_details` kale key-access doet →
   `KeyError: 'validation_details'` (productie-traceback DEF-500, 2026-07-03).
2. `_render_generation_status` leest key `reason`, maar het faalpad zet de echte
   oorzaak in `error_message` → gebruiker ziet altijd "Onbekende fout".
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from services.service_factory import ServiceAdapter

pytestmark = [pytest.mark.unit]

VERPLICHTE_UI_KEYS = {
    "success",
    "definitie_origineel",
    "definitie_gecorrigeerd",
    "final_score",
    "validation_details",
    "voorbeelden",
    "metadata",
    "sources",
}


def _gefaalde_response(message: str = "AI provider error: 400 temperature") -> Any:
    """Minimale orchestrator-response voor het faalpad (success=False)."""
    return SimpleNamespace(success=False, definition=None, message=message)


def _failure_dict(**overrides: Any) -> dict[str, Any]:
    """Faal-dict zoals _create_failure_response die vóór DEF-524 opleverde."""
    result: dict[str, Any] = {
        "success": False,
        "error_message": "AI provider error: 400 temperature",
        "definitie_gecorrigeerd": "Generatie mislukt",
        "voorbeelden": {},
        "metadata": {},
    }
    result.update(overrides)
    return result


def _mock_st() -> MagicMock:
    st = MagicMock()
    st.columns.side_effect = lambda spec, **_kw: [
        MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))
    ]
    return st


def _adapter() -> ServiceAdapter:
    """ServiceAdapter zonder zware __init__ (methodes onder test zijn stateless)."""
    return ServiceAdapter.__new__(ServiceAdapter)


class TestFailureResponseContract:
    def test_failure_response_bevat_alle_verplichte_ui_keys(self):
        """Faalpad-dict voldoet aan het UIResponseDict-contract (verplichte keys)."""
        result = _adapter()._create_failure_response(_gefaalde_response())

        ontbrekend = VERPLICHTE_UI_KEYS - set(result.keys())
        assert not ontbrekend, (
            f"Faalpad-response mist verplichte UIResponseDict-keys: {ontbrekend} — "
            "render-pad crasht hierop (DEF-524)"
        )
        assert result["success"] is False
        assert result["error_message"] == "AI provider error: 400 temperature"
        assert result["final_score"] == 0.0
        assert result["validation_details"].get("violations") == []

    def test_failure_response_zonder_message_geeft_default(self):
        result = _adapter()._create_failure_response(
            SimpleNamespace(success=False, definition=None, message=None)
        )
        assert result["error_message"] == "Generatie mislukt"

    def test_failure_response_v2_error_attribuut_wordt_doorgegeven(self):
        """DefinitionResponseV2 draagt de oorzaak in .error (niet .message) —
        geverifieerd E2E: 401-provider-fout bleef anders onzichtbaar."""
        result = _adapter()._create_failure_response(
            SimpleNamespace(
                success=False,
                definition=None,
                message=None,
                error="Generation failed: AI API error: Error code: 401",
            )
        )
        assert "401" in result["error_message"]


class TestRenderGenerationDetailsFaalpad:
    def test_render_details_crasht_niet_op_gefaald_resultaat(self):
        """Reproduceert de productie-crash: KeyError 'validation_details'."""
        from ui.components.definition_generator_tab import DefinitionGeneratorTab

        st = _mock_st()
        with patch("ui.components.definition_generator_tab.st", st):
            # Kale faal-dict (pre-DEF-524-vorm) mag het render-pad nooit breken.
            DefinitionGeneratorTab._render_generation_details(
                SimpleNamespace(), _failure_dict()  # type: ignore[arg-type]
            )

        metric_labels = [str(c.args[0]) for c in st.metric.call_args_list]
        assert (
            "Violations" in metric_labels
        ), f"Violations-tegel niet gerenderd; metrics: {metric_labels}"

    def test_render_details_crasht_niet_zonder_metadata(self):
        """Ook een dict zonder metadata-key mag niet crashen."""
        from ui.components.definition_generator_tab import DefinitionGeneratorTab

        kale_dict = _failure_dict()
        del kale_dict["metadata"]
        st = _mock_st()
        with patch("ui.components.definition_generator_tab.st", st):
            DefinitionGeneratorTab._render_generation_details(
                SimpleNamespace(), kale_dict  # type: ignore[arg-type]
            )

        assert st.metric.called


class TestRenderGenerationStatusFaalpad:
    def test_status_toont_echte_foutoorzaak(self):
        """Gefaalde generatie toont error_message, niet 'Onbekende fout'."""
        from ui.components.definition_generator_tab import DefinitionGeneratorTab

        st = _mock_st()
        with patch("ui.components.definition_generator_tab.st", st):
            DefinitionGeneratorTab._render_generation_status(
                SimpleNamespace(), _failure_dict()
            )

        meldingen = [
            str(c.args[0])
            for mock in (st.warning, st.error)
            for c in mock.call_args_list
        ]
        assert meldingen, "Geen faalmelding gerenderd"
        samengevoegd = " | ".join(meldingen)
        assert (
            "400 temperature" in samengevoegd
        ), f"Echte foutoorzaak niet zichtbaar; meldingen: {meldingen}"
        assert "Onbekende fout" not in samengevoegd

    def test_status_zonder_oorzaak_valt_terug_op_default(self):
        from ui.components.definition_generator_tab import DefinitionGeneratorTab

        kale_dict = _failure_dict()
        del kale_dict["error_message"]
        st = _mock_st()
        with patch("ui.components.definition_generator_tab.st", st):
            DefinitionGeneratorTab._render_generation_status(
                SimpleNamespace(), kale_dict
            )

        meldingen = [
            str(c.args[0])
            for mock in (st.warning, st.error)
            for c in mock.call_args_list
        ]
        assert any("Onbekende fout" in m for m in meldingen)
