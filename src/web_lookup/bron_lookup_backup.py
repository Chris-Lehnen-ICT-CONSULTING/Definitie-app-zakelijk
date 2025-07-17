"""
Bron Lookup Module - Zoekt en valideert bronnen voor definities.
Integreert met externe bronnen en interne repositories.
"""

import re  # Reguliere expressies voor het herkennen van bron patronen
import logging  # Logging faciliteiten voor debug en monitoring
import asyncio  # Asynchrone programmering voor parallelle bron lookups
from typing import Dict, List, Any, Optional, Tuple, Set  # Type hints voor code documentatie
from dataclasses import dataclass  # Dataklassen voor gestructureerde bron data
from enum import Enum  # Enumeraties voor bron types en validiteit
from datetime import datetime  # Datum en tijd functionaliteit voor tijdstempels
import json  # JSON verwerking voor metadata opslag
import os  # Operating system interface voor configuratie toegang

logger = logging.getLogger(__name__)  # Logger instantie voor bron lookup module


class BronType(Enum):
    """Types van juridische en beleidsmatige bronnen."""
    WETGEVING = "wetgeving"                  # Wetten en wettelijke regelingen
    JURISPRUDENTIE = "jurisprudentie"        # Rechterlijke uitspraken
    LITERATUUR = "literatuur"                # Juridische literatuur en publicaties
    BELEID = "beleid"                        # Beleidsdocumenten en richtlijnen
    INTERNE_DEFINITIE = "interne_definitie"  # Intern vastgestelde definities
    EXTERNE_BRON = "externe_bron"            # Externe bronnen (websites, databases)
    ONBEKEND = "onbekend"                    # Type kon niet worden bepaald


class BronValiditeit(Enum):
    """Validiteitsstatus van juridische bronnen."""
    GELDIG = "geldig"              # Bron is actueel en rechtsgeldig
    VEROUDERD = "verouderd"        # Bron is vervangen door nieuwere versie
    INGETROKKEN = "ingetrokken"    # Bron is expliciet ingetrokken
    ONBEKEND = "onbekend"          # Validiteit kon niet worden vastgesteld


@dataclass
class BronReferentie:
    """Bron referentie informatie."""
    naam: str
    type: BronType
    url: Optional[str] = None
    artikel: Optional[str] = None
    datum: Optional[str] = None
    validiteit: BronValiditeit = BronValiditeit.ONBEKEND
    betrouwbaarheid: float = 0.0  # 0.0 - 1.0
    contextuele_relevantie: float = 0.0  # 0.0 - 1.0
    toegankelijkheid: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass 
class BronZoekResultaat:
    """Resultaat van bron zoekopdracht."""
    query: str
    gevonden_bronnen: List[BronReferentie]
    zoek_tijd: float
    totaal_gevonden: int
    gefilterd_op: List[str] = None
    aanbevelingen: List[str] = None
    
    def __post_init__(self):
        if self.gefilterd_op is None:
            self.gefilterd_op = []
        if self.aanbevelingen is None:
            self.aanbevelingen = []


