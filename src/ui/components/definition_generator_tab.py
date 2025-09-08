"""
Definition Generator Tab - Main AI definition generation interface.
"""

import logging
from datetime import UTC
from typing import Any

import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieStatus,
    get_definitie_repository,
)
from integration.definitie_checker import CheckAction, DefinitieChecker
from services.category_service import CategoryService
from services.category_state_manager import CategoryStateManager
from services.regeneration_service import RegenerationService
from services.workflow_service import WorkflowService
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class DefinitionGeneratorTab:
    """Tab voor AI definitie generatie met duplicate checking."""

    def __init__(self, checker: DefinitieChecker):
        """Initialiseer generator tab."""
        self.checker = checker
        self.category_service = CategoryService(get_definitie_repository())
        self.workflow_service = WorkflowService()  # Business logic voor status workflow

        # TODO: Inject via dependency injection wanneer beschikbaar
        from services.definition_generator_config import UnifiedGeneratorConfig
        from services.definition_generator_prompts import UnifiedPromptBuilder

        # Basic config voor regeneration service
        config = UnifiedGeneratorConfig()
        prompt_builder = UnifiedPromptBuilder(config)
        self.regeneration_service = RegenerationService(prompt_builder)

    def render(self):
        """Render definitie generatie tab."""
        st.info(
            "💡 Gebruik de hoofdknoppen boven de tabs om definities te genereren. Resultaten worden hier getoond."
        )

        # Results sectie
        self._render_results_section()

    def _render_results_section(self):
        """Render resultaten van generatie of duplicate check."""
        # Check voor resultaten in session state
        check_result = SessionStateManager.get_value("last_check_result")
        generation_result = SessionStateManager.get_value("last_generation_result")

        if check_result:
            self._render_duplicate_check_results(check_result)

        if generation_result:
            self._render_generation_results(generation_result)

    def _render_duplicate_check_results(self, check_result):
        """Render resultaten van duplicate check."""
        st.markdown("### 🔍 Duplicate Check Resultaten")

        # Main result
        if check_result.action == CheckAction.PROCEED:
            st.success(f"✅ {check_result.message}")
        elif check_result.action == CheckAction.USE_EXISTING:
            st.warning(f"⚠️ {check_result.message}")
        else:
            st.info(f"i️ {check_result.message}")

        # Show confidence
        confidence_color = (
            "green"
            if check_result.confidence > 0.8
            else "orange" if check_result.confidence > 0.5 else "red"
        )
        st.markdown(
            f"**Vertrouwen:** <span style='color: {confidence_color}'>{check_result.confidence:.1%}</span>",
            unsafe_allow_html=True,
        )

        # Show existing definition if found
        if check_result.existing_definitie:
            self._render_existing_definition(check_result.existing_definitie)

        # Show duplicates if found
        if check_result.duplicates:
            self._render_duplicate_matches(check_result.duplicates)

    def _render_existing_definition(self, definitie: DefinitieRecord):
        """Render bestaande definitie details."""
        st.markdown("#### 📋 Bestaande Definitie")

        with st.expander(f"Definitie Details (ID: {definitie.id})", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Definitie:** {definitie.definitie}")
                st.markdown(f"**Context:** {definitie.organisatorische_context}")
                if definitie.juridische_context:
                    st.markdown(f"**Juridisch:** {definitie.juridische_context}")

            with col2:
                st.markdown(f"**Status:** `{definitie.status}`")
                st.markdown(f"**Categorie:** `{definitie.categorie}`")
                if definitie.validation_score:
                    st.markdown(f"**Score:** {definitie.validation_score:.2f}")
                st.markdown(
                    f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d') if definitie.created_at else 'Onbekend'}"
                )

            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Gebruik Deze", key=f"use_{definitie.id}"):
                    self._use_existing_definition(definitie)

            with col2:
                if st.button("📝 Bewerk", key=f"edit_{definitie.id}"):
                    self._edit_existing_definition(definitie)

            with col3:
                if st.button("🔄 Genereer Nieuw", key=f"new_{definitie.id}"):
                    # Force new generation
                    options = SessionStateManager.get_value("generation_options", {})
                    options["force_generate"] = True
                    SessionStateManager.set_value("generation_options", options)
                    self._handle_definition_generation()

    def _render_duplicate_matches(self, duplicates):
        """Render lijst van mogelijke duplicates."""
        st.markdown("#### 🔍 Mogelijke Duplicates")

        for i, dup_match in enumerate(duplicates[:3]):  # Toon max 3
            definitie = dup_match.definitie_record
            score = dup_match.match_score
            reasons = dup_match.match_reasons

            with st.expander(
                f"Match {i+1}: {definitie.begrip} (Score: {score:.2f})", expanded=i == 0
            ):
                st.markdown(f"**Definitie:** {definitie.definitie}")
                st.markdown(f"**Context:** {definitie.organisatorische_context}")
                st.markdown(f"**Redenen:** {', '.join(reasons)}")

                if st.button("Gebruik deze definitie", key=f"dup_use_{definitie.id}"):
                    self._use_existing_definition(definitie)

    def _render_generation_results(self, generation_result):
        """Render resultaten van definitie generatie."""
        st.markdown("### 🚀 Generatie Resultaten")

        agent_result = generation_result.get("agent_result")
        saved_record = generation_result.get("saved_record")
        generation_result.get("timestamp")
        determined_category = generation_result.get("determined_category")

        # Debug: Log de structuur van generation_result
        logger.debug(f"Generation result keys: {list(generation_result.keys())}")
        if agent_result and isinstance(agent_result, dict):
            logger.debug(f"Agent result type: dict, keys: {list(agent_result.keys())}")
            if "metadata" in agent_result:
                logger.debug(
                    f"Agent result metadata keys: {list(agent_result['metadata'].keys()) if isinstance(agent_result['metadata'], dict) else 'Not a dict'}"
                )
        elif agent_result:
            logger.debug(f"Agent result type: {type(agent_result).__name__}")

        if agent_result:
            # Check if it's a dict (new service) or object (legacy)
            is_dict = isinstance(agent_result, dict)

            # Success indicator
            if is_dict:
                # New service format
                if agent_result.get("success"):
                    score = agent_result.get(
                        "validation_score", agent_result.get("final_score", 0.0)
                    )
                    st.success(
                        f"✅ Definitie succesvol gegenereerd! (Score: {score:.2f})"
                    )
                else:
                    reason = agent_result.get("reason", "Onbekende fout")
                    st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {reason}")
            elif hasattr(agent_result, "success") and agent_result.success:
                st.success(
                    f"✅ Definitie succesvol gegenereerd! (Score: {agent_result.final_score:.2f})"
                )
            else:
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {agent_result.reason}")

            # Ontologische categorie sectie - prominent weergeven
            if determined_category:
                self._render_ontological_category_section(
                    determined_category, generation_result
                )

            # Generated definition
            st.markdown("#### 📝 Gegenereerde Definitie")

            # Debug: toon wat we hebben
            if st.checkbox(
                "🐛 Debug: Toon agent_result structuur", key="debug_agent_result"
            ):
                st.code(f"Type: {type(agent_result)}")
                st.code(f"Is dict: {is_dict}")
                if is_dict:
                    st.code(f"Keys: {list(agent_result.keys())}")
                    st.code(
                        f"Has definitie_origineel: {'definitie_origineel' in agent_result}"
                    )
                    st.code(
                        f"Has definitie_gecorrigeerd: {'definitie_gecorrigeerd' in agent_result}"
                    )
                else:
                    st.code(f"Attributes: {dir(agent_result)}")

            # Handle both dict (new service) and object (legacy) formats
            if is_dict:
                # New service returns dict with definitie_gecorrigeerd
                definitie_to_show = agent_result.get(
                    "definitie_gecorrigeerd", agent_result.get("definitie", "")
                )
                # Debug logging voor opschoning
                if (
                    "definitie_origineel" in agent_result
                    and "definitie_gecorrigeerd" in agent_result
                ):
                    if (
                        agent_result["definitie_origineel"]
                        != agent_result["definitie_gecorrigeerd"]
                    ):
                        logger.info(
                            f"Opschoning toegepast voor '{generation_result.get('begrip', 'onbekend')}'"
                        )
                        logger.debug(
                            f"Origineel: {agent_result['definitie_origineel'][:100]}..."
                        )
                        logger.debug(
                            f"Opgeschoond: {agent_result['definitie_gecorrigeerd'][:100]}..."
                        )
            else:
                # Legacy returns object with final_definitie
                definitie_to_show = agent_result.final_definitie
            # Toon ALTIJD beide versies
            # Nu werkt 'in' operator voor zowel dict als LegacyGenerationResult
            if (
                "definitie_origineel" in agent_result
                and "definitie_gecorrigeerd" in agent_result
            ):
                # Toon opschoning status
                if (
                    agent_result["definitie_origineel"]
                    != agent_result["definitie_gecorrigeerd"]
                ):
                    st.success("🔧 **Definitie is opgeschoond**")
                else:
                    st.info("✅ **Geen opschoning nodig - definitie was al correct**")

                # Toon ALTIJD beide versies
                st.subheader("1️⃣ Originele AI Definitie")
                st.info(agent_result["definitie_origineel"])

                st.subheader("2️⃣ Finale Definitie")
                st.info(agent_result["definitie_gecorrigeerd"])
            else:
                # Legacy format - toon enkele definitie
                st.subheader("📝 Definitie")
                st.info(definitie_to_show)

            # Bronverantwoording: toon gebruikte web bronnen indien beschikbaar
            self._render_sources_section(generation_result, agent_result, saved_record)

            # Generation details
            with st.expander("📊 Generatie Details", expanded=False):
                col1, col2, col3 = st.columns(3)

                if is_dict:
                    # New service format
                    with col1:
                        score = agent_result.get(
                            "validation_score", agent_result.get("final_score", 0.0)
                        )
                        st.metric("Finale Score", f"{score:.2f}")
                        if agent_result.get("marker"):
                            st.caption(agent_result["marker"])

                    with col2:
                        processing_time = agent_result.get("processing_time", 0.0)
                        st.metric("Verwerkingstijd", f"{processing_time:.1f}s")
                        st.metric(
                            "Succes", "Ja" if agent_result.get("success") else "Nee"
                        )

                    with col3:
                        if "toetsresultaten" in agent_result:
                            violations = len(agent_result["toetsresultaten"])
                            st.metric("Violations", violations)
                else:
                    # Legacy format
                    with col1:
                        if agent_result.iteration_count > 1:
                            st.metric("Iteraties", agent_result.iteration_count)
                        st.metric("Finale Score", f"{agent_result.final_score:.2f}")

                    with col2:
                        st.metric(
                            "Verwerkingstijd",
                            f"{agent_result.total_processing_time:.1f}s",
                        )
                        st.metric("Succes", "Ja" if agent_result.success else "Nee")

                    with col3:
                        if agent_result.best_iteration:
                            violations = len(
                                agent_result.best_iteration.validation_result.violations
                            )
                            st.metric("Violations", violations)

                    # Iteration history (only for legacy)
                    if len(agent_result.iterations) > 1:
                        st.markdown("**Iteratie Geschiedenis:**")
                        for iteration in agent_result.iterations:
                            score = iteration.validation_result.overall_score
                            st.write(
                                f"Iteratie {iteration.iteration_number}: Score {score:.2f}"
                            )

            # Validation results
            if is_dict:
                # New service format - validation details might be in different structure
                if agent_result.get("validation_details"):
                    self._render_validation_results(agent_result["validation_details"])

                # Check for voorbeelden in dict format
                # Store prompt_text in session state if available
                if agent_result.get("prompt_text"):
                    SessionStateManager.set_value(
                        "prompt_text", agent_result["prompt_text"]
                    )

                if agent_result.get("voorbeelden"):
                    self._render_voorbeelden_section(agent_result["voorbeelden"])

                    # Store voorbeelden in session state for export
                    voorbeelden = agent_result["voorbeelden"]
                    if isinstance(voorbeelden, dict):
                        SessionStateManager.set_value(
                            "voorbeeld_zinnen", voorbeelden.get("sentence", [])
                        )
                        SessionStateManager.set_value(
                            "praktijkvoorbeelden", voorbeelden.get("practical", [])
                        )
                        SessionStateManager.set_value(
                            "tegenvoorbeelden", voorbeelden.get("counter", [])
                        )
                        SessionStateManager.set_value(
                            "synoniemen", "\n".join(voorbeelden.get("synonyms", []))
                        )
                        SessionStateManager.set_value(
                            "antoniemen", "\n".join(voorbeelden.get("antonyms", []))
                        )
                        SessionStateManager.set_value(
                            "toelichting",
                            (
                                voorbeelden.get("explanation", [""])[0]
                                if voorbeelden.get("explanation")
                                else ""
                            ),
                        )
            elif agent_result.best_iteration:
                self._render_validation_results(
                    agent_result.best_iteration.validation_result
                )

                # Render voorbeelden als deze gegenereerd zijn
                if (
                    hasattr(
                        agent_result.best_iteration.generation_result, "voorbeelden"
                    )
                    and agent_result.best_iteration.generation_result.voorbeelden
                ):
                    self._render_voorbeelden_section(
                        agent_result.best_iteration.generation_result.voorbeelden
                    )

                    # Store voorbeelden in session state voor export
                    voorbeelden = (
                        agent_result.best_iteration.generation_result.voorbeelden
                    )
                    SessionStateManager.set_value(
                        "voorbeeld_zinnen", voorbeelden.get("sentence", [])
                    )
                    SessionStateManager.set_value(
                        "praktijkvoorbeelden", voorbeelden.get("practical", [])
                    )
                    SessionStateManager.set_value(
                        "tegenvoorbeelden", voorbeelden.get("counter", [])
                    )
                    SessionStateManager.set_value(
                        "synoniemen", "\n".join(voorbeelden.get("synonyms", []))
                    )
                    SessionStateManager.set_value(
                        "antoniemen", "\n".join(voorbeelden.get("antonyms", []))
                    )
                    SessionStateManager.set_value(
                        "toelichting",
                        (
                            voorbeelden.get("explanation", [""])[0]
                            if voorbeelden.get("explanation")
                            else ""
                        ),
                    )
                # Debug: toon waarom voorbeelden niet worden gerenderd
                elif not hasattr(
                    agent_result.best_iteration.generation_result, "voorbeelden"
                ):
                    st.warning(
                        "⚠️ Geen 'voorbeelden' attribuut gevonden in generation_result"
                    )
                elif not agent_result.best_iteration.generation_result.voorbeelden:
                    st.warning("⚠️ Voorbeelden dictionary is leeg")

            # Render prompt debug section
            from ui.components.prompt_debug_section import PromptDebugSection

            if is_dict:
                # New service format - extraheer prompt uit metadata
                class PromptContainer:
                    """Wrapper om prompt_template beschikbaar te maken voor PromptDebugSection."""

                    def __init__(self, prompt_template: str):
                        self.prompt_template = prompt_template

                # Probeer eerst de prompt uit saved_record te halen (meest betrouwbaar)
                prompt_template = None

                if saved_record and saved_record.metadata:
                    metadata = saved_record.metadata
                    if isinstance(metadata, dict) and "prompt_template" in metadata:
                        prompt_template = metadata["prompt_template"]
                        logger.debug("Prompt gevonden in saved_record metadata")

                # Als dat niet lukt, probeer uit agent_result
                if not prompt_template:
                    if "metadata" in agent_result and isinstance(
                        agent_result["metadata"], dict
                    ):
                        prompt_template = agent_result["metadata"].get(
                            "prompt_template"
                        )
                        if prompt_template:
                            logger.debug("Prompt gevonden in agent_result metadata")
                    elif "prompt_template" in agent_result:
                        prompt_template = agent_result["prompt_template"]
                        logger.debug("Prompt gevonden direct in agent_result")
                    elif "prompt_text" in agent_result:
                        # Support voor nieuwe V2 orchestrator die prompt_text gebruikt
                        prompt_template = agent_result["prompt_text"]
                        logger.debug(
                            "Prompt gevonden als 'prompt_text' in agent_result"
                        )
                    elif "prompt" in agent_result:
                        prompt_template = agent_result["prompt"]
                        logger.debug("Prompt gevonden als 'prompt' in agent_result")

                # Haal voorbeelden_prompts op voor beide paths
                voorbeelden_prompts = (
                    generation_result.get("voorbeelden_prompts")
                    if generation_result
                    else None
                )

                # Render de debug sectie
                if prompt_template:
                    prompt_container = PromptContainer(prompt_template)
                    PromptDebugSection.render(prompt_container, voorbeelden_prompts)
                else:
                    # Als er nog steeds geen prompt is, toon de debug sectie met lege prompt
                    with st.expander("🔍 Debug: Gebruikte Prompts", expanded=False):
                        st.info(
                            "Geen prompt informatie beschikbaar voor deze generatie."
                        )
                        st.caption(
                            "Dit kan gebeuren bij oudere generaties of wanneer de prompt niet is opgeslagen."
                        )

                        # Als er wel voorbeelden prompts zijn, toon die alsnog
                        if voorbeelden_prompts:
                            st.markdown("#### 🎯 Voorbeelden Generatie Prompts")
                            tabs = st.tabs(list(voorbeelden_prompts.keys()))

                            for i, (example_type, prompt) in enumerate(
                                voorbeelden_prompts.items()
                            ):
                                with tabs[i]:
                                    st.code(prompt, language="text")

                                    # Download knop per type
                                    st.download_button(
                                        label=f"⬇️ Download {example_type} Prompt",
                                        data=prompt,
                                        file_name=f"{example_type}_prompt.txt",
                                        mime="text/plain",
                                        key=f"download_{example_type}_prompt_fallback",
                                    )
            else:
                # Legacy format
                iteration_result = (
                    agent_result.best_iteration.generation_result
                    if agent_result.best_iteration
                    else None
                )
                voorbeelden_prompts = (
                    generation_result.get("voorbeelden_prompts")
                    if generation_result
                    else None
                )
                PromptDebugSection.render(iteration_result, voorbeelden_prompts)

        # Category change regeneration preview (op logische locatie)
        category_change_state = generation_result.get("category_change_state")
        if category_change_state and category_change_state.show_regeneration_preview:
            self._render_category_change_preview(
                category_change_state, generation_result, saved_record
            )

        # Saved record info
        if saved_record:
            st.markdown("#### 💾 Database Record")
            st.info(
                f"Definitie opgeslagen met ID: {saved_record.id} (Status: {saved_record.status})"
            )

            # Action buttons
            col1, col2, col3 = st.columns(3)

    def _render_ontological_category_section(
        self, determined_category: str, generation_result: dict[str, Any]
    ):
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
                # Genereer uitleg op basis van standaard patronen
                reasoning = self._generate_category_reasoning(determined_category)
                st.markdown(f"**Reden:** {reasoning}")

            # Toon alle scores in kleinere text
            if "category_scores" in generation_result:
                scores = generation_result["category_scores"]
                # Format scores als float met 2 decimalen
                score_text = " | ".join(
                    [f"{cat}: {score:.2f}" for cat, score in scores.items()]
                )
                st.markdown(
                    f"<small>Alle scores: {score_text}</small>", unsafe_allow_html=True
                )

        with col2:
            # Knop voor handmatige aanpassing
            if st.button("🔄 Wijzig Categorie", key="change_category"):
                SessionStateManager.set_value("show_category_selector", True)
                st.rerun()

        # Toon categorie selector als gevraagd
        if SessionStateManager.get_value("show_category_selector", False):
            self._render_category_selector(determined_category, generation_result)

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

    def _render_category_selector(
        self, current_category: str, generation_result: dict[str, Any]
    ):
        """Render categorie selector voor handmatige aanpassing."""
        st.markdown("##### 🎯 Kies Ontologische Categorie")

        # Categorie opties
        options = [
            ("type", "🏷️ Type/Klasse"),
            ("proces", "⚙️ Proces/Activiteit"),
            ("resultaat", "📊 Resultaat/Uitkomst"),
            ("exemplaar", "🔍 Exemplaar/Instantie"),
        ]

        # Zoek huidige index
        current_index = next(
            (i for i, (val, _) in enumerate(options) if val == current_category), 1
        )

        # Selectie
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
                # GEEN st.rerun() hier - we willen de regeneration preview zien!

        with col3:
            if st.button("❌ Annuleren", key="cancel_category"):
                SessionStateManager.set_value("show_category_selector", False)
                st.rerun()

    def _update_category(self, new_category: str, generation_result: dict[str, Any]):
        """
        Update de ontologische categorie via WorkflowService (SA architectuur).

        Deze methode delegeert alle business logic naar de WorkflowService
        en reageert alleen op het resultaat voor UI updates.
        """
        # Extract benodigde data voor workflow
        old_category = generation_result.get("determined_category", "proces")
        current_definition = self._extract_definition_from_result(generation_result)
        begrip = generation_result.get("begrip", "")
        saved_record = generation_result.get("saved_record")

        # Voer workflow uit via orchestration layer
        from services.workflow_service import WorkflowAction

        result = self.workflow_service.execute_category_change_workflow(
            definition_id=saved_record.id if saved_record else None,
            old_category=old_category,
            new_category=new_category,
            current_definition=current_definition,
            begrip=begrip,
            user="web_user",  # TODO: Get actual user when auth implemented
            reason="Handmatige aanpassing via UI",
        )

        # Update local state voor UI consistency
        if result.success:
            CategoryStateManager.update_generation_result_category(
                generation_result, new_category
            )

        # Toon workflow resultaat
        if result.success:
            st.success(result.message)
        else:
            st.error(result.message)
            return

        # Handel UI acties af op basis van workflow resultaat
        if result.action == WorkflowAction.SHOW_REGENERATION_PREVIEW:
            # Store category change state in generation_result voor later rendering
            generation_result["category_change_state"] = result.preview_data.get(
                "category_change_state"
            )
            # Hide category selector nu preview wordt getoond
            SessionStateManager.set_value("show_category_selector", False)
        elif result.action == WorkflowAction.SHOW_SUCCESS:
            # Geen verdere actie nodig, success message is al getoond
            pass
        elif result.action == WorkflowAction.SHOW_ERROR:
            # Error is al getoond, log voor debugging
            logger.error(f"Category change workflow error: {result.error}")

        # Action buttons alleen als er een saved_record is
        if saved_record:
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📝 Bewerk Definitie"):
                    self._edit_definition(saved_record)

            with col2:
                if st.button("👨‍💼 Submit voor Review"):
                    self._submit_for_review(saved_record)

            with col3:
                if st.button("📤 Exporteer"):
                    self._export_definition(saved_record)

    def _render_sources_section(self, generation_result, agent_result, saved_record):
        """Render sectie met gebruikte bronnen (provenance)."""
        try:
            sources = None

            # 1) Probeer uit saved_record.metadata (na opslag)
            if saved_record and getattr(saved_record, "metadata", None):
                metadata = saved_record.metadata
                if isinstance(metadata, dict):
                    sources = metadata.get("sources")

            # 2) STORY 3.1: Check direct sources attribute (preview fix)
            if sources is None and hasattr(agent_result, "sources"):
                sources = agent_result.sources

            # 3) Val terug op agent_result.metadata (legacy support)
            if sources is None and isinstance(agent_result, dict):
                meta = agent_result.get("metadata")
                if isinstance(meta, dict):
                    sources = meta.get("sources")
            elif sources is None and hasattr(agent_result, "metadata"):
                if isinstance(agent_result.metadata, dict):
                    sources = agent_result.metadata.get("sources")

            # STORY 3.1: Always show sources section with feedback
            st.markdown("#### 📚 Gebruikte Bronnen")

            if not sources:
                st.info(
                    "ℹ️ Geen externe bronnen geraadpleegd. Web lookup is uitgeschakeld of er zijn geen relevante bronnen gevonden."
                )
                return

            for idx, src in enumerate(sources[:5]):  # Toon max 5
                # Use source_label if available (Story 3.1), fallback to provider
                provider_label = src.get("source_label") or self._get_provider_label(
                    src.get("provider", "bron")
                )
                title = src.get("title") or src.get("definition") or "(zonder titel)"
                url = src.get("url") or src.get("link") or ""
                score = src.get("score") or src.get("confidence") or 0.0
                used = src.get("used_in_prompt", False)
                snippet = src.get("snippet") or src.get("context") or ""
                is_authoritative = src.get("is_authoritative", False)
                legal_meta = src.get("legal")

                with st.expander(
                    f"{idx+1}. {provider_label} — {title[:80]}", expanded=(idx == 0)
                ):
                    # Show badges
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if is_authoritative:
                            st.success("✓ Autoritatief")
                    with col2:
                        if used:
                            st.info("→ In prompt")

                    # Show juridical citation if available
                    if legal_meta and legal_meta.get("citation_text"):
                        st.markdown(
                            f"**Juridische verwijzing**: {legal_meta['citation_text']}"
                        )

                    # Show score and snippet
                    st.markdown(f"**Score**: {score:.2f}")
                    if snippet:
                        st.markdown(
                            f"**Fragment**: {snippet[:500]}{'...' if len(snippet) > 500 else ''}"
                        )
                    if url:
                        st.markdown(f"[🔗 Open bron]({url})")
        except Exception as e:
            logger.debug(f"Kon bronnen sectie niet renderen: {e}")

    def _get_provider_label(self: str) -> str:
        """Get human-friendly label for provider (local helper)."""
        labels = {
            "wikipedia": "Wikipedia NL",
            "overheid": "Overheid.nl",
            "rechtspraak": "Rechtspraak.nl",
            "wiktionary": "Wiktionary NL",
        }
        return labels.get(self, self.replace("_", " ").title())

    def _render_validation_results(self, validation_result):
        """Render validation resultaten."""
        st.markdown("#### ✅ Kwaliteitstoetsing")

        # Overall score
        score_color = (
            "green"
            if validation_result.overall_score > 0.8
            else "orange" if validation_result.overall_score > 0.6 else "red"
        )
        st.markdown(
            f"**Overall Score:** <span style='color: {score_color}'>{validation_result.overall_score:.2f}</span>",
            unsafe_allow_html=True,
        )

        # Toggle button for detailed results
        if st.button("📊 Toon/verberg gedetailleerde toetsresultaten"):
            current_state = SessionStateManager.get_value(
                "toon_detailleerde_toetsing", False
            )
            SessionStateManager.set_value(
                "toon_detailleerde_toetsing", not current_state
            )

        # Show detailed results if toggled
        if SessionStateManager.get_value("toon_detailleerde_toetsing", False):
            # Get all test results from session state
            beoordeling = SessionStateManager.get_value("beoordeling_gen", [])
            if beoordeling:
                st.markdown("### 📋 Alle Toetsregels Resultaten")
                for regel in beoordeling:
                    if "✔️" in regel:
                        st.success(regel)
                    elif "❌" in regel:
                        st.error(regel)
                    elif "🟡" in regel or "⚠️" in regel:
                        st.warning(regel)
                    else:
                        st.info(regel)
            else:
                st.warning("⚠️ Geen gedetailleerde toetsresultaten beschikbaar.")

        # Show only violations summary when collapsed
        if validation_result.violations:
            st.markdown("**Gevonden Issues (samenvatting):**")
            for violation in validation_result.violations[:5]:  # Toon max 5
                severity_emoji = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "🔶",
                    "low": "i️",
                }
                emoji = severity_emoji.get(violation.severity.value, "📋")
                st.write(f"{emoji} {violation.rule_id}: {violation.description}")
        else:
            st.success("🎉 Geen kwaliteitsissues gevonden!")

    def _use_existing_definition(self, definitie: DefinitieRecord):
        """Gebruik bestaande definitie."""
        SessionStateManager.set_value("selected_definition", definitie)
        st.success(f"✅ Definitie {definitie.id} geselecteerd voor gebruik")
        st.rerun()

    def _edit_existing_definition(self, definitie: DefinitieRecord):
        """Bewerk bestaande definitie."""
        # TODO: Navigate to edit interface
        st.info("🔄 Navigating to edit interface...")

    def _edit_definition(self, definitie: DefinitieRecord):
        """Bewerk gegenereerde definitie."""
        # TODO: Implement definition editing
        st.info("🔄 Edit functionality coming soon...")

    def _submit_for_review(self, definitie: DefinitieRecord):
        """Submit definitie voor expert review via WorkflowService."""
        try:
            # First, validate the transition via WorkflowService (business logic)
            if not self.workflow_service.can_change_status(
                current_status=definitie.status, new_status=DefinitieStatus.REVIEW.value
            ):
                st.error(
                    "❌ Deze definitie kan niet voor review worden ingediend vanuit de huidige status"
                )
                return

            # Get the prepared status changes from service
            status_changes = self.workflow_service.submit_for_review(
                definition_id=definitie.id,
                user="web_user",
                notes="Submitted via web interface",
            )

            # Apply changes via repository (data access layer)
            # TODO: In Phase 2, create a DefinitionWorkflowService that combines both
            success = self.checker.repository.change_status(
                definitie_id=definitie.id,
                new_status=DefinitieStatus.REVIEW,
                changed_by=status_changes["updated_by"],
                notes="Submitted via web interface",
            )

            if success:
                st.success("✅ Definitie ingediend voor review")
                # Log the workflow change for audit purposes
                logger.info(
                    f"Definition {definitie.id} submitted for review by {status_changes['updated_by']}"
                )
            else:
                st.error("❌ Kon status niet wijzigen")
        except ValueError as e:
            # WorkflowService throws ValueError for invalid transitions
            st.error(f"❌ Workflow fout: {e!s}")
        except Exception as e:
            st.error(f"❌ Onverwachte fout: {e!s}")
            logger.exception("Error submitting definition for review")

    def _export_definition(self, definitie: DefinitieRecord):
        """Exporteer definitie via nieuwe ExportService."""
        try:
            # Gebruik UI Components Adapter voor clean export
            from ui.components_adapter import get_ui_adapter

            adapter = get_ui_adapter()

            # Offer multiple formats
            col1, col2 = st.columns([3, 1])

            with col1:
                export_format = st.selectbox(
                    "Export formaat:",
                    ["txt", "json", "csv"],
                    format_func=lambda x: x.upper(),
                    key=f"export_format_{definitie.id}",
                )

            with col2:
                if st.button("📤 Exporteer", key=f"export_btn_{definitie.id}"):
                    # Set current definition ID in session state
                    SessionStateManager.set_value("current_definition_id", definitie.id)

                    # Use adapter to export
                    success = adapter.export_definition(format=export_format)

                    if success:
                        st.balloons()

        except Exception as e:
            st.error(f"❌ Export mislukt: {e!s}")
            logger.exception(f"Export failed for definition {definitie.id}")

    def _render_voorbeelden_section(self, voorbeelden: dict[str, list[str]]):
        """Render sectie met gegenereerde voorbeelden."""
        st.markdown("#### 📚 Gegenereerde Content")

        # Voorbeeldzinnen
        if voorbeelden.get("sentence"):
            with st.expander("🔤 Voorbeeldzinnen", expanded=True):
                for voorbeeld in voorbeelden["sentence"]:
                    st.write(f"• {voorbeeld}")

        # Praktijkvoorbeelden
        if voorbeelden.get("practical"):
            with st.expander("💼 Praktijkvoorbeelden", expanded=True):
                for voorbeeld in voorbeelden["practical"]:
                    st.info(voorbeeld)

        # Tegenvoorbeelden
        if voorbeelden.get("counter"):
            with st.expander("❌ Tegenvoorbeelden (wat het NIET is)", expanded=False):
                for voorbeeld in voorbeelden["counter"]:
                    st.warning(voorbeeld)

        # Synoniemen met voorkeursterm selectie
        if voorbeelden.get("synonyms"):
            with st.expander("🔄 Synoniemen", expanded=False):
                synoniemen_lijst = voorbeelden["synonyms"]

                # Toon synoniemen verticaal
                for syn in synoniemen_lijst:
                    st.write(f"• {syn}")

                # Voorkeursterm selectie
                if len(synoniemen_lijst) > 0:
                    st.markdown("---")

                    # Haal het oorspronkelijke begrip op uit de session state
                    oorspronkelijk_begrip = SessionStateManager.get_value("begrip", "")

                    # Maak opties lijst met oorspronkelijke begrip als eerste optie
                    voorkeursterm_opties = ["(geen voorkeursterm)"]
                    if (
                        oorspronkelijk_begrip
                        and oorspronkelijk_begrip not in synoniemen_lijst
                    ):
                        voorkeursterm_opties.append(oorspronkelijk_begrip)
                    voorkeursterm_opties.extend(synoniemen_lijst)

                    voorkeursterm = st.selectbox(
                        "Selecteer voorkeursterm:",
                        options=voorkeursterm_opties,
                        key="voorkeursterm_selectie",
                    )

                    if voorkeursterm != "(geen voorkeursterm)":
                        SessionStateManager.set_value("voorkeursterm", voorkeursterm)
                        st.info(f"✅ Voorkeursterm: **{voorkeursterm}**")

        # Antoniemen
        if voorbeelden.get("antonyms"):
            with st.expander("↔️ Antoniemen", expanded=False):
                # Toon antoniemen verticaal
                for ant in voorbeelden["antonyms"]:
                    st.write(f"• {ant}")

        # Toelichting
        if voorbeelden.get("explanation"):
            with st.expander("💡 Toelichting", expanded=True):
                st.write(
                    voorbeelden["explanation"][0]
                    if isinstance(voorbeelden["explanation"], list)
                    else voorbeelden["explanation"]
                )

    def _trigger_regeneration_with_category(
        self,
        begrip: str,
        new_category: str,
        old_category: str,
        saved_record: DefinitieRecord,
    ):
        """Trigger nieuwe definitie generatie met aangepaste categorie."""
        st.warning(
            f"🔄 Nieuwe definitie genereren voor categorie: {self.category_service.get_category_display_name(new_category)}"
        )

        # Set regeneration context in service layer (conform GVI architectuur)
        self.regeneration_service.set_regeneration_context(
            begrip=begrip,
            old_category=old_category,
            new_category=new_category,
            previous_definition=saved_record.definitie if saved_record else None,
            reason="Gebruiker heeft categorie handmatig aangepast",
        )

        # Ook in session voor UI navigation (temporary bridge)
        SessionStateManager.set_value("regeneration_active", True)
        SessionStateManager.set_value("regeneration_begrip", begrip)
        SessionStateManager.set_value("regeneration_category", new_category)

        # Informeer gebruiker
        st.info(
            f"""
        📝 **Regeneratie geactiveerd**:
        - Ga naar het hoofdscherm
        - Het begrip '{begrip}' wordt automatisch ingevuld
        - Categorie '{new_category}' wordt gebruikt
        - De generator zal rekening houden met de nieuwe categorie
        """
        )

        # Show navigation button
        if st.button("🏠 Ga naar Generator", key="nav_to_generator"):
            st.switch_page("app.py")

    def _render_regeneration_preview(
        self,
        begrip: str,
        current_definition: str,
        old_category: str,
        new_category: str,
        generation_result: dict[str, Any],
        saved_record: Any,
    ):
        """Render enhanced preview voor regeneration met betere UX."""
        st.markdown("---")
        st.markdown("### 🔄 Definitie Regeneratie Preview")

        # Category change overview
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("**Oude Categorie:**")
            st.markdown(f"🏷️ `{self._get_category_display_name(old_category)}`")

        with col2:
            st.markdown("**➡️**")

        with col3:
            st.markdown("**Nieuwe Categorie:**")
            st.markdown(f"🎯 `{self._get_category_display_name(new_category)}`")

        # Current definition preview
        st.markdown("**Huidige Definitie:**")
        st.info(
            current_definition[:200] + ("..." if len(current_definition) > 200 else "")
        )

        # Impact preview - gebruik workflow service analyse
        impact_analysis = self.workflow_service._analyze_category_change_impact(
            old_category, new_category
        )

        st.markdown("**Verwachte Impact:**")
        for impact in impact_analysis:
            st.markdown(f"• {impact}")

        # Enhanced action options
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
                # Set regeneration context en navigate
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

    def _get_category_display_name(self, category: str) -> str:
        """Get user-friendly display name voor categorie."""
        category_names = {
            "type": "🏷️ Type/Klasse",
            "proces": "⚙️ Proces/Activiteit",
            "resultaat": "📊 Resultaat/Uitkomst",
            "exemplaar": "🔍 Exemplaar/Instantie",
            "ENT": "🏷️ Entiteit",
            "ACT": "⚙️ Activiteit",
            "REL": "🔗 Relatie",
            "ATT": "📋 Attribuut",
            "AUT": "⚖️ Autorisatie",
            "STA": "📊 Status",
            "OTH": "❓ Overig",
        }
        return category_names.get(category, f"❓ {category}")

    def _analyze_regeneration_impact(
        self, old_category: str, new_category: str
    ) -> list[str]:
        """Analyseer verwachte impact van category change."""
        impacts = []

        # Category-specific impact analysis
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

        # General impacts
        impacts.extend(
            [
                "🎯 Terminologie wordt aangepast aan nieuwe categorie",
                "✅ Kwaliteitstoetsing wordt opnieuw uitgevoerd",
                "📄 Nieuwe definitie krijgt eigen versiehistorie",
            ]
        )

        return impacts

    def _direct_regenerate_definition(
        self,
        begrip: str,
        new_category: str,
        old_category: str,
        saved_record: Any,
        generation_result: dict[str, Any],
    ):
        """Voer directe definitie regeneration uit zonder navigation."""
        st.markdown("---")
        st.markdown("### 🚀 Directe Regeneration Gestart")

        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Set regeneration context
            status_text.text("🔄 Setting regeneration context...")
            progress_bar.progress(20)

            self.regeneration_service.set_regeneration_context(
                begrip=begrip,
                old_category=old_category,
                new_category=new_category,
                previous_definition=saved_record.definitie,
                reason="Direct regeneration na category wijziging",
            )

            # Step 2: Get definition service
            status_text.text("⚙️ Initializing definition service...")
            progress_bar.progress(40)

            # Import here to avoid circular imports
            from services import get_definition_service

            definition_service = get_definition_service()

            # Step 3: Prepare generation context
            status_text.text("📝 Preparing generation context...")
            progress_bar.progress(60)

            # Extract context from original generation result
            context_dict = self._extract_context_from_generation_result(
                generation_result
            )

            # Step 4: Generate new definition
            status_text.text("🤖 Generating new definition...")
            progress_bar.progress(80)

            from domain.ontological_categories import OntologischeCategorie

            service_result = definition_service.generate_definition(
                begrip=begrip,
                context_dict=context_dict,
                organisatie=generation_result.get("organisatie", ""),
                categorie=OntologischeCategorie(new_category.lower()),
                regeneration_context=self.regeneration_service.get_active_context(),
            )

            # Step 5: Update UI with results
            status_text.text("✅ Processing results...")
            progress_bar.progress(100)

            # Store new results in session state
            from datetime import datetime

            from ui.session_state import SessionStateManager

            SessionStateManager.set_value(
                "last_generation_result",
                {
                    "begrip": begrip,
                    "check_result": None,
                    "agent_result": service_result,
                    "saved_record": None,  # Will be created if user saves
                    "determined_category": new_category,
                    "category_reasoning": f"Direct regeneration: {old_category} → {new_category}",
                    "category_scores": {
                        new_category: 1.0
                    },  # Perfect score for manual selection
                    "timestamp": datetime.now(UTC),
                    "regeneration_used": True,
                    "direct_regeneration": True,
                },
            )

            # Clear regeneration context
            self.regeneration_service.clear_context()

            # Show success and results
            progress_bar.empty()
            status_text.empty()

            st.success("🎉 Nieuwe definitie succesvol gegenereerd!")

            # Show comparison
            self._render_definition_comparison(
                old_definition=saved_record.definitie,
                new_result=service_result,
                old_category=old_category,
                new_category=new_category,
            )

            # Auto-navigation option
            st.info("💡 De nieuwe definitie staat klaar in het Generator tabblad")
            if st.button("👀 Bekijk Resultaat", key="view_new_result"):
                st.switch_page("app.py")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()

            st.error(f"❌ Regeneration mislukt: {e}")
            st.info("Probeer de handmatige aanpassing optie.")

            # Clear any partial context
            self.regeneration_service.clear_context()

    def _extract_context_from_generation_result(
        self, generation_result: dict[str, Any]
    ) -> dict:
        """Extract context information from previous generation result."""
        # Try to get context from various sources in the generation result
        context_dict = {"organisatorisch": [], "juridisch": [], "wettelijk": []}

        # Extract from stored context if available
        if "document_context" in generation_result:
            doc_context = generation_result["document_context"]
            if isinstance(doc_context, dict):
                for key in context_dict:
                    if key in doc_context:
                        context_dict[key] = doc_context[key]

        # Fallback: extract from session state
        from ui.session_state import SessionStateManager

        for context_type in context_dict:
            session_value = SessionStateManager.get_value(f"{context_type}_context", [])
            if session_value and not context_dict[context_type]:
                context_dict[context_type] = session_value

        return context_dict

    def _render_definition_comparison(
        self,
        old_definition: str,
        new_result: dict,
        old_category: str,
        new_category: str,
    ):
        """Render comparison tussen oude en nieuwe definitie."""
        st.markdown("---")
        st.markdown("### 📊 Definitie Vergelijking")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"**Oude Definitie** ({self._get_category_display_name(old_category)}):"
            )
            st.info(old_definition)

        with col2:
            st.markdown(
                f"**Nieuwe Definitie** ({self._get_category_display_name(new_category)}):"
            )

            # Extract new definition from result
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

        # Quality comparison if available
        if isinstance(new_result, dict) and "validation_score" in new_result:
            new_score = new_result["validation_score"]
            st.markdown(f"**Kwaliteitsscore nieuwe definitie:** {new_score:.2f}")

    def _extract_definition_from_result(self, generation_result: dict[str, Any]) -> str:
        """Extract definitie uit generation result, ongeacht format."""
        # Check voor agent_result
        agent_result = generation_result.get("agent_result")
        if not agent_result:
            return ""

        # Check if it's a dict (new service) or object (legacy)
        if isinstance(agent_result, dict):
            # New service format
            return agent_result.get(
                "definitie_gecorrigeerd", agent_result.get("definitie", "")
            )
        # Legacy format
        return getattr(agent_result, "final_definitie", "")

    def _clear_results(self):
        """Wis alle resultaten."""
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")

    def _show_settings_modal(self):
        """Toon instellingen modal."""
        # TODO: Implement settings modal
        st.info("⚙️ Settings modal coming soon...")

    def _render_category_change_preview(
        self,
        category_change_state,
        generation_result: dict[str, Any],
        saved_record: Any,
    ):
        """Render category change preview via DataAggregationService state."""
        st.markdown("---")
        st.markdown("### 🔄 Definitie Regeneratie Preview")

        # Success message
        if category_change_state.success_message:
            st.success(category_change_state.success_message)

        # Category change overview
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("**Oude Categorie:**")
            st.markdown(
                f"🏷️ `{self._get_category_display_name(category_change_state.old_category)}`"
            )

        with col2:
            st.markdown("**➡️**")

        with col3:
            st.markdown("**Nieuwe Categorie:**")
            st.markdown(
                f"🎯 `{self._get_category_display_name(category_change_state.new_category)}`"
            )

        # Current definition preview
        st.markdown("**Huidige Definitie:**")
        definition_preview = category_change_state.current_definition
        st.info(
            definition_preview[:200] + ("..." if len(definition_preview) > 200 else "")
        )

        # Impact preview
        if category_change_state.impact_analysis:
            st.markdown("**Verwachte Impact:**")
            for impact in category_change_state.impact_analysis:
                st.markdown(f"• {impact}")

        # Enhanced action options
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
                # Clear the category change state
                generation_result.pop("category_change_state", None)
                st.success("✅ Definitie behouden met nieuwe categorie!")
                st.rerun()
