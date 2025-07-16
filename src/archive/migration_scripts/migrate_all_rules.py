#!/usr/bin/env python3
"""
Script om ALLE legacy toets functies uit core.py te migreren naar modulaire structuur.
Dit script analyseert elke functie en genereert de bijbehorende Python module.
"""

import re
import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Mapping van functienaam naar module imports die nodig zijn
SPECIAL_IMPORTS = {
    'ARAI04': ['from web_lookup import is_plurale_tantum'],
    'ARAI04SUB1': ['from web_lookup import is_plurale_tantum'],
}

def extract_function_body(core_content: str, func_name: str) -> str:
    """Extract de complete functie body."""
    # Zoek begin van functie
    pattern = rf'^def {func_name}\([^)]*\):\s*\n'
    match = re.search(pattern, core_content, re.MULTILINE)
    if not match:
        return None
    
    start = match.end()
    lines = core_content[start:].split('\n')
    
    # Verzamel functie body tot volgende def of einde
    body_lines = []
    indent_level = None
    
    for line in lines:
        # Stop bij volgende functie definitie op top level
        if line.startswith('def ') and indent_level is not None:
            break
        
        # Skip lege regels aan begin
        if not body_lines and not line.strip():
            continue
            
        # Bepaal indent level van eerste non-empty line
        if indent_level is None and line.strip():
            indent_level = len(line) - len(line.lstrip())
        
        # Stop als we terug op top level zijn (behalve lege regels)
        if line.strip() and not line.startswith(' '):
            break
            
        body_lines.append(line)
    
    # Verwijder trailing lege regels
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    
    return '\n'.join(body_lines)


def analyze_function_signature(core_content: str, func_name: str) -> Dict:
    """Analyseer functie signature en parameters."""
    pattern = rf'def {func_name}\(([^)]*)\):'
    match = re.search(pattern, core_content)
    if not match:
        return {}
    
    params_str = match.group(1)
    params = [p.strip() for p in params_str.split(',') if p.strip()]
    
    # Bepaal welke parameters de functie gebruikt
    param_info = {
        'has_definitie': 'definitie' in params,
        'has_regel': 'regel' in params,
        'has_begrip': 'begrip' in params,
        'has_contexten': 'contexten' in params,
        'has_bronnen': 'bronnen_gebruikt' in params,
        'has_repository': 'repository' in params,
        'has_voorkeursterm': 'voorkeursterm' in params,
        'params_str': params_str,
        'params': params
    }
    
    return param_info


def create_validator_module(regel_id: str, func_name: str, core_content: str) -> str:
    """Creëer een validator module voor een regel."""
    # Haal functie body op
    body = extract_function_body(core_content, func_name)
    if not body:
        print(f"⚠️  Kon body niet extraheren voor {func_name}")
        return None
    
    # Analyseer parameters
    param_info = analyze_function_signature(core_content, func_name)
    
    # Basis module naam
    module_name = regel_id.replace('-', '_')
    class_name = module_name.replace('_', '')
    
    # Check voor speciale imports
    extra_imports = SPECIAL_IMPORTS.get(regel_id, [])
    imports_str = '\n'.join(extra_imports) if extra_imports else ''
    
    # Template voor module
    template = f'''"""
Toetsregel {regel_id}
Automatisch gemigreerd van legacy core.py
"""

import re
from typing import Dict, List, Tuple, Optional
import logging
{imports_str}

logger = logging.getLogger(__name__)


class {class_name}Validator:
    """Validator voor {regel_id}."""
    
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
        self.prioriteit = config.get('prioriteit', 'midden')
    
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
        # Haal regel config op
        regel = self.config
        
        # Extract context parameters indien nodig
        if context:
            {'contexten = context.get("contexten")' if param_info.get('has_contexten') else ''}
            {'bronnen_gebruikt = context.get("bronnen_gebruikt")' if param_info.get('has_bronnen') else ''}
            {'repository = context.get("repository")' if param_info.get('has_repository') else ''}
            {'voorkeursterm = context.get("voorkeursterm")' if param_info.get('has_voorkeursterm') else ''}
        
        # Legacy implementatie
        try:
{body}
        except Exception as e:
            logger.error(f"Fout in {{self.id}} validator: {{e}}")
            return False, f"⚠️ {{self.id}}: fout bij uitvoeren toetsregel", 0.0
        
        # Convert legacy return naar nieuwe format
        if isinstance(result, str):
            # Bepaal succes op basis van emoji
            succes = "✔️" in result or "✅" in result
            score = 1.0 if succes else 0.0
            if "🟡" in result:
                score = 0.5
            return succes, result, score
        
        # Fallback
        return False, f"⚠️ {{self.id}}: geen resultaat", 0.0
    
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
            hints.append(f"Volg dit voorbeeld: {{goede_voorbeelden[0]}}")
        
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
    
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '{regel_id}.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return {class_name}Validator(config)
'''
    
    # Voeg result variabele toe aan einde van body indien nodig
    if not re.search(r'\breturn\b', body):
        body += '\n            result = f"⚠️ {self.id}: geen return statement gevonden"'
        template = template.replace('{body}', body + '\n            return result')
    else:
        # Vervang return statements met result assignment
        body_modified = re.sub(r'^(\s*)return\s+', r'\1result = ', body, flags=re.MULTILINE)
        template = template.replace('{body}', body_modified)
    
    # Clean up template
    template = re.sub(r'\n\s*\n\s*\n', '\n\n', template)  # Verwijder extra lege regels
    
    return template


