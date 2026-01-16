"""
# ruff: noqa: PLR0912, PLR0915, SIM102, RUF001, PLC0206
Definition Generator Tab - Main AI definition generation interface.

DEF-266 Phase 4: Refactored to use extracted renderers for validation,
category, and voorbeelden. Main tab now acts as orchestrator (~1000 LOC target).
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord

from integration.definitie_checker import DefinitieChecker
from services.category_service import CategoryService
from services.workflow_service import WorkflowService
from ui.components.category_renderer import CategoryRenderer
from ui.components.duplicate_check_renderer import DuplicateCheckRenderer
from ui.components.sources_renderer import SourcesRenderer
from ui.components.validation_renderer import ValidationRenderer
from ui.components.voorbeelden_renderer import VoorbeeldenRenderer
from ui.helpers.context_helpers import has_min_one_context
from ui.session_state import SessionStateManager
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_dict, ensure_string

logger = logging.getLogger(__name__)


class DefinitionGeneratorTab:
    """Tab voor AI definitie generatie met duplicate checking.

    DEF-266: Refactored to delegate rendering to specialized components:
    - ValidationRenderer: validation results display
    - CategoryRenderer: ontological/UFO category selection
    - VoorbeeldenRenderer: examples display and persistence
    - SourcesRenderer: web sources and provenance
    - DuplicateCheckRenderer: duplicate check results
    """

    def __init__(self, checker: DefinitieChecker):
        """Initialiseer generator tab met renderers."""
        # DEF-175: Lazy import to avoid database layer dependency at module level
        from database.definitie_repository import get_definitie_repository

        self.checker = checker
        self.category_service = CategoryService(get_definitie_repository())
        self.workflow_service = WorkflowService()

        # DEF-266: Extracted renderers
        self.duplicate_renderer = DuplicateCheckRenderer()
        self.sources_renderer = SourcesRenderer()
        self.validation_renderer = ValidationRenderer()
        self.category_renderer = CategoryRenderer()
        self.voorbeelden_renderer = VoorbeeldenRenderer()

    def render(self):
        """Render definitie generatie tab."""
        st.info(
            "💡 Gebruik de hoofdknoppen boven de tabs om definities te genereren. Resultaten worden hier getoond."
        )
        self._render_results_section()

    def _render_results_section(self):
        """Render resultaten van generatie of duplicate check."""
        check_result = SessionStateManager.get_value("last_check_result")
        generation_result = SessionStateManager.get_value("last_generation_result")

        # Vroegtijdige guard: minsténs 1 context vereist
        try:
            if not has_min_one_context():
                st.warning(
                    "Minstens één context is vereist (organisatorisch of juridisch of wettelijk) om te genereren of op te slaan."
                )
        except Exception as e:
            logger.error(f"Context validation check failed: {e}", exc_info=True)
            st.error("⚠️ Fout bij context validatie - controleer invoer")

        if check_result:
            self.duplicate_renderer.render_check_results(check_result)

        if generation_result:
            self._render_generation_results(generation_result)

    def _render_generation_results(self, generation_result: dict[str, Any]):
        """Render resultaten van definitie generatie."""
        st.markdown("### 🚀 Generatie Resultaten")

        agent_result = safe_dict_get(generation_result, "agent_result")
        saved_record = safe_dict_get(generation_result, "saved_record")
        saved_definition_id = safe_dict_get(generation_result, "saved_definition_id")
        determined_category = safe_dict_get(generation_result, "determined_category")

        self._log_generation_result_debug(generation_result, agent_result)

        if not agent_result:
            return

        # Show success/warning indicator
        self._render_generation_status(agent_result)

        # DEF-215: Check for degraded validation mode
        validation_metadata = safe_dict_get(agent_result, "validation_metadata", {})
        system_info = safe_dict_get(validation_metadata, "system", {})
        if safe_dict_get(system_info, "degraded_mode", False):
            self._render_degraded_mode_warning(system_info)

        # EPIC-018: Badge/indicator voor gebruikte documentcontext
        self._render_document_context_badge(generation_result)

        # Cache definition ID for Expert/Edit tabs
        self._cache_definition_id(saved_definition_id, saved_record)

        # Ontologische categorie sectie - delegated to CategoryRenderer
        if determined_category:
            self.category_renderer.render_ontological_category_section(
                determined_category, generation_result, saved_record
            )

        # UFO-categorie selector - delegated to CategoryRenderer
        try:
            self.category_renderer.render_ufo_category_selector(generation_result)
        except Exception:
            logger.debug(
                "UFO-categorie selector render skipped due to error", exc_info=True
            )

        # Generated definition
        self._render_definition_section(agent_result, generation_result)

        # Bronverantwoording - delegated to SourcesRenderer
        self.sources_renderer.render_sources_section(
            generation_result, agent_result, saved_record
        )

        # Synonym Review UI
        self._render_synonym_review(generation_result)

        # Generation details expander
        self._render_generation_details(agent_result)

        # Validation results - delegated to ValidationRenderer
        self._render_validation_section(agent_result)

        # Voorbeelden sectie - delegated to VoorbeeldenRenderer
        self._render_voorbeelden_section(
            agent_result, generation_result, saved_record, saved_definition_id
        )

        # Prompt Debug Section
        self._render_prompt_debug_section(agent_result, generation_result, saved_record)

        # Saved record info
        if saved_record:
            self._render_saved_record_info(saved_record)

    # ============ Orchestration methods (delegate to renderers) ============

    def _render_document_context_badge(self, generation_result: dict[str, Any]) -> None:
        """Render document context badge if documents were used."""
        try:
            doc_ctx = safe_dict_get(generation_result, "document_context")
            if (
                isinstance(doc_ctx, dict)
                and int(doc_ctx.get("document_count", 0) or 0) > 0
            ):
                st.info(
                    f"📄 Documentcontext gebruikt: {int(doc_ctx['document_count'])} document(en)"
                )
        except Exception as e:
            logger.warning(f"Failed to render document context badge: {e}")

    def _cache_definition_id(self, saved_definition_id: Any, saved_record: Any) -> None:
        """Cache definition ID for Expert/Edit tabs."""
        target_id = None
        if isinstance(saved_definition_id, int) and saved_definition_id > 0:
            target_id = saved_definition_id
        elif saved_record and getattr(saved_record, "id", None):
            target_id = int(saved_record.id)

        if target_id:
            try:
                SessionStateManager.set_value(
                    "selected_review_definition_id", target_id
                )
                SessionStateManager.set_value("editing_definition_id", target_id)
            except Exception as e:
                logger.warning(
                    f"Failed to cache definition ID for Expert/Edit tabs: {e}"
                )

    def _render_definition_section(
        self, agent_result: dict[str, Any], generation_result: dict[str, Any]
    ) -> None:
        """Render the generated definition section."""
        st.markdown("#### 📝 Gegenereerde Definitie")

        # Debug checkbox
        if st.checkbox(
            "🐛 Debug: Toon agent_result structuur", key="debug_agent_result"
        ):
            self._render_agent_result_debug(agent_result)

        # V2-only: agent_result is a dict
        definitie_to_show = (
            agent_result.get(
                "definitie_gecorrigeerd", agent_result.get("definitie", "")
            )
            if isinstance(agent_result, dict)
            else ""
        )

        # Log cleaning applied
        self._log_cleaning_applied(agent_result, generation_result)

        # Render both versions if available
        if isinstance(agent_result, dict) and (
            "definitie_origineel" in agent_result
            and "definitie_gecorrigeerd" in agent_result
        ):
            self._render_dual_definition(agent_result, generation_result)
        else:
            # Legacy format - single definition
            st.subheader("📝 Definitie")
            st.info(definitie_to_show)
            self._cache_definition_text(definitie_to_show, generation_result)

    def _render_dual_definition(
        self, agent_result: dict[str, Any], generation_result: dict[str, Any]
    ) -> None:
        """Render both original and corrected definitions."""
        if (
            agent_result["definitie_origineel"]
            != agent_result["definitie_gecorrigeerd"]
        ):
            st.success("🔧 **Definitie is opgeschoond**")
        else:
            st.info("✅ **Geen opschoning nodig - definitie was al correct**")

        st.subheader("1️⃣ Originele AI Definitie")
        st.info(agent_result["definitie_origineel"])

        st.subheader("2️⃣ Finale Definitie")
        st.info(agent_result["definitie_gecorrigeerd"])

        # Cache for UI use
        try:
            SessionStateManager.set_value(
                "current_definition_text",
                ensure_string(agent_result.get("definitie_gecorrigeerd") or ""),
            )
            SessionStateManager.set_value(
                "current_begrip",
                ensure_string(generation_result.get("begrip", "")),
            )
        except Exception as e:
            logger.warning(f"Failed to cache multi-definitie result: {e}")

    def _cache_definition_text(
        self, definitie_to_show: str, generation_result: dict[str, Any]
    ) -> None:
        """Cache definition text in session state."""
        try:
            SessionStateManager.set_value(
                "current_definition_text", ensure_string(definitie_to_show)
            )
            SessionStateManager.set_value(
                "current_begrip",
                ensure_string(generation_result.get("begrip", "")),
            )
        except Exception as e:
            logger.warning(f"Failed to cache legacy format result: {e}")

    def _render_synonym_review(self, generation_result: dict[str, Any]) -> None:
        """Render synonym review UI."""
        try:
            from ui.components.synonym_review import SynonymReviewComponent

            synonym_reviewer = SynonymReviewComponent()
            synonym_reviewer.render_synonym_metadata(generation_result)
        except Exception as e:
            logger.debug(f"Synonym review UI skipped: {e}")

    def _render_generation_details(self, agent_result: dict[str, Any]) -> None:
        """Render generation details expander."""
        with st.expander("📊 Generatie Details", expanded=False):
            if isinstance(agent_result, dict):
                col1, col2, col3 = st.columns(3)
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
                    st.metric("Succes", "Ja" if agent_result.get("success") else "Nee")

                with col3:
                    if "toetsresultaten" in agent_result:
                        violations = len(agent_result["toetsresultaten"])
                        st.metric("Violations", violations)

    def _render_validation_section(self, agent_result: dict[str, Any]) -> None:
        """Render validation section - delegates to ValidationRenderer."""
        try:
            if isinstance(agent_result, dict):
                validation_details = agent_result.get("validation_details")
                if validation_details is not None:
                    self.validation_renderer.render_validation_results(
                        validation_details
                    )
                else:
                    st.markdown("#### ✅ Kwaliteitstoetsing")
                    st.info("ℹ️ Geen validatiedetails beschikbaar.")
        except Exception as e:
            st.markdown("#### ✅ Kwaliteitstoetsing")
            st.error(f"Validatiesectie kon niet worden gerenderd: {e!s}")
            logger.exception("Validation section rendering failed")

    def _render_voorbeelden_section(
        self,
        agent_result: dict[str, Any],
        generation_result: dict[str, Any],
        saved_record: Any,
        saved_definition_id: int | None,
    ) -> None:
        """Render voorbeelden section - delegates to VoorbeeldenRenderer."""
        try:
            if isinstance(agent_result, dict):
                voorbeelden = agent_result.get("voorbeelden", {})

                # Debug logging point D - UI render
                if os.getenv("DEBUG_EXAMPLES"):
                    logger.info(
                        "[EXAMPLES-D] UI-render | gen_id=%s | voorbeelden=%s | counts=%s",
                        (
                            agent_result.get("metadata", {}).get("generation_id")
                            if isinstance(agent_result, dict)
                            else "NO_ID"
                        ),
                        "present" if voorbeelden else "missing",
                        {
                            k: len(v) if isinstance(v, list | str) else "INVALID"
                            for k, v in (voorbeelden or {}).items()
                        },
                    )

                if voorbeelden:
                    self.voorbeelden_renderer.render_voorbeelden_section(voorbeelden)
                    self.voorbeelden_renderer.render_voorbeelden_save_buttons(
                        voorbeelden, agent_result, saved_record, saved_definition_id
                    )
                else:
                    st.markdown("#### 📚 Gegenereerde Content")
                    st.info("ℹ️ Geen voorbeelden beschikbaar voor deze generatie.")
        except Exception as e:
            st.markdown("#### 📚 Gegenereerde Content")
            st.error(f"Voorbeeldensectie kon niet worden gerenderd: {e!s}")
            logger.exception("Examples section rendering failed")
            if isinstance(agent_result, dict):
                st.code(
                    f"Debug: voorbeelden type = {type(agent_result.get('voorbeelden'))}"
                )
                st.code(
                    f"Debug: voorbeelden content = {agent_result.get('voorbeelden')}"
                )

    def _render_prompt_debug_section(
        self,
        agent_result: dict[str, Any],
        generation_result: dict[str, Any],
        saved_record: Any,
    ) -> None:
        """Render prompt debug section."""
        try:
            from ui.components.prompt_debug_section import PromptDebugSection

            prompt_template: str | None = None
            if isinstance(agent_result, dict):
                meta = agent_result.get("metadata") or {}
                if isinstance(meta, dict):
                    prompt_template = (
                        meta.get("prompt_text") or meta.get("prompt_template") or None
                    )

            if (
                not prompt_template
                and saved_record
                and getattr(saved_record, "metadata", None)
            ):
                meta = (
                    saved_record.metadata
                    if isinstance(saved_record.metadata, dict)
                    else {}
                )
                prompt_template = (
                    meta.get("prompt_text") or meta.get("prompt_template") or None
                )

            voorbeelden_prompts = (
                generation_result.get("voorbeelden_prompts")
                if generation_result
                else None
            )

            class _PromptContainer:
                def __init__(self, text: str | None):
                    self.prompt_template = text or ""

            container = _PromptContainer(prompt_template) if prompt_template else None
            PromptDebugSection.render(container, voorbeelden_prompts)
        except Exception as e:
            logger.debug(f"Prompt debug section render skipped: {e}")

    def _render_saved_record_info(self, saved_record: DefinitieRecord) -> None:
        """Render saved record info and action buttons."""
        st.markdown("#### 💾 Database Record")
        st.info(
            f"Definitie opgeslagen met ID: {saved_record.id} (Status: {saved_record.status})"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Bewerk Definitie", key="edit_saved_def"):
                self._edit_definition(saved_record)

        with col2:
            if st.button("👨‍💼 Submit voor Review", key="submit_saved_review"):
                self._submit_for_review(saved_record)

        with col3:
            if st.button("📤 Exporteer", key="export_saved_def"):
                self._export_definition(saved_record)

    # ============ Helper/utility methods ============

    def _log_generation_result_debug(
        self, generation_result: dict, agent_result: Any
    ) -> None:
        """Log debug information about generation result structure."""
        logger.debug(f"Generation result keys: {list(generation_result.keys())}")

        if not agent_result:
            return

        if isinstance(agent_result, dict):
            logger.debug(f"Agent result type: dict, keys: {list(agent_result.keys())}")
            if "metadata" in agent_result and isinstance(
                agent_result["metadata"], dict
            ):
                logger.debug(
                    f"Agent result metadata keys: {list(agent_result['metadata'].keys())}"
                )
        else:
            logger.debug(f"Agent result type: {type(agent_result).__name__}")

    def _render_generation_status(self, agent_result: Any) -> None:
        """Render the success/warning status of generation."""
        is_dict = isinstance(agent_result, dict)

        if is_dict:
            if safe_dict_get(agent_result, "success"):
                score = self._extract_score_from_result(agent_result)
                st.success(f"✅ Definitie succesvol gegenereerd! (Score: {score:.2f})")
            else:
                reason = ensure_string(
                    safe_dict_get(agent_result, "reason", "Onbekende fout")
                )
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {reason}")
        elif hasattr(agent_result, "success"):
            if agent_result.success:
                st.success(
                    f"✅ Definitie succesvol gegenereerd! (Score: {agent_result.final_score:.2f})"
                )
            else:
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {agent_result.reason}")

    def _render_degraded_mode_warning(self, system_info: dict) -> None:
        """DEF-215: Render warning banner for degraded validation mode."""
        rules_loaded = system_info.get("rules_loaded", 0)
        rules_expected = system_info.get("rules_expected", 45)
        coverage = (rules_loaded / rules_expected * 100) if rules_expected > 0 else 0
        reason = system_info.get("degradation_reason", "Onbekende fout")

        st.warning(
            f"### ⚠️ BEPERKTE VALIDATIE MODUS\n\n"
            f"Validatie draait met **verminderde dekking** door een systeemprobleem.\n\n"
            f"- **Regels actief**: {rules_loaded} (alleen basis)\n"
            f"- **Regels verwacht**: {rules_expected} (volledige set)\n"
            f"- **Dekking**: {coverage:.0f}%\n\n"
            f"**Impact**: Je definitie is alleen gevalideerd tegen basisregels. "
            f"Geavanceerde controles (juridisch, ontologisch, taalkundig) zijn overgeslagen.\n\n"
            f"**Aanbeveling**: Controleer gegenereerde definities handmatig voor productiegebruik."
        )

        with st.expander("📋 Technische details", expanded=False):
            st.markdown(f"**Reden**: `{reason}`")
            st.markdown(
                "**Overgeslagen controles**:\n"
                "- Juridische compliance regels (ESS-xx serie)\n"
                "- Ontologische consistentie checks (CON-xx serie)\n"
                "- Geavanceerde structuur validatie (STR-xx serie)\n"
                "- Taalkundige kwaliteitsregels (ARAI-xx serie)"
            )

    def _extract_score_from_result(self, agent_result: dict) -> float:
        """Extract validation score from agent result."""
        return float(
            safe_dict_get(
                agent_result,
                "validation_score",
                safe_dict_get(agent_result, "final_score", 0.0),
            )
        )

    def _render_agent_result_debug(self, agent_result: Any) -> None:
        """Render debug info for agent_result structure."""
        is_dict = isinstance(agent_result, dict)
        st.code(f"Type: {type(agent_result)}")
        st.code(f"Is dict: {is_dict}")
        if is_dict:
            st.code(f"Keys: {list(agent_result.keys())}")
            st.code(f"Has definitie_origineel: {'definitie_origineel' in agent_result}")
            st.code(
                f"Has definitie_gecorrigeerd: {'definitie_gecorrigeerd' in agent_result}"
            )
        else:
            st.code(f"Attributes: {dir(agent_result)}")

    def _log_cleaning_applied(
        self, agent_result: dict[str, Any], generation_result: dict[str, Any]
    ) -> None:
        """Log when cleaning was applied."""
        if isinstance(agent_result, dict) and (
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

    # ============ Action methods ============

    def _edit_definition(self, definitie: DefinitieRecord) -> None:
        """Bewerk gegenereerde definitie."""
        st.info("🔄 Edit functionality coming soon...")

    def _submit_for_review(self, definitie: DefinitieRecord) -> None:
        """Submit definitie voor expert review via DefinitionWorkflowService."""
        try:
            service_container = SessionStateManager.get_value("service_container")
            if service_container is not None:
                workflow_service = service_container.definition_workflow_service()
            else:
                from ui.cached_services import get_cached_service_container

                container = get_cached_service_container()
                workflow_service = container.definition_workflow_service()

            result = workflow_service.submit_for_review(
                definition_id=definitie.id,
                user="web_user",
                notes="Submitted via web interface",
            )

            if result.success:
                st.success("✅ Definitie ingediend voor review")
                logger.info(
                    f"Definition {definitie.id} submitted for review by {result.updated_by}"
                )
            else:
                st.error(f"❌ {result.error_message or 'Kon status niet wijzigen'}")
        except Exception as e:
            st.error(f"❌ Onverwachte fout: {e!s}")
            logger.exception("Error submitting definition for review")

    def _export_definition(self, definitie: DefinitieRecord) -> None:
        """Exporteer definitie via ExportService."""
        try:
            from ui.components_adapter import get_ui_adapter

            adapter = get_ui_adapter()

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
                    SessionStateManager.set_value("current_definition_id", definitie.id)
                    success = adapter.export_definition(format=export_format)
                    if success:
                        st.balloons()

        except Exception as e:
            st.error(f"❌ Export mislukt: {e!s}")
            logger.exception(f"Export failed for definition {definitie.id}")

    def _clear_results(self) -> None:
        """Wis alle resultaten."""
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")

    def _show_settings_modal(self) -> None:
        """Toon instellingen modal."""
        st.info("⚙️ Settings modal coming soon...")

    def _render_save_as_draft_option(
        self,
        generation_result: dict[str, Any],
        agent_result: dict[str, Any],
    ) -> None:
        """Render option to save unacceptable definition as draft."""
        try:
            vdet = agent_result.get("validation_details") or {}
            acceptable = bool(vdet.get("is_acceptable", False))
            definitie_text = agent_result.get(
                "definitie_gecorrigeerd"
            ) or agent_result.get("definitie", "")

            if definitie_text and not acceptable:
                st.warning("❗ Deze generatie voldoet niet aan de kwaliteitsdrempel.")
                can_save = has_min_one_context()
                if not can_save:
                    st.caption(
                        "Minstens één context vereist om als concept op te slaan."
                    )
                if st.button("💾 Bewaar als concept en bewerk", disabled=not can_save):
                    self._save_as_draft(generation_result, definitie_text)
        except Exception as e:
            logger.warning(f"Could not render save-as-draft option: {e}")

    def _save_as_draft(
        self, generation_result: dict[str, Any], definitie_text: str
    ) -> None:
        """Save definition as draft concept."""
        from services.interfaces import Definition
        from ui.cached_services import get_cached_service_container

        container = get_cached_service_container()
        repo = container.repository()

        begrip_val = ensure_string(generation_result.get("begrip", ""))
        ctx = ensure_dict(SessionStateManager.get_value("global_context", {}))
        org_list = ctx.get("organisatorische_context", []) or []
        jur_list = ctx.get("juridische_context", []) or []
        wet_list = ctx.get("wettelijke_basis", []) or []
        categorie = (
            ensure_string(safe_dict_get(generation_result, "determined_category", ""))
            or None
        )

        if not (org_list or jur_list or wet_list):
            st.error(
                "Kan niet opslaan: voeg minimaal één context toe (organisatorisch of juridisch of wettelijk)."
            )
            return

        new_def = Definition(
            begrip=begrip_val,
            definitie=definitie_text,
            organisatorische_context=list(org_list),
            juridische_context=list(jur_list),
            wettelijke_basis=list(wet_list),
            categorie=categorie,
            created_by="legacy_ui",
            metadata={"status": "draft"},
        )
        try:
            new_id = repo.save(new_def)
            SessionStateManager.set_value("editing_definition_id", int(new_id))
            SessionStateManager.set_value("edit_organisatorische_context", org_list)
            SessionStateManager.set_value("edit_juridische_context", jur_list)
            SessionStateManager.set_value("edit_wettelijke_basis", wet_list)
            SessionStateManager.set_value("selected_review_definition_id", int(new_id))
            st.success("✅ Concept opgeslagen. Open de Bewerk-tab om te bewerken.")
        except Exception as se:
            st.error(f"Opslaan mislukt: {se}")
