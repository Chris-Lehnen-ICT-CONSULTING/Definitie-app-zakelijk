"""
Definitie Lookup Module - Zoekt bestaande definities in verschillende bronnen.
Ondersteunt zoeken in interne database, externe bronnen en web repositories.
"""

import re  # Reguliere expressies voor patroon matching
import logging  # Logging faciliteiten voor debug en monitoring
import asyncio  # Asynchrone programmering voor parallelle web lookups
from typing import Dict, List, Any, Optional, Tuple, Set  # Type hints voor code documentatie
from dataclasses import dataclass, field  # Dataklassen voor gestructureerde definitie data
from enum import Enum  # Enumeraties voor status en context types
from datetime import datetime  # Datum en tijd functionaliteit voor timestamps
import json  # JSON verwerking voor data export/import
import os  # Operating system interface voor bestandstoegang
from pathlib import Path  # Object-georiÃ«nteerde pad manipulatie

logger = logging.getLogger(__name__)  # Logger instantie voor web lookup module


class DefinitieStatus(Enum):
    """Status van gevonden definities in externe bronnen."""
    ACTIEF = "actief"              # Definitie is actueel en actief in gebruik
    VEROUDERD = "verouderd"        # Definitie is vervangen door nieuwere versie
    CONCEPT = "concept"            # Definitie is nog in ontwikkeling
    INGETROKKEN = "ingetrokken"    # Definitie is niet meer geldig
    ONBEKEND = "onbekend"          # Status kon niet worden bepaald


class DefinitieContext(Enum):
    """Juridische context waarin definitie wordt gebruikt."""
    STRAFRECHT = "strafrecht"                        # Context van het strafrecht
    CIVIEL_RECHT = "civiel_recht"                    # Context van het burgerlijk recht
    BESTUURSRECHT = "bestuursrecht"                  # Context van het bestuursrecht
    EUROPEES_RECHT = "europees_recht"                # Context van Europese wetgeving
    INTERNATIONAAL_RECHT = "internationaal_recht"    # Context van internationaal recht
    ORGANISATIE_SPECIFIEK = "organisatie_specifiek"  # Specifiek voor een organisatie
    ALGEMEEN = "algemeen"                            # Algemene context zonder specificatie


@dataclass
class GevondenDefinitie:
    """Een gevonden definitie uit externe of interne bron."""
    begrip: str
    definitie: str
    bron: str
    status: DefinitieStatus = DefinitieStatus.ONBEKEND
    context: DefinitieContext = DefinitieContext.ALGEMEEN
    url: Optional[str] = None
    datum: Optional[str] = None
    organisatie: Optional[str] = None
    rechtsgebied: Optional[str] = None
    betrouwbaarheid: float = 0.0  # 0.0 - 1.0
    relevantie: float = 0.0  # 0.0 - 1.0
    gelijkenis_score: float = 0.0  # 0.0 - 1.0 voor duplicaat detectie
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_display_name(self) -> str:
        """Krijg weergave naam voor de definitie."""
        prefix = ""
        if self.organisatie:
            prefix = f"[{self.organisatie}] "
        elif self.context != DefinitieContext.ALGEMEEN:
            prefix = f"[{self.context.value}] "
        
        return f"{prefix}{self.begrip}"


@dataclass
class DefinitieZoekResultaat:
    """Resultaat van definitie zoekopdracht."""
    query: str
    gevonden_definities: List[GevondenDefinitie]
    zoek_tijd: float
    totaal_gevonden: int
    exacte_matches: List[GevondenDefinitie] = field(default_factory=list)
    gedeeltelijke_matches: List[GevondenDefinitie] = field(default_factory=list)
    gerelateerde_begrippen: List[str] = field(default_factory=list)
    suggesties: List[str] = field(default_factory=list)
    duplicaat_analyse: Dict[str, Any] = field(default_factory=dict)


