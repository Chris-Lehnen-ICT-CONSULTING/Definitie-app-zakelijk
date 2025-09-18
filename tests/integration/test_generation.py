#!/usr/bin/env python3
"""Test script voor definitie generatie na refactor."""

import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.service_factory import ServiceFactory

logging.basicConfig(level=logging.INFO)

async def test_generation():
    """Test definitie generatie."""
    print("Starting test...")
    
    # Get service factory
    factory = ServiceFactory()
    
    # Test parameters
    begrip = "overeenkomst"
    context_dict = {
        "organisatorisch": ["Rechtbank"],
        "juridisch": ["Burgerlijk recht"],
        "wettelijk": ["BW"]
    }
    
    try:
        # Call async generate_definition directly
        print(f"Generating definition for: {begrip}")
        result = await factory.generate_definition(begrip, context_dict)
        
        print("\n=== RESULT ===")
        print(f"Success: {result.get('success')}")
        print(f"Definition: {result.get('definitie_gecorrigeerd', 'NOT FOUND')[:200]}...")
        print(f"Score: {result.get('final_score')}")
        
        if not result.get('success'):
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())