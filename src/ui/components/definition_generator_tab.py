"""
Definition Generator Tab - Main AI definition generation interface.
"""

import logging
from typing import Any

import streamlit as st
from database.definitie_repository import DefinitieRecord, DefinitieStatus
from integration.definitie_checker import CheckAction, DefinitieChecker
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class DefinitionGeneratorTab:
    """Tab voor AI definitie generatie met duplicate checking."""

    def __init__(self, checker: DefinitieChecker):
        """Initialiseer generator tab."""
        self.checker = checker

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

        if agent_result:
            # Check if it's a dict (new service) or object (legacy)
            is_dict = isinstance(agent_result, dict)

            # Success indicator
            if (is_dict and agent_result.get("success")) or (
                not is_dict
                and hasattr(agent_result, "success")
                and agent_result.success
            ):
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
            st.info(agent_result.final_definitie)

            # Generation details
            with st.expander("📊 Generatie Details", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    if agent_result.iteration_count > 1:
                        st.metric("Iteraties", agent_result.iteration_count)
                    st.metric("Finale Score", f"{agent_result.final_score:.2f}")

                with col2:
                    st.metric(
                        "Verwerkingstijd", f"{agent_result.total_processing_time:.1f}s"
                    )
                    st.metric("Succes", "Ja" if agent_result.success else "Nee")

                with col3:
                    if agent_result.best_iteration:
                        violations = len(
                            agent_result.best_iteration.validation_result.violations
                        )
                        st.metric("Violations", violations)

                # Iteration history
                if len(agent_result.iterations) > 1:
                    st.markdown("**Iteratie Geschiedenis:**")
                    for iteration in agent_result.iterations:
                        score = iteration.validation_result.overall_score
                        st.write(
                            f"Iteratie {iteration.iteration_number}: Score {score:.2f}"
                        )

            # Validation results
            if agent_result.best_iteration:
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
                self._update_category(new_category, generation_result)
                st.success(f"Categorie gewijzigd naar: {selected_option[1]}")
                SessionStateManager.set_value("show_category_selector", False)
                st.rerun()

        with col3:
            if st.button("❌ Annuleren", key="cancel_category"):
                SessionStateManager.set_value("show_category_selector", False)
                st.rerun()

    def _update_category(self, new_category: str, generation_result: dict[str, Any]):
        """Update de ontologische categorie in de sessie en database."""
        # Update generation result
        generation_result["determined_category"] = new_category
        SessionStateManager.set_value("last_generation_result", generation_result)

        # Update database record als deze bestaat
        saved_record = generation_result.get("saved_record")
        if saved_record:
            try:
                # Update record in database
                saved_record.categorie = new_category
                from database.definitie_repository import get_definitie_repository

                repo = get_definitie_repository()
                repo.update_definitie(saved_record)
                st.success("Categorie bijgewerkt in database")
            except Exception as e:
                st.error(f"Fout bij bijwerken database: {e}")

            # Action buttons
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
        """Submit definitie voor expert review."""
        try:
            success = self.checker.repository.change_status(
                definitie.id,
                DefinitieStatus.REVIEW,
                "web_user",
                "Submitted via web interface",
            )

            if success:
                st.success("✅ Definitie ingediend voor review")
            else:
                st.error("❌ Kon status niet wijzigen")
        except Exception as e:
            st.error(f"❌ Fout: {e!s}")

    def _export_definition(self, definitie: DefinitieRecord):
        """Exporteer definitie naar TXT bestand."""
        try:
            import os

            from export.export_txt import exporteer_naar_txt

            # Bereid gegevens voor voor export
            export_data = {
                "begrip": definitie.begrip,
                "definitie_gecorrigeerd": definitie.definitie,
                "definitie_origineel": definitie.definitie,  # TODO: originele bewaren
                "metadata": {
                    "organisatorische_context": definitie.organisatorische_context,
                    "juridische_context": definitie.juridische_context,
                    "categorie": definitie.categorie,
                    "datum_voorstel": definitie.created_at,
                    "voorgesteld_door": definitie.created_by or "",
                    "ketenpartners": SessionStateManager.get_value("ketenpartners", []),
                },
                "context_dict": {
                    "organisatorisch": (
                        [definitie.organisatorische_context]
                        if definitie.organisatorische_context
                        else []
                    ),
                    "juridisch": (
                        [definitie.juridische_context]
                        if definitie.juridische_context
                        else []
                    ),
                    "wettelijk": SessionStateManager.get_value("wet_basis", []),
                },
                "toetsresultaten": {
                    "score": definitie.validation_score or 0.0,
                    "resultaten": SessionStateManager.get_value("beoordeling_gen", []),
                },
                "bronnen": SessionStateManager.get_value("bronnen", []),
                # Voorbeelden uit session state
                "voorbeeld_zinnen": SessionStateManager.get_value(
                    "voorbeeld_zinnen", []
                ),
                "praktijkvoorbeelden": SessionStateManager.get_value(
                    "praktijkvoorbeelden", []
                ),
                "tegenvoorbeelden": SessionStateManager.get_value(
                    "tegenvoorbeelden", []
                ),
                "toelichting": SessionStateManager.get_value("toelichting", ""),
                "synoniemen": SessionStateManager.get_value("synoniemen", ""),
                "voorkeursterm": SessionStateManager.get_value("voorkeursterm", ""),
                "antoniemen": SessionStateManager.get_value("antoniemen", ""),
            }

            # Zorg dat export directory bestaat
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            # Exporteer naar TXT
            bestandspad = exporteer_naar_txt(export_data)

            # Lees bestand voor download
            with open(bestandspad, encoding="utf-8") as f:
                txt_content = f.read()

            # Bied download aan
            bestandsnaam = os.path.basename(bestandspad)
            st.download_button(
                label="📥 Download TXT Export",
                data=txt_content,
                file_name=bestandsnaam,
                mime="text/plain",
            )

            st.success(f"✅ Export succesvol: {bestandsnaam}")

        except Exception as e:
            st.error(f"❌ Export mislukt: {e!s}")
            import traceback

            st.code(traceback.format_exc())

    def _render_voorbeelden_section(self, voorbeelden: dict[str, list[str]]):
        """Render sectie met gegenereerde voorbeelden."""
        st.markdown("#### 📚 Gegenereerde Content")

        # Voorbeeldzinnen
        if voorbeelden.get("sentence"):
            with st.expander("🔤 Voorbeeldzinnen", expanded=True):
                for i, voorbeeld in enumerate(voorbeelden["sentence"], 1):
                    st.write(f"{i}. {voorbeeld}")

        # Praktijkvoorbeelden
        if voorbeelden.get("practical"):
            with st.expander("💼 Praktijkvoorbeelden", expanded=True):
                for i, voorbeeld in enumerate(voorbeelden["practical"], 1):
                    st.info(voorbeeld)

        # Tegenvoorbeelden
        if voorbeelden.get("counter"):
            with st.expander("❌ Tegenvoorbeelden (wat het NIET is)", expanded=False):
                for i, voorbeeld in enumerate(voorbeelden["counter"], 1):
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

    def _clear_results(self):
        """Wis alle resultaten."""
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")

    def _show_settings_modal(self):
        """Toon instellingen modal."""
        # TODO: Implement settings modal
        st.info("⚙️ Settings modal coming soon...")
