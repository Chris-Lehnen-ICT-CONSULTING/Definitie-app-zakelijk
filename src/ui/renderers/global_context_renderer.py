"""Renderer voor globale context selectie, metadata en categorie preview.

Geextraheerd uit TabbedInterface (DEF-141). Bevat alle UI-logica
voor de context configuratie boven de tabs: begrip invoer, context
selector, metadata velden, en ontologische categorie preview.
"""

import asyncio as _default_asyncio
import logging
from datetime import UTC, datetime
from typing import Any, cast

import streamlit as _default_st

from ui.session_state import SessionStateManager as _DefaultSM

logger = logging.getLogger(__name__)


class GlobalContextRenderer:
    """Render globale context UI boven de tab navigatie."""

    def __init__(self, context_selector: Any) -> None:
        self.context_selector = context_selector

    # ------------------------------------------------------------------
    # Begrip & context
    # ------------------------------------------------------------------

    def render_begrip_input(self) -> str:
        """Render begrip invoerveld en sla op in session state."""
        _default_st.markdown("### 📝 Definitie Aanvraag")
        _DefaultSM.initialize_session_state({"begrip_input": ""})
        previous = _DefaultSM.get_value("begrip", "")
        value = _default_st.text_input(
            "Voer een term in waarvoor een definitie moet worden gegenereerd",
            placeholder="bijv. authenticatie, verificatie, identiteitsvaststelling...",
            help="Het centrale begrip waarvoor een definitie gegenereerd wordt",
            key="begrip_input",
        )
        # DEF-500: spiegel de widget-waarde naar de niet-widget-key "begrip";
        # render_category_preview en de auto-generatie-trigger lezen die key.
        # Bij een gewijzigde term is de gecachte classificatie niet langer
        # geldig — anders genereert de handler met de categorie van de vorige term.
        if value != previous:
            for stale_key in (
                "determined_category",
                "category_reasoning",
                "category_scores",
            ):
                _DefaultSM.clear_value(stale_key)
        _DefaultSM.set_value("begrip", value)
        return value

    def render_context_selector(self) -> dict[str, Any]:
        """Render context selector met fallback.

        DEF-498: de sectiekop is eigendom van de selector (elke render-route
        print hem zelf) — hier niet nogmaals renderen, anders dubbele kop.
        """
        try:
            context_data = self.context_selector.render()
            logger.debug("Context selector succesvol geladen")
        except Exception as e:
            logger.error(f"Context selector crashed: {e}", exc_info=True)
            _default_st.error(f"❌ Context selector fout: {type(e).__name__}: {e!s}")
            try:
                context_data = self.render_simplified_context_selector()
            except Exception as e2:
                logger.error(
                    f"Simplified selector also failed: {e2}",
                    exc_info=True,
                )
                context_data = {
                    "organisatorische_context": [],
                    "juridische_context": [],
                    "wettelijke_basis": [],
                }

        _DefaultSM.set_value("global_context", context_data)

        if any(context_data.values()):
            self.render_context_summary(context_data)

        return cast(dict[str, Any], context_data)

    def render_simplified_context_selector(self) -> dict[str, Any]:
        """Render context selector via ContextManager-only implementatie."""
        try:
            from ui.components.enhanced_context_manager_selector import (
                render_context_selector,
            )

            return cast(dict[str, Any], render_context_selector())
        except Exception as e:
            logger.error(
                f"Enhanced context selector kon niet renderen: {e}",
                exc_info=True,
            )
            return {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            }

    def render_context_summary(self, context_data: dict[str, Any]) -> None:
        """Render samenvatting van geselecteerde context."""
        summary_parts = []

        if context_data.get("organisatorische_context"):
            summary_parts.append(
                f"📋 Org: {', '.join(context_data['organisatorische_context'])}"
            )
        if context_data.get("juridische_context"):
            summary_parts.append(
                f"⚖️ Juridisch: {', '.join(context_data['juridische_context'])}"
            )
        if context_data.get("wettelijke_basis"):
            summary_parts.append(
                f"📜 Wet: {', '.join(context_data['wettelijke_basis'])}"
            )

        if summary_parts:
            _default_st.info(" | ".join(summary_parts))

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def render_metadata_fields(self) -> None:
        """Render metadata velden voor definitie voorstel."""
        col1, col2, col3 = _default_st.columns(3)

        with col1:
            _DefaultSM.initialize_session_state(
                {"datum_voorstel": datetime.now(UTC).date()}
            )
            _default_st.date_input(
                "📅 Datum voorstel",
                key="datum_voorstel",
                help="Datum waarop deze definitie wordt voorgesteld",
            )

        with col2:
            _DefaultSM.initialize_session_state({"voorgesteld_door": ""})
            _default_st.text_input(
                "👤 Voorgesteld door",
                placeholder="Naam van voorsteller",
                help="Persoon of organisatie die deze definitie voorstelt",
                key="voorgesteld_door",
            )

        with col3:
            ketenpartner_opties = [
                "ZM",
                "DJI",
                "KMAR",
                "CJIB",
                "JUSTID",
                "OM",
                "Reclassering",
                "NP",
            ]
            ketenpartners = _default_st.multiselect(
                "🤝 Ketenpartners die akkoord zijn",
                options=ketenpartner_opties,
                default=_DefaultSM.get_value("ketenpartners", []),
                help="Partners die akkoord zijn met deze definitie",
            )
            _DefaultSM.set_value("ketenpartners", ketenpartners)

        _default_st.markdown("#### 🧭 UFO-categorie (optioneel)")
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
        ufo_default = _DefaultSM.get_value("ufo_categorie", "")
        default_index = (
            ufo_opties.index(ufo_default) if ufo_default in ufo_opties else 0
        )
        ufo_selected = _default_st.selectbox(
            "UFO-categorie",
            options=ufo_opties,
            index=default_index,
            key="meta_ufo_categorie",
            help="Kies desgewenst een UFO-categorie; "
            "deze wordt automatisch opgeslagen bij generatie",
        )
        _DefaultSM.set_value("ufo_categorie", ufo_selected)

    # ------------------------------------------------------------------
    # Ontologische categorie
    # ------------------------------------------------------------------

    async def determine_ontological_category(
        self, begrip: str, org_context: Any, jur_context: Any
    ) -> tuple[Any, Any, Any]:
        """Bepaal automatisch de ontologische categorie.

        Gebruikt ImprovedOntologyClassifier met 3-context support.
        """
        from ontologie.improved_classifier import ImprovedOntologyClassifier

        try:
            classifier = ImprovedOntologyClassifier()

            result = classifier.classify(
                begrip=begrip,
                org_context=org_context,
                jur_context=jur_context,
                wet_context="",
            )

            if result is None:
                raise RuntimeError(
                    f"Classifier returned None voor '{begrip}'. "
                    "Dit duidt op een interne fout."
                )

            logger.info(
                f"Ontologische classificatie voor '{begrip}': "
                f"{result.categorie.value} (scores: {result.test_scores})"
            )

            return result.categorie, result.reasoning, result.test_scores

        except Exception as e:
            logger.error(
                f"Ontologische classificatie gefaald voor '{begrip}': {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Kan ontologische categorie niet bepalen voor '{begrip}'. "
                "Controleer of context compleet is."
            ) from e

    def render_category_preview(
        self,
        *,
        _st: Any = None,
        _sm: Any = None,
        _asyncio_run: Any = None,
        _determine_fn: Any = None,
    ) -> None:
        """Toon voorgestelde ontologische categorie met mogelijkheid tot override.

        DEF-36: Preview van pre-geclassificeerde categorie voor gebruiker.

        Keyword-only params ``_st``, ``_sm``, ``_asyncio_run`` and
        ``_determine_fn`` allow the TabbedInterface delegate to inject
        module-level references that tests patch (see DEF-141).
        """
        st = _st if _st is not None else _default_st
        sm = _sm if _sm is not None else _DefaultSM
        arun = _asyncio_run if _asyncio_run is not None else _default_asyncio.run
        classify = (
            _determine_fn
            if _determine_fn is not None
            else self.determine_ontological_category
        )

        begrip = sm.get_value("begrip", "")
        if begrip.strip():
            determined_category = sm.get_value("determined_category")

            if not determined_category:
                context_data = sm.get_value("global_context", {})
                org_context = context_data.get("organisatorische_context", [])
                jur_context = context_data.get("juridische_context", [])

                if org_context or jur_context:
                    primary_org = org_context[0] if org_context else ""
                    primary_jur = jur_context[0] if jur_context else ""

                    try:
                        auto_categorie, reasoning, scores = arun(
                            classify(begrip, primary_org, primary_jur)
                        )

                        sm.set_value("determined_category", auto_categorie.value)
                        sm.set_value("category_reasoning", reasoning)
                        sm.set_value("category_scores", scores)

                        logger.info(
                            f"DEF-36: Pre-classificatie voor '{begrip}': "
                            f"{auto_categorie.value} (scores: {scores})"
                        )

                        determined_category = auto_categorie.value
                    except Exception as e:
                        logger.warning(f"Auto-classificatie mislukt: {e}")
                        return

        determined_category = sm.get_value("determined_category")
        if not determined_category:
            return

        st.markdown("#### 🎯 Ontologische Categorie")

        col1, col2 = st.columns([2, 1])

        with col1:
            reasoning = sm.get_value("category_reasoning", "")
            scores = sm.get_value("category_scores", {})

            st.info(f"**Voorgesteld:** {determined_category}")
            with st.expander("ℹ️ Waarom deze categorie?"):
                st.write(reasoning)
                if scores:
                    st.write("**Scores:**", scores)

        with col2:
            manual_override = st.selectbox(
                "Aanpassen?",
                options=["", "TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"],
                index=0,
                key="manual_category_override",
                help="Laat leeg om voorgestelde categorie te gebruiken",
            )

            if manual_override:
                sm.set_value("manual_ontological_category", manual_override)
                st.success(f"✓ Gebruik {manual_override}")
