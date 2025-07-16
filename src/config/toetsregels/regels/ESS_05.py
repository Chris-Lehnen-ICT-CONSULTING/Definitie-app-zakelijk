"""
Toetsregel ESS-05: Voldoende onderscheidend

Een definitie moet duidelijk maken wat het begrip uniek maakt ten opzichte van andere verwante begrippen.
Gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ESS05Validator:
    """Validator voor ESS-05: Voldoende onderscheidend."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit ESS-05.json
        """
        self.config = config
        self.id = config.get('id', 'ESS-05')
        self.naam = config.get('naam', 'Voldoende onderscheidend')
        self.uitleg = config.get('uitleg', '')
        self.herkenbaar_patronen = config.get('herkenbaar_patronen', [])
        self.goede_voorbeelden = config.get('goede_voorbeelden', [])
        self.foute_voorbeelden = config.get('foute_voorbeelden', [])
        self.prioriteit = config.get('prioriteit', 'hoog')
        
        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")
    
    def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens ESS-05 regel.
        
        Een definitie moet expliciet maken waarin het begrip zich onderscheidt
        van verwante begrippen in hetzelfde domein.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        d = definitie.lower().strip()
        
        # 1️⃣ Expliciete FOUT-voorbeelden afvangen
        for fout in self.foute_voorbeelden:
            if fout.lower() in d:
                return False, (
                    f"❌ {self.id}: definitie bevat niet-onderscheidende formulering "
                    f"(fout voorbeeld: '…{fout}…')"
                ), 0.0
        
        # 2️⃣ Expliciete GOED-voorbeelden direct honoreren
        for goed in self.goede_voorbeelden:
            if goed.lower() in d:
                return True, (
                    f"✔️ {self.id}: onderscheidende formulering aangetroffen "
                    "(volgens goed voorbeeld)"
                ), 1.0
        
        # 3️⃣ Patronen uit JSON op zoek naar sleutelwoorden
        gevonden = []
        for pattern in self.compiled_patterns:
            if pattern.search(definitie):
                gevonden.append(pattern.pattern)
        
        if gevonden:
            labels = ", ".join(sorted(set(gevonden)))
            return True, f"✔️ {self.id}: onderscheidende patroon(en) herkend ({labels})", 1.0
        
        # 4️⃣ Fallback: niets gevonden → definitie is onvoldoende onderscheidend
        return False, (
            f"❌ {self.id}: geen onderscheidende elementen gevonden; "
            "definitie maakt niet duidelijk waarin het begrip zich onderscheidt"
        ), 0.0
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []
        
        hints.append("Maak expliciet waarin het begrip zich onderscheidt van verwante begrippen")
        hints.append("Gebruik formuleringen zoals: 'in tegenstelling tot', 'verschilt van', 'specifiek voor'")
        hints.append("Vermeld unieke kenmerken of onderscheidende eigenschappen")
        hints.append("Geef aan wat dit begrip anders maakt dan soortgelijke begrippen")
        
        if self.goede_voorbeelden:
            hints.append(f"Voorbeeld van goede onderscheiding: {self.goede_voorbeelden[0]}")
        
        return hints


def create_validator(config_path: str = None) -> ESS05Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        ESS05Validator instantie
    """
    import json
    import os
    
    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'ESS-05.json')
    
    # Laad configuratie
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return ESS05Validator(config)