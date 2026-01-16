"""
Category selection and display renderer for definition generator tab.

Extracted from definition_generator_tab.py as part of DEF-266 Phase 4 refactoring.
Handles ontological category display, UFO category selection, and category change workflows.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import streamlit as st

from services.category_state_manager import CategoryStateManager
from services.workflow_service import WorkflowAction, WorkflowService
from ui.components.formatters import (
    extract_definition_from_result,
    get_category_display_name,
)
from ui.session_state import SessionStateManager
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_string

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord

logger = logging.getLogger(__name__)


class CategoryRenderer:
    """Renderer voor ontologische categorie selectie en weergave."""

    def __init__(self):
        """Initialiseer category renderer."""
        self.workflow_service = WorkflowService()

    def render_ontological_category_section(
        self,
        determined_category: str,
        generation_result: dict[str, Any],
        saved_record: Any = None,
    ) -> None:
        """Render ontologische categorie sectie met uitleg en aanpassingsmogelijkheid."""
        st.markdown("#### 🎯 Ontologische Categorie")

        # Definieer categorie informatie
        category_info = {
            "type": {
                "label": "Type/Klasse",
                "icon": "🏷️",
                "description": "Begrip dat een categorie of klasse van objecten/concepten beschrijft",
                "examples": ["document", "systeem", "middel", "bewijs"],
            },
            "proces": {
                "label": "Proces/Activiteit",
                "icon": "⚙️",
                "description": "Begrip dat een activiteit, handeling of proces beschrijft",
                "examples": ["verificatie", "vaststelling", "controle", "behandeling"],
            },
            "resultaat": {
                "label": "Resultaat/Uitkomst",
                "icon": "📊",
                "description": "Begrip dat een uitkomst, resultaat of conclusie beschrijft",
                "examples": ["besluit", "rapport", "uitslag", "oordeel"],
            },
            "exemplaar": {
                "label": "Exemplaar/Instantie",
                "icon": "🔍",
                "description": "Begrip dat een specifiek exemplaar of instantie beschrijft",
                "examples": ["persoon", "zaak", "geval", "situatie"],
            },
        }

        current_info = category_info.get(determined_category, category_info["proces"])

        # Toon huidige categorie prominent
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{current_info['icon']} {current_info['label']}**")
            st.markdown(f"*{current_info['description']}*")

            # Toon waarom deze categorie gekozen is
            if "category_reasoning" in generation_result:
                st.markdown(f"**Reden:** {generation_result['category_reasoning']}")
            else:
                reasoning = self._generate_category_reasoning(determined_category)
                st.markdown(f"**Reden:** {reasoning}")

            # Toon alle scores in kleinere text
            if "category_scores" in generation_result:
                scores = generation_result["category_scores"]
                score_text = " | ".join(
                    [f"{cat}: {score:.2f}" for cat, score in scores.items()]
                )
                st.markdown(
                    f"<small>Alle scores: {score_text}</small>", unsafe_allow_html=True
                )

        with col2:
            if st.button("🔄 Wijzig Categorie", key="change_category"):
                SessionStateManager.set_value("show_category_selector", True)
                st.rerun()

        # Toon categorie selector als gevraagd
        if SessionStateManager.get_value("show_category_selector", False):
            self.render_category_selector(determined_category, generation_result)

        # Category change regeneration preview
        category_change_state = generation_result.get("category_change_state")
        if category_change_state and category_change_state.show_regeneration_preview:
            self.render_category_change_preview(
                category_change_state, generation_result, saved_record
            )

    def render_ufo_category_selector(self, generation_result: dict[str, Any]) -> None:
        """Render de UFO-categorie selectie en opslagknop."""
        st.markdown("#### 🧭 UFO-categorie")
        ufo_opties = [
            "",
            "Kind",
            "Event",
            "Role",
            "Phase",
            "Relator",
            "Mode",
            "Quantity",
            "Quality",
            "Subkind",
            "Category",
            "Mixin",
            "RoleMixin",
            "PhaseMixin",
            "Abstract",
            "Relatie",
            "Event Composition",
        ]

        saved_record = safe_dict_get(generation_result, "saved_record")
        saved_definition_id = safe_dict_get(generation_result, "saved_definition_id")
        target_id = None
        if isinstance(saved_definition_id, int) and saved_definition_id > 0:
            target_id = saved_definition_id
        elif saved_record and getattr(saved_record, "id", None):
            target_id = int(saved_record.id)

        current_ufo = None
        try:
            if target_id:
                from database.definitie_repository import get_definitie_repository

                repo = get_definitie_repository()
                rec = repo.get_definitie(target_id)
                current_ufo = getattr(rec, "ufo_categorie", None) if rec else None
        except Exception as e:
            logger.warning(f"UFO category lookup from repository failed: {e}")
            current_ufo = None

        try:
            default_index = (
                ufo_opties.index(current_ufo or "")
                if (current_ufo or "") in ufo_opties
                else 0
            )
        except Exception as e:
            logger.warning(f"UFO category default index calculation failed: {e}")
            default_index = 0

        def _persist_ufo_selection(key: str, def_id: int | None):
            try:
                if not def_id:
                    return
                value = SessionStateManager.get_value(key)
                if value == "":
                    value = None
                from database.definitie_repository import get_definitie_repository

                repo = get_definitie_repository()
                user = SessionStateManager.get_value("user", default="system")
                _ = repo.update_definitie(
                    int(def_id), {"ufo_categorie": value}, updated_by=user
                )
            except Exception as e:
                logger.warning(f"UFO category persist failed: {e}")

        key_sel = f"ufo_select_{target_id or 'new'}"
        st.selectbox(
            "Selecteer UFO-categorie",
            options=ufo_opties,
            index=default_index,
            key=key_sel,
            help="Kies de UFO-categorie volgens het OntoUML/UFO metamodel",
            on_change=_persist_ufo_selection,
            args=(key_sel, target_id),
        )

    def render_category_selector(
        self, current_category: str, generation_result: dict[str, Any]
    ) -> None:
        """Render categorie selector voor handmatige aanpassing."""
        st.markdown("##### 🎯 Kies Ontologische Categorie")

        options = [
            ("type", "🏷️ Type/Klasse"),
            ("proces", "⚙️ Proces/Activiteit"),
            ("resultaat", "📊 Resultaat/Uitkomst"),
            ("exemplaar", "🔍 Exemplaar/Instantie"),
        ]

        current_index = next(
            (i for i, (val, _) in enumerate(options) if val == current_category), 1
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            selected_option = st.selectbox(
                "Selecteer categorie:",
                options,
                index=current_index,
                format_func=lambda x: x[1],
                key="category_selector",
            )

        with col2:
            if st.button("✅ Toepassen", key="apply_category"):
                new_category = selected_option[0]
                SessionStateManager.set_value("show_category_selector", False)
                self._update_category(new_category, generation_result)

        with col3:
            if st.button("❌ Annuleren", key="cancel_category"):
                SessionStateManager.set_value("show_category_selector", False)
                st.rerun()

    def render_category_change_preview(
        self,
        category_change_state: Any,
        generation_result: dict[str, Any],
        saved_record: Any,
    ) -> None:
        """Render category change preview via DataAggregationService state."""
        st.markdown("---")
        st.markdown("### 🔄 Definitie Regeneratie Preview")

        if category_change_state.success_message:
            st.success(category_change_state.success_message)

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("**Oude Categorie:**")
            st.markdown(
                f"🏷️ `{get_category_display_name(category_change_state.old_category)}`"
            )

        with col2:
            st.markdown("**➡️**")

        with col3:
            st.markdown("**Nieuwe Categorie:**")
            st.markdown(
                f"🎯 `{get_category_display_name(category_change_state.new_category)}`"
            )

        st.markdown("**Huidige Definitie:**")
        definition_preview = category_change_state.current_definition
        st.info(
            definition_preview[:200] + ("..." if len(definition_preview) > 200 else "")
        )

        if category_change_state.impact_analysis:
            st.markdown("**Verwachte Impact:**")
            for impact in category_change_state.impact_analysis:
                st.markdown(f"• {impact}")

        st.markdown("**Kies je actie:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "🚀 Direct Regenereren",
                key="direct_regenerate_clean",
                help="Genereer direct een nieuwe definitie met de nieuwe categorie",
                type="primary",
            ):
                self._direct_regenerate_definition(
                    begrip=category_change_state.begrip,
                    new_category=category_change_state.new_category,
                    old_category=category_change_state.old_category,
                    saved_record=saved_record,
                    generation_result=generation_result,
                )

        with col2:
            if st.button(
                "🎯 Handmatig Aanpassen",
                key="manual_regenerate_clean",
                help="Ga naar generator om handmatig aan te passen",
            ):
                self._trigger_regeneration_with_category(
                    begrip=category_change_state.begrip,
                    new_category=category_change_state.new_category,
                    old_category=category_change_state.old_category,
                    saved_record=saved_record,
                )

        with col3:
            if st.button(
                "✅ Behoud Huidige",
                key="keep_current_def_clean",
                help="Behoud de huidige definitie met nieuwe categorie",
            ):
                generation_result.pop("category_change_state", None)
                st.success("✅ Definitie behouden met nieuwe categorie!")
                st.rerun()

    def render_regeneration_preview(
        self,
        begrip: str,
        current_definition: str,
        old_category: str,
        new_category: str,
        generation_result: dict[str, Any],
        saved_record: Any,
    ) -> None:
        """Render enhanced preview voor regeneration met betere UX."""
        st.markdown("---")
        st.markdown("### 🔄 Definitie Regeneratie Preview")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("**Oude Categorie:**")
            st.markdown(f"🏷️ `{get_category_display_name(old_category)}`")

        with col2:
            st.markdown("**➡️**")

        with col3:
            st.markdown("**Nieuwe Categorie:**")
            st.markdown(f"🎯 `{get_category_display_name(new_category)}`")

        st.markdown("**Huidige Definitie:**")
        st.info(
            current_definition[:200] + ("..." if len(current_definition) > 200 else "")
        )

        impact_analysis = self.workflow_service._analyze_category_change_impact(
            old_category, new_category
        )

        st.markdown("**Verwachte Impact:**")
        for impact in impact_analysis:
            st.markdown(f"• {impact}")

        st.markdown("**Kies je actie:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "🚀 Direct Regenereren",
                key="direct_regenerate",
                help="Genereer direct een nieuwe definitie met de nieuwe categorie",
                type="primary",
            ):
                self._direct_regenerate_definition(
                    begrip=begrip,
                    new_category=new_category,
                    old_category=old_category,
                    saved_record=saved_record,
                    generation_result=generation_result,
                )

        with col2:
            if st.button(
                "🎯 Handmatig Aanpassen",
                key="manual_regenerate",
                help="Ga naar generator om handmatig aan te passen",
            ):
                self._trigger_regeneration_with_category(
                    begrip=begrip,
                    new_category=new_category,
                    old_category=old_category,
                    saved_record=saved_record,
                )

        with col3:
            if st.button(
                "✅ Behoud Huidige",
                key="keep_current_def",
                help="Behoud de huidige definitie met nieuwe categorie",
            ):
                st.success("✅ Definitie behouden met nieuwe categorie!")
                st.info(
                    "De categorie is bijgewerkt, maar de definitie blijft ongewijzigd."
                )

    def render_definition_comparison(
        self,
        old_definition: str,
        new_result: dict,
        old_category: str,
        new_category: str,
    ) -> None:
        """Render comparison tussen oude en nieuwe definitie."""
        st.markdown("---")
        st.markdown("### 📊 Definitie Vergelijking")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"**Oude Definitie** ({get_category_display_name(old_category)}):"
            )
            st.info(old_definition)

        with col2:
            st.markdown(
                f"**Nieuwe Definitie** ({get_category_display_name(new_category)}):"
            )

            if isinstance(new_result, dict):
                new_definition = new_result.get(
                    "definitie_gecorrigeerd",
                    new_result.get("definitie", "Geen definitie beschikbaar"),
                )
            else:
                new_definition = getattr(
                    new_result, "final_definitie", "Geen definitie beschikbaar"
                )

            st.success(new_definition)

        if isinstance(new_result, dict) and "validation_score" in new_result:
            new_score = new_result["validation_score"]
            st.markdown(f"**Kwaliteitsscore nieuwe definitie:** {new_score:.2f}")

    # ============ Private methods ============

    def _generate_category_reasoning(self, category: str) -> str:
        """Genereer uitleg waarom deze categorie gekozen is."""
        reasonings = {
            "type": "Begrip bevat woorden die wijzen op een categorie of klasse van objecten",
            "proces": "Begrip bevat woorden die wijzen op een activiteit of proces",
            "resultaat": "Begrip bevat woorden die wijzen op een uitkomst of resultaat",
            "exemplaar": "Begrip bevat woorden die wijzen op een specifiek exemplaar of instantie",
        }
        return reasonings.get(
            category, "Automatisch bepaald op basis van woordpatronen"
        )

    def _update_category(
        self, new_category: str, generation_result: dict[str, Any]
    ) -> None:
        """Update de ontologische categorie via WorkflowService."""
        old_category = safe_dict_get(generation_result, "determined_category", "proces")
        current_definition = extract_definition_from_result(generation_result)
        begrip = ensure_string(safe_dict_get(generation_result, "begrip", ""))
        saved_record = generation_result.get("saved_record")

        result = self.workflow_service.execute_category_change_workflow(
            definition_id=saved_record.id if saved_record else None,
            old_category=old_category,
            new_category=new_category,
            current_definition=current_definition,
            begrip=begrip,
            user="web_user",
            reason="Handmatige aanpassing via UI",
        )

        if result.success:
            CategoryStateManager.update_generation_result_category(
                generation_result, new_category
            )
            SessionStateManager.set_value("manual_ontological_category", new_category)
            logger.info(f"Handmatige categorie override gezet: {new_category}")

        if result.success:
            st.success(result.message)
        else:
            st.error(result.message)
            return

        if result.action == WorkflowAction.SHOW_REGENERATION_PREVIEW:
            generation_result["category_change_state"] = result.preview_data.get(
                "category_change_state"
            )
            SessionStateManager.set_value("show_category_selector", False)
        elif result.action == WorkflowAction.SHOW_ERROR:
            logger.error(f"Category change workflow error: {result.error}")

    def _trigger_regeneration_with_category(
        self,
        begrip: str,
        new_category: str,
        old_category: str,
        saved_record: DefinitieRecord,
    ) -> None:
        """Deprecated: Regeneration service removed (US-445)."""
        st.info(
            f"💡 Om te regenereren met categorie '{new_category}': "
            f"Ga naar Generator tab, wijzig categorie dropdown, en klik 'Genereer Definitie'"
        )

    def _direct_regenerate_definition(
        self,
        begrip: str,
        new_category: str,
        old_category: str,
        saved_record: Any,
        generation_result: dict[str, Any],
    ) -> None:
        """Trigger direct regeneration with new ontological category."""
        SessionStateManager.set_value("manual_ontological_category", new_category)

        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")
        SessionStateManager.clear_value("last_check_result")

        options = SessionStateManager.get_value("generation_options", {})
        options.pop("force_generate", None)
        options.pop("force_duplicate", None)
        SessionStateManager.set_value("generation_options", options)

        SessionStateManager.set_value("trigger_auto_generation", True)

        st.success(f"✅ Regeneratie gestart met categorie '{new_category}'!")
        st.rerun()

    def analyze_regeneration_impact(
        self, old_category: str, new_category: str
    ) -> list[str]:
        """Analyseer verwachte impact van category change."""
        impacts = []

        if old_category == "proces" and new_category == "type":
            impacts.extend(
                [
                    "🔄 Focus verschuift van 'hoe' naar 'wat'",
                    "📝 Definitie wordt meer beschrijvend dan procedureel",
                    "⚖️ Juridische precisie kan toenemen",
                ]
            )
        elif old_category == "type" and new_category == "proces":
            impacts.extend(
                [
                    "🔄 Focus verschuift van 'wat' naar 'hoe'",
                    "📋 Definitie wordt meer procedureel",
                    "⚙️ Stappen/fasen kunnen worden toegevoegd",
                ]
            )
        elif "resultaat" in [old_category, new_category]:
            impacts.append("📊 Uitkomst-georiënteerde bewoordingen")
        elif "exemplaar" in [old_category, new_category]:
            impacts.append("🔍 Specificiteit niveau kan wijzigen")

        impacts.extend(
            [
                "🎯 Terminologie wordt aangepast aan nieuwe categorie",
                "✅ Kwaliteitstoetsing wordt opnieuw uitgevoerd",
                "📄 Nieuwe definitie krijgt eigen versiehistorie",
            ]
        )

        return impacts

    def extract_context_from_generation_result(
        self, generation_result: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Extract context information from previous generation result."""
        context_dict: dict[str, list[str]] = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
        }

        if "document_context" in generation_result:
            doc_context = generation_result["document_context"]
            if isinstance(doc_context, dict):
                for key in context_dict:
                    if key in doc_context:
                        context_dict[key] = doc_context[key]

        for context_type, context_value in list(context_dict.items()):
            session_value = SessionStateManager.get_value(f"{context_type}_context", [])
            if session_value and not context_value:
                context_dict[context_type] = session_value

        return context_dict
