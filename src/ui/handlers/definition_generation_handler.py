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
import re
from datetime import UTC, datetime
from typing import Any, cast

import streamlit as _default_st

from document_processing.document_processor import get_document_processor
from domain.categorie_herkomst import HERKOMST_HANDMATIG, HERKOMST_MODEL
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker
from ui.helpers.betekenisconflict import (
    HERSTELBARE_VERDUIDELIJKINGSFOUTEN,
    KEY_AFWIJZING,
    KEY_OPEN,
    KEY_VERZONDEN,
    invoer_vingerafdruk,
    open_conflict_uit,
    rag_selectie_voor_vingerafdruk,
    verzonden_verduidelijking_voor,
)
from ui.helpers.categorie_weergave import generatiecategorie_van
from ui.session_state import SessionStateManager as _DefaultSM
from utils.type_helpers import ensure_dict, ensure_string

# Hybrid context imports - optionele module voor hybride context verrijking

logger = logging.getLogger(__name__)

# DEF-553: grens-validatie van het begrip vóór generatie. De quality-gate
# toetst alleen de gegenereerde definitietekst, niet het begrip zelf —
# zonder deze check belandt betekenisloze invoer als concept in de database.
# De letter-subranges À-Ö/Ø-ö/ø-ÿ sluiten × (U+00D7) en ÷ (U+00F7) uit;
# ":" is toegestaan voor wetsartikel-notatie (bv. "artikel 6:162 BW").
_BEGRIP_MAX_LENGTH = 100
_BEGRIP_HAS_LETTER = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
_BEGRIP_ALLOWED_CHARS = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ&/():.,'’\- ]+")


def validate_begrip_input(begrip: str) -> str | None:
    """Valideer een begrip op de invoergrens.

    Returns:
        Gebruikersgerichte afwijsreden, of None als het begrip geldig is.
    """
    stripped = begrip.strip()
    if not stripped:
        return "voer eerst een begrip in"
    if len(stripped) > _BEGRIP_MAX_LENGTH:
        return f"het begrip is te lang (maximaal {_BEGRIP_MAX_LENGTH} tekens)"
    if not _BEGRIP_HAS_LETTER.search(stripped):
        return "het begrip moet minimaal één letter bevatten"
    if not _BEGRIP_ALLOWED_CHARS.fullmatch(stripped):
        return (
            "het begrip bevat ongeldige tekens; toegestaan zijn letters, "
            "cijfers, spaties en - & / ( ) : . , '"
        )
    return None


