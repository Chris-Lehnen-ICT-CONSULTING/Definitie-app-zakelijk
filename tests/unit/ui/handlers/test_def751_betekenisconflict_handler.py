"""DEF-751 stap 2 — adapter en generatiehandler bij een gemeld betekenisconflict.

* De adapter maakt van de specifieke orchestrator-non-success een UI-dict
  zonder definitie, zonder opslag-id en zonder oordeel, met de conflict-
  gegevens onder één additieve sleutel.
* De handler meldt bij een conflict géén succes, opent geen editrecord, legt
  geen categoriekeuze vast en zet het open conflict — gebonden aan de
  volledige invoer (begrip, context, categorie, documentselectie, RAG-
  selectie) — in de sessie.
* Een verzonden verduidelijking wordt alleen toegepast als zij bij ditzelfde
  conflict én bij de actuele invoer hoort; anders vervalt zij met een melding.
  Toepassen is eenmalig. De verduidelijking reist via het typed veld, niet
  via vrije options.
* Ook een gewone mislukte generatie krijgt geen succesmelding meer.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from integration.definitie_checker import CheckAction
from services.interfaces import DefinitionResponseV2
from services.service_factory import ServiceAdapter
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler
from ui.helpers.betekenisconflict import (
    KEY_OPEN,
    KEY_VERZONDEN,
    invoer_vingerafdruk,
)

pytestmark = [pytest.mark.unit]

CONTEXT = {
    "organisatorische_context": ["DJI"],
    "juridische_context": ["Strafrecht"],
    "wettelijke_basis": [],
}
VRAAG = "Is de handeling of het vastgelegde gegeven bedoeld?"
LEZINGEN = [
    {"lezing": "de handeling", "bron": "bron 1", "grond": "bron 1 zegt activiteit"},
    {
        "lezing": "het gegeven",
        "bron": "context: DJI",
        "grond": "DJI gebruikt resultaat",
    },
]
CONFLICT_MD = {
    "generation_id": "gen-conflict-1",
    "error_type": "betekenisconflict",
    "phases_completed": 4,
    "betekenisconflict": {
        "vraag": VRAAG,
        "lezingen": LEZINGEN,
        "gemeld_door": "model",
        "begrip": "registratie",
        "ontologische_categorie": "proces",
        "organisatorische_context": ["DJI"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": [],
        "generation_id": "gen-conflict-1",
    },
}


class FakeSM:
    """Stateful SessionStateManager-double (get/set/clear op één dict)."""

    def __init__(self, **waarden: Any) -> None:
        self.data: dict[str, Any] = {"generation_options": {}, **waarden}

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self.data[key] = value

    def clear_value(self, key: str) -> None:
        self.data.pop(key, None)


class FakeService:
    """Definitieservice-double; `antwoorden` is een lijst UI-dicts op volgorde."""

    def __init__(self, *antwoorden: dict[str, Any]) -> None:
        self.antwoorden = list(antwoorden)
        self.aanroepen: list[dict[str, Any]] = []

    async def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        self.aanroepen.append(
            {"begrip": begrip, "context_dict": context_dict, **kwargs}
        )
        return self.antwoorden.pop(0)

    def to_ui_response(self, response):
        return response


def conflict_ui() -> dict[str, Any]:
    return ServiceAdapter.to_ui_response(
        ServiceAdapter.__new__(ServiceAdapter),
        DefinitionResponseV2(success=False, error=VRAAG, metadata=dict(CONFLICT_MD)),
    )


def succes_ui(did: int = 7) -> dict[str, Any]:
    return {
        "success": True,
        "saved_definition_id": did,
        "definitie_gecorrigeerd": "Een x is …",
    }


def _handler(service: FakeService) -> tuple[DefinitionGenerationHandler, MagicMock]:
    checker = MagicMock()
    checker.check_before_generation.return_value = MagicMock(action=CheckAction.PROCEED)
    repo = MagicMock()
    repo.get_definitie.return_value = MagicMock(id=7, version_number=1)
    return DefinitionGenerationHandler(checker, service, repo), repo


def _run(handler, sm, st, begrip="registratie", context=CONTEXT) -> None:
    with patch(
        "ui.helpers.async_bridge.run_async", lambda coro, **kw: asyncio.run(coro)
    ):
        handler.handle_definition_generation(begrip, context, _st=st, _sm=sm)


def _vingerafdruk(**extra) -> str:
    basis = {
        "begrip": "registratie",
        "organisatorische_context": ["DJI"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": [],
        "categorie": "proces",
        "document_ids": [],
        "rag_collection_ids": None,
    }
    return invoer_vingerafdruk(**{**basis, **extra})


# ------------------------------------------------------------------ adapter


def test_adapter_maakt_specifieke_non_success_zonder_definitie_of_oordeel():
    ui = conflict_ui()
    assert ui["success"] is False
    assert ui["betekenisconflict"]["vraag"] == VRAAG
    assert ui["betekenisconflict"]["lezingen"] == LEZINGEN
    assert ui["betekenisconflict"]["gemeld_door"] == "model"
    assert ui["error_message"] == VRAAG
    assert ui["definitie_origineel"] == "" and ui["definitie_gecorrigeerd"] == ""
    assert "saved_definition_id" not in ui
    assert ui["final_score"] == 0.0
    assert ui["validation_details"]["violations"] == []
    assert ui["voorbeelden"] == {}


def test_adapter_gewone_fout_draagt_geen_conflictsleutel():
    ui = ServiceAdapter.to_ui_response(
        ServiceAdapter.__new__(ServiceAdapter),
        DefinitionResponseV2(
            success=False,
            error="ongeldig",
            metadata={"error_type": "modelantwoord_ongeldig", "reden": "x"},
        ),
    )
    assert ui["success"] is False and "betekenisconflict" not in ui
    assert ui["error_message"] == "ongeldig"


# ------------------------------------------------------------------ handler


def test_conflict_geen_succes_geen_editrecord_geen_keuze_wel_open_conflict():
    service = FakeService(conflict_ui())
    handler, repo = _handler(service)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    st = MagicMock()
    _run(handler, sm, st)

    assert not st.success.called
    assert st.warning.called
    melding = " ".join(str(a) for c in st.warning.call_args_list for a in c.args)
    assert "erduidelijking" in melding and "geen definitie" in melding
    assert "editing_definition_id" not in sm.data
    assert not repo.record_category_choice.called
    resultaat = sm.data["last_generation_result"]
    assert resultaat["saved_definition_id"] is None
    assert resultaat["saved_record"] is None
    assert resultaat["agent_result"]["betekenisconflict"]["vraag"] == VRAAG
    open_conflict = sm.data[KEY_OPEN]
    assert open_conflict["generation_id"] == "gen-conflict-1"
    assert open_conflict["vraag"] == VRAAG
    assert open_conflict["lezingen"] == LEZINGEN
    assert open_conflict["vingerafdruk"] == _vingerafdruk()
    assert open_conflict["begrip"] == "registratie"
    assert KEY_VERZONDEN not in sm.data


def test_conflict_laat_bestaand_editrecord_ongemoeid():
    service = FakeService(conflict_ui())
    handler, _ = _handler(service)
    sm = FakeSM(determined_category="proces", editing_definition_id=99)
    _run(handler, sm, MagicMock())
    assert sm.data["editing_definition_id"] == 99


def test_gewone_mislukking_meldt_geen_succes_en_sluit_open_conflict():
    service = FakeService(
        {"success": False, "error_message": "Generation failed: boem"}
    )
    handler, _ = _handler(service)
    sm = FakeSM(determined_category="proces")
    sm.data[KEY_OPEN] = {"generation_id": "oud"}
    st = MagicMock()
    _run(handler, sm, st)
    assert not st.success.called
    assert st.error.called
    assert "boem" in str(st.error.call_args)
    assert KEY_OPEN not in sm.data


def test_succes_sluit_open_conflict_en_meldt_succes():
    service = FakeService(succes_ui())
    handler, _ = _handler(service)
    sm = FakeSM(determined_category="proces")
    sm.data[KEY_OPEN] = {"generation_id": "oud"}
    st = MagicMock()
    _run(handler, sm, st)
    assert st.success.called
    assert KEY_OPEN not in sm.data
    assert sm.data["editing_definition_id"] == 7


# ---------------------------------------------------------------- binding


def _met_verzonden(
    sm: FakeSM,
    *,
    vingerafdruk: str,
    generation_id: str = "gen-conflict-1",
    tekst="Bedoeld is de handeling",
):
    sm.data[KEY_OPEN] = {
        "generation_id": "gen-conflict-1",
        "vingerafdruk": _vingerafdruk(),
        "vraag": VRAAG,
        "lezingen": LEZINGEN,
        "begrip": "registratie",
    }
    sm.data[KEY_VERZONDEN] = {
        "generation_id": generation_id,
        "vingerafdruk": vingerafdruk,
        "tekst": tekst,
    }


def test_verzonden_verduidelijking_wordt_bij_dezelfde_invoer_eenmalig_toegepast():
    service = FakeService(succes_ui())
    handler, _ = _handler(service)
    sm = FakeSM(determined_category="proces", category_reasoning="r")
    _met_verzonden(sm, vingerafdruk=_vingerafdruk())
    st = MagicMock()
    _run(handler, sm, st)

    aanroep = service.aanroepen[0]
    assert aanroep["betekenisverduidelijking"] == "Bedoeld is de handeling"
    # Niet via vrije options, alleen via het typed veld.
    assert "betekenisverduidelijking" not in aanroep.get("options", {})
    assert KEY_VERZONDEN not in sm.data, "verduidelijking is eenmalig"
    assert KEY_OPEN not in sm.data
    assert not st.info.called


@pytest.mark.parametrize(
    "wijziging",
    [
        {"begrip": "keurmerk"},
        {"context": {**CONTEXT, "organisatorische_context": ["OM"]}},
        {"context": {**CONTEXT, "wettelijke_basis": ["Pbw"]}},
        {"sessie": {"manual_ontological_category": "TYPE"}},
        {"sessie": {"determined_category": None}},
        {"sessie": {"selected_documents": ["doc-abc"]}},
        {"sessie": {"rag_selected_collection_ids": [3]}},
        {"verzonden": {"generation_id": "ander-conflict"}},
        {"verzonden": {"tekst": "   "}},
    ],
)
def test_gewijzigde_invoer_of_ander_conflict_laat_verduidelijking_vervallen(wijziging):
    service = FakeService(succes_ui())
    handler, _ = _handler(service)
    sessie = {"determined_category": "proces", "category_reasoning": "r"}
    sessie.update(wijziging.get("sessie", {}))
    sm = FakeSM(**sessie)
    _met_verzonden(sm, vingerafdruk=_vingerafdruk(), **wijziging.get("verzonden", {}))
    st = MagicMock()
    with (
        patch.object(handler, "_get_document_context", return_value=None),
        patch.object(handler, "_build_document_snippets", return_value=[]),
    ):
        _run(
            handler,
            sm,
            st,
            begrip=wijziging.get("begrip", "registratie"),
            context=wijziging.get("context", CONTEXT),
        )

    aanroep = service.aanroepen[0]
    assert not aanroep.get("betekenisverduidelijking")
    assert KEY_VERZONDEN not in sm.data
    assert st.info.called
    assert "niet toegepast" in str(st.info.call_args)


def test_vingerafdruk_dekt_alle_relevante_invoer_en_is_stabiel():
    basis = _vingerafdruk()
    assert basis == _vingerafdruk()
    assert basis == _vingerafdruk(begrip="  Registratie ")
    assert basis == _vingerafdruk(organisatorische_context=["DJI"])
    for afwijkend in (
        {"begrip": "keurmerk"},
        {"organisatorische_context": ["OM"]},
        {"juridische_context": []},
        {"wettelijke_basis": ["Pbw"]},
        {"categorie": None},
        {"categorie": "type"},
        {"document_ids": ["doc-abc"]},
        {"rag_collection_ids": [3]},
    ):
        assert _vingerafdruk(**afwijkend) != basis, afwijkend
    # Volgorde van lijsten en documentselectie is irrelevant.
    assert _vingerafdruk(document_ids=["b", "a"]) == _vingerafdruk(
        document_ids=["a", "b"]
    )
