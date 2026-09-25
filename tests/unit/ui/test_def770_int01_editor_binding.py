"""DEF-770 reviewronde 2 — de bewerk-tab toont INT-01 alleen gebonden aan de
actuele formuliertekst.

Echte editorroute met gemockte `st`: `_validate_definition` (echte wrapper en
ModularValidationService via een vervangen servicecontainer) →
`edit_last_validation` → `_render_fullwidth_validation_results`.

* Openen zonder sessieresultaat toont de opgeslagen INT-01-uitkomst als die
  aan de formuliertekst bindt; anders zichtbaar niet toepasbaar.
* Na toetsing van één zin en daarna een tweede zin in het formulier blijft
  'één definitieformulering' (zinsstructuur pass) niet staan.
* ESS-03-herbinding blijft ongemoeid (eigen testbestand DEF-766).
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    herbind_int01_in_validatieresultaat,
    normaliseer_validatieresultaat,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

EEN_ZIN = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
TWEE_ZINNEN = EEN_ZIN + " Heeft vaste vorm."
ZINSSTRUCTUUR_PASS = "Eén definitieformulering"


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "int01-editor.db"))


def _mock_st() -> MagicMock:
    m = MagicMock()
    m.button.side_effect = lambda *a, **kw: False
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _teksten(m: MagicMock) -> list[str]:
    uit: list[str] = []
    for api in ("markdown", "success", "warning", "error", "info", "caption", "text"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return uit


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    tab._ess03_binding = lambda: None  # type: ignore[method-assign]
    return tab


def _open(repo, tekst: str) -> tuple[int, Definition]:
    did = repo.save(
        Definition(
            begrip="transitie-eis",
            definitie=tekst,
            categorie="type",
            organisatorische_context=["Stichting Zilver"],
            juridische_context=[],
            wettelijke_basis=[],
            metadata={"status": "draft", "created_by": "synthetisch"},
        )
    )
    return did, _laad(repo, did)


def _laad(repo, did: int) -> Definition:
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    waarden: dict[str, Any] = {
        "begrip": geladen.begrip,
        "definitie": geladen.definitie,
        "organisatorische_context": list(geladen.organisatorische_context or []),
        "juridische_context": [],
        "wettelijke_basis": [],
        "categorie": "type",
        "toelichting": geladen.toelichting or "",
        "status": "draft",
    }
    for veld, waarde in waarden.items():
        SessionStateManager.set_value(f"edit_{did}_{veld}", waarde)
    return geladen


def _valideer_via_editor(tab) -> None:
    """Zoals de knop 'Valideren': de editorroute met de echte wrapper."""
    container = MagicMock()
    container.orchestrator.return_value.validation_service = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        )
    )
    with (
        patch(
            "ui.cached_services.get_cached_service_container", return_value=container
        ),
        patch("ui.components.definition_edit_tab.st", _mock_st()),
    ):
        resultaat = tab._validate_definition()
    assert isinstance(resultaat, dict)
    SessionStateManager.set_value("edit_last_validation", resultaat)


def _render(tab) -> list[str]:
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_fullwidth_validation_results()
    return _teksten(m)


def _int01_kop(teksten: list[str]) -> str:
    koppen = [t for t in teksten if t.startswith("**INT-01**")]
    assert len(koppen) == 1, teksten
    return koppen[0]


class TestOpenenZonderSessieresultaat:
    def test_opgeslagen_uitkomst_wordt_getoond_als_zij_bindt(self, repo, sessie):
        did, _ = _open(repo, EEN_ZIN)
        tab = _tab(repo)
        teksten = _render(tab)
        assert "Nog te beoordelen" in _int01_kop(teksten)
        assert any(ZINSSTRUCTUUR_PASS in t for t in teksten)
        assert any("Compactheid is nog niet" in t for t in teksten)
        assert any("Begrijpelijkheid is nog niet" in t for t in teksten)

    def test_gewijzigde_formuliertekst_maakt_de_opgeslagen_uitkomst_oud(
        self, repo, sessie
    ):
        did, _ = _open(repo, EEN_ZIN)
        tab = _tab(repo)
        SessionStateManager.set_value(f"edit_{did}_definitie", TWEE_ZINNEN)
        teksten = _render(tab)
        assert "Nog te beoordelen" in _int01_kop(teksten)
        assert not any(ZINSSTRUCTUUR_PASS in t for t in teksten)
        assert any("gewijzigd" in t and "INT-01" in t for t in teksten)

    def test_opgeslagen_uitkomst_van_een_andere_tekst_is_niet_toepasbaar(
        self, repo, sessie
    ):
        did, _ = _open(repo, EEN_ZIN)
        with sqlite3.connect(repo.db_path) as conn:
            conn.execute(
                "UPDATE definities SET definitie = ? WHERE id = ?", (TWEE_ZINNEN, did)
            )
        _laad(repo, did)
        teksten = _render(_tab(repo))
        assert not any(ZINSSTRUCTUUR_PASS in t for t in teksten)
        assert any("gewijzigd" in t and "INT-01" in t for t in teksten)

    def test_zonder_opgeslagen_uitkomst_zichtbaar_niet_beoordeeld(self, repo, sessie):
        did, _ = _open(repo, EEN_ZIN)
        with sqlite3.connect(repo.db_path) as conn:
            conn.execute(
                "UPDATE definities SET generation_prompt_data = NULL WHERE id = ?",
                (did,),
            )
        _laad(repo, did)
        teksten = _render(_tab(repo))
        assert not any(ZINSSTRUCTUUR_PASS in t for t in teksten)
        assert any("INT-01" in t and "niet beoordeeld" in t for t in teksten)


class TestSessieresultaatNaTekstwijziging:
    def test_tweede_zin_na_eerste_validatie_toont_geen_oude_pass(self, repo, sessie):
        did, _ = _open(repo, EEN_ZIN)
        tab = _tab(repo)
        _valideer_via_editor(tab)
        basis = _render(tab)
        assert any(ZINSSTRUCTUUR_PASS in t for t in basis)

        SessionStateManager.set_value(f"edit_{did}_definitie", TWEE_ZINNEN)
        gewijzigd = _render(tab)
        assert "Nog te beoordelen" in _int01_kop(gewijzigd)
        assert not any(ZINSSTRUCTUUR_PASS in t for t in gewijzigd)
        assert any("gewijzigd" in t and "INT-01" in t for t in gewijzigd)
        uitkomst = tab._actueel_sessieresultaat()["raw_v2"]
        assert uitkomst["rule_statuses"]["INT-01"] == "review_required"
        assert "INT-01" not in uitkomst["passed_rules"]

        # Teruggezette tekst: de toetsing geldt weer.
        SessionStateManager.set_value(f"edit_{did}_definitie", EEN_ZIN)
        assert any(ZINSSTRUCTUUR_PASS in t for t in _render(tab))

        # Opnieuw toetsen op de tweede zin: fout met passage.
        SessionStateManager.set_value(f"edit_{did}_definitie", TWEE_ZINNEN)
        _valideer_via_editor(tab)
        opnieuw = _render(tab)
        assert "maken. Heeft" in " ".join(opnieuw)
        assert not any(ZINSSTRUCTUUR_PASS in t for t in opnieuw)


def _vers_resultaat(tekst: str) -> dict[str, Any]:
    """Een vers genormaliseerd resultaat zoals de dienst het levert voor `tekst`."""
    ruw = asyncio.run(
        ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            )
        ).validate_text(begrip="transitie-eis", text=tekst)
    )
    return normaliseer_validatieresultaat(ruw)


def _is_verse_fail(tab) -> bool:
    v2 = tab._actueel_sessieresultaat()["raw_v2"]
    return v2["rule_statuses"]["INT-01"] == "fail" and any(
        (v.get("code") or v.get("rule_id")) == "INT-01" for v in v2["violations"]
    )


def _meldt_tekstwijziging(teksten: list[str]) -> bool:
    return any("gewijzigd" in t and "INT-01" in t for t in teksten)


def _zet_formuliertekst(did: int, tekst: str) -> None:
    SessionStateManager.set_value("edit_" + str(did) + "_definitie", tekst)


class TestAndereProducenten:
    """Reviewronde 3: ook voorsteltoepassing en opslaan leveren een vers
    resultaat dat aan exact de getoetste tekst en dit record gebonden is."""

    def test_voorsteltoepassing_bindt_aan_de_getoetste_kandidaattekst(
        self, repo, sessie
    ):
        did, _ = _open(repo, EEN_ZIN)
        tab = _tab(repo)
        toepassing = {
            "status": "applied",
            "candidate_text": TWEE_ZINNEN,
            "validation": _vers_resultaat(TWEE_ZINNEN)["raw_v2"],
        }

        async def _pas_toe(*_a, **_k):
            return toepassing

        with (
            patch.object(tab, "_onopgeslagen_bewerking", return_value=False),
            patch.object(tab, "_getoonde_versie", return_value=1),
            patch.object(tab, "_refresh_current_definition"),
            patch.object(tab.edit_service, "pas_voorstel_toe", _pas_toe),
            patch("ui.helpers.async_bridge.run_async", asyncio.run),
            patch("ui.components.definition_edit_tab.st", _mock_st()),
        ):
            tab._pas_voorstel_toe(did, "p1", "tester")
        opgeslagen = SessionStateManager.get_value("edit_last_validation")
        assert opgeslagen["editing_definition_id"] == did
        # Volgende run: de toegepaste tekst staat in het formulier.
        _zet_formuliertekst(did, TWEE_ZINNEN)
        assert _is_verse_fail(tab)
        teksten = _render(tab)
        assert not _meldt_tekstwijziging(teksten)
        assert "maken. Heeft" in " ".join(teksten)
        # Een echte tekstwijziging daarna maakt het resultaat wel oud.
        _zet_formuliertekst(did, EEN_ZIN)
        assert _meldt_tekstwijziging(_render(tab))

    def test_opslaan_bindt_aan_de_opgeslagen_tekst_en_het_record(self, repo, sessie):
        did, _ = _open(repo, EEN_ZIN)
        _zet_formuliertekst(did, TWEE_ZINNEN)
        tab = _tab(repo)
        opslag = {"success": True, "validation": _vers_resultaat(TWEE_ZINNEN)}
        with (
            patch.object(tab.edit_service, "save_definition", return_value=opslag),
            patch.object(tab, "_refresh_current_definition"),
            patch("ui.components.definition_edit_tab.st", _mock_st()),
        ):
            tab._save_definition()
        opgeslagen = SessionStateManager.get_value("edit_last_validation")
        assert opgeslagen["editing_definition_id"] == did
        assert _is_verse_fail(tab)
        assert not _meldt_tekstwijziging(_render(tab))
        _zet_formuliertekst(did, TWEE_ZINNEN + " Extra.")
        assert _meldt_tekstwijziging(_render(tab))


class TestDekkingNaHerbinding:
    """Reviewronde 3: na fail -> review_required blijven de afgeleide
    dekkingsvelden consistent met de tellers."""

    def test_fail_naar_open_herberekent_evaluated_en_ratio(self):
        resultaat = _vers_resultaat(TWEE_ZINNEN)["raw_v2"]
        voor = dict(resultaat["evaluation_coverage"])
        herbonden = herbind_int01_in_validatieresultaat(resultaat, EEN_ZIN)
        dekking = herbonden["evaluation_coverage"]
        assert dekking["failed"] == voor["failed"] - 1
        assert dekking["review_required"] == voor["review_required"] + 1
        assert dekking["evaluated"] == dekking["passed"] + dekking["failed"]
        assert dekking["evaluated"] == voor["evaluated"] - 1
        assert dekking["total"] == voor["total"]
        assert dekking["coverage_ratio"] == round(
            dekking["evaluated"] / dekking["total"], 4
        )
        # Het oorspronkelijke resultaat blijft onveranderd.
        assert resultaat["evaluation_coverage"] == voor
