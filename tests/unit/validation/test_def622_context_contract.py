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


@pytest.mark.parametrize(
    "versie",
    ["ontbreekt", None, True, [], {}, "invalid", 2.5, 2, "3", 3.0],
    ids=[
        "ontbreekt",
        "None",
        "True",
        "lijst",
        "dict",
        "tekst",
        "float",
        "ander",
        "cijfertekst",
        "float-gelijk",
    ],
)
async def test_review_without_valid_version_does_not_count_for_versioned_record(
    validator, versie
):
    """V2b: draagt het record een versie, dan telt een beoordeling zonder
    geldig (gelijk) versienummer niet; alleen bij een record zónder versie
    (los tekstfragment) blijft de vingerafdruk de enige binding."""
    text = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
    context = {
        "organisatorische_context": ["Stichting Zilver"],
        "definition_version": 3,
    }
    first = await assess(validator, text, context)
    detail = first["rule_results"]["CON-01"]
    review = {
        "fingerprint": detail["fingerprint"],
        "actor": "synthetische-expert",
        "decisions": {
            detail["parts"][1]["id"]: {
                "function": "necessary",
                "reason": "De exclusieve uitgever identificeert dit keurmerk.",
            }
        },
    }
    if versie != "ontbreekt":
        review["version_number"] = versie
    context["context_review"] = review

    result = await assess(validator, text, context)
    assert result["rule_statuses"]["CON-01"] == "review_required"
    samenvatting = result["rule_results"]["CON-01"]["review"]
    assert samenvatting["applied"] is False
    assert "versie" in samenvatting["reason"]

    # Gelijk versienummer: de beoordeling telt.
    context["context_review"] = {**review, "version_number": 3}
    assert (await assess(validator, text, context))["rule_statuses"]["CON-01"] == "pass"
    # Een misvormde recordversie ontgrendelt de vingerafdruk-alleen-semantiek
    # niet: het record is versiegebonden, de vergelijking is onmogelijk.
    for misvormd in ("3", 3.0, True):
        context["definition_version"] = misvormd
        misvormd_resultaat = await assess(validator, text, context)
        assert misvormd_resultaat["rule_statuses"]["CON-01"] == "review_required"
        assert (
            "versie" in misvormd_resultaat["rule_results"]["CON-01"]["review"]["reason"]
        )
    # Zonder recordversie (los, onopgeslagen fragment) blijft de vingerafdruk
    # de enige binding.
    context.pop("definition_version")
    context["context_review"] = review
    assert (await assess(validator, text, context))["rule_statuses"]["CON-01"] == "pass"


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
        # Reviewbevinding 2: ongeldige typen mogen niet via str(...) tot een
        # 'geldige' beoordelaar of onderbouwing worden.
        {"actor": True, "reason": True},
        {"actor": [""], "reason": "Exclusieve uitgever."},
        {"actor": "synthetische-expert", "reason": ["Exclusieve uitgever."]},
        {"actor": 1, "reason": "Exclusieve uitgever."},
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


@pytest.mark.parametrize(
    ("tekst", "waarden", "verwacht"),
    [
        # Reviewbevinding 1: de detectie volgt dezelfde casefold-normalisatie
        # als de context zelf; de opgeslagen schrijfwijze bepaalt niet of een
        # gewoon woord een signaal is (B-04: signaal, mens beoordeelt).
        ("kwaliteitsmerk om producten te onderscheiden", ("OM", "om"), "om"),
        ("merk dat dji toekent", ("DJI", "dji"), "dji"),
        (
            "merk van Stichting Straße",
            ("Stichting Straße", "Stichting STRASSE"),
            "Stichting Straße",
        ),
    ],
)
async def test_detection_follows_casefold_regardless_of_stored_spelling(
    validator, tekst, waarden, verwacht
):
    uitkomsten = []
    for waarde in waarden:
        result = await assess(validator, tekst, {"organisatorische_context": [waarde]})
        detail = result["rule_results"]["CON-01"]
        signalen = [p["evidence"] for p in detail["parts"] if p.get("evidence")]
        uitkomsten.append(
            (result["rule_statuses"]["CON-01"], signalen, detail["fingerprint"])
        )
    statussen = {u[0] for u in uitkomsten}
    assert statussen == {"review_required"}, uitkomsten
    assert all(u[1] == [verwacht] for u in uitkomsten), uitkomsten
    # Gelijke canonieke context → gelijke vingerafdruk én gelijke beoordeling.
    assert len({u[2] for u in uitkomsten}) == 1


