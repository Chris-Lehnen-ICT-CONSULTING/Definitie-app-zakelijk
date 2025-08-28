# Module 1: Core Instructions - Requirements Based Implementation

## Analyse van Requirements

### Uit Legacy PromptBuilder
De originele implementatie bevat:
```python
# Basis rol en instructie (regels 155-158)
"Je bent een expert in beleidsmatige definities voor overheidsgebruik."
"Formuleer een definitie in één enkele zin, zonder toelichting."

# Woordsoort-specifiek advies (regels 160-172)
- Werkwoord: "definieer het dan als proces of activiteit"
- Deverbaal: "beschrijf het dan als uitkomst van een proces"
- Anders: "Gebruik een zakelijke en generieke stijl"
```

### Uit Service Architectuur Requirements
1. **ESS-02 Compliance**: Ontologische categorieën moeten ondersteund worden
2. **Modulariteit**: Elke module moet zelfstandig testbaar zijn
3. **Performance**: Totale prompt generatie < 5 seconden
4. **Karakter Management**: Dynamisch beheer van beschikbare ruimte

### Uit Evaluation Report
Ontbrekende elementen die toegevoegd moeten worden:
- ✅ Nederlandse overheidscontext specificatie
- ✅ Kwaliteitscriteria
- ✅ Output format specificaties
- ✅ Karakter limieten
- ✅ Waarschuwingen voor veelgemaakte fouten
- ✅ Gestructureerde opbouw

## Voorgestelde Implementatie

### Versie 1: Minimale Uitbreiding (Backwards Compatible)
```python
def _build_role_and_basic_rules_v1(self, begrip: str) -> str:
    """Minimale uitbreiding die backwards compatible blijft."""
    return """Je bent een ervaren Nederlandse expert in beleidsmatige definities voor overheidsgebruik.
Formuleer een definitie in één enkele zin, zonder toelichting.
Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip.

Let op: De definitie moet geschikt zijn voor officiële overheidsdocumenten."""
```

### Versie 2: Gebalanceerde Implementatie (Aanbevolen)
```python
def _build_role_and_basic_rules_v2(self, begrip: str, metadata: Dict[str, Any]) -> str:
    """Gebalanceerde implementatie met essentiële uitbreidingen."""

    # Bepaal woordsoort voor specifiek advies
    woordsoort = self._bepaal_woordsoort(begrip)

    # Basis instructies
    instructions = [
        "Je bent een ervaren Nederlandse expert in beleidsmatige definities voor overheidsgebruik.",
        "",
        "**Je opdracht**: Formuleer een heldere, eenduidige definitie in één enkele zin, zonder toelichting.",
        ""
    ]

    # Woordsoort-specifiek advies (uit legacy)
    if woordsoort == "werkwoord":
        instructions.append("Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit.")
    elif woordsoort == "deverbaal":
        instructions.append("Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces.")
    else:
        instructions.append("Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip.")

    # Kwaliteitseisen
    instructions.extend([
        "",
        "**Vereisten**:",
        "• Begin NIET met lidwoorden (de, het, een)",
        "• Gebruik geen cirkelredeneringen",
        "• Wees volledig maar beknopt",
        "• Geschikt voor officiële overheidsdocumenten"
    ])

    # Karakter waarschuwing indien relevant
    max_chars = metadata.get('max_chars', 4000)
    if max_chars < 2500:
        instructions.append(f"• ⚠️ Maximaal {max_chars - 1500} karakters beschikbaar voor de definitie")

    return "\n".join(instructions)
```

### Versie 3: Volledige Implementatie (Maximale Features)
```python
def _build_role_and_basic_rules_v3(self, begrip: str, context: EnrichedContext) -> str:
    """Volledige implementatie met alle features uit requirements."""

    sections = []

    # 1. Rol definitie
    sections.append(self._build_role_definition())

    # 2. Opdracht specificatie
    sections.append(self._build_task_specification(begrip))

    # 3. Woordsoort-specifiek advies
    sections.append(self._build_word_type_guidance(begrip))

    # 4. Definitie vereisten
    sections.append(self._build_definition_requirements())

    # 5. Kwaliteitscriteria
    sections.append(self._build_quality_criteria())

    # 6. Waarschuwingen en limieten
    sections.append(self._build_warnings_and_limits(context))

    return "\n\n".join(filter(None, sections))
```

## Implementatie Keuze

