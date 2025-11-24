#!/usr/bin/env python3
"""
Database Setup Script - Initialiseer definitie database met schema en test data.
"""

import logging  # Logging faciliteiten voor setup proces
import sys  # Systeem interface voor path manipulatie
from pathlib import Path  # Object-georiënteerde pad manipulatie

# Voeg src directory toe aan Python path voor module imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # Relatief pad naar src directory

from generation.definitie_generator import (
    OntologischeCategorie,  # Ontologische categorieën
)

# Importeer database componenten voor setup en initialisatie
from database.definitie_repository import (
    DefinitieRecord,  # Repository en data modellen
    DefinitieStatus,
    SourceType,  # Status en bron type enumeraties
    get_definitie_repository,
)

# Setup logging configuratie voor database setup script
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)  # Configureer logging format
logger = logging.getLogger(__name__)  # Logger instantie voor setup script


def create_test_data() -> list[DefinitieRecord]:
    """Maak test data voor de database met voorbeelden van verschillende definities."""
    # Maak lijst met test definities voor verschillende scenario's
    return [
        DefinitieRecord(
            begrip="verificatie",
            definitie="Proces waarbij identiteitsgegevens systematisch worden gecontroleerd tegen authentieke bronregistraties om de juistheid en volledigheid te waarborgen",
            categorie=OntologischeCategorie.PROCES.value,
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            status=DefinitieStatus.ESTABLISHED.value,
            validation_score=0.95,
            source_type=SourceType.GENERATED.value,
            created_by="setup_script",
            approved_by="admin",
        ),
        DefinitieRecord(
            begrip="registratie",
            definitie="Handeling waarbij gegevens worden vastgelegd in een gestructureerd systeem voor latere raadpleging en verwerking",
            categorie=OntologischeCategorie.PROCES.value,
            organisatorische_context="OM",
            juridische_context="",
            status=DefinitieStatus.DRAFT.value,
            validation_score=0.78,
            source_type=SourceType.GENERATED.value,
            created_by="setup_script",
        ),
        DefinitieRecord(
            begrip="identiteitsbewijs",
            definitie="Document dat officieel de identiteit van een natuurlijk persoon of rechtspersoon vaststelt en bevestigt",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="DJI",
            juridische_context="burgerlijk recht",
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.88,
            source_type=SourceType.MANUAL.value,
            created_by="domain_expert",
        ),
        DefinitieRecord(
            begrip="besluit",
            definitie="Formele uitspraak die resulteert uit beoordeling van feiten en omstandigheden volgens vastgestelde criteria en procedures",
            categorie=OntologischeCategorie.RESULTAAT.value,
            organisatorische_context="OM",
            juridische_context="bestuursrecht",
            status=DefinitieStatus.ESTABLISHED.value,
            validation_score=0.92,
            source_type=SourceType.IMPORTED.value,
            imported_from="juridisch_woordenboek.json",
            created_by="import_script",
            approved_by="juridisch_adviseur",
        ),
        DefinitieRecord(
            begrip="dossier",
            definitie="Gestructureerde verzameling documenten en gegevens betreffende een specifieke zaak, persoon of onderwerp",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="DJI",
            juridische_context="",
            status=DefinitieStatus.ARCHIVED.value,
            validation_score=0.65,
            source_type=SourceType.GENERATED.value,
            created_by="old_system",
        ),
        DefinitieRecord(
            begrip="toezicht",
            definitie="Systematische activiteit waarbij wordt gecontroleerd of handelingen, processen of situaties voldoen aan vastgestelde normen en voorschriften",
            categorie=OntologischeCategorie.PROCES.value,
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            status=DefinitieStatus.ESTABLISHED.value,
            validation_score=0.91,
            source_type=SourceType.GENERATED.value,
            created_by="definitie_agent",
            approved_by="hoofd_juridische_zaken",
        ),
        DefinitieRecord(
            begrip="authentisering",
            definitie="Proces waarbij de echtheid en geldigheid van een identiteit, document of systeem wordt vastgesteld door verificatie tegen vertrouwde bronnen",
            categorie=OntologischeCategorie.PROCES.value,
            organisatorische_context="KMAR",
            juridische_context="",
            status=DefinitieStatus.REVIEW.value,
            validation_score=0.83,
            source_type=SourceType.GENERATED.value,
            created_by="security_expert",
        ),
        DefinitieRecord(
            begrip="rapport",
            definitie="Gestructureerd document dat resultaten, bevindingen of aanbevelingen presenteert op basis van onderzoek, analyse of evaluatie",
            categorie=OntologischeCategorie.RESULTAAT.value,
            organisatorische_context="OM",
            juridische_context="",
            status=DefinitieStatus.ESTABLISHED.value,
            validation_score=0.87,
            source_type=SourceType.MANUAL.value,
            created_by="rapportage_specialist",
            approved_by="manager_rapportage",
        ),
    ]


