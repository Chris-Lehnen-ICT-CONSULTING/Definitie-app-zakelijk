# Volledige Temperature Analyse voor Voorbeelden Modules

## Samenvatting

Er zijn 4 verschillende voorbeelden modules met verschillende temperature strategieën:

### 1. **voorbeelden.py** (Origineel/Legacy)
- **Status**: ✅ ACTIEF gebruikt door `definitie_agent.py`
- **Temperature Strategie**: Uniform 0.5 voor alles
- **Functies**: Alleen basis functies (voorbeeld zinnen, praktijk, tegen)

### 2. **cached_voorbeelden.py**
- **Status**: ❌ NIET actief gebruikt
- **Temperature Strategie**: Gevarieerd per functie type
- **Functies**: Uitgebreid met synoniemen, antoniemen, toelichting

### 3. **async_voorbeelden.py**
- **Status**: ❌ NIET actief gebruikt
- **Temperature Strategie**: Identiek aan cached_voorbeelden.py
- **Model**: Hardcoded "gpt-4" voor meeste functies

### 4. **unified_voorbeelden.py**
- **Status**: ✅ ACTIEF gebruikt door `definition_orchestrator.py`
- **Temperature Strategie**: Uniform default 0.5 (configureerbaar)
- **Probleem**: Gebruikt NIET de gevarieerde temperatures!

## Temperature Business Logica (uit cached/async modules)

| Functie Type | Temperature | Rationale |
|--------------|-------------|-----------|
| Synoniemen | 0.2 | Lage creativiteit, hoge precisie voor taalkundige correctheid |
| Antoniemen | 0.2 | Lage creativiteit, exacte tegenstellingen gewenst |
| Toelichting | 0.3 | Gemiddeld-laag voor informatieve, consistente uitleg |
| Voorbeeldzinnen | 0.5 | Gemiddeld voor balans tussen variatie en coherentie |
| Praktijkvoorbeelden | 0.6 | Hoger voor creatieve, realistische scenarios |
| Tegenvoorbeelden | 0.6 | Hoger voor diverse, verrassende tegenvoorbeelden |

## Probleem Analyse

### Inconsistentie 1: Legacy vs Modern
- `definitie_agent.py` gebruikt nog steeds de oude `voorbeelden.py` (uniform 0.5)
- `definition_orchestrator.py` gebruikt `unified_voorbeelden.py` (ook uniform 0.5)
- Niemand gebruikt de modules met gevarieerde temperatures

### Inconsistentie 2: Verloren Business Logica
De doordachte temperature variaties uit `cached_voorbeelden.py` zijn verloren gegaan in:
- De originele `voorbeelden.py` (heeft ze nooit gehad)
- De nieuwe `unified_voorbeelden.py` (niet geïmplementeerd)

### Code Bewijs
In `unified_voorbeelden.py` worden alle convenience functies aangemaakt zonder temperature te specificeren:
```python
request = ExampleRequest(
    begrip=begrip,
    definitie=definitie,
    context_dict=context_dict,
    example_type=ExampleType.SYNONYMS,
    generation_mode=mode,
    max_examples=5,  # Wel max_examples, maar geen temperature!
)
```

## Aanbevelingen

### 1. Korte Termijn Fix
Update `unified_voorbeelden.py` om de juiste temperatures te gebruiken:

```python
# In de convenience functies
def genereer_synoniemen(...):
    request = ExampleRequest(
        ...
        temperature=0.2,  # Voeg dit toe!
        ...
    )

def genereer_praktijkvoorbeelden(...):
    request = ExampleRequest(
        ...
        temperature=0.6,  # Voeg dit toe!
        ...
    )
# etc.
```

### 2. Lange Termijn Strategie
1. Migreer `definitie_agent.py` naar `unified_voorbeelden.py`
2. Verwijder legacy `voorbeelden.py`
3. Archive `cached_voorbeelden.py` en `async_voorbeelden.py`
4. Centraliseer temperature configuratie in een config file

### 3. Temperature Configuratie Voorstel
```python
TEMPERATURE_CONFIG = {
    ExampleType.SYNONYMS: 0.2,
    ExampleType.ANTONYMS: 0.2,
    ExampleType.EXPLANATION: 0.3,
    ExampleType.SENTENCE: 0.5,
    ExampleType.PRACTICAL: 0.6,
    ExampleType.COUNTER: 0.6,
}
```

## Conclusie

De verschillende temperatures zijn een **bewuste en slimme design keuze**, maar deze is **verloren gegaan** in de huidige implementatie. Beide actief gebruikte modules (`voorbeelden.py` en `unified_voorbeelden.py`) gebruiken een uniforme temperature van 0.5, wat suboptimaal is voor de verschillende use cases.
