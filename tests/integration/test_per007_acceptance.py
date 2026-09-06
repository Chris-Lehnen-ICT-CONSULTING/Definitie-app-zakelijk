"""
PER-007 Acceptance Tests: Full End-to-End Validation
These tests validate that all architecture decisions are properly implemented.

DEF-519 — de zeven node-intenties zijn behouden; alleen fixtures en contract zijn
bijgewerkt:

* ``HybridContextManager`` vereist een ``ContextConfig`` (vijf nodes faalden op
  ``TypeError: missing 1 required positional argument: 'config'``);
* ``PromptServiceV2._convert_request_to_context`` bestaat niet meer. De actuele
  route is ``build_generation_prompt`` → ``context_manager.build_enriched_context``
  → ``prompt_generator.build_prompt``. De doorgifte wordt gemeten door de
  concrete ``EnrichedContext`` bij die downstreamgrens waar te nemen, met de
  échte contextmanager erboven;
* alle ``except (AssertionError, KeyError): pass``, ``if key in ...``,
  ``if os.path.exists(...)`` en ``except ImportError: pass`` zijn weg: ontbrekend
  bewijs is nu een zichtbare failure met exact pad.

Rode nodes zijn niet-gekozen architectuur, niet stuk gereedschap. Dispositie:
  owner (testdispositie): DEF-519
  owner (inhoudelijk beleid): nog niet vastgesteld
  trigger: vrijgegeven inhoudelijk herstel van de betreffende functionaliteit
  herbeoordeling: 2026-10-06
Rode claims: Anders-filtering (AC3/AC5), ASTRA-waarschuwingen (AC4), ontbrekende
ContextFormatter/UI-laag (AC1/AC7) en het UI-stringbeleid (AC6). Er wordt niets
van die architectuur binnen DEF-519 gebouwd en niets gereconstrueerd.
"""

import ast
import logging
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from services.definition_generator_config import ContextConfig
from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.acceptance]

# `advisory`-dispositie (DEF-519) op zes van de zeven nodes; `test_ac2` slaagt op
# de huidige bron en blijft verplicht. De acceptatie-intenties zijn individueel
# gedisponeerd, niet stil vervangen of weggefilterd; geen skip of xfail.
# Owner: testdispositie-519, inhoudelijke owner niet vastgesteld.
# Trigger: vrijgegeven PER007-herstel.
# Herbeoordeling: 2026-10-06.
# Uitzondering: `test_ac4_astra_warnings_not_errors` is een ASTRA-intentie met
# eigen owner DEF-468 en eigen trigger (DEF-468 implementeert ASTRA).

PROJECTWORTEL = Path(__file__).resolve().parents[2]


def bronwortel() -> Path:
    """De te scannen bronmap, afgeleid van ``__file__`` (niet van de CWD)."""
    return PROJECTWORTEL / "src"


def _maak_manager() -> HybridContextManager:
    """Echte contextmanager met de actuele, verplichte configuratie."""
    return HybridContextManager(ContextConfig())


@contextmanager
def waargenomen_promptgrens(prompt_service: PromptServiceV2):
    """Leg vast wat de promptgenerator werkelijk van de service krijgt.

    Alleen deze ene downstreamgrens is bevroren; de context erboven wordt door
    de échte HybridContextManager gebouwd, dus de assertie toetst product-
    gedrag en niet haar eigen dubbel.
    """
    waarnemingen: list[dict] = []

    def _vastleggen(*, begrip, context):
        waarnemingen.append({"begrip": begrip, "context": context})
        return "BEVROREN PROMPTTEKST"

    with patch.object(
        prompt_service.prompt_generator, "build_prompt", side_effect=_vastleggen
    ):
        yield waarnemingen


