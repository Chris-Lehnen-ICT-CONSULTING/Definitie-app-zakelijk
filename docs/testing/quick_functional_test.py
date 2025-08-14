#!/usr/bin/env python3
"""Quick functional test voor DefinitieAgent."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🔍 Quick Functional Test\n")

# Test 1: Config
try:
    from config.config_loader import load_toetsregels
    rules = load_toetsregels()
    print(f"✅ Config: {len(rules)} toetsregels geladen")
except Exception as e:
    print(f"❌ Config: {e}")

# Test 2: AI Toetser
try:
    from ai_toetser.core import AIToetser
    toetser = AIToetser()
    result = toetser.toets_definitie("Een proces.", "test")
    print(f"✅ AI Toetser: {'Voldoet' if result['voldoet'] else 'Voldoet niet'}")
except Exception as e:
    print(f"❌ AI Toetser: {e}")

# Test 3: Database
try:
    from database.definitie_repository import DefinitieRepository
    repo = DefinitieRepository("test.db")
    print("✅ Database: Repository geïnitialiseerd")
except Exception as e:
    print(f"❌ Database: {e}")

# Test 4: Session State
try:
    from ui.session_state import SessionStateManager
    print(f"✅ SessionState: clear_value method exists = {hasattr(SessionStateManager, 'clear_value')}")
except Exception as e:
    print(f"❌ SessionState: {e}")

# Test 5: Services
try:
    from services.definition_service import DefinitionService
    print("✅ Services: DefinitionService importeert")
except Exception as e:
    print(f"❌ Services: {e}")

print("\n✨ Quick test compleet!")