class BronValidator:
    """Valideert en beoordeelt bronnen."""
    
    def __init__(self):
        self.bekende_wetten = self._laad_bekende_wetten()
        self.betrouwbare_domeinen = self._laad_betrouwbare_domeinen()
        
    def _laad_bekende_wetten(self) -> Set[str]:
        """Laad lijst van bekende wetten."""
        return {
            "Wetboek van Strafrecht",
            "Wetboek van Strafvordering", 
            "Burgerlijk Wetboek",
            "Wetboek van Burgerlijke Rechtsvordering",
            "Algemene wet bestuursrecht",
            "Wet op de rechtsbijstand",
            "Penitentiaire beginselenwet",
            "Wet op de identificatie",
            "Paspoortwet",
            "Wet basisregistratie personen",
            "Vreemdelingenwet",
            "Rijkswet op het Nederlanderschap"
        }
    
    def _laad_betrouwbare_domeinen(self) -> Set[str]:
        """Laad lijst van betrouwbare web domeinen."""
        return {
            "wetten.overheid.nl",
            "rechtspraak.nl",
            "rijksoverheid.nl",
            "europa.eu",
            "eur-lex.europa.eu",
            "government.nl",
            "justid.nl",
            "dji.nl"
        }
    
    def valideer_bron(self, bron: BronReferentie) -> BronReferentie:
        """
        Valideer en beoordeel een bron.
        
        Args:
            bron: BronReferentie om te valideren
            
        Returns:
            BronReferentie met bijgewerkte scores
        """
        # Betrouwbaarheid score
        bron.betrouwbaarheid = self._bereken_betrouwbaarheid(bron)
        
        # Validiteit check
        bron.validiteit = self._check_validiteit(bron)
        
        # Toegankelijkheid check
        bron.toegankelijkheid = self._check_toegankelijkheid(bron)
        
        return bron
    
    def _bereken_betrouwbaarheid(self, bron: BronReferentie) -> float:
        """Bereken betrouwbaarheidscore."""
        score = 0.5  # Base score
        
        # Type-gebaseerde score
        type_scores = {
            BronType.WETGEVING: 1.0,
            BronType.JURISPRUDENTIE: 0.9,
            BronType.BELEID: 0.8,
            BronType.LITERATUUR: 0.7,
            BronType.INTERNE_DEFINITIE: 0.6,
            BronType.EXTERNE_BRON: 0.4
        }
        score = type_scores.get(bron.type, 0.3)
        
        # URL-gebaseerde aanpassing
        if bron.url:
            for domein in self.betrouwbare_domeinen:
                if domein in bron.url:
                    score += 0.2
                    break
            else:
                score -= 0.1  # Onbekend domein
        
        # Naam-gebaseerde aanpassing
        if bron.naam in self.bekende_wetten:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_validiteit(self, bron: BronReferentie) -> BronValiditeit:
        """Check validiteit van bron."""
        # Eenvoudige implementatie - kan uitgebreid worden
        if bron.type == BronType.WETGEVING:
            return BronValiditeit.GELDIG  # Assume wetgeving is geldig
        elif bron.datum:
            # Check datum voor actualiteit
            try:
                bron_datum = datetime.fromisoformat(bron.datum.replace("-", ""))
                nu = datetime.now()
                verschil = (nu - bron_datum).days
                
                if verschil > 1825:  # 5 jaar
                    return BronValiditeit.VEROUDERD
                else:
                    return BronValiditeit.GELDIG
            except:
                pass
        
        return BronValiditeit.ONBEKEND
    
    def _check_toegankelijkheid(self, bron: BronReferentie) -> bool:
        """Check of bron toegankelijk is."""
        if not bron.url:
            return True  # Geen URL = not web-based
        
        # Check voor bekende toegankelijke domeinen
        for domein in self.betrouwbare_domeinen:
            if domein in bron.url:
                return True
        
        return False  # Conservatieve benadering


class BronHerkenner:
    """Herkent bronverwijzingen in tekst."""
    
    def __init__(self):
        self.patronen = self._laad_herkennings_patronen()
    
    def _laad_herkennings_patronen(self) -> List[Dict[str, Any]]:
        """Laad regex patronen voor bronherkenning."""
        return [
            {
                "naam": "wet_artikel",
                "pattern": re.compile(
                    r'(?P<wet>(?:Wetboek van|Wet op|Algemene wet)\s+[A-Za-z\s]+?)(?:,\s*)?artikel\s+(?P<artikel>\d+[a-z]?)',
                    re.IGNORECASE
                ),
                "type": BronType.WETGEVING
            },
            {
                "naam": "jurisprudentie",
                "pattern": re.compile(
                    r'(?P<instantie>HR|Hof|Rechtbank)\s+(?P<datum>\d{1,2}[-/]\d{1,2}[-/]\d{4}),?\s*(?P<nummer>[\w\./]+)',
                    re.IGNORECASE
                ),
                "type": BronType.JURISPRUDENTIE
            },
            {
                "naam": "beleidsdocument",
                "pattern": re.compile(
                    r'(?P<organisatie>DJI|OM|KMAR|Ministerie)\s+(?P<type>circulaire|richtlijn|handleiding|beleid)\s+(?P<nummer>[\w/.-]+)',
                    re.IGNORECASE
                ),
                "type": BronType.BELEID
            },
            {
                "naam": "url_referentie",
                "pattern": re.compile(
                    r'https?://(?P<domein>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/(?P<pad>[^\s<>"\']*)',
                    re.IGNORECASE
                ),
                "type": BronType.EXTERNE_BRON
            }
        ]
    
    def herken_bronnen_in_tekst(self, tekst: str) -> List[BronReferentie]:
        """
        Herken bronverwijzingen in tekst.
        
        Args:
            tekst: Tekst om te analyseren
            
        Returns:
            List van gevonden BronReferentie objecten
        """
        gevonden_bronnen = []
        
        for patroon_info in self.patronen:
            patroon = patroon_info["pattern"]
            bron_type = patroon_info["type"]
            
            for match in patroon.finditer(tekst):
                groups = match.groupdict()
                
                # Bepaal naam op basis van type
                if bron_type == BronType.WETGEVING:
                    naam = f"{groups.get('wet', 'Onbekende wet')} artikel {groups.get('artikel', '?')}"
                elif bron_type == BronType.JURISPRUDENTIE:
                    naam = f"{groups.get('instantie', 'Rechtspraak')} {groups.get('datum', '')} {groups.get('nummer', '')}"
                elif bron_type == BronType.BELEID:
                    naam = f"{groups.get('organisatie', '')} {groups.get('type', '')} {groups.get('nummer', '')}"
                elif bron_type == BronType.EXTERNE_BRON:
                    naam = f"Web: {groups.get('domein', '')}"
                else:
                    naam = match.group(0)
                
                bron = BronReferentie(
                    naam=naam.strip(),
                    type=bron_type,
                    url=match.group(0) if bron_type == BronType.EXTERNE_BRON else None,
                    artikel=groups.get('artikel'),
                    datum=groups.get('datum'),
                    metadata={
                        "match_text": match.group(0),
                        "match_start": match.start(),
                        "match_end": match.end(),
                        "groups": groups
                    }
                )
                
                gevonden_bronnen.append(bron)
        
        return gevonden_bronnen


