#!/usr/bin/env python3
"""
Centrale runner voor maintenance scripts.
Biedt overzicht van beschikbare tools en hun status.
"""

import os
import sys
from pathlib import Path
import subprocess
import importlib.util

def list_maintenance_scripts():
    """List alle maintenance scripts met hun documentatie."""
    maintenance_dir = Path(__file__).parent / "maintenance"
    scripts = []
    
    for script_file in maintenance_dir.glob("*.py"):
        if script_file.stem == "__init__":
            continue
            
        # Probeer docstring te lezen
        try:
            spec = importlib.util.spec_from_file_location(script_file.stem, script_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            doc = module.__doc__ or "Geen beschrijving"
        except Exception:
            doc = "Kon documentatie niet laden"
        
        scripts.append({
            "name": script_file.stem,
            "path": script_file,
            "doc": doc.strip()
        })
    
    return scripts

def main():
    print("🔧 DefinitieAgent Maintenance Tools")
    print("=" * 50)
    print()
    
    scripts = list_maintenance_scripts()
    
    if not scripts:
        print("❌ Geen maintenance scripts gevonden")
        return
    
    print("📋 Beschikbare scripts:\n")
    
    for i, script in enumerate(scripts, 1):
        print(f"{i}. {script['name']}")
        print(f"   {script['doc']}")
        print()
    
    print("\n💡 Gebruik: python tools/maintenance/<script_naam>.py --help")
    print("💡 Of run direct: python tools/run_maintenance.py <script_naam> [args]")
    
    # Als argumenten gegeven, run het script
    if len(sys.argv) > 1:
        script_name = sys.argv[1]
        script_args = sys.argv[2:]
        
        # Zoek script
        script_path = None
        for script in scripts:
            if script['name'] == script_name:
                script_path = script['path']
                break
        
        if script_path:
            print(f"\n▶️  Running {script_name}...")
            print("-" * 50)
            subprocess.run([sys.executable, str(script_path)] + script_args)
        else:
            print(f"\n❌ Script '{script_name}' niet gevonden")

if __name__ == "__main__":
    main()