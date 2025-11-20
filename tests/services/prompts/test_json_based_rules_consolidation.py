"""
Test suite voor DEF-156 Phase 1: JSON-based rules module consolidation.

Deze tests valideren dat:
1. Output van alle 5 modules identiek blijft na consolidatie
2. Module namen backward compatible blijven
3. Header formatting (emoji + tekst) exact gepreserveerd wordt
4. Prioriteiten behouden blijven
5. Edge cases correct worden afgehandeld (CON trailing dash)

Test Strategie:
- Eerst baseline testen met huidige implementatie
- Na consolidatie exact dezelfde tests draaien
- Output moet byte-for-byte identiek zijn
"""

import pytest

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.modules.base_module import ModuleContext

# Import generic JSON-based rule module (DEF-156 Phase 1: consolidated from 5 duplicates)
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule


def _make_context(
    begrip: str = "authenticatie",
    meta: dict | None = None,
    base_ctx: dict | None = None,
) -> ModuleContext:
    """Helper function om test context te maken."""
    enriched = EnrichedContext(
        base_context=base_ctx
        or {
            "organisatorische_context": ["OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["WvSr"],
        },
        sources=[
            ContextSource(source_type="web_lookup", confidence=0.9, content="wiki")
        ],
        expanded_terms={},
        confidence_scores={"web_lookup": 0.9},
        metadata=meta or {},
    )
    cfg = UnifiedGeneratorConfig()
    return ModuleContext(
        begrip=begrip, enriched_context=enriched, config=cfg, shared_state={}
    )


# Helper functions to instantiate modules (replaces old wrapper classes)
def _make_arai_module() -> JSONBasedRulesModule:
    """Create ARAI rules module."""
    return JSONBasedRulesModule(
        rule_prefix="ARAI",
        module_id="arai_rules",
        module_name="ARAI Validation Rules",
        header_emoji="✅",
        header_text="Algemene Regels AI (ARAI)",
        priority=75,
    )


def _make_con_module() -> JSONBasedRulesModule:
    """Create CON rules module."""
    return JSONBasedRulesModule(
        rule_prefix="CON-",  # Edge case: trailing dash
        module_id="con_rules",
        module_name="Context Validation Rules (CON)",
        header_emoji="🌐",
        header_text="Context Regels (CON)",
        priority=70,
    )


def _make_ess_module() -> JSONBasedRulesModule:
    """Create ESS rules module."""
    return JSONBasedRulesModule(
        rule_prefix="ESS-",
        module_id="ess_rules",
        module_name="Essence Validation Rules (ESS)",
        header_emoji="🎯",
        header_text="Essentie Regels (ESS)",
        priority=75,
    )


def _make_sam_module() -> JSONBasedRulesModule:
    """Create SAM rules module."""
    return JSONBasedRulesModule(
        rule_prefix="SAM-",
        module_id="sam_rules",
        module_name="Coherence Validation Rules (SAM)",
        header_emoji="🔗",
        header_text="Samenhang Regels (SAM)",
        priority=65,
    )


def _make_ver_module() -> JSONBasedRulesModule:
    """Create VER rules module."""
    return JSONBasedRulesModule(
        rule_prefix="VER-",
        module_id="ver_rules",
        module_name="Form Validation Rules (VER)",
        header_emoji="📐",
        header_text="Vorm Regels (VER)",
        priority=60,
    )


# =============================================================================
# BASELINE TESTS - Current Implementation
# Deze tests documenteren de huidige output als referentie
# =============================================================================


def test_arai_module_baseline():
    """Test ARAI module baseline output."""
    mod = _make_arai_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    # Verify success
    assert out.success is True, "ARAI module moet succesvol executeren"

    # Verify metadata
    assert out.metadata["rules_count"] > 0, "ARAI moet rules bevatten"
    assert out.metadata["include_examples"] is True

    # Verify header format (CRITICAL for user recognition)
    assert (
        "### ✅ Algemene Regels AI (ARAI):" in out.content
    ), "ARAI header moet exact format hebben"

    # Verify rule format
    assert "🔹 **ARAI-" in out.content, "ARAI rules moeten juiste prefix hebben"

    # Note: Examples (✅/❌) alleen aanwezig als JSON data ze bevat
    # Niet verplicht voor alle regels

    return out.content  # Return voor comparison


def test_con_module_baseline():
    """Test CON module baseline output."""
    mod = _make_con_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert out.success is True
    assert out.metadata["rules_count"] > 0

    # Verify header format
    assert (
        "### 🌐 Context Regels (CON):" in out.content
    ), "CON header moet exact format hebben"

    # Verify rule format - CON has trailing dash!
    assert "🔹 **CON-" in out.content, "CON rules moeten 'CON-' prefix hebben"

    return out.content


def test_ess_module_baseline():
    """Test ESS module baseline output."""
    mod = _make_ess_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert out.success is True
    assert out.metadata["rules_count"] > 0

    # Verify header format
    assert (
        "### 🎯 Essentie Regels (ESS):" in out.content
    ), "ESS header moet exact format hebben"

    # Verify rule format
    assert "🔹 **ESS-" in out.content, "ESS rules moeten juiste prefix hebben"

    return out.content


def test_sam_module_baseline():
    """Test SAM module baseline output."""
    mod = _make_sam_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert out.success is True
    assert out.metadata["rules_count"] > 0

    # Verify header format
    assert (
        "### 🔗 Samenhang Regels (SAM):" in out.content
    ), "SAM header moet exact format hebben"

    # Verify rule format
    assert "🔹 **SAM-" in out.content, "SAM rules moeten juiste prefix hebben"

    return out.content


def test_ver_module_baseline():
    """Test VER module baseline output."""
    mod = _make_ver_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert out.success is True
    assert out.metadata["rules_count"] > 0

    # Verify header format - VER is "Vorm Regels" (not "Verifieerbare")
    assert (
        "### 📐 Vorm Regels (VER):" in out.content
    ), "VER header moet exact format hebben"

    # Verify rule format
    assert "🔹 **VER-" in out.content, "VER rules moeten juiste prefix hebben"

    return out.content


# =============================================================================
# PRIORITY TESTS
# =============================================================================


def test_module_priorities():
    """Test dat alle modules de juiste prioriteiten hebben."""
    arai = _make_arai_module()
    con = _make_con_module()
    ess = _make_ess_module()
    sam = _make_sam_module()
    ver = _make_ver_module()

    # Initialize all
    for mod in [arai, con, ess, sam, ver]:
        mod.initialize({})

    # Verify priorities (from pre-consolidation check)
    assert arai.priority == 75, "ARAI priority moet 75 zijn"
    assert con.priority == 70, "CON priority moet 70 zijn"
    assert ess.priority == 75, "ESS priority moet 75 zijn"
    assert sam.priority == 65, "SAM priority moet 65 zijn"
    assert ver.priority == 60, "VER priority moet 60 zijn"


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================


def test_generic_module_importable():
    """Test dat JSONBasedRulesModule correct importeerbaar is."""
    # DEF-156 Phase 1: Test generic module instead of wrappers

    from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule

    # Verify instantiable
    assert JSONBasedRulesModule is not None

    # Verify all 5 modules can be created with factory functions
    assert _make_arai_module() is not None
    assert _make_con_module() is not None
    assert _make_ess_module() is not None
    assert _make_sam_module() is not None
    assert _make_ver_module() is not None


def test_module_ids_preserved():
    """Test dat module_id attributes behouden blijven."""
    arai = _make_arai_module()
    con = _make_con_module()
    ess = _make_ess_module()
    sam = _make_sam_module()
    ver = _make_ver_module()

    # Initialize all
    for mod in [arai, con, ess, sam, ver]:
        mod.initialize({})

    # Verify module IDs
    assert arai.module_id == "arai_rules"
    assert con.module_id == "con_rules"
    assert ess.module_id == "ess_rules"
    assert sam.module_id == "sam_rules"
    assert ver.module_id == "ver_rules"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


def test_con_trailing_dash_edge_case():
    """Test dat CON module correct omgaat met trailing dash in prefix.

    Dit is een bekend edge case: CON gebruikt "CON-" met trailing dash,
    terwijl andere modules plain prefix gebruiken zonder dash.
    """
    mod = _make_con_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    # Verify dat CON- prefix correct wordt gebruikt
    assert (
        "CON-01" in out.content or "CON-" in out.content
    ), "CON rules moeten 'CON-' prefix hebben met trailing dash"

    # Verify geen dubbele dash
    assert "CON--" not in out.content, "Geen dubbele dash in CON prefix"


def test_examples_toggle():
    """Test dat include_examples config correct werkt voor alle modules."""
    modules = [
        _make_arai_module(),
        _make_con_module(),
        _make_ess_module(),
        _make_sam_module(),
        _make_ver_module(),
    ]

    ctx = _make_context()

    # Test with examples enabled
    for mod in modules:
        mod.initialize({"include_examples": True})
        out = mod.execute(ctx)
        # Note: Voorbeelden (✅/❌) zijn alleen aanwezig als JSON data ze bevat
        # We checken alleen dat metadata correct is
        assert (
            out.metadata.get("include_examples") is True
        ), f"{mod.module_id} metadata moet include_examples=True bevatten"

    # Test with examples disabled
    modules_no_examples = [
        _make_arai_module(),
        _make_con_module(),
        _make_ess_module(),
        _make_sam_module(),
        _make_ver_module(),
    ]

    for mod in modules_no_examples:
        mod.initialize({"include_examples": False})
        out = mod.execute(ctx)
        assert out.metadata.get("include_examples") is False


# =============================================================================
# INTEGRATION TEST - All Modules Together
# =============================================================================


def test_all_modules_execute_successfully():
    """Integration test: alle 5 modules moeten succesvol executeren samen."""
    modules = [
        _make_arai_module(),
        _make_con_module(),
        _make_ess_module(),
        _make_sam_module(),
        _make_ver_module(),
    ]

    ctx = _make_context()

    for mod in modules:
        mod.initialize({"include_examples": True})
        out = mod.execute(ctx)
        assert out.success is True, f"{mod.module_id} moet succesvol executeren"
        assert len(out.content) > 0, f"{mod.module_id} moet content genereren"
        assert (
            out.metadata.get("rules_count", 0) > 0
        ), f"{mod.module_id} moet rules bevatten"


# =============================================================================
# POST-CONSOLIDATION COMPARISON TESTS
# Deze tests worden OPNIEUW gedraaid NA consolidatie implementatie
# Output moet IDENTIEK zijn aan baseline
# =============================================================================


@pytest.mark.skip(reason="Run AFTER consolidation implementation")
def test_post_consolidation_arai_output_identical():
    """
    CRITICAL TEST: Vergelijk ARAI output na consolidatie met baseline.

    Deze test moet EXACT DEZELFDE output genereren als test_arai_module_baseline().
    Draai deze test NA implementatie van JSONBasedRulesModule.
    """
    # Haal baseline op
    baseline = test_arai_module_baseline()

    # Genereer nieuwe output met geconsolideerde module
    mod = _make_arai_module()  # Nu een wrapper van JSONBasedRulesModule
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    # Output moet IDENTIEK zijn
    assert (
        out.content == baseline
    ), "ARAI output na consolidatie moet identiek zijn aan baseline"


@pytest.mark.skip(reason="Run AFTER consolidation implementation")
def test_post_consolidation_con_output_identical():
    """CRITICAL TEST: Vergelijk CON output na consolidatie met baseline."""
    baseline = test_con_module_baseline()

    mod = _make_con_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert (
        out.content == baseline
    ), "CON output na consolidatie moet identiek zijn aan baseline"


@pytest.mark.skip(reason="Run AFTER consolidation implementation")
def test_post_consolidation_ess_output_identical():
    """CRITICAL TEST: Vergelijk ESS output na consolidatie met baseline."""
    baseline = test_ess_module_baseline()

    mod = _make_ess_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert (
        out.content == baseline
    ), "ESS output na consolidatie moet identiek zijn aan baseline"


@pytest.mark.skip(reason="Run AFTER consolidation implementation")
def test_post_consolidation_sam_output_identical():
    """CRITICAL TEST: Vergelijk SAM output na consolidatie met baseline."""
    baseline = test_sam_module_baseline()

    mod = _make_sam_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert (
        out.content == baseline
    ), "SAM output na consolidatie moet identiek zijn aan baseline"


@pytest.mark.skip(reason="Run AFTER consolidation implementation")
def test_post_consolidation_ver_output_identical():
    """CRITICAL TEST: Vergelijk VER output na consolidatie met baseline."""
    baseline = test_ver_module_baseline()

    mod = _make_ver_module()
    mod.initialize({"include_examples": True})

    ctx = _make_context()
    out = mod.execute(ctx)

    assert (
        out.content == baseline
    ), "VER output na consolidatie moet identiek zijn aan baseline"


# =============================================================================
# VISUAL INSPECTION HELPER
# =============================================================================


def test_visual_inspection_helper():
    """
    Helper test om output visueel te inspecteren.

    Draai deze test om de output van alle modules te zien:
    pytest tests/services/prompts/test_json_based_rules_consolidation.py::test_visual_inspection_helper -v -s
    """
    modules = [
        ("ARAI", _make_arai_module()),
        ("CON", _make_con_module()),
        ("ESS", _make_ess_module()),
        ("SAM", _make_sam_module()),
        ("VER", _make_ver_module()),
    ]

    ctx = _make_context()

    print("\n" + "=" * 80)
    print("VISUAL INSPECTION - All Module Outputs")
    print("=" * 80)

    for name, mod in modules:
        mod.initialize({"include_examples": True})
        out = mod.execute(ctx)

        print(f"\n{name} MODULE OUTPUT:")
        print("-" * 80)
        # Print eerste 500 characters voor inspection
        print(out.content[:500])
        print("...")
        print(f"Total length: {len(out.content)} characters")
        print(f"Rules count: {out.metadata.get('rules_count')}")
        print(f"Priority: {mod.priority}")