class BronZoeker:
    """Zoekt bronnen in verschillende repositories."""
    
    def __init__(self):
        self.herkenner = BronHerkenner()
        self.validator = BronValidator()
    
    async def zoek_bronnen(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        max_resultaten: int = 10
    ) -> BronZoekResultaat:
        """
        Zoek bronnen voor een gegeven query.
        
        Args:
            query: Zoekterm
            context: Contextuele informatie
            max_resultaten: Maximum aantal resultaten
            
        Returns:
            BronZoekResultaat met gevonden bronnen
        """
        start_tijd = datetime.now()
        
        # Combineer verschillende zoekstrategie�n
        bronnen = []
        
        # 1. Herken bronnen in query tekst zelf
        tekstbronnen = self.herkenner.herken_bronnen_in_tekst(query)
        bronnen.extend(tekstbronnen)
        
        # 2. Zoek in interne bronnen database
        interne_bronnen = await self._zoek_interne_bronnen(query, context)
        bronnen.extend(interne_bronnen)
        
        # 3. Zoek in wettelijke databases
        wettelijke_bronnen = await self._zoek_wettelijke_bronnen(query, context)
        bronnen.extend(wettelijke_bronnen)
        
        # 4. Valideer en score alle bronnen
        for bron in bronnen:
            self.validator.valideer_bron(bron)
        
        # 5. Filter en sorteer
        gefilterde_bronnen = self._filter_en_sorteer_bronnen(bronnen, max_resultaten)
        
        eind_tijd = datetime.now()
        zoek_tijd = (eind_tijd - start_tijd).total_seconds()
        
        return BronZoekResultaat(
            query=query,
            gevonden_bronnen=gefilterde_bronnen,
            zoek_tijd=zoek_tijd,
            totaal_gevonden=len(bronnen),
            aanbevelingen=self._genereer_aanbevelingen(gefilterde_bronnen)
        )
    
    async def _zoek_interne_bronnen(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[BronReferentie]:
        """Zoek in interne definities database."""
        try:
            # Probeer database import
            from database.definitie_repository import get_definitie_repository
            
            repository = get_definitie_repository()
            resultaten = repository.search_definities(query=query, limit=5)
            
            bronnen = []
            for definitie in resultaten:
                bron = BronReferentie(
                    naam=f"Interne definitie: {definitie.begrip}",
                    type=BronType.INTERNE_DEFINITIE,
                    betrouwbaarheid=0.6,
                    contextuele_relevantie=0.8,
                    metadata={
                        "definitie_id": definitie.id,
                        "categorie": definitie.categorie,
                        "organisatorische_context": definitie.organisatorische_context
                    }
                )
                bronnen.append(bron)
            
            return bronnen
            
        except ImportError:
            logger.warning("Database repository niet beschikbaar voor bron lookup")
            return []
    
    async def _zoek_wettelijke_bronnen(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[BronReferentie]:
        """Zoek in wettelijke databases (placeholder)."""
        # Mock implementatie - kan uitgebreid worden met echte API calls
        wettelijke_termen = {
            "authenticatie": [
                BronReferentie(
                    "Wet op de identificatie artikel 1",
                    BronType.WETGEVING,
                    url="https://wetten.overheid.nl/BWBR0006297/",
                    artikel="1",
                    betrouwbaarheid=1.0
                )
            ],
            "verificatie": [
                BronReferentie(
                    "Paspoortwet artikel 2",
                    BronType.WETGEVING,
                    url="https://wetten.overheid.nl/BWBR0005212/",
                    artikel="2",
                    betrouwbaarheid=1.0
                )
            ],
            "identiteit": [
                BronReferentie(
                    "Wet basisregistratie personen artikel 1.1",
                    BronType.WETGEVING,
                    url="https://wetten.overheid.nl/BWBR0033715/",
                    artikel="1.1",
                    betrouwbaarheid=1.0
                )
            ]
        }
        
        query_lower = query.lower()
        gevonden_bronnen = []
        
        for term, bronnen in wettelijke_termen.items():
            if term in query_lower:
                gevonden_bronnen.extend(bronnen)
        
        return gevonden_bronnen
    
    def _filter_en_sorteer_bronnen(
        self, 
        bronnen: List[BronReferentie], 
        max_resultaten: int
    ) -> List[BronReferentie]:
        """Filter en sorteer bronnen op relevantie."""
        # Remove duplicates
        unique_bronnen = []
        seen_names = set()
        
        for bron in bronnen:
            if bron.naam not in seen_names:
                unique_bronnen.append(bron)
                seen_names.add(bron.naam)
        
        # Sorteer op betrouwbaarheid en relevantie
        sorted_bronnen = sorted(
            unique_bronnen,
            key=lambda b: (b.betrouwbaarheid + b.contextuele_relevantie) / 2,
            reverse=True
        )
        
        return sorted_bronnen[:max_resultaten]
    
    def _genereer_aanbevelingen(self, bronnen: List[BronReferentie]) -> List[str]:
        """Genereer aanbevelingen op basis van gevonden bronnen."""
        aanbevelingen = []
        
        if not bronnen:
            aanbevelingen.append("Geen bronnen gevonden. Probeer een bredere zoekopdracht.")
            return aanbevelingen
        
        # Analyse van brontypes
        type_counts = {}
        for bron in bronnen:
            type_counts[bron.type] = type_counts.get(bron.type, 0) + 1
        
        if BronType.WETGEVING in type_counts:
            aanbevelingen.append(f" {type_counts[BronType.WETGEVING]} wettelijke bron(nen) gevonden")
        
        if BronType.INTERNE_DEFINITIE in type_counts:
            aanbevelingen.append(f"= {type_counts[BronType.INTERNE_DEFINITIE]} interne definitie(s) beschikbaar")
        
        # Betrouwbaarheidsadvies
        hoge_betrouwbaarheid = [b for b in bronnen if b.betrouwbaarheid > 0.8]
        if hoge_betrouwbaarheid:
            aanbevelingen.append(f"P {len(hoge_betrouwbaarheid)} bronnen met hoge betrouwbaarheid")
        
        # Toegankelijkheidsadvies
        niet_toegankelijk = [b for b in bronnen if not b.toegankelijkheid]
        if niet_toegankelijk:
            aanbevelingen.append(f"� {len(niet_toegankelijk)} bronnen mogelijk niet direct toegankelijk")
        
        return aanbevelingen


# Convenience functions
async def zoek_bronnen_voor_begrip(
    begrip: str, 
    context: Optional[Dict[str, Any]] = None,
    max_resultaten: int = 5
) -> BronZoekResultaat:
    """
    Convenience functie voor bron lookup.
    
    Args:
        begrip: Begrip om bronnen voor te zoeken
        context: Contextuele informatie
        max_resultaten: Maximum aantal resultaten
        
    Returns:
        BronZoekResultaat met gevonden bronnen
    """
    zoeker = BronZoeker()
    return await zoeker.zoek_bronnen(begrip, context, max_resultaten)


def herken_bronnen_in_definitie(definitie: str) -> List[BronReferentie]:
    """
    Herken bronverwijzingen in definitie tekst.
    
    Args:
        definitie: Definitie tekst om te analyseren
        
    Returns:
        List van gevonden BronReferentie objecten
    """
    herkenner = BronHerkenner()
    bronnen = herkenner.herken_bronnen_in_tekst(definitie)
    
    # Valideer gevonden bronnen
    validator = BronValidator()
    for bron in bronnen:
        validator.valideer_bron(bron)
    
    return bronnen


async def valideer_definitie_bronnen(
    definitie: str,
    verwachte_bronnen: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Valideer bronnen in definitie.
    
    Args:
        definitie: Definitie tekst
        verwachte_bronnen: Lijst van verwachte bron namen
        
    Returns:
        Validatie resultaat dictionary
    """
    gevonden_bronnen = herken_bronnen_in_definitie(definitie)
    
    resultaat = {
        "definitie": definitie,
        "gevonden_bronnen": gevonden_bronnen,
        "aantal_bronnen": len(gevonden_bronnen),
        "gemiddelde_betrouwbaarheid": 0.0,
        "bevat_wettelijke_bronnen": False,
        "toegankelijke_bronnen": 0,
        "validatie_score": 0.0,
        "aanbevelingen": []
    }
    
    if gevonden_bronnen:
        # Bereken statistieken
        betrouwbaarheden = [b.betrouwbaarheid for b in gevonden_bronnen]
        resultaat["gemiddelde_betrouwbaarheid"] = sum(betrouwbaarheden) / len(betrouwbaarheden)
        
        resultaat["bevat_wettelijke_bronnen"] = any(
            b.type == BronType.WETGEVING for b in gevonden_bronnen
        )
        
        resultaat["toegankelijke_bronnen"] = sum(
            1 for b in gevonden_bronnen if b.toegankelijkheid
        )
        
        # Validatie score (0.0 - 1.0)
        score_factors = [
            resultaat["gemiddelde_betrouwbaarheid"],
            1.0 if resultaat["bevat_wettelijke_bronnen"] else 0.5,
            resultaat["toegankelijke_bronnen"] / len(gevonden_bronnen)
        ]
        resultaat["validatie_score"] = sum(score_factors) / len(score_factors)
        
        # Aanbevelingen
        if resultaat["validatie_score"] > 0.8:
            resultaat["aanbevelingen"].append(" Uitstekende bronverwijzingen")
        elif resultaat["validatie_score"] > 0.6:
            resultaat["aanbevelingen"].append(" Goede bronverwijzingen")
        else:
            resultaat["aanbevelingen"].append("� Bronverwijzingen kunnen verbeterd worden")
        
        if not resultaat["bevat_wettelijke_bronnen"]:
            resultaat["aanbevelingen"].append("=� Overweeg toevoegen van wettelijke bronnen")
    
    else:
        resultaat["aanbevelingen"].append("� Geen bronverwijzingen gevonden in definitie")
    
    return resultaat


if __name__ == "__main__":
    # Test de bron lookup functionaliteit
    import asyncio
    
    async def test_bron_lookup():
        print("🔍 Testing Bron Lookup System")
        print("=" * 40)
        
        # Test 1: Herken bronnen in tekst
        test_tekst = """
        Volgens artikel 1 van de Wet op de identificatie en conform HR 12-03-2020, ECLI:NL:HR:2020:123
        wordt authenticatie gedefinieerd. Zie ook DJI circulaire 2024/001 en 
        https://wetten.overheid.nl/BWBR0006297/
        """
        
        herkenner = BronHerkenner()
        gevonden_bronnen = herkenner.herken_bronnen_in_tekst(test_tekst)
        
        print(f"🔍 Gevonden {len(gevonden_bronnen)} bronnen in test tekst:")
        for bron in gevonden_bronnen:
            print(f"   - {bron.naam} ({bron.type.value})")
        
        # Test 2: Zoek bronnen
        zoeker = BronZoeker()
        zoek_resultaat = await zoeker.zoek_bronnen("authenticatie", max_resultaten=5)
        
        print(f"\n🔍 Zoekresultaat voor 'authenticatie':")
        print(f"   Zoektijd: {zoek_resultaat.zoek_tijd:.3f}s")
        print(f"   Gevonden: {len(zoek_resultaat.gevonden_bronnen)} van {zoek_resultaat.totaal_gevonden}")
        
        for bron in zoek_resultaat.gevonden_bronnen:
            print(f"   - {bron.naam} (betrouwbaarheid: {bron.betrouwbaarheid:.2f})")
        
        # Test 3: Valideer definitie bronnen
        test_definitie = "Authenticatie volgens artikel 1 Wet op de identificatie is het proces..."
        validatie = await valideer_definitie_bronnen(test_definitie)
        
        print(f"\n Definitie validatie:")
        print(f"   Score: {validatie['validatie_score']:.2f}")
        print(f"   Bronnen: {validatie['aantal_bronnen']}")
        print(f"   Aanbevelingen: {', '.join(validatie['aanbevelingen'])}")
    
    # Run test
    asyncio.run(test_bron_lookup())