"""
Toetsregel SAM-02: Geen vage kwantoren

Vermijd het gebruik van vage kwantoren zoals 'enkele', 'meerdere', 'veel', etc.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SAM02Validator:
    """Validator voor SAM-02: Geen vage kwantoren."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit SAM-02.json
        """
        self.config = config
        self.id = config.get('id', 'SAM-02')
        self.naam = config.get('naam', 'Geen vage kwantoren')
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
        Valideer definitie volgens SAM-02 regel.
        
        Controleert op vage kwantoren die de definitie onduidelijk maken.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        tekst_lc = definitie.lower()
        
        # Check expliciete voorbeelden
        for fout in self.foute_voorbeelden:
            if fout.lower() in tekst_lc:
                return False, f"❌ {self.id}: vage kwantoren aangetroffen (fout voorbeeld)", 0.0
        
        for goed in self.goede_voorbeelden:
            if goed.lower() in tekst_lc:
                return True, f"✔️ {self.id}: concrete aantallen gebruikt (goed voorbeeld)", 1.0
        
        # Zoek vage kwantoren
        gevonden = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            gevonden.extend(matches)
        
        if gevonden:
            unieke = ", ".join(sorted(set(gevonden)))
            return False, f"❌ {self.id}: vage kwantoren aangetroffen: {unieke}", 0.0
        
        return True, f"✔️ {self.id}: geen vage kwantoren aangetroffen", 1.0
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []
        
        hints.append("Gebruik concrete aantallen in plaats van vage termen")
        hints.append("Vermijd woorden zoals: enkele, meerdere, veel, weinig")
        hints.append("Gebruik specifieke getallen of bereiken: 2, 3-5, minimaal 10")
        hints.append("Als exacte aantallen niet mogelijk zijn, gebruik dan 'één of meer'")
        
        return hints


def create_validator(config_path: str = None) -> SAM02Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        SAM02Validator instantie
    """
    import json
    import os
    
    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'SAM-02.json')
    
    # Laad configuratie
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return SAM02Validator(config)