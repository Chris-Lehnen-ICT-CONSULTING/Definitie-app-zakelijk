"""Sources Renderer - Renders web sources/provenance section.

Extracted from definition_generator_tab.py to reduce God Class complexity.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, cast

import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord

from ui.components.formatters import get_provider_label

logger = logging.getLogger(__name__)


def _als_mapping(waarde: Any) -> Mapping[str, Any]:
    """Typegetrouwe vernauwing: een mapping, anders een lege mapping."""
    return waarde if isinstance(waarde, Mapping) else {}


def _extract_metadata_value(
    saved_record: DefinitieRecord | None,
    agent_result: dict[str, Any],
    key: str,
) -> str | bool | float | dict[str, Any] | list[Any] | None:
    """Extract a metadata value from saved_record or agent_result.

    Tries multiple locations in order:
    1. saved_record.metadata[key]
    2. agent_result.metadata[key] (dict format)
    3. agent_result.metadata[key] (object format)
    """
    # Try saved_record first.
    # DEF-439: DefinitieRecord declareert geen `metadata`; lees defensief via
    # getattr zodat de check mypy-clean is en gedrag identiek blijft.
    meta = getattr(saved_record, "metadata", None) if saved_record else None
    if meta:
        if isinstance(meta, dict) and key in meta:
            return meta.get(key)

    # Try agent_result dict format
    if isinstance(agent_result, dict):
        meta = agent_result.get("metadata")
        if isinstance(meta, dict) and key in meta:
            return meta.get(key)
    # Try agent_result object format
    elif hasattr(agent_result, "metadata") and isinstance(agent_result.metadata, dict):
        if key in agent_result.metadata:
            return agent_result.metadata.get(key)

    return None


def _extract_sources(
    saved_record: DefinitieRecord | None,
    agent_result: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """Extract sources from dict format (V2 canonical format).

    Tries in order:
    1. saved_record.metadata.sources (from DB)
    2. agent_result.sources (V2 direct dict key, from ServiceAdapter.to_ui_response())

    Note: Legacy object-attribute fallbacks removed in DEF-263 after audit confirmed
    no legacy formats are used in the codebase. All code paths use V2 dict format.
    """
    # 1) Try saved_record.metadata (DB format).
    # DEF-439: defensieve getattr i.p.v. directe attribuut-toegang (zie boven).
    metadata = getattr(saved_record, "metadata", None) if saved_record else None
    if metadata:
        if isinstance(metadata, dict):
            sources = metadata.get("sources")
            if sources is not None:
                # DEF-439: cast Any-waarde uit dict naar declared return type.
                return cast("list[dict[str, Any]]", sources)

    # 2) Direct sources key on agent_result dict (V2 format)
    if isinstance(agent_result, dict):
        sources = agent_result.get("sources")
        if sources is not None:
            # DEF-439: cast Any-waarde uit dict naar declared return type.
            return cast("list[dict[str, Any]]", sources)

    return None


class SourcesRenderer:
    """Renders web sources (provenance) section.

    Handles:
    - Finding sources from multiple fallback locations
    - Displaying web lookup status and availability
    - Rendering sources grouped by provider
    - Debug toggles for SRU/WL troubleshooting
    """

    def render_sources_section(
        self,
        generation_result: dict[str, Any],
        agent_result: dict[str, Any],
        saved_record: DefinitieRecord | None = None,
    ) -> None:
        """Render complete sources section with fallback logic.

        Args:
            generation_result: Full generation result dict
            agent_result: Agent result (V2 dict or legacy object)
            saved_record: Saved DefinitieRecord (optional)
        """
        try:
            sources = _extract_sources(saved_record, agent_result)

            st.markdown("#### 📚 Gebruikte Bronnen")

            # Extract status metadata
            status_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_status"
            )
            available_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_available"
            )
            timeout_meta = _extract_metadata_value(
                saved_record, agent_result, "web_lookup_timeout"
            )

            # Show status information
            # DEF-439: cast union-metadata naar de smallere param-types (non-behavioral).
            self._render_status_info(
                cast("str | None", status_meta),
                cast("bool | None", available_meta),
                cast("float | None", timeout_meta),
            )

            # Debug toggles
            self._render_debug_toggles(
                saved_record,
                agent_result,
                cast("str | None", status_meta),
                cast("bool | None", available_meta),
                cast("float | None", timeout_meta),
            )

            # Handle no sources case
            if not sources:
                self._render_no_sources_message(
                    cast("str | None", status_meta),
                    cast("bool | None", available_meta),
                )
                return

            # Render sources list
            self._render_sources_list(sources)

        except KeyError as e:
            logger.error(f"Missing required source data key: {e}", exc_info=True)
            st.warning("Brongegevens zijn incompleet. Controleer de definitie data.")
        except AttributeError as e:
            logger.error(f"Invalid source data structure: {e}", exc_info=True)
            st.warning("Bronnenformaat wordt niet herkend. Vernieuw de pagina.")
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid source data value: {e}", exc_info=True)
            st.warning("Bronwaarde kon niet worden verwerkt. Probeer opnieuw.")

    def _render_status_info(
        self,
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render web lookup status information."""
        if status_meta or available_meta is not None:
            status_text = status_meta or "onbekend"
            avail_text = (
                "beschikbaar"
                if available_meta is True
                else "niet beschikbaar" if available_meta is False else "onbekend"
            )
            # Fallback to env if metadata has no timeout
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

    def _render_debug_toggles(
        self,
        saved_record: DefinitieRecord | None,
        agent_result: dict[str, Any],
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render debug toggles for SRU/WL troubleshooting."""
        debug_info = _extract_metadata_value(
            saved_record, agent_result, "web_lookup_debug"
        )

        # SRU/WL debug: show lookup attempts (JSON)
        if st.checkbox(
            "🐛 SRU/WL debug: Toon lookup attempts (JSON)",
            key="debug_web_lookup_attempts",
        ):
            st.json(debug_info or {})

        # Show attempts table if available
        if debug_info and isinstance(debug_info, dict):
            attempts_list = debug_info.get("attempts") or []
            if attempts_list:
                self._render_attempts_table(attempts_list)

        # Raw web_lookup data debug
        if st.checkbox(
            "🐛 Debug: Toon ruwe web_lookup data (JSON)",
            key="debug_web_lookup_sources_raw",
        ):
            self._render_raw_debug_data(
                saved_record, agent_result, status_meta, available_meta, timeout_meta
            )

    def _render_attempts_table(self, attempts_list: list[dict]) -> None:
        """Render attempts as a table."""
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
                except (TypeError, AttributeError):
                    try:
                        repr_str = repr(a)
                        truncated = repr_str[:100] if len(repr_str) > 100 else repr_str
                    except Exception:
                        truncated = f"<unrepresentable {type(a).__name__}>"
                    logger.warning(
                        "Malformed attempt in _render_attempts_table: "
                        "type=%s, repr=%r",
                        type(a).__name__,
                        truncated,
                    )
                    continue

            if rows:
                try:
                    import pandas as pd  # type: ignore

                    st.dataframe(pd.DataFrame(rows))
                except Exception:
                    # Fallback without pandas
                    for r in rows:
                        st.markdown(
                            f"- {r['provider']} ({r['api']}): {r['strategie']} — {r['query/term']}"
                            f" — status={r['status']} records={r.get('records') or 0}"
                        )

    def _render_raw_debug_data(
        self,
        saved_record: DefinitieRecord | None,
        agent_result: dict[str, Any],
        status_meta: str | None,
        available_meta: bool | None,
        timeout_meta: float | None,
    ) -> None:
        """Render raw debug data for troubleshooting."""
        saved_meta_sources = None
        agent_meta_sources = None
        agent_attr_sources = None
        agent_top_sources = None

        # DEF-439: defensieve getattr (DefinitieRecord declareert geen metadata).
        m = getattr(saved_record, "metadata", None) if saved_record else None
        if isinstance(m, dict):
            saved_meta_sources = m.get("sources")

        if isinstance(agent_result, dict):
            m = agent_result.get("metadata")
            if isinstance(m, dict):
                agent_meta_sources = m.get("sources")
            agent_top_sources = agent_result.get("sources")
        elif hasattr(agent_result, "metadata") and isinstance(
            agent_result.metadata, dict
        ):
            agent_meta_sources = agent_result.metadata.get("sources")

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

    def _render_no_sources_message(
        self,
        status_meta: str | None,
        available_meta: bool | None,
    ) -> None:
        """Render appropriate message when no sources are found."""
        if available_meta is False or status_meta == "not_available":
            msg = "ℹ️ Web lookup is niet beschikbaar in deze omgeving."
        elif status_meta == "timeout":
            msg = "⏱️ Web lookup time-out — geen bronnen opgehaald."
        elif status_meta == "error":
            msg = "⚠️ Web lookup fout — geen bronnen opgehaald."
        else:
            msg = "ℹ️ Geen relevante externe bronnen gevonden."
        st.info(msg)

    @staticmethod
    def _score_color(score: float) -> str:
        """DEF-364: Return color indicator for RAG score."""
        if score > 0.7:
            return "🟢"
        if score >= 0.5:
            return "🟠"
        return "🔴"

    # DEF-743: de documentroute levert alleen een selectiewijze, geen zoekscore.
    _SELECTION_BASIS_LABELS = {
        "term_match": "Letterlijke termtreffer",
        "selected_short_document": "Geselecteerd kort document",
    }
    _SNIPPET_PREVIEW_CHARS = 500

    def _render_sources_list(
        self,
        sources: list[dict[str, Any]],
        bijlage: Callable[[int, dict[str, Any]], None] | None = None,
    ) -> None:
        """Render the list of sources with expanders.

        DEF-743: ``bijlage(idx, src)`` rendert optioneel extra regels binnen de
        expander van elke bron (bronbasis: id, kwitantie, AI-oordeel, citaten).
        """
        for idx, src in enumerate(sources):
            provider_label = src.get("source_label") or get_provider_label(
                src.get("provider", "bron")
            )
            # Fix Bug #9: Strip whitespace and provide fallback
            title_raw = src.get("title") or src.get("definition") or ""
            title = title_raw.strip() or "(zonder titel)"
            url = src.get("url") or src.get("link") or ""
            # Fix Bug #2: Safely convert score to float
            # DEF-743: een echte numerieke nul is een waarde; alleen bij
            # ontbrekende score terugvallen op confidence.
            score_raw = src.get("score")
            if score_raw is None:
                score_raw = src.get("confidence")
            try:
                score = float(score_raw) if score_raw is not None else 0.0
            except (TypeError, ValueError):
                logger.warning(f"Invalid score value: {score_raw!r}, defaulting to 0.0")
                score = 0.0
            used = src.get("used_in_prompt", False)
            # F6: ook bronnen met alleen `chunk_text`/`content` tonen hun passage.
            snippet = (
                src.get("snippet")
                or src.get("context")
                or src.get("chunk_text")
                or src.get("content")
                or ""
            )
            legal_meta = src.get("legal")
            is_rag = src.get("provider") == "rag"
            is_document = src.get("provider") == "documents"

            # DEF-364: Score color for RAG sources
            score_indicator = f" {self._score_color(score)}" if is_rag else ""
            preview = self._SNIPPET_PREVIEW_CHARS

            with st.expander(
                f"{idx+1}. {provider_label} — {title[:80]}{score_indicator}",
                expanded=(idx == 0),
            ):
                # Show badges
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    # DEF-743: herkomst is een feit over de route; provider of
                    # legacy `is_authoritative` bewijst geen gezag (CON-02).
                    st.caption(f"Herkomst: {provider_label}")
                with col2:
                    if used:
                        st.info("→ In prompt")

                if is_document:
                    self._render_document_source_details(src)
                else:
                    # DEF-743: de score is zoekinformatie van web/RAG, geen
                    # bronbeoordeling; de RAG-kleur blijft (DEF-364).
                    kleur = f"{self._score_color(score)} " if is_rag else ""
                    st.markdown(f"**Zoekscore**: {kleur}{score:.2f}")
                    st.caption(
                        "Zoekscore = relevantie volgens de zoekroute, "
                        "geen beoordeling van de bron."
                    )

                # Show juridical citation if available
                if legal_meta and legal_meta.get("citation_text"):
                    st.markdown(
                        f"**Juridische verwijzing**: {legal_meta['citation_text']}"
                    )

                # Show snippet and link (DEF-743: ook voor de RAG-route)
                if snippet:
                    st.markdown(
                        f"**Fragment**: {snippet[:preview]}"
                        f"{'...' if len(snippet) > preview else ''}"
                    )
                if url:
                    st.markdown(f"[🔗 Open bron]({url})")
                if bijlage is not None:
                    bijlage(idx, src)

            # DEF-743: de volledige AANGELEVERDE passage raadpleegbaar houden;
            # aparte expander naast de bron (expanders nesten niet in elke versie).
            if len(snippet) > preview:
                with st.expander(
                    f"↳ Volledige passage bij bron {idx+1} ({len(snippet)} tekens)"
                ):
                    st.text(snippet)

    # ------------------------------------------------------------------
    # DEF-743: bronbasis (CON-02) — dezelfde bronlijst, verrijkt met bewijs
    # ------------------------------------------------------------------

    _ONDERDEELLABEL = {
        "source_authority": "Brongezag/toepasselijkheid",
        "semantic_support": "Betekenissteun",
        "reference_quality": "Verwijskwaliteit",
    }
    _DEELSTATUS = {
        "pass": "✅ voldoet",
        "fail": "❌ voldoet niet",
        "review_required": "🟠 nog te beoordelen",
        "error": "⚙️ technisch probleem",
    }
    _WEGGELATEN_REDEN = {
        "channel_disabled": "kanaal uitgeschakeld",
        "not_selected": "niet geselecteerd voor de prompt",
        "max_count": "boven het maximum aantal bronnen",
        "budget": "buiten het promptbudget",
        "empty_content": "lege passage",
        "not_in_receipt": "niet in de kwitantie (niet aangekomen)",
    }
    _REVIEW_TYPE_LABEL = {
        "reference_exception": "Verwijzingsuitzondering (bron zonder bruikbare hyperlink)",
        "no_appropriate_source": "Uitzondering: geen passende bron na onderbouwd zoeken",
        "part_correction": "Deskundige correctie van één AI-onderdeel (geen uitzondering)",
    }

    @staticmethod
    def _canonieke_ids(sources: list[dict[str, Any]]) -> dict[int, Any]:
        """index → canonieke `Bronidentiteit` (C-kern): stabiel id én metadata.

        `canoniseer_bronnen` sorteert, ontdubbelt en geeft botsende varianten
        een `#variant`-suffix. De koppeling van een getoonde rij naar háár
        canonieke bron gebruikt (F5) twee dingen tegelijk:

        1. het basis-id dat de kern voor déze rij afleidt
           (`canoniseer_bronnen([rij])` — aangeleverd `source_id`, doc/rag/url,
           of hash) — twee rijen die alleen in hun aangeleverde `source_id`
           verschillen blijven zo twee bronnen (root-probe A/B);
        2. de volledige identiteitsmetadata (`vingerafdrukdeel` zonder id) —
           twee rijen met hetzelfde basis-id maar een andere versie/vindplaats
           krijgen elk hun eigen `#variant`.

        Een kandidaat is de canonieke bron met exact het basis-id, of met een
        door de kern gegenereerde variant (`<basis>#<8 tekens>`) van dat id
        én gelijke metadata; een origineel id dat zelf een '#' bevat wordt dus
        nooit blind afgeknipt. Is de koppeling niet eenduidig, dan wordt de
        rij niet gekoppeld (geen gok). Zonder kern (ImportError) blijft de map
        leeg en meldt de sectie dat.
        """
        try:
            from domain.sources.normalisatie import canoniseer_bronnen
        except ImportError:
            return {}

        def _meta(bron: Any) -> str:
            deel = {
                k: v for k, v in bron.vingerafdrukdeel().items() if k != "source_id"
            }
            return json.dumps(deel, ensure_ascii=False, sort_keys=True)

        try:
            canoniek = canoniseer_bronnen(sources)
            uit: dict[int, Any] = {}
            for idx, src in enumerate(sources):
                los = canoniseer_bronnen([src])
                if len(los) != 1:
                    continue
                basis, meta = los[0].source_id, _meta(los[0])
                exact = [
                    b for b in canoniek if b.source_id == basis and _meta(b) == meta
                ]
                if len(exact) == 1:
                    uit[idx] = exact[0]
                    continue
                varianten = [
                    b
                    for b in canoniek
                    if b.source_id.startswith(basis + "#")
                    and len(b.source_id) == len(basis) + 9
                    and _meta(b) == meta
                ]
                if len(varianten) == 1:
                    uit[idx] = varianten[0]
            return uit
        except Exception as e:  # kern-fout is geen UI-crash
            logger.warning("canoniseer_bronnen mislukt: %s", e)
            return {}

    @staticmethod
    def _beoordelingskwitantie(
        sources: list[dict[str, Any]], assessment: Mapping[str, Any] | None
    ) -> tuple[dict[str, Any], str | None, dict[str, bool]]:
        """(verzonden passage per canoniek id, status, afkapmarkering per id).

        C §5a: `assessment_receipt` zegt exact wat de beoordeling per bron
        ontving (afgekapt op `max_passage_chars`). Alleen een door de kern
        (`verzonden_passages`) aan de canonieke bronnen gebonden kwitantie
        levert een "wat de beoordeling zag"-claim; status `None` = gebonden,
        `"afwezig"` = historisch zonder kwitantie (werkelijke modelinvoer
        onbekend), anders de reden waarom de kwitantie niet bindt.
        """
        if (
            not isinstance(assessment, Mapping)
            or assessment.get("status") != "assessed"
        ):
            return {}, "afwezig", {}
        receipt = assessment.get("assessment_receipt")
        if receipt is None:
            return {}, "afwezig", {}
        try:
            from domain.sources.contract import verzonden_passages
            from domain.sources.normalisatie import canoniseer_bronnen

            verzonden, fout = verzonden_passages(receipt, canoniseer_bronnen(sources))
        except ImportError:
            return {}, "bronkern niet beschikbaar", {}
        except Exception as e:  # kern-fout is geen UI-crash
            logger.warning("beoordelingskwitantie niet te controleren: %s", e)
            return {}, f"niet te controleren ({type(e).__name__})", {}
        if fout is not None:
            return {}, fout, {}
        afgekapt: dict[str, bool] = {}
        for item in receipt.get("sources") or []:
            if isinstance(item, Mapping) and isinstance(item.get("source_id"), str):
                afgekapt[item["source_id"]] = bool(item.get("truncated"))
        return {b.source_id: b for b in verzonden}, None, afgekapt

    def render_bronbasis_section(
        self,
        *,
        sources: list[dict[str, Any]] | None,
        assessment: Mapping[str, Any] | None,
        receipt: Mapping[str, Any] | None = None,
        review: Mapping[str, Any] | None = None,
        con02: Mapping[str, Any] | None = None,
        evidence_status: Mapping[str, Any] | None = None,
        review_status: Mapping[str, Any] | None = None,
        titel: str = "#### 📚 Bronbasis (CON-02)",
    ) -> None:
        """Toon de bronbasis van een record: bronnen, kwitantie, AI-oordeel,
        geverifieerde citaten, onzekerheden, herkomst (AI/deskundige),
        stale-/historische labels en deskundige uitzonderingen.

        Alles komt uit opgeslagen/aangeleverde gegevens (ID-only herladen
        volstaat); er wordt niets opgehaald en niets beoordeeld. Bron- en
        gebruikerstekst wordt als tekst getoond (geen HTML, geen uitvoering).
        """
        try:
            st.markdown(titel)
            self._render_bronbasis_status(evidence_status, review_status)
            if isinstance(con02, Mapping):
                from ui.components.validation_view import render_rule_results

                render_rule_results({"CON-02": dict(con02)})
            self._render_kwitantie(receipt)
            self._render_beoordeling_samenvatting(assessment)
            bronnen = list(sources or [])
            if not bronnen:
                st.info(
                    "ℹ️ Geen bronnen bij dit record. CON-02 blijft 'nog te beoordelen' "
                    "tot er bronnen zijn of een deskundige een gemotiveerde "
                    "uitzondering vastlegt."
                )
            else:
                ids = self._canonieke_ids(bronnen)
                if not ids:
                    st.caption(
                        "Bronkern niet beschikbaar: bron-id's en AI-oordeel per bron "
                        "kunnen niet gekoppeld worden."
                    )

                verzonden, kwitantiestatus, afgekapt = self._beoordelingskwitantie(
                    bronnen, assessment
                )
                if kwitantiestatus not in (None, "afwezig"):
                    st.warning(
                        "⚙️ Beoordelingskwitantie bindt niet aan de opgeslagen bronnen "
                        f"({kwitantiestatus}): wat de beoordeling werkelijk zag is niet "
                        "vast te stellen; er wordt geen modelinvoer geclaimd."
                    )

                def _bijlage(idx: int, src: dict[str, Any]) -> None:
                    self._render_bron_bewijs(
                        src,
                        ids.get(idx),
                        assessment,
                        verzonden=verzonden,
                        kwitantiestatus=kwitantiestatus,
                        afgekapt=afgekapt,
                    )

                self._render_sources_list(bronnen, bijlage=_bijlage)
            self._render_afgewezen_claims(assessment)
            self._render_uitzondering(review, review_status)
        except (KeyError, AttributeError, TypeError, ValueError) as e:
            logger.error("Bronbasis kon niet worden getoond: %s", e, exc_info=True)
            st.warning(
                "Bronbasis kon niet volledig worden getoond; controleer de brongegevens."
            )

    def _render_bronbasis_status(
        self,
        evidence_status: Mapping[str, Any] | None,
        review_status: Mapping[str, Any] | None,
    ) -> None:
        if isinstance(evidence_status, Mapping):
            status = str(evidence_status.get("status") or "")
            if status == "reference_only":
                st.warning(
                    "📎 Alleen een korte bronverwijzing (historisch record): onvolledig "
                    "bewijs, geen broninhoud of beoordeling."
                )
            elif status == "invalid":
                st.error(
                    "⚙️ Opgeslagen bronbewijs is onleesbaar: "
                    f"{evidence_status.get('reason') or 'geen details'}"
                )
            elif status == "present" and evidence_status.get("current") is False:
                st.warning(
                    "⏳ Historisch bronbewijs: hoort bij een eerdere tekst/context — "
                    f"{evidence_status.get('reason') or 'niet meer actueel'}. "
                    "Toets opnieuw voor een actuele beoordeling."
                )
        if (
            isinstance(review_status, Mapping)
            and review_status.get("status") == "stale"
        ):
            st.warning(
                "⏳ Eerdere deskundige uitzondering is verouderd (andere recordversie) "
                "en telt niet meer."
            )
        elif (
            isinstance(review_status, Mapping)
            and review_status.get("status") == "invalid"
        ):
            st.error(
                "⚙️ Opgeslagen deskundige uitzondering is ongeldig: "
                f"{review_status.get('reason') or 'geen details'}"
            )

    def _render_kwitantie(self, receipt: Mapping[str, Any] | None) -> None:
        """Geselecteerd vs. werkelijk in de prompt (E-kwitantie), fouten apart."""
        if not isinstance(receipt, Mapping):
            return
        status = str(receipt.get("status") or "")
        kanalen = _als_mapping(receipt.get("channels"))
        delen = []
        for naam, k in kanalen.items():
            if not isinstance(k, Mapping):
                continue
            aan = "aan" if k.get("enabled") else "uit"
            delen.append(
                f"{naam}: {k.get('used', 0)} van {k.get('supplied', 0)} aangeleverd in prompt ({aan})"
            )
        if delen:
            st.caption("Brontransport (kwitantie): " + " · ".join(delen))
        fouten = receipt.get("errors") or []
        if status == "error" or fouten:
            st.error(
                "⚙️ Technische fout bij het verzamelen van bronnen: "
                + ", ".join(
                    f"{f.get('stage')}: {f.get('type')}"
                    for f in fouten
                    if isinstance(f, Mapping)
                )
                + " — dit is geen 'geen bron' en geen fout in de definitie."
            )
        weggelaten = [
            w for w in (receipt.get("omitted") or []) if isinstance(w, Mapping)
        ]
        if weggelaten:
            regels = ", ".join(
                f"{w.get('source_type')}:{w.get('source_id') or '?'} "
                f"({self._WEGGELATEN_REDEN.get(str(w.get('reason')), w.get('reason'))})"
                for w in weggelaten
            )
            st.caption(f"Geselecteerd maar niet in de prompt: {regels}")

    def _render_beoordeeld_onderdeel(
        self, onderdeel: str, deel: Mapping[str, Any]
    ) -> None:
        """Eén AI-onderdeel: status, reden, onzekerheid en de claims met vlag."""
        label = self._ONDERDEELLABEL.get(onderdeel, onderdeel)
        deelstatus = self._DEELSTATUS.get(
            str(deel.get("status")), str(deel.get("status"))
        )
        st.markdown(f"- **{label}**: {deelstatus}")
        if deel.get("reason"):
            st.text(f"  reden: {deel.get('reason')}")
        if deel.get("uncertainty"):
            st.text(f"  onzekerheid: {deel.get('uncertainty')}")
        for claim in deel.get("claims") or []:
            if isinstance(claim, Mapping):
                steun = claim.get("supported")
                vlag = "✅" if steun is True else "❌" if steun is False else "🟠"
                st.text(
                    f"  {vlag} {claim.get('aspect')}: {claim.get('text')}"
                    f" (bron {claim.get('source_id') or '—'})"
                )

    def _render_beoordeling_samenvatting(
        self, assessment: Mapping[str, Any] | None
    ) -> None:
        if not isinstance(assessment, Mapping):
            return
        status = str(assessment.get("status") or "")
        attributie = assessment.get("attribution")
        model = (
            f"{attributie.get('provider') or '?'} · {attributie.get('model') or '?'}"
            if isinstance(attributie, Mapping)
            else "?"
        )
        if status == "assessed":
            st.caption(
                f"🤖 AI-bronbeoordeling ({model}, prompt {assessment.get('prompt_version')}, "
                f"{assessment.get('assessed_at') or 'tijdstip onbekend'}) — herkenbaar als AI; "
                "geen vaststelling."
            )
            for onderdeel, deel in _als_mapping(assessment.get("parts")).items():
                if isinstance(deel, Mapping):
                    self._render_beoordeeld_onderdeel(str(onderdeel), deel)
        elif status == "error":
            fout = _als_mapping(assessment.get("error"))
            st.error(
                f"⚙️ AI-bronbeoordeling technisch mislukt ({fout.get('type') or 'onbekend'}): "
                f"{fout.get('message') or 'geen details'}"
            )
        elif status == "no_sources":
            st.info("ℹ️ Geen bronnen aangeleverd: geen AI-bronbeoordeling uitgevoerd.")
        elif status == "unavailable":
            st.warning("⚙️ Geen bronbeoordelingsdienst beschikbaar bij deze toetsing.")

    def _render_bron_bewijs(
        self,
        src: dict[str, Any],
        identiteit: Any,
        assessment: Mapping[str, Any] | None,
        *,
        verzonden: Mapping[str, Any] | None = None,
        kwitantiestatus: str | None = "afwezig",
        afgekapt: Mapping[str, bool] | None = None,
    ) -> None:
        """Per bron: canoniek id/versie/vindplaats, kwitantie-vlag, AI-oordeel en citaten."""
        source_id = getattr(identiteit, "source_id", None)
        if identiteit is not None:
            st.caption(
                f"Bron-id: {source_id} · versie: {getattr(identiteit, 'version', None) or 'onbekend'}"
                f" · vindplaats: {getattr(identiteit, 'locator', None) or 'onbekend'}"
                f" · profiel (gedeclareerd): {getattr(identiteit, 'declared_profile', None) or 'onbekend'}"
            )
            # DEF-808: door de gebruiker opgegeven coördinaten blijven herkenbaar
            # als opgave (door/op) — geen authenticiteitsbewijs, geen gezag.
            opgave = src.get("declared_metadata")
            if isinstance(opgave, Mapping) and opgave:
                st.caption(
                    "Opgegeven bronmetadata (geen authenticiteitsbewijs): "
                    f"url: {opgave.get('url') or 'geen'} · versie: "
                    f"{opgave.get('source_version') or 'onbekend'} · vindplaats: "
                    f"{opgave.get('locator') or 'onbekend'} — opgegeven door "
                    f"{opgave.get('declared_by') or 'onbekend'} op "
                    f"{opgave.get('declared_at') or 'onbekend tijdstip'}."
                )
            # F6/C5: drie rollen, elk onder eigen label, niets overschreven:
            # (1) de aangeleverde/generatiepassage (fragment hierboven);
            # (2) de canonieke opgeslagen passage (kernregel: `prompt_content`
            #     als aanwezig, anders snippet/chunk_text/content) — de bron
            #     waar een citaat in moet staan, maar níet per se wat de
            #     beoordeling zag (kan > afkapgrens zijn);
            # (3) "Wat de beoordeling zag": uitsluitend uit een door de kern
            #     gebonden beoordelingskwitantie (C §5a); zonder kwitantie is
            #     de werkelijke modelinvoer onbekend (historisch), bij een niet-
            #     bindende kwitantie wordt niets geclaimd.
            canoniek_passage = str(getattr(identiteit, "passage", "") or "")
            self._render_canonieke_passage(src, canoniek_passage)
            self._render_beoordelingsinvoer(
                source_id,
                canoniek_passage,
                verzonden=verzonden,
                kwitantiestatus=kwitantiestatus,
                afgekapt=afgekapt,
            )
        self._render_generatiekwitantie(src)
        if (
            not isinstance(assessment, Mapping)
            or assessment.get("status") != "assessed"
        ):
            return
        for onderdeel, deel in _als_mapping(assessment.get("parts")).items():
            if isinstance(deel, Mapping):
                self._render_ai_oordeel_per_bron(str(onderdeel), deel, source_id)

    def _render_canonieke_passage(
        self, src: dict[str, Any], canoniek_passage: str
    ) -> None:
        """Rol (2): de canonieke opgeslagen passage, alleen apart als zij afwijkt."""
        aangeleverd = str(
            src.get("snippet")
            or src.get("context")
            or src.get("chunk_text")
            or src.get("content")
            or ""
        )
        preview = self._SNIPPET_PREVIEW_CHARS
        if canoniek_passage and canoniek_passage != aangeleverd:
            st.markdown(
                f"**Canonieke opgeslagen passage** (wijkt af van de aangeleverde "
                f"passage, {len(canoniek_passage)} tekens):"
            )
            st.text(
                canoniek_passage[:preview]
                + ("…" if len(canoniek_passage) > preview else "")
            )
            if len(canoniek_passage) > preview:
                st.markdown("Volledige canonieke passage:")
                st.text(canoniek_passage)
        elif canoniek_passage:
            st.caption(
                "Canonieke opgeslagen passage = de aangeleverde passage hierboven."
            )
        else:
            st.caption("Canonieke opgeslagen passage: leeg (geen inhoud aangeleverd).")

    def _render_beoordelingsinvoer(
        self,
        source_id: Any,
        canoniek_passage: str,
        *,
        verzonden: Mapping[str, Any] | None,
        kwitantiestatus: str | None,
        afgekapt: Mapping[str, bool] | None,
    ) -> None:
        """Rol (3): "Wat de beoordeling zag" uit een gebonden kwitantie; anders
        onbekend (historisch), niet vast te stellen (niet bindend) of afwezig."""
        preview = self._SNIPPET_PREVIEW_CHARS
        gezien = (verzonden or {}).get(source_id) if source_id else None
        if kwitantiestatus is None and gezien is not None and source_id is not None:
            inhoud = str(getattr(gezien, "passage", "") or "")
            is_afgekapt = bool((afgekapt or {}).get(source_id))
            st.markdown(
                "**Wat de beoordeling zag** (gebonden beoordelingskwitantie"
                + (
                    f"; afgekapt: {len(inhoud)} van {len(canoniek_passage)} tekens"
                    if is_afgekapt
                    else f"; volledig, {len(inhoud)} tekens"
                )
                + "):"
            )
            st.text(inhoud[:preview] + ("…" if len(inhoud) > preview else ""))
            if len(inhoud) > preview:
                st.markdown("Volledige verzonden passage:")
                st.text(inhoud)
        elif kwitantiestatus == "afwezig":
            st.caption(
                "Wat de beoordeling zag: onbekend — geen beoordelingskwitantie "
                "bij deze beoordeling (historisch of niet uitgevoerd); de "
                "opgeslagen passage hierboven blijft leesbaar."
            )
        elif kwitantiestatus is not None:
            st.caption(
                "Wat de beoordeling zag: niet vast te stellen — de kwitantie bindt "
                "niet aan de opgeslagen bronnen (zie melding boven de bronnen)."
            )
        else:
            st.caption(
                "Wat de beoordeling zag: deze bron staat niet in de gebonden kwitantie."
            )

    def _render_generatiekwitantie(self, src: dict[str, Any]) -> None:
        """Geselecteerd vs. werkelijk gebruikt (E-kwitantie): een aangeleverde
        bron is pas steun als zij werkelijk in de prompt stond."""
        if src.get("used_in_prompt"):
            nr = src.get("receipt_nr")
            extra = []
            if src.get("truncated"):
                extra.append("afgekapt")
            if src.get("sanitized"):
                extra.append("gesanitiseerd")
            st.caption(
                "Generatie (kwitantie): werkelijk in de prompt"
                + (f" als bron nr {nr}" if nr is not None else "")
                + (f" ({', '.join(extra)})" if extra else "")
                + " — dit zegt niets over gezag of betekenissteun."
            )
        elif src.get("omitted_reason"):
            st.warning(
                "Generatie (kwitantie): geselecteerd maar NIET in de prompt: "
                f"{self._WEGGELATEN_REDEN.get(str(src.get('omitted_reason')), src.get('omitted_reason'))}"
                " — geen generatiesteun uit deze bron; de AI-bronbeoordeling "
                "hieronder staat daar los van."
            )
        elif src.get("used_in_prompt") is False:
            st.caption("Generatie (kwitantie): niet in de prompt gebruikt.")

    def _render_ai_oordeel_per_bron(
        self, onderdeel: str, deel: Mapping[str, Any], source_id: Any
    ) -> None:
        """Het AI-oordeel en de geverifieerde citaten van één onderdeel voor deze bron."""
        label = self._ONDERDEELLABEL.get(onderdeel, onderdeel)
        for oordeel in deel.get("sources") or []:
            if isinstance(oordeel, Mapping) and oordeel.get("source_id") == source_id:
                velden = []
                if "profile" in oordeel:
                    velden.append(f"profiel {oordeel.get('profile')}")
                if "applicable" in oordeel:
                    velden.append(f"toepasselijk: {oordeel.get('applicable')}")
                if "locatable" in oordeel:
                    velden.append(f"terugvindbaar: {oordeel.get('locatable')}")
                st.markdown(f"**AI · {label}**: {', '.join(velden) or '—'}")
                if oordeel.get("reason"):
                    st.text(str(oordeel.get("reason")))
        for bewijs in deel.get("evidence") or []:
            if isinstance(bewijs, Mapping) and bewijs.get("source_id") == source_id:
                st.markdown(f"**Geverifieerd citaat ({label})**:")
                st.text(str(bewijs.get("quote") or ""))

    def _render_afgewezen_claims(self, assessment: Mapping[str, Any] | None) -> None:
        if not isinstance(assessment, Mapping):
            return
        afgewezen = [
            r for r in (assessment.get("rejected") or []) if isinstance(r, Mapping)
        ]
        if not afgewezen:
            return
        with st.expander(
            f"⚠️ {len(afgewezen)} modelclaim(s) afgewezen (onbewezen of verzonnen)",
            expanded=False,
        ):
            for r in afgewezen:
                st.text(f"[{r.get('part')}] {r.get('reason')}: {r.get('detail') or ''}")

    def _render_uitzondering(
        self,
        review: Mapping[str, Any] | None,
        review_status: Mapping[str, Any] | None,
    ) -> None:
        """De deskundige uitzondering (platte, getypeerde vorm) als uitzondering."""
        if not isinstance(review, Mapping) or not review:
            return
        soort = str(review.get("type") or "")
        label = self._REVIEW_TYPE_LABEL.get(
            soort, f"Deskundige beoordeling ({soort or 'onbekend type'})"
        )
        verouderd = (
            isinstance(review_status, Mapping)
            and review_status.get("status") == "stale"
        )
        kop = f"🧑‍⚖️ {label}" + (" — VEROUDERD" if verouderd else "")
        st.markdown(f"**{kop}**")
        st.caption(
            f"Vastgelegd door {review.get('actor') or 'onbekend'} "
            f"op {review.get('reviewed_at') or 'onbekend tijdstip'} "
            f"(recordversie {review.get('version_number')}); "
            f"geaccepteerd: {'ja' if review.get('accepted') is True else 'nee'}. "
            + (
                "Een correctie vervangt het oordeel over één onderdeel; het "
                "oorspronkelijke AI-oordeel blijft zichtbaar. Geen vaststelling."
                if soort == "part_correction"
                else "Een uitzondering is geen positieve bronbeoordeling en geen vaststelling."
            )
        )
        if review.get("rationale"):
            st.text(f"Motivering: {review.get('rationale')}")
        if soort == "reference_exception":
            st.text(
                f"Bron-id: {review.get('source_id')} · versie: {review.get('source_version') or 'onbekend'}"
                f" · vindplaats: {review.get('locator')} · inhoudshash: {review.get('content_hash')}"
            )
        elif soort == "part_correction":
            st.text(
                f"Onderdeel: {self._ONDERDEELLABEL.get(str(review.get('part_id')), review.get('part_id'))}"
                f" · deskundig oordeel: {self._DEELSTATUS.get(str(review.get('status')), review.get('status'))}"
            )
            for claim in review.get("evidence") or []:
                if isinstance(claim, Mapping):
                    st.text(
                        f"Bewijs: bron {claim.get('source_id')} · versie "
                        f"{claim.get('source_version') or 'onbekend'} · vindplaats "
                        f"{claim.get('locator') or 'onbekend'}\n  citaat: {claim.get('quote')}"
                    )
        elif soort == "no_appropriate_source":
            zoek = _als_mapping(review.get("search"))
            st.text(
                "Gezocht met: "
                + ", ".join(str(q) for q in (zoek.get("queries") or []))
                + "\n"
                "Geraadpleegd: "
                + ", ".join(str(c) for c in (zoek.get("consulted") or []))
                + "\n"
                f"Conclusie: {zoek.get('conclusion') or '—'}"
            )

    def _render_document_source_details(self, src: dict[str, Any]) -> None:
        """DEF-743: Render filename/location and selection basis of an upload.

        The numeric document score only marks a term match and is not shown;
        without a recorded ``selection_basis`` no basis is invented.
        """
        fname = src.get("title") or src.get("filename")
        cite = src.get("citation_label")
        if fname or cite:
            st.markdown(
                f"**Document**: {fname or '(onbekend)'}"
                f"{f' · Locatie: {cite}' if cite else ''}"
            )
        basis = src.get("selection_basis")
        if basis:
            st.markdown(
                f"**Selectie**: {self._SELECTION_BASIS_LABELS.get(basis, basis)}"
            )
