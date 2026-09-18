"""
JSON-Based Rules Module - Generieke base voor JSON toetsregel modules.

DEF-156 Phase 1: Consolidatie van 5 identieke rule modules
- AraiRulesModule (ARAI)
- ConRulesModule (CON)
- EssRulesModule (ESS)
- SamRulesModule (SAM)
- VerRulesModule (VER)

Deze modules zijn 100% identiek, behalve voor:
- rule_prefix (filter voor JSON keys)
- module_id
- module_name
- header_emoji
- priority

Door deze parameters te externaliseren, reduceren we 640 lines naar 128 lines
(512 line reduction = 80% code eliminatie).
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput
from .ess02_aanwijzing import GEDEELDE_ESS02_AANWIJZING

logger = logging.getLogger(__name__)

# DEF-743: de con_rules-module is altijd actief omdat de bronbasisnorm (CON-02)
# ongeacht context geldt. Alle overige CON-regels (CON-01 contextcontract
# DEF-622, CON-CIRC-001, toekomstige) zijn contextgebonden en worden alleen
# getoond als `has_any_context()` waar is — smal: een no-context-prompt krijgt
# precies de bronregel erbij en niets anders; met context is de set ongewijzigd.
_CONTEXTGEBONDEN_PREFIX = "CON-"
_CONTEXTVRIJE_REGELS: frozenset[str] = frozenset({"CON-02"})


def _is_contextgebonden(regel_key: str) -> bool:
    return (
        regel_key.startswith(_CONTEXTGEBONDEN_PREFIX)
        and regel_key not in _CONTEXTVRIJE_REGELS
    )


class JSONBasedRulesModule(BasePromptModule):
    """
    Generieke module voor validatieregels die uit JSON worden geladen.

    Deze module implementeert het volledige pattern voor JSON-based regel modules:
    1. Load regels from cached toetsregel manager
    2. Filter regels by prefix (ARAI, CON, ESS, SAM, VER)
    3. Format rules met emoji, naam, uitleg, toetsvraag, voorbeelden
    4. Generate markdown sectie met header

    Parameters:
        rule_prefix: Prefix voor filteren (bijv. "ARAI", "CON-")
        module_id: Unieke identifier (bijv. "arai_rules")
        module_name: Display naam (bijv. "ARAI Validation Rules")
        header_emoji: Emoji voor sectie header (bijv. "✅")
        header_text: Display tekst in header (bijv. "Algemene Regels AI (ARAI)")
        priority: Execution priority (60-75)

    Example:
        >>> module = JSONBasedRulesModule(
        ...     rule_prefix="ARAI",
        ...     module_id="arai_rules",
        ...     module_name="ARAI Validation Rules",
        ...     header_emoji="✅",
        ...     header_text="Algemene Regels AI (ARAI)",
        ...     priority=75
        ... )
    """

    def __init__(
        self,
        rule_prefix: str,
        module_id: str,
        module_name: str,
        header_emoji: str,
        header_text: str,
        priority: int,
    ):
        """
        Initialize generic JSON-based rules module.

        Args:
            rule_prefix: Prefix voor filtering (bijv. "ARAI", "CON-")
            module_id: Unieke identifier
            module_name: Display naam
            header_emoji: Emoji voor header
            header_text: Tekst voor header
            priority: Execution priority (60-75)
        """
        super().__init__(
            module_id=module_id, module_name=module_name, priority=priority
        )
        self.rule_prefix = rule_prefix
        self.header_emoji = header_emoji
        self.header_text = header_text
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie met optionele 'include_examples' boolean
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        logger.debug(
            f"JSONBasedRulesModule '{self.module_id}' geïnitialiseerd "
            f"(prefix={self.rule_prefix}, examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd.

        Args:
            context: Module context (niet gebruikt)

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer validatieregels sectie voor specifieke prefix.

        Args:
            context: Module context; alleen `enriched_context.has_any_context()`
                wordt gelezen, voor de contextgebonden regels (DEF-743).

        Returns:
            ModuleOutput met:
            - content: Markdown sectie met header + formatted rules
            - metadata: rules_count (getoond), rules_skipped (contextgebonden,
              niet getoond), include_examples, rule_prefix
        """
        try:
            sections = []

            # Header: ### {emoji} {text}:
            sections.append(f"### {self.header_emoji} {self.header_text}:")

            # Load toetsregels on-demand from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter alleen regels met dit prefix
            filtered_rules = {
                k: v for k, v in all_rules.items() if k.startswith(self.rule_prefix)
            }

            # DEF-743: contextgebonden regels alleen tonen als er context is.
            has_context = self._has_any_context(context)
            rules_skipped = sorted(
                k for k in filtered_rules if not has_context and _is_contextgebonden(k)
            )
            shown_rules = {
                k: v for k, v in filtered_rules.items() if k not in rules_skipped
            }

            # Sorteer regels alfabetisch
            sorted_rules = sorted(shown_rules.items())

            # Format elke regel
            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            # Combineer alle secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(shown_rules),
                    "rules_skipped": rules_skipped,
                    "include_examples": self.include_examples,
                    "rule_prefix": self.rule_prefix,
                },
            )

        except Exception as e:
            logger.error(
                f"JSONBasedRulesModule '{self.module_id}' execution failed: {e}",
                exc_info=True,
            )
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate {self.rule_prefix} rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    @staticmethod
    def _has_any_context(context: ModuleContext) -> bool:
        """DEF-743: leest alleen het contextpredicaat; faalt gesloten naar False.

        Zonder (of met een onvolledige) enriched_context wordt een
        contextgebonden regel niet getoond — dezelfde keuze als de
        orchestrator maakt voor `context_awareness`.
        """
        enriched = getattr(context, "enriched_context", None)
        predicate = getattr(enriched, "has_any_context", None)
        if not callable(predicate):
            return False
        try:
            return bool(predicate())
        except (AttributeError, TypeError):
            return False

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formateer een regel uit JSON data naar markdown lines.

        Format (na DEF-126 + DEF-171):
        🔹 **REGEL-KEY - Naam**
        - Uitleg tekst
        - **Instructie:** imperatieve instructie (voor TOP 10 regels only)
          ✅ Goed voorbeeld
          ❌ Fout voorbeeld

        DEF-171: Toetsvraag patterns verwijderd (validation → ValidationOrchestratorV2)

        Args:
            regel_key: Regel identifier (bijv. "ARAI-01", "CON-02")
            regel_data: Regel data uit JSON met keys:
                - naam: Regel naam
                - uitleg: Uitleg tekst
                - goede_voorbeelden: List van goede voorbeelden
                - foute_voorbeelden: List van foute voorbeelden

        Returns:
            List van markdown lines voor deze regel
        """
        lines = []

        # Header met emoji: 🔹 **REGEL-KEY - Naam**
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        # Uitleg
        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        # DEF-126: Transform TOP 10 validation questions to instructions
        # DEF-171: Removed Toetsvraag fallback (validation handled by ValidationOrchestratorV2)
        instruction = self._get_instruction_for_rule(regel_key)
        if instruction:
            lines.append(f"- **Instructie:** {instruction}")

        # Voorbeelden (indien enabled in config)
        if self.include_examples:
            # Goede voorbeelden: ✅ tekst
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            # Foute voorbeelden: ❌ tekst
            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines

    def _get_instruction_for_rule(self, regel_key: str) -> str | None:
        """
        DEF-126: Transform validation questions to generation instructions.

        Returns instruction for TOP 10 highest-impact rules, None for others.

        Args:
            regel_key: Regel identifier (bijv. "ARAI-01")

        Returns:
            Instruction string or None if not in TOP 10
        """
        # DEF-126 Phase 1 + Phase 2 transformation mapping
        instruction_map = {
            # ARAI rules (Algemene Regels AI)
            "ARAI-01": "Begin de definitie met een zelfstandig naamwoord of naamwoordgroep",
            "ARAI-02": "Vermijd containerbegrippen zoals 'aspect', 'ding', 'iets', 'element' zonder verdere specificatie",
            "ARAI-02SUB1": "Vermijd algemene containertermen zoals 'aspect', 'ding', 'iets', 'element', 'factor'",
            "ARAI-02SUB2": "Vermijd ongespecificeerde containerbegrippen zoals 'proces', 'voorziening', 'activiteit'",
            "ARAI-03": "Vermijd subjectieve of contextafhankelijke bijvoeglijke naamwoorden",
            "ARAI-04": "Vermijd modale hulpwerkwoorden zoals 'kan', 'moet', 'mag', 'zal'",
            "ARAI-04SUB1": "Vermijd modale werkwoorden die onduidelijkheid scheppen over de essentie van het begrip",
            "ARAI-05": "Vermijd impliciete verwijzingen naar aannames, gewoonten of niet-toegelichte contexten",
            "ARAI-06": "Start zonder lidwoord ('de', 'het', 'een'), zonder koppelwerkwoord ('is', 'betekent') en zonder herhaling van het begrip",
            # ESS rules (Essentie)
            "ESS-01": (
                "Beschrijf de kenmerken die het begrip binnen de gegeven betekenis afbakenen. "
                "Neem geen niet-begripsbepalend doel, gewenst effect, motief of incidenteel "
                "(vervolg)gebruik op in de definitiekern, ook niet als onderscheidend kenmerk "
                "naast een genus. Behoud een functie, rol of gebruiksbestemming uitsluitend "
                "wanneer de gegeven bron of expliciet bevestigde domeinafbakening onderbouwt "
                "dat die het begrip mede bepaalt. Een bestemming is niet hetzelfde als actuele "
                "werking: sluit een defect of ongebruikt exemplaar niet onbedoeld uit. "
                "Geef gebruikte grond en onzekerheid apart bij de kandidaat; een "
                "modelmotivering is geen menselijk bewijs. De app kan overig doel of gebruik "
                "als apart toelichtingsvoorstel aanbieden. Verander term en registratiecontext "
                "niet; volg voor de definitiekern het bestaande CON-01-beleid, inclusief "
                "noodzakelijke namen. Verzin geen bron, afbakening of beoordeling. Bij "
                "ontbrekende of strijdige informatie: maak dit zichtbaar en geef hoogstens "
                "een herkenbaar voorlopig voorstel. Volg het bestaande uitvoerformaat: "
                "voeg grond, onzekerheid of toelichting niet toe aan de definitiekern. "
                "Een bevestigde overtreding blijft voldoet niet, ook bij een gezaghebbende "
                "bron; het oordeel start geen automatische wijziging of regeneratie."
            ),
            # DEF-750: dezelfde aanwijzing als de betekenislaagsectie; geen
            # "kies tussen vier" en geen markerplicht.
            "ESS-02": GEDEELDE_ESS02_AANWIJZING,
            # DEF-766: één norm voor genereren en toetsen (G). De oude
            # instructie "noem criteria voor unieke identificatie (zoals
            # serienummer, kenteken, ID, registratienummer)" is vervallen: een
            # nummer is geen bewijs van individuatie en de opdracht liet een
            # model identifiers, bronnen en telconventies verzinnen of een stof
            # tot monster maken. De gerichte verduidelijkingsvraag uit de
            # onderzoekstekst loopt binnen het bestaande uitvoercontract (één
            # zin, alleen de definitiekern) via de ESS-03-beoordeling; de
            # conflictmelding van DEF-751 blijft beperkt tot de ESS-02-
            # betekenislaag en wordt hier niet stil verbreed.
            "ESS-03": (
                "Bepaal uit de bedoelde betekenis en de beschikbare onderbouwing wat "
                "als één instantie geldt. Maak een noodzakelijke eenheidsgrens "
                "duidelijk met een passend bovenbegrip en begripsbepalende kenmerken. "
                "Gebruik een identifier alleen als zijn referentsoort, scope en "
                "relevante geldigheid zijn onderbouwd; verzin geen nummer, bron of "
                "telconventie. Laat niet-telbare stoffen of kwaliteiten niet stil "
                "veranderen in telbare monsters, porties of registraties. Bij een "
                "noodzakelijke maar onbesliste eenheidsgrens of continuïteitsvraag "
                "waarover bronnen en context elkaar niet werkelijk tegenspreken: "
                "verzin geen grens of conventie en lever één voorlopige kandidaat "
                "binnen de beschikbare grond, zonder melding of toelichting in de "
                "zin; de gerichte verduidelijkingsvraag blijft bij de "
                "ESS-03-beoordeling (nog te beoordelen). Spreken bronnen of context "
                "elkaar werkelijk tegen over de teleenheid, maak dan geen stille "
                "keuze en leg geen betwiste telconventie in de kern vast. Een naam "
                "of het woord ‘uniek’ is geen bewijs. "
                "Houd registratiecontext en bronadministratie buiten de kern, maar "
                "behoud inhoudelijk noodzakelijke namen en voorwaarden. Geef uitleg "
                "en synthetische voorbeelden afzonderlijk; ze vervangen geen "
                "ontbrekende kernafgrenzing."
            ),
            "ESS-04": "Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)",
            "ESS-05": "Maak expliciet duidelijk waarin het begrip zich onderscheidt van andere verwante begrippen",
            # STR rules (Structuur)
            "STR-01": "Start de definitie met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord",
            "STR-02": "Begin met een breder begrip (genus) en specificeer vervolgens hoe de term daarvan verschilt",
            "STR-03": "Geef een volledige definitie, niet alleen een synoniem",
            "STR-04": "Volg de algemene opening direct met een toespitsing die het specifieke type verduidelijkt",
            "STR-05": "Beschrijf wat het begrip is, niet enkel uit welke onderdelen het bestaat",
            "STR-06": "Beschrijf wat het begrip is, niet waarvoor het dient of waarom het nodig is",
            "STR-07": "Vermijd dubbele ontkenningen (zoals 'niet zonder', 'onmogelijk om niet te')",
            "STR-08": "Gebruik 'en' ondubbelzinnig (maak duidelijk of beide vereist zijn of één van beide)",
            "STR-09": "Gebruik 'of' ondubbelzinnig (maak duidelijk of het inclusief of exclusief is)",
            # INT rules (Integriteit)
            "INT-01": "Formuleer de definitie als één enkele, begrijpelijke zin",
            "INT-02": "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'",
            "INT-03": "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin",
            "INT-04": "Maak bepaalde lidwoorden ('de instelling', 'het systeem') expliciet door direct te specificeren welke bedoeld wordt",
            "INT-06": "Vermijd toelichtende formuleringen zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', 'namelijk'",
            "INT-07": "Licht afkortingen direct toe in dezelfde zin (bijv. DJI (Dienst Justitiële Inrichtingen))",
            "INT-08": "Formuleer positief (wat iets wél is), niet negatief (wat iets niet is)",
            "INT-09": "Maak opsommingen limitatief (vermijd 'zoals', 'bijvoorbeeld', 'onder andere', 'etc.')",
            "INT-10": "Zorg dat de definitie begrijpelijk is zonder specialistische of niet-openbare kennis",
            # VER rules (Vorm)
            "VER-01": "Gebruik enkelvoud, tenzij het begrip een plurale-tantum is (alleen meervoud bestaat)",
            "VER-02": "Formuleer de definitie in het enkelvoud",
            "VER-03": "Gebruik de infinitief voor werkwoord-termen (niet vervoegd)",
            # CON rules (Context)
            # DEF-622 (B-02): registratiecontext buiten de zin; een inhoudelijk
            # noodzakelijke naam mag blijven staan.
            "CON-01": (
                "Verwerk de context impliciet in de formulering; vermeld de "
                "registratiecontext niet in de definitiezin. Een naam uit de context "
                "mag alleen voorkomen als die inhoudelijk noodzakelijk is om het "
                "begrip af te bakenen of te identificeren"
            ),
            # DEF-743: één bronbasisnorm voor genereren en toetsen (G). Dezelfde
            # norm als CON-02.json; hier de generatiekant in één instructie. De
            # uitleg erboven noemt al de bronsoorten en de peildatum; de
            # BRONNEN INSTRUCTIE geeft de XML-legenda en de datanorm.
            "CON-02": (
                "Gebruik alleen aangeleverde, passende bronpassages met hun beperkingen "
                "en uitzonderingen; route of zoekscore is geen bewijs van gezag; verzin "
                "geen bron; een bronvermelding in de zin is niet verplicht"
            ),
            # SAM rules (Samenstelling)
            "SAM-01": "Zorg dat kwalificaties niet leiden tot een betekenis die afwijkt van het algemeen aanvaarde begrip",
            "SAM-02": "Vermijd herhaling uit de definitie van het hoofdbegrip bij het kwalificeren van begrippen",
            "SAM-03": "Herhaal geen andere definitieteksten; verwijs naar het begrip of definieer afzonderlijk",
            "SAM-04": "Begin samengestelde begrippen met het component dat de specialisatie vormt (genus) en specificeer daarna",
            "SAM-05": "Vermijd cirkeldefinities (wederzijdse verwijzingen tussen begrippen)",
            "SAM-06": "Gebruik consistente terminologie (kies één voorkeurs-term per begrip)",
            "SAM-07": "Vermijd betekenisverruiming; beperk je tot elementen die inherent zijn aan de term",
            "SAM-08": "Voor synoniemen: gebruik exact dezelfde definitiestructuur",
            # DUP rules (Duplicate detection)
            "DUP_01": "Formuleer een originele definitie die substantieel verschilt van standaardformuleringen",
        }

        return instruction_map.get(regel_key)
