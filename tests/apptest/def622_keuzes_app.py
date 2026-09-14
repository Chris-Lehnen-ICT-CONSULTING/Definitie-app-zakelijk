"""Streamlit-app voor het AppTest-ketenbewijs van DEF-622 (B-08/B-09).

Wordt uitsluitend gestart door `streamlit.testing.v1.AppTest` vanuit
`run_def622_apptest.py`, met een synthetische repository op het pad in
`DEF622_APPTEST_DB` (gezaaid door de driver). Rendert dezelfde consumenten
als de productie-UI, zonder de volledige `TabbedInterface`:

1. de duplicaatmelding met de drie bestaande keuzes via de echte
   `DefinitionGeneratorTab`-resultaatsectie, na een echte
   `DefinitieChecker.check_before_generation`;
2. na "Bewerk": de echte `DefinitionEditTab` die `editing_definition_id`
   consumeert en het record in de editor laadt;
3. na "Genereer Nieuw" (met reden): de echte `DefinitionGenerationHandler`
   op een echte `ServiceContainer`/`ServiceAdapter` — de enige bevroren grens
   is de AI-client (`BevrorenAIClient`, dezelfde als de offline kernjourney);
   het nieuwe concept wordt door productiecode in de synthetische DB
   opgeslagen;
4. de gedeelde validatieweergave met een echte CON-01-uitkomst.

Isolatie: de offline-bootstrap (`tests.offline_bootstrap.install`) staat vóór
elke productimport aan — netwerk dicht, SQLite alleen binnen de sessieroot,
dummykeys. Onder `run_profile` is hij via `sitecustomize` al actief
(idempotent).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parents[2]
for pad in (str(REPO), str(REPO / "src")):
    if pad not in sys.path:
        sys.path.insert(0, pad)

from tests import offline_bootstrap

offline_bootstrap.install()
assert offline_bootstrap.gate_is_actief(), "offline-gate niet actief in de app"

DB_PAD = os.environ["DEF622_APPTEST_DB"]
WERKMAP = Path(DB_PAD).parent

import services.ai as ai_pakket
from database import definitie_repository as repo_module
from tests.integration.functionality.conftest import (
    BevrorenAIClient,
    _spiegel_relatieve_configs,
)

# Relatieve schrijfpaden (cache, exports) landen in de werkmap, niet in de repo.
_spiegel_relatieve_configs(WERKMAP)
os.chdir(WERKMAP)
# De enige bevroren grens: de providerclient.
ai_pakket.create_ai_client = lambda provider, api_key, timeout=30.0: BevrorenAIClient()

repo = repo_module.get_definitie_repository(DB_PAD)
assert repo.db_path == DB_PAD, "repository-singleton wijst niet naar de testdatabase"

from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import DefinitieChecker
from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.manager import get_toetsregel_manager
from ui.components.definition_generator_tab import DefinitionGeneratorTab
from ui.components.validation_view import render_validation_detailed_list
from ui.session_state import SessionStateManager

GLOBAL_CONTEXT = {
    "organisatorische_context": ["Stichting Zilver"],
    "juridische_context": ["privaatrecht"],
    "wettelijke_basis": ["Regeling Z"],
}

SessionStateManager.initialize_session_state()
SessionStateManager.set_value("global_context", GLOBAL_CONTEXT)
SessionStateManager.set_value("begrip", "keurmerk")
# Pre-classificatie is verplicht voor de handler (single path).
SessionStateManager.set_value("determined_category", "TYPE")
SessionStateManager.set_value("selected_documents", [])

checker = DefinitieChecker(repo)
if not SessionStateManager.get_value("def622_gecontroleerd"):
    # Lookup met afwijkende schrijfwijze/volgorde: bewijst de genormaliseerde
    # gelijke-contextherkenning op de echte UI-route.
    SessionStateManager.set_value(
        "last_check_result",
        checker.check_before_generation(
            begrip="keurmerk",
            organisatorische_context='["stichting zilver"]',
            juridische_context='["Privaatrecht"]',
            categorie=OntologischeCategorie.TYPE,
            wettelijke_basis=["regeling z"],
        ),
    )
    SessionStateManager.set_value("def622_gecontroleerd", True)


def _adapter():
    """Echte container + adapter, eenmaal per sessie (dure opbouw)."""
    if "def622_adapter" not in st.session_state:
        from services import ai_service_v2
        from services.container import ServiceContainer
        from services.service_factory import ServiceAdapter
        from utils import container_manager

        # Zelfde hermetische keuze als de pytest-conftest (`_mock_tiktoken`):
        # de tokenheuristiek i.p.v. tiktoken, dat anders een BPE-bestand
        # wil downloaden — en dat is netwerk.
        ai_service_v2.TIKTOKEN_AVAILABLE = False

        container = ServiceContainer(
            {
                "db_path": DB_PAD,
                "enable_monitoring": False,
                "enable_ontology": False,
            }
        )
        # Geen enkel codepad mag alsnog de productiecontainer optuigen.
        container_manager.get_cached_container = lambda: container

        # Zelfde grenzen als `bevroren_omgeving`: de cache schrijft in de
        # werkmap, en de voorbeeldengenerator gebruikt de AIServiceV2 van
        # déze container (met de bevroren client) — anders bouwt hij een
        # eigen client en probeert die het netwerk.
        from utils import cache as cache_module
        from voorbeelden import unified_voorbeelden

        cache_map = WERKMAP / "cache"
        cache_map.mkdir(exist_ok=True)
        cache_module._cache.cache_dir = cache_map
        cache_module._cache.config.cache_dir = cache_map
        cache_module._cache.metadata_file = cache_map / "meta.json"
        cache_module._cache.metadata = {}
        unified_voorbeelden.reset_examples_generator()
        unified_voorbeelden.get_examples_generator().ai_service = container.ai_service()
        st.session_state["def622_adapter"] = ServiceAdapter(container)
    return st.session_state["def622_adapter"]


# Zelfde consument als `TabbedInterface.render`: een gezette trigger start de
# generatie via de echte handler.
if SessionStateManager.get_value("trigger_auto_generation", False):
    SessionStateManager.clear_value("trigger_auto_generation")
    from ui.handlers.definition_generation_handler import (
        DefinitionGenerationHandler,
    )

    DefinitionGenerationHandler(
        checker=checker, definition_service=_adapter(), repository=repo
    ).handle_definition_generation("keurmerk", GLOBAL_CONTEXT)

st.markdown("## Generatie")
DefinitionGeneratorTab(checker)._render_results_section()

if SessionStateManager.get_value("active_tab") == "edit":
    # Zelfde consument als de Bewerk-tab in `TabbedInterface`.
    from services.definition_edit_repository import DefinitionEditRepository
    from ui.components.definition_edit_tab import DefinitionEditTab

    st.markdown("## Bewerken")
    DefinitionEditTab(repository=DefinitionEditRepository(DB_PAD)).render()

st.markdown("## Toetsing")
if SessionStateManager.get_value("def622_validatie") is None:
    service = ModularValidationService(get_toetsregel_manager(), None, None)
    SessionStateManager.set_value(
        "def622_validatie",
        asyncio.run(
            service.validate_definition(
                begrip="keurmerk",
                text="kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend",
                context={"organisatorische_context": ["Stichting Zilver"]},
            )
        ),
    )
render_validation_detailed_list(
    SessionStateManager.get_value("def622_validatie"),
    key_prefix="def622",
    show_toggle=False,
)
