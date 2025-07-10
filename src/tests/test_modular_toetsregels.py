"""
Tests voor het modulaire toetsregels systeem.
Controleert integratie tussen ToetsregelManager, adapter en bestaande code.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from config.toetsregel_manager import ToetsregelManager, RegelPrioriteit, RegelAanbeveling
from config.toetsregels_adapter import (
    ToetsregelsCompatibilityAdapter,
    load_toetsregels,
    get_toetsregels_by_priority,
    get_toetsregels_by_category
)


class TestToetsregelManager:
    """Test ToetsregelManager functionaliteit."""
    
    def test_manager_initialization(self):
        """Test of manager correct initialiseert."""
        manager = ToetsregelManager()
        
        assert manager.base_dir.exists()
        assert manager.regels_dir.exists()
        assert manager.sets_dir.exists()
        
        # Check dat er regels beschikbaar zijn
        regels = manager.get_available_regels()
        assert len(regels) > 0
        assert "CON-01" in regels
        assert "ESS-02" in regels
    
    def test_regel_loading(self):
        """Test het laden van individuele regels."""
        manager = ToetsregelManager()
        
        # Test bestaande regel
        con01 = manager.load_regel("CON-01")
        assert con01 is not None
        assert con01["id"] == "CON-01"
        assert "naam" in con01
        assert "uitleg" in con01
        assert "prioriteit" in con01
        
        # Test niet-bestaande regel
        fake_regel = manager.load_regel("NIET-BESTAAT")
        assert fake_regel is None
    
    def test_regelset_loading(self):
        """Test het laden van regelsets."""
        manager = ToetsregelManager()
        
        # Test verplichte regels
        verplicht = manager.load_regelset("verplicht")
        assert verplicht is not None
        assert len(verplicht.regels) > 0
        
        # Test kritieke regels
        kritiek = manager.load_regelset("verplicht-hoog")
        assert kritiek is not None
        assert len(kritiek.regels) > 0
        
        # Test categorie-specifieke regels
        context_regels = manager.load_regelset("context")
        assert context_regels is not None
        
        # Controleer dat alle regels in de set daadwerkelijk laden
        for regel_id in context_regels.regels:
            regel = manager.load_regel(regel_id)
            assert regel is not None
    
    def test_verplichte_regels(self):
        """Test ophalen van verplichte regels."""
        manager = ToetsregelManager()
        
        verplichte_regels = manager.get_verplichte_regels()
        assert len(verplichte_regels) > 0
        
        # Controleer dat alle regels verplicht zijn
        for regel in verplichte_regels:
            assert regel.get("aanbeveling") == "verplicht"
    
    def test_kritieke_regels(self):
        """Test ophalen van kritieke regels."""
        manager = ToetsregelManager()
        
        kritieke_regels = manager.get_kritieke_regels()
        assert len(kritieke_regels) > 0
        
        # Controleer dat alle regels zowel verplicht als hoge prioriteit hebben
        for regel in kritieke_regels:
            assert regel.get("aanbeveling") == "verplicht"
            assert regel.get("prioriteit") == "hoog"
    
    def test_regels_voor_categorie(self):
        """Test ophalen van regels per ontologische categorie."""
        manager = ToetsregelManager()
        
        # Test alle categorieën
        categorieën = ["type", "proces", "resultaat", "exemplaar"]
        
        for categorie in categorieën:
            regels = manager.get_regels_voor_categorie(categorie)
            # Elke categorie moet tenminste enkele regels hebben
            assert len(regels) > 0
            
            # Controleer dat alle regels geldig zijn
            for regel in regels:
                assert "id" in regel
                assert "naam" in regel
    
    def test_caching(self):
        """Test caching functionaliteit."""
        manager = ToetsregelManager()
        
        # Reset stats
        manager.stats = {
            'regels_geladen': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'sets_geladen': 0
        }
        
        # Eerste keer laden = cache miss
        regel1 = manager.load_regel("CON-01")
        assert manager.stats['cache_misses'] > 0
        
        # Tweede keer laden = cache hit
        regel2 = manager.load_regel("CON-01")
        assert regel1 == regel2
        assert manager.stats['cache_hits'] > 0
    
    def test_regel_validatie(self):
        """Test regel validatie."""
        manager = ToetsregelManager()
        
        # Test geldige regel
        geldige_regel = {
            "id": "TEST-01",
            "naam": "Test regel",
            "uitleg": "Dit is een test",
            "prioriteit": "hoog",
            "aanbeveling": "verplicht"
        }
        
        errors = manager.validate_regel(geldige_regel)
        assert len(errors) == 0
        
        # Test ongeldige regel (ontbrekende velden)
        ongeldige_regel = {
            "id": "TEST-02"
        }
        
        errors = manager.validate_regel(ongeldige_regel)
        assert len(errors) > 0


class TestBackwardCompatibility:
    """Test backward compatibility adapter."""
    
    def test_legacy_format_generation(self):
        """Test generatie van legacy formaat."""
        legacy_data = load_toetsregels()
        
        assert "regels" in legacy_data
        assert len(legacy_data["regels"]) > 0
        
        # Controleer dat bekende regels aanwezig zijn
        assert "CON-01" in legacy_data["regels"]
        assert "ESS-02" in legacy_data["regels"]
        
        # Controleer structuur van regel
        con01 = legacy_data["regels"]["CON-01"]
        assert "id" in con01
        assert "naam" in con01
        assert "uitleg" in con01
    
    def test_priority_filtering(self):
        """Test filteren op prioriteit."""
        hoge_prioriteit = get_toetsregels_by_priority("hoog")
        
        assert len(hoge_prioriteit) > 0
        
        # Controleer dat alle regels hoge prioriteit hebben
        for regel in hoge_prioriteit:
            assert regel.get("prioriteit") == "hoog"
    
    def test_category_filtering(self):
        """Test filteren op categorie."""
        con_regels = get_toetsregels_by_category("CON")
        
        assert len(con_regels) > 0
        
        # Controleer dat alle regels beginnen met CON
        for regel in con_regels:
            assert regel.get("id", "").startswith("CON")
        
        # Test andere categorieën
        ess_regels = get_toetsregels_by_category("ESS")
        assert len(ess_regels) > 0
        
        int_regels = get_toetsregels_by_category("INT")
        assert len(int_regels) > 0


class TestIntegration:
    """Test integratie met bestaande systeem."""
    
    def test_config_integration(self):
        """Test integratie met configuratie systeem."""
        try:
            from config.config_manager import get_config_manager
            from config.toetsregels_adapter import integrate_with_config_manager
            
            # Test integratie
            integrate_with_config_manager()
            
            # Dit mag geen errors geven
            assert True
            
        except ImportError:
            # Skip als ConfigManager niet beschikbaar is
            pytest.skip("ConfigManager niet beschikbaar")
    
    def test_performance_comparison(self):
        """Test performance vergeleken met oude systeem."""
        import time
        
        # Test nieuwe systeem
        start_time = time.time()
        manager = ToetsregelManager()
        
        # Laad kritieke regels 10 keer
        for _ in range(10):
            regels = manager.get_kritieke_regels()
        
        nieuwe_tijd = time.time() - start_time
        
        # Test legacy systeem
        start_time = time.time()
        
        # Laad legacy formaat 10 keer
        for _ in range(10):
            legacy_data = load_toetsregels()
            
        legacy_tijd = time.time() - start_time
        
        # Nieuwe systeem zou sneller moeten zijn na eerste load (caching)
        print(f"Nieuwe systeem: {nieuwe_tijd:.4f}s")
        print(f"Legacy systeem: {legacy_tijd:.4f}s")
        
        # Dit is meer een benchmark dan een test
        assert True
    
    def test_memory_usage(self):
        """Test geheugengebruik."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss
        
        # Laad veel regels
        manager = ToetsregelManager()
        
        # Laad alle beschikbare regels
        for regel_id in manager.get_available_regels():
            manager.load_regel(regel_id)
        
        # Laad alle regelsets
        for set_naam in manager.get_available_sets():
            manager.load_regelset(set_naam.replace('.json', ''))
        
        end_memory = process.memory_info().rss
        memory_used = end_memory - start_memory
        
        # Memory usage should be reasonable (less than 50MB for rules)
        assert memory_used < 50 * 1024 * 1024  # 50MB
        
        print(f"Memory gebruikt: {memory_used / 1024 / 1024:.2f} MB")


