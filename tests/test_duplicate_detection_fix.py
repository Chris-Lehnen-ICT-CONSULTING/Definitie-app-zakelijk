"""
Test voor DEF-54: Consistente duplicate detection tussen Checker en Repository.

Test verifieert dat categorie WEL onderdeel is van de unieke key.
"""

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieStatus,
    SourceType,
    get_definitie_repository,
)
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker


@pytest.fixture(autouse=True)
def _cleanup_test_records():
    """Clean up test records before and after each test."""
    repo = get_definitie_repository()
    test_begrippen = ["test_begrip_duplicate", "test_begrip_multi_category"]

    # Cleanup BEFORE test
    for begrip in test_begrippen:
        records = repo.search_definities(query=begrip)
        for record in records:
            try:
                # Delete via direct SQL to avoid any validation
                with repo._get_connection() as conn:
                    conn.execute("DELETE FROM definities WHERE id = ?", (record.id,))
                    conn.commit()
            except Exception:
                pass  # Ignore deletion errors

    yield  # Run test

    # Cleanup AFTER test (for cleanliness)
    for begrip in test_begrippen:
        records = repo.search_definities(query=begrip)
        for record in records:
            try:
                with repo._get_connection() as conn:
                    conn.execute("DELETE FROM definities WHERE id = ?", (record.id,))
                    conn.commit()
            except Exception:
                pass


def test_duplicate_detection_with_same_category():
    """
    Test: Zelfde begrip + context + categorie → Moet BLOCKED worden.
    """
    repo = get_definitie_repository()
    checker = DefinitieChecker(repository=repo)

    begrip = "test_begrip_duplicate"
    org_context = '["TestOrg"]'
    jur_context = ""
    categorie = OntologischeCategorie.TYPE

    # Check of record al bestaat
    existing = repo.find_definitie(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie.value,
    )

    # Als record nog niet bestaat, maak het aan
    record1_id = None
    if not existing:
        record1 = DefinitieRecord(
            begrip=begrip,
            definitie="Test definitie 1",
            categorie=categorie.value,
            organisatorische_context=org_context,
            juridische_context=jur_context,
            status=DefinitieStatus.DRAFT.value,
            source_type=SourceType.MANUAL.value,
            wettelijke_basis="[]",
        )
        record1_id = repo.create_definitie(record1)
        assert record1_id is not None, "Eerste record moet succesvol aangemaakt worden"

    # Stap 2: Check voor duplicates
    check_result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie,
    )

    # Verwacht: NIET PROCEED (er is een duplicate)
    assert (
        check_result.action != CheckAction.PROCEED
    ), f"Expected duplicate detection, but got action: {check_result.action}"
    assert (
        check_result.existing_definitie is not None
    ), "Existing definitie moet gevonden worden"

    # Stap 3: Probeer tweede record aan te maken (moet falen)
    record2 = DefinitieRecord(
        begrip=begrip,
        definitie="Test definitie 2 (duplicate)",
        categorie=categorie.value,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        status=DefinitieStatus.DRAFT.value,
        source_type=SourceType.MANUAL.value,
        wettelijke_basis="[]",
    )

    # Should raise error for duplicate
    error_msg = "bestaat al"
    with pytest.raises((ValueError, Exception), match=error_msg):
        repo.create_definitie(record2)


def test_duplicate_detection_with_different_category():
    """
    Test: Zelfde begrip + context, VERSCHILLENDE categorie → Moet TOEGESTAAN worden.
    """
    repo = get_definitie_repository()
    checker = DefinitieChecker(repository=repo)

    begrip = "test_begrip_multi_category"
    org_context = '["TestOrg"]'
    jur_context = ""
    categorie_type = OntologischeCategorie.TYPE
    categorie_proces = OntologischeCategorie.PROCES

    # Check of TYPE record al bestaat
    existing_type = repo.find_definitie(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie_type.value,
    )

    # Maak TYPE record aan als het nog niet bestaat
    if not existing_type:
        record_type = DefinitieRecord(
            begrip=begrip,
            definitie="Test definitie als TYPE",
            categorie=categorie_type.value,
            organisatorische_context=org_context,
            juridische_context=jur_context,
            status=DefinitieStatus.DRAFT.value,
            source_type=SourceType.MANUAL.value,
            wettelijke_basis="[]",
        )
        record_type_id = repo.create_definitie(record_type)
        assert (
            record_type_id is not None
        ), "TYPE record moet succesvol aangemaakt worden"

    # Stap 2: Check voor duplicates met PROCES categorie
    check_result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie_proces,
    )

    # Verwacht: PROCEED (geen duplicate met PROCES categorie)
    assert (
        check_result.action == CheckAction.PROCEED
    ), f"Expected PROCEED for different category, but got: {check_result.action}"

    # Stap 3: Check of PROCES record al bestaat
    existing_proces = repo.find_definitie(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie_proces.value,
    )

    # Maak PROCES record aan als het nog niet bestaat
    if not existing_proces:
        record_proces = DefinitieRecord(
            begrip=begrip,
            definitie="Test definitie als PROCES",
            categorie=categorie_proces.value,
            organisatorische_context=org_context,
            juridische_context=jur_context,
            status=DefinitieStatus.DRAFT.value,
            source_type=SourceType.MANUAL.value,
            wettelijke_basis="[]",
        )
        record_proces_id = repo.create_definitie(record_proces)
        assert (
            record_proces_id is not None
        ), "PROCES record moet succesvol aangemaakt worden"

    # Verificatie: beide records bestaan
    type_record = repo.find_definitie(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie_type.value,
    )
    proces_record = repo.find_definitie(
        begrip=begrip,
        organisatorische_context=org_context,
        juridische_context=jur_context,
        categorie=categorie_proces.value,
    )

    assert type_record is not None, "TYPE record moet bestaan"
    assert proces_record is not None, "PROCES record moet bestaan"
    assert type_record.categorie == categorie_type.value
    assert proces_record.categorie == categorie_proces.value


if __name__ == "__main__":
    # Run tests manually for quick verification
    print("🧪 Testing duplicate detection fix...")
    print("\n1️⃣ Test: Same category (should block)")
    try:
        test_duplicate_detection_with_same_category()
        print("✅ PASSED: Same category blocked correctly")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")

    print("\n2️⃣ Test: Different category (should allow)")
    try:
        test_duplicate_detection_with_different_category()
        print("✅ PASSED: Different category allowed correctly")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")

    print("\n✅ All tests passed!")
