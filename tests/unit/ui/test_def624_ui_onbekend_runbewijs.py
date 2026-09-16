"""DEF-624: de gedeelde weergave bij ontbrekend of ongeldig runbewijs.

`render_validation_detailed_list` stopte alleen bij een expliciete
`validation_unknown`; een resultaat zonder status liep door naar de gate en
de groene regels. Nu stopt de weergave op elke niet-uitgevoerde run, met een
reden die klopt: een ontbrekende status is géén "niet alle toetsregels
konden worden geladen" — dat zou de oorzaak bij de regelset leggen terwijl
er simpelweg geen run is vastgelegd.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    UNKNOWN_REASON_VALIDATION_ERROR,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)

pytestmark = [pytest.mark.unit]


def _resultaat(**extra: Any) -> dict[str, Any]:
    basis: dict[str, Any] = {
        "version": "2.0.0",
        "overall_score": 0.95,
        "is_acceptable": True,
        "violations": [
            {
                "code": "VAL-STR-001",
                "rule_id": "STR-01",
                "severity": "error",
                "message": "oude overtreding",
            }
        ],
        "passed_rules": ["CON-01"],
        "rule_statuses": {"CON-01": "pass", "STR-01": "fail"},
        "acceptance_gate": {"status": "pass", "acceptable": True, "reasons": []},
        "system": {"correlation_id": "3f8c1a2e-0000-4000-8000-000000000000"},
    }
    basis.update(extra)
    return basis


class _Expander:
    def __init__(self, uitvoer: list[str], titel: str, **_kw: Any) -> None:
        uitvoer.append(f"[expander] {titel}")

    def __enter__(self) -> _Expander:
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def _vang(monkeypatch: pytest.MonkeyPatch) -> tuple[list[str], dict[str, list[str]]]:
    """Alle tekstuitvoer, plus per API apart (om groen van neutraal te scheiden)."""
    from ui.components import validation_view

    alles: list[str] = []
    per_api: dict[str, list[str]] = {}
    for api in ("markdown", "info", "warning", "success", "error", "write", "text"):
        per_api[api] = []

        def _vang_api(t: Any, *a: Any, _api: str = api, **kw: Any) -> None:
            alles.append(str(t))
            per_api[_api].append(str(t))

        monkeypatch.setattr(validation_view.st, api, _vang_api, raising=False)
    monkeypatch.setattr(
        validation_view.st,
        "expander",
        lambda titel, **kw: _Expander(alles, titel, **kw),
        raising=False,
    )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    for helper in ("_calculate_validation_stats", "_build_detailed_assessment"):
        monkeypatch.setattr(
            validation_view,
            helper,
            lambda *a, _n=helper, **kw: pytest.fail(f"{_n} aangeroepen zonder run"),
        )
    return alles, per_api


def _render(resultaat: dict[str, Any], **kw: Any) -> None:
    from ui.components import validation_view

    validation_view.render_validation_detailed_list(
        resultaat,
        key_prefix="def624",
        show_toggle=False,
        gate={"status": "pass", "acceptable": True, "reasons": []},
        **kw,
    )


@pytest.mark.parametrize(
    "invoer",
    [
        pytest.param({}, id="status_afwezig"),
        pytest.param({"validation_status": None}, id="status_null"),
        pytest.param({"validation_status": "VALIDATED"}, id="status_ongeldig"),
    ],
)
def test_zonder_runbewijs_geen_gate_geen_groen_en_de_juiste_reden(
    monkeypatch: pytest.MonkeyPatch, invoer: dict[str, Any]
) -> None:
    alles, per_api = _vang(monkeypatch)

    _render(_resultaat(**invoer))

    samen = "\n".join(alles).lower()
    assert "niet te bepalen" in samen, alles
    assert "runbewijs" in samen or "validation_status" in samen, alles
    # Niet toeschrijven aan een incomplete regelset: dat is een andere oorzaak.
    assert "toetsregels konden" not in samen, alles
    assert "geladen" not in samen, alles
    assert not any(m in samen for m in ("gate:", "gates:", "overall score")), alles
    assert per_api["success"] == [], per_api["success"]
    assert "beoordelingsdekking" not in samen


def test_ontbrekende_status_toont_de_oude_bevindingen_niet_als_oordeel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Beschikbaar voor uitleg, niet als actuele geldige verklaring."""
    alles, per_api = _vang(monkeypatch)

    _render(_resultaat())

    samen = "\n".join(alles)
    assert "STR-01" in samen and "oude overtreding" in samen, alles
    assert any("geen actuele toetsing" in t.lower() for t in alles), alles
    # Neutraal getoond: niet als rode fout, niet als groen succes.
    assert per_api["error"] == [] and per_api["success"] == []


