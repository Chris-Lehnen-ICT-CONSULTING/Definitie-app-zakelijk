"""
PER-007 RED Phase Tests: Single Source of Truth
These tests MUST fail initially - proving multiple paths exist for context processing.

DEF-519 — de zes node-intenties en hun inhoudelijke assertions zijn behouden;
alleen de fixtures zijn actueel gemaakt:

* de bronscans waren CWD-relatief en verborgen lees-/parsefouten achter
  `except Exception: pass`; ze lopen nu vanaf de projectroot (`__file__`) met
  verplichte, niet-lege bestand- én functiescope en zichtbare fouten;
* `HybridContextManager` vereist een `ContextConfig`;
* de entry-pointtest slikte constructorfouten in en telde daardoor routes die
  helemaal niet werkten; constructie gebeurt nu echt en fouten propageren;
* de legacy-import ving elke `ImportError`; alleen een exact passende
  `ModuleNotFoundError.name` telt als "bestaat niet" — een kapotte dependency
  wordt niet stil groen.

Dit zijn historische bron- en interfaceheuristieken op namen en attributen. Zij
bewijzen niet dat de architectuur als geheel correct is. Waar de huidige code de
gewenste single-source-/UI-laag-/deprecatiekeuze niet levert, blijft de node
positief rood: owner testdispositie DEF-519; inhoudelijke hersteleigenaar niet
vastgesteld; trigger = vrijgegeven architectuurherstel; herbeoordeling
2026-10-06. Geen skip/xfail, geen filters, niets nagebouwd.
"""

import ast
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.red_phase]

# `advisory`-dispositie (DEF-519) op vier van de zeven nodes; de drie zonder
# marker toetsen actief geblokkeerde legacypaden en blijven verplicht. Elke node
# is afzonderlijk aan het actieve contract getoetst — geen generiek
# red_phase-filter, geen nieuwe skip of xfail.
# Owner: testdispositie-519, inhoudelijke owner niet vastgesteld.
# Trigger: vrijgegeven PER007-herstel.
# Herbeoordeling: 2026-10-06.

PROJECTWORTEL = Path(__file__).resolve().parents[2]
BRON = PROJECTWORTEL / "src"
UI_BRON = BRON / "ui"


def python_bestanden(map_: Path) -> list[Path]:
    """Alle .py-bestanden onder `map_`; ontbrekende of lege scope is een fout.

    Zonder deze controle kan een verkeerde root een lege scan opleveren en
    wordt `0 == 0` als bewijs gelezen.
    """
    assert map_.is_dir(), f"bronmap ontbreekt: {map_}"
    bestanden = sorted(map_.rglob("*.py"))
    assert bestanden, f"geen Python-bronbestanden gevonden in {map_}"
    return bestanden