async def test_evidence_binds_to_exact_record_text_across_cleaning(validator):
    """Reviewbevinding 3: bewijs en vingerafdruk horen bij de exacte recordtekst.

    Een cleaningstap die alleen witruimte strept mag een eerdere beoordeling
    niet geldig houden voor een gewijzigde recordtekst, en de gerapporteerde
    positie hoort bij de tekst die de expert ziet.
    """

    class _Strip:
        def clean_text(self, text: str) -> str:
            return text.strip()

    validator.cleaning_service = _Strip()
    context = {"organisatorische_context": ["Stichting Zilver"]}
    basis = await assess(validator, "merk dat Stichting Zilver toekent", context)
    detail = basis["rule_results"]["CON-01"]
    naam = next(p for p in detail["parts"] if p.get("evidence"))
    assert naam["position"] == 9

    context["context_review"] = {
        "fingerprint": detail["fingerprint"],
        "actor": "synthetische-expert",
        "decisions": {naam["id"]: {"function": "necessary", "reason": "Uitgever."}},
    }
    assert (await assess(validator, "merk dat Stichting Zilver toekent", context))[
        "rule_statuses"
    ]["CON-01"] == "pass"

    verschoven = await assess(validator, "  merk dat Stichting Zilver toekent", context)
    verschoven_detail = verschoven["rule_results"]["CON-01"]
    assert verschoven_detail["fingerprint"] != detail["fingerprint"]
    assert verschoven["rule_statuses"]["CON-01"] == "review_required"
    assert (
        next(p for p in verschoven_detail["parts"] if p.get("evidence"))["position"]
        == 11
    )


async def test_partial_failure_keeps_proven_parts_visible(validator):
    """Reviewbevinding 4: een fout in één deelcontrole wist de andere niet."""
    from domain.context import contract as contractmodule

    text = "merk binnen Stichting Zilver en Stichting Goud"
    context = {"organisatorische_context": ["Stichting Zilver", "Stichting Goud"]}
    first = await assess(validator, text, context)
    detail = first["rule_results"]["CON-01"]
    zilver = next(p for p in detail["parts"] if p.get("evidence") == "Stichting Zilver")
    context["context_review"] = {
        "fingerprint": detail["fingerprint"],
        "actor": "synthetische-expert",
        "decisions": {
            zilver["id"]: {"function": "registration", "reason": "Alleen registratie."}
        },
    }

    origineel = contractmodule._naamdeel

    def _faalt_op_goud(treffer, beslissing):
        if treffer.gevonden == "Stichting Goud":
            raise RuntimeError("synthetische deelstoring")
        return origineel(treffer, beslissing)

    with patch.object(contractmodule, "_naamdeel", side_effect=_faalt_op_goud):
        result = await assess(validator, text, context)

    assert result["rule_statuses"]["CON-01"] == "fail"
    parts = {p["id"]: p for p in result["rule_results"]["CON-01"]["parts"]}
    assert parts[zilver["id"]]["status"] == "fail"
    foutdelen = [p for p in parts.values() if p["status"] == "error"]
    assert len(foutdelen) == 1 and foutdelen[0]["evidence"] == "Stichting Goud"
    assert "synthetische deelstoring" not in foutdelen[0]["reason"]
    assert result["rule_results"]["CON-01"]["fingerprint"] == detail["fingerprint"]
    assert any(v.get("code") == "CON-01" for v in result["violations"])

    # Zonder bewezen overtreding blijft de regel als geheel een technische
    # fout, mét de afgeronde onderdelen zichtbaar.
    context.pop("context_review")
    with patch.object(contractmodule, "_naamdeel", side_effect=_faalt_op_goud):
        alleen_fout = await assess(validator, text, context)
    assert alleen_fout["rule_statuses"]["CON-01"] == "error"
    statussen = {p["status"] for p in alleen_fout["rule_results"]["CON-01"]["parts"]}
    assert statussen == {"pass", "review_required", "error"}
    assert not any(v.get("code") == "CON-01" for v in alleen_fout["violations"])
