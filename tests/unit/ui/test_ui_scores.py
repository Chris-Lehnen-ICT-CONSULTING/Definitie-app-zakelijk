#!/usr/bin/env python3
"""
Test script voor UI scores fix.
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import pytest

from ui.tabbed_interface import TabbedInterface

pytestmark = [pytest.mark.unit]


async def test_ui_scores():
    """Test de UI scores functionaliteit."""
    print("🧪 Testing UI Scores Fix")
    print("=" * 40)

    # Maak TabbedInterface instantie
    interface = TabbedInterface()

    # Test begrippen
    test_begrippen = [
        ("toets", "KMAR", "Strafrecht"),
        ("authenticatie", "Gemeente", "Wet"),
        ("document", "Overheid", "Wob"),
    ]

    for begrip, org, jur in test_begrippen:
        print(f"\n📋 Testing: '{begrip}'")
        try:
            categorie, reasoning, scores = (
                await interface._determine_ontological_category(begrip, org, jur)
            )
            print(f"   ✅ Categorie: {categorie.value}")
            print(f"   📊 Scores: {scores}")
            print(f"   🔍 Reasoning: {reasoning[:50]}...")

            # Test score formatting
            score_text = " | ".join(
                [f"{cat}: {score:.2f}" for cat, score in scores.items()]
            )
            print(f"   📝 Formatted: {score_text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_ui_scores())
