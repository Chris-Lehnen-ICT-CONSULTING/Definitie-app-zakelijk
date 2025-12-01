"""
# ruff: noqa: PLR0912, PLR0915, SIM102, RUF001, PLC0206
Definition Generator Tab - Main AI definition generation interface.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import json
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import streamlit as st

# DEF-175: get_definitie_repository moved to lazy import in __init__

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord
from integration.definitie_checker import CheckAction, DefinitieChecker
from services.category_service import CategoryService
from services.category_state_manager import CategoryStateManager
from services.workflow_service import WorkflowService
from ui.session_state import SessionStateManager
from utils.dict_helpers import safe_dict_get
from utils.type_helpers import ensure_dict, ensure_string

logger = logging.getLogger(__name__)


class DefinitionGeneratorTab:
    """Tab voor AI definitie generatie met duplicate checking."""

    def __init__(self, checker: DefinitieChecker):
        """Initialiseer generator tab."""
        # DEF-175: Lazy import to avoid database layer dependency at module level
        from database.definitie_repository import get_definitie_repository

        self.checker = checker
        self.category_service = CategoryService(get_definitie_repository())
        self.workflow_service = WorkflowService()  # Business logic voor status workflow

        # Injectie via dependency injection volgt wanneer beschikbaar

        # Basic config voor regeneration service

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

        # Vroegtijdige guard: minsténs 1 context vereist (UI-melding)
        try:
            if not self._has_min_one_context():
                st.warning(
                    "Minstens één context is vereist (organisatorisch of juridisch of wettelijk) om te genereren of op te slaan."
                )
        except Exception as e:
            logger.error(f"Context validation check failed: {e}", exc_info=True)
            st.error("⚠️ Fout bij context validatie - controleer invoer")

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
                org, jur, wet = self._format_record_context(definitie)
                if org:
                    st.markdown(f"**Organisatorisch:** {org}")
                if jur:
                    st.markdown(f"**Juridisch:** {jur}")
                if wet:
                    st.markdown(f"**Wettelijk:** {wet}")

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
                can_generate = self._has_min_one_context()
                if not can_generate:
                    st.caption("Minstens één context vereist om nieuw te genereren.")
                if st.button(
                    "🔄 Genereer Nieuw",
                    key=f"new_{definitie.id}",
                    disabled=not can_generate,
                ):
                    # Forceer nieuwe generatie: zet flag en trigger automatische generatie
                    options = ensure_dict(
                        SessionStateManager.get_value("generation_options", {})
                    )
                    options["force_generate"] = True
                    options["force_duplicate"] = True
                    SessionStateManager.set_value("generation_options", options)
                    try:
                        SessionStateManager.clear_value("last_check_result")
                        SessionStateManager.clear_value("selected_definition")
                    except Exception:
                        pass
                    # Trigger automatische generatie bij volgende render
                    SessionStateManager.set_value("trigger_auto_generation", True)
                    st.rerun()

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
                org, jur, wet = self._format_record_context(definitie)
                ctx_parts = []
                if org:
                    ctx_parts.append(f"Organisatorisch: {org}")
                if jur:
                    ctx_parts.append(f"Juridisch: {jur}")
                if wet:
                    ctx_parts.append(f"Wettelijk: {wet}")
                st.markdown(
                    f"**Context:** {' | '.join(ctx_parts) if ctx_parts else '—'}"
                )
                st.markdown(f"**Redenen:** {', '.join(reasons)}")

                if st.button("Gebruik deze definitie", key=f"dup_use_{definitie.id}"):
                    self._use_existing_definition(definitie)

    @staticmethod
    def _format_record_context(def_record: DefinitieRecord) -> tuple[str, str, str]:
        """Formatteer contextvelden van een DefinitieRecord als weergavetekst.

        DefinitieRecord bewaart org/jur als TEXT; voor V2 kan dit JSON arrays zijn.
        Deze helper parseert veilig en maakt een korte weergave.
        """
        import json as _json

        def _parse(val) -> list[str]:
            try:
                if not val:
                    return []
                if isinstance(val, str):
                    return (
                        list(_json.loads(val)) if val.strip().startswith("[") else [val]
                    )
                if isinstance(val, list):
                    return val
            except Exception:
                return []
            return []

        org_list = _parse(getattr(def_record, "organisatorische_context", None))
        jur_list = _parse(getattr(def_record, "juridische_context", None))
        wet_list: list[str] = []
        if hasattr(def_record, "get_wettelijke_basis_list"):
            wet_list = def_record.get_wettelijke_basis_list() or []
        return ", ".join(org_list), ", ".join(jur_list), ", ".join(wet_list)

    # ===== Context guards (minstens 1 vereist) =====
    def _get_global_context_lists(self) -> dict[str, list[str]]:
        """Lees globale UI-context en normaliseer naar lijsten."""
        try:
            ctx = ensure_dict(SessionStateManager.get_value("global_context", {}))
        except Exception:
            ctx = {}
        org_list = ctx.get("organisatorische_context", []) or []
        jur_list = ctx.get("juridische_context", []) or []
        wet_list = ctx.get("wettelijke_basis", []) or []
        return {
            "organisatorische_context": list(org_list),
            "juridische_context": list(jur_list),
            "wettelijke_basis": list(wet_list),
        }

    def _has_min_one_context(self) -> bool:
        """True wanneer minstens één van de drie contextlijsten een waarde bevat."""
        try:
            ctx = self._get_global_context_lists()
            return bool(
                ctx.get("organisatorische_context")
                or ctx.get("juridische_context")
                or ctx.get("wettelijke_basis")
            )
        except Exception:
            return False

    def _render_generation_results(self, generation_result):
        """Render resultaten van definitie generatie."""
        st.markdown("### 🚀 Generatie Resultaten")

        agent_result = safe_dict_get(generation_result, "agent_result")
        saved_record = safe_dict_get(generation_result, "saved_record")
        saved_definition_id = safe_dict_get(generation_result, "saved_definition_id")
        safe_dict_get(generation_result, "timestamp")
        determined_category = safe_dict_get(generation_result, "determined_category")

        # Debug logging
        self._log_generation_result_debug(generation_result, agent_result)

        if not agent_result:
            return

        # Show success/warning indicator
        self._render_generation_status(agent_result)

        # DEF-215: Check for degraded validation mode and show warning
        validation_metadata = safe_dict_get(agent_result, "validation_metadata", {})
        system_info = safe_dict_get(validation_metadata, "system", {})
        if safe_dict_get(system_info, "degraded_mode", False):
            self._render_degraded_mode_warning(system_info)

        # EPIC-018: Badge/indicator voor gebruikte documentcontext
        try:
            doc_ctx = safe_dict_get(generation_result, "document_context")
            if (
                isinstance(doc_ctx, dict)
                and int(doc_ctx.get("document_count", 0) or 0) > 0
            ):
                st.info(
                    f"📄 Documentcontext gebruikt: {int(doc_ctx['document_count'])} document(en)"
                )
        except Exception:
            pass

        # Sla ID van bewaarde definitie op voor Expert-tab prefill
        # Bewaar het ID van de opgeslagen definitie voor de Expert/Bewerk tabs
        target_id = None
        if isinstance(saved_definition_id, int) and saved_definition_id > 0:
            target_id = saved_definition_id
        elif saved_record and getattr(saved_record, "id", None):
            target_id = int(saved_record.id)

        if target_id:
            try:
                # Voor Expert/Bewerk tabs
                SessionStateManager.set_value(
                    "selected_review_definition_id", target_id
                )
                # Zorg dat de Bewerk-tab direct kan auto-laden
                SessionStateManager.set_value("editing_definition_id", target_id)
            except Exception:
                pass

        # Ontologische categorie sectie - prominent weergeven
        if determined_category:
            self._render_ontological_category_section(
                determined_category, generation_result, saved_record
            )

        # UFO-categorie selector (onder ontologische categorie)
        try:
            self._render_ufo_category_selector(generation_result)
        except Exception:
            logger.debug(
                "UFO-categorie selector render skipped due to error", exc_info=True
            )

        # Generated definition
        st.markdown("#### 📝 Gegenereerde Definitie")

        # Debug: toon wat we hebben
        if st.checkbox(
            "🐛 Debug: Toon agent_result structuur", key="debug_agent_result"
        ):
            is_dict = isinstance(agent_result, dict)
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

        # V2-only: agent_result is a dict
        definitie_to_show = (
            agent_result.get(
                "definitie_gecorrigeerd", agent_result.get("definitie", "")
            )
            if isinstance(agent_result, dict)
            else ""
        )

        # Debug logging voor opschoning
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

        # Toon ALTIJD beide versies
        # Nu werkt 'in' operator voor zowel dict als LegacyGenerationResult
        if isinstance(agent_result, dict) and (
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
            # Bewaar finale tekst + begrip voor UI-uitleg (pass-rationales)
            try:
                SessionStateManager.set_value(
                    "current_definition_text",
                    ensure_string(agent_result.get("definitie_gecorrigeerd") or ""),
                )
                SessionStateManager.set_value(
                    "current_begrip",
                    ensure_string(generation_result.get("begrip", "")),
                )
            except Exception:
                pass
        else:
            # Legacy format - toon enkele definitie
            st.subheader("📝 Definitie")
            st.info(definitie_to_show)
            try:
                SessionStateManager.set_value(
                    "current_definition_text", ensure_string(definitie_to_show)
                )
                SessionStateManager.set_value(
                    "current_begrip",
                    ensure_string(generation_result.get("begrip", "")),
                )
            except Exception:
                pass

        # Bronverantwoording: toon gebruikte web bronnen indien beschikbaar
        self._render_sources_section(generation_result, agent_result, saved_record)

        # PHASE 3.2: Synonym Review UI (Architecture v3.1)
        try:
            from ui.components.synonym_review import SynonymReviewComponent

            synonym_reviewer = SynonymReviewComponent()
            synonym_reviewer.render_synonym_metadata(generation_result)
        except Exception as e:
            logger.debug(f"Synonym review UI skipped: {e}")

        # Generation details
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

        # Validation results (dict or object) with section isolation
        try:
            if isinstance(agent_result, dict):
                validation_details = agent_result.get("validation_details")
                if validation_details is not None:
                    self._render_validation_results(validation_details)
                else:
                    st.markdown("#### ✅ Kwaliteitstoetsing")
                    st.info("ℹ️ Geen validatiedetails beschikbaar.")
        except Exception as e:
            st.markdown("#### ✅ Kwaliteitstoetsing")
            st.error(f"Validatiesectie kon niet worden gerenderd: {e!s}")
            logger.exception("Validation section rendering failed")

        # GEEN SESSION STATE VOOR PROMPTS! Prompts komen DIRECT uit agent_result!

        # Voorbeelden sectie - direct vanuit agent_result tonen, GEEN session state!
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
                    self._render_voorbeelden_section(voorbeelden)
                    # Persistente opslag van voorbeelden in DB (automatisch) wanneer een record is opgeslagen
                    try:
                        saved_id = None
                        if (
                            saved_record is not None
                            and hasattr(saved_record, "id")
                            and saved_record.id
                        ):
                            saved_id = int(saved_record.id)
                        elif (
                            isinstance(saved_definition_id, int)
                            and saved_definition_id > 0
                        ):
                            saved_id = int(saved_definition_id)

                        if saved_id:
                            # DEF-156: Show UI confirmation when voorbeelden are auto-saved
                            saved_successfully = self._maybe_persist_examples(
                                saved_id, agent_result
                            )
                            if saved_successfully:
                                # Count total voorbeelden items for confirmation message
                                vb = agent_result.get("voorbeelden", {})
                                if isinstance(vb, dict):
                                    total = sum(
                                        (
                                            len(v)
                                            if isinstance(v, list)
                                            else (1 if v else 0)
                                        )
                                        for v in vb.values()
                                    )
                                    st.success(
                                        f"✅ Voorbeelden automatisch opgeslagen ({total} items)"
                                    )
                    except Exception as e:
                        logger.warning(
                            f"Automatisch opslaan van voorbeelden overgeslagen: {e}"
                        )

                    # Handmatige opslagknop (forceren)
                    try:
                        col_left, col_right = st.columns([1, 3])
                        with col_left:
                            can_save_examples = True
                            saved_id_btn = None
                            if (
                                saved_record is not None
                                and hasattr(saved_record, "id")
                                and saved_record.id
                            ):
                                saved_id_btn = int(saved_record.id)
                            elif (
                                isinstance(saved_definition_id, int)
                                and saved_definition_id > 0
                            ):
                                saved_id_btn = int(saved_definition_id)
                            else:
                                can_save_examples = False

                            help_text = None
                            if not can_save_examples:
                                help_text = "Sla eerst de definitie op om voorbeelden te kunnen bewaren."

                            if st.button(
                                "💾 Voorbeelden naar DB opslaan (forceren)",
                                key="force_save_examples",
                                disabled=not can_save_examples,
                                help=help_text,
                            ):
                                if saved_id_btn:
                                    ok = self._persist_examples_manual(
                                        saved_id_btn, agent_result
                                    )
                                    if ok:
                                        st.success(
                                            "✅ Voorbeelden opgeslagen in database"
                                        )
                                    else:
                                        st.info(
                                            "ℹ️ Geen op te slaan voorbeelden of al up-to-date"
                                        )
                    except Exception as e:
                        logger.debug(
                            f"Render force-save examples knop overgeslagen: {e}"
                        )
                else:
                    st.markdown("#### 📚 Gegenereerde Content")
                    st.info("ℹ️ Geen voorbeelden beschikbaar voor deze generatie.")
        except Exception as e:
            st.markdown("#### 📚 Gegenereerde Content")
            st.error(f"Voorbeeldensectie kon niet worden gerenderd: {e!s}")
            logger.exception("Examples section rendering failed")
            # Debug info om te zien wat er mis gaat
            if isinstance(agent_result, dict):
                st.code(
                    f"Debug: voorbeelden type = {type(agent_result.get('voorbeelden'))}"
                )
                st.code(
                    f"Debug: voorbeelden content = {agent_result.get('voorbeelden')}"
                )

        # Prompt Debug Section — always render (not only on errors)
        try:
            from ui.components.prompt_debug_section import PromptDebugSection

            # Prefer prompt from agent_result.metadata, fallback to saved_record.metadata
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

            # Example prompts captured during generation (optional)
            voorbeelden_prompts = (
                generation_result.get("voorbeelden_prompts")
                if generation_result
                else None
            )

            # Always render the debug section
            class _PromptContainer:
                def __init__(self, text: str | None):
                    # PromptDebugSection expects attribute prompt_template
                    self.prompt_template = text or ""

            container = _PromptContainer(prompt_template) if prompt_template else None
            PromptDebugSection.render(container, voorbeelden_prompts)
        except Exception as e:
            # Never break the page on debug issues
            logger.debug(f"Prompt debug section render skipped: {e}")

        # Saved record info
        if saved_record:
            st.markdown("#### 💾 Database Record")
            st.info(
                f"Definitie opgeslagen met ID: {saved_record.id} (Status: {saved_record.status})"
            )

            # Action buttons
            col1, col2, col3 = st.columns(3)

    def _render_ontological_category_section(
        self,
        determined_category: str,
        generation_result: dict[str, Any],
        saved_record: Any = None,
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

        # Category change regeneration preview (direct onder categorie sectie)
        category_change_state = generation_result.get("category_change_state")
        if category_change_state and category_change_state.show_regeneration_preview:
            self._render_category_change_preview(
                category_change_state, generation_result, saved_record
            )

    def _render_ufo_category_selector(self, generation_result: dict[str, Any]) -> None:
        """Render de UFO-categorie selectie en opslagknop.

        Toont een selectbox met UFO-categorieën en biedt een knop om de keuze
        op te slaan bij het opgeslagen record (indien beschikbaar).
        """
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
        except Exception:
            current_ufo = None

        try:
            default_index = (
                ufo_opties.index(current_ufo or "")
                if (current_ufo or "") in ufo_opties
                else 0
            )
        except Exception:
            default_index = 0

        def _persist_ufo_selection(key: str, def_id: int | None):
            try:
                if not def_id:
                    return
                from ui.session_state import SessionStateManager

                value = SessionStateManager.get_value(key)
                if value == "":
                    value = None
                from database.definitie_repository import get_definitie_repository

                repo = get_definitie_repository()
                user = SessionStateManager.get_value("user", default="system")
                _ = repo.update_definitie(
                    int(def_id), {"ufo_categorie": value}, updated_by=user
                )
            except Exception:
                # Zwijgende fout om UI niet te verstoren; logs via Streamlit niet nodig
                pass

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

    def _maybe_persist_examples(
        self, definitie_id: int, agent_result: dict[str, Any]
    ) -> bool:
        """Sla gegenereerde voorbeelden automatisch op in de DB.

        - Vermijdt dubbele opslag door te keyen op generation_id
        - Slaat alleen op wanneer er daadwerkelijk content is
        - Vergelijkt met huidige actieve DB-voorbeelden om onnodige writes te vermijden

        Returns:
            True if voorbeelden were saved, False otherwise
        """
        try:
            meta = (
                ensure_dict(agent_result.get("metadata", {}))
                if isinstance(agent_result, dict)
                else {}
            )
            gen_id = meta.get("generation_id")
            # FIX: Remove flag check - causes silent save failures on regeneration
            # Flag reuse in same session prevents voorbeelden from being saved
            # Use DB comparison for idempotency instead (line 874)
            logger.debug(
                f"Auto-save voorbeelden check for definitie_id={definitie_id}, gen_id={gen_id}"
            )

            raw = (
                ensure_dict(agent_result.get("voorbeelden", {}))
                if isinstance(agent_result, dict)
                else {}
            )
            if not raw:
                logger.warning(
                    f"No voorbeelden data in agent_result for definitie {definitie_id}"
                )
                return False

            # Canonicaliseer en normaliseer naar lists
            from ui.helpers.examples import canonicalize_examples

            canon = canonicalize_examples(raw)

            def _as_list(v: Any) -> list[str]:
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
                if isinstance(v, str) and v.strip():
                    return [v.strip()]
                return []

            to_save: dict[str, list[str]] = {
                "voorbeeldzinnen": _as_list(canon.get("voorbeeldzinnen")),
                "praktijkvoorbeelden": _as_list(canon.get("praktijkvoorbeelden")),
                "tegenvoorbeelden": _as_list(canon.get("tegenvoorbeelden")),
                "synoniemen": _as_list(canon.get("synoniemen")),
                "antoniemen": _as_list(canon.get("antoniemen")),
            }
            # Toelichting optioneel opslaan als één regel (repository ondersteunt explanation)
            if (
                isinstance(canon.get("toelichting"), str)
                and canon.get("toelichting").strip()
            ):
                to_save["toelichting"] = [canon.get("toelichting").strip()]  # type: ignore[index]

            # Controleer of er iets nieuws is
            total_new = sum(len(v) for v in to_save.values())
            if total_new == 0:
                logger.warning(
                    f"Voorbeelden dict empty (0 items) for definitie {definitie_id}"
                )
                return False

            # Vergelijk met huidige actieve voorbeelden; sla alleen op als er verschil is
            from database.definitie_repository import get_definitie_repository

            repo = get_definitie_repository()
            current = repo.get_voorbeelden_by_type(definitie_id)

            def _norm(d: dict[str, list[str]]) -> dict[str, set[str]]:
                return {k: {str(x).strip() for x in (d.get(k) or [])} for k in d}

            # Map DB keys naar canonical UI keys voor vergelijking
            # DB keys zijn al canonicalized in helpers.resolve_examples pad, maar hier gebruiken we direct:
            current_canon = {
                "voorbeeldzinnen": current.get("sentence", [])
                or current.get("voorbeeldzinnen", []),
                "praktijkvoorbeelden": current.get("practical", [])
                or current.get("praktijkvoorbeelden", []),
                "tegenvoorbeelden": current.get("counter", [])
                or current.get("tegenvoorbeelden", []),
                "synoniemen": current.get("synonyms", [])
                or current.get("synoniemen", []),
                "antoniemen": current.get("antonyms", [])
                or current.get("antoniemen", []),
                "toelichting": current.get("explanation", [])
                or current.get("toelichting", []),
            }

            if _norm(current_canon) == _norm(to_save):
                logger.info(
                    f"Voorbeelden identical to database for definitie {definitie_id}, skipping save"
                )
                return False  # Not saved (already exists)

            # Sla op met voorkeursterm uit session state
            from pydantic import ValidationError

            from models.voorbeelden_validation import validate_save_voorbeelden_input

            voorkeursterm = SessionStateManager.get_value("voorkeursterm", "")

            # DEF-74: Validate input before saving
            try:
                validated = validate_save_voorbeelden_input(
                    definitie_id=definitie_id,
                    voorbeelden_dict=to_save,
                    generation_model="ai",
                    generation_params=meta if isinstance(meta, dict) else None,
                    gegenereerd_door=ensure_string(meta.get("model") or "ai"),
                    voorkeursterm=voorkeursterm if voorkeursterm else None,
                )
                repo.save_voorbeelden(**validated.model_dump())
                logger.info(
                    f"✅ Voorbeelden saved for definitie {definitie_id}: "
                    f"{total_new} items across {len([k for k, v in to_save.items() if v])} types"
                )
                # DEF-156: Return success indicator for UI confirmation
                return True
            except ValidationError as e:
                logger.error(
                    f"Voorbeelden validation failed for definitie {definitie_id}: {e}"
                )
                # Don't raise in auto-save context, just log
                return False
        except Exception as e:
            logger.warning("Automatisch opslaan voorbeelden mislukt: %s", e)
            return False

    def _persist_examples_manual(
        self, definitie_id: int, agent_result: dict[str, Any]
    ) -> bool:
        """Forceer het opslaan van voorbeelden in de DB (handmatige actie).

        Returns True als er iets is opgeslagen, False als er niets te doen was.
        """
        try:
            raw = (
                ensure_dict(agent_result.get("voorbeelden", {}))
                if isinstance(agent_result, dict)
                else {}
            )
            if not raw:
                return False

            from ui.helpers.examples import canonicalize_examples

            canon = canonicalize_examples(raw)

            def _as_list(v: Any) -> list[str]:
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
                if isinstance(v, str) and v.strip():
                    return [v.strip()]
                return []

            to_save: dict[str, list[str]] = {
                "voorbeeldzinnen": _as_list(canon.get("voorbeeldzinnen")),
                "praktijkvoorbeelden": _as_list(canon.get("praktijkvoorbeelden")),
                "tegenvoorbeelden": _as_list(canon.get("tegenvoorbeelden")),
                "synoniemen": _as_list(canon.get("synoniemen")),
                "antoniemen": _as_list(canon.get("antoniemen")),
            }
            if (
                isinstance(canon.get("toelichting"), str)
                and canon.get("toelichting").strip()
            ):
                to_save["toelichting"] = [canon.get("toelichting").strip()]  # type: ignore[index]

            total_new = sum(len(v) for v in to_save.values())
            if total_new == 0:
                return False

            from database.definitie_repository import get_definitie_repository

            repo = get_definitie_repository()
            from pydantic import ValidationError

            from models.voorbeelden_validation import validate_save_voorbeelden_input

            voorkeursterm = SessionStateManager.get_value("voorkeursterm", "")

            # DEF-74: Validate input before saving
            try:
                validated = validate_save_voorbeelden_input(
                    definitie_id=definitie_id,
                    voorbeelden_dict=to_save,
                    generation_model="ai",
                    generation_params=(
                        ensure_dict(agent_result.get("metadata", {}))
                        if isinstance(agent_result, dict)
                        else None
                    ),
                    gegenereerd_door=ensure_string(
                        (agent_result.get("metadata", {}) or {}).get("model")
                        if isinstance(agent_result, dict)
                        else "ai"
                    ),
                    voorkeursterm=voorkeursterm if voorkeursterm else None,
                )
                repo.save_voorbeelden(**validated.model_dump())
            except ValidationError as e:
                logger.error(f"Voorbeelden validation failed: {e}")
                return False
            return True
        except Exception as e:
            logger.warning("Force opslaan voorbeelden mislukt: %s", e)
            return False

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
        old_category = safe_dict_get(generation_result, "determined_category", "proces")
        current_definition = self._extract_definition_from_result(generation_result)
        begrip = ensure_string(safe_dict_get(generation_result, "begrip", ""))
        saved_record = generation_result.get("saved_record")

        # Voer workflow uit via orchestration layer
        from services.workflow_service import WorkflowAction

        result = self.workflow_service.execute_category_change_workflow(
            definition_id=saved_record.id if saved_record else None,
            old_category=old_category,
            new_category=new_category,
            current_definition=current_definition,
            begrip=begrip,
            user="web_user",
            reason="Handmatige aanpassing via UI",
        )

        # Update local state voor UI consistency
        if result.success:
            CategoryStateManager.update_generation_result_category(
                generation_result, new_category
            )
            # Bewaar handmatige override in session state zodat deze niet wordt overschreven bij volgende generatie
            SessionStateManager.set_value("manual_ontological_category", new_category)
            logger.info(f"Handmatige categorie override gezet: {new_category}")

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

        # Action buttons
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
        else:
            # Geen saved_record beschikbaar: bied optie om als concept op te slaan wanneer niet acceptabel
            try:
                agent_result = safe_dict_get(generation_result, "agent_result")
                if isinstance(agent_result, dict):
                    vdet = agent_result.get("validation_details") or {}
                    acceptable = bool(vdet.get("is_acceptable", False))
                    definitie_text = agent_result.get(
                        "definitie_gecorrigeerd"
                    ) or agent_result.get("definitie", "")
                    if definitie_text and not acceptable:
                        st.warning(
                            "❗ Deze generatie voldoet niet aan de kwaliteitsdrempel."
                        )
                        can_save = self._has_min_one_context()
                        if not can_save:
                            st.caption(
                                "Minstens één context vereist om als concept op te slaan."
                            )
                        if st.button(
                            "💾 Bewaar als concept en bewerk", disabled=not can_save
                        ):
                            from services.interfaces import Definition
                            from ui.cached_services import get_cached_service_container

                            container = get_cached_service_container()
                            repo = container.repository()

                            begrip_val = ensure_string(
                                generation_result.get("begrip", "")
                            )
                            # Haal contextlijsten uit globale context (zoals gebruikt bij generatie)
                            ctx = ensure_dict(
                                SessionStateManager.get_value("global_context", {})
                            )
                            org_list = ctx.get("organisatorische_context", []) or []
                            jur_list = ctx.get("juridische_context", []) or []
                            wet_list = ctx.get("wettelijke_basis", []) or []
                            categorie = (
                                ensure_string(
                                    safe_dict_get(
                                        generation_result, "determined_category", ""
                                    )
                                )
                                or None
                            )

                            # Defensieve guard (naast disabled UI)
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
                                # Zet auto-load voor Bewerk-tab
                                SessionStateManager.set_value(
                                    "editing_definition_id", int(new_id)
                                )
                                SessionStateManager.set_value(
                                    "edit_organisatorische_context", org_list
                                )
                                SessionStateManager.set_value(
                                    "edit_juridische_context", jur_list
                                )
                                SessionStateManager.set_value(
                                    "edit_wettelijke_basis", wet_list
                                )
                                SessionStateManager.set_value(
                                    "selected_review_definition_id", int(new_id)
                                )
                                st.success(
                                    "✅ Concept opgeslagen. Open de Bewerk-tab om te bewerken."
                                )
                            except Exception as se:
                                st.error(f"Opslaan mislukt: {se}")
            except Exception as e:
                logger.warning(f"Could not render save-as-draft option: {e}")

    def _render_sources_section(self, generation_result, agent_result, saved_record):
        """Render sectie met gebruikte bronnen (provenance)."""
        try:
            sources = None

            # 1) Probeer uit saved_record.metadata (na opslag)
            if saved_record and getattr(saved_record, "metadata", None):
                metadata = saved_record.metadata
                if isinstance(metadata, dict):
                    sources = metadata.get("sources")

            # 2) STORY 3.1: Check direct sources key when agent_result is dict
            if sources is None and isinstance(agent_result, dict):
                sources = agent_result.get("sources")

            # 2b) Backward: attribute style (should not occur for dict responses)
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

            # Toon statusinformatie indien beschikbaar
            status_meta = None
            available_meta = None
            if saved_record and getattr(saved_record, "metadata", None):
                meta = saved_record.metadata
                if isinstance(meta, dict):
                    status_meta = meta.get("web_lookup_status")
                    available_meta = meta.get("web_lookup_available")
            if status_meta is None:
                if isinstance(agent_result, dict):
                    meta = agent_result.get("metadata")
                    if isinstance(meta, dict):
                        status_meta = meta.get("web_lookup_status")
                        available_meta = meta.get("web_lookup_available")
                elif hasattr(agent_result, "metadata") and isinstance(
                    agent_result.metadata, dict
                ):
                    status_meta = agent_result.metadata.get("web_lookup_status")
                    available_meta = agent_result.metadata.get("web_lookup_available")

            # Timeout uit metadata of environment
            timeout_meta = None
            if saved_record and getattr(saved_record, "metadata", None):
                m = saved_record.metadata
                if isinstance(m, dict):
                    timeout_meta = m.get("web_lookup_timeout")
            if timeout_meta is None:
                if isinstance(agent_result, dict):
                    m = agent_result.get("metadata")
                    if isinstance(m, dict):
                        timeout_meta = m.get("web_lookup_timeout")
                elif hasattr(agent_result, "metadata") and isinstance(
                    agent_result.metadata, dict
                ):
                    timeout_meta = agent_result.metadata.get("web_lookup_timeout")

            if status_meta or available_meta is not None:
                status_text = status_meta or "onbekend"
                avail_text = (
                    "beschikbaar"
                    if (available_meta is True)
                    else "niet beschikbaar" if (available_meta is False) else "onbekend"
                )
                # Fallback naar env als metadata geen timeout bevat
                if timeout_meta is None:
                    try:
                        timeout_meta = float(
                            os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", "10.0")
                        )
                    except Exception:
                        timeout_meta = 10.0
                st.caption(
                    f"Web lookup: {status_text} ({avail_text}) — timeout {float(timeout_meta):.1f}s"
                )

            # SRU/WL debug: toon lookup attempts (endpoints/termen)
            # Zoek debug-informatie in metadata (saved_record of agent_result)
            debug_info = None
            if saved_record and getattr(saved_record, "metadata", None):
                m = saved_record.metadata
                if isinstance(m, dict):
                    debug_info = m.get("web_lookup_debug")
            if debug_info is None:
                if isinstance(agent_result, dict):
                    m = agent_result.get("metadata")
                    if isinstance(m, dict):
                        debug_info = m.get("web_lookup_debug")
                elif hasattr(agent_result, "metadata") and isinstance(
                    agent_result.metadata, dict
                ):
                    debug_info = agent_result.metadata.get("web_lookup_debug")

            if st.checkbox(
                "🐛 SRU/WL debug: Toon lookup attempts (JSON)",
                key="debug_web_lookup_attempts",
            ):
                st.json(debug_info or {})

            # Extra: overzichtelijke tabel met pogingdetails (provider, strategie, query)
            if debug_info and isinstance(debug_info, dict):
                attempts_list = debug_info.get("attempts") or []
                if attempts_list:
                    if st.checkbox(
                        "🐛 SRU/WL debug: Toon pogingdetails (tabel)",
                        key="debug_web_lookup_attempts_table",
                    ):
                        rows = []
                        for a in attempts_list:
                            try:
                                provider = a.get("provider") or a.get("endpoint") or "?"
                                api = a.get("api_type") or "?"
                                strategy = a.get("strategy") or (
                                    "fallback" if a.get("fallback") else ""
                                )
                                q = a.get("query") or a.get("term") or ""
                                status = (
                                    a.get("status")
                                    if "status" in a
                                    else (
                                        "ok"
                                        if a.get("success")
                                        else "fail" if "success" in a else ""
                                    )
                                )
                                records = a.get("records")
                                url = a.get("url") or ""
                                rows.append(
                                    {
                                        "provider": provider,
                                        "api": api,
                                        "strategie": strategy,
                                        "query/term": q,
                                        "status": status,
                                        "records": records,
                                        "url": url,
                                    }
                                )
                            except Exception:
                                continue
                        if rows:
                            try:
                                import pandas as pd  # type: ignore

                                st.dataframe(pd.DataFrame(rows))
                            except Exception:
                                # Fallback zonder pandas
                                for r in rows:
                                    st.markdown(
                                        f"- {r['provider']} ({r['api']}): {r['strategie']} — {r['query/term']}"
                                        f" — status={r['status']} records={r.get('records') or 0}"
                                    )

            # Debug toggle: toon ruwe web_lookup data (JSON)
            if st.checkbox(
                "🐛 Debug: Toon ruwe web_lookup data (JSON)",
                key="debug_web_lookup_sources_raw",
            ):
                # Verzamel ruwe bronnenlijsten van verschillende plekken
                saved_meta_sources = None
                agent_meta_sources = None
                agent_attr_sources = None

                if saved_record and getattr(saved_record, "metadata", None):
                    m = saved_record.metadata
                    if isinstance(m, dict):
                        saved_meta_sources = m.get("sources")

                if isinstance(agent_result, dict):
                    m = agent_result.get("metadata")
                    if isinstance(m, dict):
                        agent_meta_sources = m.get("sources")
                elif hasattr(agent_result, "metadata") and isinstance(
                    agent_result.metadata, dict
                ):
                    agent_meta_sources = agent_result.metadata.get("sources")

                # Top-level sources on dict response (canonical)
                agent_top_sources = None
                if isinstance(agent_result, dict):
                    agent_top_sources = agent_result.get("sources")

                if hasattr(agent_result, "sources"):
                    agent_attr_sources = agent_result.sources

                st.json(
                    {
                        "web_lookup_status": status_meta,
                        "web_lookup_available": available_meta,
                        "web_lookup_timeout": timeout_meta,
                        "saved_record.metadata.sources": saved_meta_sources,
                        "agent_result.metadata.sources": agent_meta_sources,
                        "agent_result.sources": agent_attr_sources,
                        "agent_result.top_level_sources": agent_top_sources,
                    }
                )

            if not sources:
                # Toon specifiekere feedback op basis van metadata indien beschikbaar
                web_status = None
                web_available = None

                # Metadata uit saved_record
                if saved_record and getattr(saved_record, "metadata", None):
                    meta = saved_record.metadata
                    if isinstance(meta, dict):
                        web_status = meta.get("web_lookup_status")
                        web_available = meta.get("web_lookup_available")

                # Metadata uit agent_result
                if web_status is None:
                    if isinstance(agent_result, dict):
                        meta = agent_result.get("metadata")
                        if isinstance(meta, dict):
                            web_status = meta.get("web_lookup_status")
                            web_available = meta.get("web_lookup_available")
                    elif hasattr(agent_result, "metadata") and isinstance(
                        agent_result.metadata, dict
                    ):
                        web_status = agent_result.metadata.get("web_lookup_status")
                        web_available = agent_result.metadata.get(
                            "web_lookup_available"
                        )

                # Bepaal bericht
                if web_available is False or web_status == "not_available":
                    msg = "ℹ️ Web lookup is niet beschikbaar in deze omgeving."
                elif web_status == "timeout":
                    msg = "⏱️ Web lookup time-out — geen bronnen opgehaald."
                elif web_status == "error":
                    msg = "⚠️ Web lookup fout — geen bronnen opgehaald."
                else:
                    msg = "ℹ️ Geen relevante externe bronnen gevonden."

                st.info(msg)
                return

            # Toon alle gevonden bronnen (gebruik expander om het compact te houden)
            for idx, src in enumerate(sources):
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

                    # Documentbron: toon bestandsnaam/locatie
                    if src.get("provider") == "documents":
                        fname = src.get("title") or src.get("filename")
                        cite = src.get("citation_label")
                        if fname or cite:
                            st.markdown(
                                f"**Document**: {fname or '(onbekend)'}{f' · Locatie: {cite}' if cite else ''}"
                            )

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

    def _get_provider_label(self, provider: str) -> str:
        """Get human-friendly label for provider (local helper)."""
        labels = {
            "wikipedia": "Wikipedia NL",
            "overheid": "Overheid.nl",
            "rechtspraak": "Rechtspraak.nl",
            "wiktionary": "Wiktionary NL",
        }
        return labels.get(provider, provider.replace("_", " ").title())

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

        # Handle dict format (V2)
        if is_dict:
            if safe_dict_get(agent_result, "success"):
                score = self._extract_score_from_result(agent_result)
                st.success(f"✅ Definitie succesvol gegenereerd! (Score: {score:.2f})")
            else:
                reason = ensure_string(
                    safe_dict_get(agent_result, "reason", "Onbekende fout")
                )
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {reason}")
        # Handle object format (legacy)
        elif hasattr(agent_result, "success"):
            if agent_result.success:
                st.success(
                    f"✅ Definitie succesvol gegenereerd! (Score: {agent_result.final_score:.2f})"
                )
            else:
                st.warning(f"⚠️ Generatie gedeeltelijk succesvol: {agent_result.reason}")

    def _render_degraded_mode_warning(self, system_info: dict) -> None:
        """DEF-215: Render warning banner for degraded validation mode.

        Shows user that validation is operating with reduced rule coverage
        due to ToetsregelManager initialization failure.

        Args:
            system_info: System metadata from validation result containing:
                - degraded_mode: bool
                - rules_loaded: int
                - rules_expected: int
                - degradation_reason: str | None
        """
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
        return cast(
            float,
            safe_dict_get(
                agent_result,
                "validation_score",
                safe_dict_get(agent_result, "final_score", 0.0),
            ),
        )

    def _build_detailed_assessment(self, validation_result: dict) -> list[str]:
        """Build detailed assessment from validation result."""
        try:
            violations = validation_result.get("violations", []) or []
            passed_rules = validation_result.get("passed_rules", []) or []

            # Calculate statistics
            stats = self._calculate_validation_stats(violations, passed_rules)

            lines = []
            # Add summary line
            lines.append(self._format_validation_summary(stats))

            # Add violation lines
            lines.extend(self._format_violations(violations))

            # Add passed rules
            lines.extend(self._format_passed_rules(stats["passed_ids"]))

            return lines
        except Exception as e:
            logger.debug(f"Kon beoordeling_gen niet afleiden uit V2-resultaat: {e}")
            return []

    def _calculate_validation_stats(self, violations: list, passed_rules: list) -> dict:
        """Calculate validation statistics."""
        failed_ids = sorted(
            {
                str(v.get("rule_id") or v.get("code") or "")
                for v in violations
                if isinstance(v, dict)
            }
        )
        passed_ids = sorted({str(r) for r in passed_rules})
        total = len(set(failed_ids).union(passed_ids))
        passed_count = len(passed_ids)
        failed_count = len(failed_ids)
        pct = (passed_count / total * 100.0) if total > 0 else 0.0

        return {
            "failed_ids": failed_ids,
            "passed_ids": passed_ids,
            "total": total,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "percentage": pct,
        }

    def _format_validation_summary(self, stats: dict) -> str:
        """Format validation summary line."""
        summary = f"📊 **Toetsing Samenvatting**: {stats['passed_count']}/{stats['total']} regels geslaagd ({stats['percentage']:.1f}%)"
        if stats["failed_count"] > 0:
            summary += f" | ❌ {stats['failed_count']} gefaald"
        return summary

    def _format_violations(self, violations: list) -> list[str]:
        """Format violation lines with severity-based sorting and emojis."""
        lines = []

        def _v_key(v):
            rid = str(v.get("rule_id") or v.get("code") or "")
            return self._rule_sort_key(rid)

        for v in sorted(violations, key=_v_key):
            rid = str(v.get("rule_id") or v.get("code") or "")
            sev = str(v.get("severity", "warning")).lower()
            desc = v.get("description") or v.get("message") or ""
            suggestion = v.get("suggestion")
            if suggestion:
                # Voeg verbeteradvies toe zonder UI-structuur te wijzigen
                desc = f"{desc} · Wat verbeteren: {suggestion}"
            emoji = self._get_severity_emoji(sev)
            name, explanation = self._get_rule_display_and_explanation(rid)
            name_part = f" — {name}" if name else ""
            expl_labeled = (
                f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
            )
            lines.append(
                f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}"
            )

        return lines

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        if severity in {"critical", "error", "high"}:
            return "❌"
        if severity in {"warning", "medium", "low"}:
            return "⚠️"
        return "📋"

    def _format_passed_rules(self, passed_ids: list[str]) -> list[str]:
        """Format passed rule lines, inclusief 'Wat toetst' en 'Waarom'."""
        lines_out: list[str] = []
        text, begrip = self._get_current_text_and_begrip()
        for rid in sorted(passed_ids, key=self._rule_sort_key):
            name, explanation = self._get_rule_display_and_explanation(rid)
            name_part = f" — {name}" if name else ""
            wat_toetst = (
                f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
            )
            reason = self._build_pass_reason(rid, text, begrip)
            waarom = f" · Waarom geslaagd: {reason}" if reason else ""
            lines_out.append(f"✅ {rid}{name_part}: OK · {wat_toetst}{waarom}")
        return lines_out

    def _render_validation_results(self, validation_result):
        """Render validation resultaten via gedeelde renderer (V2 dict)."""
        st.markdown("#### ✅ Kwaliteitstoetsing")
        try:
            from ui.components.validation_view import render_validation_detailed_list

            render_validation_detailed_list(
                validation_result,
                key_prefix="gen",
                show_toggle=True,
                gate=(
                    validation_result.get("acceptance_gate")
                    if isinstance(validation_result, dict)
                    else None
                ),
            )
        except Exception as e:
            st.error(f"Validatiesectie kon niet worden gerenderd: {e!s}")

    def _extract_rule_id_from_line(self, line: str) -> str:
        """Haal regelcode (bv. CON-01) heuristisch uit een weergegeven lijn."""
        try:
            import re as _re

            m = _re.search(r"([A-Z]{2,5}(?:[-_][A-Z0-9]+)+)", str(line))
            return m.group(1) if m else ""
        except Exception:
            return ""

    def _rule_sort_key(self, rule_id: str):
        """Groeperings- en sorteersleutel voor regelcodes.

        Volgorde van groepen: CON → ESS → STR → INT → SAM → ARAI → VER → VAL → overige.
        Binnen een groep sorteren we op nummer indien aanwezig (01, 02, ...),
        daarna op volledige code voor stabiele weergave.
        """
        rid = (rule_id or "").upper().replace("_", "-")
        prefix = rid.split("-", 1)[0] if "-" in rid else rid[:4]
        order = {
            "CON": 0,
            "ESS": 1,
            "STR": 2,
            "INT": 3,
            "SAM": 4,
            "ARAI": 5,
            "VER": 6,
            "VAL": 7,
        }
        grp = order.get(prefix, 99)
        # Probeer een numeriek onderdeel na de eerste '-' te parsen
        num = 9999
        try:
            tail = rid.split("-", 1)[1] if "-" in rid else ""
            # Neem eerste aaneengesloten cijferreeks als nummer
            import re as _re

            m = _re.search(r"(\d+)", tail)
            if m:
                num = int(m.group(1))
        except Exception:
            num = 9999
        return (grp, num, rid)

    def _build_rule_hint_markdown(self, rule_id: str) -> str:
        """Bouw korte hint-uitleg voor een toetsregel uit JSON en standaardtekst.

        Toont:
        - Wat toetst de regel (uitleg/toetsvraag)
        - Optioneel voorbeelden (goed/fout) als bullets
        - Link naar uitgebreide handleiding
        """
        try:
            import json as _json
            from pathlib import Path

            rules_dir = Path("src/toetsregels/regels")
            json_path = rules_dir / f"{rule_id}.json"
            if not json_path.exists():
                alt = rule_id.replace("_", "-")
                json_path = rules_dir / f"{alt}.json"

            name = explanation = ""
            good = bad = []
            if json_path.exists():
                data = _json.loads(json_path.read_text(encoding="utf-8"))
                name = str(data.get("naam") or "").strip()
                explanation = str(
                    data.get("uitleg") or data.get("toetsvraag") or ""
                ).strip()
                good = list(data.get("goede_voorbeelden") or [])
                bad = list(data.get("foute_voorbeelden") or [])

            lines = []
            title = f"**{rule_id}** — {name}" if name else f"**{rule_id}**"
            lines.append(title)
            if explanation:
                lines.append(f"Wat toetst: {explanation}")
            if good:
                lines.append("\nGoed voorbeeld:")
                lines.extend([f"- {g}" for g in good[:2]])
            if bad:
                lines.append("\nFout voorbeeld:")
                lines.extend([f"- {b}" for b in bad[:2]])
            lines.append(
                "\nMeer uitleg: [Validatieregels (CON-01 e.a.)](docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )
            return "\n".join(lines)
        except Exception:
            return (
                "Meer uitleg: [Validatieregels (CON-01 e.a.)]"
                "(docs/handleidingen/gebruikers/uitleg-validatieregels.md)"
            )

    def _use_existing_definition(self, definitie: DefinitieRecord):
        """Gebruik bestaande definitie."""
        SessionStateManager.set_value("selected_definition", definitie)

    # ============ UI-private utilities (géén aparte helpers/module) ============
    def _get_current_text_and_begrip(self) -> tuple[str, str]:
        """Lees huidige definitietekst/begrip uit UI-state (best effort)."""
        try:
            text = ensure_string(
                SessionStateManager.get_value("current_definition_text", "")
            )
            begrip = ensure_string(SessionStateManager.get_value("current_begrip", ""))
            return text, begrip
        except Exception:
            return "", ""

    def _compute_text_metrics(self, text: str) -> dict[str, int]:
        """Kleine metrics voor pass-rationales (UI-only)."""
        t = ensure_string(text)
        words = len(t.split()) if t else 0
        chars = len(t)
        commas = t.count(",")
        return {"words": words, "chars": chars, "commas": commas}

    def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
        """Beknopte reden waarom regel geslaagd is (heuristiek, UI-only)."""
        rid = ensure_string(rule_id).upper()
        m = self._compute_text_metrics(text)
        w, c, cm = m.get("words", 0), m.get("chars", 0), m.get("commas", 0)

        try:
            if rid == "VAL-EMP-001":
                return f"Niet leeg (tekens={c} > 0)." if c > 0 else ""
            if rid == "VAL-LEN-001":
                return (
                    f"Lengte OK: {w} woorden ≥ 5 en {c} tekens ≥ 15."
                    if (w >= 5 and c >= 15)
                    else ""
                )
            if rid == "VAL-LEN-002":
                return (
                    f"Lengte OK: {w} ≤ 80 en {c} ≤ 600."
                    if (w <= 80 and c <= 600)
                    else ""
                )
            if rid == "ESS-CONT-001":
                return f"Essentie aanwezig: {w} woorden ≥ 6." if w >= 6 else ""
            if rid == "CON-CIRC-001":
                gb = ensure_string(begrip)
                if gb:
                    found = re.search(
                        rf"\b{re.escape(gb)}\b", ensure_string(text), re.IGNORECASE
                    )
                    return (
                        "Begrip niet in tekst (geen exacte match)." if not found else ""
                    )
                return "Begrip niet opgegeven."
            if rid == "STR-TERM-001":
                return (
                    "Verboden term niet aangetroffen ('HTTP protocol')."
                    if "HTTP protocol" not in ensure_string(text)
                    else ""
                )
            if rid == "STR-ORG-001":
                redund = bool(
                    re.search(
                        r"\bsimpel\b.*\bcomplex\b|\bcomplex\b.*\bsimpel\b",
                        ensure_string(text),
                        re.IGNORECASE,
                    )
                )
                return (
                    "Geen lange komma-zin (>300 tekens en ≥6 komma's) en geen redundantiepatroon."
                    if not (c > 300 and cm >= 6) and not redund
                    else ""
                )
            if rid == "ESS-02":
                return "Eenduidige ontologische marker aanwezig."
            if rid == "CON-01":
                return "Context niet letterlijk benoemd; geen duplicaat gedetecteerd."
            if rid in {"ESS-03", "ESS-04", "ESS-05"}:
                return "Vereist element herkend (heuristiek)."
        except Exception:
            return ""

        return "Geen issues gemeld door validator."

    # (Verouderde util-methodes voor aparte expander verwijderd)

    def _get_rule_display_and_explanation(self, rule_id: str) -> tuple[str, str]:
        """Haal naam/uitleg uit JSON wanneer beschikbaar; anders korte fallback.

        - Leest best-effort `src/toetsregels/regels/<RULE>.json`
        - Valt terug op ingebouwde korte omschrijving per bekende basisregel
        - Geen externe helpers; alles local en cached in memory per render
        """
        # 1) Probeer JSON (best-effort)
        try:
            rules_dir = Path("src/toetsregels/regels")
            json_path = rules_dir / f"{rule_id}.json"
            if not json_path.exists():
                # Sommige ID's gebruiken underscore in id-veld; bestandsnaam is met koppelteken
                # Probeer varianten (zonder effect als al bestond)
                alt = rule_id.replace("_", "-")
                json_path = rules_dir / f"{alt}.json"
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                name = str(data.get("naam") or "").strip()
                explanation = str(
                    data.get("uitleg") or data.get("toetsvraag") or ""
                ).strip()
                if name or explanation:
                    return name, explanation
        except Exception:
            pass

        # 2) Fallback mapping (kernregels) — kort en helder
        fallback = {
            "VAL-EMP-001": "Controleert of de definitietekst niet leeg is.",
            "VAL-LEN-001": "Minimale lengte (woorden/tekens) voor voldoende informatiedichtheid.",
            "VAL-LEN-002": "Maximale lengte om overdadigheid te voorkomen.",
            "ESS-CONT-001": "Essentiële inhoud aanwezig (niet te summier).",
            "CON-CIRC-001": "Detecteert of het begrip letterlijk in de definitie voorkomt.",
            "STR-TERM-001": "Terminologiekwesties (bijv. 'HTTP-protocol' i.p.v. 'HTTP protocol').",
            "STR-ORG-001": "Lange, komma-rijke zinnen of redundantie/tegenstrijdigheid.",
            "ESS-02": "Eenduidige ontologische marker (type/particulier/proces/resultaat).",
            "CON-01": "Context niet letterlijk benoemen; waarschuwt bij dubbele context.",
        }
        return "", fallback.get(rule_id, "Geen beschrijving beschikbaar.")

    def _edit_existing_definition(self, definitie: DefinitieRecord):
        """Bewerk bestaande definitie."""
        # Zet doel definitie en navigeer programmatic naar radio-tab 'edit'
        SessionStateManager.set_value("editing_definition_id", definitie.id)
        SessionStateManager.set_value("active_tab", "edit")
        st.success("✏️ Bewerk-tab geopend — laden van definitie…")
        st.rerun()

    def _edit_definition(self, definitie: DefinitieRecord):
        """Bewerk gegenereerde definitie."""
        st.info("🔄 Edit functionality coming soon...")

    def _submit_for_review(self, definitie: DefinitieRecord):
        """Submit definitie voor expert review via DefinitionWorkflowService."""
        try:
            # US-072: Use DefinitionWorkflowService for combined workflow and repository actions
            service_container = SessionStateManager.get_value("service_container")
            if service_container is not None:
                workflow_service = service_container.definition_workflow_service()
            else:
                # Fallback to container method
                from ui.cached_services import get_cached_service_container

                container = get_cached_service_container()
                workflow_service = container.definition_workflow_service()

            # Submit for review using the new consolidated service
            result = workflow_service.submit_for_review(
                definition_id=definitie.id,
                user="web_user",
                notes="Submitted via web interface",
            )

            if result.success:
                st.success("✅ Definitie ingediend voor review")
                # Log the workflow change for audit purposes
                logger.info(
                    f"Definition {definitie.id} submitted for review by {result.updated_by}"
                )
            else:
                st.error(f"❌ {result.error_message or 'Kon status niet wijzigen'}")
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
        # Debug logging point D - Rendering voorbeelden in UI
        try:
            import uuid

            from utils.voorbeelden_debug import DEBUG_ENABLED, debugger

            if DEBUG_ENABLED:
                render_gen_id = str(uuid.uuid4())[:8]
                debugger.log_point(
                    "D",
                    render_gen_id,
                    location="definition_generator_tab._render_voorbeelden_section",
                    voorbeelden_keys=list(voorbeelden.keys()) if voorbeelden else [],
                    voorbeelden_counts=(
                        {
                            k: len(v) if isinstance(v, list) else 1
                            for k, v in voorbeelden.items()
                        }
                        if voorbeelden
                        else {}
                    ),
                )
                debugger.log_session_state(render_gen_id, "D")
        except ImportError:
            # Debug module not available, continue without logging
            pass

        st.markdown("#### 📚 Gegenereerde Content")

        # Debug: toon wat er exact in voorbeelden zit
        with st.expander("🔍 Debug: Voorbeelden Content", expanded=False):
            st.json(voorbeelden)

            # Show debug status if enabled
            try:
                from utils.voorbeelden_debug import DEBUG_ENABLED

                if DEBUG_ENABLED:
                    st.info("📊 Debug logging enabled (DEBUG_EXAMPLES=true)")
                    if "render_gen_id" in locals():
                        st.caption(f"Generation ID: {render_gen_id}")
            except ImportError:
                pass

        # Uniforme rendering van voorbeelden (generator-stijl met expanders)
        from ui.components.examples_renderer import render_examples_expandable

        render_examples_expandable(voorbeelden)

    def _trigger_regeneration_with_category(
        self,
        begrip: str,
        new_category: str,
        old_category: str,
        saved_record: DefinitieRecord,
    ):
        """Deprecated: Regeneration service removed (US-445). Use category dropdown + generate."""
        st.info(
            f"💡 Om te regenereren met categorie '{new_category}': "
            f"Ga naar Generator tab, wijzig categorie dropdown, en klik 'Genereer Definitie'"
        )

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
        """Trigger direct regeneration with new ontological category.

        Note: Duplicate check will run with the new category. If a definition with
        the same begrip + context + new_category already exists, user will be warned.
        """
        from ui.session_state import SessionStateManager

        # Set manual category override
        SessionStateManager.set_value("manual_ontological_category", new_category)

        # Clear any previous generation results
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")
        SessionStateManager.clear_value("last_check_result")

        # Clear force flags - let duplicate check run normally with new category
        options = SessionStateManager.get_value("generation_options", {})
        options.pop("force_generate", None)
        options.pop("force_duplicate", None)
        SessionStateManager.set_value("generation_options", options)

        # Trigger auto-generation
        SessionStateManager.set_value("trigger_auto_generation", True)

        st.success(f"✅ Regeneratie gestart met categorie '{new_category}'!")
        st.rerun()

    def _extract_context_from_generation_result(
        self, generation_result: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Extract context information from previous generation result."""
        # Try to get context from various sources in the generation result
        context_dict: dict[str, list[str]] = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
        }

        # Extract from stored context if available
        if "document_context" in generation_result:
            doc_context = generation_result["document_context"]
            if isinstance(doc_context, dict):
                for key in context_dict:
                    if key in doc_context:
                        context_dict[key] = doc_context[key]

        # Fallback: extract from session state
        from ui.session_state import SessionStateManager

        for context_type, context_value in list(context_dict.items()):
            session_value = SessionStateManager.get_value(f"{context_type}_context", [])
            if session_value and not context_value:
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
            result = agent_result.get(
                "definitie_gecorrigeerd", agent_result.get("definitie", "")
            )
            return result if isinstance(result, str) else ""
        # Legacy format
        legacy_result = getattr(agent_result, "final_definitie", "")
        return legacy_result if isinstance(legacy_result, str) else ""

    def _clear_results(self):
        """Wis alle resultaten."""
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("last_generation_result")
        SessionStateManager.clear_value("selected_definition")

    def _show_settings_modal(self):
        """Toon instellingen modal."""
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
