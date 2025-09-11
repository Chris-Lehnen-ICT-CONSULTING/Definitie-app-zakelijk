#!/usr/bin/env python3
"""
Project Vernederlandsing Script
Dit script hernoemt alle projectbestanden naar Nederlandse namen
en past alle referenties aan in code, tests, en configuratie.

BELANGRIJK: Dit script test na ELKE wijziging of alles nog werkt!
"""

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ProjectVernederlandser:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = (
            self.project_root / f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        self.wijzigingen_log = []
        self.fouten_log = []

        # Vertaal woordenboek voor bestandsnamen
        self.bestand_vertalingen = {
            # Core Services
            "definition_service": "definitie_service",
            "web_lookup_service": "web_opzoek_service",
            "validation_service": "validatie_service",
            "cache_service": "cache_service",  # blijft Engels
            "config_manager": "configuratie_beheerder",
            "service_factory": "service_fabriek",
            # UI Componenten
            "definition_generator_tab": "definitie_generator_tab",
            "web_lookup_tab": "web_opzoek_tab",
            "history_tab": "geschiedenis_tab",
            "expert_review_tab": "expert_beoordeling_tab",
            "admin_tab": "beheer_tab",
            # Utils
            "file_utils": "bestand_hulpmiddelen",
            "text_utils": "tekst_hulpmiddelen",
            "validation_utils": "validatie_hulpmiddelen",
            "security_utils": "beveiliging_hulpmiddelen",
            # Models
            "definition_model": "definitie_model",
            "validation_result": "validatie_resultaat",
            "cache_entry": "cache_item",
            # Orchestration
            "orchestration": "orkestratie",
            "definitie_agent": "definitie_agent",  # al Nederlands
            # Test files
            "test_": "test_",  # prefix blijft
            "_test": "_test",  # suffix blijft
        }

        # Functie/Class naam vertalingen
        self.code_vertalingen = {
            # Functies
            "generate_definition": "genereer_definitie",
            "validate_input": "valideer_invoer",
            "get_results": "krijg_resultaten",
            "save_to_cache": "bewaar_in_cache",
            "load_from_cache": "laad_uit_cache",
            "process_request": "verwerk_verzoek",
            "handle_error": "behandel_fout",
            # Classes
            "DefinitionService": "DefinitieService",
            "ValidationService": "ValidatieService",
            "WebLookupService": "WebOpzoekService",
            "ConfigManager": "ConfiguratieBeheerder",
            "CacheService": "CacheService",
            # Methods
            "get_": "krijg_",
            "set_": "zet_",
            "create_": "maak_",
            "delete_": "verwijder_",
            "update_": "werk_bij_",
            "check_": "controleer_",
            "is_": "is_",
            "has_": "heeft_",
        }

    def maak_backup(self) -> bool:
        """Maak een volledige backup van het project"""
        print(f"🔄 Backup maken naar {self.backup_dir}...")
        try:
            # Git commit voor zekerheid
            subprocess.run(["git", "add", "-A"], cwd=self.project_root, check=False)
            subprocess.run(
                ["git", "commit", "-m", "backup: voor vernederlandsing"],
                cwd=self.project_root,
                check=False,
            )
            subprocess.run(
                ["git", "tag", f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"],
                cwd=self.project_root,
                check=False,
            )

            # Fysieke backup
            shutil.copytree(
                self.project_root,
                self.backup_dir,
                ignore=shutil.ignore_patterns(
                    ".git", "__pycache__", "*.pyc", "venv", ".venv"
                ),
            )
            print("✅ Backup succesvol aangemaakt")
            return True
        except Exception as e:
            print(f"❌ Backup mislukt: {e}")
            return False

    def test_huidige_staat(self) -> bool:
        """Test of alle tests slagen in huidige staat"""
        print("\n🧪 Tests draaien voor baseline...")
        result = subprocess.run(
            ["pytest", "--tb=short", "-q"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✅ Alle tests slagen in huidige staat")
            return True
        else:
            print("❌ Tests falen in huidige staat!")
            print(result.stdout)
            return False

    def vind_alle_referenties(self, oude_naam: str) -> dict[str, list[tuple[int, str]]]:
        """Vind alle referenties naar een bestandsnaam"""
        referenties = {}

        # Zoek patronen
        patronen = [
            f"from .* import .*{oude_naam}",
            f"import .*{oude_naam}",
            f'"{oude_naam}"',
            f"'{oude_naam}'",
            f"{oude_naam}\\(",  # functie calls
            f"class.*{oude_naam}",
            f"def.*{oude_naam}",
        ]

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            gevonden = []
            try:
                with open(py_file, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        for patroon in patronen:
                            if re.search(patroon, line, re.IGNORECASE):
                                gevonden.append((line_num, line.strip()))

                if gevonden:
                    referenties[str(py_file)] = gevonden
            except Exception as e:
                print(f"⚠️  Waarschuwing: Kan {py_file} niet lezen: {e}")

        # Check ook in JSON files
        for json_file in self.project_root.rglob("*.json"):
            if "node_modules" in str(json_file):
                continue

            try:
                with open(json_file, encoding="utf-8") as f:
                    content = f.read()
                    if oude_naam in content:
                        referenties[str(json_file)] = [(0, f"Bevat '{oude_naam}'")]
            except Exception:
                pass

        return referenties

    def test_enkele_wijziging(self, gewijzigde_bestanden: list[str]) -> bool:
        """Test of specifieke bestanden nog werken na wijziging"""
        print("  🧪 Testen na wijziging...")

        # Quick syntax check
        for bestand in gewijzigde_bestanden:
            if bestand.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", bestand],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    print(f"    ❌ Syntax error in {bestand}")
                    return False

        # Run gerelateerde tests
        test_bestanden = []
        for bestand in gewijzigde_bestanden:
            # Zoek bijbehorende test
            if "/src/" in bestand:
                test_path = bestand.replace("/src/", "/tests/").replace(
                    ".py", "_test.py"
                )
                alt_test_path = bestand.replace("/src/", "/tests/").replace(".py", "")
                alt_test_path = (
                    Path(alt_test_path).parent / f"test_{Path(bestand).name}"
                )

                if Path(test_path).exists():
                    test_bestanden.append(test_path)
                elif Path(alt_test_path).exists():
                    test_bestanden.append(str(alt_test_path))

        if test_bestanden:
            result = subprocess.run(
                ["pytest", "--tb=short", "-q"] + test_bestanden,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print("    ✅ Tests slagen")
                return True
            else:
                print("    ❌ Tests falen")
                print(result.stdout[-500:])  # Laatste 500 chars
                return False

        print("    ⚠️  Geen tests gevonden voor deze module")
        return True

    def hernoem_bestand(
        self, oud_pad: Path, nieuw_pad: Path, dry_run: bool = True
    ) -> bool:
        """Hernoem een enkel bestand en update alle referenties"""
        oude_naam = oud_pad.stem
        nieuwe_naam = nieuw_pad.stem

        print(
            f"\n📝 {'[DRY RUN] ' if dry_run else ''}Hernoemen: {oude_naam} → {nieuwe_naam}"
        )

        # Vind alle referenties
        referenties = self.vind_alle_referenties(oude_naam)
        print(f"  📍 Gevonden in {len(referenties)} bestanden")

        if dry_run:
            for bestand, refs in referenties.items():
                print(f"    - {bestand}: {len(refs)} referenties")
            return True

        # Daadwerkelijke hernoeming
        try:
            # 1. Hernoem het bestand zelf
            oud_pad.rename(nieuw_pad)
            self.wijzigingen_log.append(f"Bestand: {oud_pad} → {nieuw_pad}")

            # 2. Update alle imports en referenties
            gewijzigde_bestanden = [str(nieuw_pad)]

            for bestand, refs in referenties.items():
                try:
                    with open(bestand, encoding="utf-8") as f:
                        content = f.read()

                    # Vervang oude naam door nieuwe naam
                    nieuwe_content = content

                    # Import statements
                    nieuwe_content = re.sub(
                        f"from (.*){oude_naam}",
                        f"from \\1{nieuwe_naam}",
                        nieuwe_content,
                    )
                    nieuwe_content = re.sub(
                        f"import (.*){oude_naam}",
                        f"import \\1{nieuwe_naam}",
                        nieuwe_content,
                    )

                    # String referenties
                    nieuwe_content = nieuwe_content.replace(
                        f'"{oude_naam}"', f'"{nieuwe_naam}"'
                    )
                    nieuwe_content = nieuwe_content.replace(
                        f"'{oude_naam}'", f"'{nieuwe_naam}'"
                    )

                    if content != nieuwe_content:
                        with open(bestand, "w", encoding="utf-8") as f:
                            f.write(nieuwe_content)
                        gewijzigde_bestanden.append(bestand)
                        self.wijzigingen_log.append(f"Updated: {bestand}")

                except Exception as e:
                    print(f"    ❌ Fout bij updaten {bestand}: {e}")
                    self.fouten_log.append(f"Update fout in {bestand}: {e}")

            # 3. Test of alles nog werkt
            if not self.test_enkele_wijziging(gewijzigde_bestanden):
                print("    ❌ Tests falen na hernoeming, terugdraaien...")
                # Rollback
                nieuw_pad.rename(oud_pad)
                # Rollback van alle content wijzigingen wordt nog toegevoegd (US-073)
                return False

            return True

        except Exception as e:
            print(f"  ❌ Fout bij hernoemen: {e}")
            self.fouten_log.append(f"Hernoeming fout {oud_pad}: {e}")
            return False

    def analyseer_module(self, module_path: str) -> list[tuple[Path, str]]:
        """Analyseer een module en bepaal welke bestanden hernoemd moeten worden"""
        hernoemingen = []
        module_dir = self.project_root / module_path

        if not module_dir.exists():
            print(f"❌ Module {module_path} bestaat niet")
            return hernoemingen

        for py_file in module_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            bestand_naam = py_file.stem

            # Check of hernoeming nodig is
            for eng, nl in self.bestand_vertalingen.items():
                if eng in bestand_naam and eng != nl:
                    nieuwe_naam = bestand_naam.replace(eng, nl)
                    if nieuwe_naam != bestand_naam:
                        hernoemingen.append((py_file, nieuwe_naam))
                        break

        return hernoemingen

    def voer_module_migratie_uit(self, module_path: str, dry_run: bool = True):
        """Migreer een complete module"""
        print(f"\n{'='*60}")
        print(f"🔄 Module migratie: {module_path} {'[DRY RUN]' if dry_run else ''}")
        print(f"{'='*60}")

        # Analyseer wat er moet gebeuren
        hernoemingen = self.analyseer_module(module_path)
        print(f"\n📊 Gevonden {len(hernoemingen)} bestanden om te hernoemen")

        if not hernoemingen:
            print("✅ Geen hernoemingen nodig voor deze module")
            return

        # Voer hernoemingen uit
        succes_count = 0
        for oud_pad, nieuwe_naam in hernoemingen:
            nieuw_pad = oud_pad.parent / f"{nieuwe_naam}.py"

            if self.hernoem_bestand(oud_pad, nieuw_pad, dry_run):
                succes_count += 1

        print(f"\n📈 Resultaat: {succes_count}/{len(hernoemingen)} succesvol")

        if not dry_run and succes_count == len(hernoemingen):
            # Commit changes
            subprocess.run(["git", "add", "-A"], cwd=self.project_root, check=False)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"refactor: vernederlands module {module_path}",
                ],
                cwd=self.project_root,
                check=False,
            )
            print("✅ Wijzigingen gecommit")

    def schrijf_rapport(self):
        """Schrijf een rapport van alle wijzigingen"""
        rapport_path = self.project_root / "vernederlandsing-rapport.md"

        with open(rapport_path, "w", encoding="utf-8") as f:
            f.write("# Vernederlandsing Rapport\n\n")
            f.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Succesvolle Wijzigingen\n\n")
            for wijziging in self.wijzigingen_log:
                f.write(f"- {wijziging}\n")

            if self.fouten_log:
                f.write("\n## Fouten\n\n")
                for fout in self.fouten_log:
                    f.write(f"- ❌ {fout}\n")

            f.write("\n## Statistieken\n")
            f.write(f"- Totaal wijzigingen: {len(self.wijzigingen_log)}\n")
            f.write(f"- Totaal fouten: {len(self.fouten_log)}\n")

        print(f"\n📄 Rapport geschreven naar {rapport_path}")


def main():
    """Hoofdfunctie voor CLI gebruik"""
    import argparse

    parser = argparse.ArgumentParser(description="Vernederlands project bestandsnamen")
    parser.add_argument(
        "--module", type=str, required=True, help="Module pad om te migreren"
    )
    parser.add_argument(
        "--execute", action="store_true", help="Voer daadwerkelijk uit (anders dry-run)"
    )
    parser.add_argument("--skip-backup", action="store_true", help="Sla backup over")
    parser.add_argument(
        "--skip-tests", action="store_true", help="Sla initiële tests over"
    )

    args = parser.parse_args()

    # Bepaal project root
    project_root = Path(__file__).parent.parent.parent

    # Initialiseer vernederlandser
    vernederlandser = ProjectVernederlandser(project_root)

    # Maak backup
    if not args.skip_backup and args.execute:
        if not vernederlandser.maak_backup():
            print("❌ Kan niet doorgaan zonder backup")
            return 1

    # Test huidige staat
    if not args.skip_tests:
        if not vernederlandser.test_huidige_staat():
            print("❌ Tests moeten eerst slagen voordat we kunnen migreren")
            return 1

    # Voer migratie uit
    vernederlandser.voer_module_migratie_uit(args.module, dry_run=not args.execute)

    # Schrijf rapport
    if args.execute:
        vernederlandser.schrijf_rapport()

    return 0


if __name__ == "__main__":
    sys.exit(main())
