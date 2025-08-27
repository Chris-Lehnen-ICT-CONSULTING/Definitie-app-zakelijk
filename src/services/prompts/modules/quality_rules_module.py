"""
Quality Rules Module - Implementeert alle validatieregels voor definities.

Deze module is verantwoordelijk voor:
1. Alle CON, ESS, INT, SAM, STR en ARAI validatieregels
2. Gestructureerde presentatie met voorbeelden
3. Context-aware regel selectie
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class QualityRulesModule(BasePromptModule):
    """
    Module voor alle validatie/toetsregels.

    Genereert de complete set van validatieregels die gebruikt
    moeten worden bij het definiëren van begrippen.
    """

    def __init__(self):
        """Initialize de quality rules module."""
        super().__init__(
            module_id="quality_rules",
            module_name="Validation Rules Module",
            priority=70,  # Belangrijke prioriteit - validatie regels
        )
        self.include_arai_rules = True
        self.include_examples = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_arai_rules = config.get("include_arai_rules", True)
        self.include_examples = config.get("include_examples", True)
        self._initialized = True
        logger.info(
            f"QualityRulesModule geïnitialiseerd "
            f"(arai={self.include_arai_rules}, examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd.

        Args:
            context: Module context

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer alle validatieregels.

        Args:
            context: Module context

        Returns:
            ModuleOutput met validatieregels
        """
        try:
            # Bouw de validatieregels sectie
            sections = []

            # Start sectie
            sections.append("### ✅ Richtlijnen voor de definitie:")

            # Context regels (CON)
            sections.extend(self._build_context_rules())

            # Essentie regels (ESS)
            sections.extend(self._build_essence_rules())

            # Integriteit regels (INT)
            sections.extend(self._build_integrity_rules())

            # Samenhang regels (SAM)
            sections.extend(self._build_coherence_rules())

            # Structuur regels (STR)
            sections.extend(self._build_structure_rules())

            # ARAI regels (indien enabled)
            if self.include_arai_rules:
                sections.extend(self._build_arai_rules())

            # Combineer secties
            content = "\n".join(sections)

            rule_count = 34 if self.include_arai_rules else 25

            return ModuleOutput(
                content=content,
                metadata={
                    "total_rules": rule_count,
                    "include_arai": self.include_arai_rules,
                    "include_examples": self.include_examples,
                },
            )

        except Exception as e:
            logger.error(f"QualityRulesModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate quality rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _build_context_rules(self) -> list[str]:
        """Bouw CON (Context) regels."""
        rules = []

        rules.append(
            """🔹 **CON-01 - Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming**
- Formuleer de definitie zó dat deze past binnen de opgegeven context(en), zonder deze expliciet te benoemen in de definitie zelf.
- Toetsvraag: Is de betekenis van het begrip contextspecifiek geformuleerd, zonder dat de context letterlijk of verwijzend in de definitie wordt genoemd?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Toezicht is het systematisch volgen van handelingen om te beoordelen of ze voldoen aan vastgestelde normen.
  ✅ Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem.
  ✅ Een maatregel is een opgelegde beperking of correctie bij vastgestelde overtredingen.
  ❌ Toezicht is controle uitgevoerd door DJI in juridische context, op basis van het Wetboek van Strafvordering.
  ❌ Registratie: het vastleggen van persoonsgegevens binnen de organisatie DJI, in strafrechtelijke context.
  ❌ Een maatregel is, binnen de context van het strafrecht, een corrigerende sanctie."""
            )

        rules.append(
            """🔹 **CON-02 - Baseren op authentieke bron**
- Gebruik een gezaghebbende of officiële bron als basis voor de definitie.
- Toetsvraag: Is duidelijk op welke authentieke of officiële bron de definitie is gebaseerd?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ gegevensverwerking: iedere handeling met gegevens zoals bedoeld in de AVG
  ✅ delict: gedraging die volgens het Wetboek van Strafrecht strafbaar is gesteld
  ❌ gegevensverwerking: handeling met gegevens (geen bron vermeld)
  ❌ delict: iets strafbaars (geen verwijzing naar wet)"""
            )

        return rules

    def _build_essence_rules(self) -> list[str]:
        """Bouw ESS (Essentie) regels."""
        rules = []

        rules.append(
            """🔹 **ESS-01 - Essentie, niet doel**
- Een definitie beschrijft wat iets is, niet wat het doel of de bedoeling ervan is.
- Toetsvraag: Bevat de definitie uitsluitend de essentie van het begrip, zonder doel- of gebruiksgericht taalgebruik?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ meldpunt: instantie die meldingen registreert over strafbare feiten
  ✅ sanctie: maatregel die volgt op normovertreding
  ❌ meldpunt: instantie om meldingen te kunnen verwerken
  ❌ sanctie: maatregel met als doel naleving te bevorderen"""
            )

        rules.append(
            """🔹 **ESS-02 - Ontologische categorie expliciteren (type / particulier / proces / resultaat)**
- Indien een begrip meerdere ontologische categorieën kan aanduiden, moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt: soort (type), exemplaar (particulier), proces (activiteit) of resultaat (uitkomst).
- Toetsvraag: Geeft de definitie ondubbelzinnig aan of het begrip een type, een particular, een proces of een resultaat is?"""
        )

        rules.append(
            """🔹 **ESS-04 - Toetsbaarheid**
- Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).
- Toetsvraag: Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ …binnen 3 dagen nadat het verzoek is ingediend…
  ✅ …tenminste 80% van de steekproef voldoet…
  ✅ …uiterlijk na 1 week na ontvangst…
  ❌ …zo snel mogelijk na ontvangst…
  ❌ …zo veel mogelijk resultaten…
  ❌ …moet zo mogelijk conform…"""
            )

        rules.append(
            """🔹 **ESS-05 - Voldoende onderscheidend**
- Een definitie moet duidelijk maken wat het begrip uniek maakt ten opzichte van andere verwante begrippen.
- Toetsvraag: Maakt de definitie expliciet duidelijk waarin het begrip zich onderscheidt van andere begrippen?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Reclasseringstoezicht: toezicht gericht op gedragsverandering, in tegenstelling tot detentietoezicht dat gericht is op vrijheidsbeneming.
  ✅ Een onttrekking is een incident waarbij een jeugdige zonder toestemming één van de volgende voorzieningen verlaat: open justitiële inrichting of gesloten inrichtingsgebied.
  ✅ Auto: vierwielig motorvoertuig met uniek chassisnummer en kenteken, waardoor elke auto individueel wordt geïdentificeerd.
  ❌ Toezicht: het houden van toezicht op iemand.
  ❌ Een onttrekking is een incident waarbij een jeugdige zonder toestemming de inrichting verlaat."""
            )

        return rules

    def _build_integrity_rules(self) -> list[str]:
        """Bouw INT (Integriteit) regels."""
        rules = []

        rules.append(
            """🔹 **INT-01 - Compacte en begrijpelijke zin**
- Een definitie is compact en in één enkele zin geformuleerd.
- Toetsvraag: Is de definitie geformuleerd als één enkele, begrijpelijke zin?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften, in plaats van meer permanente."""
            )

        rules.append(
            """🔹 **INT-02 - Geen beslisregel**
- Een definitie bevat geen beslisregels of voorwaarden.
- Toetsvraag: Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ✅ Toegang: toestemming verleend door een bevoegde autoriteit om een systeem te gebruiken.
  ✅ Beschikking: schriftelijk besluit genomen door een bevoegde autoriteit.
  ✅ Register: officiële inschrijving in een openbaar register door een bevoegde instantie.
  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.
  ❌ Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld.
  ❌ Beschikking: schriftelijk besluit, mits de aanvraag compleet is ingediend.
  ❌ Register: officiële inschrijving in een openbaar register, tenzij er bezwaar ligt."""
            )

        rules.append(
            """🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**
- Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt.
- Toetsvraag: Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd.
  ✅ Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan.
  ❌ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd.
  ❌ Voorwaarde: bepaling die aangeeft onder welke omstandigheden deze geldt."""
            )

        rules.append(
            """🔹 **INT-04 - Lidwoord-verwijzing duidelijk**
- Definities mogen geen onduidelijke verwijzingen met de lidwoorden 'de' of 'het' bevatten.
- Toetsvraag: Bevat de definitie zinnen als 'de instelling', 'het systeem'? Zo ja: is in diezelfde zin expliciet benoemd welke instelling of welk systeem wordt bedoeld?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Een instelling (de Raad voor de Rechtspraak) neemt beslissingen binnen het strafrechtelijk systeem.
  ✅ Het systeem (Reclasseringsapplicatie) voert controles automatisch uit.
  ❌ De instelling neemt beslissingen binnen het strafrechtelijk systeem.
  ❌ Het systeem voert controles uit zonder verdere specificatie."""
            )

        rules.append(
            """🔹 **INT-06 - Definitie bevat geen toelichting**
- Een definitie bevat geen nadere toelichting of voorbeelden, maar uitsluitend de afbakening van het begrip.
- Toetsvraag: Bevat de definitie signalen van toelichting zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', enzovoort?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ model: vereenvoudigde weergave van de werkelijkheid
  ❌ model: vereenvoudigde weergave van de werkelijkheid, die visueel wordt weergegeven"""
            )

        rules.append(
            """🔹 **INT-07 - Alleen toegankelijke afkortingen**
- In een definitie gebruikte afkortingen zijn voorzien van een voor de doelgroep direct toegankelijke referentie.
- Toetsvraag: Bevat de definitie afkortingen? Zo ja: zijn deze in hetzelfde stuk tekst uitgelegd of gelinkt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Dienst Justitiële Inrichtingen (DJI)
  ✅ OM (Openbaar Ministerie)
  ✅ AVG (Algemene verordening gegevensbescherming)
  ✅ KvK (Kamer van Koophandel)
  ✅ [[Algemene verordening gegevensbescherming]]
  ❌ DJI voert toezicht uit.
  ❌ De AVG vereist naleving.
  ❌ OM is bevoegd tot vervolging.
  ❌ KvK registreert bedrijven."""
            )

        rules.append(
            """🔹 **INT-08 - Positieve formulering**
- Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken; uitzondering voor onderdelen die de definitie specifieker maken (bijv. relatieve bijzinnen).
- Toetsvraag: Is de definitie in principe positief geformuleerd en vermijdt deze negatieve formuleringen, behalve om specifieke onderdelen te verduidelijken?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ bevoegd persoon: medewerker met formele autorisatie om gegevens in te zien
  ✅ gevangene: persoon die zich niet vrij kan bewegen
  ❌ bevoegd persoon: iemand die niet onbevoegd is
  ❌ toegang: mogelijkheid om een ruimte te betreden, uitgezonderd voor onbevoegden"""
            )

        return rules

    def _build_coherence_rules(self) -> list[str]:
        """Bouw SAM (Samenhang) regels."""
        rules = []

        rules.append(
            """🔹 **SAM-01 - Kwalificatie leidt niet tot afwijking**
- Een definitie mag niet zodanig zijn geformuleerd dat deze afwijkt van de betekenis die de term in andere contexten heeft.
- Toetsvraag: Leidt de gebruikte kwalificatie in de definitie tot een betekenis die wezenlijk afwijkt van het algemeen aanvaarde begrip?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ proces: reeks activiteiten met een gemeenschappelijk doel
  ✅ juridisch proces: proces binnen de context van rechtspleging
  ❌ proces: technische afhandeling van informatie tussen systemen (terwijl 'proces' elders breder wordt gebruikt)"""
            )

        rules.append(
            """🔹 **SAM-05 - Geen cirkeldefinities**
- Een cirkeldefinitie (wederzijdse of meerdiepse verwijzing tussen begrippen) mag niet voorkomen.
- Toetsvraag: Treden er wederzijdse verwijzingen op tussen begrippen (cirkeldefinitie)?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ object: fysiek ding dat bestaat in ruimte en tijd
  ✅ entiteit: iets dat bestaat
  ❌ object: een ding is een object
  ❌ ding: een object is een ding"""
            )

        rules.append(
            """🔹 **SAM-07 - Geen betekenisverruiming binnen definitie**
- De definitie mag de betekenis van de term niet uitbreiden met extra elementen die niet in de term besloten liggen.
- Toetsvraag: Bevat de definitie uitsluitend elementen die inherent zijn aan de term, zonder aanvullende uitbreidingen?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ toezicht houden: het controleren of regels worden nageleefd
  ❌ toezicht houden: het controleren en indien nodig corrigeren van gedrag"""
            )

        return rules

    def _build_structure_rules(self) -> list[str]:
        """Bouw STR (Structuur) regels."""
        rules = []

        # STR-01 t/m STR-09
        rules.extend(self._build_structure_rules_part1())
        rules.extend(self._build_structure_rules_part2())

        return rules

    def _build_structure_rules_part1(self) -> list[str]:
        """Bouw STR regels deel 1 (STR-01 t/m STR-04)."""
        rules = []

        rules.append(
            """🔹 **STR-01 - definitie start met zelfstandig naamwoord**
- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord.
- Toetsvraag: Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ proces dat beslissers identificeert...
  ✅ maatregel die recidive voorkomt...
  ❌ is een maatregel die recidive voorkomt
  ❌ wordt toegepast in het gevangeniswezen"""
            )

        rules.append(
            """🔹 **STR-02 - Kick-off ≠ de term**
- De definitie moet beginnen met verwijzing naar een breder begrip, en dan de verbijzondering ten opzichte daarvan aangeven.
- Toetsvraag: Begint de definitie met een breder begrip en specificeert het vervolgens hoe het te definiëren begrip daarvan verschilt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ analist: professional verantwoordelijk voor …
  ❌ analist: analist die verantwoordelijk is voor …"""
            )

        rules.append(
            """🔹 **STR-03 - Definitie ≠ synoniem**
- De definitie van een begrip mag niet simpelweg een synoniem zijn van de te definiëren term.
- Toetsvraag: Is de definitie meer dan alleen een synoniem van de term?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ evaluatie: resultaat van iets beoordelen, appreciëren of interpreteren
  ❌ evaluatie: beoordeling
  ❌ registratie: vastlegging (in een systeem)"""
            )

        rules.append(
            """🔹 **STR-04 - Kick-off vervolgen met toespitsing**
- Een definitie moet na de algemene opening meteen toespitsen op het specifieke begrip.
- Toetsvraag: Volgt na de algemene opening direct een toespitsing die uitlegt welk soort proces of element bedoeld wordt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ proces dat beslissers informeert
  ✅ gegeven over de verblijfplaats van een betrokkene
  ❌ proces
  ❌ gegeven
  ❌ activiteit die plaatsvindt"""
            )

        return rules

    def _build_structure_rules_part2(self) -> list[str]:
        """Bouw STR regels deel 2 (STR-05 t/m STR-09)."""
        rules = []

        rules.append(
            """🔹 **STR-05 - Definitie ≠ constructie**
- Een definitie moet aangeven wat iets is, niet uit welke onderdelen het bestaat.
- Toetsvraag: Geeft de definitie aan wat het begrip is, in plaats van alleen waar het uit bestaat?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ motorvoertuig: gemotoriseerd voertuig dat niet over rails rijdt, zoals auto's, vrachtwagens en bussen
  ❌ motorvoertuig: een voertuig met een chassis, vier wielen en een motor van meer dan 50 cc"""
            )

        rules.append(
            """🔹 **STR-06 - Essentie ≠ informatiebehoefte**
- Een definitie geeft de aard van het begrip weer, niet de reden waarom het nodig is.
- Toetsvraag: Bevat de definitie uitsluitend wat het begrip is, en niet waarom het nodig is of waarvoor het gebruikt wordt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt
  ❌ beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen"""
            )

        rules.append(
            """🔹 **STR-07 - Geen dubbele ontkenning**
- Een definitie bevat geen dubbele ontkenning.
- Toetsvraag: Bevat de definitie een dubbele ontkenning die de begrijpelijkheid schaadt?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Beveiliging: maatregelen die toegang beperken tot bevoegde personen
  ❌ Beveiliging: maatregelen die het niet onmogelijk maken om geen toegang te verkrijgen"""
            )

        rules.append(
            """🔹 **STR-08 - Dubbelzinnige 'en' is verboden**
- Een definitie bevat geen 'en' die onduidelijk maakt of beide kenmerken vereist zijn of slechts één van beide.
- Toetsvraag: Is het gebruik van 'en' in de definitie ondubbelzinnig? Is het duidelijk of beide elementen vereist zijn of slechts één?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Toegang is beperkt tot personen met een geldig toegangspasje en een schriftelijke toestemming
  ❌ Toegang is beperkt tot personen met een pasje en toestemming
  ❌ Het systeem vereist login en verificatie"""
            )

        rules.append(
            """🔹 **STR-09 - Dubbelzinnige 'of' is verboden**
- Een definitie bevat geen 'of' die onduidelijk maakt of beide mogelijkheden gelden of slechts één van de twee.
- Toetsvraag: Is het gebruik van 'of' in de definitie ondubbelzinnig? Is het duidelijk of het gaat om een inclusieve of exclusieve keuze?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart
  ❌ Een persoon met een paspoort of identiteitskaart
  ❌ Een verdachte is iemand die een misdrijf beraamt of uitvoert"""
            )

        return rules

    def _build_arai_rules(self) -> list[str]:
        """Bouw ARAI regels."""
        rules = []

        rules.append(
            """🔹 **ARAI-01 - Geen werkwoord als kern (afgeleid)**
- De kern van de definitie mag geen werkwoord zijn, om verwarring tussen handelingen en concepten te voorkomen.
- Toetsvraag: Is de kern van de definitie een zelfstandig naamwoord (en geen werkwoord)?"""
        )

        if self.include_examples:
            rules.append(
                """  ✅ proces dat beslissers identificeert
  ✅ instelling die zorg verleent
  ❌ Een systeem dat registreert...
  ❌ Een functie die uitvoert..."""
            )

        rules.append(
            """🔹 **ARAI-02 - Geen nevenschikkingen (afgeleid)**
- Vermijd opsommingen met 'en/of' die leiden tot onduidelijkheid over wat exact bedoeld wordt.
- Toetsvraag: Is de definitie vrij van nevenschikkende constructies die tot interpretatieproblemen kunnen leiden?"""
        )

        rules.append(
            """🔹 **ARAI-02SUB1 - Vermijd 'en/of' constructies**
- Het gebruik van 'en/of' maakt onduidelijk of beide opties gelden of slechts één.
- Toetsvraag: Bevat de definitie geen 'en/of' constructies?"""
        )

        rules.append(
            """🔹 **ARAI-02SUB2 - Beperk gebruik van komma-opsommingen**
- Lange opsommingen met komma's maken definities complex en onduidelijk.
- Toetsvraag: Bevat de definitie geen uitgebreide komma-gescheiden lijsten?"""
        )

        rules.append(
            """🔹 **ARAI-03 - Vermijd vage kwalificaties**
- Subjectieve of relatieve termen zoals 'belangrijk', 'adequaat', 'voldoende' zijn niet objectief meetbaar.
- Toetsvraag: Bevat de definitie alleen objectieve, meetbare termen?"""
        )

        rules.append(
            """🔹 **ARAI-04 - Geen temporele beperkingen**
- Vermijd tijdsgebonden formuleringen die de definitie beperken tot specifieke periodes.
- Toetsvraag: Is de definitie tijdloos geformuleerd?"""
        )

        rules.append(
            """🔹 **ARAI-04SUB1 - Vermijd 'voorheen', 'vroeger', 'nieuw'**
- Deze termen maken definities tijdsafhankelijk en dus instabiel.
- Toetsvraag: Bevat de definitie geen verwijzingen naar specifieke tijdsperiodes?"""
        )

        rules.append(
            """🔹 **ARAI-05 - Consistente enkelvoud/meervoud**
- Gebruik consequent enkelvoud of meervoud, mix deze niet binnen één definitie.
- Toetsvraag: Is het gebruik van enkelvoud/meervoud consistent binnen de definitie?"""
        )

        rules.append(
            """🔹 **ARAI-06 - Geen modaliteiten**
- Vermijd woorden als 'kan', 'mag', 'moet', 'zou' die onzekerheid introduceren.
- Toetsvraag: Bevat de definitie geen modaliteiten die de betekenis verzwakken?"""
        )

        return rules
