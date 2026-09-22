"""DEF-766 correctieronde 1 — gedragsmatige reproducties van R4 en R5 (bestaande API).

Vóór de correctie: een bewust gewiste ESS-03-verduidelijking viel bij de
replay terug op de verduidelijking uit de oude beoordeling (R5), en de
editorcontext nam de `betekenisverduidelijking` uit de generatieregistratie
niet over (R4). Deze tests asserteren het gecorrigeerde gedrag.
"""

from __future__ import annotations

import pytest

from domain.ess03.contract import Intentie
from services.definition_edit_service import (
    bouw_validatiecontext,
    ess03_intentie_van_definition,
)
from services.interfaces import Definition
from tests.fixtures.def766_fakes import bouw_ess03_beoordeling

pytestmark = [pytest.mark.unit]

TEKST = "Afzonderlijk aaneengesloten landoppervlak dat volledig door water is omgeven."


def _definition(**meta) -> Definition:
    return Definition(
        begrip="eiland",
        definitie=TEKST,
        toelichting="Conventie.",
        categorie="type",
        organisatorische_context=["W"],
        metadata=dict(meta),
    )


def test_r5_gewiste_verduidelijking_valt_niet_terug_op_de_oude_beoordeling():
    oud = bouw_ess03_beoordeling(
        "eiland",
        TEKST,
        {"organisatorische_context": ["W"]},
        None,
        intentie=Intentie(
            toelichting="Conventie.", categorie="type", verduidelijking="Peil P."
        ),
    )
    definition = _definition(ess03_verduidelijking="", ess03_assessment=oud)
    assert ess03_intentie_van_definition(definition).verduidelijking is None


def test_r5_zonder_sleutel_wordt_geen_verduidelijking_uit_de_beoordeling_afgeleid():
    oud = bouw_ess03_beoordeling(
        "eiland",
        TEKST,
        {"organisatorische_context": ["W"]},
        None,
        intentie=Intentie(
            toelichting="Conventie.", categorie="type", verduidelijking="Peil P."
        ),
    )
    definition = _definition(ess03_assessment=oud)
    assert ess03_intentie_van_definition(definition).verduidelijking is None


def test_r4_editorcontext_draagt_de_betekenisverduidelijking_van_het_record():
    ctx = bouw_validatiecontext(
        _definition(),
        {
            "generation_prompt_data": {
                "betekenisverduidelijking": "Bedoeld als handeling."
            }
        },
    )
    assert ctx.get("betekenisverduidelijking") == "Bedoeld als handeling."
