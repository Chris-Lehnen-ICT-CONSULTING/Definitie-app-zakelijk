#!/usr/bin/env python3
"""
Definitie Manager CLI Tool - Command line interface voor definitie database management.
Biedt functionaliteit voor CRUD operaties, import/export, en duplicate checking.
"""

import argparse  # Command line argument parsing voor CLI interface
import logging  # Logging faciliteiten voor debug en monitoring
import sys  # Systeem interface voor path manipulatie
from pathlib import Path  # Object-georiënteerde pad manipulatie

# Voeg src directory toe aan Python path voor module imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # Relatief pad naar src directory

from generation.definitie_generator import (
    OntologischeCategorie,  # Ontologische categorieën
)

# Importeer database en core componenten voor definitie management
from database.definitie_repository import (
    DefinitieStatus,  # Status en bron type enumeraties
)
from database.definitie_repository import (
    get_definitie_repository,
)
from integration.definitie_checker import (
    generate_or_retrieve_definition,  # Integratie en duplicaat checking
)
from integration.definitie_checker import (
    DefinitieChecker,
)

# Setup logging configuratie voor CLI tool
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)  # Configureer logging format
logger = logging.getLogger(__name__)  # Logger instantie voor CLI tool


class DefinitieManagerCLI:
    """Command line interface voor definitie database management en operaties."""

    def __init__(self, db_path: str | None = None):
        """Initialiseer CLI met database repository en checker."""
        self.repository = get_definitie_repository(
            db_path
        )  # Haal database repository op
        self.checker = DefinitieChecker(
            self.repository
        )  # Maak definitie checker instantie

    def cmd_list(self, args):
        """List definities met optionele filters."""
        print("🔍 DEFINITIES OVERZICHT")
        print("=" * 50)

        # Parse filters
        status = DefinitieStatus(args.status) if args.status else None
        categorie = OntologischeCategorie(args.categorie) if args.categorie else None

        # Search definities
        definities = self.repository.search_definities(
            query=args.query,
            categorie=categorie,
            organisatorische_context=args.context,
            status=status,
            limit=args.limit,
        )

        if not definities:
            print("❌ Geen definities gevonden met opgegeven criteria")
            return

        # Display results
        for i, definitie in enumerate(definities, 1):
            print(f"\n📋 {i}. {definitie.begrip} (ID: {definitie.id})")
            print(f"   Categorie: {definitie.categorie.upper()}")
            print(f"   Context: {definitie.organisatorische_context}")
            print(f"   Status: {definitie.status}")
            print(
                f"   Score: {definitie.validation_score:.2f}"
                if definitie.validation_score
                else "   Score: N/A"
            )
            print(f"   Definitie: {definitie.definitie[:100]}...")
            if definitie.approved_by:
                print(f"   Goedgekeurd door: {definitie.approved_by}")

        print(f"\n📊 Totaal: {len(definities)} definities")

    def cmd_show(self, args):
        """Toon details van specifieke definitie."""
        definitie = self.repository.get_definitie(args.id)

        if not definitie:
            print(f"❌ Definitie met ID {args.id} niet gevonden")
            return

        print("📋 DEFINITIE DETAILS")
        print("=" * 50)
        print(f"ID: {definitie.id}")
        print(f"Begrip: {definitie.begrip}")
        print(f"Categorie: {definitie.categorie}")
        print(f"Organisatorische context: {definitie.organisatorische_context}")
        print(f"Juridische context: {definitie.juridische_context or 'N/A'}")
        print(f"Status: {definitie.status}")
        print(f"Versie: {definitie.version_number}")
        print(f"Validation score: {definitie.validation_score or 'N/A'}")
        print(f"Bron type: {definitie.source_type}")

        print("\n📝 DEFINITIE:")
        print(f"{definitie.definitie}")

        print("\n📅 METADATA:")
        print(
            f"Aangemaakt: {definitie.created_at} door {definitie.created_by or 'Unknown'}"
        )
        print(
            f"Gewijzigd: {definitie.updated_at} door {definitie.updated_by or 'Unknown'}"
        )

        if definitie.approved_by:
            print(f"Goedgekeurd: {definitie.approved_at} door {definitie.approved_by}")
            if definitie.approval_notes:
                print(f"Notities: {definitie.approval_notes}")

        # Show validation issues if any
        issues = definitie.get_validation_issues_list()
        if issues:
            print("\n⚠️ VALIDATION ISSUES:")
            for issue in issues:
                print(
                    f"   - {issue.get('rule_id', 'Unknown')}: {issue.get('description', 'No description')}"
                )

    def cmd_check(self, args):
        """Check voor duplicates zonder definitie te genereren."""
        print("🔍 DUPLICATE CHECK")
        print("=" * 30)

        categorie = OntologischeCategorie(args.categorie)

        check_result = self.checker.check_before_generation(
            begrip=args.begrip,
            organisatorische_context=args.context,
            juridische_context=args.juridische_context or "",
            categorie=categorie,
        )

        print(f"📋 Begrip: {args.begrip}")
        print(f"🏢 Context: {args.context}")
        print(f"⚖️ Juridisch: {args.juridische_context or 'N/A'}")
        print(f"📂 Categorie: {categorie.value}")

        print("\n🎯 RESULTAAT:")
        print(f"Actie: {check_result.action.value}")
        print(f"Vertrouwen: {check_result.confidence:.2f}")
        print(f"Bericht: {check_result.message}")

        if check_result.existing_definitie:
            print("\n📋 BESTAANDE DEFINITIE:")
            existing = check_result.existing_definitie
            print(f"   ID: {existing.id}")
            print(f"   Status: {existing.status}")
            print(f"   Definitie: {existing.definitie}")

        if check_result.duplicates:
            print("\n🔍 MOGELIJKE DUPLICATEN:")
            for i, dup in enumerate(check_result.duplicates[:3], 1):
                print(
                    f"   {i}. {dup.definitie_record.begrip} (Score: {dup.match_score:.2f})"
                )
                print(
                    f"      ID: {dup.definitie_record.id}, Status: {dup.definitie_record.status}"
                )
                print(f"      Redenen: {', '.join(dup.match_reasons)}")

    def cmd_generate(self, args):
        """Genereer nieuwe definitie met duplicate checking."""
        print("🚀 DEFINITIE GENERATIE")
        print("=" * 30)

        definitie_text, metadata = generate_or_retrieve_definition(
            begrip=args.begrip,
            organisatorische_context=args.context,
            juridische_context=args.juridische_context or "",
            categorie=args.categorie,
            force_new=args.force,
            created_by=args.created_by or "cli_user",
        )

        print(f"📋 Begrip: {args.begrip}")
        print(f"🏢 Context: {args.context}")
        print(f"📂 Categorie: {args.categorie}")
        print(f"🔄 Force new: {args.force}")

        print("\n📝 GEGENEREERDE DEFINITIE:")
        print(f"{definitie_text}")

        print("\n📊 METADATA:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")

        if metadata.get("source") == "generated":
            print("\n✅ Nieuwe definitie succesvol gegenereerd en opgeslagen!")
        elif metadata.get("source") == "existing":
            print("\n♻️ Bestaande definitie gebruikt (geen nieuwe generatie)")
        else:
            print(f"\n❌ Generatie gefaald: {metadata.get('error', 'Unknown error')}")

    def cmd_approve(self, args):
        """Keur definitie goed."""
        success = self.checker.approve_definition(
            definitie_id=args.id, approved_by=args.approved_by, notes=args.notes
        )

        if success:
            print(f"✅ Definitie {args.id} goedgekeurd door {args.approved_by}")
        else:
            print(f"❌ Kon definitie {args.id} niet goedkeuren")

    def cmd_status(self, args):
        """Wijzig status van definitie."""
        new_status = DefinitieStatus(args.status)

        success = self.repository.change_status(
            definitie_id=args.id,
            new_status=new_status,
            changed_by=args.changed_by,
            notes=args.notes,
        )

        if success:
            print(
                f"✅ Status van definitie {args.id} gewijzigd naar {new_status.value}"
            )
        else:
            print(f"❌ Kon status van definitie {args.id} niet wijzigen")

    def cmd_export(self, args):
        """Exporteer definities naar JSON."""
        filters = {}
        if args.status:
            filters["status"] = DefinitieStatus(args.status)
        if args.context:
            filters["organisatorische_context"] = args.context
        if args.categorie:
            filters["categorie"] = OntologischeCategorie(args.categorie)

        count = self.repository.export_to_json(args.file, filters)
        print(f"✅ {count} definities geëxporteerd naar {args.file}")

    def cmd_import(self, args):
        """Importeer definities uit JSON."""
        successful, failed, errors = self.repository.import_from_json(
            args.file, args.imported_by or "cli_user"
        )

        print("📥 IMPORT RESULTATEN:")
        print(f"✅ Succesvol: {successful}")
        print(f"❌ Gefaald: {failed}")

        if errors:
            print("\n⚠️ FOUTEN:")
            for error in errors[:5]:  # Toon eerste 5 fouten
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... en {len(errors) - 5} meer fouten")

    def cmd_stats(self, args):
        """Toon database statistieken."""
        stats = self.repository.get_statistics()

        print("📊 DATABASE STATISTIEKEN")
        print("=" * 30)
        print(f"Totaal definities: {stats['total_definities']}")

        print("\n📈 PER STATUS:")
        for status, count in stats["by_status"].items():
            print(f"   {status}: {count}")

        print("\n📂 PER CATEGORIE:")
        for categorie, count in stats["by_category"].items():
            print(f"   {categorie}: {count}")

        if stats["average_validation_score"]:
            print(
                f"\n🎯 Gemiddelde validation score: {stats['average_validation_score']}"
            )

    def cmd_pending(self, args):
        """Toon definities die wachten op goedkeuring."""
        pending = self.checker.get_pending_definitions()

        print("⏳ DEFINITIES IN REVIEW")
        print("=" * 30)

        if not pending:
            print("✅ Geen definities wachten op goedkeuring")
            return

        for definitie in pending:
            print(f"\n📋 {definitie.begrip} (ID: {definitie.id})")
            print(f"   Context: {definitie.organisatorische_context}")
            print(f"   Categorie: {definitie.categorie}")
            print(
                f"   Score: {definitie.validation_score:.2f}"
                if definitie.validation_score
                else "   Score: N/A"
            )
            print(f"   Aangemaakt: {definitie.created_at} door {definitie.created_by}")
            print(f"   Definitie: {definitie.definitie[:80]}...")

        print(f"\n📊 Totaal {len(pending)} definities in review")


