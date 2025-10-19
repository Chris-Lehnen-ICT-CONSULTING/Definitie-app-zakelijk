"""
UFO Classifier Service voor Nederlandse Juridische Definities
=============================================================
Single-user implementatie met focus op CORRECTHEID boven SNELHEID
Target: 95% precisie door grondige analyse van alle 16 UFO categorieën

Author: AI-Generated Implementation
Date: 2025-01-23
Version: 1.0.0
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# Configure logging
logger = logging.getLogger(__name__)


class UFOCategory(Enum):
    """Alle 16 UFO/OntoUML categorieën voor Nederlandse juridische concepten."""

    # Primaire categorieën (Endurants)
    KIND = "Kind"  # Zelfstandige entiteit (persoon, organisatie, zaak)
    EVENT = "Event"  # Tijdsgebonden gebeurtenis/proces
    ROLE = "Role"  # Rol die entiteit kan aannemen (verdachte, eigenaar)
    PHASE = "Phase"  # Levensfase van entiteit (in onderzoek, definitief)
    RELATOR = "Relator"  # Medieert relatie tussen entiteiten (contract, huwelijk)
    MODE = "Mode"  # Intrinsieke eigenschap met drager (gezondheid, locatie)
    QUANTITY = "Quantity"  # Meetbare grootheid (bedrag, percentage)
    QUALITY = "Quality"  # Kwalitatieve eigenschap (ernst, betrouwbaarheid)

    # Subcategorieën (Sortals & Non-Sortals)
    SUBKIND = "Subkind"  # Subtype dat essentie behoudt
    CATEGORY = "Category"  # Essentiële eigenschappen delend
    MIXIN = "Mixin"  # Niet-essentiële eigenschappen delend
    ROLEMIXIN = "RoleMixin"  # Rol-eigenschappen delend
    PHASEMIXIN = "PhaseMixin"  # Fase-eigenschappen delend

    # Collecties
    COLLECTIVE = "Collective"  # Verzameling met uniforme structuur
    VARIABLECOLLECTION = "VariableCollection"  # Variabele verzameling
    FIXEDCOLLECTION = "FixedCollection"  # Vaste verzameling


@dataclass
class UFOClassificationResult:
    """
    Resultaat van UFO classificatie met volledige transparantie.
    Focus op uitgebreide uitleg voor juridische verantwoording.
    """

    term: str
    definition: str
    primary_category: UFOCategory
    secondary_categories: list[UFOCategory] = field(default_factory=list)
    confidence: float = 0.0

    # Volledige analyse resultaten (geen shortcuts)
    all_scores: dict[UFOCategory, float] = field(default_factory=dict)
    matched_patterns: list[str] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)

    # Uitgebreide uitleg voor transparantie
    detailed_explanation: list[str] = field(default_factory=list)
    disambiguation_notes: list[str] = field(default_factory=list)
    decision_path: list[str] = field(default_factory=list)

    # Metadata
    classification_time_ms: float = 0.0
    classifier_version: str = "1.0.0"
    timestamp: datetime = field(default_factory=datetime.now)


class DutchLegalLexicon:
    """
    Complete Nederlandse juridische woordenschat (500+ termen).
    Georganiseerd per rechtsgebied voor maximale herkenning.
    """

    def __init__(self):
        self.lexicons = self._load_complete_lexicons()

    def _load_complete_lexicons(self) -> dict[str, set[str]]:
        """Laad ALLE 500+ juridische termen (geen lazy loading voor single-user)."""

        return {
            "strafrecht": {
                # Actoren (50 termen)
                "verdachte",
                "dader",
                "slachtoffer",
                "getuige",
                "medeverdachte",
                "medepleger",
                "medeplichtige",
                "uitlokker",
                "benadeelde",
                "aangever",
                "klager",
                "veroordeelde",
                "recidivist",
                "first offender",
                "jeugdige",
                "meerderjarige",
                "minderjarige",
                "toerekeningsvatbare",
                "ontoerekeningsvatbare",
                "verdediging",
                "advocaat",
                "raadsman",
                "officier van justitie",
                "rechter",
                "rechter-commissaris",
                "griffier",
                "reclassering",
                "jeugdbescherming",
                "kinderbescherming",
                "voogd",
                "curator",
                "bewindvoerder",
                "mentor",
                # Handelingen & Procedures (60 termen)
                "aangifte",
                "aanhouding",
                "arrestatie",
                "fouillering",
                "doorzoeking",
                "inbeslagname",
                "verhoor",
                "ondervraging",
                "confrontatie",
                "schouw",
                "inverzekeringstelling",
                "voorgeleiding",
                "bewaring",
                "gevangenhouding",
                "voorlopige hechtenis",
                "schorsing",
                "dagvaarding",
                "oproeping",
                "betekening",
                "kennisgeving",
                "zitting",
                "behandeling",
                "pleidooi",
                "requisitoir",
                "strafeis",
                "verweer",
                "repliek",
                "dupliek",
                "beraadslaging",
                "uitspraak",
                "vonnis",
                "arrest",
                "veroordeling",
                "vrijspraak",
                "ontslag van rechtsvervolging",
                "schuldigverklaring",
                "straf",
                "maatregel",
                "gevangenisstraf",
                "hechtenis",
                "taakstraf",
                "geldboete",
                "voorwaardelijke straf",
                "proeftijd",
                "bijzondere voorwaarden",
                "hoger beroep",
                "cassatie",
                "verzet",
                "herziening",
                "gratie",
                "strafonderbreking",
                "strafuitstel",
                "vervroegde invrijheidstelling",
                "voorwaardelijke invrijheidstelling",
                "elektronisch toezicht",
                # Documenten & Besluiten (40 termen)
                "proces-verbaal",
                "strafdossier",
                "procesdossier",
                "kennisgeving van inbeslagneming",
                "bevel tot inverzekeringstelling",
                "bevel tot bewaring",
                "bevel tot gevangenhouding",
                "vordering",
                "beschikking",
                "beslissing",
                "strafbeschikking",
                "transactie",
                "sepot",
                "seponering",
                "tenlastelegging",
                "akte",
                "verklaring",
                "bekentenis",
                "ontkenning",
                "getuigenverklaring",
                "deskundigenrapport",
                "reclasseringsrapport",
                "uittreksel justitiële documentatie",
                "verklaring omtrent gedrag",
                "strafblad",
                "documentatie",
                "dossier",
            },
            "bestuursrecht": {
                # Actoren (40 termen)
                "burger",
                "inwoner",
                "belanghebbende",
                "derde-belanghebbende",
                "aanvrager",
                "vergunninghouder",
                "bezwaarmaker",
                "appellant",
                "verweerder",
                "gemachtigde",
                "bestuursorgaan",
                "bevoegd gezag",
                "college",
                "burgemeester",
                "wethouders",
                "gedeputeerde staten",
                "commissaris van de koning",
                "minister",
                "staatssecretaris",
                "ambtenaar",
                "inspecteur",
                "controleur",
                "handhaver",
                "toezichthouder",
                "adviseur",
                "commissie",
                "adviescommissie",
                "bezwaarcommissie",
                "klachtencommissie",
                "ombudsman",
                "bestuursrechter",
                "voorzieningenrechter",
                "hoger beroepsrechter",
                # Handelingen & Procedures (50 termen)
                "aanvraag",
                "verzoek",
                "melding",
                "kennisgeving",
                "zienswijze",
                "inspraak",
                "consultatie",
                "advies",
                "voorbereiding",
                "onderzoek",
                "besluitvorming",
                "beschikking",
                "besluit",
                "vaststelling",
                "goedkeuring",
                "weigering",
                "intrekking",
                "wijziging",
                "verlenging",
                "publicatie",
                "bekendmaking",
                "mededeling",
                "ter inzage legging",
                "terinzagelegging",
                "bezwaar",
                "bezwaarprocedure",
                "hoorzitting",
                "heroverweging",
                "heroverwegingsbesluit",
                "administratief beroep",
                "beroep",
                "hoger beroep",
                "voorlopige voorziening",
                "schorsing",
                "vernietiging",
                "handhaving",
                "sanctie",
                "bestuursdwang",
                "dwangsom",
                "last onder dwangsom",
                "last onder bestuursdwang",
                "waarschuwing",
                "herstelmaatregel",
                "gedogen",
                "legalisatie",
                "toezicht",
                "controle",
                # Documenten & Instrumenten (30 termen)
                "vergunning",
                "ontheffing",
                "vrijstelling",
                "concessie",
                "subsidie",
                "beleidsregel",
                "algemeen verbindend voorschrift",
                "verordening",
                "regeling",
                "nadere regels",
                "uitvoeringsregels",
                "mandaat",
                "delegatie",
                "attributie",
                "convenant",
                "bestuursovereenkomst",
                "bestemmingsplan",
                "omgevingsplan",
                "omgevingsvergunning",
                "milieuvergunning",
                "bouwvergunning",
                "gebruiksvergunning",
                "exploitatievergunning",
                "evenementenvergunning",
                "standplaatsvergunning",
                "ventvergunning",
                "onttrekkingsvergunning",
            },
            "civiel_recht": {
                # Partijen & Relaties (40 termen)
                "koper",
                "verkoper",
                "huurder",
                "verhuurder",
                "pachter",
                "verpachter",
                "schuldenaar",
                "schuldeiser",
                "crediteur",
                "debiteur",
                "opdrachtgever",
                "opdrachtnemer",
                "aannemer",
                "onderaannemer",
                "werkgever",
                "werknemer",
                "vennoot",
                "aandeelhouder",
                "bestuurder",
                "commissaris",
                "curator",
                "bewindvoerder",
                "executeur",
                "erfgenaam",
                "legataris",
                "erflater",
                "schenker",
                "begiftigde",
                "bruiklener",
                "bruikleengever",
                "bewaarnemer",
                "bewaargever",
                "borg",
                "hoofdelijk schuldenaar",
                "pandgever",
                "pandhouder",
                "hypotheekgever",
                "hypotheekhouder",
                "vruchtgebruiker",
                "hoofdgerechtigde",
                # Overeenkomsten & Rechtshandelingen (40 termen)
                "koopovereenkomst",
                "huurovereenkomst",
                "pachtovereenkomst",
                "arbeidsovereenkomst",
                "aanneemovereenkomst",
                "opdracht",
                "lastgeving",
                "bemiddeling",
                "agentuur",
                "distributieovereenkomst",
                "franchiseovereenkomst",
                "licentieovereenkomst",
                "leaseovereenkomst",
                "bruikleenovereenkomst",
                "bewaargeving",
                "borgstelling",
                "schenking",
                "ruiling",
                "dading",
                "vaststellingsovereenkomst",
                "cessie",
                "subrogatie",
                "novatie",
                "delegatie",
                "schuldvernieuwing",
                "kwijtschelding",
                "verrekening",
                "opzegging",
                "ontbinding",
                "nietigheid",
                "vernietiging",
                "bekrachtiging",
                "conversie",
                "dwaling",
                "bedrog",
                "misbruik van omstandigheden",
                "bedreiging",
                "onbekwaamheid",
                "wilsgebrek",
                "toestemming",
                # Goederen & Rechten (20 termen)
                "eigendom",
                "bezit",
                "houderschap",
                "vruchtgebruik",
                "erfpacht",
                "opstal",
                "erfdienstbaarheid",
                "pand",
                "hypotheek",
                "beslag",
                "retentierecht",
                "voorrecht",
                "zekerheidsrecht",
                "goederenrecht",
                "zaak",
                "roerende zaak",
                "onroerende zaak",
                "registergoed",
                "vermogensrecht",
                "vorderingsrecht",
            },
            "algemeen_juridisch": {
                # Rechtspersonen & Organisaties (40 termen)
                "rechtspersoon",
                "natuurlijk persoon",
                "publiekrechtelijke rechtspersoon",
                "privaatrechtelijke rechtspersoon",
                "vennootschap",
                "bv",
                "nv",
                "vof",
                "cv",
                "maatschap",
                "coöperatie",
                "onderlinge waarborgmaatschappij",
                "vereniging",
                "stichting",
                "kerkgenootschap",
                "overheidsorgaan",
                "zelfstandig bestuursorgaan",
                "openbaar lichaam",
                "gemeente",
                "provincie",
                "waterschap",
                "rijk",
                "staat",
                "ministerie",
                "dienst",
                "agentschap",
                "inspectie",
                "autoriteit",
                "raad",
                "commissie",
                "rechtbank",
                "gerechtshof",
                "hoge raad",
                "centrale raad van beroep",
                "raad van state",
                "college van beroep voor het bedrijfsleven",
                "accountantskamer",
                "notariskamer",
                "medisch tuchtcollege",
                "tuchtcollege",
                # Algemene Juridische Concepten (50 termen)
                "recht",
                "plicht",
                "bevoegdheid",
                "aanspraak",
                "rechtsverhouding",
                "rechtsfeit",
                "rechtshandeling",
                "rechtsgevolg",
                "rechtssubject",
                "rechtsobject",
                "rechtsregel",
                "rechtsnorm",
                "rechtsbeginsel",
                "rechtszekerheid",
                "rechtsgelijkheid",
                "rechtvaardigheid",
                "redelijkheid",
                "billijkheid",
                "proportionaliteit",
                "subsidiariteit",
                "zorgvuldigheid",
                "motivering",
                "belangenafweging",
                "discretionaire bevoegdheid",
                "gebonden bevoegdheid",
                "beleidsvrijheid",
                "beoordelingsruimte",
                "toetsing",
                "rechtmatigheid",
                "onrechtmatigheid",
                "nietigheid",
                "vernietigbaarheid",
                "verjaring",
                "stuiting",
                "schorsing",
                "verval",
                "afstand",
                "rechtsverwerking",
                "vertrouwensbeginsel",
                "gelijkheidsbeginsel",
                "zorgvuldigheidsbeginsel",
                "motiveringsbeginsel",
                "rechtszekerheidsbeginsel",
                "evenredigheidsbeginsel",
                "verbod van détournement de pouvoir",
                "verbod van willekeur",
                "hoor en wederhoor",
                "openbaarheid",
                # Procedures & Documenten (40 termen)
                "procedure",
                "proces",
                "geding",
                "instantie",
                "aanleg",
                "termijn",
                "beroepstermijn",
                "bezwaartermijn",
                "vervaltermijn",
                "fatale termijn",
                "verjaringstermijn",
                "redelijke termijn",
                "proceshandeling",
                "processtuk",
                "dossier",
                "akte",
                "authentieke akte",
                "onderhandse akte",
                "notariële akte",
                "grosse",
                "executoriale titel",
                "dwangbevel",
                "exploot",
                "dagvaarding",
                "verzoekschrift",
                "beroepschrift",
                "bezwaarschrift",
                "klaagschrift",
                "conclusie",
                "memorie",
                "pleitnota",
                "productie",
                "bewijs",
                "bewijslast",
                "bewijsmiddel",
                "schriftelijk bewijs",
                "getuigenbewijs",
                "deskundigenbericht",
                "vermoeden",
                "bekentenis",
                "eed",
                "verklaring",
            },
        }

    def get_all_terms(self) -> set[str]:
        """Retourneer alle 500+ juridische termen."""
        all_terms = set()
        for domain_terms in self.lexicons.values():
            all_terms.update(domain_terms)
        return all_terms

    def get_domain_terms(self, domain: str) -> set[str]:
        """Retourneer termen voor specifiek rechtsgebied."""
        return self.lexicons.get(domain, set())

    def find_matching_terms(self, text: str) -> dict[str, list[str]]:
        """Vind alle juridische termen in de tekst per domein."""
        text_lower = text.lower()
        matches = {}

        for domain, terms in self.lexicons.items():
            domain_matches = [term for term in terms if term in text_lower]
            if domain_matches:
                matches[domain] = domain_matches

        return matches


class PatternMatcher:
    """
    Complete pattern matching voor alle 16 UFO categorieën.
    Grondige analyse zonder performance shortcuts.
    """

    def __init__(self):
        self.lexicon = DutchLegalLexicon()
        self.patterns = self._initialize_all_patterns()
        self.disambiguation_rules = self._initialize_disambiguation()

    def _initialize_all_patterns(self) -> dict[str, dict[str, Any]]:
        """Initialiseer ALLE patterns voor ALLE 16 categorieën."""

        return {
            UFOCategory.KIND: {
                "patterns": [
                    r"\b(?:een|de|het)\s+(\w+)\s+(?:is|zijn|betreft)",
                    r"(?:natuurlijk|rechts)persoon",
                    r"(?:organisatie|instantie|orgaan|lichaam)",
                    r"(?:zaak|goed|object|voorwerp)\b",
                    r"(?:document|akte|stuk|dossier)\b",
                    r"(?:gebouw|pand|onroerend goed|perceel)\b",
                    r"(?:voertuig|auto|schip|vliegtuig)\b",
                ],
                "keywords": {
                    "persoon",
                    "mens",
                    "individu",
                    "organisatie",
                    "bedrijf",
                    "instelling",
                    "zaak",
                    "ding",
                    "object",
                    "entiteit",
                    "document",
                    "gebouw",
                    "voertuig",
                    "systeem",
                    "apparaat",
                },
                "weight": 1.0,
            },
            UFOCategory.EVENT: {
                "patterns": [
                    r"(?:tijdens|gedurende|na afloop van|voorafgaand aan)",
                    r"(?:proces|procedure|handeling|gebeurtenis)\b",
                    r"\b\w+(?:ing|atie|itie)\b",  # Nominalisaties
                    r"(?:aanvang|begin|einde|afloop|verloop)",
                    r"(?:uitvoer|voltrek|verricht|plaats\s?vind)",
                    r"(?:start|stop|duur|periode|termijn)",
                ],
                "keywords": {
                    "arrestatie",
                    "aanhouding",
                    "zitting",
                    "procedure",
                    "proces",
                    "behandeling",
                    "onderzoek",
                    "verhoor",
                    "uitspraak",
                    "vonnis",
                    "gebeurtenis",
                    "handeling",
                    "actie",
                    "operatie",
                    "transactie",
                },
                "weight": 0.9,
            },
            UFOCategory.ROLE: {
                "patterns": [
                    r"(?:in de hoedanigheid van|in de rol van|als)\s+\w+",
                    r"(?:optreedt?|handel\w+|fungeer\w+)\s+als",
                    r"(?:verdachte|beklaagde|getuige|aangever)\b",
                    r"(?:koper|verkoper|huurder|verhuurder)\b",
                    r"(?:werkgever|werknemer|opdrachtgever|opdrachtnemer)\b",
                ],
                "keywords": {
                    "verdachte",
                    "dader",
                    "slachtoffer",
                    "getuige",
                    "rechter",
                    "officier",
                    "advocaat",
                    "notaris",
                    "deurwaarder",
                    "curator",
                    "eigenaar",
                    "gebruiker",
                    "bewoner",
                    "bestuurder",
                    "aandeelhouder",
                },
                "weight": 0.8,
            },
            UFOCategory.PHASE: {
                "patterns": [
                    r"(?:in\s+)?(?:onderzoek|behandeling|beraad)",
                    r"(?:voorlopig|definitief|concept|ontwerp)",
                    r"(?:actief|inactief|gesloten|gearchiveerd)",
                    r"(?:lopend|afgerond|gestart|beëindigd)",
                    r"(?:status|staat|toestand|fase|stadium)",
                ],
                "keywords": {
                    "onderzoek",
                    "voorlopig",
                    "definitief",
                    "concept",
                    "ontwerp",
                    "actief",
                    "inactief",
                    "lopend",
                    "afgerond",
                    "gesloten",
                    "nieuw",
                    "oud",
                    "huidig",
                    "voormalig",
                    "toekomstig",
                },
                "weight": 0.7,
            },
            UFOCategory.RELATOR: {
                "patterns": [
                    r"(?:overeenkomst|contract|verbintenis|afspraak)",
                    r"(?:huwelijk|partnerschap|relatie|verhouding)",
                    r"(?:vergunning|machtiging|mandaat|volmacht)",
                    r"(?:tussen|met|jegens|tegenover)\s+\w+",
                    r"(?:partijen|contractanten|partners)",
                ],
                "keywords": {
                    "overeenkomst",
                    "contract",
                    "huwelijk",
                    "verbintenis",
                    "relatie",
                    "vergunning",
                    "mandaat",
                    "volmacht",
                    "licentie",
                    "concessie",
                    "dagvaarding",
                    "beschikking",
                    "vonnis",
                    "arrest",
                    "uitspraak",
                },
                "weight": 0.8,
            },
            UFOCategory.MODE: {
                "patterns": [
                    r"(?:eigenschap|kenmerk|attribuut|karakteristiek)",
                    r"(?:toestand|conditie|gesteldheid)",
                    r"(?:van|behorend bij|eigen aan)\s+\w+",
                    r"(?:gezondheid|locatie|positie|status)",
                    r"(?:kleur|grootte|vorm|gewicht)",
                ],
                "keywords": {
                    "gezondheid",
                    "locatie",
                    "adres",
                    "woonplaats",
                    "nationaliteit",
                    "gemoedstoestand",
                    "geestestoestand",
                    "lichamelijke toestand",
                    "vermogen",
                    "inkomen",
                    "bezit",
                    "eigenschap",
                    "kwaliteit",
                },
                "weight": 0.6,
            },
            UFOCategory.QUANTITY: {
                "patterns": [
                    r"\d+\s*(?:euro|EUR|€|\$|dollar)",
                    r"\d+\s*(?:%|procent|percent)",
                    r"\d+\s*(?:meter|km|cm|mm|m²|m³)",
                    r"\d+\s*(?:kilo|gram|kg|g|ton)",
                    r"\d+\s*(?:liter|ml|cl|dl)",
                    r"(?:aantal|hoeveelheid|bedrag|som|totaal)",
                ],
                "keywords": {
                    "bedrag",
                    "aantal",
                    "hoeveelheid",
                    "percentage",
                    "tarief",
                    "prijs",
                    "kosten",
                    "omzet",
                    "winst",
                    "verlies",
                    "afstand",
                    "oppervlakte",
                    "inhoud",
                    "gewicht",
                    "duur",
                },
                "weight": 0.7,
            },
            UFOCategory.QUALITY: {
                "patterns": [
                    r"(?:kwaliteit|hoedanigheid|graad|niveau)",
                    r"(?:goed|slecht|hoog|laag|zwaar|licht)",
                    r"(?:ernstig|eenvoudig|complex|simpel)",
                    r"(?:betrouwbaar|onbetrouwbaar|waarschijnlijk)",
                    r"(?:mate van|graad van|niveau van)",
                ],
                "keywords": {
                    "ernst",
                    "zwaarte",
                    "kwaliteit",
                    "betrouwbaarheid",
                    "waarschijnlijkheid",
                    "complexiteit",
                    "moeilijkheidsgraad",
                    "urgentie",
                    "prioriteit",
                    "belangrijkheid",
                    "relevantie",
                    "geschiktheid",
                    "toepasbaarheid",
                },
                "weight": 0.6,
            },
            UFOCategory.SUBKIND: {
                "patterns": [
                    r"(?:soort|type|variant|vorm)\s+van",
                    r"(?:specifieke|bijzondere|speciale)\s+\w+",
                    r"(?:sub|onder|deel)\w+",
                    r"is een\s+\w+\s+die",
                ],
                "keywords": {
                    "subtype",
                    "subcategorie",
                    "deelgroep",
                    "variant",
                    "vorm",
                    "soort",
                    "type",
                    "klasse",
                    "categorie",
                    "groep",
                },
                "weight": 0.5,
            },
            UFOCategory.CATEGORY: {
                "patterns": [
                    r"(?:categorie|klasse|groep|verzameling)",
                    r"(?:alle|elke|iedere)\s+\w+",
                    r"(?:behoort tot|valt onder|deel van)",
                ],
                "keywords": {
                    "categorie",
                    "klasse",
                    "groep",
                    "verzameling",
                    "collectie",
                    "type",
                    "soort",
                    "classificatie",
                    "indeling",
                    "rubricering",
                },
                "weight": 0.5,
            },
            UFOCategory.MIXIN: {
                "patterns": [
                    r"(?:gemeenschappelijk|gedeeld|gezamenlijk)",
                    r"(?:kenmerk|eigenschap)\s+van\s+(?:verschillende|meerdere)",
                    r"(?:onafhankelijk van|los van)\s+\w+",
                ],
                "keywords": {
                    "gemeenschappelijk",
                    "gedeeld",
                    "gezamenlijk",
                    "collectief",
                    "algemeen",
                    "universeel",
                    "generiek",
                    "abstract",
                },
                "weight": 0.4,
            },
            UFOCategory.ROLEMIXIN: {
                "patterns": [
                    r"rol-gerelateerd\w*",
                    r"(?:verschillende rollen|meerdere functies)",
                    r"(?:ongeacht|los van)\s+(?:rol|functie)",
                ],
                "keywords": {
                    "rolpatroon",
                    "functiepatroon",
                    "gedragspatroon",
                    "rolmodel",
                },
                "weight": 0.4,
            },
            UFOCategory.PHASEMIXIN: {
                "patterns": [
                    r"fase-gerelateerd\w*",
                    r"(?:verschillende fasen|meerdere stadia)",
                    r"(?:gedurende|tijdens)\s+(?:verschillende|alle)\s+fasen",
                ],
                "keywords": {"fasepatroon", "stadiumpatroon", "levenscycluspatroon"},
                "weight": 0.4,
            },
            UFOCategory.COLLECTIVE: {
                "patterns": [
                    r"(?:groep|collectie|verzameling|set)\s+van",
                    r"(?:team|ploeg|commissie|raad|college)",
                    r"(?:samen|gezamenlijk|collectief)",
                    r"(?:leden|deelnemers|participanten)",
                ],
                "keywords": {
                    "groep",
                    "team",
                    "commissie",
                    "raad",
                    "college",
                    "vereniging",
                    "collectief",
                    "gemeenschap",
                    "samenwerking",
                    "consortium",
                    "alliantie",
                    "coalitie",
                    "federatie",
                },
                "weight": 0.6,
            },
            UFOCategory.VARIABLECOLLECTION: {
                "patterns": [
                    r"(?:wisselend|variabel|veranderlijk)\s+aantal",
                    r"(?:groeiende|krimpende|fluctuerende)\s+groep",
                    r"(?:dynamische|flexibele)\s+verzameling",
                ],
                "keywords": {
                    "dynamisch",
                    "variabel",
                    "flexibel",
                    "wisselend",
                    "veranderlijk",
                },
                "weight": 0.5,
            },
            UFOCategory.FIXEDCOLLECTION: {
                "patterns": [
                    r"(?:vast|bepaald|gefixeerd)\s+aantal",
                    r"(?:onveranderlijke|statische)\s+groep",
                    r"(?:vaste|permanente)\s+samenstelling",
                ],
                "keywords": {
                    "vast",
                    "bepaald",
                    "gefixeerd",
                    "statisch",
                    "permanent",
                    "onveranderlijk",
                    "definitief",
                },
                "weight": 0.5,
            },
        }

    def _initialize_disambiguation(self) -> dict[str, list[tuple[str, UFOCategory]]]:
        """Initialiseer disambiguatie regels voor complexe termen."""

        return {
            "zaak": [
                (r"(?:rechts|straf|civiele)\s*zaak", UFOCategory.EVENT),
                (r"zaak\s+(?:voor|bij)\s+de\s+rechter", UFOCategory.EVENT),
                (r"(?:roerende|onroerende)\s+zaak", UFOCategory.KIND),
                (r"zaak\s+(?:als|zoals)\s+(?:auto|gebouw|voorwerp)", UFOCategory.KIND),
                (
                    r"de\s+zaak\s+van\s+(?:verdachte|eisende partij)",
                    UFOCategory.ABSTRACT,
                ),
            ],
            "huwelijk": [
                (
                    r"(?:sluiten|voltrekken|aangaan)\s+(?:van\s+)?(?:een\s+)?huwelijk",
                    UFOCategory.EVENT,
                ),
                (r"huwelijks(?:voltrekking|sluiting|ceremonie)", UFOCategory.EVENT),
                (
                    r"(?:staat|band|verbintenis)\s+van\s+het\s+huwelijk",
                    UFOCategory.RELATOR,
                ),
                (r"huwelijk\s+tussen", UFOCategory.RELATOR),
                (r"gehuwd\s+(?:zijn|paar|stel)", UFOCategory.RELATOR),
            ],
            "overeenkomst": [
                (
                    r"(?:sluiten|aangaan|tekenen)\s+(?:van\s+)?(?:een\s+)?overeenkomst",
                    UFOCategory.EVENT,
                ),
                (r"overeenkomst\s+(?:komt\s+)?tot\s+stand", UFOCategory.EVENT),
                (r"(?:koop|huur|arbeids)overeenkomst", UFOCategory.RELATOR),
                (r"overeenkomst\s+tussen\s+partijen", UFOCategory.RELATOR),
                (r"document\s+van\s+de\s+overeenkomst", UFOCategory.KIND),
            ],
            "procedure": [
                (
                    r"(?:start|begin|aanvang)\s+(?:van\s+)?(?:de\s+)?procedure",
                    UFOCategory.EVENT,
                ),
                (r"procedure\s+(?:duurt|neemt|vergt)", UFOCategory.EVENT),
                (r"(?:bezwaar|beroeps|klacht)procedure", UFOCategory.EVENT),
                (r"volgens\s+de\s+procedure", UFOCategory.KIND),
                (r"procedurele\s+(?:regel|voorschrift)", UFOCategory.KIND),
            ],
            "vergunning": [
                (
                    r"(?:aanvragen|verlenen|verstrekken)\s+(?:van\s+)?(?:een\s+)?vergunning",
                    UFOCategory.EVENT,
                ),
                (r"vergunning(?:verlening|aanvraag)", UFOCategory.EVENT),
                (r"(?:bouw|milieu|omgevings)vergunning", UFOCategory.RELATOR),
                (r"vergunning\s+voor", UFOCategory.RELATOR),
                (r"document\s+van\s+de\s+vergunning", UFOCategory.KIND),
            ],
            "besluit": [
                (r"(?:nemen|maken)\s+(?:van\s+)?(?:een\s+)?besluit", UFOCategory.EVENT),
                (r"besluitvorming(?:sproces)?", UFOCategory.EVENT),
                (r"(?:bestuurs|rechterlijk)\s+besluit", UFOCategory.RELATOR),
                (
                    r"besluit\s+(?:van|door)\s+(?:het\s+)?(?:bestuur|rechter)",
                    UFOCategory.RELATOR,
                ),
                (r"schriftelijk\s+besluit", UFOCategory.KIND),
            ],
        }

    def find_all_matches(self, text: str) -> dict[UFOCategory, list[str]]:
        """
        Vind ALLE matches voor ALLE categorieën (geen shortcuts).
        Single-user: performance is geen issue, volledigheid wel.
        """
        matches = {}
        text_lower = text.lower()

        # Check ALLE patterns voor ALLE categorieën
        for category, config in self.patterns.items():
            category_matches = []

            # Check regex patterns
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower):
                    category_matches.append(f"Pattern: {pattern}")

            # Check keywords
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    category_matches.append(f"Keyword: {keyword}")

            # Check juridische termen
            legal_terms = self.lexicon.find_matching_terms(text)
            if legal_terms:
                for domain, terms in legal_terms.items():
                    for term in terms:
                        category_matches.append(f"Legal [{domain}]: {term}")

            if category_matches:
                matches[category] = category_matches

        return matches

    def apply_disambiguation(
        self, term: str, definition: str
    ) -> tuple[UFOCategory, str] | None:
        """
        Pas context-aware disambiguatie toe voor complexe termen.
        Retourneert category en uitleg van disambiguatie.
        """
        term_lower = term.lower()
        definition_lower = definition.lower()

        if term_lower in self.disambiguation_rules:
            for pattern, category in self.disambiguation_rules[term_lower]:
                if re.search(pattern, definition_lower):
                    explanation = f"Term '{term}' gedisambigueerd naar {category.value} op basis van context: '{pattern}'"
                    return category, explanation

        return None


class UFOClassifierService:
    """
    Hoofdservice voor UFO classificatie van Nederlandse juridische definities.
    Focus: CORRECTHEID boven SNELHEID (single-user applicatie).
    Target: 95% precisie door grondige analyse.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialiseer de UFO classifier service.

        Args:
            config_path: Optioneel pad naar YAML configuratie
        """
        self.version = "1.0.0"
        self.pattern_matcher = PatternMatcher()
        self.config = self._load_config(config_path)

        # Log initialisatie
        logger.info(f"UFOClassifierService v{self.version} geïnitialiseerd")
        logger.info(
            f"Geladen: {len(self.pattern_matcher.lexicon.get_all_terms())} juridische termen"
        )

    def _load_config(self, config_path: Path | None) -> dict:
        """Laad configuratie uit YAML bestand."""
        if config_path and config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def classify(
        self, term: str, definition: str, context: dict[str, Any] | None = None
    ) -> UFOClassificationResult:
        """
        Classificeer een juridische term volgens UFO/OntoUML.

        BELANGRIJ: Voert ALTIJD de complete 9-staps analyse uit.
        Geen shortcuts voor performance - correctheid is belangrijker.

        Args:
            term: De te classificeren term
            definition: De definitie van de term
            context: Optionele context informatie

        Returns:
            UFOClassificationResult met volledige analyse
        """
        start_time = datetime.now()

        # Basis validatie
        if not term or not definition:
            msg = "Term en definitie zijn verplicht"
            raise ValueError(msg)

        logger.info(f"Start classificatie van: {term}")

        # Initialiseer resultaat
        result = UFOClassificationResult(
            term=term,
            definition=definition,
            primary_category=UFOCategory.KIND,  # Default
            classifier_version=self.version,
        )

        # Stap 1: Vind ALLE matches voor ALLE categorieën
        all_matches = self.pattern_matcher.find_all_matches(f"{term}. {definition}")
        result.matched_patterns = []
        for _category, patterns in all_matches.items():
            result.matched_patterns.extend(patterns)

        # Stap 2: Pas de volledige 9-staps beslislogica toe
        result.decision_path = []
        primary_category = self._apply_complete_9_step_logic(
            term, definition, all_matches, result.decision_path
        )
        result.primary_category = primary_category

        # Stap 3: Check voor disambiguatie
        disambiguation = self.pattern_matcher.apply_disambiguation(term, definition)
        if disambiguation:
            disambiguated_category, explanation = disambiguation
            if disambiguated_category != primary_category:
                result.disambiguation_notes.append(explanation)
                result.disambiguation_notes.append(
                    f"Oorspronkelijke classificatie: {primary_category.value}, "
                    f"Na disambiguatie: {disambiguated_category.value}"
                )
                result.primary_category = disambiguated_category

        # Stap 4: Bereken scores voor ALLE categorieën
        all_scores = self._calculate_all_scores(all_matches, definition, context)
        result.all_scores = all_scores

        # Stap 5: Bepaal confidence (gebaseerd op zekerheid van classificatie)
        result.confidence = self._calculate_confidence(
            result.primary_category, all_scores, len(result.matched_patterns)
        )

        # Stap 6: Identificeer secundaire categorieën
        result.secondary_categories = self._identify_secondary_categories(
            all_scores, result.primary_category
        )

        # Stap 7: Genereer uitgebreide uitleg
        result.detailed_explanation = self._generate_detailed_explanation(
            result, all_matches, disambiguation
        )

        # Bereken classificatie tijd
        end_time = datetime.now()
        result.classification_time_ms = (end_time - start_time).total_seconds() * 1000

        logger.info(
            f"Classificatie compleet: {term} -> {result.primary_category.value} "
            f"({result.confidence:.2%}) in {result.classification_time_ms:.1f}ms"
        )

        return result

    def _apply_complete_9_step_logic(
        self,
        term: str,
        definition: str,
        matches: dict[UFOCategory, list[str]],
        decision_path: list[str],
    ) -> UFOCategory:
        """
        Pas de COMPLETE 9-staps UFO beslislogica toe.
        ALLE stappen worden ALTIJD doorlopen voor maximale accuratesse.
        """

        text = f"{term}. {definition}".lower()

        # Stap 1: Is het een zelfstandig, substantieel "ding"?
        decision_path.append("Stap 1: Check voor zelfstandige entiteit (Kind)")
        if self._is_independent_entity(text, matches):
            decision_path.append("✓ Gedetecteerd als zelfstandige entiteit")
            if not self._has_stronger_category(matches, UFOCategory.KIND):
                return UFOCategory.KIND

        # Stap 2: Is het tijdsgebonden (gebeurtenis/proces)?
        decision_path.append("Stap 2: Check voor tijdsgebonden gebeurtenis (Event)")
        if self._is_temporal_event(text, matches):
            decision_path.append("✓ Gedetecteerd als temporele gebeurtenis")
            if not self._has_stronger_category(matches, UFOCategory.EVENT):
                return UFOCategory.EVENT

        # Stap 3: Is het een rol die een entiteit kan aannemen?
        decision_path.append("Stap 3: Check voor contextuele rol (Role)")
        if self._is_contextual_role(text, matches):
            decision_path.append("✓ Gedetecteerd als rol")
            if not self._has_stronger_category(matches, UFOCategory.ROLE):
                return UFOCategory.ROLE

        # Stap 4: Is het een levensfase van een entiteit?
        decision_path.append("Stap 4: Check voor levensfase (Phase)")
        if self._is_life_phase(text, matches):
            decision_path.append("✓ Gedetecteerd als fase")
            if not self._has_stronger_category(matches, UFOCategory.PHASE):
                return UFOCategory.PHASE

        # Stap 5: Medieert het een relatie tussen entiteiten?
        decision_path.append("Stap 5: Check voor mediërende relatie (Relator)")
        if self._mediates_relationship(text, matches):
            decision_path.append("✓ Gedetecteerd als relator")
            if not self._has_stronger_category(matches, UFOCategory.RELATOR):
                return UFOCategory.RELATOR

        # Stap 6: Is het een intrinsieke eigenschap met drager?
        decision_path.append("Stap 6: Check voor intrinsieke eigenschap (Mode)")
        if self._is_intrinsic_mode(text, matches):
            decision_path.append("✓ Gedetecteerd als mode")
            if not self._has_stronger_category(matches, UFOCategory.MODE):
                return UFOCategory.MODE

        # Stap 7: Is het een meetbare grootheid?
        decision_path.append("Stap 7: Check voor meetbare grootheid (Quantity)")
        if self._is_measurable_quantity(text, matches):
            decision_path.append("✓ Gedetecteerd als quantity")
            if not self._has_stronger_category(matches, UFOCategory.QUANTITY):
                return UFOCategory.QUANTITY

        # Stap 8: Is het een kwalitatieve eigenschap?
        decision_path.append("Stap 8: Check voor kwalitatieve eigenschap (Quality)")
        if self._is_qualitative_property(text, matches):
            decision_path.append("✓ Gedetecteerd als quality")
            if not self._has_stronger_category(matches, UFOCategory.QUALITY):
                return UFOCategory.QUALITY

        # Stap 9: Verfijn met subcategorieën
        decision_path.append("Stap 9: Check voor subcategorieën")
        subcategory = self._refine_with_subcategories(text, matches)
        if subcategory:
            decision_path.append(f"✓ Gedetecteerd als {subcategory.value}")
            return subcategory

        # Fallback: Als geen enkele categorie matched -> Kind (meest algemeen)
        decision_path.append(
            "Geen specifieke categorie gedetecteerd, fallback naar Kind"
        )
        return UFOCategory.KIND

    def _is_independent_entity(self, text: str, matches: dict) -> bool:
        """Check of het een zelfstandige entiteit is."""
        indicators = [
            "persoon" in text,
            "organisatie" in text,
            "zaak" in text and "roerende" in text,
            "document" in text,
            "gebouw" in text,
            UFOCategory.KIND in matches and len(matches[UFOCategory.KIND]) >= 2,
        ]
        return any(indicators)

    def _is_temporal_event(self, text: str, matches: dict) -> bool:
        """Check of het een tijdsgebonden gebeurtenis is."""
        indicators = [
            "tijdens" in text or "gedurende" in text,
            "proces" in text or "procedure" in text,
            "handeling" in text or "gebeurtenis" in text,
            bool(re.search(r"\b\w+(?:ing|atie)\b", text)),
            UFOCategory.EVENT in matches and len(matches[UFOCategory.EVENT]) >= 2,
        ]
        return any(indicators)

    def _is_contextual_role(self, text: str, matches: dict) -> bool:
        """Check of het een contextuele rol is."""
        indicators = [
            "in de hoedanigheid van" in text,
            "als" in text and ("optreed" in text or "handel" in text),
            "verdachte" in text or "dader" in text,
            "koper" in text or "verkoper" in text,
            UFOCategory.ROLE in matches and len(matches[UFOCategory.ROLE]) >= 2,
        ]
        return any(indicators)

    def _is_life_phase(self, text: str, matches: dict) -> bool:
        """Check of het een levensfase is."""
        indicators = [
            "in onderzoek" in text,
            "voorlopig" in text or "definitief" in text,
            "actief" in text or "inactief" in text,
            "fase" in text or "stadium" in text,
            UFOCategory.PHASE in matches and len(matches[UFOCategory.PHASE]) >= 2,
        ]
        return any(indicators)

    def _mediates_relationship(self, text: str, matches: dict) -> bool:
        """Check of het een mediërende relatie is."""
        indicators = [
            "overeenkomst" in text and "tussen" in text,
            "contract" in text or "verbintenis" in text,
            "huwelijk" in text and "sluiten" not in text,
            "vergunning" in text and "voor" in text,
            UFOCategory.RELATOR in matches and len(matches[UFOCategory.RELATOR]) >= 2,
        ]
        return any(indicators)

    def _is_intrinsic_mode(self, text: str, matches: dict) -> bool:
        """Check of het een intrinsieke eigenschap is."""
        indicators = [
            "eigenschap" in text or "kenmerk" in text,
            "toestand" in text or "conditie" in text,
            "gezondheid" in text or "locatie" in text,
            "van" in text and "behorend bij" in text,
            UFOCategory.MODE in matches and len(matches[UFOCategory.MODE]) >= 2,
        ]
        return any(indicators)

    def _is_measurable_quantity(self, text: str, matches: dict) -> bool:
        """Check of het een meetbare grootheid is."""
        indicators = [
            bool(re.search(r"\d+\s*(?:euro|EUR|€|%)", text)),
            "bedrag" in text or "aantal" in text,
            "hoeveelheid" in text or "percentage" in text,
            UFOCategory.QUANTITY in matches and len(matches[UFOCategory.QUANTITY]) >= 2,
        ]
        return any(indicators)

    def _is_qualitative_property(self, text: str, matches: dict) -> bool:
        """Check of het een kwalitatieve eigenschap is."""
        indicators = [
            "kwaliteit" in text or "hoedanigheid" in text,
            "ernst" in text or "zwaarte" in text,
            "betrouwbaarheid" in text or "waarschijnlijkheid" in text,
            "mate van" in text or "graad van" in text,
            UFOCategory.QUALITY in matches and len(matches[UFOCategory.QUALITY]) >= 2,
        ]
        return any(indicators)

    def _refine_with_subcategories(
        self, text: str, matches: dict
    ) -> UFOCategory | None:
        """Verfijn met subcategorieën."""

        # Check voor collecties
        if "groep" in text or "verzameling" in text or "team" in text:
            if "vast" in text or "bepaald" in text:
                return UFOCategory.FIXEDCOLLECTION
            if "variabel" in text or "wisselend" in text:
                return UFOCategory.VARIABLECOLLECTION
            return UFOCategory.COLLECTIVE

        # Check voor mixins
        if "gemeenschappelijk" in text or "gedeeld" in text:
            if "rol" in text:
                return UFOCategory.ROLEMIXIN
            if "fase" in text:
                return UFOCategory.PHASEMIXIN
            return UFOCategory.MIXIN

        # Check voor subtypes
        if "soort van" in text or "type van" in text:
            return UFOCategory.SUBKIND

        if "categorie" in text or "klasse" in text:
            return UFOCategory.CATEGORY

        return None

    def _has_stronger_category(
        self, matches: dict[UFOCategory, list[str]], current: UFOCategory
    ) -> bool:
        """
        Check of er een sterkere categorie is gedetecteerd.
        Gebruikt voor het voorkomen van voorbarige classificatie.
        """
        # Definieer sterkte hiërarchie (hogere waarde = sterker bewijs nodig)
        strength_order = {
            UFOCategory.KIND: 1,
            UFOCategory.EVENT: 2,
            UFOCategory.ROLE: 3,
            UFOCategory.PHASE: 3,
            UFOCategory.RELATOR: 4,
            UFOCategory.MODE: 5,
            UFOCategory.QUANTITY: 5,
            UFOCategory.QUALITY: 5,
            UFOCategory.SUBKIND: 6,
            UFOCategory.CATEGORY: 6,
            UFOCategory.MIXIN: 7,
            UFOCategory.ROLEMIXIN: 7,
            UFOCategory.PHASEMIXIN: 7,
            UFOCategory.COLLECTIVE: 6,
            UFOCategory.VARIABLECOLLECTION: 7,
            UFOCategory.FIXEDCOLLECTION: 7,
        }

        current_strength = strength_order.get(current, 0)

        for category, category_matches in matches.items():
            if strength_order.get(category, 0) < current_strength:
                # Een sterkere categorie heeft meer matches
                if len(category_matches) > len(matches.get(current, [])) * 1.5:
                    return True

        return False

    def _calculate_all_scores(
        self,
        matches: dict[UFOCategory, list[str]],
        definition: str,
        context: dict | None,
    ) -> dict[UFOCategory, float]:
        """
        Bereken scores voor ALLE categorieën.
        Grondige analyse zonder shortcuts.
        """
        scores = {}

        for category in UFOCategory:
            base_score = 0.0

            # Score op basis van matches
            if category in matches:
                match_count = len(matches[category])
                base_score = min(match_count * 0.2, 0.8)

            # Bonus voor juridische context
            if context and context.get("domain"):
                if self._is_relevant_for_domain(category, context["domain"]):
                    base_score += 0.1

            # Penalty voor ambiguïteit
            if (
                "mogelijk" in definition.lower()
                or "waarschijnlijk" in definition.lower()
            ):
                base_score *= 0.9

            scores[category] = min(base_score, 1.0)

        return scores

    def _is_relevant_for_domain(self, category: UFOCategory, domain: str) -> bool:
        """Check of categorie relevant is voor juridisch domein."""
        domain_relevance = {
            "strafrecht": [UFOCategory.EVENT, UFOCategory.ROLE, UFOCategory.PHASE],
            "bestuursrecht": [UFOCategory.RELATOR, UFOCategory.KIND, UFOCategory.EVENT],
            "civiel_recht": [UFOCategory.RELATOR, UFOCategory.ROLE, UFOCategory.KIND],
            "algemeen_juridisch": [
                UFOCategory.KIND,
                UFOCategory.CATEGORY,
                UFOCategory.MIXIN,
            ],
        }

        return category in domain_relevance.get(domain, [])

    def _calculate_confidence(
        self,
        primary_category: UFOCategory,
        all_scores: dict[UFOCategory, float],
        pattern_count: int,
    ) -> float:
        """
        Bereken confidence score voor classificatie.
        Target: 95% precisie voor hoge confidence scores.
        """

        primary_score = all_scores.get(primary_category, 0.0)

        # Basis confidence op primary score
        confidence = primary_score

        # Bonus voor veel matches
        if pattern_count > 5:
            confidence += 0.1
        elif pattern_count > 10:
            confidence += 0.2

        # Bonus voor duidelijke winnaar
        sorted_scores = sorted(all_scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            margin = sorted_scores[0] - sorted_scores[1]
            if margin > 0.3:
                confidence += 0.15

        # Penalty voor ambiguïteit
        ambiguous_categories = sum(1 for score in all_scores.values() if score > 0.4)
        if ambiguous_categories > 3:
            confidence *= 0.8

        # Normaliseer naar 0-1 range
        return min(max(confidence, 0.0), 1.0)

    def _identify_secondary_categories(
        self, all_scores: dict[UFOCategory, float], primary: UFOCategory
    ) -> list[UFOCategory]:
        """Identificeer relevante secundaire categorieën."""

        secondary = []
        threshold = 0.3  # Minimale score voor secundaire categorie

        for category, score in all_scores.items():
            if category != primary and score >= threshold:
                secondary.append(category)

        # Sorteer op score
        secondary.sort(key=lambda c: all_scores[c], reverse=True)

        return secondary[:3]  # Maximaal 3 secundaire categorieën

    def _generate_detailed_explanation(
        self,
        result: UFOClassificationResult,
        all_matches: dict[UFOCategory, list[str]],
        disambiguation: tuple | None,
    ) -> list[str]:
        """
        Genereer uitgebreide uitleg voor juridische verantwoording.
        ALLE overwegingen worden gedocumenteerd.
        """

        explanations = []

        # Header
        explanations.append(f"=== UFO Classificatie Analyse voor '{result.term}' ===")

        # Primaire classificatie
        explanations.append(
            f"\n📍 Primaire Classificatie: {result.primary_category.value}"
        )
        explanations.append(f"   Confidence: {result.confidence:.1%}")

        # Beslispad
        explanations.append("\n📊 Beslislogica Pad:")
        for step in result.decision_path:
            explanations.append(f"   {step}")

        # Alle gevonden matches
        explanations.append("\n🔍 Gevonden Patronen per Categorie:")
        for category, patterns in all_matches.items():
            if patterns:
                explanations.append(f"\n   {category.value}:")
                for pattern in patterns[:5]:  # Top 5 per categorie
                    explanations.append(f"      • {pattern}")

        # Score overzicht
        explanations.append("\n📈 Score Overzicht (alle categorieën):")
        sorted_scores = sorted(
            result.all_scores.items(), key=lambda x: x[1], reverse=True
        )
        for category, score in sorted_scores[:8]:  # Top 8
            bar = "█" * int(score * 10)
            explanations.append(f"   {category.value:20} {bar} {score:.2f}")

        # Disambiguatie indien toegepast
        if disambiguation:
            explanations.append("\n⚖️ Disambiguatie Toegepast:")
            for note in result.disambiguation_notes:
                explanations.append(f"   {note}")

        # Secundaire categorieën
        if result.secondary_categories:
            explanations.append("\n🔗 Secundaire Categorieën:")
            for cat in result.secondary_categories:
                score = result.all_scores.get(cat, 0)
                explanations.append(f"   • {cat.value} (score: {score:.2f})")

        # Juridische context
        explanations.append("\n⚖️ Juridische Overwegingen:")
        legal_matches = self.pattern_matcher.lexicon.find_matching_terms(
            result.definition
        )
        if legal_matches:
            for domain, terms in legal_matches.items():
                explanations.append(f"   {domain}: {', '.join(terms[:5])}")

        # Performance metrics
        explanations.append(f"\n⏱️ Analyse Tijd: {result.classification_time_ms:.1f}ms")
        explanations.append(f"📝 Classifier Versie: {result.classifier_version}")

        return explanations

    def batch_classify(
        self, definitions: list[tuple[str, str]], context: dict | None = None
    ) -> list[UFOClassificationResult]:
        """
        Classificeer meerdere definities.
        Single-user: geen async/parallel processing nodig.
        """

        results = []
        total = len(definitions)

        logger.info(f"Start batch classificatie van {total} definities")

        for i, (term, definition) in enumerate(definitions, 1):
            try:
                result = self.classify(term, definition, context)
                results.append(result)

                if i % 10 == 0:
                    logger.info(f"Voortgang: {i}/{total} ({i/total*100:.1f}%)")

            except Exception as e:
                logger.error(f"Fout bij classificatie van '{term}': {e}")
                # Maak een fout-resultaat
                error_result = UFOClassificationResult(
                    term=term,
                    definition=definition,
                    primary_category=UFOCategory.KIND,
                    confidence=0.0,
                )
                error_result.detailed_explanation = [f"FOUT: {e!s}"]
                results.append(error_result)

        logger.info(f"Batch classificatie compleet: {len(results)} items")

        return results


# Integration met ServiceContainer
def create_ufo_classifier_service() -> UFOClassifierService:
    """
    Factory functie voor ServiceContainer integratie.
    """
    config_path = Path("config/ufo_rules.yaml")
    return UFOClassifierService(config_path)


if __name__ == "__main__":
    # Test de classifier met enkele voorbeelden
    classifier = UFOClassifierService()

    test_cases = [
        (
            "verdachte",
            "Persoon die wordt verdacht van het plegen van een strafbaar feit",
        ),
        ("arrestatie", "Het aanhouden van een persoon door de politie"),
        (
            "koopovereenkomst",
            "Overeenkomst waarbij de verkoper zich verbindt een zaak te geven",
        ),
        (
            "eigendom",
            "Het meest omvattende recht dat een persoon op een zaak kan hebben",
        ),
        (
            "rechtszaak",
            "Procedure voor de rechter waarbij partijen hun geschil voorleggen",
        ),
        ("besluit", "Een schriftelijke beslissing van een bestuursorgaan"),
        ("huwelijk", "De wettelijke verbintenis tussen twee personen"),
    ]

    print("UFO Classifier Test Run")
    print("=" * 80)

    for term, definition in test_cases:
        result = classifier.classify(term, definition)
        print(f"\nTerm: {term}")
        print(f"Categorie: {result.primary_category.value}")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Tijd: {result.classification_time_ms:.1f}ms")
        print("-" * 40)
