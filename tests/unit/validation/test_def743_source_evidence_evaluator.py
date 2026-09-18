"""CON-02 (DEF-743): de actieve bronbewijs-evaluator op de productiegrens.

Alle tests lopen door de echte `ModularValidationService` met de echte
regelset (53 records, contract uit de root-SSOT), zodat het runtimecontract
(rule_results, rule_statuses, geen cijfer, geen totaalscore, geen
herstelroute) op de productiegrens wordt bewezen. De AI-beoordeling is hier
een gestructureerd, al gevalideerd document (replay); de service die haar
verkrijgt heeft eigen tests.
"""

import pytest

from domain.sources.contract import (
    CONTRACTVERSIE,
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_UITZONDERING_GEEN_BRON,
    ONDERDEEL_VERWIJZING,
    REVIEW_TYPE_CORRECTIE,
    REVIEW_TYPE_GEEN_BRON,
    REVIEW_TYPE_VERWIJZING,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.null_repository import NullDefinitionRepository
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import (
    AutomationStatus,
    EvaluatorType,
    Executability,
    ScorePolicy,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "toezichthouder"
TEKST = (
    "Persoon die bij of krachtens wettelijk voorschrift is belast met het houden "
    "van toezicht op de naleving van het bepaalde bij of krachtens enig wettelijk "
    "voorschrift."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Inspectie"],
    "juridische_context": ["bestuursrecht"],
    "wettelijke_basis": ["Synthetische Bestuurswet"],
}
PASSAGE = (
    "Artikel 5:11. Onder toezichthouder wordt verstaan: een persoon, bij of krachtens "
    "wettelijk voorschrift belast met het houden van toezicht op de naleving van het "
    "bepaalde bij of krachtens enig wettelijk voorschrift."
)
BRON = {
    "provider": "documents",
    "doc_id": "wet-11",
    "filename": "synthetische-bestuurswet.txt",
    "citation_label": "art. 5:11",
    "bron_type": "wet",
    "url": "https://intern.example/bestuurswet#art-5-11",  # DEF-806
    "snippet": PASSAGE,
    "score": 1.0,
}
CITAAT = "bij of krachtens wettelijk voorschrift belast met het houden van toezicht"


@pytest.fixture(scope="module")
def validator():
    return ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )


def _fp(bronnen=(BRON,), tekst=TEKST, peildatum=None):
    return bereken_bronvingerafdruk(
        BEGRIP, tekst, CONTEXT, list(bronnen), peildatum=peildatum
    )


def _deel(status, reason="synthetische reden", quote=CITAAT, **extra):
    return {
        "status": status,
        "reason": reason,
        "uncertainty": None,
        "evidence": (
            [{"source_id": "doc:wet-11", "quote": quote, "locator": "art. 5:11"}]
            if quote
            else []
        ),
        **extra,
    }


def _assessment(
    fingerprint=None, gezag="pass", steun="pass", verwijzing="pass", **overrides
):
    doc = {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "con02-assess/1",
        "fingerprint": fingerprint or _fp(),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-15T12:00:00+00:00",
        "attribution": {
            "provider": "fake",
            "model": "fake-model",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 1,
        },
        "peildatum": None,
        "sources": [b.als_dict() for b in canoniseer_bronnen([BRON])],
        "parts": {
            ONDERDEEL_GEZAG: _deel(
                gezag,
                sources=[
                    {
                        "source_id": "doc:wet-11",
                        "profile": "wet_regelgeving",
                        "applicable": True,
                        "reason": "x",
                    }
                ],
            ),
            ONDERDEEL_STEUN: _deel(
                steun,
                claims=[
                    {
                        "aspect": "kenmerk",
                        "text": "toezicht op de naleving",
                        "supported": True,
                        "source_id": "doc:wet-11",
                    }
                ],
            ),
            ONDERDEEL_VERWIJZING: _deel(
                verwijzing,
                quote="Artikel 5:11",
                sources=[{"source_id": "doc:wet-11", "locatable": True, "reason": "x"}],
            ),
        },
        "rejected": [],
        "raw_response_sha256": None,
    }
    doc.update(overrides)
    return doc


async def _valideer(validator, *, tekst=TEKST, context=None):
    ctx = {**CONTEXT, **(context or {})}
    return await validator.validate_definition(begrip=BEGRIP, text=tekst, context=ctx)


def _con02(result):
    return result["rule_statuses"]["CON-02"], result["rule_results"]["CON-02"]


def _part(detail, onderdeel):
    return next(p for p in detail["parts"] if p["id"] == onderdeel)


async def test_regelrecord_is_broninhoudelijk_en_zonder_cijfer(validator):
    record = validator._snapshot.rule_records["CON-02"]
    assert record.evaluator is EvaluatorType.SOURCE_EVIDENCE
    assert record.executability is Executability.JUDGMENT
    assert record.automation_status is AutomationStatus.AUTOMATED
    assert record.score_policy is ScorePolicy.NO_SCORE
    for veld in (
        "herkenbaar_patronen",
        "bronpatronen_specifiek",
        "bronpatronen_algemeen",
    ):
        assert veld not in record.data
    assert "citatie" in record.get("toelichting").casefold()
    # Bevinding 7: het foute voorbeeld verliest een werkelijk in de gegeven
    # passage aanwezige categorie; het maakt geen disjunctvoorwaarde algemeen.
    (fout,) = record.get("foute_voorbeelden")
    assert (
        "orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld" in fout
    )
    assert "persoon of college met enig openbaar gezag" in fout
    assert "vereist 'krachtens publiekrecht ingesteld'" not in fout


async def test_geen_bronnen_is_expliciet_open_ook_met_bronwoord(validator):
    for tekst in (TEKST, TEKST + " Zoals bepaald in de wet, conform de regeling."):
        result = await _valideer(validator, tekst=tekst)
        status, detail = _con02(result)
        assert status == "review_required"
        assert detail["score"] is None
        assert [p["id"] for p in detail["parts"]] == [
            ONDERDEEL_GEZAG,
            ONDERDEEL_STEUN,
            ONDERDEEL_VERWIJZING,
        ]
        assert all(p["status"] == "review_required" for p in detail["parts"])
        assert not any(v.get("code") == "CON-02" for v in result["violations"])
        assert "CON-02" not in result["passed_rules"]
        assert result["overall_score"] is None
        assert result["detailed_scores"]["samenhang"] is None
        assert any(r["rule_id"] == "CON-02" for r in result["review_required"])


async def test_bronnen_zonder_beoordeling_blijven_open_niet_pass(validator):
    status, detail = _con02(
        await _valideer(validator, context={"provenance_sources": [BRON]})
    )
    assert status == "review_required"
    assert "niet uitgevoerd" in detail["review"]["assessment"]["reason"]


async def test_gegronde_beoordeling_geeft_pass_zonder_cijfer_of_totaalscore(validator):
    result = await _valideer(
        validator,
        context={"provenance_sources": [BRON], "source_assessment": _assessment()},
    )
    status, detail = _con02(result)
    assert status == "pass"
    assert "CON-02" in result["passed_rules"]
    assert detail["score"] is None
    assert detail["fingerprint"] == _fp()
    assert _part(detail, ONDERDEEL_GEZAG)["evidence"] == CITAAT
    assert _part(detail, ONDERDEEL_GEZAG)["field"] == "source_assessment"
    assert detail["review"]["assessment"]["model"] == "fake-model"
    assert result["overall_score"] is None  # geen cijfer, ook niet via de rest


async def test_fail_met_bewijs_en_open_geven_violation_met_beide_zichtbaar(validator):
    result = await _valideer(
        validator,
        context={
            "provenance_sources": [BRON],
            "source_assessment": _assessment(
                steun="fail", verwijzing="review_required"
            ),
        },
    )
    status, detail = _con02(result)
    assert status == "fail"
    (violation,) = [v for v in result["violations"] if v["code"] == "CON-02"]
    assert violation["metadata"]["failing_parts"] == [ONDERDEEL_STEUN]
    assert violation["metadata"]["open_parts"] == [ONDERDEEL_VERWIJZING]
    assert violation["metadata"]["fingerprint"] == _fp()
    assert "bronwoord" not in (violation.get("suggestion") or "").casefold()
    assert "automatisch" in (violation.get("suggestion") or "").casefold()
    assert "CON-02" not in result["passed_rules"]
    assert _part(detail, ONDERDEEL_GEZAG)["status"] == "pass"


async def test_technische_fout_is_error_en_blokkeert(validator):
    result = await _valideer(
        validator,
        context={
            "provenance_sources": [BRON],
            "source_assessment": beoordeling_technische_fout(
                _fp(), "timeout", "AI timed out"
            ),
        },
    )
    status, detail = _con02(result)
    assert status == "error"
    assert all(p["status"] == "error" for p in detail["parts"])
    assert result["evaluation_coverage"]["error"] >= 1
    assert result["is_acceptable"] is False
    assert not any(v.get("code") == "CON-02" for v in result["violations"])


async def test_niet_beschikbare_dienst_is_open_met_reden(validator):
    status, detail = _con02(
        await _valideer(
            validator,
            context={
                "provenance_sources": [BRON],
                "source_assessment": beoordeling_niet_beschikbaar(_fp(), "geen dienst"),
            },
        )
    )
    assert status == "review_required"
    assert detail["review"]["assessment"]["status"] == "unavailable"


@pytest.mark.parametrize(
    "context",
    [
        {
            "provenance_sources": [BRON],
            "source_assessment": _assessment(fingerprint="0" * 64),
        },
        {
            "provenance_sources": [{**BRON, "citation_label": "art. 9"}],
            "source_assessment": _assessment(),
        },
        {
            "provenance_sources": [BRON],
            "source_assessment": _assessment(),
            "peildatum": "2026-01-01",
        },
        {
            "provenance_sources": [BRON],
            "source_assessment": _assessment(),
            "record_text": TEKST + " gewijzigd",
        },
    ],
)
async def test_stale_beoordeling_geeft_nooit_pass(validator, context):
    status, detail = _con02(await _valideer(validator, context=context))
    assert status == "review_required"
    assert detail["review"]["assessment"]["applied"] is False


async def test_vervalste_positieve_beoordeling_zonder_bewijs_geeft_geen_pass(validator):
    vervalst = _assessment()
    for onderdeel in vervalst["parts"].values():
        onderdeel["evidence"] = [
            {"source_id": "doc:wet-11", "quote": "verzonnen citaat"}
        ]
    status, _ = _con02(
        await _valideer(
            validator,
            context={"provenance_sources": [BRON], "source_assessment": vervalst},
        )
    )
    assert status == "review_required"


async def test_verwijzingsuitzondering_blijft_zichtbaar_open(validator):
    # DEF-806: de uitzondering geldt alleen voor een bron zónder hyperlink.
    zonder_link = {**BRON, "url": None}
    fp = _fp(bronnen=(zonder_link,))
    review = {
        "type": REVIEW_TYPE_VERWIJZING,
        "accepted": True,
        "actor": "synthetische-deskundige",
        "rationale": "Intern beschikbaar, geen hyperlink.",
        "version_number": 2,
        "fingerprint": fp,
        "reviewed_at": None,
        "source_id": "doc:wet-11",
        "content_hash": bereken_inhoudshash(PASSAGE),
        "source_version": None,
        "locator": "art. 5:11",
    }
    result = await _valideer(
        validator,
        context={
            "provenance_sources": [zonder_link],
            "source_assessment": _assessment(
                fingerprint=fp, verwijzing="review_required"
            ),
            "source_review": review,
            "definition_version": 2,
        },
    )
    status, detail = _con02(result)
    assert status == "review_required"
    verwijzing = _part(detail, ONDERDEEL_VERWIJZING)
    assert verwijzing["field"] == "source_review"
    assert verwijzing["evidence"] == "art. 5:11"
    assert detail["review"]["accepted_exception"] == "reference"
    assert "CON-02" not in result["passed_rules"]
    # Versieconflict: uitzondering vervalt, AI-oordeel blijft.
    result2 = await _valideer(
        validator,
        context={
            "provenance_sources": [zonder_link],
            "source_assessment": _assessment(
                fingerprint=fp, verwijzing="review_required"
            ),
            "source_review": review,
            "definition_version": 3,
        },
    )
    _, detail2 = _con02(result2)
    assert detail2["review"]["applied"] is False
    assert "versie" in detail2["review"]["reason"]
    assert _part(detail2, ONDERDEEL_VERWIJZING)["field"] == "source_assessment"


async def test_geen_passende_bron_uitzondering_is_extra_onderdeel(validator):
    review = {
        "type": REVIEW_TYPE_GEEN_BRON,
        "accepted": True,
        "actor": "synthetische-deskundige",
        "rationale": "Intern begrip zonder externe bron.",
        "version_number": None,
        "fingerprint": _fp(bronnen=()),
        "reviewed_at": None,
        "search": {
            "queries": ["toezichthouder"],
            "consulted": ["register"],
            "conclusion": "niets gevonden",
        },
    }
    status, detail = _con02(
        await _valideer(validator, context={"source_review": review})
    )
    assert status == "review_required"
    assert _part(detail, ONDERDEEL_UITZONDERING_GEEN_BRON)["field"] == "source_review"
    assert detail["review"]["accepted_exception"] == "no_source"


async def test_zonder_term_is_con02_niet_geevalueerd_nooit_pass(validator):
    result = await validator.validate_definition(
        begrip="", text=TEKST, context=dict(CONTEXT)
    )
    assert result["rule_statuses"]["CON-02"] == "not_evaluated"
    assert "CON-02" not in result["rule_results"]


async def test_evaluator_crash_wordt_technische_fout_zonder_cijfer(
    validator, monkeypatch
):
    from domain.sources import contract
    from services.validation.evaluators import source_evidence as evaluator_module

    def kapot(*_a, **_k):
        raise RuntimeError("synthetische crash")

    monkeypatch.setattr(evaluator_module, "beoordeel_bronbasis", kapot)
    result = await _valideer(validator, context={"provenance_sources": [BRON]})
    assert result["rule_statuses"]["CON-02"] == "error"
    assert result["rule_results"]["CON-02"]["status"] == "error"
    assert "CON-02" not in result.get("rule_scores", {})
    assert contract.CONTRACTVERSIE == "con02/1"


async def test_deskundige_correctie_van_een_onderdeel_op_de_productiegrens(validator):
    """part_correction: één onderdeel krijgt het deskundige oordeel mét gebonden bewijs."""
    correctie = {
        "type": REVIEW_TYPE_CORRECTIE,
        "accepted": True,
        "actor": "synthetische-deskundige",
        "rationale": "De wettekst dekt het kenmerk 'toezicht op de naleving' letterlijk.",
        "version_number": 2,
        "fingerprint": _fp(),
        "reviewed_at": "2026-09-15T14:00:00+00:00",
        "part_id": ONDERDEEL_STEUN,
        "status": "pass",
        "evidence": [
            {
                "source_id": "doc:wet-11",
                "content_hash": bereken_inhoudshash(PASSAGE),
                "source_version": None,
                "quote": "toezicht op de naleving",
                "locator": "art. 5:11",
            }
        ],
    }
    context = {
        "provenance_sources": [BRON],
        "source_assessment": _assessment(steun="review_required"),
        "source_review": correctie,
        "definition_version": 2,
    }
    result = await _valideer(validator, context=context)
    status, detail = _con02(result)
    assert (
        status == "pass"
    )  # de drie onderdelen zijn nu pass; de samenstelling volgt gewoon
    steun = _part(detail, ONDERDEEL_STEUN)
    assert steun["field"] == "source_review"
    assert steun["evidence"] == "toezicht op de naleving"
    assert detail["review"]["accepted_exception"] is None
    assert detail["review"]["applied_correction"]["part_id"] == ONDERDEEL_STEUN
    assert (
        detail["review"]["applied_correction"]["original"]["status"]
        == "review_required"
    )
    assert _part(detail, ONDERDEEL_GEZAG)["field"] == "source_assessment"
    # Vervalste claim (citaat niet in de bron) → correctie niet toegepast, AI-oordeel blijft.
    vervalst = {
        **correctie,
        "evidence": [{**correctie["evidence"][0], "quote": "verzonnen citaat"}],
    }
    status2, detail2 = _con02(
        await _valideer(validator, context={**context, "source_review": vervalst})
    )
    assert status2 == "review_required"
    assert detail2["review"]["applied"] is False
    assert _part(detail2, ONDERDEEL_STEUN)["field"] == "source_assessment"