class DefinitieGelijkenisAnalyzer:
    """Analyseert gelijkenis tussen definities voor duplicaat detectie."""
    
    def __init__(self):
        self.stop_woorden = self._laad_stop_woorden()
    
    def _laad_stop_woorden(self) -> Set[str]:
        """Laad Nederlandse stop woorden."""
        return {
            "de", "het", "een", "en", "van", "in", "op", "is", "zijn", "wordt", "worden",
            "door", "met", "voor", "als", "dat", "die", "deze", "aan", "bij", "tot",
            "om", "onder", "over", "uit", "te", "naar", "kan", "moet", "zal", "heeft",
            "hebben", "waar", "wat", "wie", "hoe", "waarom", "wanneer", "welke"
        }
    
    def bereken_gelijkenis(self, definitie1: str, definitie2: str) -> float:
        """
        Bereken gelijkenis score tussen twee definities.
        
        Args:
            definitie1: Eerste definitie
            definitie2: Tweede definitie
            
        Returns:
            Gelijkenis score (0.0 - 1.0)
        """
        # Normaliseer teksten
        norm1 = self._normaliseer_tekst(definitie1)
        norm2 = self._normaliseer_tekst(definitie2)
        
        # Bereken verschillende gelijkenis metrics
        woord_gelijkenis = self._bereken_woord_gelijkenis(norm1, norm2)
        structuur_gelijkenis = self._bereken_structuur_gelijkenis(norm1, norm2)
        semantische_gelijkenis = self._bereken_semantische_gelijkenis(norm1, norm2)
        
        # Gewogen gemiddelde
        totaal_score = (
            woord_gelijkenis * 0.4 +
            structuur_gelijkenis * 0.3 +
            semantische_gelijkenis * 0.3
        )
        
        return min(1.0, max(0.0, totaal_score))
    
    def _normaliseer_tekst(self, tekst: str) -> List[str]:
        """Normaliseer tekst voor analyse."""
        # Lowercase en schoon maken
        tekst = re.sub(r'[^\w\s]', ' ', tekst.lower())
        woorden = tekst.split()
        
        # Verwijder stop woorden
        gefilterde_woorden = [w for w in woorden if w not in self.stop_woorden and len(w) > 2]
        
        return gefilterde_woorden
    
    def _bereken_woord_gelijkenis(self, woorden1: List[str], woorden2: List[str]) -> float:
        """Bereken woord overlap gelijkenis."""
        if not woorden1 or not woorden2:
            return 0.0
        
        set1 = set(woorden1)
        set2 = set(woorden2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _bereken_structuur_gelijkenis(self, woorden1: List[str], woorden2: List[str]) -> float:
        """Bereken structurele gelijkenis."""
        if not woorden1 or not woorden2:
            return 0.0
        
        # Lengte gelijkenis
        lengte_ratio = min(len(woorden1), len(woorden2)) / max(len(woorden1), len(woorden2))
        
        # Begin/eind gelijkenis
        begin_match = 0
        for i in range(min(3, len(woorden1), len(woorden2))):
            if woorden1[i] == woorden2[i]:
                begin_match += 1
        
        begin_score = begin_match / 3
        
        return (lengte_ratio + begin_score) / 2
    
    def _bereken_semantische_gelijkenis(self, woorden1: List[str], woorden2: List[str]) -> float:
        """Bereken semantische gelijkenis (eenvoudige implementatie)."""
        # Eenvoudige implementatie gebaseerd op synoniemen en gerelateerde termen
        juridische_clusters = {
            "verificatie": {"verificatie", "controle", "toetsing", "validatie", "check"},
            "authenticatie": {"authenticatie", "identiteitsvaststelling", "legitimatie"},
            "identiteit": {"identiteit", "persoon", "individu", "subject"},
            "proces": {"proces", "procedure", "activiteit", "handeling", "actie"},
            "document": {"document", "bewijs", "stuk", "papier", "formulier"}
        }
        
        # Find clusters voor beide woordenlijsten
        clusters1 = self._vind_semantische_clusters(woorden1, juridische_clusters)
        clusters2 = self._vind_semantische_clusters(woorden2, juridische_clusters)
        
        # Bereken cluster overlap
        if not clusters1 or not clusters2:
            return 0.0
        
        gemeenschappelijke_clusters = len(clusters1 & clusters2)
        totale_clusters = len(clusters1 | clusters2)
        
        return gemeenschappelijke_clusters / totale_clusters if totale_clusters > 0 else 0.0
    
    def _vind_semantische_clusters(self, woorden: List[str], clusters: Dict[str, Set[str]]) -> Set[str]:
        """Vind semantische clusters in woordenlijst."""
        gevonden_clusters = set()
        
        for cluster_naam, cluster_woorden in clusters.items():
            if any(woord in cluster_woorden for woord in woorden):
                gevonden_clusters.add(cluster_naam)
        
        return gevonden_clusters


class DefinitieZoeker:
    """Hoofdklasse voor het zoeken van definities."""
    
    def __init__(self):
        self.gelijkenis_analyzer = DefinitieGelijkenisAnalyzer()
        self.cache = {}
        self.cache_ttl = 3600  # 1 uur
    
    async def zoek_definities(
        self, 
        begrip: str, 
        context: Optional[Dict[str, Any]] = None,
        zoek_opties: Optional[Dict[str, Any]] = None
    ) -> DefinitieZoekResultaat:
        """
        Zoek definities voor een begrip.
        
        Args:
            begrip: Begrip om te zoeken
            context: Contextuele informatie
            zoek_opties: Zoek configuratie
            
        Returns:
            DefinitieZoekResultaat met gevonden definities
        """
        start_tijd = datetime.now()
        
        # Default opties
        opties = {
            "zoek_exacte_matches": True,
            "zoek_gedeeltelijke_matches": True,
            "zoek_gerelateerde": True,
            "max_resultaten": 20,
            "min_gelijkenis": 0.3,
            "include_internal": True,
            "include_external": True
        }
        if zoek_opties:
            opties.update(zoek_opties)
        
        # Check cache
        cache_key = f"{begrip}_{hash(str(context))}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if (datetime.now() - cache_entry["timestamp"]).seconds < self.cache_ttl:
                return cache_entry["result"]
        
        # Zoek in verschillende bronnen
        alle_definities = []
        
        if opties["include_internal"]:
            interne_definities = await self._zoek_interne_definities(begrip, context)
            alle_definities.extend(interne_definities)
        
        if opties["include_external"]:
            externe_definities = await self._zoek_externe_definities(begrip, context)
            alle_definities.extend(externe_definities)
        
        # Analyseer en categoriseer resultaten
        resultaat = self._analyseer_zoekresultaten(
            begrip, alle_definities, opties
        )
        
        # Bereken zoektijd
        eind_tijd = datetime.now()
        resultaat.zoek_tijd = (eind_tijd - start_tijd).total_seconds()
        
        # Cache resultaat
        self.cache[cache_key] = {
            "result": resultaat,
            "timestamp": datetime.now()
        }
        
        return resultaat
    
    async def _zoek_interne_definities(
        self, 
        begrip: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[GevondenDefinitie]:
        """Zoek in interne definities database."""
        try:
            from database.definitie_repository import get_definitie_repository
            
            repository = get_definitie_repository()
            
            # Exacte match
            exacte_resultaten = repository.search_definities(query=begrip, limit=10)
            
            # Fuzzy search
            fuzzy_resultaten = repository.search_definities(
                query=begrip, 
                fuzzy=True, 
                limit=10
            )
            
            # Combineer resultaten
            alle_resultaten = list(exacte_resultaten) + list(fuzzy_resultaten)
            
            # Converteer naar GevondenDefinitie
            gevonden_definities = []
            for definitie in alle_resultaten:
                gevonden_def = GevondenDefinitie(
                    begrip=definitie.begrip,
                    definitie=definitie.definitie,
                    bron=f"Interne Database (ID: {definitie.id})",
                    status=self._map_definitie_status(definitie.status),
                    organisatie=definitie.organisatorische_context,
                    rechtsgebied=definitie.juridische_context,
                    betrouwbaarheid=0.9,  # Hoge betrouwbaarheid voor interne definities
                    metadata={
                        "id": definitie.id,
                        "version": definitie.version_number,
                        "created_at": definitie.created_at.isoformat() if definitie.created_at else None,
                        "validation_score": definitie.validation_score
                    }
                )
                
                # Bereken relevantie
                gevonden_def.relevantie = self._bereken_relevantie(begrip, gevonden_def)
                
                gevonden_definities.append(gevonden_def)
            
            return gevonden_definities
            
        except ImportError:
            logger.warning("Database repository niet beschikbaar voor definitie lookup")
            return []
        except Exception as e:
            logger.error(f"Fout bij zoeken interne definities: {e}")
            return []
    
    async def _zoek_externe_definities(
        self, 
        begrip: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[GevondenDefinitie]:
        """Zoek in externe bronnen."""
        externe_definities = []
        
        # Mock externe bronnen - kan uitgebreid worden met echte API calls
        juridische_definities = self._laad_juridische_definities()
        
        begrip_lower = begrip.lower()
        
        for extern_begrip, definitie_info in juridische_definities.items():
            if begrip_lower in extern_begrip.lower() or extern_begrip.lower() in begrip_lower:
                gevonden_def = GevondenDefinitie(
                    begrip=extern_begrip,
                    definitie=definitie_info["definitie"],
                    bron=definitie_info["bron"],
                    url=definitie_info.get("url"),
                    rechtsgebied=definitie_info.get("rechtsgebied"),
                    betrouwbaarheid=definitie_info.get("betrouwbaarheid", 0.7),
                    context=self._bepaal_context(definitie_info.get("rechtsgebied", "")),
                    metadata=definitie_info.get("metadata", {})
                )
                
                gevonden_def.relevantie = self._bereken_relevantie(begrip, gevonden_def)
                externe_definities.append(gevonden_def)
        
        return externe_definities
    
    def _laad_juridische_definities(self) -> Dict[str, Dict[str, Any]]:
        """Laad externe juridische definities (mock data)."""
        return {
            "authenticatie": {
                "definitie": "Het proces waarbij de identiteit van een persoon wordt vastgesteld en geverifieerd aan de hand van door die persoon verstrekte identificerende gegevens.",
                "bron": "Besluit digitale overheid",
                "url": "https://wetten.overheid.nl/BWBR0040826/",
                "rechtsgebied": "Bestuursrecht",
                "betrouwbaarheid": 0.95,
                "metadata": {"type": "wettelijke_definitie", "jaar": "2018"}
            },
            "verificatie": {
                "definitie": "De handeling waarbij wordt nagegaan of verstrekte gegevens juist en volledig zijn door vergelijking met authentieke gegevens.",
                "bron": "Wet basisregistratie personen",
                "url": "https://wetten.overheid.nl/BWBR0033715/",
                "rechtsgebied": "Bestuursrecht", 
                "betrouwbaarheid": 0.95,
                "metadata": {"type": "wettelijke_definitie", "jaar": "2014"}
            },
            "identiteitsvaststelling": {
                "definitie": "Het proces waarbij de identiteit van een persoon wordt vastgesteld door middel van controle van een identiteitsdocument en verificatie van biometrische gegevens.",
                "bron": "Wet op de identificatie",
                "url": "https://wetten.overheid.nl/BWBR0006297/",
                "rechtsgebied": "Strafrecht",
                "betrouwbaarheid": 0.95,
                "metadata": {"type": "wettelijke_definitie", "jaar": "1994"}
            },
            "identiteitsbewijs": {
                "definitie": "Een document als bedoeld in artikel 1 van de Paspoortwet, een Nederlandse identiteitskaart of een ander bij algemene maatregel van bestuur aangewezen document.",
                "bron": "Wet op de identificatie artikel 1",
                "url": "https://wetten.overheid.nl/BWBR0006297/2019-07-01#Artikel1",
                "rechtsgebied": "Strafrecht",
                "betrouwbaarheid": 1.0,
                "metadata": {"type": "wettelijke_definitie", "artikel": "1"}
            },
            "biometrisch gegeven": {
                "definitie": "Een fysieke of gedragsmatige eigenschap van een natuurlijk persoon op grond waarvan de identiteit van die persoon kan worden vastgesteld.",
                "bron": "Algemene verordening gegevensbescherming",
                "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                "rechtsgebied": "Europees recht",
                "betrouwbaarheid": 1.0,
                "metadata": {"type": "europese_definitie", "artikel": "4"}
            }
        }
    
    def _map_definitie_status(self, status: str) -> DefinitieStatus:
        """Map database status naar DefinitieStatus enum."""
        mapping = {
            "draft": DefinitieStatus.CONCEPT,
            "review": DefinitieStatus.CONCEPT,
            "established": DefinitieStatus.ACTIEF,
            "archived": DefinitieStatus.INGETROKKEN
        }
        return mapping.get(status, DefinitieStatus.ONBEKEND)
    
    def _bepaal_context(self, rechtsgebied: str) -> DefinitieContext:
        """Bepaal context op basis van rechtsgebied."""
        mapping = {
            "strafrecht": DefinitieContext.STRAFRECHT,
            "civiel recht": DefinitieContext.CIVIEL_RECHT,
            "bestuursrecht": DefinitieContext.BESTUURSRECHT,
            "europees recht": DefinitieContext.EUROPEES_RECHT,
            "internationaal recht": DefinitieContext.INTERNATIONAAL_RECHT
        }
        return mapping.get(rechtsgebied.lower(), DefinitieContext.ALGEMEEN)
    
    def _bereken_relevantie(self, query: str, definitie: GevondenDefinitie) -> float:
        """Bereken relevantie score voor definitie."""
        query_lower = query.lower()
        begrip_lower = definitie.begrip.lower()
        
        # Exacte match
        if query_lower == begrip_lower:
            return 1.0
        
        # Begrip bevat query
        if query_lower in begrip_lower:
            return 0.8
        
        # Query bevat begrip
        if begrip_lower in query_lower:
            return 0.7
        
        # Woord overlap
        query_woorden = set(query_lower.split())
        begrip_woorden = set(begrip_lower.split())
        overlap = len(query_woorden & begrip_woorden)
        total = len(query_woorden | begrip_woorden)
        
        if total > 0:
            return 0.5 + (overlap / total) * 0.3
        
        return 0.3
    
    def _analyseer_zoekresultaten(
        self, 
        query: str, 
        alle_definities: List[GevondenDefinitie],
        opties: Dict[str, Any]
    ) -> DefinitieZoekResultaat:
        """Analyseer en categoriseer zoekresultaten."""
        
        # Remove duplicates en sorteer
        unique_definities = self._remove_duplicates(alle_definities)
        
        # Filter op minimale relevantie
        gefilterde_definities = [
            d for d in unique_definities 
            if d.relevantie >= opties.get("min_gelijkenis", 0.3)
        ]
        
        # Sorteer op relevantie en betrouwbaarheid
        gesorteerde_definities = sorted(
            gefilterde_definities,
            key=lambda d: (d.relevantie + d.betrouwbaarheid) / 2,
            reverse=True
        )
        
        # Beperk aantal resultaten
        max_resultaten = opties.get("max_resultaten", 20)
        top_definities = gesorteerde_definities[:max_resultaten]
        
        # Categoriseer resultaten
        exacte_matches = [d for d in top_definities if d.relevantie >= 0.9]
        gedeeltelijke_matches = [d for d in top_definities if 0.5 <= d.relevantie < 0.9]
        
        # Zoek gerelateerde begrippen
        gerelateerde_begrippen = self._vind_gerelateerde_begrippen(query, alle_definities)
        
        # Genereer suggesties
        suggesties = self._genereer_zoek_suggesties(query, top_definities)
        
        # Duplicaat analyse
        duplicaat_analyse = self._analyseer_duplicaten(top_definities)
        
        return DefinitieZoekResultaat(
            query=query,
            gevonden_definities=top_definities,
            zoek_tijd=0.0,  # Wordt later ingevuld
            totaal_gevonden=len(alle_definities),
            exacte_matches=exacte_matches,
            gedeeltelijke_matches=gedeeltelijke_matches,
            gerelateerde_begrippen=gerelateerde_begrippen,
            suggesties=suggesties,
            duplicaat_analyse=duplicaat_analyse
        )
    
    def _remove_duplicates(self, definities: List[GevondenDefinitie]) -> List[GevondenDefinitie]:
        """Verwijder duplicaten op basis van begrip en bron."""
        seen = set()
        unique_definities = []
        
        for definitie in definities:
            key = (definitie.begrip.lower(), definitie.bron)
            if key not in seen:
                seen.add(key)
                unique_definities.append(definitie)
        
        return unique_definities
    
    def _vind_gerelateerde_begrippen(
        self, 
        query: str, 
        alle_definities: List[GevondenDefinitie]
    ) -> List[str]:
        """Vind gerelateerde begrippen."""
        gerelateerde = set()
        query_woorden = set(query.lower().split())
        
        for definitie in alle_definities:
            begrip_woorden = set(definitie.begrip.lower().split())
            
            # Als er overlap is maar het is geen exacte match
            if (query_woorden & begrip_woorden and 
                definitie.begrip.lower() != query.lower()):
                gerelateerde.add(definitie.begrip)
        
        return sorted(list(gerelateerde))[:10]  # Top 10
    
    def _genereer_zoek_suggesties(
        self, 
        query: str, 
        top_definities: List[GevondenDefinitie]
    ) -> List[str]:
        """Genereer zoek suggesties."""
        suggesties = []
        
        if not top_definities:
            suggesties.append(f"Probeer een bredere zoekterm dan '{query}'")
            suggesties.append("Controleer spelling en probeer synoniemen")
            return suggesties
        
        exacte_matches = [d for d in top_definities if d.relevantie >= 0.9]
        if exacte_matches:
            suggesties.append(f" {len(exacte_matches)} exacte matches gevonden")
        
        externe_bronnen = [d for d in top_definities if "Interne Database" not in d.bron]
        if externe_bronnen:
            suggesties.append(f"= {len(externe_bronnen)} externe bron(nen) beschikbaar")
        
        hoge_betrouwbaarheid = [d for d in top_definities if d.betrouwbaarheid >= 0.9]
        if hoge_betrouwbaarheid:
            suggesties.append(f"P {len(hoge_betrouwbaarheid)} definities met hoge betrouwbaarheid")
        
        return suggesties
    
    def _analyseer_duplicaten(self, definities: List[GevondenDefinitie]) -> Dict[str, Any]:
        """Analyseer mogelijke duplicaten."""
        duplicaten = []
        
        for i, def1 in enumerate(definities):
            for j, def2 in enumerate(definities[i+1:], i+1):
                if def1.begrip.lower() == def2.begrip.lower():
                    gelijkenis = self.gelijkenis_analyzer.bereken_gelijkenis(
                        def1.definitie, def2.definitie
                    )
                    
                    if gelijkenis >= 0.7:  # Hoge gelijkenis threshold
                        duplicaten.append({
                            "definitie1": def1.get_display_name(),
                            "definitie2": def2.get_display_name(),
                            "gelijkenis": gelijkenis,
                            "aanbeveling": "Mogelijk duplicaat - vergelijk bronnen"
                        })
        
        return {
            "gevonden_duplicaten": len(duplicaten),
            "duplicaten": duplicaten,
            "threshold": 0.7
        }


# Convenience functions
async def zoek_definitie(
    begrip: str,
    context: Optional[Dict[str, Any]] = None,
    max_resultaten: int = 10
) -> DefinitieZoekResultaat:
    """
    Convenience functie voor definitie lookup.
    
    Args:
        begrip: Begrip om te zoeken
        context: Contextuele informatie
        max_resultaten: Maximum aantal resultaten
        
    Returns:
        DefinitieZoekResultaat met gevonden definities
    """
    zoeker = DefinitieZoeker()
    opties = {"max_resultaten": max_resultaten}
    return await zoeker.zoek_definities(begrip, context, opties)


async def detecteer_duplicaten(
    begrip: str,
    definitie: str,
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Detecteer mogelijke duplicaten voor een gegeven definitie.
    
    Args:
        begrip: Begrip van de definitie
        definitie: Definitie tekst
        threshold: Gelijkenis threshold voor duplicaat detectie
        
    Returns:
        Dictionary met duplicaat analyse
    """
    zoeker = DefinitieZoeker()
    zoek_resultaat = await zoeker.zoek_definities(begrip)
    
    analyzer = DefinitieGelijkenisAnalyzer()
    mogelijke_duplicaten = []
    
    for gevonden_def in zoek_resultaat.gevonden_definities:
        gelijkenis = analyzer.bereken_gelijkenis(definitie, gevonden_def.definitie)
        
        if gelijkenis >= threshold:
            mogelijke_duplicaten.append({
                "begrip": gevonden_def.begrip,
                "definitie": gevonden_def.definitie,
                "bron": gevonden_def.bron,
                "gelijkenis": gelijkenis,
                "betrouwbaarheid": gevonden_def.betrouwbaarheid
            })
    
    # Sorteer op gelijkenis
    mogelijke_duplicaten.sort(key=lambda x: x["gelijkenis"], reverse=True)
    
    return {
        "input_begrip": begrip,
        "input_definitie": definitie,
        "threshold": threshold,
        "mogelijke_duplicaten": mogelijke_duplicaten,
        "duplicaat_gevonden": len(mogelijke_duplicaten) > 0,
        "aanbeveling": (
            "Mogelijke duplicaten gevonden - controleer bestaande definities"
            if mogelijke_duplicaten
            else "Geen duplicaten gevonden"
        )
    }


if __name__ == "__main__":
    # Test de definitie lookup functionaliteit
    import asyncio
    
    async def test_definitie_lookup():
        print("ð Testing Definitie Lookup System")
        print("=" * 40)
        
        # Test 1: Zoek definities
        zoek_resultaat = await zoek_definitie("authenticatie", max_resultaten=5)
        
        print(f"ð Zoekresultaat voor 'authenticatie':")
        print(f"   Zoektijd: {zoek_resultaat.zoek_tijd:.3f}s")
        print(f"   Gevonden: {len(zoek_resultaat.gevonden_definities)} van {zoek_resultaat.totaal_gevonden}")
        print(f"   Exacte matches: {len(zoek_resultaat.exacte_matches)}")
        
        for definitie in zoek_resultaat.gevonden_definities:
            print(f"   - {definitie.get_display_name()}")
            print(f"     Relevantie: {definitie.relevantie:.2f}, Betrouwbaarheid: {definitie.betrouwbaarheid:.2f}")
            print(f"     {definitie.definitie[:80]}...")
        
        # Test 2: Duplicaat detectie
        test_definitie = "Het proces van identiteitsvaststelling door verificatie van gegevens"
        duplicaat_resultaat = await detecteer_duplicaten("authenticatie", test_definitie)
        
        print(f"\nð Duplicaat analyse:")
        print(f"   Duplicaten gevonden: {duplicaat_resultaat['duplicaat_gevonden']}")
        print(f"   Aantal mogelijke duplicaten: {len(duplicaat_resultaat['mogelijke_duplicaten'])}")
        print(f"   Aanbeveling: {duplicaat_resultaat['aanbeveling']}")
        
        if duplicaat_resultaat['mogelijke_duplicaten']:
            for dup in duplicaat_resultaat['mogelijke_duplicaten'][:3]:
                print(f"     - {dup['begrip']} (gelijkenis: {dup['gelijkenis']:.2f})")
        
        # Test 3: Gelijkenis analyse
        analyzer = DefinitieGelijkenisAnalyzer()
        def1 = "Het proces waarbij de identiteit wordt vastgesteld"
        def2 = "Procedure voor vaststelling van een persoon zijn identiteit"
        
        gelijkenis = analyzer.bereken_gelijkenis(def1, def2)
        print(f"\n=ï¿½ Gelijkenis analyse:")
        print(f"   Definitie 1: {def1}")
        print(f"   Definitie 2: {def2}")
        print(f"   Gelijkenis score: {gelijkenis:.3f}")
    
    # Run test
    asyncio.run(test_definitie_lookup())