### Aanbeveling: Versie 2 (Gebalanceerde)
**Waarom:**
1. Behoudt kernfunctionaliteit uit legacy
2. Voegt essentiële ontbrekende elementen toe
3. Blijft beknopt (~400-600 karakters)
4. Backwards compatible qua output
5. Makkelijk uit te breiden naar v3 indien nodig

### Vergelijking

| Aspect | Huidige | V1 | V2 | V3 |
|--------|---------|----|----|----|
| Karakters | 209 | ~280 | ~600 | ~1200 |
| Woordsoort advies | ❌ | ❌ | ✅ | ✅ |
| Kwaliteitscriteria | ❌ | ❌ | ✅ | ✅ |
| Karakter limieten | ❌ | ❌ | ✅ | ✅ |
| Structuur | Plat | Plat | Licht | Volledig |
| Legacy compatible | ✅ | ✅ | ✅ | ⚠️ |

## Implementatie Plan

### Fase 1: Direct Implementeren
1. Vervang huidige `_build_role_and_basic_rules` met V2
2. Voeg `_bepaal_woordsoort` helper methode toe
3. Test met bestaande test cases

### Fase 2: A/B Testing
1. Feature flag voor oude vs nieuwe versie
2. Vergelijk output kwaliteit op 100 test begrippen
3. Meet impact op validatie scores

### Fase 3: Optimalisatie
1. Fine-tune op basis van feedback
2. Overweeg upgrade naar V3 voor specifieke categorieën
3. Documenteer best practices

## Code Voorbeeld

```python
def _build_role_and_basic_rules(self, begrip: str) -> str:
    """
    Component 1: Expert rol en fundamentele schrijfregels.

    Implementeert requirements uit legacy prompt builder met moderne structuur.
    """
    # Extract metadata indien beschikbaar
    metadata = getattr(self, '_current_metadata', {})
    woordsoort = self._bepaal_woordsoort(begrip)

    # Bouw instructies volgens V2 specificatie
    lines = [
        "Je bent een ervaren Nederlandse expert in beleidsmatige definities voor overheidsgebruik.",
        "",
        "**Je opdracht**: Formuleer een heldere, eenduidige definitie in één enkele zin, zonder toelichting.",
        ""
    ]

    # Woordsoort-specifiek advies (legacy compatibility)
    if woordsoort == "werkwoord":
        lines.append("Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit.")
    elif woordsoort == "deverbaal":
        lines.append("Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces.")
    else:
        lines.append("Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip.")

    # Essentiële vereisten
    lines.extend([
        "",
        "**Vereisten**:",
        "• Begin NIET met lidwoorden (de, het, een)",
        "• Gebruik geen cirkelredeneringen",
        "• Wees volledig maar beknopt",
        "• Geschikt voor officiële overheidsdocumenten"
    ])

    # Dynamische karakter waarschuwing
    max_chars = metadata.get('max_chars', 4000)
    available = max_chars - 1500  # Schat overige prompt onderdelen
    if available < 2500:
        lines.append(f"• ⚠️ Maximaal {available} karakters beschikbaar voor de definitie")

    return "\n".join(lines)

def _bepaal_woordsoort(self, begrip: str) -> str:
    """
    Bepaal woordsoort van begrip (uit legacy prompt_builder).

    Returns:
        'werkwoord', 'deverbaal', of 'overig'
    """
    begrip_lower = begrip.lower()

    # Werkwoord detectie
    werkwoord_suffixen = ['eren', 'elen', 'enen', 'igen', 'iken', 'ijven']
    if any(begrip_lower.endswith(suffix) for suffix in werkwoord_suffixen):
        return "werkwoord"

    # Deverbaal detectie (zelfstandig naamwoord afgeleid van werkwoord)
    deverbaal_suffixen = ['ing', 'atie', 'age', 'ment', 'tie', 'sie']
    if any(begrip_lower.endswith(suffix) for suffix in deverbaal_suffixen):
        return "deverbaal"

    return "overig"
```

## Success Criteria

1. **Output Kwaliteit**: Definities voldoen vaker aan alle toetsregels (+15%)
2. **Consistentie**: Minder variatie in output kwaliteit (<5%)
3. **Performance**: Geen significante impact op generatie tijd (<100ms)
4. **Backwards Compatible**: Bestaande tests blijven slagen
5. **Maintainability**: Code is beter gestructureerd en testbaar

---
*Document gemaakt: 2025-08-26*
*Gebaseerd op: Legacy code analyse + Requirements documenten*
