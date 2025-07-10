#!/usr/bin/env python3
"""
Script om monolithische toetsregels.json te migreren naar modulaire structuur.
Elke regel wordt opgeslagen als afzonderlijk JSON bestand.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_directory_structure(base_path: Path):
    """Maak de nieuwe directory structuur aan."""
    directories = [
        base_path / "regels",
        base_path / "sets",
        base_path / "sets" / "per-categorie", 
        base_path / "sets" / "per-context",
        base_path / "sets" / "per-prioriteit"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory aangemaakt: {directory}")


def extract_individual_rules(source_file: Path, target_dir: Path):
    """Extraheer individuele regels naar afzonderlijke bestanden."""
    logger.info(f"Laden van {source_file}")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regels = data.get('regels', {})
    extracted_count = 0
    
    for regel_id, regel_data in regels.items():
        # Regel bestand pad
        regel_file = target_dir / "regels" / f"{regel_id}.json"
        
        # Sla regel op als individueel JSON bestand
        with open(regel_file, 'w', encoding='utf-8') as f:
            json.dump(regel_data, f, ensure_ascii=False, indent=2)
        
        extracted_count += 1
        logger.info(f"Regel {regel_id} opgeslagen naar {regel_file}")
    
    logger.info(f"Totaal {extracted_count} regels geëxtraheerd")
    return extracted_count


def create_rule_sets(source_file: Path, target_dir: Path):
    """Maak voorgedefinieerde regelsets aan."""
    logger.info("Genereren van regelsets...")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regels = data.get('regels', {})
    
    # Verzamel regels per categorie
    verplichte_regels = []
    hoge_prioriteit_regels = []
    context_regels = []
    essentie_regels = []
    interne_regels = []
    structuur_regels = []
    samenhang_regels = []
    arai_regels = []
    
    # Categoriseer regels
    for regel_id, regel_data in regels.items():
        prioriteit = regel_data.get('prioriteit', '')
        aanbeveling = regel_data.get('aanbeveling', '')
        
        # Verplichte regels
        if aanbeveling == 'verplicht':
            verplichte_regels.append(regel_id)
        
        # Hoge prioriteit regels
        if prioriteit == 'hoog':
            hoge_prioriteit_regels.append(regel_id)
        
        # Per categorie
        if regel_id.startswith('CON-'):
            context_regels.append(regel_id)
        elif regel_id.startswith('ESS-'):
            essentie_regels.append(regel_id)
        elif regel_id.startswith('INT-'):
            interne_regels.append(regel_id)
        elif regel_id.startswith('STR-'):
            structuur_regels.append(regel_id)
        elif regel_id.startswith('SAM-'):
            samenhang_regels.append(regel_id)
        elif regel_id.startswith('ARAI'):
            arai_regels.append(regel_id)
    
    # Sla regelsets op
    regelsets = {
        "sets/per-prioriteit/verplicht.json": {
            "naam": "Verplichte Regels",
            "beschrijving": "Alle regels met aanbeveling 'verplicht'",
            "regels": verplichte_regels
        },
        "sets/per-prioriteit/hoog.json": {
            "naam": "Hoge Prioriteit Regels", 
            "beschrijving": "Alle regels met prioriteit 'hoog'",
            "regels": hoge_prioriteit_regels
        },
        "sets/per-prioriteit/verplicht-hoog.json": {
            "naam": "Kritieke Regels",
            "beschrijving": "Regels die zowel verplicht als hoge prioriteit hebben",
            "regels": list(set(verplichte_regels) & set(hoge_prioriteit_regels))
        },
        "sets/per-categorie/context.json": {
            "naam": "Context Regels (CON)",
            "beschrijving": "Regels voor contextuele formulering",
            "regels": context_regels
        },
        "sets/per-categorie/essentie.json": {
            "naam": "Essentie Regels (ESS)",
            "beschrijving": "Regels voor begripsinhoud en -zuiverheid", 
            "regels": essentie_regels
        },
        "sets/per-categorie/interne.json": {
            "naam": "Interne Regels (INT)",
            "beschrijving": "Regels voor interne kwaliteit van definities",
            "regels": interne_regels
        },
        "sets/per-categorie/structuur.json": {
            "naam": "Structuur Regels (STR)",
            "beschrijving": "Regels voor structuur en opbouw",
            "regels": structuur_regels
        },
        "sets/per-categorie/samenhang.json": {
            "naam": "Samenhang Regels (SAM)",
            "beschrijving": "Regels voor samenhang en consistentie",
            "regels": samenhang_regels
        },
        "sets/per-categorie/arai.json": {
            "naam": "ARAI Regels",
            "beschrijving": "Architectuur regels voor begrippen",
            "regels": arai_regels
        }
    }
    
    # Ontologische categorie specifieke sets
    ontologische_sets = {
        "sets/per-context/type-regels.json": {
            "naam": "Regels voor Type definities",
            "beschrijving": "Regels specifiek voor type/soort begrippen",
            "regels": verplichte_regels + ['ESS-02', 'ESS-05', 'INT-03']
        },
        "sets/per-context/proces-regels.json": {
            "naam": "Regels voor Proces definities", 
            "beschrijving": "Regels specifiek voor proces/activiteit begrippen",
            "regels": verplichte_regels + ['ESS-01', 'ESS-02', 'STR-01']
        },
        "sets/per-context/resultaat-regels.json": {
            "naam": "Regels voor Resultaat definities",
            "beschrijving": "Regels specifiek voor resultaat/uitkomst begrippen", 
            "regels": verplichte_regels + ['ESS-02', 'ESS-04', 'ESS-05']
        },
        "sets/per-context/exemplaar-regels.json": {
            "naam": "Regels voor Exemplaar definities",
            "beschrijving": "Regels specifiek voor exemplaar/instantie begrippen",
            "regels": verplichte_regels + ['ESS-02', 'ESS-03', 'ESS-05']
        }
    }
    
    regelsets.update(ontologische_sets)
    
    # Sla alle regelsets op
    for bestand_pad, regelset_data in regelsets.items():
        volledig_pad = target_dir / bestand_pad
        with open(volledig_pad, 'w', encoding='utf-8') as f:
            json.dump(regelset_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Regelset opgeslagen: {volledig_pad}")
    
    return len(regelsets)


def create_manager_config(target_dir: Path):
    """Maak centrale manager configuratie aan."""
    config = {
        "versie": "1.0.0",
        "beschrijving": "Centrale configuratie voor modulaire toetsregels",
        "directories": {
            "regels": "regels/",
            "sets": "sets/",
            "cache": "cache/"
        },
        "default_sets": {
            "basis": "sets/per-prioriteit/verplicht-hoog.json",
            "volledig": "sets/per-prioriteit/verplicht.json"
        },
        "cache_settings": {
            "enabled": True,
            "ttl_seconds": 3600,
            "max_items": 1000
        },
        "validatie": {
            "verplichte_velden": ["id", "naam", "uitleg", "prioriteit", "aanbeveling"],
            "toegestane_prioriteiten": ["hoog", "midden", "laag"],
            "toegestane_aanbevelingen": ["verplicht", "aanbevolen", "optioneel"]
        }
    }
    
    config_file = target_dir / "toetsregels-manager.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Manager configuratie opgeslagen: {config_file}")
    return config_file


def main():
    """Hoofdfunctie voor migratie."""
    # Paden definiëren
    source_file = Path("../config/toetsregels.json")
    target_dir = Path("../config/toetsregels")
    
    logger.info("=== MIGRATIE NAAR MODULAIRE TOETSREGELS ===")
    logger.info(f"Bron: {source_file}")
    logger.info(f"Doel: {target_dir}")
    
    # Controleer of bron bestand bestaat
    if not source_file.exists():
        logger.error(f"Bron bestand niet gevonden: {source_file}")
        return False
    
    try:
        # Stap 1: Maak directory structuur
        create_directory_structure(target_dir)
        
        # Stap 2: Extraheer individuele regels
        regel_count = extract_individual_rules(source_file, target_dir)
        
        # Stap 3: Maak regelsets
        set_count = create_rule_sets(source_file, target_dir)
        
        # Stap 4: Maak manager configuratie
        config_file = create_manager_config(target_dir)
        
        logger.info("=== MIGRATIE VOLTOOID ===")
        logger.info(f"Regels geëxtraheerd: {regel_count}")
        logger.info(f"Regelsets aangemaakt: {set_count}")
        logger.info(f"Configuratie: {config_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Fout tijdens migratie: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)