"""Handler voor definitie generatie en duplicate-check logica.

Geextraheerd uit TabbedInterface (DEF-141) als onderdeel van de
god-object opsplitsing. Bevat alle business logic voor het genereren
van definities en het controleren op duplicaten.

NOTE: De publieke methods accepteren optionele ``_st`` en ``_sm`` parameters
zodat TabbedInterface-delegates de module-level symbolen kunnen doorgeven die
tests patchen (``ui.tabbed_interface.st`` / ``ui.tabbed_interface.SessionStateManager``).
Bij direct gebruik (buiten tests) worden de standaard imports gebruikt.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any, cast

import streamlit as _default_st

from document_processing.document_processor import get_document_processor
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker
from ui.session_state import SessionStateManager as _DefaultSM
from utils.type_helpers import ensure_dict

# Hybrid context imports - optionele module voor hybride context verrijking
try:
    import importlib.util

    HYBRID_CONTEXT_AVAILABLE = (
        importlib.util.find_spec("hybrid_context.hybrid_context_engine") is not None
    )
except ImportError:
    HYBRID_CONTEXT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DefinitionGenerationHandler:
    """Handle definitie generatie en duplicate-check flows.

    Constructor parameters komen vanuit TabbedInterface.__init__ zodat
    deze handler dezelfde services deelt als de orchestrator.
    """

    def __init__(self, checker: DefinitieChecker, definition_service, repository):
        self.checker = checker
        self.definition_service = definition_service
        self.repository = repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_definition_generation(
        self,
        begrip: str,
        context_data: dict[str, Any],
        *,
        _st=None,
        _sm=None,
    ):
        """Handle definitie generatie met voorafgaande duplicate-check en keuze.

        Args:
            _st: Streamlit module override (voor testbaarheid via delegate).
            _sm: SessionStateManager override (voor testbaarheid via delegate).
        """
        st = _st if _st is not None else _default_st
        SessionStateManager = _sm if _sm is not None else _DefaultSM
        try:
            with st.spinner("🔄 Genereren van definitie met hybride context..."):
                # EPIC-010: Consistente context variabelen voor alle 3 types
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                wet_context = context_data.get("wettelijke_basis", [])

                # Extract primary context items
                primary_org = org_context[0] if org_context else ""
                primary_jur = jur_context[0] if jur_context else ""

                # SINGLE PATH: Validate that classification was performed
                # Classification must happen in _render_category_preview() before generation

                # Check voor handmatige override (hoogste prioriteit)
                manual_category = SessionStateManager.get_value(
                    "manual_ontological_category"
                )

                if manual_category:
                    # Gebruik handmatige override
                    category_map = {
                        "type": OntologischeCategorie.TYPE,
                        "proces": OntologischeCategorie.PROCES,
                        "resultaat": OntologischeCategorie.RESULTAAT,
                        "exemplaar": OntologischeCategorie.EXEMPLAAR,
                    }
                    auto_categorie = category_map.get(
                        manual_category.lower(), OntologischeCategorie.PROCES
                    )
                    category_reasoning = (
                        f"Handmatig gekozen door gebruiker: {manual_category}"
                    )
                    category_scores = {"manual_override": 1.0}
                    logger.info(
                        f"Gebruik handmatige categorie override: {manual_category}"
                    )
                else:
                    # Gebruik pre-geclassificeerde categorie (REQUIRED)
                    determined_category = SessionStateManager.get_value(
                        "determined_category"
                    )

                    if not determined_category:
                        # GEEN FALLBACK: Pre-classificatie is VERPLICHT
                        st.error(
                            "❌ Ontologische categorie is niet bepaald. "
                            "Scroll naar boven om de categorie te "
                            "zien/aanpassen voordat je genereert."
                        )
                        logger.error(
                            "Generatie geblokkeerd: geen pre-classificatie beschikbaar. "
                            "Gebruiker moet categorie preview zien voordat generatie."
                        )
                        return

                    # Converteer string naar OntologischeCategorie enum
                    category_map = {
                        "TYPE": OntologischeCategorie.TYPE,
                        "PROCES": OntologischeCategorie.PROCES,
                        "RESULTAAT": OntologischeCategorie.RESULTAAT,
                        "EXEMPLAAR": OntologischeCategorie.EXEMPLAAR,
                    }
                    # DEF-138 FIX: uppercase determined_category voor case-insensitive match
                    auto_categorie = category_map.get(
                        (
                            determined_category.upper()
                            if determined_category
                            else "PROCES"
                        ),
                        OntologischeCategorie.PROCES,
                    )
                    category_reasoning = SessionStateManager.get_value(
                        "category_reasoning", ""
                    )
                    category_scores = SessionStateManager.get_value(
                        "category_scores", {}
                    )
                    logger.info(
                        f"Gebruik pre-geclassificeerde categorie: {determined_category}"
                    )

                # Krijg document context en selected document IDs
                document_context = self._get_document_context(_sm=_sm)
                selected_doc_ids = SessionStateManager.get_value(
                    "selected_documents", []
                )

                # DUPLICATE GATE: Voer duplicate-check uit vóór generatie (tenzij geforceerd)
                options = ensure_dict(
                    SessionStateManager.get_value("generation_options", {})
                )
                is_forced = bool(options.get("force_generate"))

                # Gebruik de automatisch bepaalde categorie voor nauwkeuriger check
                if not is_forced:
                    # DB repository bewaart org/jur als JSON-string; vergelijk exact daarop
                    import json as _json

                    primary_org = _json.dumps(
                        sorted(org_context or []), ensure_ascii=False
                    )
                    primary_jur = _json.dumps(
                        sorted(jur_context or []), ensure_ascii=False
                    )
                    wet_norm = sorted({str(x).strip() for x in (wet_context or [])})
                    check_result = self.checker.check_before_generation(
                        begrip=begrip,
                        organisatorische_context=primary_org,
                        juridische_context=primary_jur,
                        categorie=auto_categorie,
                        wettelijke_basis=wet_norm,
                    )

                    # Als we NIET mogen doorgaan, toon keuzes en stop generatie
                    if check_result.action != CheckAction.PROCEED:
                        SessionStateManager.set_value("last_check_result", check_result)
                        st.warning("⚠️ Bestaande definitie gevonden. Kies een optie:")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(
                                "👁️ Toon bestaande definitie",
                                key="btn_show_existing",
                            ):
                                if check_result.existing_definitie:
                                    SessionStateManager.set_value(
                                        "selected_definition",
                                        check_result.existing_definitie,
                                    )
                                # Wis eventuele vorige generatie-output
                                SessionStateManager.clear_value(
                                    "last_generation_result"
                                )
                                st.rerun()
                        with c2:
                            if st.button(
                                "🚀 Genereer nieuwe definitie",
                                key="btn_force_generate",
                            ):
                                # Forceer generatie en duid duplicaat als geaccepteerd
                                options["force_generate"] = True
                                options["force_duplicate"] = True
                                SessionStateManager.set_value(
                                    "generation_options", options
                                )
                                # Wis duplicate-check resultaat
                                try:
                                    SessionStateManager.clear_value("last_check_result")
                                    SessionStateManager.clear_value(
                                        "selected_definition"
                                    )
                                except (KeyError, AttributeError) as e:
                                    logger.debug(
                                        "Could not clear session state during "
                                        f"force generate: {e}"
                                    )
                                # Ga door met geforceerde generatie (buiten gate)
                            else:
                                # Niet gekozen → stop huidige generatie
                                return

                # Check of hybrid context gebruikt moet worden
                use_hybrid = HYBRID_CONTEXT_AVAILABLE and (
                    len(selected_doc_ids) > 0
                    or (
                        document_context
                        and document_context.get("document_count", 0) > 0
                    )
                )

                if use_hybrid:
                    st.info(
                        "🔄 Hybrid context activief - "
                        "combineer document en web context..."
                    )

                # Altijd V2-servicepad gebruiken (geen legacy fallback)
                from ui.helpers.async_bridge import run_async

                # Haal actuele generation options op (kan force flags bevatten)
                options = ensure_dict(
                    SessionStateManager.get_value("generation_options", {})
                )

                # EPIC-018: bouw een samenvatting van documentcontext voor de service
                doc_summary = None
                if document_context and document_context.get("document_count", 0) > 0:
                    doc_summary = self._build_document_context_summary(document_context)
                # EPIC-018/US-229: bouw snippets op basis van begrip
                doc_snippets = []
                if selected_doc_ids:
                    # Config via env
                    try:
                        per_doc = int(os.getenv("DOCUMENT_SNIPPETS_PER_DOC", "4"))
                    except ValueError as e:
                        logger.warning(
                            "Invalid DOCUMENT_SNIPPETS_PER_DOC value, "
                            f"using default 4: {e}"
                        )
                        per_doc = 4
                    try:
                        window_chars = int(os.getenv("SNIPPET_WINDOW_CHARS", "280"))
                    except ValueError as e:
                        logger.warning(
                            "Invalid SNIPPET_WINDOW_CHARS value, "
                            f"using default 280: {e}"
                        )
                        window_chars = 280

                    doc_snippets = self._build_document_snippets(
                        begrip=begrip,
                        selected_doc_ids=selected_doc_ids,
                        max_snippets_total=len(selected_doc_ids) * max(1, per_doc),
                        per_doc_max=per_doc,
                        snippet_window=window_chars,
                    )

                service_result = run_async(
                    self.definition_service.generate_definition(
                        begrip=begrip,
                        context_dict={
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": wet_context,
                        },
                        organisatie=primary_org,
                        categorie=auto_categorie,
                        ufo_categorie=(
                            SessionStateManager.get_value("ufo_categorie") or None
                        ),
                        options={
                            k: v
                            for k, v in options.items()
                            if k in ("force_generate", "force_duplicate")
                        },
                        document_context=doc_summary,
                        document_snippets=doc_snippets,
                    ),
                    timeout=120,
                )

                # Converteer naar checker formaat voor UI compatibility
                check_result = None
                agent_result = service_result

                # Voor auto-load in Bewerk-tab
                saved_record = None
                saved_definition_id = None
                if isinstance(service_result, dict) and service_result.get("success"):
                    saved_definition_id = service_result.get("saved_definition_id")

                # Capture voorbeelden prompts voor debug
                voorbeelden_prompts = None
                if isinstance(agent_result, dict) and (
                    agent_result.get("definitie_gecorrigeerd")
                    or agent_result.get("definitie")
                ):
                    try:
                        from ui.components.prompt_debug_section import (
                            capture_voorbeelden_prompts,
                        )

                        context_dict = {
                            "organisatorisch": org_context,
                            "juridisch": jur_context,
                            "wettelijk": wet_context,
                        }

                        definitie_for_prompts = agent_result.get(
                            "definitie_gecorrigeerd"
                        ) or agent_result.get("definitie", "")
                        voorbeelden_prompts = capture_voorbeelden_prompts(
                            begrip=begrip,
                            definitie=definitie_for_prompts,
                            context_dict=context_dict,
                        )
                    except Exception as e:
                        logger.warning(f"Could not capture example prompts: {e}")

                # Debug logging point C - Pre-store
                if os.getenv("DEBUG_EXAMPLES"):
                    logger.info(
                        "[EXAMPLES-C] Pre-store | gen_id=%s | "
                        "voorbeelden=%s | counts=%s",
                        (
                            agent_result.get("metadata", {}).get("generation_id")
                            if isinstance(agent_result, dict)
                            else "NO_ID"
                        ),
                        (
                            "present"
                            if isinstance(agent_result, dict)
                            and agent_result.get("voorbeelden")
                            else "missing"
                        ),
                        {
                            k: len(v) if isinstance(v, list | str) else "INVALID"
                            for k, v in (
                                agent_result.get("voorbeelden", {})
                                if isinstance(agent_result, dict)
                                else {}
                            ).items()
                        },
                    )

                # Store results voor display in tabs
                SessionStateManager.set_value(
                    "last_generation_result",
                    {
                        "begrip": begrip,
                        "check_result": check_result,
                        "agent_result": agent_result,
                        "saved_record": saved_record,
                        "saved_definition_id": saved_definition_id,
                        "determined_category": auto_categorie.value,
                        "category_reasoning": category_reasoning,
                        "category_scores": category_scores,
                        "document_context": document_context,
                        "voorbeelden_prompts": voorbeelden_prompts,
                        "timestamp": datetime.now(UTC),
                    },
                )

                # Koppel gegenereerde definitie aan edit tab voor auto-load
                logger.info(
                    "DEBUG: saved_record = %s, type = %s",
                    saved_record,
                    type(saved_record),
                )
                if saved_record:
                    logger.info(
                        "DEBUG: saved_record has id? %s",
                        hasattr(saved_record, "id"),
                    )
                    if hasattr(saved_record, "id"):
                        logger.info("DEBUG: saved_record.id = %s", saved_record.id)

                # Bepaal te openen definitie-ID voor de Bewerk-tab
                target_edit_id = None
                if saved_definition_id:
                    target_edit_id = int(saved_definition_id)
                elif saved_record and hasattr(saved_record, "id"):
                    target_edit_id = int(saved_record.id)

                if target_edit_id:
                    SessionStateManager.set_value(
                        "editing_definition_id", target_edit_id
                    )
                    SessionStateManager.set_value(
                        "edit_organisatorische_context", org_context
                    )
                    SessionStateManager.set_value(
                        "edit_juridische_context", jur_context
                    )
                    SessionStateManager.set_value("edit_wettelijke_basis", wet_context)
                    logger.info(
                        "Definition %s prepared for edit tab with contexts: "
                        "org=%s items, jur=%s items, wet=%s items",
                        target_edit_id,
                        len(org_context),
                        len(jur_context),
                        len(wet_context),
                    )

                # Debug logging point C2 - Post-store
                if os.getenv("DEBUG_EXAMPLES"):
                    stored = SessionStateManager.get_value("last_generation_result", {})
                    stored_agent_result = stored.get("agent_result", {})
                    logger.info(
                        "[EXAMPLES-C2] Post-store | gen_id=%s | "
                        "stored.voorbeelden=%s",
                        (
                            stored_agent_result.get("metadata", {}).get("generation_id")
                            if isinstance(stored_agent_result, dict)
                            else "NO_ID"
                        ),
                        (
                            "present"
                            if isinstance(stored_agent_result, dict)
                            and stored_agent_result.get("voorbeelden")
                            else "missing"
                        ),
                    )

                # Reset force flag na generatie
                try:
                    if options.get("force_generate"):
                        options.pop("force_generate", None)
                        SessionStateManager.set_value("generation_options", options)
                except (KeyError, AttributeError) as e:
                    logger.debug(f"Could not reset force_generate flag: {e}")

                # V2 validation is already included in agent_result
                if isinstance(agent_result, dict):
                    validation_details = agent_result.get("validation_details", {})
                    logger.info(
                        "V2 validation available - overall_score: %s, "
                        "violations: %s, passed_rules: %s",
                        validation_details.get("overall_score", 0.0),
                        len(validation_details.get("violations", [])),
                        len(validation_details.get("passed_rules", [])),
                    )

                # Toon document context info als gebruikt
                if document_context and document_context.get("document_count", 0) > 0:
                    st.success(
                        "✅ Definitie gegenereerd met context van "
                        f"{document_context['document_count']} document(en)! "
                        "Bekijk resultaten in de 'Definitie Generatie' tab."
                    )
                else:
                    st.success(
                        "✅ Definitie succesvol gegenereerd! "
                        "Bekijk resultaten in de 'Definitie Generatie' tab."
                    )

        except Exception as e:
            st.error(f"❌ Fout bij generatie: {e!s}")
            logger.error(f"Global generation failed: {e}", exc_info=True)

    def handle_duplicate_check(
        self,
        begrip: str,
        context_data: dict[str, Any],
        *,
        _st=None,
        _sm=None,
    ):
        """Handle duplicate check vanaf hoofdniveau."""
        st = _st if _st is not None else _default_st
        SessionStateManager = _sm if _sm is not None else _DefaultSM
        try:
            with st.spinner("🔍 Controleren op duplicates..."):
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])
                wet_context = context_data.get("wettelijke_basis", [])

                import json as _json

                primary_org = _json.dumps(sorted(org_context or []), ensure_ascii=False)
                primary_jur = _json.dumps(sorted(jur_context or []), ensure_ascii=False)
                wet_norm = sorted({str(x).strip() for x in (wet_context or [])})

                check_result = self.checker.check_before_generation(
                    begrip=begrip,
                    organisatorische_context=primary_org,
                    juridische_context=primary_jur,
                    categorie=OntologischeCategorie.PROCES,  # Default
                    wettelijke_basis=wet_norm,
                )

                SessionStateManager.set_value("last_check_result", check_result)
                st.success(
                    "✅ Duplicate check voltooid! "
                    "Bekijk resultaten in de 'Definitie Generatie' tab."
                )

        except Exception as e:
            st.error(f"❌ Fout bij duplicate check: {e!s}")
            logger.error(f"Global duplicate check failed: {e}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_document_context(self, *, _sm=None) -> dict[str, Any] | None:
        """Krijg document context voor definitie generatie."""
        SessionStateManager = _sm if _sm is not None else _DefaultSM
        try:
            selected_docs = SessionStateManager.get_value("selected_documents", [])
            if not selected_docs:
                return None

            processor = get_document_processor()
            aggregated_context = processor.get_aggregated_context(selected_docs)

            if aggregated_context["document_count"] == 0:
                return None

            return cast(dict[str, Any], aggregated_context)

        except Exception as e:
            logger.error(f"Fout bij ophalen document context: {e}")
            return None

    def _build_document_context_summary(self, aggregated: dict[str, Any]) -> str:
        """Bouw een compacte samenvatting uit geaggregeerde documentcontext."""
        try:
            parts: list[str] = []
            doc_cnt = int(aggregated.get("document_count", 0) or 0)
            total_len = int(aggregated.get("total_text_length", 0) or 0)
            if doc_cnt > 0:
                parts.append(f"Docs: {doc_cnt} | Tekst: {total_len} chars")

            kws = list(aggregated.get("aggregated_keywords", []) or [])[:10]
            if kws:
                parts.append("Keywords: " + ", ".join(kws))

            concepts = list(aggregated.get("aggregated_concepts", []) or [])[:5]
            if concepts:
                parts.append("Concepten: " + ", ".join(concepts))

            legal = list(aggregated.get("aggregated_legal_refs", []) or [])[:5]
            if legal:
                parts.append("Juridisch: " + ", ".join(legal))

            hints = list(aggregated.get("aggregated_context_hints", []) or [])[:3]
            if hints:
                parts.append("Hints: " + "; ".join(hints))

            return " | ".join(parts)
        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Could not build document context summary: {e}")
            return ""

    def _build_document_snippets(
        self,
        begrip: str,
        selected_doc_ids: list[str],
        max_snippets_total: int | None = None,
        per_doc_max: int = 4,
        snippet_window: int = 280,
    ) -> list[dict[str, Any]]:
        """Zoek op begrip in geselecteerde documenten en bouw korte snippets."""
        try:
            if not begrip or not selected_doc_ids:
                return []

            processor = get_document_processor()
            begrip_lower = str(begrip).strip().lower()

            # Stel totaal-limiet af op aantal documenten x per-doc-limiet
            if max_snippets_total is None:
                max_snippets_total = max(
                    0, int(len(selected_doc_ids) * max(1, per_doc_max))
                )

            snippets: list[dict[str, Any]] = []
            for doc_id in selected_doc_ids:
                doc = processor.get_document_by_id(doc_id)
                if not doc or not getattr(doc, "extracted_text", None):
                    continue

                text = doc.extracted_text
                haystack = text.lower()
                # Zoek meerdere matches (max per_doc_max)
                try:
                    import re

                    count_for_doc = 0
                    for m in re.finditer(re.escape(begrip_lower), haystack):
                        if len(snippets) >= max_snippets_total:
                            break
                        if count_for_doc >= max(1, per_doc_max):
                            break

                        idx = m.start()
                        start = max(0, idx - snippet_window // 2)
                        end = min(
                            len(text),
                            idx + len(begrip) + snippet_window // 2,
                        )
                        raw = text[start:end].replace("\n", " ").strip()

                        # Bepaal bronvermelding binnen document
                        citation_label = None
                        try:
                            mime = getattr(doc, "mime_type", "") or ""
                            if mime == "application/pdf":
                                page_num = text.count("\f", 0, idx) + 1
                                citation_label = f"p. {page_num}"
                            elif (
                                mime == "application/vnd.openxmlformats-"
                                "officedocument.wordprocessingml.document"
                            ):
                                para_num = text.count("\n", 0, idx) + 1
                                citation_label = f"¶ {para_num}"
                        except (AttributeError, IndexError):
                            citation_label = None

                        snippet = {
                            "provider": "documents",
                            "title": getattr(doc, "filename", "document"),
                            "filename": getattr(doc, "filename", None),
                            "doc_id": getattr(doc, "id", None),
                            "snippet": raw,
                            "score": 1.0,
                            "used_in_prompt": True,
                            "citation_label": citation_label,
                        }
                        snippets.append(snippet)
                        count_for_doc += 1
                        if len(snippets) >= max_snippets_total:
                            break
                except (re.error, ValueError, IndexError) as e:
                    logger.debug(
                        f"Skipping document due to snippet extraction error: {e}"
                    )
                    continue

            return snippets[:max_snippets_total]
        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Could not build document snippets: {e}")
            return []
