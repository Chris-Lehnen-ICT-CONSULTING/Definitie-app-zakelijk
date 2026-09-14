"""CON-01: onderscheidende productie-uitkomsten volgens B-01/B-04/B-06/B-08.

Alle tests lopen door de echte `ModularValidationService` met de echte
regelset, zodat het contract (rule_results, fingerprint, deeluitkomsten en
het ontbreken van een cijfer) op de productiegrens wordt bewezen.
"""

from unittest.mock import patch

import pytest

from services.null_repository import NullDefinitionRepository
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


@pytest.fixture
def validator():
    return ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )


async def assess(validator, text, context):
    return await validator.validate_definition(
        begrip="keurmerk", text=text, context=context
    )


@pytest.mark.parametrize("context", [{}, {"organisatorische_context": [" ", ""]}])
async def test_no_meaningful_context_is_explicit_failure(validator, context):
    result = await assess(
        validator, "kwaliteitsmerk voor gecontroleerde producten", context
    )
    assert result["rule_statuses"]["CON-01"] == "fail"
    detail = result["rule_results"]["CON-01"]
    assert detail["score"] is None
    assert detail["parts"][0]["action"]


async def test_selected_name_is_open_instead_of_automatic_rejection(validator):
    result = await assess(
        validator,
        "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend",
        {"organisatorische_context": ["Stichting Zilver"]},
    )
    assert result["rule_statuses"]["CON-01"] == "review_required"
    part = result["rule_results"]["CON-01"]["parts"][1]
    assert part["evidence"] == "Stichting Zilver"
    assert part["reason"] and part["action"]
    assert result["overall_score"] is None


async def test_generic_legal_word_without_selected_name_does_not_fail(validator):
    result = await assess(
        validator,
        "juridisch instrument voor de beoordeling van producten",
        {"wettelijke_basis": ["Regeling Zilver"]},
    )
    assert result["rule_statuses"]["CON-01"] == "pass"
    assert result["rule_results"]["CON-01"]["score"] is None
    assert result["overall_score"] is None


async def test_reviewed_registration_and_open_name_remain_visible_together(validator):
    text = "merk binnen Stichting Zilver en Stichting Goud"
    context = {"organisatorische_context": ["Stichting Zilver", "Stichting Goud"]}
    first = await assess(validator, text, context)
    detail = first["rule_results"]["CON-01"]
    silver = next(p for p in detail["parts"] if p.get("evidence") == "Stichting Zilver")
    context["context_review"] = {
        "fingerprint": detail["fingerprint"],
        "actor": "synthetische-expert",
        "decisions": {
            silver["id"]: {
                "function": "registration",
                "reason": "Deze frase noemt uitsluitend de registratieomgeving.",
            }
        },
    }
    result = await assess(validator, text, context)
    assert result["rule_statuses"]["CON-01"] == "fail"
    parts = result["rule_results"]["CON-01"]["parts"]
    assert {p["status"] for p in parts} >= {"fail", "review_required"}


async def test_necessary_name_review_expires_when_text_changes(validator):
    text = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
    context = {"organisatorische_context": ["Stichting Zilver"]}
    first = await assess(validator, text, context)
    detail = first["rule_results"]["CON-01"]
    context["context_review"] = {
        "fingerprint": detail["fingerprint"],
        "actor": "synthetische-expert",
        "decisions": {
            detail["parts"][1]["id"]: {
                "function": "necessary",
                "reason": "De exclusieve uitgever identificeert dit keurmerk.",
            }
        },
    }
    reviewed = await assess(validator, text, context)
    assert reviewed["rule_statuses"]["CON-01"] == "pass"
    changed = await assess(validator, text + " binnen de registratieomgeving", context)
    assert changed["rule_statuses"]["CON-01"] == "review_required"


