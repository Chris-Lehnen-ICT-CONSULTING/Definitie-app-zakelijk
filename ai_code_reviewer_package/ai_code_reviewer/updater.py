#!/usr/bin/env python3
"""
Package Updater - Automatische updates voor AI Code Reviewer
"""

import requests
import subprocess
import sys
from typing import Optional
import pkg_resources
from packaging import version


class PackageUpdater:
    """Handelt package updates af."""
    
    def __init__(self):
        self.package_name = "ai-code-reviewer"
        self.pypi_url = f"https://pypi.org/pypi/{self.package_name}/json"
        
    def get_current_version(self) -> str:
        """Krijg huidige geïnstalleerde versie."""
        try:
            return pkg_resources.get_distribution(self.package_name).version
        except pkg_resources.DistributionNotFound:
            return "0.0.0"
    
    def get_latest_version(self) -> Optional[str]:
        """Krijg laatste versie van PyPI."""
        try:
            response = requests.get(self.pypi_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['info']['version']
        except Exception as e:
            print(f"Warning: Could not check for updates: {e}")
            return None
    
    def check_for_updates(self) -> Optional[str]:
        """Check of er updates beschikbaar zijn."""
        current = self.get_current_version()
        latest = self.get_latest_version()
        
        if not latest:
            return None
            
        if version.parse(latest) > version.parse(current):
            return latest
            
        return None
    
    def update_package(self) -> bool:
        """Update het package naar de laatste versie."""
        try:
            print("📦 Updating AI Code Reviewer...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", self.package_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Package updated successfully!")
                new_version = self.get_current_version()
                print(f"📌 Now using version {new_version}")
                return True
            else:
                print(f"❌ Update failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Update error: {e}")
            return False
    
    def auto_update_check(self) -> None:
        """Automatische update check (non-invasive)."""
        latest = self.check_for_updates()
        if latest:
            print(f"💡 New version {latest} available. Run 'ai-code-review update' to upgrade.")