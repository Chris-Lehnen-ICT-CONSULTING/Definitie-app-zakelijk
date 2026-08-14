import asyncio

import pytest

from domain.context.normalisatie import contextsleutel
from services.interfaces import DuplicateCandidate
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]


class _FakeDef:
    def __init__(self, id, begrip, org=None, jur=None, categorie=None, status="draft"):
        self.id = id
        self.begrip = begrip
        self.organisatorische_context = org or []
        self.juridische_context = jur or []
        self.categorie = categorie
        self.status = status


class _FakeRepo:
    """Bootst de publieke duplicaat-capability na (DEF-672).

    Was gebouwd op `_get_all_definitions`, een privémethode die in DEF-176 is
    verwijderd en die de productie-repository dus niet had — waardoor deze test
    een pad toetste dat in werkelijkheid nooit liep. Filtert nu net als de echte
    repository op begrip en status, en levert genormaliseerde sleutels.
    """

    def __init__(self, defs):
        self._defs = defs

    def find_duplicate_candidates(self, begrip):
        gezocht = str(begrip or "").strip().casefold()
        return [
            DuplicateCandidate(
                id=d.id,
                status=d.status,
                categorie=d.categorie,
                organisatorische_context=contextsleutel(d.organisatorische_context),
                juridische_context=contextsleutel(d.juridische_context),
                wettelijke_basis=contextsleutel(getattr(d, "wettelijke_basis", [])),
            )
            for d in self._defs
            if str(d.begrip or "").strip().casefold() == gezocht
            and str(d.status or "") != "archived"
        ]


@pytest.mark.asyncio
async def test_ess02_marker_override_passes():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = await svc.validate_definition(
        begrip="toezicht",
        text="toezicht is een proces waarbij…",
        ontologische_categorie=None,
        context={"marker": "proces"},
    )
    # No ESS-02 violation expected
    assert not any(v.get("code") == "ESS-02" for v in res.get("violations", []))


@pytest.mark.asyncio
async def test_ess02_ambiguity_fails():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    # Text suggests both process and result
    text = "… is een proces en tevens het resultaat van …"
    res = await svc.validate_definition(
        begrip="sanctionering",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-02" and v.get("severity") == "error"
        for v in res["violations"]
    )


@pytest.mark.asyncio
async def test_con01_duplicate_signals_warning():
    # Existing definition with same context
    existing = _FakeDef(
        1,
        "registratie",
        org=["DJI"],
        jur=["strafrecht"],
        categorie="proces",
        status="established",
    )
    repo = _FakeRepo([existing])
    svc = ModularValidationService(
        get_toetsregel_manager(), None, None, repository=repo
    )
    res = await svc.validate_definition(
        begrip="registratie",
        text="Registratie is het vastleggen …",
        ontologische_categorie="proces",
        context={
            "organisatorische_context": ["DJI"],
            "juridische_context": ["strafrecht"],
            "categorie": "proces",
        },
    )
    # Expect a CON-01 warning with existing_definition_id
    # DEF-674: de duplicaatmelding komt van DUP_01, niet meer van CON-01.
    warns = [
        v
        for v in res["violations"]
        if v.get("code") == "DUP_01" and v.get("severity") == "warning"
    ]
    assert warns, f"No DUP_01 duplicate warning found: {res['violations']}"
    assert warns[0].get("metadata", {}).get("existing_definition_id") == 1


@pytest.mark.asyncio
async def test_ess01_goal_phrases_forbidden():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "… is een systeem om te registreren …"
    res = await svc.validate_definition(
        begrip="systeem",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    # ESS-01 is sinds DEF-624 een oordeelregel; de doelfrase blijft een
    # reviewersignaal maar is geen bewijs meer.
    review = {r["rule_id"]: r for r in res.get("review_required", [])}
    assert "ESS-01" in review, res
    assert review["ESS-01"]["signals"], review
    assert "ESS-01" not in res.get("passed_rules", []), res
    assert not any(v.get("code") == "ESS-01" for v in res["violations"]), res