async def test_technical_error_is_visible_separately_and_is_no_violation(validator):
    """B-06/B-08: een technische fout is geen inhoudelijk 'Voldoet niet'."""
    with patch(
        "services.validation.evaluators.context_metadata."
        "ContextMetadataEvaluator.evaluate",
        side_effect=RuntimeError("synthetische storing"),
    ):
        result = await assess(
            validator,
            "kwaliteitsmerk voor gecontroleerde producten",
            {"organisatorische_context": ["Stichting Zilver"]},
        )
    assert result["rule_statuses"]["CON-01"] == "error"
    detail = result["rule_results"]["CON-01"]
    assert detail["status"] == "error"
    assert detail["score"] is None
    statuses = {p["status"] for p in detail["parts"]}
    assert statuses == {"error"}
    part = detail["parts"][0]
    assert part["action"]
    # Geen interne foutdetails als normuitleg (B-08).
    assert "synthetische storing" not in part["reason"]
    assert not any(v.get("code") == "CON-01" for v in result["violations"])


async def test_evidence_is_found_text_and_selected_value_is_kept_apart(validator):
    result = await assess(
        validator,
        "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend",
        {"organisatorische_context": ["STICHTING ZILVER"]},
    )
    part = next(
        p for p in result["rule_results"]["CON-01"]["parts"] if p.get("evidence")
    )
    assert part["evidence"] == "Stichting Zilver"
    assert part["context_value"] == "STICHTING ZILVER"
    assert part["field"] == "organisatorische_context"


async def test_same_name_on_two_positions_gives_two_separate_parts(validator):
    """Dezelfde naam kan op twee plekken een verschillende functie hebben."""
    result = await assess(
        validator,
        "merk van Stichting Zilver dat Stichting Zilver toekent",
        {"organisatorische_context": ["Stichting Zilver"]},
    )
    parts = [p for p in result["rule_results"]["CON-01"]["parts"] if p.get("evidence")]
    assert len(parts) == 2
    assert parts[0]["id"] != parts[1]["id"]
    assert parts[0]["position"] < parts[1]["position"]


async def test_fingerprint_binds_term_text_and_context(validator):
    text = "kwaliteitsmerk voor gecontroleerde producten"
    context = {"organisatorische_context": ["Stichting Zilver"]}
    basis = (await assess(validator, text, context))["rule_results"]["CON-01"]
    andere_term = await validator.validate_definition(
        begrip="waarmerk", text=text, context=context
    )
    andere_context = await assess(
        validator, text, {"organisatorische_context": ["Stichting Goud"]}
    )
    zelfde = await assess(
        validator, text, {"organisatorische_context": [" stichting zilver "]}
    )
    assert basis["fingerprint"] != andere_term["rule_results"]["CON-01"]["fingerprint"]
    assert (
        basis["fingerprint"] != andere_context["rule_results"]["CON-01"]["fingerprint"]
    )
    assert basis["fingerprint"] == zelfde["rule_results"]["CON-01"]["fingerprint"]


@pytest.mark.parametrize(
    "review",
    [
        {"actor": "", "reason": "Exclusieve uitgever."},
        {"actor": "synthetische-expert", "reason": "  "},
    ],
)
async def test_review_without_actor_or_reason_does_not_count(validator, review):
    text = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
    context = {"organisatorische_context": ["Stichting Zilver"]}
    first = await assess(validator, text, context)
    detail = first["rule_results"]["CON-01"]
    naam = next(p for p in detail["parts"] if p.get("evidence"))
    context["context_review"] = {
        "fingerprint": detail["fingerprint"],
        "actor": review["actor"],
        "decisions": {
            naam["id"]: {"function": "necessary", "reason": review["reason"]}
        },
    }
    result = await assess(validator, text, context)
    assert result["rule_statuses"]["CON-01"] == "review_required"


async def test_uppercase_acronym_does_not_match_ordinary_lowercase_word(validator):
    """`OM` als context mag niet elke 'om' in de tekst tot naamsignaal maken."""
    result = await assess(
        validator,
        "kwaliteitsmerk om producten te onderscheiden",
        {"organisatorische_context": ["OM"]},
    )
    assert result["rule_statuses"]["CON-01"] == "pass"
    assert not any(p.get("evidence") for p in result["rule_results"]["CON-01"]["parts"])
