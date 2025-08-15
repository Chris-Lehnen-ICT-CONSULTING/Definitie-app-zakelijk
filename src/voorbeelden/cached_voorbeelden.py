"""
Cached version of voorbeelden (examples) generation.
This module provides intelligent caching for all example generation functions.
"""

import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from utils.cache import cache_example_generation, cache_synonym_generation

# Load environment and initialize OpenAI client
load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@cache_example_generation(ttl=1800)  # Cache for 30 minutes
def genereer_voorbeeld_zinnen(
    begrip: str, definitie: str, context_dict: Dict[str, List[str]]
) -> List[str]:
    """Generate example sentences with caching."""
    prompt = (
        f"Geef 2 tot 3 korte voorbeeldzinnen waarin het begrip '{begrip}' "
        "op een duidelijke manier wordt gebruikt.\n"
        "Gebruik onderstaande contexten alleen als achtergrond, maar noem ze niet letterlijk:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        blob = resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren korte voorbeelden: {e}"]

    # Split on lines and remove numbering
    zinnen: List[str] = []
    for line in blob.splitlines():
        # If AI uses "1. …" or "- …", strip it off
        zin = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if zin:
            zinnen.append(zin)
    # Fallback: return entire blob if no separate lines found
    return zinnen or [blob]


@cache_example_generation(ttl=1800)  # Cache for 30 minutes
def genereer_praktijkvoorbeelden(
    begrip: str, definitie: str, context_dict: Dict[str, List[str]]
) -> List[str]:
    """Generate practice examples with caching."""
    prompt = (
        f"Geef 2 tot 3 praktijkvoorbeelden waarin het begrip '{begrip}' "
        "in een realistische situatie wordt toegepast.\n"
        "Gebruik onderstaande contexten voor realisme, maar noem ze niet letterlijk:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}\n\n"
        f"Definitie ter referentie: {definitie}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=400,
        )
        blob = resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren praktijkvoorbeelden: {e}"]

    # Split into separate examples
    voorbeelden: List[str] = []
    for line in blob.splitlines():
        # Remove numbering and clean up
        voorbeeld = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if voorbeeld and len(voorbeeld) > 10:  # Filter out very short lines
            voorbeelden.append(voorbeeld)

    return voorbeelden or [blob]


@cache_example_generation(ttl=1800)  # Cache for 30 minutes
def genereer_tegenvoorbeelden(
    begrip: str, definitie: str, context_dict: Dict[str, List[str]]
) -> List[str]:
    """Generate counter-examples with caching."""
    prompt = (
        f"Geef 2 tot 3 tegenvoorbeelden die NIET onder het begrip '{begrip}' vallen, "
        "maar wel verwant zijn of verwarrend kunnen zijn.\n"
        "Leg kort uit waarom elk voorbeeld NIET onder de definitie valt.\n\n"
        f"Definitie: {definitie}\n\n"
        f"Context (alleen voor begrip): {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=300,
        )
        blob = resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return [f"❌ Fout bij genereren tegenvoorbeelden: {e}"]

    # Split into separate counter-examples
    tegenvoorbeelden: List[str] = []
    for line in blob.splitlines():
        # Remove numbering and clean up
        voorbeeld = re.sub(r"^\s*(?:\d+\.|-)\s*", "", line).strip()
        if voorbeeld and len(voorbeeld) > 10:  # Filter out very short lines
            tegenvoorbeelden.append(voorbeeld)

    return tegenvoorbeelden or [blob]


@cache_synonym_generation(ttl=7200)  # Cache for 2 hours
def genereer_synoniemen(begrip: str, context_dict: Dict[str, List[str]]) -> str:
    """Generate synonyms with caching."""
    prompt = (
        f"Geef maximaal 5 synoniemen voor het begrip '{begrip}', "
        f"relevant binnen de context van overheidsgebruik.\n"
        f"Gebruik onderstaande contexten als achtergrond. Geef de synoniemen als een lijst, zonder toelichting:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"❌ Fout bij genereren synoniemen: {e}"


@cache_synonym_generation(ttl=7200)  # Cache for 2 hours
def genereer_antoniemen(begrip: str, context_dict: Dict[str, List[str]]) -> str:
    """Generate antonyms with caching."""
    prompt = (
        f"Geef maximaal 5 antoniemen voor het begrip '{begrip}', "
        f"binnen de context van overheidsgebruik.\n"
        f"Gebruik onderstaande contexten alleen als achtergrond. Geef de antoniemen als een lijst, zonder toelichting:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"❌ Fout bij genereren antoniemen: {e}"


@cache_synonym_generation(ttl=3600)  # Cache for 1 hour
def genereer_toelichting(begrip: str, context_dict: Dict[str, List[str]]) -> str:
    """Generate explanation with caching."""
    prompt = (
        f"Geef een korte toelichting op de betekenis en toepassing van het begrip '{begrip}', "
        f"zoals het zou kunnen voorkomen in overheidsdocumenten.\n"
        f"Gebruik de contexten hieronder alleen als achtergrond en noem ze niet letterlijk:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"❌ Fout bij genereren toelichting: {e}"
