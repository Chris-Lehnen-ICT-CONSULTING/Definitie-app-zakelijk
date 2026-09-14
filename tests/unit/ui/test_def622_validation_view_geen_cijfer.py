"""DEF-622: de gedeelde validatieweergave bij een niet-beschikbare totaalscore.

Reviewbevinding 6 op de contractcommit: `render_validation_detailed_list`
deed `float(None)` en crashte vóór er één regeluitkomst was getoond. De
weergave moet "niet beschikbaar" tonen, de gate-blokkade benoemen en de
CON-01-deeluitkomsten (aanleiding, reden, vervolgstap) doorrenderen (B-08).
"""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = [pytest.mark.unit]


def _resultaat(**extra: Any) -> dict[str, Any]:
    basis: dict[str, Any] = {
        "version": "1.3.0",
        "validation_status": "validated",
        "overall_score": None,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {"taal": 0.9, "samenhang": None},
        "rule_statuses": {"CON-01": "review_required"},
        "rule_results": {
            "CON-01": {
                "status": "review_required",
                "score": None,
                "contract_version": "con01/1",
                "fingerprint": "abc",
                "parts": [
                    {
                        "id": "context_aanwezig",
                        "status": "pass",
                        "evidence": None,
                        "context_value": None,
                        "field": None,
                        "position": None,
                        "reason": "Er is minstens één contextwaarde vastgelegd.",
                        "action": "Geen actie nodig.",
                    },
                    {
                        "id": "naam:organisatorische_context:stichting zilver@36",
                        "status": "review_required",
                        "evidence": "Stichting Zilver",
                        "context_value": "Stichting Zilver",
                        "field": "organisatorische_context",
                        "position": 36,
                        "reason": "De naam 'Stichting Zilver' staat in de definitiezin.",
                        "action": "Laat de expert de functie van de naam beoordelen.",
                    },
                ],
                "review": None,
            }
        },
        "acceptance_gate": {
            "status": "blocked",
            "acceptable": False,
            "gates_failed": ["overall_score_unavailable"],
            "gates_passed": [],
            "reasons": ["totaalscore niet beschikbaar: regel(s) zonder cijfer CON-01"],
        },
        "system": {"correlation_id": "3f8c1a2e-0000-4000-8000-000000000000"},
    }
    basis.update(extra)
    return basis


def _vang_uitvoer(monkeypatch: pytest.MonkeyPatch, view: Any) -> list[str]:
    getoond: list[str] = []
    for api in ("markdown", "info", "warning", "success", "error", "write"):
        monkeypatch.setattr(
            view.st, api, lambda t, *a, **kw: getoond.append(str(t)), raising=True
        )

    class _Expander:
        def __init__(self, titel: str, **_kw: Any) -> None:
            getoond.append(str(titel))

        def __enter__(self) -> _Expander:
            return self

        def __exit__(self, *exc: Any) -> bool:
            return False

    monkeypatch.setattr(view.st, "expander", _Expander, raising=True)
    return getoond


def test_niet_beschikbare_score_crasht_niet_en_toont_uitkomsten(monkeypatch):
    from ui.components import validation_view

    getoond = _vang_uitvoer(monkeypatch, validation_view)
    validation_view.render_validation_detailed_list(
        _resultaat(), key_prefix="def622", show_toggle=False
    )
    samen = "\n".join(getoond).lower()
    assert "niet beschikbaar" in samen
    assert "0.00" not in samen
    # De gate-blokkade blijft zichtbaar…
    assert "blokkade" in samen or "gate" in samen
    # …en de CON-01-deeluitkomsten met aanleiding, reden en vervolgstap.
    assert "stichting zilver" in samen
    assert "laat de expert de functie van de naam beoordelen" in samen
    assert "nog te beoordelen" in samen
