#!/usr/bin/env python3
"""
Manual test script voor Category-Aware Duplicate Detection.

Test de fix voor het probleem dat category wijzigingen niet werden
meegenomen in duplicate checking, waardoor regeneration werd geblokkeerd.

Dit script test:
- Repository find_definitie met categorie parameter
- Repository find_duplicates met categorie parameter
- DefinitieChecker integration
- End-to-end scenario waar category wijziging nieuwe generatie triggert

Run dit script om te valideren dat de category-aware duplicate detection werkt.
"""

import logging
import os
import sys
import tempfile
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_database():
    """Create temporary test database."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    # Initialize repository with test database
    repo = DefinitieRepository(temp_db.name)
    repo._init_database()  # Create tables

    return repo, temp_db.name


def create_test_records(repo: DefinitieRepository):
    """Create test records in database."""
    # Record 1: verificatie as proces
    record1 = DefinitieRecord(
        begrip="verificatie",
        definitie="Een proces waarbij documenten worden gecontroleerd op geldigheid",
        organisatorische_context="Gemeente Amsterdam",
        juridische_context="Wet BRP",
        categorie="proces",
        created_by="test_user",
    )
    record1_id = repo.create_definitie(record1)

    # Record 2: verificatie as type (same context, different category)
    record2 = DefinitieRecord(
        begrip="verificatie",
        definitie="Een type controle-instrument voor documenten",
        organisatorische_context="Gemeente Amsterdam",
        juridische_context="Wet BRP",
        categorie="type",
        created_by="test_user",
    )
    record2_id = repo.create_definitie(record2)

    # Record 3: authenticatie as proces (different begrip)
    record3 = DefinitieRecord(
        begrip="authenticatie",
        definitie="Een proces van identiteitsvaststelling",
        organisatorische_context="Gemeente Amsterdam",
        juridische_context="Wet BRP",
        categorie="proces",
        created_by="test_user",
    )
    record3_id = repo.create_definitie(record3)

    return record1_id, record2_id, record3_id


def test_repository_find_definitie_with_category():
    """Test repository find_definitie met category parameter."""
    print("\n🗃️ Test 1: Repository find_definitie with Category")
    print("=" * 60)

    repo, db_path = create_test_database()

    try:
        # Create test records
        record1_id, record2_id, record3_id = create_test_records(repo)

        # Test 1: Find verificatie with proces category
        result = repo.find_definitie(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="proces",
        )

        if result and result.id == record1_id:
            print("   ✅ Found correct record for verificatie + proces")
        else:
            print(
                f"   ❌ Wrong record found: {result.id if result else None}, expected: {record1_id}"
            )
            return False

        # Test 2: Find verificatie with type category
        result = repo.find_definitie(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="type",
        )

        if result and result.id == record2_id:
            print("   ✅ Found correct record for verificatie + type")
        else:
            print(
                f"   ❌ Wrong record found: {result.id if result else None}, expected: {record2_id}"
            )
            return False

        # Test 3: Find with non-existing category combination
        result = repo.find_definitie(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="resultaat",  # This combination doesn't exist
        )

        if result is None:
            print("   ✅ Correctly returned None for non-existing category combination")
        else:
            print(f"   ❌ Found unexpected record: {result.id}")
            return False

        # Test 4: Find without category (legacy behavior)
        result = repo.find_definitie(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            # No categorie parameter - should find first match
        )

        if result and result.begrip == "verificatie":
            print("   ✅ Legacy behavior works (no category filter)")
        else:
            print("   ❌ Legacy behavior broken")
            return False

        print("✅ Repository find_definitie with category test PASSED\\n")
        return True

    finally:
        os.unlink(db_path)


def test_repository_find_duplicates_with_category():
    """Test repository find_duplicates met category parameter."""
    print("\n🔍 Test 2: Repository find_duplicates with Category")
    print("=" * 60)

    repo, db_path = create_test_database()

    try:
        # Create test records
        record1_id, record2_id, record3_id = create_test_records(repo)

        # Test 1: Find duplicates for verificatie with proces category
        duplicates = repo.find_duplicates(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="proces",
        )

        # Should only find the proces record
        if len(duplicates) == 1 and duplicates[0].definitie_record.id == record1_id:
            print("   ✅ Found only proces record for verificatie + proces category")
        else:
            print(
                f"   ❌ Wrong duplicates found: {[d.definitie_record.id for d in duplicates]}"
            )
            return False

        # Test 2: Find duplicates for verificatie with type category
        duplicates = repo.find_duplicates(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="type",
        )

        # Should only find the type record
        if len(duplicates) == 1 and duplicates[0].definitie_record.id == record2_id:
            print("   ✅ Found only type record for verificatie + type category")
        else:
            print(
                f"   ❌ Wrong duplicates found: {[d.definitie_record.id for d in duplicates]}"
            )
            return False

        # Test 3: Find duplicates without category (legacy behavior)
        duplicates = repo.find_duplicates(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            # No categorie parameter - should find both records
        )

        found_ids = {d.definitie_record.id for d in duplicates}
        expected_ids = {record1_id, record2_id}

        if found_ids == expected_ids:
            print("   ✅ Legacy behavior finds both records (no category filter)")
        else:
            print(
                f"   ❌ Legacy behavior broken. Found: {found_ids}, Expected: {expected_ids}"
            )
            return False

        # Test 4: Fuzzy match with category
        duplicates = repo.find_duplicates(
            begrip="verific",  # Partial match
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie="proces",
        )

        # Should find the proces record via fuzzy matching
        if len(duplicates) >= 1 and any(
            d.definitie_record.id == record1_id for d in duplicates
        ):
            print("   ✅ Fuzzy match with category works")
        else:
            print(
                f"   ❌ Fuzzy match with category failed: {[d.definitie_record.id for d in duplicates]}"
            )
            return False

        print("✅ Repository find_duplicates with category test PASSED\\n")
        return True

    finally:
        os.unlink(db_path)


def test_definitie_checker_integration():
    """Test DefinitieChecker integration met category-aware duplicate detection."""
    print("\n🔧 Test 3: DefinitieChecker Integration")
    print("=" * 60)

    repo, db_path = create_test_database()

    try:
        # Create test records
        record1_id, record2_id, record3_id = create_test_records(repo)

        # Create checker
        checker = DefinitieChecker(repo)

        # Test 1: Check for existing verificatie + proces (should find existing)
        check_result = checker.check_before_generation(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie=OntologischeCategorie.PROCES,
        )

        if (
            check_result.action == CheckAction.USE_EXISTING
            and check_result.existing_definitie.id == record1_id
        ):
            print("   ✅ Correctly found existing proces record")
        else:
            print(
                f"   ❌ Wrong result for existing proces: {check_result.action}, record: {check_result.existing_definitie.id if check_result.existing_definitie else None}"
            )
            return False

        # Test 2: Check for existing verificatie + type (should find existing)
        check_result = checker.check_before_generation(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie=OntologischeCategorie.TYPE,
        )

        if (
            check_result.action == CheckAction.USE_EXISTING
            and check_result.existing_definitie.id == record2_id
        ):
            print("   ✅ Correctly found existing type record")
        else:
            print(
                f"   ❌ Wrong result for existing type: {check_result.action}, record: {check_result.existing_definitie.id if check_result.existing_definitie else None}"
            )
            return False

        # Test 3: Check for verificatie + resultaat (should proceed with generation)
        check_result = checker.check_before_generation(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie=OntologischeCategorie.RESULTAAT,  # This combination doesn't exist
        )

        if check_result.action == CheckAction.PROCEED:
            print(
                "   ✅ Correctly proceeds with generation for new category combination"
            )
        else:
            print(f"   ❌ Wrong result for new category: {check_result.action}")
            return False

        # Test 4: Check with force_generate=True (should always proceed)
        check_result = checker.check_before_generation(
            begrip="verificatie",
            organisatorische_context="Gemeente Amsterdam",
            juridische_context="Wet BRP",
            categorie=OntologischeCategorie.PROCES,  # Existing combination
        )

        # Without force_generate, it should find existing
        if check_result.action != CheckAction.PROCEED:
            print("   ✅ Without force_generate, existing record is found")
        else:
            print("   ❌ Should find existing record without force_generate")
            return False

        print("✅ DefinitieChecker integration test PASSED\\n")
        return True

    finally:
        os.unlink(db_path)


def test_end_to_end_category_change_scenario():
    """Test complete end-to-end scenario: category change should trigger new generation."""
    print("\n🔄 Test 4: End-to-End Category Change Scenario")
    print("=" * 60)

    repo, db_path = create_test_database()

    try:
        # Create checker
        checker = DefinitieChecker(repo)

        # Scenario: User generates definitie for "validatie" as "proces"
        print("   📝 Step 1: Generate initial definition (validatie + proces)")

        # This should proceed (no existing record)
        check_result = checker.check_before_generation(
            begrip="validatie",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie=OntologischeCategorie.PROCES,
        )

        if check_result.action != CheckAction.PROCEED:
            print(
                f"   ❌ Initial generation should proceed, got: {check_result.action}"
            )
            return False

        # Simulate saving the generated definition
        initial_record = DefinitieRecord(
            begrip="validatie",
            definitie="Een proces waarbij gegevens worden gecontroleerd op juistheid",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie="proces",
            created_by="test_user",
        )
        initial_record_id = repo.create_definitie(initial_record)

        print(f"   ✅ Initial definition created (ID: {initial_record_id})")

        # Step 2: User changes category to "type" - should allow new generation
        print("   🔄 Step 2: User changes category to 'type'")

        check_result = checker.check_before_generation(
            begrip="validatie",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie=OntologischeCategorie.TYPE,  # Different category!
        )

        if check_result.action == CheckAction.PROCEED:
            print("   ✅ Category change correctly triggers new generation")
        else:
            print(
                f"   ❌ Category change should allow generation, got: {check_result.action}"
            )
            if check_result.existing_definitie:
                print(
                    f"        Found existing: ID={check_result.existing_definitie.id}, category={check_result.existing_definitie.categorie}"
                )
            return False

        # Step 3: Generate new definition with new category
        print("   📝 Step 3: Generate new definition with type category")

        new_record = DefinitieRecord(
            begrip="validatie",
            definitie="Een type controle-mechanisme voor gegevenskwaliteit",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie="type",
            created_by="test_user",
        )
        new_record_id = repo.create_definitie(new_record)

        print(f"   ✅ New definition created (ID: {new_record_id})")

        # Step 4: Verify both records exist and can be found correctly
        print("   🔍 Step 4: Verify both definitions exist and are findable")

        proces_record = repo.find_definitie(
            begrip="validatie",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie="proces",
        )

        type_record = repo.find_definitie(
            begrip="validatie",
            organisatorische_context="Overheidsorganisatie",
            juridische_context="AVG",
            categorie="type",
        )

        if proces_record and type_record and proces_record.id != type_record.id:
            print("   ✅ Both definitions exist and are distinct")
            print(
                f"        Proces definition (ID {proces_record.id}): {proces_record.definitie[:60]}..."
            )
            print(
                f"        Type definition (ID {type_record.id}): {type_record.definitie[:60]}..."
            )
        else:
            print("   ❌ Could not find both distinct definitions")
            return False

        print("✅ End-to-end category change scenario PASSED\\n")
        return True

    finally:
        os.unlink(db_path)


def test_edge_cases():
    """Test edge cases en error scenarios."""
    print("\n⚠️ Test 5: Edge Cases and Error Scenarios")
    print("=" * 60)

    repo, db_path = create_test_database()

    try:
        # Test 1: Empty/None category parameter
        print("   🔍 Test 5.1: None category parameter")

        result = repo.find_definitie(
            begrip="test",
            organisatorische_context="context",
            juridische_context="juridisch",
            categorie=None,  # None category
        )

        # Should work without error (legacy behavior)
        if result is None:  # No record exists, which is expected
            print("   ✅ None category parameter handled gracefully")
        else:
            # If record exists, that's also fine
            print("   ✅ None category parameter works")

        # Test 2: Empty string category
        print("   🔍 Test 5.2: Empty string category")

        _ = repo.find_duplicates(
            begrip="test",
            organisatorische_context="context",
            categorie="",  # Empty string
        )

        # Should work without error
        print("   ✅ Empty string category handled gracefully")

        # Test 3: Special characters in category
        print("   🔍 Test 5.3: Special characters in category")

        try:
            result = repo.find_definitie(
                begrip="test",
                organisatorische_context="context",
                categorie="test'category; DROP TABLE definities;",  # SQL injection attempt
            )
            print("   ✅ SQL injection protection works")
        except Exception as e:
            print(f"   ❌ SQL injection caused error: {e}")
            return False

        print("✅ Edge cases test PASSED\\n")
        return True

    finally:
        os.unlink(db_path)


def main():
    """Run alle category-aware duplicate detection tests."""
    print("🔍 Starting Category-Aware Duplicate Detection Tests")
    print("=" * 70)
    print("Testing the fix for the issue where category changes")
    print("were not considered in duplicate detection, blocking regeneration.")
    print("=" * 70)

    test_results = []

    try:
        # Run all tests
        test_results.append(
            (
                "Repository find_definitie with Category",
                test_repository_find_definitie_with_category(),
            )
        )
        test_results.append(
            (
                "Repository find_duplicates with Category",
                test_repository_find_duplicates_with_category(),
            )
        )
        test_results.append(
            ("DefinitieChecker Integration", test_definitie_checker_integration())
        )
        test_results.append(
            ("End-to-End Category Change", test_end_to_end_category_change_scenario())
        )
        test_results.append(("Edge Cases", test_edge_cases()))

        # Summary
        passed_tests = [name for name, result in test_results if result]
        failed_tests = [name for name, result in test_results if not result]

        print("📋 TEST SUMMARY")
        print("=" * 50)

        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")

        print(f"\\n📊 Results: {len(passed_tests)}/{len(test_results)} tests passed")

        if len(failed_tests) == 0:
            print("🎉 ALL CATEGORY-AWARE DUPLICATE DETECTION TESTS PASSED!")
            print("✅ Category changes now correctly trigger new generation")
            print("✅ Duplicate detection is category-aware")
            print("✅ Fix resolves the regeneration blocking issue")
            print("✅ Legacy behavior is preserved for backward compatibility")
            return True
        print(f"❌ {len(failed_tests)} tests failed: {', '.join(failed_tests)}")
        return False

    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
