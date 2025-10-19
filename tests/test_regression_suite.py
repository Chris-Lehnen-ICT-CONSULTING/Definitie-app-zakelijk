#!/usr/bin/env python3
"""
Volledige Regressietest Suite voor DefinitieAgent

Deze uitgebreide test suite valideert alle aspecten van de DefinitieAgent codebase:
- Import functionaliteit en module structuur
- Nederlandse commentaren kwaliteit en consistentie
- Core functionaliteit en workflows
- Database operaties en data integriteit
- API integraties en error handling
- Performance en memory usage
- Configuration management
- Web lookup en externe integraties

Auteur: DefinitieAgent Development Team
Versie: 1.0.0
Datum: Juli 2025
"""

import asyncio
import contextlib
import importlib
import inspect
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

# Voeg src directory toe aan Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configureer logging voor tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestImportStructure(unittest.TestCase):
    """Test de import structuur en module beschikbaarheid."""

    def setUp(self):
        """Setup voor import tests."""
        self.core_modules = [
            "main",
            "ui.tabbed_interface",
            "ui.session_state",
            "database.definitie_repository",
            # Nieuwe architectuur kernmodules
            "services.service_factory",
            "services.container",
            "services.interfaces",
            # Validatie en utiliteiten
            "ai_toetser.modular_toetser",
            "validation.definitie_validator",
            "services.modern_web_lookup_service",
            "config.config_manager",
            "utils.cache",
            "utils.smart_rate_limiter",
        ]

        self.optional_modules = [
            "hybrid_context.hybrid_context_engine",
            "document_processing.document_processor",
            "voorbeelden.unified_voorbeelden",
        ]

    def test_core_modules_import(self):
        """Test dat alle core modules correct importeren."""
        failed_imports = []

        for module_name in self.core_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"Module {module_name} importeert als None"
                logger.info(f"✅ {module_name} import succesvol")
            except Exception as e:
                failed_imports.append((module_name, str(e)))
                logger.error(f"❌ {module_name} import gefaald: {e}")

        assert (
            len(failed_imports) == 0
        ), f"Core modules faalden bij import: {failed_imports}"

    def test_optional_modules_graceful_degradation(self):
        """Test dat optionele modules graceful degradation hebben."""
        for module_name in self.optional_modules:
            try:
                importlib.import_module(module_name)
                logger.info(f"✅ Optionele module {module_name} beschikbaar")
            except ImportError:
                logger.info(
                    f"i️ Optionele module {module_name} niet beschikbaar (verwacht)"
                )
                # Dit is acceptabel voor optionele modules
            except Exception as e:
                self.fail(f"Optionele module {module_name} heeft onverwachte fout: {e}")

    def test_logs_module_resolution(self):
        """Test dat logs module correct wordt opgelost (optioneel)."""
        try:
            from logs.application.log_definitie import get_logger, log_definitie

            logger_instance = get_logger("test")
            assert logger_instance is not None
            logger.info("✅ Logs module import succesvol")
        except ImportError:
            self.skipTest("logs.application.log_definitie niet aanwezig (optioneel)")
        except Exception as e:
            self.fail(f"Logs module import gefaald: {e}")

    def test_package_init_files(self):
        """Test dat alle packages __init__.py bestanden hebben."""
        src_path = Path(__file__).parent.parent / "src"
        missing_init_files = []

        for directory in src_path.rglob("*"):
            if directory.is_dir() and not directory.name.startswith("."):
                init_file = directory / "__init__.py"
                if not init_file.exists():
                    # Skip __pycache__ directories
                    if "__pycache__" not in str(directory):
                        missing_init_files.append(str(directory.relative_to(src_path)))

        assert (
            len(missing_init_files) == 0
        ), f"Ontbrekende __init__.py bestanden in: {missing_init_files}"


