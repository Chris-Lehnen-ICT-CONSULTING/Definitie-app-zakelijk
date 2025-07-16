"""
Toetsregel ARAI04SUB1
Automatisch gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging
from web_lookup import is_plurale_tantum

logger = logging.getLogger(__name__)

class ARAI04SUB1Validator:
    """Validator voor ARAI04SUB1."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit ARAI04SUB1.json
        """
        self.config = config
        self.id = config.get('id', 'ARAI04SUB1')
        self.naam = config.get('naam', '')
        self.uitleg = config.get('uitleg', '')
        self.prioriteit = config.get('prioriteit', 'midden')
    
    def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens ARAI04SUB1 regel.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt  
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        # Haal regel config op
        regel = self.config
        
        # Extract context parameters indien nodig
        if context:

        # Legacy implementatie
        try:
    patronen = regel.get("herkenbaar_patronen", [])
    modale_termen = set()
    for patroon in patronen:
        modale_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not modale_termen:
        if goed:
            return "✔️ ARAI04SUB1: geen modale werkwoorden gevonden, definitie komt overeen met goed voorbeeld"
        return "✔️ ARAI04SUB1: geen modale werkwoorden aangetroffen in de definitie"

    if fout:
        return f"❌ ARAI04SUB1: modale werkwoorden herkend ({', '.join(modale_termen)}), zoals in fout voorbeeld"
    return f"❌ ARAI04SUB1: modale werkwoorden herkend ({', '.join(modale_termen)}), kan verwarring veroorzaken"
        except Exception as e:
            logger.error(f"Fout in {self.id} validator: {e}")
            return False, f"⚠️ {self.id}: fout bij uitvoeren toetsregel", 0.0
        
        # Convert legacy return naar nieuwe format
        if isinstance(result, str):
            # Bepaal succes op basis van emoji
            succes = "✔️" in result or "✅" in result
            score = 1.0 if succes else 0.0
            if "🟡" in result:
                score = 0.5
            return succes, result, score
        
        # Fallback
        return False, f"⚠️ {self.id}: geen resultaat", 0.0
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []
        
        if self.uitleg:
            hints.append(self.uitleg)
            
        goede_voorbeelden = self.config.get('goede_voorbeelden', [])
        if goede_voorbeelden:
            hints.append(f"Volg dit voorbeeld: {goede_voorbeelden[0]}")
        
        return hints

def create_validator(config_path: str = None) -> ARAI04SUB1Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        ARAI04SUB1Validator instantie
    """
    import json
    import os
    
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'ARAI04SUB1.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return ARAI04SUB1Validator(config)