def create_parser():
    """Maak argument parser voor CLI."""
    parser = argparse.ArgumentParser(
        description="Definitie Manager CLI - Beheer definitie database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  %(prog)s list --status established --context DJI
  %(prog)s check --begrip verificatie --context DJI --categorie proces
  %(prog)s generate --begrip toezicht --context OM --categorie proces
  %(prog)s approve --id 5 --approved-by admin
  %(prog)s export --file definities.json --status established
  %(prog)s import --file externe_definities.json
        """,
    )

    parser.add_argument("--db", help="Database bestand pad (default: auto)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Beschikbare commando's")

    # List command
    list_parser = subparsers.add_parser("list", help="Toon lijst van definities")
    list_parser.add_argument("--query", help="Zoekterm in begrip of definitie")
    list_parser.add_argument(
        "--status", choices=[s.value for s in DefinitieStatus], help="Filter op status"
    )
    list_parser.add_argument(
        "--categorie",
        choices=[c.value for c in OntologischeCategorie],
        help="Filter op categorie",
    )
    list_parser.add_argument("--context", help="Filter op organisatorische context")
    list_parser.add_argument(
        "--limit", type=int, default=20, help="Maximum aantal resultaten"
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Toon details van definitie")
    show_parser.add_argument("id", type=int, help="Definitie ID")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check voor duplicates")
    check_parser.add_argument("--begrip", required=True, help="Te checken begrip")
    check_parser.add_argument(
        "--context", required=True, help="Organisatorische context"
    )
    check_parser.add_argument("--juridische-context", help="Juridische context")
    check_parser.add_argument(
        "--categorie",
        required=True,
        choices=[c.value for c in OntologischeCategorie],
        help="Ontologische categorie",
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Genereer nieuwe definitie"
    )
    generate_parser.add_argument("--begrip", required=True, help="Te definiëren begrip")
    generate_parser.add_argument(
        "--context", required=True, help="Organisatorische context"
    )
    generate_parser.add_argument("--juridische-context", help="Juridische context")
    generate_parser.add_argument(
        "--categorie",
        required=True,
        choices=[c.value for c in OntologischeCategorie],
        help="Ontologische categorie",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Forceer nieuwe generatie ondanks duplicates",
    )
    generate_parser.add_argument("--created-by", help="Wie de definitie aanmaakt")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Keur definitie goed")
    approve_parser.add_argument("--id", type=int, required=True, help="Definitie ID")
    approve_parser.add_argument(
        "--approved-by", required=True, help="Wie de definitie goedkeurt"
    )
    approve_parser.add_argument("--notes", help="Goedkeuringsnotities")

    # Status command
    status_parser = subparsers.add_parser("status", help="Wijzig definitie status")
    status_parser.add_argument("--id", type=int, required=True, help="Definitie ID")
    status_parser.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in DefinitieStatus],
        help="Nieuwe status",
    )
    status_parser.add_argument("--changed-by", help="Wie de wijziging uitvoert")
    status_parser.add_argument("--notes", help="Wijzigingsnotities")

    # Export command
    export_parser = subparsers.add_parser("export", help="Exporteer definities")
    export_parser.add_argument("--file", required=True, help="Export bestand pad")
    export_parser.add_argument(
        "--status", choices=[s.value for s in DefinitieStatus], help="Filter op status"
    )
    export_parser.add_argument("--context", help="Filter op organisatorische context")
    export_parser.add_argument(
        "--categorie",
        choices=[c.value for c in OntologischeCategorie],
        help="Filter op categorie",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Importeer definities")
    import_parser.add_argument("--file", required=True, help="Import bestand pad")
    import_parser.add_argument("--imported-by", help="Wie de import uitvoert")

    # Stats command
    subparsers.add_parser("stats", help="Toon database statistieken")

    # Pending command
    subparsers.add_parser("pending", help="Toon definities in review")

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize CLI
        cli = DefinitieManagerCLI(args.db)

        # Execute command
        command_method = getattr(cli, f"cmd_{args.command}")
        command_method(args)

    except Exception as e:
        print(f"❌ Fout: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
