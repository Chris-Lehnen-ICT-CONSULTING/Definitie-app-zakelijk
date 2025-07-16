#!/usr/bin/env python3
"""
Script om legacy toets functies uit core.py te migreren naar modulaire structuur.

Dit script:
1. Leest de toets functies uit core.py
2. Genereert validator classes in de juiste module
3. Maakt gebruik van de nieuwe modulaire loader
"""

import re
import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple


def extract_toets_functions(core_path: str) -> Dict[str, str]:
    """Extract toets functions from core.py."""
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all toets functions
    pattern = r'def (toets_[A-Z0-9_]+)\(([^)]+)\):\s*\n((?:.*\n)*?)(?=\ndef|\nclass|\Z)'
    matches = re.findall(pattern, content, re.MULTILINE)
    
    functions = {}
    for match in matches:
        func_name = match[0]
        params = match[1]
        body = match[2]
        
        # Skip already migrated or special functions
        if func_name in ['toets_definitie', 'toets_op_basis_van_regel']:
            continue
            
        regel_id = func_name.replace('toets_', '').replace('_', '-')
        functions[regel_id] = {
            'name': func_name,
            'params': params,
            'body': body,
            'full': f"def {func_name}({params}):\n{body}"
        }
    
    return functions


def determine_category(regel_id: str) -> str:
    """Determine which category file a rule belongs to."""
    prefix = regel_id.split('-')[0]
    
    mapping = {
        'ARAI': 'ai_rules',
        'INT': 'integrity_rules',
        'SAM': 'samenhang_rules',
        'VER': 'versioning_rules'
    }
    
    return mapping.get(prefix, 'other_rules')


def create_validator_class(regel_id: str, func_data: Dict) -> str:
    """Create a validator class from a legacy function."""
    class_name = regel_id.replace('-', '').replace('SUB', 'Sub')
    
    # Extract the body and adapt it
    body = func_data['body']
    
    # Simple transformation - this needs manual review
    template = f'''class {class_name}Validator(BaseValidator):
    """
    Validator voor {regel_id}.
    Gemigreerd van legacy core.py
    """
    
    def __init__(self):
        super().__init__(
            regel_id="{regel_id}",
            regel_naam="TODO: Add naam from JSON",
            categorie="TODO: Add category"
        )
    
    def valideer(self, context: ValidationContext) -> ValidationResult:
        """Valideer volgens {regel_id} regel."""
        definitie = context.definitie
        regel = context.regel_config
        
        # Legacy code - needs adaptation
        {body.replace('return ', 'melding = ')}
        
        # Convert legacy return to new format
        if 'melding' in locals():
            succes = "✔️" in melding
            return ValidationResult(
                regel_id=self.regel_id,
                melding=melding,
                ernst="info" if succes else "error",
                suggestie=""
            )
        
        return self._geen_problemen_gevonden()
'''
    
    return template


def create_migration_files(functions: Dict[str, Dict]):
    """Create new validator files for each category."""
    categories = {}
    
    # Group by category
    for regel_id, func_data in functions.items():
        category = determine_category(regel_id)
        if category not in categories:
            categories[category] = []
        categories[category].append((regel_id, func_data))
    
    # Create files
    validators_dir = Path(__file__).parent / "validators"
    
    for category, rules in categories.items():
        file_path = validators_dir / f"{category}.py"
        
        # Generate content
        content = f'''"""
{category.replace('_', ' ').title()} validators.
Gemigreerd van legacy core.py
"""

from typing import Dict, List, Optional, Any
import re
import logging

from .base_validator import BaseValidator, ValidationContext, ValidationResult

logger = logging.getLogger(__name__)


'''
        
        # Add each validator class
        for regel_id, func_data in sorted(rules):
            content += create_validator_class(regel_id, func_data)
            content += "\n\n"
        
        print(f"Creating {file_path}")
        print(f"  - {len(rules)} validators")
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


