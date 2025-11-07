import asyncio

import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager


class _FakeDef:
    def __init__(self, id, begrip, org=None, jur=None, categorie=None, status="draft"):
        self.id = id
        self.begrip = begrip
        self.organisatorische_context = org or []
        self.juridische_context = jur or []
        self.categorie = categorie
        self.status = status


class _FakeRepo:
    def __init__(self, defs):
        self._defs = defs

    def _get_all_definitions(self):
        return list(self._defs)


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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


@pytest.mark.asyncio()
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
    warns = [
        v
        for v in res["violations"]
        if v.get("code") == "CON-01" and v.get("severity") == "warning"
    ]
    assert warns, f"No CON-01 duplicate warning found: {res['violations']}"
    assert warns[0].get("metadata", {}).get("existing_definition_id") == 1


@pytest.mark.asyncio()
async def test_ess01_goal_phrases_forbidden():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    text = "… is een systeem om te registreren …"
    res = await svc.validate_definition(
        begrip="systeem",
        text=text,
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "ESS-01" for v in res["violations"]
    )  # forbidden pattern