class TestDataIntegrity:
    """Test data integriteit van gemigreerde regels."""
    
    def test_all_rules_migrated(self):
        """Test dat alle regels correct zijn gemigreerd."""
        manager = ToetsregelManager()
        
        # Laad legacy data om te vergelijken
        legacy_data = load_toetsregels()
        legacy_regels = legacy_data["regels"]
        
        # Haal alle nieuwe regels op
        nieuwe_regels = {}
        for regel_id in manager.get_available_regels():
            regel = manager.load_regel(regel_id)
            if regel:
                nieuwe_regels[regel_id] = regel
        
        # Controleer dat alle legacy regels ook in nieuwe systeem zitten
        for regel_id in legacy_regels:
            assert regel_id in nieuwe_regels, f"Regel {regel_id} niet gemigreerd"
        
        # Controleer aantal
        assert len(nieuwe_regels) == len(legacy_regels)
    
    def test_rule_content_integrity(self):
        """Test dat regel inhoud correct is behouden."""
        manager = ToetsregelManager()
        
        # Test enkele specifieke regels op inhoud
        test_regels = ["CON-01", "ESS-02", "INT-03"]
        
        for regel_id in test_regels:
            regel = manager.load_regel(regel_id)
            assert regel is not None
            
            # Controleer verplichte velden
            assert regel["id"] == regel_id
            assert len(regel["naam"]) > 0
            assert len(regel["uitleg"]) > 0
            assert regel["prioriteit"] in ["hoog", "midden", "laag"]
            assert regel["aanbeveling"] in ["verplicht", "aanbevolen", "optioneel"]
    
    def test_rule_sets_completeness(self):
        """Test dat regelsets compleet zijn."""
        manager = ToetsregelManager()
        
        # Test dat alle regels in verplicht-hoog daadwerkelijk verplicht en hoog zijn
        kritieke_regels = manager.get_kritieke_regels()
        
        for regel in kritieke_regels:
            assert regel["aanbeveling"] == "verplicht"
            assert regel["prioriteit"] == "hoog"
        
        # Test dat categoriesets correct zijn
        con_set = manager.load_regelset("context")
        for regel_id in con_set.regels:
            assert regel_id.startswith("CON")


if __name__ == "__main__":
    # Run tests als script wordt uitgevoerd
    import subprocess
    import sys
    
    print("🧪 Running Modular Toetsregels Tests")
    print("=" * 40)
    
    # Run pytest op dit bestand
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], capture_output=False)
    
    sys.exit(result.returncode)