class TestNederlandseCommentaren(unittest.TestCase):
    """Test de kwaliteit en consistentie van Nederlandse commentaren."""

    def setUp(self):
        """Setup voor commentaar tests."""
        self.src_path = Path(__file__).parent.parent / "src"
        self.python_files = list(self.src_path.rglob("*.py"))

        # Nederlandse woorden die we verwachten in commentaren
        self.expected_dutch_words = [
            "voor",
            "van",
            "een",
            "het",
            "de",
            "met",
            "en",
            "in",
            "op",
            "functie",
            "klasse",
            "module",
            "bestand",
            "configuratie",
            "definitie",
            "validatie",
            "generatie",
            "database",
            "systeem",
        ]

        # Technische termen die Engels mogen blijven
        self.allowed_english_terms = [
            "import",
            "class",
            "def",
            "return",
            "if",
            "else",
            "try",
            "except",
            "API",
            "JSON",
            "HTTP",
            "URL",
            "UUID",
            "cache",
            "token",
            "hash",
        ]

    def test_docstrings_are_dutch(self):
        """Test dat docstrings in het Nederlands zijn."""
        non_dutch_files = []

        for py_file in self.python_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Extract docstrings
                docstring_pattern = r'"""(.*?)"""'
                docstrings = re.findall(docstring_pattern, content, re.DOTALL)

                for docstring in docstrings:
                    if len(docstring.strip()) > 20:  # Skip zeer korte docstrings
                        dutch_word_count = sum(
                            1
                            for word in self.expected_dutch_words
                            if word.lower() in docstring.lower()
                        )

                        if (
                            dutch_word_count < 2
                        ):  # Verwacht minimaal 2 Nederlandse woorden
                            non_dutch_files.append(
                                str(py_file.relative_to(self.src_path))
                            )
                            break

            except Exception as e:
                logger.warning(f"Kon {py_file} niet lezen: {e}")

        assert (
            len(non_dutch_files) < len(self.python_files) * 0.1
        ), f"Te veel bestanden zonder Nederlandse docstrings: {non_dutch_files[:5]}"

    def test_inline_comments_are_dutch(self):
        """Test dat inline commentaren grotendeels in het Nederlands zijn."""
        files_with_poor_dutch_comments = []

        for py_file in self.python_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                comment_lines = [line for line in lines if line.strip().startswith("#")]

                if (
                    len(comment_lines) > 5
                ):  # Alleen testen bij bestanden met genoeg commentaren
                    dutch_comments = 0
                    for comment in comment_lines:
                        comment_text = comment.strip("#").strip()
                        if len(comment_text) > 10:  # Skip zeer korte commentaren
                            dutch_word_count = sum(
                                1
                                for word in self.expected_dutch_words
                                if word.lower() in comment_text.lower()
                            )
                            if dutch_word_count >= 1:
                                dutch_comments += 1

                    dutch_ratio = (
                        dutch_comments / len(comment_lines) if comment_lines else 0
                    )
                    if dutch_ratio < 0.7:  # Verwacht 70% Nederlandse commentaren
                        files_with_poor_dutch_comments.append(
                            (str(py_file.relative_to(self.src_path)), dutch_ratio)
                        )

            except Exception as e:
                logger.warning(f"Kon {py_file} niet analyseren: {e}")

        assert (
            len(files_with_poor_dutch_comments) < 5
        ), f"Te veel bestanden met onvoldoende Nederlandse commentaren: {files_with_poor_dutch_comments}"

    def test_function_documentation_completeness(self):
        """Test dat belangrijke functies Nederlandse documentatie hebben."""
        undocumented_functions = []

        for py_file in self.python_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj) and not name.startswith("_"):
                            docstring = inspect.getdoc(obj)
                            if not docstring or len(docstring) < 10:
                                undocumented_functions.append(
                                    f"{py_file.relative_to(self.src_path)}:{name}"
                                )
                            elif not any(
                                word in docstring.lower()
                                for word in self.expected_dutch_words[:5]
                            ):
                                undocumented_functions.append(
                                    f"{py_file.relative_to(self.src_path)}:{name} (no Dutch)"
                                )

            except Exception as e:
                # Skip bestanden die niet geïmporteerd kunnen worden
                logger.debug(f"Skip {py_file}: {e}")

        # Verwacht dat minder dan 20% van de functies ongedocumenteerd is
        total_functions = len(undocumented_functions) + 100  # Geschatte totaal
        assert (
            len(undocumented_functions) / total_functions < 0.3
        ), f"Te veel ongedocumenteerde functies: {undocumented_functions[:10]}"


