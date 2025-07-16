#!/usr/bin/env python3
"""
Script om een nieuwe toetsregel module te maken.

Gebruik: python create_regel_module.py REGEL-ID "Regel naam" "Uitleg"
Voorbeeld: python create_regel_module.py TEST-01 "Test regel" "Dit is een test regel"
"""

import sys
import json
import os
from pathlib import Path


PYTHON_TEMPLATE = '''"""
Toetsregel {regel_id}: {naam}

{uitleg}
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class {class_name}Validator:
    """Validator voor {regel_id}: {naam}."""
    
    def __init__(self, config: Dict):
        """
        Initialiseer validator met configuratie uit JSON.
        
        Args:
            config: Dictionary met configuratie uit {regel_id}.json
        """
        self.config = config
        self.id = config.get('id', '{regel_id}')
        self.naam = config.get('naam', '')
        self.uitleg = config.get('uitleg', '')
        self.herkenbaar_patronen = config.get('herkenbaar_patronen', [])
        self.prioriteit = config.get('prioriteit', 'midden')
        
        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {{self.id}}: {{pattern}} - {{e}}")
    
    def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Valideer definitie volgens {regel_id} regel.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie
            
        Returns:
            Tuple van (succes, melding, score)
        """
        # TODO: Implementeer specifieke validatie logica voor {regel_id}
        
        # Voorbeeld: check patronen
        for pattern in self.compiled_patterns:
            if pattern.search(definitie):
                return True, f"✔️ {{self.id}}: {{self.naam}} - Patroon gevonden", 1.0
        
        return False, f"❌ {{self.id}}: {{self.uitleg}}", 0.0
    
    def get_generation_hints(self) -> List[str]:
        """
        Geef hints voor definitie generatie.
        
        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []
        
        # Voeg hints toe op basis van de regel
        if self.config.get('goede_voorbeelden'):
            hints.append(f"Volg deze voorbeelden: {{', '.join(self.config['goede_voorbeelden'][:2])}}")
        
        hints.append(self.uitleg)
        
        return hints


def create_validator(config_path: str = None) -> {class_name}Validator:
    """
    Factory functie om validator te maken.
    
    Args:
        config_path: Optioneel pad naar configuratie bestand
        
    Returns:
        {class_name}Validator instantie
    """
    import json
    import os
    
    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '{regel_id}.json')
    
    # Laad configuratie
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return {class_name}Validator(config)
'''

JSON_TEMPLATE = {
    "id": "",
    "naam": "",
    "uitleg": "",
    "toelichting": "",
    "toetsvraag": "",
    "herkenbaar_patronen": [],
    "goede_voorbeelden": [],
    "foute_voorbeelden": [],
    "prioriteit": "midden",
    "aanbeveling": "aanbevolen",
    "geldigheid": "algemeen",
    "status": "concept",
    "type": "algemeen",
    "thema": "",
    "brondocument": "",
    "relatie": []
}


def create_regel_module(regel_id: str, naam: str, uitleg: str):
    """
    Maak een nieuwe toetsregel module.
    
    Args:
        regel_id: ID van de regel (bijv. 'TEST-01')
        naam: Naam van de regel
        uitleg: Uitleg van de regel
    """
    # Bepaal paden
    regels_dir = Path(__file__).parent / "regels"
    json_path = regels_dir / f"{regel_id}.json"
    
    # Python module naam (TEST-01 -> TEST_01)
    module_name = regel_id.replace('-', '_')
    py_path = regels_dir / f"{module_name}.py"
    
    # Class naam (TEST_01 -> TEST01)
    class_name = module_name.replace('_', '')
    
    # Check of bestanden al bestaan
    if json_path.exists():
        print(f"❌ JSON bestand bestaat al: {json_path}")
        return
    
    if py_path.exists():
        print(f"❌ Python module bestaat al: {py_path}")
        return
    
    # Maak JSON configuratie
    json_config = JSON_TEMPLATE.copy()
    json_config['id'] = regel_id
    json_config['naam'] = naam
    json_config['uitleg'] = uitleg
    
    # Schrijf JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON configuratie aangemaakt: {json_path}")
    
    # Maak Python module
    python_content = PYTHON_TEMPLATE.format(
        regel_id=regel_id,
        naam=naam,
        uitleg=uitleg,
        class_name=class_name,
        module_name=module_name
    )
    
    # Schrijf Python module
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(python_content)
    
    print(f"✅ Python module aangemaakt: {py_path}")
    
    print(f"""
📝 Volgende stappen:
1. Bewerk {json_path} om patronen, voorbeelden en metadata toe te voegen
2. Implementeer de validatie logica in {py_path}
3. Test de regel met: python -m pytest tests/test_toetsregel_{module_name}.py
""")


def main():
    """Main functie voor command line gebruik."""
    if len(sys.argv) < 4:
        print("Gebruik: python create_regel_module.py REGEL-ID \"Regel naam\" \"Uitleg\"")
        print("Voorbeeld: python create_regel_module.py TEST-01 \"Test regel\" \"Dit is een test regel\"")
        sys.exit(1)
    
    regel_id = sys.argv[1]
    naam = sys.argv[2]
    uitleg = sys.argv[3]
    
    create_regel_module(regel_id, naam, uitleg)


if __name__ == "__main__":
    main()