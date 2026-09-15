"""Streamlit-app voor het AppTest-ketenbewijs van de expertactie (DEF-622).

Wordt uitsluitend gestart door `streamlit.testing.v1.AppTest` vanuit
`run_def622_expert_apptest.py`, met een synthetische repository op het pad in
`DEF622_APPTEST_DB` (gezaaid door de driver) en het te beoordelen record in
`DEF622_APPTEST_RECORD`. Rendert dezelfde consumenten als de productie-UI:

1. de echte `ExpertReviewTab._render_definition_review` voor het gekozen
   record — details, contextcontract met de naamfunctie-invoer, de
   vaststelacties (gate-preview + "Vaststellen") en het reviewformulier met
   "Re-validate" — op een echte `ServiceContainer` (workflow-service en
   orchestrator) tegen de synthetische database;
2. de gedeelde validatieweergave (`render_validation_detailed_list`) met vijf
   echte CON-01-uitkomsten uit de echte `ModularValidationService`: Voldoet,
   Voldoet niet, Nog te beoordelen, Voldoet niet + Nog te beoordelen (B-08)
   en Technisch probleem (B-06).

Overige gatevoorwaarden zijn expliciet geïsoleerd: het gezaaide record heeft
een synthetische validatiescore en geen kritieke issues (DEF-630 blijft
eigenaar van de algemene gate); alleen CON-01 bepaalt hier de gate-uitkomst.

Isolatie: de offline-bootstrap staat vóór elke productimport aan (netwerk
dicht, SQLite alleen binnen de sessieroot, dummykeys).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

import streamlit as st

REPO = Path(__file__).resolve().parents[2]
for pad in (str(REPO), str(REPO / "src")):
    if pad not in sys.path:
        sys.path.insert(0, pad)

from tests import offline_bootstrap

offline_bootstrap.install()
assert offline_bootstrap.gate_is_actief(), "offline-gate niet actief in de app"

DB_PAD = os.environ["DEF622_APPTEST_DB"]
RECORD_ID = int(os.environ["DEF622_APPTEST_RECORD"])
WERKMAP = Path(DB_PAD).parent

import services.ai as ai_pakket
from database import definitie_repository as repo_module
from tests.integration.functionality.conftest import (
    BevrorenAIClient,
    _spiegel_relatieve_configs,
)

_spiegel_relatieve_configs(WERKMAP)
os.chdir(WERKMAP)
ai_pakket.create_ai_client = lambda provider, api_key, timeout=30.0: BevrorenAIClient()

repo = repo_module.get_definitie_repository(DB_PAD)
assert repo.db_path == DB_PAD, "repository-singleton wijst niet naar de testdatabase"

from services.container import ServiceContainer
from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.manager import get_toetsregel_manager
from ui.components.expert_review_tab import ExpertReviewTab
from ui.components.validation_view import render_validation_detailed_list
from ui.session_state import SessionStateManager
from utils import container_manager


def _container() -> ServiceContainer:
    """Echte container op de synthetische database, eenmaal per sessie."""
    if "def622_container" not in st.session_state:
        from services import ai_service_v2

        ai_service_v2.TIKTOKEN_AVAILABLE = False
        st.session_state["def622_container"] = ServiceContainer(
            {
                "db_path": DB_PAD,
                "enable_monitoring": False,
                "enable_ontology": False,
            }
        )
    return st.session_state["def622_container"]


# Geen enkel codepad mag alsnog de productiecontainer optuigen: zowel de
# manager als de al-geïmporteerde naam in `ui.cached_services`.
from ui import cached_services

container_manager.get_cached_container = _container
cached_services.get_cached_container = _container

SessionStateManager.initialize_session_state()
if SessionStateManager.get_value("selected_review_definition") is None:
    SessionStateManager.set_value(
        "selected_review_definition", repo.get_definitie(RECORD_ID)
    )

st.markdown("## Expertreview")
ExpertReviewTab(repo)._render_definition_review()


# --------------------------------------------------- vijf echte uitkomsten

ZIN_MET_NAAM = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
ZIN_ZONDER_NAAM = "kwaliteitsmerk voor gecontroleerde producten"
ZIN_TWEE_NAMEN = "merk binnen Stichting Zilver en Stichting Goud"


def _uitkomsten() -> dict[str, dict]:
    service = ModularValidationService(get_toetsregel_manager(), None, None)

    async def toets(text: str, context: dict) -> dict:
        return await service.validate_definition(
            begrip="keurmerk", text=text, context=context
        )

    async def alles() -> dict[str, dict]:
        org = {"organisatorische_context": ["Stichting Zilver"]}
        twee = {"organisatorische_context": ["Stichting Zilver", "Stichting Goud"]}
        eerste = await toets(ZIN_TWEE_NAMEN, dict(twee))
        detail = eerste["rule_results"]["CON-01"]
        zilver = next(
            p for p in detail["parts"] if p.get("evidence") == "Stichting Zilver"
        )
        beoordeeld = {
            **twee,
            "context_review": {
                "fingerprint": detail["fingerprint"],
                "actor": "Reviewer Rood",
                "decisions": {
                    zilver["id"]: {
                        "function": "registration",
                        "reason": "Noemt uitsluitend de registratieomgeving.",
                    }
                },
            },
        }
        uit = {
            "voldoet": await toets(ZIN_ZONDER_NAAM, dict(org)),
            "open": await toets(ZIN_MET_NAAM, dict(org)),
            "voldoet_niet": await toets(ZIN_ZONDER_NAAM, {}),
            "voldoet_niet_en_open": await toets(ZIN_TWEE_NAMEN, beoordeeld),
        }
        with patch(
            "services.validation.evaluators.context_metadata."
            "ContextMetadataEvaluator.evaluate",
            side_effect=RuntimeError("synthetische storing"),
        ):
            uit["technisch"] = await toets(ZIN_ZONDER_NAAM, dict(org))
        return uit

    return asyncio.run(alles())


if SessionStateManager.get_value("def622_uitkomsten") is None:
    SessionStateManager.set_value("def622_uitkomsten", _uitkomsten())

st.markdown("## Toetsing")
for naam, resultaat in SessionStateManager.get_value("def622_uitkomsten").items():
    st.markdown(f"### Geval: {naam}")
    render_validation_detailed_list(
        resultaat, key_prefix=f"def622_{naam}", show_toggle=False
    )