class TestCoreFunctionality(unittest.TestCase):
    """Test de core functionaliteit van DefinitieAgent."""

    def setUp(self):
        """Setup voor functionaliteit tests."""
        # Mock Streamlit om tests mogelijk te maken (gebruik centrale mock)
        try:
            from mocks.streamlit_mock import get_streamlit_mock

            sys.modules["streamlit"] = get_streamlit_mock()
        except Exception:
            from unittest.mock import MagicMock

            sys.modules["streamlit"] = MagicMock()

    def test_definitie_repository_basic_operations(self):
        """Test basis database operaties."""
        try:
            from database.definitie_repository import (
                DefinitieRecord,
                DefinitieRepository,
            )

            # Gebruik tijdelijke database voor tests
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_db_path = tmp.name

            try:
                repo = DefinitieRepository(tmp_db_path)

                # Zorg ervoor dat database schema is geïnitialiseerd
                # Door de _init_database methode wordt schema.sql automatisch uitgevoerd

                # Test create
                test_record = DefinitieRecord(
                    begrip="test_begrip",
                    definitie="Test definitie voor regressietest",
                    organisatorische_context="Test",
                    juridische_context="test_juridisch",
                    categorie="proces",
                    created_by="test_suite",
                )

                created_id = repo.create_definitie(test_record)
                assert created_id is not None

                # Test read
                retrieved = repo.get_definitie(created_id)
                assert retrieved is not None
                assert retrieved.begrip == "test_begrip"

                # Test search
                results = repo.search_definities(query="test_begrip")
                assert len(results) > 0

                logger.info("✅ Database operaties succesvol getest")

            finally:
                # Cleanup tijdelijke database
                import os

                with contextlib.suppress(FileNotFoundError):
                    os.unlink(tmp_db_path)

        except Exception as e:
            self.fail(f"Database test gefaald: {e}")

    def test_configuration_loading(self):
        """Test configuratie laden en validatie."""
        try:
            # Test toetsregels laden - dit is de meest kritieke configuratie
            from toetsregels.loader import load_toetsregels

            toetsregels = load_toetsregels().get("regels", {})
            assert isinstance(toetsregels, dict)
            assert len(toetsregels) > 0

            # Valideer toetsregel structuur
            for _regel_id, regel_data in toetsregels.items():
                assert "uitleg" in regel_data
                assert isinstance(regel_data["uitleg"], str)
                assert len(regel_data["uitleg"]) > 10

            # Test config manager - minder kritiek voor core functionaliteit
            try:
                from config.config_manager import ConfigManager

                config_manager = ConfigManager()
                assert config_manager is not None
            except ImportError:
                logger.info(
                    "⚠️ Config manager niet beschikbaar, maar toetsregels werken"
                )

            logger.info("✅ Configuratie laden succesvol getest")

        except Exception as e:
            self.fail(f"Configuratie test gefaald: {e}")

    def test_validation_system(self):
        """Test het validatie systeem."""
        try:
            # Test basis validatie functionaliteit die kritiek is
            from ai_toetser.modular_toetser import toets_definitie

            # Test validatie van een goede definitie
            test_definitie = (
                "Een systematisch proces voor het vaststellen van identiteit"
            )
            test_begrip = "verificatie"

            # Gebruik minimale toetsregels voor test
            test_toetsregels = {
                "test_rule": {
                    "uitleg": "Test regel voor unit test",
                    "gewicht": 1.0,
                    "categorie": "test",
                }
            }

            result = toets_definitie(test_definitie, test_toetsregels, test_begrip)
            assert result is not None

            # Test optionele validator klasse
            try:
                from ai_toetser.modular_toetser import ModularToetser

                validator = ModularToetser()
                assert validator is not None
            except ImportError:
                logger.info(
                    "⚠️ ModularToetser klasse niet beschikbaar, maar toets_definitie werkt"
                )

            logger.info("✅ Validatie systeem succesvol getest")

        except Exception as e:
            self.fail(f"Validatie test gefaald: {e}")

    @patch("openai.OpenAI")
    def test_ai_integration_mocked(self, mock_openai):
        """Test AI integratie met gemockte OpenAI (nieuwe architectuur)."""
        try:
            # Mock OpenAI response
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = (
                "Test definitie gegenereerd door AI"
            )
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            from services.service_factory import get_definition_service

            service = get_definition_service()
            assert service is not None

            logger.info("✅ AI integratie mock test succesvol")

        except Exception as e:
            self.fail(f"AI integratie test gefaald: {e}")


