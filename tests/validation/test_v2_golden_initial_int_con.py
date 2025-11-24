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


@pytest.mark.asyncio
async def test_int01_single_sentence_pass_and_multi_sentence_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    # PASS: één zin, geen INT-01 patterns (geen komma, en, of, maar, die, waarbij, etc.)
    text_ok = "maatregel: corrigerende actie ter naleving van regels"
    res_ok = await svc.validate_definition(
        begrip="maatregel",
        text=text_ok,
        ontologische_categorie=None,
        context={},
    )
    assert not any(
        v.get("code") == "INT-01" for v in res_ok.get("violations", [])
    ), res_ok

    # FAIL: meerzinnigheid en verbindingswoorden → zou INT-01 patterns moeten raken
    text_bad = (
        "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. "
        "In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften."
    )
    res_bad = await svc.validate_definition(
        begrip="transitie-eis",
        text=text_bad,
        ontologische_categorie=None,
        context={},
    )
    assert any(
        v.get("code") == "INT-01" for v in res_bad.get("violations", [])
    ), res_bad


@pytest.mark.asyncio
async def test_con01_forbidden_context_patterns_and_duplicate_signal():
    # Set up repo with existing definition → duplicate signal as warning
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

    # FAIL: explicit context mention should trigger CON-01
    text_bad = "Registratie is het formeel vastleggen van gegevens binnen de context van het strafrecht bij DJI."
    res_bad = await svc.validate_definition(
        begrip="registratie",
        text=text_bad,
        ontologische_categorie="proces",
        context={
            "organisatorische_context": ["DJI"],
            "juridische_context": ["strafrecht"],
            "categorie": "proces",
        },
    )
    assert any(
        v.get("code") == "CON-01" for v in res_bad.get("violations", [])
    ), res_bad

    # Also expect a duplicate-context warning via repo signal
    dup_warns = [
        v
        for v in res_bad.get("violations", [])
        if v.get("code") == "CON-01" and v.get("severity") == "warning"
    ]
    assert (
        dup_warns
    ), f"Expected CON-01 duplicate warning, got: {res_bad.get('violations', [])}"
    assert dup_warns[0].get("metadata", {}).get("existing_definition_id") == 1

    # PASS: no explicit context wording → CON-01 should not appear (duplicate still may warn if same context)
    text_ok = "Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem"
    res_ok = await svc.validate_definition(
        begrip="registratie",
        text=text_ok,
        ontologische_categorie="proces",
        context={
            "organisatorische_context": ["OnbekendOrg"],
            "juridische_context": ["bestuursrecht"],
            "categorie": "proces",
        },
    )
    assert not any(
        v.get("code") == "CON-01" and v.get("severity") != "warning"
        for v in res_ok.get("violations", [])
    ), res_ok