def setup_database(db_path: str | None = None, include_test_data: bool = True):
    """
    Setup complete database met schema en optioneel test data.

    Args:
        db_path: Pad naar database bestand
        include_test_data: Of test data moet worden toegevoegd
    """
    print("🔧 DEFINITIE DATABASE SETUP")
    print("=" * 40)

    # Initialiseer repository (dit maakt automatisch de database aan)
    repository = get_definitie_repository(db_path)

    print(f"✅ Database geïnitialiseerd: {repository.db_path}")

    if include_test_data:
        print("\n📥 Laden van test data...")

        test_records = create_test_data()

        for record in test_records:
            try:
                # Check of definitie al bestaat
                existing = repository.find_definitie(
                    record.begrip,
                    record.organisatorische_context,
                    record.juridische_context or "",
                    DefinitieStatus(record.status) if record.status != "any" else None,
                )

                if existing:
                    print(f"⏭️  Skip '{record.begrip}' - bestaat al (ID: {existing.id})")
                    continue

                # Maak nieuwe definitie
                record_id = repository.create_definitie(record)
                print(
                    f"✅ Toegevoegd: '{record.begrip}' (ID: {record_id}) - {record.status}"
                )

                # Set approval als established
                if (
                    record.status == DefinitieStatus.ESTABLISHED.value
                    and record.approved_by
                ):
                    repository.change_status(
                        record_id,
                        DefinitieStatus.ESTABLISHED,
                        record.approved_by,
                        "Goedgekeurd tijdens setup",
                    )

            except Exception as e:
                print(f"❌ Fout bij toevoegen '{record.begrip}': {e}")

        print("\n✅ Test data setup voltooid")

    # Toon statistieken
    stats = repository.get_statistics()

    print("\n📊 DATABASE STATISTIEKEN:")
    print(f"   Totaal definities: {stats['total_definities']}")

    if stats["by_status"]:
        print("   Per status:")
        for status, count in stats["by_status"].items():
            print(f"     - {status}: {count}")

    if stats["by_category"]:
        print("   Per categorie:")
        for category, count in stats["by_category"].items():
            print(f"     - {category}: {count}")

    if stats["average_validation_score"]:
        print(f"   Gemiddelde score: {stats['average_validation_score']:.3f}")

    print("\n🎯 Setup voltooid! Database klaar voor gebruik.")

    # Toon hoe CLI te gebruiken
    print("\n💡 CLI VOORBEELDEN:")
    print("   python tools/definitie_manager.py list")
    print(
        "   python tools/definitie_manager.py check --begrip authenticatie --context DJI --categorie proces"
    )
    print(
        "   python tools/definitie_manager.py generate --begrip controle --context OM --categorie proces"
    )
    print("   python tools/definitie_manager.py stats")


def create_sample_export():
    """Maak voorbeeld export bestand."""
    export_path = (
        Path(__file__).parent.parent.parent / "exports" / "sample_definitions.json"
    )
    export_path.parent.mkdir(exist_ok=True)

    repository = get_definitie_repository()

    # Exporteer established definities
    count = repository.export_to_json(
        str(export_path), {"status": DefinitieStatus.ESTABLISHED}
    )

    print(f"📤 Sample export gemaakt: {export_path} ({count} definities)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup definitie database")
    parser.add_argument("--db", help="Database bestand pad")
    parser.add_argument(
        "--no-test-data", action="store_true", help="Geen test data toevoegen"
    )
    parser.add_argument(
        "--export-sample", action="store_true", help="Maak sample export"
    )

    args = parser.parse_args()

    try:
        setup_database(db_path=args.db, include_test_data=not args.no_test_data)

        if args.export_sample:
            create_sample_export()

    except Exception as e:
        print(f"❌ Setup gefaald: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
