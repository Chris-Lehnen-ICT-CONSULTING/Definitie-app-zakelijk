"""
Voorbeelden (examples) renderer for definition generator tab.

Extracted from definition_generator_tab.py as part of DEF-266 Phase 4 refactoring.
Handles rendering and persistence of generated examples (voorbeeldzinnen, praktijkvoorbeelden, etc).
"""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st
from pydantic import ValidationError

from models.voorbeelden_validation import validate_save_voorbeelden_input
from ui.session_state import SessionStateManager
from utils.type_helpers import ensure_dict, ensure_string

logger = logging.getLogger(__name__)


class VoorbeeldenRenderer:
    """Renderer voor voorbeelden sectie in de definitie generator."""

    def render_voorbeelden_section(self, voorbeelden: dict[str, list[str]]) -> None:
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
                    location="voorbeelden_renderer.render_voorbeelden_section",
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

    def maybe_persist_examples(
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

            to_save = self._prepare_voorbeelden_for_save(canon)

            # Controleer of er iets nieuws is
            total_new = sum(len(v) for v in to_save.values())
            if total_new == 0:
                logger.warning(
                    f"Voorbeelden dict empty (0 items) for definitie {definitie_id}"
                )
                return False

            # Vergelijk met huidige actieve voorbeelden
            from database.definitie_repository import get_definitie_repository

            repo = get_definitie_repository()
            current = repo.get_voorbeelden_by_type(definitie_id)

            if self._voorbeelden_are_identical(current, to_save):
                logger.info(
                    f"Voorbeelden identical to database for definitie {definitie_id}, skipping save"
                )
                return False

            # Sla op met voorkeursterm uit session state
            voorkeursterm = SessionStateManager.get_value("voorkeursterm", "")

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
                return True
            except ValidationError as e:
                logger.error(
                    f"Voorbeelden validation failed for definitie {definitie_id}: {e}"
                )
                return False
        except Exception as e:
            logger.warning("Automatisch opslaan voorbeelden mislukt: %s", e)
            return False

    def persist_examples_manual(
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

            to_save = self._prepare_voorbeelden_for_save(canon)

            total_new = sum(len(v) for v in to_save.values())
            if total_new == 0:
                return False

            from database.definitie_repository import get_definitie_repository

            repo = get_definitie_repository()
            voorkeursterm = SessionStateManager.get_value("voorkeursterm", "")

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

    def render_voorbeelden_save_buttons(
        self,
        voorbeelden: dict[str, Any],
        agent_result: dict[str, Any],
        saved_record: Any,
        saved_definition_id: int | None,
    ) -> None:
        """Render save buttons for voorbeelden section."""
        # Persistente opslag van voorbeelden in DB (automatisch)
        try:
            saved_id = None
            if (
                saved_record is not None
                and hasattr(saved_record, "id")
                and saved_record.id
            ):
                saved_id = int(saved_record.id)
            elif isinstance(saved_definition_id, int) and saved_definition_id > 0:
                saved_id = int(saved_definition_id)

            if saved_id:
                saved_successfully = self.maybe_persist_examples(saved_id, agent_result)
                if saved_successfully:
                    vb = agent_result.get("voorbeelden", {})
                    if isinstance(vb, dict):
                        total = sum(
                            (len(v) if isinstance(v, list) else (1 if v else 0))
                            for v in vb.values()
                        )
                        st.success(
                            f"✅ Voorbeelden automatisch opgeslagen ({total} items)"
                        )
        except Exception as e:
            logger.warning(f"Automatisch opslaan van voorbeelden overgeslagen: {e}")

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
                elif isinstance(saved_definition_id, int) and saved_definition_id > 0:
                    saved_id_btn = int(saved_definition_id)
                else:
                    can_save_examples = False

                help_text = None
                if not can_save_examples:
                    help_text = (
                        "Sla eerst de definitie op om voorbeelden te kunnen bewaren."
                    )

                if st.button(
                    "💾 Voorbeelden naar DB opslaan (forceren)",
                    key="force_save_examples",
                    disabled=not can_save_examples,
                    help=help_text,
                ):
                    if saved_id_btn:
                        ok = self.persist_examples_manual(saved_id_btn, agent_result)
                        if ok:
                            st.success("✅ Voorbeelden opgeslagen in database")
                        else:
                            st.info("ℹ️ Geen op te slaan voorbeelden of al up-to-date")
        except Exception as e:
            logger.debug(f"Render force-save examples knop overgeslagen: {e}")

    # ============ Private helper methods ============

    def _prepare_voorbeelden_for_save(
        self, canon: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Prepare voorbeelden dict for saving to database."""

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
        # Toelichting optioneel opslaan als één regel
        if (
            isinstance(canon.get("toelichting"), str)
            and canon.get("toelichting").strip()
        ):
            to_save["toelichting"] = [canon.get("toelichting").strip()]  # type: ignore[index]

        return to_save

    def _voorbeelden_are_identical(
        self, current: dict[str, list[str]], to_save: dict[str, list[str]]
    ) -> bool:
        """Check if current DB voorbeelden are identical to what we want to save."""

        def _norm(d: dict[str, list[str]]) -> dict[str, set[str]]:
            return {k: {str(x).strip() for x in (d.get(k) or [])} for k in d}

        # Map DB keys naar canonical UI keys voor vergelijking
        current_canon = {
            "voorbeeldzinnen": current.get("sentence", [])
            or current.get("voorbeeldzinnen", []),
            "praktijkvoorbeelden": current.get("practical", [])
            or current.get("praktijkvoorbeelden", []),
            "tegenvoorbeelden": current.get("counter", [])
            or current.get("tegenvoorbeelden", []),
            "synoniemen": current.get("synonyms", []) or current.get("synoniemen", []),
            "antoniemen": current.get("antonyms", []) or current.get("antoniemen", []),
            "toelichting": current.get("explanation", [])
            or current.get("toelichting", []),
        }

        return _norm(current_canon) == _norm(to_save)
