"""Unit-dekking voor case-normalisatie van de ontologische categorie (DEF-447).

Deterministisch (geen AI-call, geen context-opbouw): `_build_checklist` is een
pure functie die de focus-regel rendert. Borgt dat de productiefix in de
unit-gate valt i.p.v. alleen in de (mogelijk overslaande) integration-suite.
"""

import pytest

from services.prompts.modules.definition_task_module import DefinitionTaskModule

pytestmark = [pytest.mark.unit]


class TestCategoryCaseNormalization:
    """De focus-regel moet case-insensitief zijn voor de ontologische categorie."""

    def test_uppercase_matches_lowercase_output(self):
        module = DefinitionTaskModule()
        lower = module._build_checklist("proces")
        upper = module._build_checklist("PROCES")
        mixed = module._build_checklist("pRoCeS")

        # Alle case-varianten produceren identieke checklist-output.
        assert upper == lower
        assert mixed == lower
        # En de focus-regel verschijnt canoniek lowercase. DEF-750: de
        # opgegeven categorie is een te controleren betekenisclaim, geen
        # exclusieve klasse ("Dit is een ...") en geen woordplicht.
        assert "🎯 Focus: opgegeven categorie **proces** (activiteit als kern)" in lower

    def test_each_known_category_gets_focus_line(self):
        module = DefinitionTaskModule()
        hints = {
            "proces": "activiteit als kern",
            "type": "algemeen begrip; benoem een passend genus",
            "resultaat": "uitkomst als kern",
            "exemplaar": "één bepaald ding of voorval",
        }
        for categorie, hint in hints.items():
            checklist = module._build_checklist(categorie.upper())
            assert (
                f"🎯 Focus: opgegeven categorie **{categorie}** ({hint})" in checklist
            )
            assert "te controleren betekenisclaim" in checklist

    def test_unknown_category_has_no_focus_line(self):
        module = DefinitionTaskModule()
        checklist = module._build_checklist("onbekend")
        assert "🎯 Focus" not in checklist

    def test_none_category_has_no_focus_line(self):
        module = DefinitionTaskModule()
        checklist = module._build_checklist(None)
        assert "🎯 Focus" not in checklist