class TestAcceptanceCriteria:
    """Full acceptance tests - validate architecture decisions"""

    @pytest.mark.acceptance
    @pytest.mark.advisory
    @pytest.mark.asyncio
    async def test_ac1_ui_preview_never_used_as_source(self):
        """AC1: UI preview is display only, never data source"""
        request = GenerationRequest(
            id="test-id",
            begrip="verdachte",
            organisatorische_context=["OM", "DJI"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Art. 27 Sv"],
        )

        # Stap 1: echte contextopbouw.
        base_context = _maak_manager()._build_base_context(request)
        assert isinstance(base_context, dict)
        assert base_context["organisatorisch"] == ["OM", "DJI"]
        assert base_context["juridisch"] == ["Strafrecht"]
        assert base_context["wettelijk"] == ["Art. 27 Sv"]

        # Stap 2: de prompt krijgt gestructureerde data, geen UI-string.
        prompt_service = PromptServiceV2()
        with waargenomen_promptgrens(prompt_service) as waarnemingen:
            await prompt_service.build_generation_prompt(request)

        assert len(waarnemingen) == 1, "promptgenerator niet aangeroepen"
        doorgegeven = waarnemingen[0]["context"]
        assert isinstance(doorgegeven, EnrichedContext)
        assert isinstance(doorgegeven.base_context, dict)
        assert doorgegeven.base_context["organisatorisch"] == ["OM", "DJI"]

        context_str = str(doorgegeven.base_context)
        assert "📋" not in context_str, "UI emoji found in prompt context"
        assert " | " not in context_str, "UI separator found in prompt context"

        # Stap 3: de formatter die dit AC veronderstelt bestaat niet (rood).
        # De prerequisite staat vóór de oorspronkelijke asserties; die blijven
        # eronder staan, zodat een leeg of half bestand de intentie niet laat
        # verdwijnen. Geen brede ImportError-catch: een onbruikbare module faalt.
        formatter_pad = PROJECTWORTEL / "src" / "services" / "ui" / "formatters.py"
        assert (
            formatter_pad.is_file()
        ), f"ContextFormatter ontbreekt: {formatter_pad} (AC1, dispositie DEF-519)"

        from services.ui.formatters import ContextFormatter

        formatter = ContextFormatter()
        ui_preview = formatter.format_preview(doorgegeven)

        # Display-formatting hoort in de UI-string te zitten.
        assert "📋" in ui_preview or "Org:" in ui_preview

        # En de UI-string mag niet terug te lezen zijn als data.
        with pytest.raises((TypeError, AttributeError, ValueError)):
            formatter.parse_ui_string(ui_preview)

    @pytest.mark.acceptance
    def test_ac2_single_context_path(self):
        """AC2: Only ONE path for context processing exists.

        Reikwijdte, eerlijk: dit is de bestaande synchrone AST-naamheuristiek.
        Zij toont aan dát het verwachte pad
        (`definition_generator_context.py:_build_base_context`) als eerste
        treffer bestaat en dát er geen functienamen met legacy-patronen
        (v1/legacy/old/deprecated) zijn. Zij bewijst NIET dat er precies één
        werkelijk contextpad is: async functies, methodenamen zonder
        'build'+'context' en aanroeprelaties vallen buiten deze scan. Een
        volledige architectuurinventarisatie hoort niet in DEF-519.
        """
        src_path = bronwortel()
        assert src_path.is_dir(), f"bronmap ontbreekt: {src_path}"

        bestanden = sorted(src_path.rglob("*.py"))
        assert bestanden, f"geen Python-bronbestanden gevonden in {src_path}"

        context_processing_functions = []
        onderzochte_functies = 0
        for filepath in bestanden:
            inhoud = filepath.read_text(encoding="utf-8")
            # Parsefouten zichtbaar: geen except/continue meer.
            tree = ast.parse(inhoud, filename=str(filepath))

            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                onderzochte_functies += 1
                if (
                    "build" in node.name.lower() and "context" in node.name.lower()
                ) or node.name == "_build_base_context":
                    rel_path = filepath.relative_to(src_path)
                    context_processing_functions.append(f"{rel_path}:{node.name}")

        assert onderzochte_functies > 0, "AST-scan vond geen enkele functie"
        assert context_processing_functions, "geen contextopbouw-functies gevonden"

        valid_path = [
            p
            for p in context_processing_functions
            if "definition_generator_context" in p
        ]
        assert valid_path, "definition_generator_context levert geen contextopbouw"
        assert (
            "definition_generator_context.py:_build_base_context" in valid_path[0]
        ), f"Wrong context processing path: {valid_path[0]}"

        legacy_indicators = ["v1", "legacy", "old", "deprecated"]
        legacy_paths = [
            p
            for p in context_processing_functions
            if any(indicator in p.lower() for indicator in legacy_indicators)
        ]
        assert (
            len(legacy_paths) == 0
        ), f"Legacy context paths still exist: {legacy_paths}"

    @pytest.mark.acceptance
    @pytest.mark.advisory
    def test_ac3_anders_works_all_lists(self):
        """AC3: Anders... option works in all three context lists"""
        test_cases = [
            (
                "organisatorische_context",
                ["OM", "Anders...", "CustomOrg"],
                "organisatorisch",
            ),
            (
                "juridische_context",
                ["Strafrecht", "Anders...", "CustomDomain"],
                "juridisch",
            ),
            ("wettelijke_basis", ["Art. 27 Sv", "Anders...", "CustomLaw"], "wettelijk"),
        ]

        # Alle drie de lijsten worden werkelijk uitgevoerd; de bevindingen gaan
        # naar één assertie aan het eind. Geen swallowed assertion: dit zijn
        # verzamelde feiten, geen gevangen fouten.
        ontbrekende_sleutels: list[str] = []
        ontbrekende_customs: list[str] = []
        anders_blijft_staan: list[str] = []

        for field_name, field_value, context_key in test_cases:
            request = GenerationRequest(id="test-id", begrip="test")
            setattr(request, field_name, field_value)

            context = _maak_manager()._build_base_context(request)

            if context_key not in context:
                ontbrekende_sleutels.append(context_key)
                continue

            custom_value = field_value[2]
            if custom_value not in context[context_key]:
                ontbrekende_customs.append(f"{context_key}:{custom_value}")
            if "Anders..." in context[context_key]:
                anders_blijft_staan.append(context_key)

        assert (
            not ontbrekende_sleutels
        ), f"contextsleutels ontbreken: {ontbrekende_sleutels}"
        assert (
            not ontbrekende_customs
        ), f"Custom values not in context: {ontbrekende_customs}"
        # Rood zolang de Anders-filtering niet geleverd is (dispositie DEF-519).
        assert (
            not anders_blijft_staan
        ), f"Anders... marker still in: {anders_blijft_staan}"

    @pytest.mark.acceptance
    @pytest.mark.advisory  # eigen owner DEF-468: ASTRA-intentie niet geleverd
    def test_ac4_astra_warnings_not_errors(self):
        """AC4: ASTRA validation gives warnings, never blocks"""
        request = GenerationRequest(
            id="test-id",
            begrip="test",
            organisatorische_context=["OM", "InvalidOrg", "DJI", "FakeOrg"],
        )

        log_records: list[logging.LogRecord] = []
        handler = logging.Handler()
        handler.emit = lambda record: log_records.append(record)

        logger = logging.getLogger("services.definition_generator_context")
        vorig_niveau = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        try:
            context = _maak_manager()._build_base_context(request)

            # Niet geblokkeerd: alle organisaties blijven in de context.
            assert "organisatorisch" in context
            for org in ["OM", "InvalidOrg", "DJI", "FakeOrg"]:
                assert (
                    org in context["organisatorisch"]
                ), f"{org} was blocked instead of warned"

            # Rood zolang ASTRA-waarschuwingen niet geleverd zijn (DEF-519).
            waarschuwingen = [
                r.getMessage() for r in log_records if r.levelname == "WARNING"
            ]
            assert waarschuwingen, "geen ASTRA-waarschuwing voor onbekende organisaties"
        finally:
            logger.removeHandler(handler)
            logger.setLevel(vorig_niveau)

    @pytest.mark.acceptance
    @pytest.mark.advisory
    @pytest.mark.asyncio
    async def test_ac5_complete_context_flow_integration(self):
        """AC5: Complete integration test of context flow"""
        request = GenerationRequest(
            id="test-id",
            begrip="verdachte",
            organisatorische_context=["OM", "Anders...", "NieuweOrganisatie", "DJI"],
            juridische_context=["Strafrecht", "Anders...", "NieuwRechtsgebied"],
            wettelijke_basis=[
                "Art. 27 Sv",
                "Anders...",
                "Nieuwe Wet 2025",
                "Art. 67 Sv",
            ],
            context="This is legacy context that should be ignored",
            organisatie="LegacyOrg",
        )

        base_context = _maak_manager()._build_base_context(request)

        # Legacy: de losse context-string wordt genegeerd zodra de lijsten er zijn.
        assert "This is legacy context that should be ignored" not in str(base_context)
        # Legacy enkelvoudig veld wordt wél toegevoegd.
        assert "LegacyOrg" in base_context["organisatorisch"]

        # Volgorde behouden binnen de wettelijke lijst.
        wettelijk = base_context["wettelijk"]
        assert wettelijk.index("Art. 27 Sv") < wettelijk.index("Art. 67 Sv")

        # Doorgifte naar de prompt via de echte route.
        prompt_service = PromptServiceV2()
        with waargenomen_promptgrens(prompt_service) as waarnemingen:
            await prompt_service.build_generation_prompt(request)

        doorgegeven = waarnemingen[0]["context"]
        assert isinstance(doorgegeven, EnrichedContext)
        assert isinstance(doorgegeven.base_context, dict)
        alle_tekst = str(base_context) + str(doorgegeven.base_context)
        assert "📋" not in alle_tekst, "UI emoji found in data layer"
        assert "⚖️" not in alle_tekst, "UI emoji found in data layer"

        # Rood zolang de Anders-filtering niet geleverd is (dispositie DEF-519).
        assert "NieuweOrganisatie" in base_context["organisatorisch"]
        assert "Anders..." not in base_context["organisatorisch"]

    @pytest.mark.acceptance
    @pytest.mark.advisory
    def test_ac6_no_ui_string_reverse_engineering(self):
        """AC6: System cannot reverse-engineer data from UI strings"""
        ui_preview = "📋 Org: OM, DJI, Rechtspraak | ⚖️ Juridisch: Strafrecht | 📜 Wet: Art. 27 Sv"

        manager = _maak_manager()
        reverse_methods = [
            "parse_ui_preview",
            "extract_from_ui",
            "context_from_display",
            "reverse_format",
        ]

        for method in reverse_methods:
            assert not hasattr(
                manager, method
            ), f"Reverse engineering method '{method}' exists in HybridContextManager"

        prompt_service = PromptServiceV2()
        for method in reverse_methods:
            assert not hasattr(
                prompt_service, method
            ), f"Reverse engineering method '{method}' exists in PromptServiceV2"

        request = GenerationRequest(id="test-id", begrip="test", context=ui_preview)
        context = manager._build_base_context(request)

        all_values: list[str] = []
        for value_list in context.values():
            if isinstance(value_list, list):
                all_values.extend(value_list)

        # Rood zolang de UI-string niet geweerd wordt (dispositie DEF-519).
        all_text = " ".join(str(v) for v in all_values)
        assert "📋" not in all_text, "UI emoji leaked into context"
        assert "⚖️" not in all_text, "UI emoji leaked into context"
        assert "📜" not in all_text, "UI emoji leaked into context"

    @pytest.mark.acceptance
    @pytest.mark.advisory
    def test_ac7_separation_of_concerns_validated(self):
        """AC7: Clear separation between presentation and data layers"""
        ui_emojis = ["📋", "⚖️", "📜"]

        data_files = [
            "services/definition_generator_context.py",
            "services/prompts/prompt_service_v2.py",
            "services/interfaces.py",
        ]
        for relatief in data_files:
            volledig = bronwortel() / relatief
            assert volledig.is_file(), f"verplichte bron ontbreekt: {volledig}"
            inhoud = volledig.read_text(encoding="utf-8")
            for indicator in ui_emojis:
                assert (
                    indicator not in inhoud
                ), f"UI indicator '{indicator}' found in data layer file {relatief}"

        # De UI-laag uit dit AC bestaat niet; rood met exact pad (DEF-519).
        ui_files = ["ui/formatters.py", "ui/components/context_display.py"]
        ontbrekend = [
            str(bronwortel() / relatief)
            for relatief in ui_files
            if not (bronwortel() / relatief).is_file()
        ]
        assert not ontbrekend, f"UI-laagbestanden ontbreken: {ontbrekend}"

        data_indicators = ["_build_base_context", "EnrichedContext(", "_parse_context"]
        for relatief in ui_files:
            inhoud = (bronwortel() / relatief).read_text(encoding="utf-8")
            for indicator in data_indicators:
                assert (
                    indicator not in inhoud
                ), f"Data processing '{indicator}' found in UI file {relatief}"

        # Formatter is output-only. Blijft onder de prerequisite staan zodat de
        # intentie niet verdwijnt zodra het bestand er (leeg) is.
        from services.ui.formatters import ContextFormatter

        formatter = ContextFormatter()
        assert hasattr(formatter, "format_ui_preview") or hasattr(
            formatter, "format_preview"
        ), "Formatter missing format methods"
        assert not hasattr(
            formatter, "parse_ui_string"
        ), "Formatter should not parse UI strings"
        assert not hasattr(
            formatter, "extract_from_preview"
        ), "Formatter should not extract from preview"