def create_integration_adapter():
    """Create adapter to use new validators with old interface."""
    adapter_content = '''"""
Legacy adapter voor backward compatibility.
Maakt het mogelijk om de nieuwe modulaire validators te gebruiken
met de oude toets_definitie interface.
"""

from typing import Dict, List, Any, Optional
import logging

from .validators import ValidationContext
from config.toetsregels.modular_loader import get_modular_loader

logger = logging.getLogger(__name__)


def toets_op_basis_van_regel(
    definitie: str,
    regel_id: str,
    regel_data: Dict[str, Any],
    begrip: Optional[str] = None,
    marker: Optional[str] = None,
    voorkeursterm: Optional[str] = None,
    bronnen_gebruikt: Optional[str] = None,
    contexten: Optional[Dict[str, List[str]]] = None,
    repository: Optional[Dict[str, str]] = None
) -> str:
    """
    Legacy interface voor toetsing van een enkele regel.
    Gebruikt de nieuwe modulaire validators.
    """
    # Probeer eerst de modulaire loader
    loader = get_modular_loader()
    
    try:
        # Valideer met nieuwe systeem
        succes, melding, score = loader.validate_with_regel(
            regel_id=regel_id,
            definitie=definitie,
            begrip=begrip or "",
            context={
                'marker': marker,
                'voorkeursterm': voorkeursterm,
                'bronnen_gebruikt': bronnen_gebruikt,
                'contexten': contexten,
                'repository': repository,
                'regel_data': regel_data
            }
        )
        
        return melding
        
    except Exception as e:
        logger.warning(f"Modulaire validator voor {regel_id} faalde: {e}")
        
        # Fallback naar legacy indien nodig
        try:
            from . import core
            
            func_name = f"toets_{regel_id.replace('-', '_')}"
            if hasattr(core, func_name):
                func = getattr(core, func_name)
                
                # Bepaal welke parameters de functie accepteert
                import inspect
                sig = inspect.signature(func)
                params = {}
                
                if 'definitie' in sig.parameters:
                    params['definitie'] = definitie
                if 'regel' in sig.parameters:
                    params['regel'] = regel_data
                if 'begrip' in sig.parameters:
                    params['begrip'] = begrip
                if 'contexten' in sig.parameters:
                    params['contexten'] = contexten
                if 'bronnen_gebruikt' in sig.parameters:
                    params['bronnen_gebruikt'] = bronnen_gebruikt
                
                return func(**params)
                
        except Exception as legacy_e:
            logger.error(f"Ook legacy validator voor {regel_id} faalde: {legacy_e}")
            
        return f"❌ {regel_id}: Validator niet gevonden"
'''
    
    adapter_path = Path(__file__).parent / "legacy_adapter.py"
    with open(adapter_path, 'w', encoding='utf-8') as f:
        f.write(adapter_content)
    
    print(f"\nCreated legacy adapter: {adapter_path}")


def main():
    """Main migration function."""
    print("🔄 Migratie van legacy toets functies naar modulaire structuur\n")
    
    # Extract functions
    core_path = Path(__file__).parent / "core.py"
    functions = extract_toets_functions(str(core_path))
    
    print(f"Gevonden {len(functions)} toets functies om te migreren:")
    for regel_id in sorted(functions.keys()):
        print(f"  - {regel_id}")
    
    print("\nGenereren van validator classes...")
    create_migration_files(functions)
    
    print("\nCreëren van legacy adapter...")
    create_integration_adapter()
    
    print("\n✅ Migratie voltooid!")
    print("\n⚠️  BELANGRIJK: De gegenereerde code heeft handmatige review nodig:")
    print("   1. Controleer de validator logica")
    print("   2. Voeg de juiste regel namen toe uit JSON")
    print("   3. Test elke validator individueel")
    print("   4. Update imports in modular_toetser.py")


if __name__ == "__main__":
    main()