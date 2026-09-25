"""
Enhanced Context Awareness Module - Intelligent context processing met adaptieve formatting.

Deze module integreert alle business logic van de Context Aware builder:
1. Context richness scoring (0.0-1.0)
2. Dynamische prompt aanpassing op basis van context kwaliteit
3. Neutrale bronpresentatie (route + inhoud; DEF-743: geen confidence-label —
   `confidence_indicators` in de config heeft geen renderend effect meer)
4. Advanced source formatting
5. Abbreviation/expansion handling
6. Verwerking van V2-contexten (organisatorisch, juridisch, wettelijk)
"""

import logging
from typing import Any

from services.definition_generator_context import ContextSource, EnrichedContext
from services.prompts.sanitization import (
    TAG_CONTEXT,
    VeiligeTekst,
    datablok,
    normaliseer_prompt_tekst,
    sanitize_prompt_blok,
)

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)

# DEF-590: ruim bemeten — documenten worden elders al samengevat. De cap is een
# vangnet tegen een prompt die door één upload onwerkbaar groot wordt, geen
# functionele limiet.
_MAX_CONTEXT_BLOK_LEN = 20_000


#: DEF-751 stap 2: het kopje waaronder het gebruikersantwoord op een gemeld
#: betekenisconflict in het `context`-datablok staat. Eén constante, zodat de
#: instructie in `DefinitionTaskModule` en de data hier naar hetzelfde wijzen.
VERDUIDELIJKING_KOP = "Verduidelijking van de bedoelde betekenislaag door de gebruiker"

#: Antwoordbudget voor de verduidelijking, gemeten ná escaping
#: (reviewcorrectie 1/2). Een antwoord dat hier niet in past wordt vóór de
#: modelaanroep zichtbaar geweigerd (orchestrator) — nooit stil afgekapt.
MAX_VERDUIDELIJKING_LEN = 4_000


def _volledig_gesaniteerd(tekst: str) -> VeiligeTekst:
    """`sanitize_prompt_blok` zonder afkap: `max_len` op de genormaliseerde lengte.

    De sanitizer kapt af op de NFKC-genormaliseerde tekst; die kan langer zijn
    dan de invoer (ligatuur `ﬁ` → `fi`, `ﷺ` → 18 tekens). Een `max_len` op de
    lengte vóór normalisatie kapte daarom stil af (Unicode-correctie op
    reviewbevinding 1). De whitespace-normalisatie van de sanitizer maakt de
    tekst hoogstens korter, dus de genormaliseerde lengte + 1 is altijd ruim.
    """
    return sanitize_prompt_blok(tekst, len(normaliseer_prompt_tekst(tekst)) + 1)


def verduidelijking_datalijn(waarde: str) -> str:
    """De exacte DATA-regel (ná normalisatie/sanitisatie/escaping) in het contextblok.

    Eén functie voor module én orchestrator: de orchestrator toetst vóór de
    modelaanroep dat precies deze regel volledig in de gebouwde prompt staat
    (postconditie "gebruikt = werkelijk aanwezig"). Nooit afgekapt — het
    budget wordt apart getoetst (`verduidelijking_te_lang`).
    """
    tekst = " ".join(waarde.split())
    return f"{VERDUIDELIJKING_KOP}: {_volledig_gesaniteerd(tekst)}"


def verduidelijking_te_lang(waarde: str) -> bool:
    """Of het antwoord ná escaping boven `MAX_VERDUIDELIJKING_LEN` uitkomt."""
    lijn = verduidelijking_datalijn(waarde)
    return len(lijn) - len(VERDUIDELIJKING_KOP) - 2 > MAX_VERDUIDELIJKING_LEN


def _verduidelijking_uit(context: ModuleContext) -> str | None:
    """De gebruikersverduidelijking uit de metadata, of None.

    Bewust géén `ContextSource` — die zou als "ADDITIONELE BRON" onder CON-02
    vallen en een gebruikersbedoeling tot bron maken. Zonder verduidelijking
    blijft de prompt byte-identiek.
    """
    waarde = (context.enriched_context.metadata or {}).get("betekenisverduidelijking")
    if not isinstance(waarde, str) or not waarde.strip():
        return None
    return waarde.strip()