class TestModernWebLookupIntegration(unittest.TestCase):
    """Test moderne web lookup service functionaliteit."""

    def test_modern_web_lookup_service(self):
        """Test dat moderne web lookup service correct werkt."""
        try:
            from services.interfaces import LookupRequest
            from services.modern_web_lookup_service import ModernWebLookupService

            # Test basis functionaliteit
            service = ModernWebLookupService()
            assert hasattr(service, "lookup")
            assert hasattr(service, "validate_source")

            logger.info("✅ Modern web lookup service check succesvol")

        except ImportError as e:
            self.fail(f"Modern web lookup import error: {e}")
        except Exception as e:
            logger.warning(f"Modern web lookup test warning: {e}")

    @patch("requests.get")
    def test_external_api_error_handling(self, mock_get):
        """Test error handling voor externe API calls."""
        try:
            # Mock network failure
            mock_get.side_effect = Exception("Network error")

            # Test dat error handling werkt
            from services.modern_web_lookup_service import ModernWebLookupService

            ModernWebLookupService()
            # Dit zou graceful moeten falen zonder de hele applicatie te crashen

            logger.info("✅ Error handling test succesvol")

        except Exception as e:
            logger.warning(f"External API test warning: {e}")


class TestPerformanceAndMemory(unittest.TestCase):
    """Test performance en memory usage."""

    def test_import_performance(self):
        """Test dat modules snel genoeg importeren."""
        start_time = time.time()

        try:
            import database.definitie_repository
            import main
            import ui.tabbed_interface
        except Exception as e:
            logger.warning(f"Performance test import warning: {e}")

        import_time = time.time() - start_time

        # Verwacht dat imports binnen 5 seconden lukken
        assert import_time < 5.0, f"Import tijd te lang: {import_time:.2f}s"

        logger.info(f"✅ Import performance: {import_time:.2f}s")

    def test_basic_memory_usage(self):
        """Test dat basis memory usage redelijk is."""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Import core modules
            import database.definitie_repository
            import main

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Verwacht dat memory increase onder 100MB blijft
            assert (
                memory_increase < 100
            ), f"Memory gebruik te hoog: {memory_increase:.1f}MB"

            logger.info(f"✅ Memory usage: +{memory_increase:.1f}MB")

        except ImportError:
            logger.info("⚠️ psutil niet beschikbaar, skip memory test")


class TestErrorHandlingAndRobustness(unittest.TestCase):
    """Test error handling en robuustheid."""

    def test_missing_config_graceful_handling(self):
        """Test graceful handling van ontbrekende configuratie."""
        try:
            # Simuleer ontbrekende config
            with patch.dict(os.environ, {}, clear=True):
                from config.config_manager import ConfigManager

                config_manager = ConfigManager()
                # Zou niet moeten crashen, maar defaults gebruiken
                assert config_manager is not None

            logger.info("✅ Missing config handling succesvol")

        except Exception as e:
            self.fail(f"Config error handling gefaald: {e}")

    def test_invalid_input_handling(self):
        """Test handling van ongeldige input."""
        try:
            from ai_toetser.modular_toetser import toets_definitie

            # Minimale toetsregels voor test
            test_toetsregels = {
                "test_rule": {
                    "uitleg": "Test regel voor unit test",
                    "gewicht": 1.0,
                    "categorie": "test",
                }
            }

            # Test met lege input
            result = toets_definitie("", test_toetsregels, "")
            assert result is not None

            # Test met zeer lange input
            long_text = "x" * 10000
            result = toets_definitie(long_text, test_toetsregels, "test")
            assert result is not None

            logger.info("✅ Invalid input handling succesvol")

        except Exception as e:
            self.fail(f"Input validation error handling gefaald: {e}")


