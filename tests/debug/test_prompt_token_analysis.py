#!/usr/bin/env python3
"""
Test script om te analyseren hoeveel tokens elke prompt module gebruikt.
Voor US-203: Prompt Token Optimization
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2
from services.definition_generator_context import EnrichedContext
import tiktoken

async def analyze_prompt_tokens():
    """Analyseer de token distributie in gegenereerde prompts."""

    # Maak test request
    request = GenerationRequest(
        begrip="Verweerder",
        organisatorische_context=["Rechtbank"],
        juridische_context=["Wetboek van Burgerlijke Rechtsvordering"],
        wettelijke_basis=["Artikel 1:2 BW"],
        ontologische_categorie="proces"
    )

    # Initialize service
    service = PromptServiceV2()

    # Build prompt
    result = await service.build_generation_prompt(request)

    print("=" * 80)
    print("PROMPT TOKEN ANALYSIS - US-203")
    print("=" * 80)

    # Token count met tiktoken (GPT-4 tokenizer)
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(result.text)

    print(f"\nTotaal aantal tokens: {len(tokens)}")
    print(f"Totaal aantal karakters: {len(result.text)}")
    print(f"Tokens/karakter ratio: {len(tokens)/len(result.text):.3f}")

    # Splits de prompt in secties om te zien welke delen veel tokens gebruiken
    sections = result.text.split("\n\n")

    print("\n" + "=" * 80)
    print("TOKEN DISTRIBUTIE PER SECTIE:")
    print("=" * 80)

    token_distribution = []
    for i, section in enumerate(sections):
        if section.strip():
            section_tokens = len(enc.encode(section))
            percentage = (section_tokens / len(tokens)) * 100

            # Eerste 100 karakters van de sectie voor identificatie
            preview = section[:100].replace("\n", " ")
            if len(section) > 100:
                preview += "..."

            token_distribution.append({
                'preview': preview,
                'tokens': section_tokens,
                'percentage': percentage,
                'chars': len(section)
            })

    # Sorteer op token count
    token_distribution.sort(key=lambda x: x['tokens'], reverse=True)

    # Print top 10 grootste secties
    print("\nTop 10 grootste token consumers:")
    for i, item in enumerate(token_distribution[:10], 1):
        print(f"\n{i}. {item['preview']}")
        print(f"   Tokens: {item['tokens']} ({item['percentage']:.1f}%)")
        print(f"   Karakters: {item['chars']}")

    # Module analyse
    print("\n" + "=" * 80)
    print("MODULE IDENTIFICATIE IN PROMPT:")
    print("=" * 80)

    modules = [
        "semantic_categorisation", "template", "expertise", "grammar",
        "metrics", "output_specification", "structure_rules", "integrity_rules",
        "error_prevention", "definition_task", "context_awareness",
        "arai_rules", "con_rules", "ess_rules", "sam_rules", "ver_rules"
    ]

    for module in modules:
        # Zoek naar indicaties van deze module in de prompt
        module_indicators = [
            f"## {module}",
            f"### {module}",
            module.upper(),
            module.replace("_", " ").title()
        ]

        found = False
        for indicator in module_indicators:
            if indicator in result.text:
                found = True
                break

        if found:
            print(f"✓ {module} module gevonden")

    # Zoek naar duplicaties
    print("\n" + "=" * 80)
    print("DUPLICATIE ANALYSE:")
    print("=" * 80)

    # Splits in regels voor duplicatie detectie
    lines = result.text.split("\n")
    line_counts = {}
    for line in lines:
        cleaned = line.strip()
        if len(cleaned) > 20:  # Alleen significante regels
            line_counts[cleaned] = line_counts.get(cleaned, 0) + 1

    duplicates = [(line, count) for line, count in line_counts.items() if count > 1]
    duplicates.sort(key=lambda x: x[1], reverse=True)

    if duplicates:
        print(f"\nGevonden {len(duplicates)} gedupliceerde regels:")
        for line, count in duplicates[:5]:
            preview = line[:80] + "..." if len(line) > 80 else line
            print(f"  {count}x: {preview}")
    else:
        print("\nGeen significante duplicaties gevonden")

    # Optimalisatie suggesties
    print("\n" + "=" * 80)
    print("OPTIMALISATIE SUGGESTIES:")
    print("=" * 80)

    target_tokens = 3000
    reduction_needed = len(tokens) - target_tokens
    reduction_percentage = (reduction_needed / len(tokens)) * 100

    print(f"\nHuidige tokens: {len(tokens)}")
    print(f"Target tokens: {target_tokens}")
    print(f"Reductie nodig: {reduction_needed} tokens ({reduction_percentage:.1f}%)")

    print("\nVoorgestelde optimalisaties:")
    print("1. Consolideer overlappende validatieregels (geschat -1500 tokens)")
    print("2. Implementeer dynamische module selectie (geschat -800 tokens)")
    print("3. Gebruik context-aware regel filtering (geschat -1000 tokens)")
    print("4. Comprimeer instructie formaat (geschat -600 tokens)")
    print("5. Cache herbruikbare prompt secties (geschat -500 tokens)")

    total_potential_savings = 4400
    print(f"\nTotaal potentiële besparing: {total_potential_savings} tokens")
    print(f"Verwacht resultaat: {len(tokens) - total_potential_savings} tokens")

    return result

if __name__ == "__main__":
    result = asyncio.run(analyze_prompt_tokens())