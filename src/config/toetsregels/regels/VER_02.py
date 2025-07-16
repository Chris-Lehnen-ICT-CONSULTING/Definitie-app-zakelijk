"""
Toetsregel VER-02: Geen tijdsgebonden formuleringen

Een definitie moet tijdloos zijn en geen verwijzingen bevatten naar 'nu', 'momenteel', etc.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VER02Validator:
    """Validator voor VER-02: Geen tijdsgebonden formuleringen."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit VER-02.json
        """
        self.config = config
        self.id = config.get('id', 'VER-02')
        self.naam = config.get('naam', 'Geen tijdsgebonden formuleringen')
        self.uitleg = config.get('uitleg', '')
        self.herkenbaar_patronen = config.get('herkenbaar_patronen', [])
        self.goede_voorbeelden = config.get('goede_voorbeelden', [])
        self.foute_voorbeelden = config.get('foute_voorbeelden', [])
        self.prioriteit = config.get('prioriteit', 'midden')
        
        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")
    
    def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens VER-02 regel.
        
        Controleert of de definitie tijdloos is geformuleerd zonder verwijzingen
        naar het heden zoals 'nu', 'momenteel', 'vandaag de dag'.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        tekst_lc = definitie.lower()
        
        # Check foute voorbeelden
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst_lc:
                return False, (
                    f"❌ {self.id}: tijdsgebonden formulering aangetroffen (fout voorbeeld)"
                ), 0.0
        
        # Zoek tijdsgebonden termen
        tijdsgebonden = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            tijdsgebonden.extend(matches)
        
        if tijdsgebonden:
            unieke = ", ".join(sorted(set(tijdsgebonden)))
            return False, (
                f"❌ {self.id}: tijdsgebonden termen gevonden: {unieke}"
            ), 0.0
        
        # Check goede voorbeelden
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                return True, (
                    f"✔️ {self.id}: tijdloze formulering (goed voorbeeld)"
                ), 1.0
        
        return True, f"✔️ {self.id}: definitie is tijdloos geformuleerd", 1.0
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []
        
        hints.append("Formuleer definities tijdloos")
        hints.append("Vermijd woorden zoals: nu, momenteel, vandaag de dag, tegenwoordig")
        hints.append("Gebruik geen verwijzingen naar het heden of verleden")
        hints.append("Maak de definitie geldig voor alle tijden")
        
        return hints


def create_validator(config_path: str = None) -> VER02Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        VER02Validator instantie
    """
    import json
    import os
    
    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'VER-02.json')
    
    # Laad configuratie
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return VER02Validator(config)