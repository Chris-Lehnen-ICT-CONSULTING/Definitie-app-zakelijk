"""
Definition Generator Tab - Main AI definition generation interface.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from ui.session_state import SessionStateManager
from integration.definitie_checker import DefinitieChecker, CheckAction
from generation.definitie_generator import OntologischeCategorie
from database.definitie_repository import DefinitieRecord, DefinitieStatus


class DefinitionGeneratorTab:
    """Tab voor AI definitie generatie met duplicate checking."""
    
    def __init__(self, checker: DefinitieChecker):
        """Initialiseer generator tab."""
        self.checker = checker
        
    def render(self):
        """Render definitie generatie tab."""
        # Input sectie
        self._render_input_section()
        
        # Generation controls
        self._render_generation_controls()
        
        # Results sectie
        self._render_results_section()
    
    def _render_input_section(self):
        """Render input sectie voor begrip en categorie."""
        st.markdown("### 📝 Definitie Aanvraag")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Begrip input
            begrip = st.text_input(
                "Te definiëren begrip",
                value=SessionStateManager.get_value("begrip", ""),
                placeholder="Voer het begrip in dat gedefinieerd moet worden...",
                help="Het centrale begrip waarvoor een definitie gegenereerd wordt"
            )
            SessionStateManager.set_value("begrip", begrip)
        
        with col2:
            # Ontologische categorie
            categorie_options = {
                "Type/Soort": "type",
                "Proces/Activiteit": "proces", 
                "Resultaat/Uitkomst": "resultaat",
                "Exemplaar/Instantie": "exemplaar"
            }
            
            selected_cat = st.selectbox(
                "Ontologische categorie",
                options=list(categorie_options.keys()),
                index=0,
                help="Bepaalt het type definitie dat gegenereerd wordt"
            )
            
            categorie = categorie_options[selected_cat]
            SessionStateManager.set_value("categorie", categorie)
        
        # Advanced options
        with st.expander("🔧 Geavanceerde Opties", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                max_iterations = st.slider(
                    "Maximum iteraties", 
                    min_value=1, max_value=5, value=3,
                    help="Aantal feedback loops voor verbetering"
                )
                
                force_generate = st.checkbox(
                    "Forceer nieuwe generatie",
                    help="Genereer altijd nieuw, zelfs bij duplicates"
                )
            
            with col2:
                acceptance_threshold = st.slider(
                    "Kwaliteitsdrempel",
                    min_value=0.5, max_value=1.0, value=0.8, step=0.05,
                    help="Minimum kwaliteitsscore voor acceptatie"
                )
                
                include_examples = st.checkbox(
                    "Genereer voorbeelden",
                    value=True,
                    help="Voeg praktische voorbeelden toe"
                )
            
            SessionStateManager.set_value("generation_options", {
                "max_iterations": max_iterations,
                "force_generate": force_generate,
                "acceptance_threshold": acceptance_threshold,
                "include_examples": include_examples
            })
    
    def _render_generation_controls(self):
        """Render generation control buttons."""
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Main generation button
            generate_button = st.button(
                "🚀 Genereer Definitie",
                type="primary",
                help="Start AI definitie generatie proces"
            )
        
        with col2:
            # Check duplicates button
            check_button = st.button(
                "🔍 Check Duplicates",
                help="Controleer op bestaande definities"
            )
        
        with col3:
            # Clear results button
            if st.button("🗑️ Wis Resultaten"):
                self._clear_results()
                st.rerun()
        
        with col4:
            # Settings button
            if st.button("⚙️ Instellingen"):
                self._show_settings_modal()
        
        # Handle button actions
        if check_button:
            self._handle_duplicate_check()
        
        if generate_button:
            self._handle_definition_generation()
    
    def _render_results_section(self):
        """Render resultaten van generatie of duplicate check."""
        # Check voor resultaten in session state
        check_result = SessionStateManager.get_value("last_check_result")
        generation_result = SessionStateManager.get_value("last_generation_result")
        
        if check_result:
            self._render_duplicate_check_results(check_result)
        
        if generation_result:
            self._render_generation_results(generation_result)
    
    def _handle_duplicate_check(self):
        """Handle duplicate check actie."""
        begrip = SessionStateManager.get_value("begrip", "").strip()
        if not begrip:
            st.error("❌ Voer eerst een begrip in")
            return
        
        # Get context
        global_context = SessionStateManager.get_value("global_context", {})
        categorie = SessionStateManager.get_value("categorie", "type")
        
        org_context = global_context.get("organisatorische_context", [])
        jur_context = global_context.get("juridische_context", [])
        
        if not org_context:
            st.error("❌ Selecteer eerst een organisatorische context")
            return
        
        with st.spinner("🔍 Controleren op duplicates..."):
            try:
                check_result = self.checker.check_before_generation(
                    begrip=begrip,
                    organisatorische_context=org_context[0] if org_context else "",
                    juridische_context=jur_context[0] if jur_context else "",
                    categorie=OntologischeCategorie(categorie)
                )
                
                SessionStateManager.set_value("last_check_result", check_result)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Fout bij duplicate check: {str(e)}")
    
    def _handle_definition_generation(self):
        """Handle definitie generatie actie."""
        begrip = SessionStateManager.get_value("begrip", "").strip()
        if not begrip:
            st.error("❌ Voer eerst een begrip in")
            return
        
        # Get context en opties
        global_context = SessionStateManager.get_value("global_context", {})
        categorie = SessionStateManager.get_value("categorie", "type")
        options = SessionStateManager.get_value("generation_options", {})
        
        org_context = global_context.get("organisatorische_context", [])
        jur_context = global_context.get("juridische_context", [])
        
        if not org_context:
            st.error("❌ Selecteer eerst een organisatorische context")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔍 Controleren op duplicates...")
            progress_bar.progress(0.2)
            
            # Voer complete workflow uit
            check_result, agent_result, saved_record = self.checker.generate_with_check(
                begrip=begrip,
                organisatorische_context=org_context[0] if org_context else "",
                juridische_context=jur_context[0] if jur_context else "",
                categorie=OntologischeCategorie(categorie),
                force_generate=options.get("force_generate", False),
                created_by=global_context.get("voorsteller", "web_user")
            )
            
            progress_bar.progress(1.0)
            status_text.text("✅ Generatie voltooid!")
            
            # Store results
            SessionStateManager.set_value("last_check_result", check_result)
            SessionStateManager.set_value("last_generation_result", {
                "agent_result": agent_result,
                "saved_record": saved_record,
                "timestamp": datetime.now()
            })
            
            time.sleep(1)  # Brief pause for user feedback
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fout bij generatie: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    
    def _render_duplicate_check_results(self, check_result):
        """Render resultaten van duplicate check."""
        st.markdown("### 🔍 Duplicate Check Resultaten")
        
        # Main result
        if check_result.action == CheckAction.PROCEED:
            st.success(f"✅ {check_result.message}")
        elif check_result.action == CheckAction.USE_EXISTING:
            st.warning(f"⚠️ {check_result.message}")
        else:
            st.info(f"ℹ️ {check_result.message}")
        
        # Show confidence
        confidence_color = "green" if check_result.confidence > 0.8 else "orange" if check_result.confidence > 0.5 else "red"
        st.markdown(f"**Vertrouwen:** <span style='color: {confidence_color}'>{check_result.confidence:.1%}</span>", 
                   unsafe_allow_html=True)
        
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
                st.markdown(f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d') if definitie.created_at else 'Onbekend'}")
            
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
            
            with st.expander(f"Match {i+1}: {definitie.begrip} (Score: {score:.2f})", expanded=i==0):
                st.markdown(f"**Definitie:** {definitie.definitie}")
                st.markdown(f"**Context:** {definitie.organisatorische_context}")
                st.markdown(f"**Redenen:** {', '.join(reasons)}")
                
                if st.button(f"Gebruik deze definitie", key=f"dup_use_{definitie.id}"):
                    self._use_existing_definition(definitie)
    
    def _render_generation_results(self, generation_result):
        """Render resultaten van definitie generatie."""
        st.markdown("### 🚀 Generatie Resultaten")
        
        agent_result = generation_result.get("agent_result")
        saved_record = generation_result.get("saved_record")
        timestamp = generation_result.get("timestamp")
        
        if agent_result:
            # Success indicator
            if agent_result.success:
                st.success(f"✅ Definitie succesvol gegenereerd! (Score: {agent_result.final_score:.2f})")
            else:
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {agent_result.reason}")
            
            # Generated definition
            st.markdown("#### 📝 Gegenereerde Definitie")
            st.info(agent_result.final_definitie)
            
            # Generation details
            with st.expander("📊 Generatie Details", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Iteraties", agent_result.iteration_count)
                    st.metric("Finale Score", f"{agent_result.final_score:.2f}")
                
                with col2:
                    st.metric("Verwerkingstijd", f"{agent_result.total_processing_time:.1f}s")
                    st.metric("Succes", "Ja" if agent_result.success else "Nee")
                
                with col3:
                    if agent_result.best_iteration:
                        violations = len(agent_result.best_iteration.validation_result.violations)
                        st.metric("Violations", violations)
                
                # Iteration history
                if len(agent_result.iterations) > 1:
                    st.markdown("**Iteratie Geschiedenis:**")
                    for iteration in agent_result.iterations:
                        score = iteration.validation_result.overall_score
                        st.write(f"Iteratie {iteration.iteration_number}: Score {score:.2f}")
            
            # Validation results
            if agent_result.best_iteration:
                self._render_validation_results(agent_result.best_iteration.validation_result)
        
        # Saved record info
        if saved_record:
            st.markdown("#### 💾 Database Record")
            st.info(f"Definitie opgeslagen met ID: {saved_record.id} (Status: {saved_record.status})")
            
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
        score_color = "green" if validation_result.overall_score > 0.8 else "orange" if validation_result.overall_score > 0.6 else "red"
        st.markdown(f"**Overall Score:** <span style='color: {score_color}'>{validation_result.overall_score:.2f}</span>", 
                   unsafe_allow_html=True)
        
        # Violations
        if validation_result.violations:
            st.markdown("**Gevonden Issues:**")
            for violation in validation_result.violations[:5]:  # Toon max 5
                severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "🔶", "low": "ℹ️"}
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
                "Submitted via web interface"
            )
            
            if success:
                st.success("✅ Definitie ingediend voor review")
            else:
                st.error("❌ Kon status niet wijzigen")
        except Exception as e:
            st.error(f"❌ Fout: {str(e)}")
    
    def _export_definition(self, definitie: DefinitieRecord):
        """Exporteer definitie."""
        # TODO: Implement export functionality
        st.info("📤 Export functionality coming soon...")
    
    def _clear_results(self):
        """Wis alle resultaten."""
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")
    
    def _show_settings_modal(self):
        """Toon instellingen modal."""
        # TODO: Implement settings modal
        st.info("⚙️ Settings modal coming soon...")