def test_ruleset_incomplete_houdt_zijn_eigen_reden_en_telling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alles, _ = _vang(monkeypatch)

    _render(
        _resultaat(
            validation_status=VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
            validation_readiness={"loaded_total": 7, "expected_total": 53},
            violations=[],
            passed_rules=[],
            rule_statuses={},
            overall_score=0.0,
            is_acceptable=False,
        )
    )

    samen = "\n".join(alles).lower()
    assert "toetsregels" in samen and "7 van 53" in samen, alles
    assert "runbewijs" not in samen, alles


def test_technische_fout_noemt_de_fout(monkeypatch: pytest.MonkeyPatch) -> None:
    alles, _ = _vang(monkeypatch)

    _render(
        _resultaat(
            validation_status=VALIDATION_STATUS_UNKNOWN,
            unknown_reason=UNKNOWN_REASON_VALIDATION_ERROR,
            system={"correlation_id": "x", "error": "Service timeout"},
            overall_score=0.0,
            is_acceptable=False,
        )
    )

    samen = "\n".join(alles).lower()
    assert "niet te bepalen" in samen
    assert "technisch" in samen and "service timeout" in samen, alles


def test_validated_resultaat_rendert_nog_steeds_de_uitkomsten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tegenhanger: de stop mag een echte run niet onderdrukken."""
    from ui.components import validation_view

    getoond: list[str] = []
    for api in ("markdown", "info", "warning", "success", "error", "write", "text"):
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, **kw: getoond.append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    monkeypatch.setattr(
        validation_view,
        "_build_detailed_assessment",
        lambda *a, **kw: ["✅ CON-01: OK"],
    )

    validation_view.render_validation_detailed_list(
        _resultaat(validation_status=VALIDATION_STATUS_VALIDATED),
        key_prefix="def624_ok",
        show_toggle=False,
    )

    samen = "\n".join(getoond)
    assert "Beoordelingsdekking" in samen
    assert "Gate: toegestaan" in samen
    assert "✅ CON-01: OK" in samen


def test_generator_tab_ziet_een_ontbrekende_status_als_onbepaald() -> None:
    from ui.components.definition_generator_tab import _validatie_is_onbepaald

    assert _validatie_is_onbepaald({"validation_details": _resultaat()}) is True
    assert (
        _validatie_is_onbepaald(
            {"validation_details": _resultaat(validation_status="ok")}
        )
        is True
    )
    assert (
        _validatie_is_onbepaald(
            {
                "validation_details": _resultaat(
                    validation_status=VALIDATION_STATUS_VALIDATED
                )
            }
        )
        is False
    )
    # Geen dict: bestaand gedrag (niets te beoordelen, geen crash).
    assert _validatie_is_onbepaald(None) is False


def test_reden_zonder_status_wordt_niet_verzonnen_bij_unknown_zonder_reden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Een expliciete unknown zonder reden blijft generiek, met de telling."""
    alles, _ = _vang(monkeypatch)

    _render(
        _resultaat(
            validation_status=VALIDATION_STATUS_UNKNOWN,
            validation_readiness={"loaded_total": 7, "expected_total": 53},
            violations=[],
            passed_rules=[],
            rule_statuses={},
            overall_score=0.0,
            is_acceptable=False,
        )
    )
    samen = "\n".join(alles)
    assert "niet te bepalen" in samen.lower()
    assert "7" in samen and "53" in samen
    assert UNKNOWN_REASON_CONTRACT_STATUS_MISSING not in samen
