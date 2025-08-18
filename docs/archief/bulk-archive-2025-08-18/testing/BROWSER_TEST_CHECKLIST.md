# Browser Test Checklist - DefinitieAgent

## 🚀 Start de Applicatie

```bash
streamlit run src/main.py
```

De app zou moeten openen op http://localhost:8501

## ✅ Test Checklist

### 1. **Eerste Pagina Load**
- [ ] App laadt zonder errors
- [ ] Je ziet "DefinitieAgent" titel

- [ ] Er zijn tabs zichtbaar
- [ ] Welke tabs zie je? (noteer namen)

### 2. **Definitie Generatie Tab**
- [ ] Is er een invoerveld voor "Begrip"?
- [ ] Zijn er dropdown/selectie velden voor context?
- [ ] Is er een "Genereer" button?

**Test met begrip: "authenticatie"**
- [ ] Vul "authenticatie" in bij begrip
- [ ] Selecteer een organisatie context (bijv. "Gemeente")
- [ ] Selecteer een afdeling (indien beschikbaar)
- [ ] Klik op "Genereer"

**Resultaat:**
- [ ] Krijg je een definitie?
- [ ] Zie je toetsresultaten?
- [ ] Welke toetsregels worden getoond?
- [ ] Zijn er rode/groene indicators?

### 3. **Voorbeelden Tab** (indien aanwezig)
- [ ] Worden er voorbeeldzinnen getoond?
- [ ] Kun je nieuwe voorbeelden genereren?

### 4. **Export Functionaliteit**
- [ ] Is er een export/download button?
- [ ] Werkt de TXT export?
- [ ] Bevat het bestand alle info?

### 5. **Error Scenarios**
Test met lege invoer:
- [ ] Wat gebeurt er als je geen begrip invult?
- [ ] Geeft de app een duidelijke foutmelding?

Test met speciale karakters:
- [ ] Probeer begrip: "test/begrip" of "test&test"
- [ ] Handelt de app dit goed af?

### 6. **AI Toetsing Details**
- [ ] Klik op toetsresultaten (indien uitklapbaar)
- [ ] Zie je gedetailleerde uitleg?
- [ ] Zijn de meldingen in het Nederlands?

## 🐛 Noteer Problemen

**UI Issues:**
- 

**Functionaliteit die niet werkt:**
- 

**Error messages:**
- 

**Onverwacht gedrag:**
- 

## 📸 Screenshots

Als je screenshots kunt maken van:
1. De hoofdpagina
2. Een gegenereerde definitie met toetsresultaten
3. Eventuele error messages

Zou dat heel waardevol zijn!

## 💬 Feedback

**Algemene indruk:**
- Is de UI intuïtief?
- Zijn de stappen logisch?
- Wat zou je verbeteren?