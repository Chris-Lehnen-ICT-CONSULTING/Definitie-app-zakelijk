# 🚨 ISSUE: Ontbrekende Toetsregel INT-05

**Issue Date**: 2025-01-14  
**Discovered By**: Code Review - DefinitionValidator  
**Severity**: Medium  
**Status**: Open

## Probleem Beschrijving

Tijdens de code review van DefinitionValidator is geconstateerd dat toetsregel INT-05 ontbreekt.

### Verwachting vs Realiteit:
- **Verwacht** (volgens MASTER-TODO.md): 46 toetsregels
- **Werkelijk aanwezig**: 45 toetsregels
- **Ontbreekt**: INT-05

## Onderzoek

### Aanwezige INT regels:
```
INT-01: Compacte en begrijpelijke zin
INT-02: [naam onbekend]
INT-03: [naam onbekend]
INT-04: [naam onbekend]
INT-06: [naam onbekend]
INT-07: [naam onbekend]
INT-08: [naam onbekend]
INT-09: [naam onbekend]
INT-10: [naam onbekend]
```

### Gevonden Feiten:
1. INT-05 bestaat niet als bestand (geen INT-05.json of INT-05.py)
2. Geen referenties naar INT-05 in de codebase
3. DISPATCHER in ai_toetser/core.py heeft geen INT-05 entry
4. Geen skip van INT-04 naar INT-06 documentatie gevonden

## Mogelijke Oorzaken

1. **Design beslissing**: INT-05 is bewust weggelaten
2. **Merge/consolidatie**: INT-05 is samengevoegd met andere regel
3. **Vergeten**: INT-05 is per ongeluk overgeslagen
4. **Hernummering**: Mogelijk was er ooit een INT-05 die later anders genummerd is

## Impact

- DefinitionValidator werkt correct met 45 regels
- Mogelijk mist er een belangrijke validatie check
- Inconsistentie tussen documentatie en implementatie

## Aanbevolen Acties

1. **Onderzoek git history** voor INT-05 references
2. **Check met team** of INT-05 bewust is weggelaten
3. **Update documentatie** OF **implementeer INT-05**
4. **Review andere categories** voor mogelijke missing rules

## Workaround

Geen workaround nodig - systeem functioneert met 45 regels.

---
*Dit issue is gedocumenteerd tijdens de systematische code review van alle componenten.*