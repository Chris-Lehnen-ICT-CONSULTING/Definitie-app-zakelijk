# 🧹 Opschoning Module

Deze module verzorgt het opschonen van AI-gegenereerde definities volgens de Nederlandse wetgevingstechniek.

## 📁 Bestanden

### 1. `opschoning.py` (Basis versie)
- **Status**: Originele implementatie, wordt indirect gebruikt
- **Functie**: Verwijdert verboden woorden en formatteert definities
- **Wanneer gebruikt**: Via `opschoning_enhanced.py`

### 2. `opschoning_enhanced.py` (Moderne versie)
- **Status**: ACTIEF - Dit wordt ALTIJD gebruikt
- **Functie**: Handelt GPT-4 responses + roept basis opschoning aan
- **Wanneer gebruikt**: Door `CleaningService` voor ALLE opschoning

### 3. `verboden_woorden.json`
- **Status**: Configuratie bestand
- **Functie**: Definieert welke woorden/frasen verwijderd moeten worden

## 🔄 Call Flow

```
UI roept aan → ServiceFactory.generate_definition()
                    ↓
             DefinitionOrchestrator._clean_definition()
                    ↓
             CleaningService.clean_text()
                    ↓
             opschoning_enhanced.opschonen_enhanced()
                    ↓
             [Verwijder GPT headers indien aanwezig]
                    ↓
             opschoning.opschonen()
                    ↓
             [Verwijder verboden woorden + formatting]
                    ↓
             Opgeschoonde definitie terug naar UI
```

## 📋 Opschoningsregels

### Verboden Beginwoorden
| Type | Voorbeelden | Reden |
|------|-------------|-------|
| Koppelwerkwoorden | is, zijn, wordt, omvat, betekent | Definities moeten direct beginnen |
| Lidwoorden | de, het, een | Nederlandse wetgevingstechniek |
| Verboden frasen | proces waarbij, handeling die | Te vaag/indirect |
| Overbodige constructies | een belangrijk, een essentieel | Niet informatief |

### Opschoningspatronen

#### 1. **Patroon A: Woord aan begin**
```
"is een uitspraak" → "uitspraak" → "Uitspraak."
```

#### 2. **Patroon B: Circulaire definitie**
```
"Vonnis is een beslissing" → "beslissing" → "Beslissing."
    ^begrip  ^verboden woord
```

#### 3. **Patroon C: Begrip met leesteken**
```
"Vonnis: een uitspraak" → "een uitspraak" → "uitspraak" → "Uitspraak."
```

#### 4. **GPT Header Verwijdering** (alleen enhanced)
```
"Ontologische categorie: resultaat
Vonnis is een uitspraak van de rechter"
↓
"Vonnis is een uitspraak van de rechter"
↓
"uitspraak van de rechter"
↓
"Uitspraak van de rechter."
```

## 🧪 Voorbeelden

### Input → Output

| Input | Begrip | Output | Toegepaste Regels |
|-------|--------|--------|-------------------|
| "is een document" | akte | "Document." | Verwijder "is een", formatting |
| "de rechterlijke uitspraak" | vonnis | "Rechterlijke uitspraak." | Verwijder "de", formatting |
| "vonnis betekent een beslissing" | vonnis | "Beslissing." | Circulaire definitie |
| "Ontologische categorie: type<br>het juridisch document" | akte | "Juridisch document." | GPT header + "het" |
| "proces waarbij partijen" | mediation | "Partijen" of origineel* | "proces waarbij" verwijderd |

*Als na alle opschoning niets overblijft, wordt het origineel behouden.

## ⚙️ Configuratie

De verboden woorden worden geladen uit `config/verboden_woorden.json`:

```json
{
  "verboden_woorden": [
    "is", "omvat", "betekent", "verwijst naar",
    "de", "het", "een",
    "proces waarbij", "handeling die", "vorm van",
    "een belangrijk", "een essentieel"
  ]
}
```

## 🔧 Uitbreiden

Om nieuwe opschoningsregels toe te voegen:

1. **Voor nieuwe verboden woorden**: Voeg toe aan `config/verboden_woorden.json`
2. **Voor nieuwe GPT metadata**: Update `extract_definition_from_gpt_response()` in `opschoning_enhanced.py`
3. **Voor nieuwe patronen**: Voeg regex toe in `opschonen()` in `opschoning.py`

## 📊 Monitoring

De `CleaningService` houdt bij:
- Of opschoning is toegepast (`was_cleaned`)
- Welke regels zijn toegepast (`applied_rules`)
- Welke verbeteringen zijn gemaakt (`improvements`)

Deze metadata wordt opgeslagen bij de definitie en getoond in de UI.
