"""
Toetsregel ESS-03: Instanties uniek onderscheidbaar (telbaarheid)

Deze module bevat de specifieke validatielogica voor ESS-03.
Controleert of een definitie criteria bevat voor unieke identificatie.
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ESS03Validator:
    """Validator voor ESS-03: Instanties uniek onderscheidbaar."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit ESS-03.json
        """
        self.config = config
        self.id = config.get('id', 'ESS-03')
        self.naam = config.get('naam', '')
        self.herkenbaar_patronen = config.get('herkenbaar_patronen', [])
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
        Valideer definitie volgens ESS-03 regel.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        # Check of het begrip telbaar is (simpele heuristiek)
        if not self._is_telbaar_begrip(begrip, context):
            return True, f"✔️ {self.id}: Niet van toepassing (niet-telbaar begrip)", 1.0
        
        # Zoek naar unieke identificatie criteria
        gevonden_criteria = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            if matches:
                gevonden_criteria.extend(matches)
        
        if gevonden_criteria:
            unieke_criteria = list(set(gevonden_criteria))
            melding = f"✔️ {self.id}: Unieke identificatie criteria gevonden: {', '.join(unieke_criteria)}"
            return True, melding, 1.0
        else:
            # Geavanceerdere check: zoek naar andere indicatoren
            if self._heeft_impliciete_identificatie(definitie):
                return True, f"✔️ {self.id}: Impliciete identificatie criteria aanwezig", 0.8
            else:
                melding = f"❌ {self.id}: {self.config.get('uitleg', 'Geen unieke identificatie criteria gevonden')}"
                return False, melding, 0.0
    
    def _is_telbaar_begrip(self, begrip: str, context: Optional[Dict] = None) -> bool:
        """
        Bepaal of een begrip telbaar is.
        
        Dit is een simpele heuristiek die uitgebreid kan worden.
        """
        # Niet-telbare indicatoren
        niet_telbaar = ['proces', 'methode', 'systeem', 'kwaliteit', 'eigenschap', 
                       'toestand', 'situatie', 'concept', 'principe']
        
        begrip_lower = begrip.lower()
        
        # Check context hints
        if context and context.get('categorie') in ['proces', 'eigenschap']:
            return False
        
        # Check niet-telbare patronen
        for indicator in niet_telbaar:
            if indicator in begrip_lower:
                return False
        
        # Default: beschouw als telbaar
        return True
    
    def _heeft_impliciete_identificatie(self, definitie: str) -> bool:
        """
        Check voor impliciete identificatie mogelijkheden.
        """
        impliciete_patronen = [
            r'\b(individueel|afzonderlijk|specifiek|eigen|uniek)\b',
            r'\b(geïdentificeerd|identificeerbaar|herkenbaar)\b',
            r'\b(onderscheiden|onderscheidbaar)\b'
        ]
        
        for pattern in impliciete_patronen:
            if re.search(pattern, definitie, re.IGNORECASE):
                return True
        
        return False
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        return [
            f"Voor telbare begrippen: vermeld unieke identificatie criteria zoals {', '.join(self.config.get('goede_voorbeelden', [])[:2])}",
            "Maak duidelijk hoe individuele instanties onderscheiden kunnen worden",
            "Overweeg het toevoegen van identificatienummers, codes of andere unieke kenmerken"
        ]


def create_validator(config_path: str = None) -> ESS03Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        ESS03Validator instantie
    """
    import json
    import os
    
    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'ESS-03.json')
    
    # Laad configuratie
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return ESS03Validator(config)


# Voor backward compatibility
def validate_ess03(definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Valideer volgens ESS-03 regel (backward compatible interface).
    """
    validator = create_validator()
    succes, melding, score = validator.validate(definitie, begrip, context)
    return succes, melding