class DefinitionGenerationHandler:
    """Handle definitie generatie en duplicate-check flows.

    Constructor parameters komen vanuit TabbedInterface.__init__ zodat
    deze handler dezelfde services deelt als de orchestrator.
    """

    def __init__(
        self, checker: DefinitieChecker, definition_service: Any, repository: Any
    ) -> None:
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
        _st: Any = None,
        _sm: Any = None,
    ) -> None:
        """Handle definitie generatie met voorafgaande duplicate-check en keuze.

        Args:
            _st: Streamlit module override (voor testbaarheid via delegate).
            _sm: SessionStateManager override (voor testbaarheid via delegate).
        """
        st = _st if _st is not None else _default_st
        SessionStateManager = _sm if _sm is not None else _DefaultSM

        # DEF-553: wijs ongeldige begrippen af vóór er iets gegenereerd,
        # gevalideerd of opgeslagen wordt.
        afwijsreden = validate_begrip_input(begrip)
        if afwijsreden:
            st.error(f"❌ Generatie geweigerd: {afwijsreden}.")
            logger.warning("Generatie geweigerd: ongeldig begrip (%s)", afwijsreden)
            # DEF-622: ook een afgewezen aanvraag verbruikt de eenmalige
            # force-opties; anders raken ze de volgende, geldige aanvraag
            # (reviewbevinding D3).
            self._wis_force_opties(_sm=SessionStateManager)
            return
        # Genormaliseerd doorgeven: consistente sleutels voor duplicate-check
        # en opslag (de allowlist staat rand-spaties toe, opslag hoort ze niet).
        begrip = begrip.strip()

        # DEF-622 (B-01, besloten vervolg): zonder minimaal één inhoudelijke
        # contextwaarde geen duplicaatcontrole en geen modelaanroep, maar een
        # vraag om context. De harde grens staat in de orchestrator; dit is de
        # vroege, begrijpelijke melding in de UI.
        if not self._heeft_inhoudelijke_context(context_data):
            st.error(
                "❌ Generatie niet gestart: vul minimaal één contextwaarde in "
                "(organisatorische context, juridische context of wettelijke "
                "basis). De context hoort bij het record en stuurt de generatie."
            )
            logger.warning("Generatie niet gestart: geen context voor %r", begrip)
            self._wis_force_opties(_sm=SessionStateManager)
            return

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

                # DEF-751: een keuze of voorstel buiten de vier generatie-
                # categorieën viel hier stil terug op PROCES — en reisde zo
                # ook de duplicaatvoorcontrole en het model in. Nu stopt de
                # handler vóór checker en model met een begrijpelijke melding;
                # de echte waarde reist exact door. Herkomst (handmatig vs.
                # model) blijft alleen sessie-informatie, geen bevestiging.
                if manual_category:
                    # Gebruik handmatige override
                    auto_categorie = generatiecategorie_van(manual_category)
                    if auto_categorie is None:
                        self._weiger_categorie(
                            manual_category,
                            "handmatige keuze",
                            _st=st,
                            _sm=SessionStateManager,
                        )
                        return
                    category_reasoning = (
                        f"Handmatig gekozen door gebruiker: {manual_category}"
                    )
                    category_scores = {"manual_override": 1.0}
                    logger.info(
                        f"Gebruik handmatige categorie override: {manual_category}"
                    )
                else:
                    # Gebruik het pre-geclassificeerde voorstel, als dat er is
                    determined_category = SessionStateManager.get_value(
                        "determined_category"
                    )

                    if not determined_category:
                        # DEF-751 B2 (schemaversie 4): geen keuze en geen
                        # voorstel — bv. uitsluitend wettelijke basis als
                        # context, waarop de classifier niet draait — is geen
                        # blokkade en geen verzonnen PROCES: de generatie loopt
                        # labelvrij door (categorie None); de bestaande CON-01-
                        # contextguard hierboven blijft de inhoudelijke grens.
                        # Een werkelijk betekenisconflict is stap 2 (ESS-02).
                        auto_categorie = None
                        category_reasoning = ""
                        category_scores = {}
                        logger.info(
                            "Generatie zonder categorielabel voor %r: geen keuze "
                            "en geen voorstel",
                            begrip,
                        )
                    else:
                        # DEF-138: kastongevoelig; DEF-751: geen PROCES-fallback
                        auto_categorie = generatiecategorie_van(determined_category)
                        if auto_categorie is None:
                            self._weiger_categorie(
                                determined_category,
                                "voorgestelde categorie",
                                _st=st,
                                _sm=SessionStateManager,
                            )
                            return
                        category_reasoning = SessionStateManager.get_value(
                            "category_reasoning", ""
                        )
                        category_scores = SessionStateManager.get_value(
                            "category_scores", {}
                        )
                        logger.info(
                            "Gebruik pre-geclassificeerde categorie: %s",
                            determined_category,
                        )

                # Krijg document context en selected document IDs
                document_context = self._get_document_context(_st=st, _sm=_sm)
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
                            # DEF-622 (besluit 5): bewust naast een bestaande
                            # definitie genereren vraagt een reden voor de audit.
                            force_reden = (
                                st.text_input(
                                    "Reden om toch een nieuw concept te genereren",
                                    key="force_generate_reason",
                                )
                                or ""
                            ).strip()
                            if st.button(
                                "🚀 Genereer nieuwe definitie",
                                key="btn_force_generate",
                            ):
                                if not force_reden:
                                    st.warning(
                                        "Geef een reden op om toch een nieuw "
                                        "concept te genereren."
                                    )
                                    return
                                # Forceer generatie en duid duplicaat als geaccepteerd
                                options["force_generate"] = True
                                options["force_duplicate"] = True
                                options["force_duplicate_reason"] = force_reden
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

                # DEF-366: RAG collection selectie uit session state
                rag_collection_ids = SessionStateManager.get_value(
                    "rag_selected_collection_ids", None
                )

                # DEF-751 stap 2: de vingerafdruk van de volledige invoer.
                # Een eerder verzonden antwoord op een betekenisconflict
                # wordt alleen toegepast als het bij het open conflict én bij
                # precies deze invoer hoort; anders vervalt het met een
                # melding. Toepassen is eenmalig; het reist via het typed
                # veld, nooit via `options`. De RAG-selectie telt als de
                # gebruikerskeuze (standaard = None), niet als de lijst die de
                # selector bij het verschijnen zelf wegschrijft.
                vingerafdruk = invoer_vingerafdruk(
                    begrip=begrip,
                    organisatorische_context=org_context,
                    juridische_context=jur_context,
                    wettelijke_basis=wet_context,
                    categorie=auto_categorie.value if auto_categorie else None,
                    document_ids=selected_doc_ids,
                    rag_collection_ids=rag_selectie_voor_vingerafdruk(
                        SessionStateManager
                    ),
                )
                # Kopie van het verzonden antwoord: wordt teruggezet als de
                # generatie het antwoord zelf weigert (reviewcorrectie 1).
                verzonden_kopie = SessionStateManager.get_value(KEY_VERZONDEN)
                verduidelijking, afwijsreden = verzonden_verduidelijking_voor(
                    SessionStateManager, vingerafdruk
                )
                if afwijsreden:
                    st.info(f"ℹ️ {afwijsreden}")
                    logger.info("Betekenisverduidelijking vervallen: %s", afwijsreden)

                _response = run_async(
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
                            **{
                                k: v
                                for k, v in options.items()
                                if k
                                in (
                                    "force_generate",
                                    "force_duplicate",
                                    "force_duplicate_reason",
                                )
                            },
                            # DEF-751 B2: alleen het modelvoorstel reist als
                            # herkomst mee in de aanvraag (`model` +
                            # reasoning/scores). Een handmatige override is
                            # een keuzeactie en wordt ná de opslag via het
                            # expliciete commando vastgelegd
                            # (`_leg_handmatige_keuze_vast`) — nooit als
                            # generieke aanvraagclaim (herreview 2). Labelvrij
                            # (geen keuze, geen voorstel): geen herkomst.
                            **(
                                {
                                    "category_choice": self._keuze_invoer(
                                        category_reasoning, category_scores
                                    )
                                }
                                if auto_categorie is not None and not manual_category
                                else {}
                            ),
                        },
                        document_context=doc_summary,
                        document_snippets=doc_snippets,
                        rag_collection_ids=rag_collection_ids,
                        **(
                            {"betekenisverduidelijking": verduidelijking}
                            if verduidelijking
                            else {}
                        ),
                    ),
                    timeout=120,
                )
                # DEF-451: serialiseer het getypeerde response naar de canonieke UI-dict
                service_result = self.definition_service.to_ui_response(_response)

                # DEF-751 stap 2 (reviewcorrectie 1): weigerde de generatie
                # vóór het model om het verzonden antwoord of het prompt-
                # budget, dan gaat dat antwoord niet verloren: het conflict
                # blijft open, het antwoord blijft verzonden, de afwijzing
                # staat bij het antwoordveld en het vorige resultaat (het
                # conflict) blijft zichtbaar. De gebruiker past aan en verzendt
                # opnieuw.
                if (
                    verduidelijking
                    and isinstance(service_result, dict)
                    and service_result.get("error_type")
                    in HERSTELBARE_VERDUIDELIJKINGSFOUTEN
                ):
                    melding = ensure_string(
                        service_result.get("error_message") or "Generatie geweigerd"
                    )
                    if isinstance(verzonden_kopie, dict):
                        SessionStateManager.set_value(KEY_VERZONDEN, verzonden_kopie)
                    SessionStateManager.set_value(KEY_AFWIJZING, melding)
                    st.error(
                        f"❌ Generatie niet uitgevoerd: {melding} Je antwoord "
                        "staat nog in de 'Definitie Generatie' tab."
                    )
                    logger.warning(
                        "Generatie geweigerd vóór het model (%s); verzonden "
                        "verduidelijking behouden",
                        service_result.get("error_type"),
                    )
                    return

                # Converteer naar checker formaat voor UI compatibility
                # DEF-439: aparte naam — deze post-generatie tak heeft geen check-result
                check_result_ui = None
                agent_result = service_result

                # DEF-751 stap 2: een door het model gemeld betekenisconflict
                # is geen definitie — niets opgeslagen, geen editrecord, geen
                # keuze-event. Het open conflict (gebonden aan deze invoer)
                # gaat de sessie in voor het antwoordveld in de tab; elke
                # andere uitkomst sluit een eerder open conflict en een
                # eerdere afwijzing.
                open_conflict = open_conflict_uit(service_result, vingerafdruk)
                SessionStateManager.clear_value(KEY_AFWIJZING)
                if open_conflict is not None:
                    SessionStateManager.set_value(KEY_OPEN, open_conflict)
                else:
                    SessionStateManager.clear_value(KEY_OPEN)

                # Voor auto-load in Bewerk-tab en voor Toepassen (herreview 3:
                # het werkelijk opgeslagen record met id én versie).
                saved_record = None
                saved_definition_id = None
                if isinstance(service_result, dict) and service_result.get("success"):
                    saved_definition_id = service_result.get("saved_definition_id")
                    saved_record = self._leg_handmatige_keuze_vast(
                        saved_definition_id,
                        auto_categorie if manual_category else None,
                        _st=st,
                    )

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
                        "check_result": check_result_ui,  # DEF-439
                        "agent_result": agent_result,
                        "saved_record": saved_record,
                        "saved_definition_id": saved_definition_id,
                        "determined_category": (
                            auto_categorie.value if auto_categorie else None
                        ),
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

                # DEF-751 stap 2: geen onvoorwaardelijk succes. Een gemeld
                # betekenisconflict is een vraag aan de gebruiker; een andere
                # non-success is een fout. Alleen een echt resultaat is succes.
                geslaagd = isinstance(service_result, dict) and bool(
                    service_result.get("success")
                )
                if open_conflict is not None:
                    st.warning(
                        "⚠️ Verduidelijking nodig: het model meldt een "
                        "betekenisconflict en heeft geen definitie geleverd. "
                        "Beantwoord de vraag in de 'Definitie Generatie' tab en "
                        "genereer daarna opnieuw."
                    )
                elif not geslaagd:
                    reden = (
                        service_result.get("error_message")
                        if isinstance(service_result, dict)
                        else None
                    ) or "onbekende fout"
                    st.error(f"❌ Generatie mislukt: {reden}")
                elif document_context and document_context.get("document_count", 0) > 0:
                    # Toon document context info als gebruikt
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
        finally:
            # DEF-622 (besluit 5): de force-keuze is eenmalig en mag niet
            # plakken — ook niet na een mislukte generatie. Anders sloeg de
            # volgende, ongerelateerde generatie stil de duplicaatcontrole
            # over en reisde `force_duplicate` mee naar DUP_01 en de opslag.
            self._wis_force_opties(_sm=SessionStateManager)

    @staticmethod
    def _heeft_inhoudelijke_context(context_data: dict[str, Any]) -> bool:
        """Minstens één niet-lege waarde in de drie contextlijsten (B-01)."""
        from domain.context.normalisatie import lees_contextwaarden

        return any(
            waarde.strip()
            for veld in (
                "organisatorische_context",
                "juridische_context",
                "wettelijke_basis",
            )
            for waarde in lees_contextwaarden(context_data.get(veld))
        )

    @staticmethod
    def _wis_force_opties(*, _sm: Any) -> None:
        opties = ensure_dict(_sm.get_value("generation_options", {}))
        gewist = False
        for sleutel in ("force_generate", "force_duplicate", "force_duplicate_reason"):
            if sleutel in opties:
                opties.pop(sleutel, None)
                gewist = True
        if gewist:
            _sm.set_value("generation_options", opties)

    @staticmethod
    def _keuze_invoer(reasoning: Any, scores: Any) -> dict[str, Any]:
        """De herkomst van het modelvoorstel voor de service (DEF-751 B2):
        `model` met reasoning/scores. Nooit een actor of status."""
        invoer: dict[str, Any] = {"origin": HERKOMST_MODEL}
        if isinstance(reasoning, str) and reasoning:
            invoer["reasoning"] = reasoning
        if isinstance(scores, dict) and scores:
            invoer["scores"] = dict(scores)
        return invoer

    def _leg_handmatige_keuze_vast(
        self, saved_definition_id: Any, override: Any, *, _st: Any
    ) -> Any:
        """Het opgeslagen record ophalen en — bij een handmatige override — de
        keuze via het expliciete commando vastleggen (DEF-751 B2, herreview 2).

        De override is de keuzeactie van deze generatieklik; zij wordt, net
        als de editor-/Toepassen-actie, als `manual`-event met de versie van
        het zojuist opgeslagen record geschreven (geen actor: deze tab kent
        geen identiteit). Geeft het record ná de opslag terug (id én versie),
        zodat Toepassen op de werkelijk getoonde versie werkt (herreview 3).
        Mislukt het commando, dan blijft het concept zonder keuze-event en
        wordt dat gemeld — niets wordt verzonnen.
        """
        if not saved_definition_id:
            return None
        try:
            record = self.repository.get_definitie(int(saved_definition_id))
        except Exception as e:  # pragma: no cover - defensieve grens
            logger.warning(
                "Opgeslagen record %s niet leesbaar: %s", saved_definition_id, e
            )
            return None
        if record is None or override is None:
            return record
        try:
            ok = self.repository.record_category_choice(
                int(saved_definition_id),
                {},
                waarde=override.value,
                herkomst=HERKOMST_HANDMATIG,
                actor=None,
                actor_source=None,
                updated_by=None,
                expected_version=record.version_number,
            )
        except ValueError as e:
            ok = False
            logger.warning("Handmatige categoriekeuze geweigerd: %s", e)
        if not ok:
            _st.warning(
                "De handmatige categoriekeuze kon niet bij het concept worden "
                "vastgelegd; kies zo nodig opnieuw in de Bewerk-tab."
            )
            return record
        return self.repository.get_definitie(int(saved_definition_id))

    def _weiger_categorie(
        self, waarde: Any, herkomst: str, *, _st: Any, _sm: Any
    ) -> None:
        """DEF-751: een keuze/voorstel buiten de vier generatiecategorieën
        stopt de generatie vóór duplicaatvoorcontrole en model — geen stille
        PROCES. De afgewezen aanvraag verbruikt de eenmalige force-opties
        (zelfde regel als de begrip- en contextgate)."""
        _st.error(
            f"❌ Generatie niet gestart: de {herkomst} '{waarde}' is geen "
            "categorie waarmee gegenereerd kan worden "
            "(type, proces, resultaat, exemplaar). Kies hierboven opnieuw."
        )
        logger.warning(
            "Generatie niet gestart: %s %r is geen generatiecategorie",
            herkomst,
            waarde,
        )
        self._wis_force_opties(_sm=_sm)

    def handle_duplicate_check(
        self,
        begrip: str,
        context_data: dict[str, Any],
        *,
        _st: Any = None,
        _sm: Any = None,
    ) -> None:
        """Handle duplicate check vanaf hoofdniveau."""
        st = _st if _st is not None else _default_st
        SessionStateManager = _sm if _sm is not None else _DefaultSM

        # DEF-553: zelfde invoergrens als generatie — de duplicate-check
        # verwerkt hetzelfde begrip-veld.
        afwijsreden = validate_begrip_input(begrip)
        if afwijsreden:
            st.error(f"❌ Duplicate-check geweigerd: {afwijsreden}.")
            logger.warning(
                "Duplicate-check geweigerd: ongeldig begrip (%s)", afwijsreden
            )
            return
        begrip = begrip.strip()

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

    def _get_document_context(
        self, *, _st: Any = None, _sm: Any = None
    ) -> dict[str, Any] | None:
        """Krijg document context voor definitie generatie.

        DEF-514: geselecteerde documenten die inmiddels uit de begrensde
        documentcache zijn geëvict, vallen niet stil weg — de gebruiker
        krijgt een expliciete waarschuwing en de generatie gaat door met
        de resterende documenten.
        """
        st = _st if _st is not None else _default_st
        SessionStateManager = _sm if _sm is not None else _DefaultSM
        try:
            selected_docs = SessionStateManager.get_value("selected_documents", [])
            if not selected_docs:
                return None

            processor = get_document_processor()

            # DEF-514: detecteer geëvicte selecties expliciet
            available_docs: list[str] = []
            for doc_id in selected_docs:
                if processor.get_document_by_id(doc_id) is None:
                    logger.warning(
                        f"Geselecteerd document '{doc_id}' is niet meer beschikbaar "
                        "(opgeruimd na cache-limiet); generatie gaat door met de "
                        "resterende documenten"
                    )
                    st.warning(
                        f"⚠️ Document '{doc_id}' is niet meer beschikbaar "
                        "(opgeruimd na cache-limiet) — upload opnieuw indien nodig"
                    )
                else:
                    available_docs.append(doc_id)

            if not available_docs:
                return None

            aggregated_context = processor.get_aggregated_context(available_docs)

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

    @staticmethod
    def _document_citation_label(
        doc: Any, text: str, idx: int, matched_term: bool
    ) -> str | None:
        """Bronvermelding binnen het document: pagina (pdf) of alinea (docx);
        een volledig kort document zonder termtreffer heet zo."""
        if not matched_term:
            return "volledig document"
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
        return citation_label

    def _build_document_snippets(
        self,
        begrip: str,
        selected_doc_ids: list[str],
        max_snippets_total: int | None = None,
        per_doc_max: int = 4,
        snippet_window: int = 280,
    ) -> list[dict[str, Any]]:
        """Selecteer termpassages of volledige korte, expliciet gekozen documenten."""
        try:
            if not begrip or not selected_doc_ids:
                return []

            processor = get_document_processor()
            begrip_lower = str(begrip).strip().lower()
            if not begrip_lower:
                return []

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

                    matched_term = begrip_lower in haystack
                    if not matched_term and (
                        not text.strip() or len(text) > snippet_window
                    ):
                        continue
                    positions = (
                        (
                            m.start()
                            for m in re.finditer(re.escape(begrip_lower), haystack)
                        )
                        if matched_term
                        else iter([0])
                    )
                    count_for_doc = 0
                    for idx in positions:
                        if len(snippets) >= max_snippets_total:
                            break
                        if count_for_doc >= max(1, per_doc_max):
                            break

                        start = max(0, idx - snippet_window // 2)
                        end = min(
                            len(text),
                            idx + len(begrip) + snippet_window // 2,
                        )
                        if not matched_term:
                            start, end = 0, len(text)
                        raw = text[start:end].replace("\n", " ").strip()
                        citation_label = self._document_citation_label(
                            doc, text, idx, matched_term
                        )
                        snippet = {
                            "provider": "documents",
                            "title": getattr(doc, "filename", "document"),
                            "filename": getattr(doc, "filename", None),
                            "doc_id": getattr(doc, "id", None),
                            "snippet": raw,
                            "score": 1.0 if matched_term else 0.0,
                            "selection_basis": (
                                "term_match"
                                if matched_term
                                else "selected_short_document"
                            ),
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
