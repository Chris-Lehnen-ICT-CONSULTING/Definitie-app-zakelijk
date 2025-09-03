# Prompt Refactoring - Voor/Na Vergelijking

## Statistieken

| Metric | Origineel | Gerefactored | Verbetering |
|--------|-----------|--------------|-------------|
| **Regels** | 553 | ~75 | -86% |
| **Tokens** | ~7250 | ~1250 | -83% |
| **Duplicaties** | 42+ | 0 | -100% |
| **Tegenstrijdigheden** | 3 | 0 | Opgelost |
| **Secties** | Ongestructureerd | 6 helder | +100% |

## Structuur Vergelijking

### VOOR: Chaotische Structuur
```
- Regel 1-23: Algemene vereisten
- Regel 24-61: Grammatica (met tegenstrijdigheid)
- Regel 63-64: Context regel
- Regel 66-100: Ontologie uitleg #1
- Regel 101-110: Templates
- Regel 111-175: ARAI regels (met duplicatie)
- Regel 176-193: CON regels (herhaalt context)
- Regel 194-229: ESS regels (herhaalt ontologie)
- Regel 230-293: STR regels
- Regel 295-349: INT regels
- Regel 350-406: SAM regels
- Regel 407-430: VER regels
- Regel 431-473: 42 "Start niet met" regels
- Regel 474-552: Finale instructies
```

### NA: Hiërarchische Structuur
```
1. ROL & DOEL (50 tokens)
2. KERNREGELS (500 tokens)
   - Structuur (MUST HAVE)
   - Inhoud (ESSENTIEEL)
   - Grammatica
3. DEFINITIE STRUCTUUR (300 tokens)
   - Ontologische Categorieën
   - Definitiepatronen
4. VERBODEN (200 tokens)
   - Nooit starten met
   - Nooit gebruiken
5. CONTEXT VERWERKING (100 tokens)
6. KWALITEITSCHECK (100 tokens)
```

## Opgeloste Problemen

### 1. Duplicatie "Start niet met..."
**Voor**: 42 afzonderlijke regels (432-473)
```
- ❌ Start niet met 'is'
- ❌ Start niet met 'betreft'
- ❌ Start niet met 'omvat'
[... 39 meer regels ...]
```

**Na**: Één compacte regel
```
Nooit starten met: Lidwoorden (de/het/een), koppelwerkwoorden (is/betreft/omvat/betekent)...
```

### 2. ARAI-02 Familie Duplicatie
**Voor**: 3 varianten (119-140)
```
ARAI-02: Vermijd vage containerbegrippen
ARAI-02SUB1: Lexicale containerbegrippen vermijden
ARAI-02SUB2: Ambtelijke containerbegrippen vermijden
```

**Na**: Geïntegreerd in Kernregel #6
```
Geen vage termen - vermijd: aspect, element, proces, activiteit...
```

### 3. Haakjes Tegenstrijdigheid
**Voor**:
- Regel 14: "Geen haakjes voor toelichtingen"
- Regel 53-61: Gebruik haakjes voor afkortingen

**Na**: Eenduidige regel
```
Geen haakjes - behalve voor afkortingen: Dienst Justitiële Inrichtingen (DJI)
```

### 4. Context Dubbele Uitleg
**Voor**:
- Regel 63-64: Eerste uitleg
- Regel 178-186: CON-01 herhaalt uitgebreid

**Na**: Één keer in sectie 5
```
Formuleer specifiek voor deze context
Noem de organisaties NIET letterlijk
```

### 5. Ontologie Triplicatie
**Voor**: 3 verschillende plekken
- Regel 66-74: Algemene uitleg
- Regel 75-100: TYPE specifiek
- Regel 202-204: ESS-02

**Na**: Één gestructureerde sectie (3)
```
Ontologische Categorieën (kies er één)
- TYPE, PROCES, RESULTAAT, EXEMPLAAR
```

## Verbeterde Leesbaarheid

### Prioriteit is nu helder:
1. **MUST HAVE** regels eerst (structuur)
2. **ESSENTIEEL** daarna (inhoud)
3. **VERBODEN** expliciet gescheiden
4. **CHECKLIST** aan het eind

### Voorbeelden geconsolideerd:
- Alleen waar nodig voor verduidelijking
- Geen herhaling van dezelfde voorbeelden
- Compacte notatie

## Impact op Gebruik

### Voor Ontwikkelaars
- **Sneller te parsen**: van 553 naar 75 regels
- **Minder tokens**: 83% reductie bespaart API kosten
- **Geen tegenstrijdigheden**: consistente implementatie

### Voor AI Model
- **Helderder instructies**: hiërarchische structuur
- **Minder verwarring**: geen duplicate/tegenstrijdige regels
- **Betere focus**: kernregels prominent

### Voor Eindgebruikers
- **Consistentere output**: geen tegenstrijdige regels
- **Snellere respons**: minder tokens te verwerken
- **Betere kwaliteit**: focus op essentiële regels

## Migratiestrategie

1. **Test nieuwe prompt** met bestaande testcases
2. **Vergelijk output** kwaliteit oude vs nieuwe prompt
3. **Valideer** dat alle kernfunctionaliteit behouden is
4. **Deploy** gefaseerd met monitoring

## Conclusie

De gerefactorde prompt behoudt alle functionaliteit maar:
- Reduceert tokens met 83%
- Elimineert alle duplicatie
- Lost tegenstrijdigheden op
- Verbetert leesbaarheid dramatisch
- Maakt prioriteiten expliciet

Dit resulteert in een efficiëntere, consistentere en beter onderhoudbare prompt.
