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
async def test_int01_single_sentence_pass_and_multi_sentence_fail():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)

    # Eén zin: geen INT-01-violation. Sinds DEF-770 is dat een deelbevinding
    # (zinsstructuur vastgesteld; compactheid en begrijpelijkheid open), dus
    # ook geen geslaagde regel. Komma, en, die en waarbij zijn geen afkeurgrond.
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
    assert "INT-01" not in res_ok.get("passed_rules", []), res_ok

    # FAIL: een tweede zin (DEF-770: functionele zinsgrens, geen woordlijst)
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
async def test_con01_name_signal_stays_open_and_duplicate_signal():
    """DEF-622 (B-04): een geselecteerde contextnaam in de zin is een
    beoordelingssignaal (review_required), geen automatische violation; de
    duplicaatmelding komt los daarvan van DUP_01."""
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

    # OPEN: de geselecteerde namen DJI en strafrecht staan letterlijk in de
    # zin → naamsignaal dat op menselijke beoordeling wacht (B-04), geen
    # violation. De frase "binnen de context van" is bewust géén afkeurgrond.
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
    assert res_bad["rule_statuses"]["CON-01"] == "review_required", res_bad[
        "rule_statuses"
    ]
    assert not any(
        v.get("code") == "CON-01" for v in res_bad.get("violations", [])
    ), res_bad
    signalen = {
        p["evidence"]
        for p in res_bad["rule_results"]["CON-01"]["parts"]
        if p.get("evidence")
    }
    assert signalen == {"strafrecht", "DJI"}, signalen

    # Also expect a duplicate-context warning via repo signal.
    # DEF-674: die melding komt van DUP_01, de regel die de database bevraagt.
    dup_warns = [
        v
        for v in res_bad.get("violations", [])
        if v.get("code") == "DUP_01" and v.get("severity") == "warning"
    ]
    assert (
        dup_warns
    ), f"Expected DUP_01 duplicate warning, got: {res_bad.get('violations', [])}"
    assert dup_warns[0].get("metadata", {}).get("existing_definition_id") == 1

    # PASS: geen geselecteerde naam in de zin → CON-01 voldoet (duplicate still may warn if same context)
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
    assert res_ok["rule_statuses"]["CON-01"] == "pass", res_ok["rule_statuses"]
    assert not any(
        v.get("code") == "CON-01" for v in res_ok.get("violations", [])
    ), res_ok