class TestSingleSourceOfTruth:
    """Tests that MUST fail initially - proving multiple paths exist"""

    @pytest.mark.red_phase
    @pytest.mark.advisory
    def test_only_one_context_processing_path_exists(self):
        """MUST FAIL: Currently multiple paths exist for context processing"""
        context_paths = []
        onderzochte_functies = 0

        # Scan for context processing functions — lees- en parsefouten zijn
        # zichtbaar, niet weggevangen.
        for filepath in python_bestanden(BRON):
            content = filepath.read_text(encoding="utf-8")
            if "build" not in content or "context" not in content:
                continue

            tree = ast.parse(content, filename=str(filepath))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                onderzochte_functies += 1
                if "context" in node.name.lower() and (
                    "build" in node.name.lower() or "convert" in node.name.lower()
                ):
                    context_paths.append(
                        f"{filepath.relative_to(PROJECTWORTEL)}:{node.name}"
                    )

        assert onderzochte_functies > 0, "AST-scan vond geen enkele functie"
        assert context_paths, "geen enkele contextroute gevonden — scope verdacht"

        # THEN: Only ONE path should exist (through DefinitionGeneratorContext)
        valid_paths = [p for p in context_paths if "definition_generator_context" in p]

        # This will FAIL - multiple paths currently exist
        assert len(context_paths) == len(valid_paths), (
            f"Found {len(context_paths)} total paths but only {len(valid_paths)} valid. "
            f"Multiple context routes exist: {context_paths[:5]}"
        )

    @pytest.mark.red_phase
    def test_legacy_context_manager_is_blocked(self):
        """MUST FAIL: Legacy context_manager should be blocked"""
        try:
            # This should not exist or be marked deprecated
            from orchestration.context_manager import LegacyContextManager

            # If it imports, it should raise DeprecationWarning
            with pytest.warns(DeprecationWarning):
                LegacyContextManager()
        except ModuleNotFoundError as exc:
            # Alleen de legacy-module zelf (of haar pakket) telt als "bestaat
            # niet". Een kapotte dependency binnen die module heeft een andere
            # naam en mag deze node niet groen maken.
            assert exc.name in {
                "orchestration",
                "orchestration.context_manager",
            }, (
                f"onverwachte ontbrekende module '{exc.name}' bij het importeren "
                "van orchestration.context_manager"
            )
        else:
            pytest.fail("Legacy context manager still accessible without deprecation")

    @pytest.mark.red_phase
    def test_prompt_context_legacy_path_blocked(self):
        """MUST FAIL: Legacy prompt_context path should be blocked"""
        # Check for legacy prompt building paths
        legacy_methods = []

        # Check if old methods still exist
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()

        # These legacy methods should not exist
        if hasattr(service, "build_prompt_with_context"):
            legacy_methods.append("build_prompt_with_context")
        if hasattr(service, "_parse_context_string"):
            legacy_methods.append("_parse_context_string")
        if hasattr(service, "convert_legacy_context"):
            legacy_methods.append("convert_legacy_context")

        # This will FAIL if legacy methods still exist
        assert len(legacy_methods) == 0, f"Legacy methods still exist: {legacy_methods}"

    @pytest.mark.red_phase
    @pytest.mark.advisory
    def test_no_direct_context_string_processing(self):
        """MUST FAIL: No service should directly process context strings"""
        from services.definition_generator_config import ContextConfig
        from services.definition_generator_context import HybridContextManager
        from services.prompts.prompt_service_v2 import PromptServiceV2

        # Check for string processing methods
        string_processors = []

        # Check PromptServiceV2
        service = PromptServiceV2()
        if hasattr(service, "_parse_context_string"):
            string_processors.append("PromptServiceV2._parse_context_string")

        # Check HybridContextManager — actuele constructor, geen except/pass.
        manager = HybridContextManager(ContextConfig())
        if hasattr(manager, "_parse_context_string"):
            # This one might be OK if it's internal only
            # But should be clearly marked as legacy/deprecated
            import inspect

            source = inspect.getsource(manager._parse_context_string)
            if "@deprecated" not in source and "legacy" not in source.lower():
                string_processors.append("HybridContextManager._parse_context_string")

        # This will FAIL if string processors exist without deprecation
        assert (
            len(string_processors) == 0
        ), f"Direct string processors still active: {string_processors}"

    @pytest.mark.red_phase
    @pytest.mark.advisory
    def test_context_flow_has_single_entry_point(self):
        """MUST FAIL: Context should have single entry point"""
        # GIVEN: All possible entry points for context
        entry_points = []

        from services.definition_generator_config import ContextConfig
        from services.definition_generator_context import (
            EnrichedContext,
            HybridContextManager,
        )

        # Method 1: Direct EnrichedContext creation — een mislukte constructie
        # wordt niet meer ingeslikt; dan is er ook geen entry point om te tellen.
        EnrichedContext(
            base_context={},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        entry_points.append("EnrichedContext.__init__")

        # Method 2: HybridContextManager
        HybridContextManager(ContextConfig())
        entry_points.append("HybridContextManager")

        # Method 3: Through PromptService (should not create context)
        from services.prompts.prompt_service_v2 import PromptServiceV2

        service = PromptServiceV2()
        if hasattr(service, "_convert_request_to_context"):
            entry_points.append("PromptServiceV2._convert_request_to_context")

        # This will FAIL - multiple entry points exist
        assert (
            len(entry_points) == 1
        ), f"Multiple context entry points: {entry_points}. Should only be HybridContextManager"

    @pytest.mark.red_phase
    @pytest.mark.advisory
    def test_no_context_manipulation_in_ui_layer(self):
        """MUST FAIL: UI should not manipulate context data"""
        # GIVEN: UI components
        ui_violations = []

        for filepath in python_bestanden(UI_BRON):
            content = filepath.read_text(encoding="utf-8")
            # UI should only display, not process
            if (
                "_build_context" in content
                or "_parse_context" in content
                or "EnrichedContext(" in content
            ):
                ui_violations.append(str(filepath.relative_to(PROJECTWORTEL)))

        # This will FAIL if UI is doing context processing
        assert (
            len(ui_violations) == 0
        ), f"UI layer manipulating context in: {ui_violations}"

    @pytest.mark.red_phase
    def test_bronscan_faalt_op_lege_en_kapotte_bron(self, tmp_path, monkeypatch):
        """Discriminator op de échte scan, niet op de parser.

        Roept `test_only_one_context_processing_path_exists` zelf aan met een
        tijdelijk verlegde `BRON`. Zou die scan een lees- of parsefout weer
        inslikken, dan komt hier geen `SyntaxError` meer naar buiten en faalt
        deze node. `monkeypatch` zet `BRON` na afloop globaal terug.
        """
        deze_module = sys.modules[__name__]

        ontbrekend = tmp_path / "bestaat-niet"
        monkeypatch.setattr(deze_module, "BRON", ontbrekend)
        with pytest.raises(AssertionError, match="bronmap ontbreekt"):
            self.test_only_one_context_processing_path_exists()

        lege_map = tmp_path / "leeg"
        lege_map.mkdir()
        monkeypatch.setattr(deze_module, "BRON", lege_map)
        with pytest.raises(AssertionError, match="geen Python-bronbestanden"):
            self.test_only_one_context_processing_path_exists()

        kapotte_map = tmp_path / "kapot"
        kapotte_map.mkdir()
        # Bevat 'build' én 'context', zodat de scan dit bestand werkelijk
        # parseert in plaats van het via het voorfilter over te slaan.
        (kapotte_map / "kapot.py").write_text("def build_context(:\n", encoding="utf-8")
        monkeypatch.setattr(deze_module, "BRON", kapotte_map)
        with pytest.raises(SyntaxError):
            self.test_only_one_context_processing_path_exists()