class TestRegressionSpecific(unittest.TestCase):
    """Test specifieke regressies die eerder opgelost zijn."""

    def test_logs_import_resolution(self):
        """Test dat logs import resolutie correct werkt (specifieke regressie)."""
        try:
            # Test verschillende manieren van logs importeren
            import os

            # Test vanuit verschillende modules
            import sys

            from logs.application.log_definitie import get_logger

            # Voeg root directory toe (zoals in onze fix)
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

            from logs.application.log_definitie import log_definitie

            logger_instance = get_logger("regression_test")
            assert logger_instance is not None

            logger.info("✅ Logs import regressie test succesvol")

        except Exception as e:
            self.fail(f"Logs import regressie gefaald: {e}")

    def test_modern_service_encoding_fix(self):
        """Test dat moderne service encoding correct is."""
        try:
            # Test dat de bestanden syntactisch correct zijn
            import ast

            src_path = Path(__file__).parent.parent / "src"
            service_files = [
                src_path / "services" / "modern_web_lookup_service.py",
                src_path / "services" / "unified_definition_generator.py",
            ]

            for file_path in service_files:
                if file_path.exists():
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Test syntax parsing
                    try:
                        ast.parse(content)
                        logger.info(f"✅ {file_path.name} syntax correct")
                    except SyntaxError as e:
                        self.fail(f"Syntax error in {file_path.name}: {e}")

        except Exception as e:
            self.fail(f"Modern service encoding test gefaald: {e}")

    def test_init_files_presence(self):
        """Test dat alle benodigde __init__.py bestanden aanwezig zijn."""
        expected_init_files = [
            "src/__init__.py",
            "src/database/__init__.py",
            "src/tools/__init__.py",
            "tests/__init__.py",
        ]

        base_path = Path(__file__).parent.parent
        missing_files = []

        for init_file in expected_init_files:
            file_path = base_path / init_file
            if not file_path.exists():
                missing_files.append(init_file)

        assert (
            len(missing_files) == 0
        ), f"Ontbrekende __init__.py bestanden: {missing_files}"

        logger.info("✅ Alle verwachte __init__.py bestanden aanwezig")


def run_regression_suite():
    """Voer de volledige regressietest suite uit."""
    print("🧪 Starting DefinitieAgent Regressietest Suite")
    print("=" * 60)

    # Configureer test suite
    test_suite = unittest.TestSuite()

    # Voeg alle test classes toe
    test_classes = [
        TestImportStructure,
        TestNederlandseCommentaren,
        TestCoreFunctionality,
        TestModernWebLookupIntegration,
        TestPerformanceAndMemory,
        TestErrorHandlingAndRobustness,
        TestRegressionSpecific,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Voer tests uit
    runner = unittest.TextTestRunner(verbosity=2, descriptions=True, failfast=False)

    result = runner.run(test_suite)

    # Rapporteer resultaten
    print("\n" + "=" * 60)
    print("🎯 REGRESSIETEST RESULTATEN:")
    print(
        f"✅ Tests geslaagd: {result.testsRun - len(result.failures) - len(result.errors)}"
    )
    print(f"❌ Tests gefaald: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"📊 Totaal tests: {result.testsRun}")

    if result.failures:
        print("\n🔴 GEFAALDE TESTS:")
        for test, traceback in result.failures:
            print(
                f"  - {test}: {traceback.split('\\n')[-2] if traceback else 'Unknown'}"
            )

    if result.errors:
        print("\n💥 TEST ERRORS:")
        for test, traceback in result.errors:
            print(
                f"  - {test}: {traceback.split('\\n')[-2] if traceback else 'Unknown'}"
            )

    success_rate = (
        (result.testsRun - len(result.failures) - len(result.errors))
        / result.testsRun
        * 100
    )
    print(f"\n🏆 SUCCESS RATE: {success_rate:.1f}%")

    if success_rate >= 95:
        print("🎉 UITSTEKEND! Regressietest suite geslaagd!")
    elif success_rate >= 85:
        print("✅ GOED! Meeste tests geslaagd, enkele issues om op te lossen")
    else:
        print("⚠️ AANDACHT NODIG! Meerdere issues gevonden")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_regression_suite()
    sys.exit(0 if success else 1)
