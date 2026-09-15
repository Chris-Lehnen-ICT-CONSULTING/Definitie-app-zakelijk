"""DEF-622 (B-03): de checker vóór generatie herkent gelijke context zoals de repository.

Reviewbevinding op de duplicaatlookup: `DefinitieChecker.check_before_generation`
filterde het door de repository gevonden record opnieuw op wettelijke basis
met een eigen normalisatie (`strip().lower()`, zonder ontdubbeling en zonder
lege waarden weg te laten). Bij `['Regeling Z', 'regeling z', '']` of bij
`Straße`/`STRASSE` vond de repository het record wél, maar gaf de checker
PROCEED zonder record terug. De checker volgt nu dezelfde `contextsleutel`.
"""

from __future__ import annotations

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker

pytestmark = [pytest.mark.unit]


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    repo = DefinitieRepository(str(tmp_path / "checker.db"))
    repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie="kwaliteitsmerk voor gecontroleerde producten",
            categorie="type",
            organisatorische_context='["Stichting Straße"]',
            juridische_context='["privaatrecht"]',
            wettelijke_basis='["Regeling Z"]',
            status=DefinitieStatus.ESTABLISHED.value,
        )
    )
    return repo


@pytest.mark.parametrize(
    ("org", "wet"),
    [
        ('["Stichting STRASSE"]', ["Regeling Z", "regeling z", ""]),
        ('["stichting straße"]', [" regeling z "]),
        ('["Stichting Straße"]', ["Regeling Z"]),
    ],
)
def test_checker_vindt_bestaand_record_bij_gelijke_genormaliseerde_context(
    repo, org, wet
):
    resultaat = DefinitieChecker(repo).check_before_generation(
        begrip="keurmerk",
        organisatorische_context=org,
        juridische_context='["Privaatrecht"]',
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=wet,
    )
    assert resultaat.action == CheckAction.USE_EXISTING, resultaat
    assert resultaat.existing_definitie is not None
    assert resultaat.existing_definitie.begrip == "keurmerk"


def test_checker_geeft_proceed_bij_werkelijk_andere_wettelijke_basis(repo):
    resultaat = DefinitieChecker(repo).check_before_generation(
        begrip="keurmerk",
        organisatorische_context='["Stichting Straße"]',
        juridische_context='["privaatrecht"]',
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=["Regeling Q"],
    )
    assert resultaat.action == CheckAction.PROCEED
    assert resultaat.existing_definitie is None
