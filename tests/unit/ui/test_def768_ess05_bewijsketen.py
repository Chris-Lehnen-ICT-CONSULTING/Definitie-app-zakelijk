"""DEF-768 / ADR-003: de ESS-05-bewijsketen van wrapper tot weergave.

Echte wrapper (`ValidationOrchestratorV2` + `ModularValidationService`), echte
tijdelijke SQLite met een repository-buur, fake ESS-05-dienst aan de
modelgrens en het echte resultatenblok van de editor (gemockte `st`).

Bewijst op de zichtbare tekst:

* een volledig geverifieerde beoordeling toont haar gecontroleerde reden en
  noemt de verifier (positieve controle: de negatieve asserties hieronder
  discrimineren dus);
* een semantische verificatiefout is een technisch probleem met fase en de
  expliciete melding dat dit geen oordeel over de definitie is;
* een concept zonder, met afgekeurde, of met niet-passende verificatie
  verschijnt nooit als actuele motivering; een `/1`-document is historie.

De fake-dienst bewijst alleen de keten, niet het detectievermogen van een
echte verifier.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.definition_repository import DefinitionRepository
from services.validation.ess05_assessment_service import Ess05Assessment
from tests.fixtures.def768_fakes import FakeEss05Assessor
from tests.unit.ui.test_def768_ess05_editor import (
    _echte_toetsing,
    _ess05_kop,
    _render_blok,
    _tab,
    _voldoet,
    _vul_editor,
    opzet,
    sessie,
)
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

GEVERIFIEERDE_REDEN = "Synthetisch totaaloordeel pass."


@pytest.fixture
def editor(opzet):  # noqa: F811 (geïmporteerde fixture, repo-patroon)
    """De editoropzet (tijdelijke SQLite + repository-buur) uit de editortest."""
    return opzet


class _GemanipuleerdeDienst(FakeEss05Assessor):
    """Levert een `assessed`-document dat daarna buiten de keten is aangepast."""

    def __init__(self, mutatie):
        super().__init__(scenario="pass")
        self.mutatie = mutatie

    async def assess(self, *args: Any, **kwargs: Any) -> Ess05Assessment:
        doc = (await super().assess(*args, **kwargs)).als_dict()
        self.mutatie(doc)
        return Ess05Assessment(doc)


def _teksten_na_toetsing(editor, dienst) -> list[str]:
    repo, did, _ = editor
    geladen = DefinitionRepository(repo.db_path).get(did)
    _vul_editor(did, geladen)
    tab = _tab(repo)
    SessionStateManager.set_value(
        "edit_last_validation", _echte_toetsing(repo, did, dienst)
    )
    return _render_blok(tab)


def _alles(teksten: list[str]) -> str:
    return "\n".join(teksten)


def test_geverifieerde_beoordeling_toont_reden_en_verifier(editor):
    teksten = _teksten_na_toetsing(editor, FakeEss05Assessor(scenario="pass"))
    alles = _alles(teksten)
    assert GEVERIFIEERDE_REDEN in alles
    assert "semantisch geverifieerd door" in alles


def test_semantische_verificatiefout_is_geen_oordeel_over_de_definitie(editor):
    teksten = _teksten_na_toetsing(editor, FakeEss05Assessor(scenario="semantic"))
    kop = _ess05_kop(teksten)
    assert "Technisch probleem" in kop
    assert not _voldoet(kop)
    assert "Voldoet niet" not in kop
    alles = _alles(teksten)
    assert "Dit is geen oordeel over de definitie" in alles
    assert "fase verification" in alles
    assert GEVERIFIEERDE_REDEN not in alles


def _zonder_verificatie(doc: dict) -> None:
    doc["verification"] = None


def _afgekeurde_verificatie(doc: dict) -> None:
    doc["verification"]["checks"][0]["outcome"] = "unsupported"


def _concept_na_verificatie_gewijzigd(doc: dict) -> None:
    # De verificatie hoort bij het oorspronkelijke concept (candidate_hash).
    doc["concept"]["claims"][0]["text"] = GEVERIFIEERDE_REDEN + " Aangevuld."


def _legacy_contract(doc: dict) -> None:
    doc["contract_version"] = "ess05/1"


@pytest.mark.parametrize(
    ("mutatie", "reden"),
    [
        (_zonder_verificatie, "semantische verificatie"),
        (_afgekeurde_verificatie, "semantische verificatie"),
        (_concept_na_verificatie_gewijzigd, "verificatie hoort niet bij"),
        (_legacy_contract, "ess05/1"),
    ],
    ids=["zonder", "afgekeurd", "ander-concept", "legacy-1"],
)
def test_ongeverifieerd_concept_verschijnt_nooit_als_motivering(editor, mutatie, reden):
    teksten = _teksten_na_toetsing(editor, _GemanipuleerdeDienst(mutatie))
    kop = _ess05_kop(teksten)
    assert "Nog te beoordelen" in kop
    alles = _alles(teksten)
    assert GEVERIFIEERDE_REDEN not in alles
    assert "semantisch geverifieerd door" not in alles
    assert reden in alles