def migrate_all_rules():
    """Migreer alle legacy regels."""
    print("🚀 Start migratie van ALLE legacy toetsregels\n")
    
    # Lees core.py
    core_path = Path(__file__).parent / "core.py"
    with open(core_path, 'r', encoding='utf-8') as f:
        core_content = f.read()
    
    # Vind alle toets functies
    pattern = r'def (toets_[A-Z0-9_]+)\('
    matches = re.findall(pattern, core_content)
    
    # Filter speciale functies
    functions = [f for f in matches if f not in ['toets_definitie', 'toets_op_basis_van_regel']]
    
    print(f"Gevonden {len(functions)} toets functies om te migreren\n")
    
    # Output directory
    output_dir = Path(__file__).parent.parent / "config" / "toetsregels" / "regels"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    migrated = []
    skipped = []
    failed = []
    
    for func_name in sorted(functions):
        # Bepaal regel ID
        regel_id = func_name.replace('toets_', '').replace('_', '-')
        module_name = func_name.replace('toets_', '')
        py_filename = f"{module_name}.py"
        py_path = output_dir / py_filename
        
        # Check of module al bestaat
        if py_path.exists():
            print(f"⏭️  {regel_id}: Module bestaat al")
            skipped.append(regel_id)
            continue
        
        # Check of JSON bestaat
        json_path = output_dir / f"{regel_id}.json"
        if not json_path.exists():
            print(f"⚠️  {regel_id}: Geen JSON configuratie gevonden, skip")
            failed.append(regel_id)
            continue
        
        try:
            # Genereer module
            module_content = create_validator_module(regel_id, func_name, core_content)
            if not module_content:
                failed.append(regel_id)
                continue
            
            # Schrijf module
            with open(py_path, 'w', encoding='utf-8') as f:
                f.write(module_content)
            
            print(f"✅ {regel_id}: Module aangemaakt")
            migrated.append(regel_id)
            
        except Exception as e:
            print(f"❌ {regel_id}: Fout bij migratie: {e}")
            failed.append(regel_id)
    
    # Samenvatting
    print(f"\n📊 Migratie Samenvatting:")
    print(f"   ✅ Gemigreerd: {len(migrated)}")
    print(f"   ⏭️  Overgeslagen: {len(skipped)}")
    print(f"   ❌ Mislukt: {len(failed)}")
    print(f"   📝 Totaal: {len(functions)}")
    
    if failed:
        print(f"\n❌ Mislukte migraties:")
        for regel_id in failed:
            print(f"   - {regel_id}")
    
    print("\n✨ Klaar! Test de gemigreerde regels met de hybrid approach.")


if __name__ == "__main__":
    migrate_all_rules()