def _sanitize_binnen_budget(tekst: str, budget: int) -> VeiligeTekst:
    """`sanitize_prompt_blok`, maar met het budget gemeten ná escaping.

    De gedeelde sanitizer kapt vóór het escapen af (DEF-590: geen entity
    middendoor). Escaping kan de tekst tot 5× laten groeien (`&` → `&amp;`),
    dus hier wordt eerst een rauwe grens gezocht waarvan het geëscapete
    resultaat binnen `budget` past; de sanitisatie is de laatste stap.
    """
    voorstuk = _rauwe_grens_binnen_budget(tekst, budget)
    return _volledig_gesaniteerd(voorstuk)


def _veilig_datablok(regels: list[str], context: ModuleContext | None = None) -> str:
    """Sanitiseer de regels en omhul ze in één `context`-datablok.

    Alle drie de contextsecties (rich/moderate/minimal) lopen hierlangs. Dat is
    de enige plek waar user-data de definitie-prompt in gaat, dus de enige plek
    die het hoeft te weten. `datablok()` faalt luid als hier ooit iets
    ongesaniteerds doorheen glipt.

    Budget (reviewcorrectie 1/2): het blok blijft ≤ `_MAX_CONTEXT_BLOK_LEN`
    gemeten ná escaping. Een gebruikersverduidelijking krijgt voorrang als
    laatste DATA-regel — volledig, nooit afgekapt; de overige regels
    (documentinhoud enz.) krijgen het restant.
    """
    rest_rauw = "\n".join(regels)
    verduidelijking = _verduidelijking_uit(context) if context is not None else None
    if verduidelijking is None:
        return datablok(
            TAG_CONTEXT, _sanitize_binnen_budget(rest_rauw, _MAX_CONTEXT_BLOK_LEN)
        )

    # Dezelfde whitespace-samenvoeging als `verduidelijking_datalijn`, zodat
    # de staart van het blok letterlijk die controletekst is.
    staart_rauw = f"{VERDUIDELIJKING_KOP}: {' '.join(verduidelijking.split())}"
    lijn = verduidelijking_datalijn(verduidelijking)
    if len(lijn) >= _MAX_CONTEXT_BLOK_LEN:
        # Laatste vangnet; de orchestrator weigert dit al vóór de modelaanroep.
        return datablok(
            TAG_CONTEXT, _sanitize_binnen_budget(staart_rauw, _MAX_CONTEXT_BLOK_LEN)
        )
    # Grens voor de rest (in het genormaliseerde domein) zó dat rest (ná
    # escaping) + newline + staart binnen het blokbudget blijft; daarna één
    # sanitisatie van de samengestelde tekst als laatste stap (DEF-590-
    # contract), zonder afkap (`_volledig_gesaniteerd`). Het resultaat wordt
    # geverifieerd — budget én volledige staart — en anders met een kleinere
    # rest opnieuw opgebouwd; met een lege rest is het resultaat de staart zelf.
    rest_budget = _MAX_CONTEXT_BLOK_LEN - len(lijn) - 1
    while True:
        rest_deel = _rauwe_grens_binnen_budget(rest_rauw, rest_budget)
        samengesteld = f"{rest_deel}\n{staart_rauw}" if rest_deel else staart_rauw
        veilig = _volledig_gesaniteerd(samengesteld)
        if len(veilig) <= _MAX_CONTEXT_BLOK_LEN and veilig.endswith(lijn):
            return datablok(TAG_CONTEXT, veilig)
        if not rest_deel:
            # Kan alleen als de staart zelf niet past; hierboven al afgevangen.
            return datablok(TAG_CONTEXT, veilig)
        rest_budget = min(rest_budget - 1, len(rest_deel) // 2)


def _rauwe_grens_binnen_budget(tekst: str, budget: int) -> str:
    """Het (NFKC-genormaliseerde) voorstuk van `tekst` waarvan de gesaniteerde
    vorm ≤ `budget` is.

    Zoekt en snijdt op de genormaliseerde tekst. NFKC is idempotent, dus een
    voorstuk daarvan expandeert niet meer bij de latere sanitisatie, en de
    whitespace-normalisatie maakt het hoogstens korter. De gemeten lengte is
    daarmee een bovengrens voor het werkelijke resultaat.
    """
    genormaliseerd = normaliseer_prompt_tekst(tekst)
    grens = min(len(genormaliseerd), max(budget, 0))
    while grens > 0 and len(sanitize_prompt_blok(genormaliseerd, grens)) > budget:
        grens = min(
            grens - 1,
            int(grens * budget / len(sanitize_prompt_blok(genormaliseerd, grens))),
        )
    return genormaliseerd[: max(grens, 0)]


class ContextAwarenessModule(BasePromptModule):
    """
    Enhanced module voor intelligente context verwerking.

    Combineert alle context processing logic in één module:
    - Context richness scoring
    - Adaptive formatting based on context quality
    - Bronpresentatie: route + inhoud, zonder gezags-/confidence-label (DEF-743)
    - Abbreviation handling
    - V2-contextverwerking: organisatorisch/juridisch/wettelijk (geen legacy 'domein')

    DEF-188: Added IMPLICIT_CONTEXT_MECHANISMS teaching GPT-4 HOW to embed context.
    """

    # DEF-622 (B-02): de CON-01-norm voor namen uit de context. Bewust één
    # tekst voor alle formatteringsniveaus, zodat de generator nooit een
    # absoluut naamverbod krijgt waar de norm een noodzakelijke naam toestaat.
    CONTEXTNAAM_NORM = (
        "De registratiecontext (waar de definitie geldt) hoort bij het record, "
        "niet in de definitiezin: vermeld haar niet als registratiecontext "
        "(geen 'binnen [organisatie]', 'volgens [wet]' of 'in de context van'). "
        "Een naam uit de context mag alléén in de zin staan als die inhoudelijk "
        "noodzakelijk is om het begrip af te bakenen of te identificeren "
        "(bijvoorbeeld de exclusieve uitgever van een keurmerk)."
    )

    # DEF-188: 3 Mechanisms for implicit context processing
    IMPLICIT_CONTEXT_MECHANISMS = """
📌 HOE CONTEXT IMPLICIET VERWERKEN (3 Mechanismen):

**MECHANISME 1 - VOCABULAIRE:**
Gebruik domein-specifieke termen.
❌ "persoon" → ✅ "verdachte" (strafrechtelijk)
❌ "gebouw" → ✅ "penitentiaire inrichting" (DJI)
❌ "straf" → ✅ "sanctie" (formeel juridisch)

**MECHANISME 2 - SCOPE:**
Kies het domeinspecifieke woord binnen de afbakening die de bron geeft; maak de betekenis niet smaller dan de bron met een extra qualifier, zoals een eigenschap die volgens de bron mag wisselen.
❌ "regels" → ✅ "gedragsregels"
❌ "beslissing" → ✅ "beschikking"
❌ "procedure" → ✅ "formele procedure"

**MECHANISME 3 - RELATIES:**
Refereer context-specifieke verbanden.
❌ "herhaling" → ✅ "recidive"
❌ "begeleiding" → ✅ "reclasseringstoezicht"
❌ "functionaris" → ✅ "officier van justitie"

🧪 TEST: Is elke naam in de zin inhoudelijk noodzakelijk voor de afbakening, en is er niets (kenmerk, register, nummer) toegevoegd alleen om de context herkenbaar te maken?
"""

    def __init__(self) -> None:
        """Initialize de enhanced context awareness module."""
        super().__init__(
            module_id="context_awareness",
            module_name="Enhanced Context Processing Module",
            priority=70,  # Hoge prioriteit - context is belangrijk
        )
        self.adaptive_formatting = True
        self.confidence_indicators = True
        self.include_abbreviations = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.adaptive_formatting = config.get("adaptive_formatting", True)
        self.confidence_indicators = config.get("confidence_indicators", True)
        self.include_abbreviations = config.get("include_abbreviations", True)
        self._initialized = True
        logger.debug(
            f"Enhanced ContextAwarenessModule geïnitialiseerd "
            f"(adaptive={self.adaptive_formatting}, confidence={self.confidence_indicators})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer input - deze module werkt altijd (ook bij geen context).

        Args:
            context: Module context

        Returns:
            (True, None) - module werkt altijd
        """
        # Deze module werkt altijd - zelfs bij geen context
        # Dan geeft het aan dat er geen context beschikbaar is
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer adaptive context sectie gebaseerd op context richness.

        Args:
            context: Module context

        Returns:
            ModuleOutput met adaptive context formatting
        """
        try:
            # Bereken context richness score
            context_score = self._calculate_context_score(context.enriched_context)

            # Sla score op voor andere modules
            context.set_shared("context_richness_score", context_score)

            # Bepaal formatting strategie op basis van score
            if context_score >= 0.8:
                content = self._build_rich_context_section(context)
                formatting_level = "rich"
            elif context_score >= 0.5:
                content = self._build_moderate_context_section(context)
                formatting_level = "moderate"
            else:
                content = self._build_minimal_context_section(context)
                formatting_level = "minimal"

            # Extract en deel traditionele context voor andere modules
            self._share_traditional_context(context)

            return ModuleOutput(
                content=content,
                metadata={
                    "context_score": context_score,
                    "formatting_level": formatting_level,
                    "adaptive_formatting": self.adaptive_formatting,
                    "sources_count": len(context.enriched_context.sources),
                    "base_context_items": sum(
                        len(items)
                        for items in context.enriched_context.base_context.values()
                    ),
                    "expanded_terms_count": len(
                        context.enriched_context.expanded_terms or {}
                    ),
                },
            )

        except Exception as e:
            logger.error(
                f"Enhanced ContextAwarenessModule execution failed: {e}", exc_info=True
            )
            return ModuleOutput(
                content=self._build_fallback_context_section(),
                metadata={"error": str(e), "fallback_used": True},
                success=False,
                error_message=f"Failed to generate enhanced context section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _calculate_context_score(self, enriched_context: EnrichedContext) -> float:
        """
        Bereken context richheid score (0.0 - 1.0).

        Gebaseerd op ContextAwarePromptBuilder logic.

        Args:
            enriched_context: EnrichedContext object

        Returns:
            Score tussen 0.0 en 1.0
        """
        score = 0.0

        # Base context contribution (max 0.3)
        total_base_items = sum(
            len(items) for items in enriched_context.base_context.values()
        )
        score += min(total_base_items / 10, 0.3)

        # Sources contribution (max 0.4)
        if enriched_context.sources:
            source_score = sum(
                source.confidence for source in enriched_context.sources
            ) / len(enriched_context.sources)
            score += source_score * 0.4

        # Expanded terms contribution (max 0.2)
        if enriched_context.expanded_terms:
            score += min(len(enriched_context.expanded_terms) / 5, 0.2)

        # Confidence scores contribution (max 0.1)
        if (
            hasattr(enriched_context, "confidence_scores")
            and enriched_context.confidence_scores
        ):
            avg_confidence = sum(enriched_context.confidence_scores.values()) / len(
                enriched_context.confidence_scores
            )
            score += avg_confidence * 0.1

        return min(score, 1.0)

    def _build_rich_context_section(self, context: ModuleContext) -> str:
        """
        Build uitgebreide context sectie voor rijke context (score ≥ 0.8).

        Args:
            context: Module context

        Returns:
            Uitgebreide context sectie
        """
        sections = []
        enriched_context = context.enriched_context

        sections.append("📊 UITGEBREIDE CONTEXT ANALYSE:")
        sections.append(
            "⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren voor deze organisatorische, juridische en wettelijke setting. Maak de definitie contextspecifiek. "
            + self.CONTEXTNAAM_NORM
        )
        sections.append("")

        # DEF-590: alles hieronder is user-data (base_context, de tekst van
        # geüploade documenten via `sources`, en de afkortingen). Die hoort in
        # één datablok — onze eigen instructies blijven er bewust buiten.
        blok_regels: list[str] = list(
            self._format_detailed_base_context(enriched_context.base_context)
        )

        # Aangeleverde contextbronnen: route + inhoud, zonder gezagslabel (DEF-743)
        if enriched_context.sources:
            blok_regels.append("")
            blok_regels.extend(self._format_sources(enriched_context.sources))

        # Expanded terms
        if self.include_abbreviations and enriched_context.expanded_terms:
            blok_regels.append("")
            blok_regels.extend(
                self._format_abbreviations_detailed(enriched_context.expanded_terms)
            )

        # DEF-751 stap 2: een gebruikersverduidelijking komt als laatste
        # DATA-regel binnen het blok, met voorrang op het budget.
        sections.append(_veilig_datablok(blok_regels, context))

        # DEF-188: Add implicit context mechanisms
        sections.append("")
        sections.append(self.IMPLICIT_CONTEXT_MECHANISMS.strip())

        return "\n".join(sections)

    def _build_moderate_context_section(self, context: ModuleContext) -> str:
        """
        Build standaard context sectie voor matige context (0.5 ≤ score < 0.8).

        Args:
            context: Module context

        Returns:
            Standaard context sectie
        """
        sections = []
        enriched_context = context.enriched_context

        sections.append("📌 VERPLICHTE CONTEXT INFORMATIE:")
        sections.append(
            "⚠️ BELANGRIJKE INSTRUCTIE: Verwerk de onderstaande context IMPLICIET in de definitie. "
            "Maak de definitie specifiek voor deze context door je woordkeuze en formulering aan te passen. "
            + self.CONTEXTNAAM_NORM
        )
        sections.append("")

        # Basis context formatting. DEF-590: de contexttekst bevat de inhoud van
        # geüploade documenten (`source.content`, confidence > 0.7) — tekst die de
        # gebruiker niet zelf schreef. Sanitiseren en in een datablok.
        context_text = enriched_context.get_all_context_text()

        # De afkortingen horen binnen hetzelfde datablok: ook al zijn hun sleutels
        # whitelist-gebonden, ze zijn afgeleid van user-input en horen niet als
        # instructie-tekst gelezen te worden.
        blok_regels: list[str] = []
        if context_text:
            blok_regels.append(context_text)
        if self.include_abbreviations and enriched_context.expanded_terms:
            if blok_regels:
                blok_regels.append("")
            blok_regels.append("AFKORTINGEN:")
            blok_regels.extend(
                self._format_abbreviations_simple(enriched_context.expanded_terms)
            )
        # DEF-751 stap 2: een gebruikersverduidelijking komt als laatste
        # DATA-regel binnen het blok, met voorrang op het budget.
        if blok_regels or _verduidelijking_uit(context):
            sections.append("🎯 SPECIFIEKE CONTEXT VOOR DEZE DEFINITIE:")
            sections.append(_veilig_datablok(blok_regels, context))
        else:
            sections.append("Geen specifieke context beschikbaar.")

        # DEF-188: Add implicit context mechanisms
        sections.append("")
        sections.append(self.IMPLICIT_CONTEXT_MECHANISMS.strip())

        return "\n".join(sections)

    def _build_minimal_context_section(self, context: ModuleContext) -> str:
        """
        Build minimale context sectie voor beperkte context (score < 0.5).

        Args:
            context: Module context

        Returns:
            Minimale context sectie
        """
        enriched_context = context.enriched_context
        # DEF-590: ook het minimale pad draagt document-content; zelfde behandeling.
        context_text = enriched_context.get_all_context_text()

        # DEF-188: Add mechanisms even for minimal context
        mechanisms = f"\n\n{self.IMPLICIT_CONTEXT_MECHANISMS.strip()}"

        if context_text:
            # DEF-751 stap 2: een gebruikersverduidelijking komt als laatste
            # DATA-regel binnen het blok, met voorrang op het budget.
            base = (
                f"📍 VERPLICHTE CONTEXT:\n{_veilig_datablok([context_text], context)}\n"
                "⚠️ INSTRUCTIE: Formuleer de definitie specifiek voor bovenstaande "
                "organisatorische, juridische en wettelijke context. "
                + self.CONTEXTNAAM_NORM
            )
            return base + mechanisms

        return "📍 Context: Geen specifieke context beschikbaar." + mechanisms

    def _format_detailed_base_context(self, base_context: dict) -> list[str]:
        """
        Format base context met categorieën voor rijke context.

        Args:
            base_context: Dictionary met base context

        Returns:
            Lijst van geformatteerde context regels
        """
        sections = []

        for context_type, items in base_context.items():
            if items:
                sections.append(f"{context_type.upper()}:")
                if isinstance(items, list):
                    for item in items:
                        sections.append(f"  • {item}")
                else:
                    sections.append(f"  • {items}")

        return sections

    def _format_sources(self, sources: list[ContextSource]) -> list[str]:
        """
        Format aangeleverde contextbronnen: route + inhoud.

        DEF-743: het vroegere `[high] Document (confidence=0.90)` kwam uit een
        vaste constante (`definition_generator_context`: 0.9 voor
        `document_context`) en suggereerde gezag/betrouwbaarheid. Een
        aanvoerroute of confidence is geen bewijs van brongezag; dat oordeel
        valt onder CON-02 op de brongegevens. De 150-tekenspreview en de
        plaats binnen het `context`-datablok zijn ongewijzigd.

        Args:
            sources: Lijst van source objecten

        Returns:
            Lijst van geformatteerde source regels
        """
        sections = ["ADDITIONELE BRONNEN:"]

        for source in sources:
            sections.append(
                f"  {source.source_type.title()}: {source.content[:150]}..."
            )

        return sections

    def _format_abbreviations_detailed(self, expanded_terms: dict) -> list[str]:
        """
        Format afkortingen voor rijke context.

        Args:
            expanded_terms: Dictionary met afkortingen

        Returns:
            Lijst van geformatteerde afkortingen
        """
        sections = ["AFKORTINGEN & UITBREIDINGEN:"]
        for abbr, expansion in expanded_terms.items():
            sections.append(f"  • {abbr} = {expansion}")

        return sections

    def _format_abbreviations_simple(self, expanded_terms: dict) -> list[str]:
        """
        Format afkortingen voor matige context.

        Args:
            expanded_terms: Dictionary met afkortingen

        Returns:
            Lijst van geformatteerde afkortingen
        """
        if not expanded_terms:
            return ["Geen afkortingen gedetecteerd."]

        return [f"- {abbr}: {expansion}" for abbr, expansion in expanded_terms.items()]

    def _share_traditional_context(self, context: ModuleContext) -> None:
        """
        Deel alle actieve context types voor andere modules.

        EPIC-010: Harmonisatie van context handling
        - Verwijderd: legacy 'domein' field (gebruik juridische_context)
        - Toegevoegd: juridical_contexts en legal_basis_contexts sharing

        Args:
            context: Module context
        """
        base_context = context.enriched_context.base_context

        # Extract alle ACTIEVE contexten (domein is legacy en wordt niet meer gebruikt)
        org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
        jur_contexts = self._extract_contexts(base_context.get("juridisch"))
        wet_contexts = self._extract_contexts(base_context.get("wettelijk"))

        # Deel alle actieve contexten voor andere modules
        if org_contexts:
            context.set_shared("organization_contexts", org_contexts)
        if jur_contexts:
            context.set_shared("juridical_contexts", jur_contexts)
        if wet_contexts:
            context.set_shared("legal_basis_contexts", wet_contexts)

        # Legacy domein wordt NIET meer gedeeld (EPIC-010)

    def _extract_contexts(self, context_value: Any) -> list[str]:
        """
        Extract context lijst uit verschillende input formaten.

        Backwards compatibility method.

        Args:
            context_value: Context waarde (bool, str, list, etc.)

        Returns:
            Lijst van context strings
        """
        if not context_value:
            return []

        # Handle verschillende input types
        if isinstance(context_value, bool):
            # Legacy support: True betekent geen specifieke context
            return []
        if isinstance(context_value, str):
            return [context_value]
        if isinstance(context_value, list):
            return [str(item) for item in context_value if item]

        logger.warning(
            f"Onbekend context type: {type(context_value)} - {context_value}"
        )
        return []

    def _build_fallback_context_section(self) -> str:
        """
        Build fallback context sectie bij errors.

        Returns:
            Fallback context sectie
        """
        return "📍 Context: Context verwerking gefaald, geen specifieke context beschikbaar."
