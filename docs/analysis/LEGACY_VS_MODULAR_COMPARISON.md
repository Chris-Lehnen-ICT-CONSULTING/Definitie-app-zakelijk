# Legacy vs Modulaire Architectuur Vergelijking

**Datum:** 2025-07-16  
**Status:** Gedetailleerde analyse voltooid

## Executive Summary

De nieuwe modulaire architectuur is **structureel superieur** maar **functioneel incompleet**. Er is een significante functionaliteitsverlies tijdens de migratie van legacy naar modulair. De applicatie draait voornamelijk op legacy code die via imports wordt gebruikt.

## 🔴 Kritieke Functionaliteit Gaps

### 1. Prompt Building Degradatie

#### Legacy Implementatie (`prompt_builder.py`)
```python
# Volledige prompt structuur met:
- ✅ Validatiematrix
- ✅ Contextverboden (dynamisch)
- ✅ Veelgemaakte fouten sectie
- ✅ Meervoud correctie
- ✅ Volledige toetsregels integratie
- ✅ Metadata sectie
```

#### Nieuwe Implementatie (`generation/definitie_generator.py`)
```python
# Beperkte prompt structuur:
- ❌ GEEN validatiematrix
- ⚠️ Basis contextverboden (recent toegevoegd)
- ❌ GEEN veelgemaakte fouten
- ❌ GEEN meervoud correctie
- ⚠️ Gedeeltelijke toetsregels
- ⚠️ Minimale metadata
```

### 2. Centrale Module Functionaliteit

| Feature | Legacy | Nieuw | Impact |
|---------|--------|-------|---------|
| UI Tabs | Volledig werkend | Skeleton | Hoog |
| Workflow | Geïntegreerd | Gefragmenteerd | Hoog |
| Session State | Consistent | Inconsistent | Medium |
| Database ops | Direct | Via repository | Laag |

### 3. Validatie Completeness

**Legacy:**
- 46 toetsregels actief in prompt
- Validatiematrix voor quality assurance
- Direct feedback naar prompt

**Nieuw:**
- Pattern matching alleen
- Geen semantische validatie
- Feedback loop incompleet

### 4. Ontbrekende UI Features

1. **Quality Control Tab**
   - Basis UI aanwezig
   - Functionaliteit ontbreekt

2. **Expert Review Tab**
   - UI bestaat
   - Backend niet geïmplementeerd

3. **Management Tab**
   - Volledig leeg
   - Geen functionaliteit

4. **Orchestration Tab**
   - Gedeeltelijk werkend
   - Integratie issues

### 5. Integratie Problemen

```
❌ Hybrid Context Engine → UI
❌ Web Lookup → Prompt Building
❌ Voorbeelden → Main Workflow
❌ Validators → Onderling
❌ Session State → Consistentie
```

## 🟡 Specifieke Feature Gaps

### Prompt Generatie Kwaliteit

**Ontbreekt in nieuwe versie:**

1. **Validatiematrix tabel**
   ```
   | Probleem | Afgedekt? | Toelichting |
   |----------|-----------|-------------|
   | Start met begrip | ✅ | ... |
   | Abstracte constructies | ✅ | ... |
   ```

2. **Veelgemaakte fouten sectie**
   - Begin niet met lidwoorden
   - Gebruik geen koppelwerkwoord
   - Vermijd containerbegrippen

3. **Dynamische contextverboden**
   - Alleen basis implementatie
   - Mist varianten detectie

### Database & Persistence

**Legacy:** Direct SQL queries
**Nieuw:** Repository pattern maar:
- Niet overal gebruikt
- Inconsistente implementatie
- Migrations outdated

### Web & Document Integration

**Legacy:** Geïntegreerd in prompt
**Nieuw:** 
- Modules bestaan
- Niet gekoppeld aan UI
- Resultaten worden niet gebruikt

## 🟢 Verbeteringen in Nieuwe Architectuur

1. **Modulariteit**
   - Betere code organisatie
   - Scheiding van verantwoordelijkheden

2. **Type Safety**
   - Type hints overal
   - Betere IDE support

3. **Async Support**
   - Modern async/await pattern
   - Event loop safe

4. **Testbaarheid**
   - In theorie beter testbaar
   - Modules kunnen geïsoleerd getest worden

## 📊 Functionaliteit Vergelijking Matrix

| Component | Legacy | Nieuw | Volledigheid |
|-----------|--------|-------|--------------|
| Prompt Builder | 100% | 60% | ⚠️ |
| Validatie | 100% | 40% | 🔴 |
| UI Functionaliteit | 100% | 30% | 🔴 |
| Database Ops | 100% | 80% | 🟡 |
| Voorbeelden | 80% | 90% | 🟢 |
| Web Lookup | 100% | 50% | ⚠️ |
| Toetsregels | 100% | 70% | 🟡 |

## 🎯 Herziene Prioriteiten: Features First

### Week 1: Make It Work
1. **UI Tabs Werkend**
   - Copy/paste legacy functionaliteit
   - Wire aan nieuwe modules
   - Manual testing per tab

2. **Prompt Kwaliteit Herstellen**
   - Validatiematrix direct overnemen
   - Veelgemaakte fouten toevoegen
   - Context handling completeren

3. **Integratie Pragmatisch**
   - Quick & dirty koppeling
   - Focus op werkend, niet perfect
   - Refactor komt later

### Week 2: Document Reality
1. **Wat werkt vastleggen**
2. **Architecture AS-IS tekenen**
3. **Manual test protocol maken**

### Week 3-4: Then Test
1. **Critical path tests**
2. **Integration tests**  
3. **NO refactoring yet**

## Conclusie

De migratie naar een modulaire architectuur is een goede strategische keuze, maar de implementatie is **significant incompleet**. De applicatie draait grotendeels op legacy code terwijl de nieuwe modules vaak alleen facades zijn. 

**Risico:** Zonder voltooiing van de migratie bestaat het risico dat de app in een "halfway house" blijft hangen met de nadelen van beide architecturen.

**Herziene Aanbeveling:** Pragmatische "Features First" aanpak:

1. **Week 1**: Maak ALLE features werkend (copy legacy code indien nodig)
2. **Week 2**: Documenteer wat je hebt
3. **Week 3-4**: Schrijf tests voor wat werkt
4. **Week 5-6**: Dan pas refactoren met test safety net

**Rationale**: Een werkende app zonder tests heeft meer waarde dan een half-werkende app met perfecte tests. Tests zijn een middel om werkende features te behouden, niet een doel op zich.