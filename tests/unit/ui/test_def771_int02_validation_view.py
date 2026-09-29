"""DEF-771 WP3: de open INT-02-reden is zichtbaar bij ingeklapte details.

Echte service-uitkomst, echte `render_validation_detailed_list`; alleen de
Streamlit-aanroepen worden opgevangen (patroon DEF-767). De reden bevat
gebruikersinvoer en verschijnt daarom letterlijk via `st.text`. Andere
oordeelregels blijven achter de toggle; een niet-uitgevoerde INT-02 levert
geen reviewtekst, maar wel de exacte NE-melding als deeluitkomst.
"""

from __future__ import annotations

import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from ui.components import validation_view
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

C04 = "Getal dat even is indien het zonder rest door twee deelbaar is."
CONTEXT = {"organisatorische_context": ["Synthetisch loket"]}
NE_CONTEXT = (
    "INT-02 — Niet uitgevoerd: context ontbreekt. Er is geen inhoudelijk oordeel."
)


def _vang_streamlit(monkeypatch) -> dict[str, list[str]]:
    shown = {
        api: []
        for api in ("markdown", "info", "warning", "success", "error", "write", "text")
    }
    for api in shown:
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, _api=api, **kw: shown[_api].append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    return shown


async def _render(monkeypatch, context, sleutel):
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    result = await svc.validate_definition(
        begrip="even getal", text=C04, context=context
    )
    shown = _vang_streamlit(monkeypatch)
    SessionStateManager.set_value(f"{sleutel}_show_validation_details", False)
    validation_view.render_validation_detailed_list(result, key_prefix=sleutel)
    return result, shown


async def test_open_int02_reden_letterlijk_zichtbaar(monkeypatch):
    result, shown = await _render(monkeypatch, CONTEXT, "def771")
    redenen = {r["rule_id"]: r["reason"] for r in result["review_required"]}
    assert redenen["INT-02"].startswith("INT-02 — Toetsvraag:")
    assert redenen["INT-02"] in shown["text"]
    for api, values in shown.items():
        if api != "text":
            assert redenen["INT-02"] not in "\n".join(values)
    # Andere oordeelregels blijven achter de toggle.
    assert redenen["STR-03"] not in "\n".join(shown["text"])


async def test_niet_uitgevoerde_int02_toont_geen_reviewtekst(monkeypatch):
    result, shown = await _render(monkeypatch, {}, "def771b")
    assert result["rule_statuses"]["INT-02"] == "not_evaluated"
    assert not any(t.startswith("INT-02") for t in shown["text"])
    # De exacte NE-melding is wél zichtbaar, via de bestaande weergave van
    # deeluitkomsten (waarschuwing, geen fout en geen reviewvraag).
    assert "**INT-02** · ⏸️ Niet beoordeeld" in "\n".join(shown["markdown"])
    assert NE_CONTEXT in "\n".join(shown["warning"])
    assert NE_CONTEXT not in "\n".join(shown["error"] + shown["text"])
