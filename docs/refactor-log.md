# Refactor Log - Prompt Structuur

## 2025-09-03: Prompt.txt Refactoring

### Gedetecteerde Problemen

**Bestand**: `/Users/chrislehnen/Projecten/Definitie-app/logs/prompt.txt`

1. **Duplicatie - "Start niet met..." regels (432-473)**
   - 42 regels met hetzelfde patroon
   - Code smell: Excessive duplication
   - Impact: ~400 onnodige tokens

2. **Duplicatie - ARAI-02 familie (119-140)**
   - Dezelfde regel 3x herhaald met kleine variaties
   - ARAI-02, ARAI-02SUB1, ARAI-02SUB2
   - Code smell: Near-duplicate code

3. **Tegenstrijdigheid - Haakjes gebruik**
   - Regel 14: "Geen haakjes voor toelichtingen"
   - Regel 53-61: Haakjes WEL gebruiken voor afkortingen
   - Code smell: Inconsistent business rules

4. **Tegenstrijdigheid - Context verwerking**
   - Regel 63-64: Context ZONDER expliciete benoeming
   - Regel 178-186: CON-01 regel herhaalt dit uitgebreid
   - Code smell: Redundant specifications

5. **Triplicatie - Ontologie uitleg**
   - Regel 66-74: Eerste uitleg
   - Regel 75-100: TYPE specifieke uitleg
   - Regel 202-204: ESS-02 herhaalt dit nogmaals
   - Code smell: Multiple explanations of same concept

### Voorgestelde Refactoring

Van 553 regels (~7250 tokens) naar ~150 regels (<2000 tokens).

#### Refactoring Strategie
1. **Extract Pattern**: Groepeer alle "start niet met" in één compacte regel
2. **Consolidate Duplicates**: Voeg ARAI-02 varianten samen
3. **Resolve Contradictions**: Maak haakjes regel eenduidig
4. **Remove Redundancy**: Één keer ontologie uitleggen
5. **Simplify Structure**: Hiërarchische indeling met prioriteit

### Toegepaste Refactoring Technieken
- Pattern consolidation
- Rule deduplication
- Contradiction resolution
- Hierarchical restructuring
- Token optimization

### Resultaat
Zie `prompt_refactored.txt` voor de nieuwe structuur.
Token reductie: ~72% (van 7250 naar <2000)
