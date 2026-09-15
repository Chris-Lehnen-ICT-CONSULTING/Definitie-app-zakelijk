"""DEF-622: `overall_score=None` en `rule_results` overleven de transports.

Reviewbevinding 5 op de contractcommit: `ServiceAdapter.normalize_validation`
maakte van "niet beschikbaar" (None) alsnog 0.0 en liet `rule_results`
vallen — precies de impliciete nul die B-06 verbiedt, op het pad dat de
Generator-tab rendert.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from services.service_factory import ServiceAdapter

pytestmark = [pytest.mark.unit]


@pytest.fixture
def adapter() -> ServiceAdapter:
    container = MagicMock()
    container.orchestrator.return_value = MagicMock()
    return ServiceAdapter(container)


def _resultaat() -> dict:
    return {
        "version": "1.3.0",
        "validation_status": "validated",
        "overall_score": None,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": ["CON-01"],
        "detailed_scores": {"taal": 0.9, "samenhang": None},
        "rule_statuses": {"CON-01": "pass"},
        "rule_results": {
            "CON-01": {
                "status": "pass",
                "score": None,
                "contract_version": "con01/1",
                "fingerprint": "abc",
                "parts": [],
                "review": None,
            }
        },
        "review_required": [],
        "acceptance_gate": {
            "status": "blocked",
            "acceptable": False,
            "gates_failed": ["overall_score_unavailable"],
            "gates_passed": [],
            "reasons": ["totaalscore niet beschikbaar"],
        },
        "system": {"correlation_id": "00000000-0000-4000-8000-000000000000"},
    }


def test_niet_beschikbare_totaalscore_blijft_none(adapter):
    genormaliseerd = adapter.normalize_validation(_resultaat())
    assert genormaliseerd["overall_score"] is None
    assert genormaliseerd["is_acceptable"] is False


def test_deeluitkomsten_en_gate_reizen_mee(adapter):
    genormaliseerd = adapter.normalize_validation(_resultaat())
    assert genormaliseerd["rule_results"]["CON-01"]["fingerprint"] == "abc"
    assert genormaliseerd["rule_statuses"] == {"CON-01": "pass"}
    assert genormaliseerd["detailed_scores"]["samenhang"] is None
    assert genormaliseerd["acceptance_gate"]["gates_failed"] == [
        "overall_score_unavailable"
    ]


def test_ontbrekende_score_blijft_de_legacy_default(adapter):
    """Alleen een expliciete None is 'niet beschikbaar'; ontbreken blijft 0.0."""
    genormaliseerd = adapter.normalize_validation({"is_acceptable": True})
    assert genormaliseerd["overall_score"] == 0.0
    assert "rule_results" not in genormaliseerd
