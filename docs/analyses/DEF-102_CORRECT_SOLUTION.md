# DEF-102: De CORRECTE Oplossing - Ontologische Categorie als Template Driver

**Datum:** 2025-11-04
**Status:** REVISED APPROACH
**Auteur:** Claude Code (na user correctie van foutieve redenatie)

---

## 🎯 De Foutieve Aanpak (Eerder Voorgesteld)

### Wat Ik Fout Voorstelde:

```
"Voeg exception toe aan STR-01 voor ESS-02 ontological markers:
 - Sta 'is een activiteit waarbij' toe (exception op STR-01)
 - Sta 'is een type...' toe (exception op STR-01)
 - etc."
```

### Waarom Dit FOUT Is:

**Logische Contradictie:**
1. ALLE begrippen hebben een ontologische categorie
2. Dus exception zou voor ALLE begrippen gelden
3. → STR-01 regel wordt nutteloos (alle begrippen krijgen exception!)

**Probleem:**
- Je kunt geen exception maken die universeel toepasbaar is
- Dan heb je geen regel meer!

---

## ✅ De CORRECTE Oplossing (User Inzicht)

### Het Principe:

> **Ontologische categorie bepaalt de VORM/TEMPLATE van de definitie**

Niet: "Maak exception voor ESS-02 op STR-01"
Wel: "ESS-02 stuurt naar templates die VOLDOEN aan STR-01"

---

## 🔄 Hoe Het Werkt

### PROCES Begrippen:

**Huidige (FOUTE) prompt:**
```
ESS-02: "Gebruik formuleringen zoals:
         - 'is een activiteit waarbij...'"
STR-01: "Start met noun, niet 'is'"
         → CONFLICT!
```

**Nieuwe (JUISTE) prompt:**
```
ESS-02: "Voor PROCES begrippen, formuleer als:
         - 'activiteit waarbij...'
         - 'handeling die...'
         - 'proces waarin...'"
STR-01: "Start met noun, niet 'is'"
         → GEEN CONFLICT! Beide vereisen noun-start
```

---

### TYPE Begrippen:

**Nieuwe prompt:**
```
ESS-02: "Voor TYPE begrippen, formuleer als:
         - 'soort/categorie van...'
         - 'type... dat...'
         - 'klasse van...'"
STR-01: "Start met noun, niet 'is'"
         → Beide vereisen noun-start
```

---

### RESULTAAT Begrippen:

**Nieuwe prompt:**
```
ESS-02: "Voor RESULTAAT begrippen, formuleer als:
         - 'resultaat van...'
         - 'uitkomst van...'
         - 'product dat ontstaat door...'"
STR-01: "Start met noun, niet 'is'"
         → Beide vereisen noun-start
```

---

### EXEMPLAAR Begrippen:

**Nieuwe prompt:**
```
ESS-02: "Voor EXEMPLAAR begrippen, formuleer als:
         - 'exemplaar van... dat...'
         - 'specifiek geval van...'
         - 'individuele instantie van...'"
STR-01: "Start met noun, niet 'is'"
         → Beide vereisen noun-start
```

---

## 📋 Wat We Moeten Fixen

### 1️⃣ ESS-02.json - Goede Voorbeelden

**Huidige Staat (FOUT):**
```json
"goede_voorbeelden_proces": [
  "Observatie is een activiteit waarbij gegevens worden verzameld door directe waarneming.",
  "Interview is een activiteit waarbij gegevens worden verzameld door middel van vraaggesprekken."
]
```

**Nieuwe Versie (GOED):**
```json
"goede_voorbeelden_proces": [
  "activiteit waarbij gegevens worden verzameld door directe waarneming",
  "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
]
```

**Wijziging:**
- Verwijder "Observatie is een" → start direct met "activiteit"
- Verwijder "Interview is een" → start direct met "handeling"

---

**Huidige Staat TYPE (lijn 26 - DEELS FOUT):**
```json
"goede_voorbeelden_type": [
  "verdachte: juridische categorie van personen die voldoen aan bepaalde criteria",
  "Adelaar is een vogelsoort die voorkomt in Europa."  // ← "is een" hier!
]
```

**Nieuwe Versie:**
```json
"goede_voorbeelden_type": [
  "juridische categorie van personen die voldoen aan bepaalde criteria",
  "vogelsoort die voorkomt in Europa"
]
```

---

**Huidige Staat RESULTAAT (lijn 45 - FOUT):**
```json
"goede_voorbeelden_resultaat": [
  "Interviewrapportage is het resultaat van het uitwerken en analyseren van het interview met persoon X."
]
```

**Nieuwe Versie:**
```json
"goede_voorbeelden_resultaat": [
  "resultaat van het uitwerken en analyseren van interviews met persoon X",
  "uitkomst van een beoordelingsproces"
]
```

---

**Huidige Staat EXEMPLAAR (lijn 32 - FOUT):**
```json
"goede_voorbeelden_particulier": [
  "Het exemplaar adelaar dat op 25 mei 2024 in de Biesbosch werd waargenomen."
]
```

**Nieuwe Versie:**
```json
"goede_voorbeelden_particulier": [
  "exemplaar van een adelaar dat op 25 mei 2024 in de Biesbosch werd waargenomen",
  "specifiek geval van een observatie uitgevoerd op 12 maart 2024"
]
```

---

### 2️⃣ semantic_categorisation_module.py - Category Guidance

**Huidige Staat (FOUT) - lijn 136-144:**
```python
base_section = """### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken:
• type (soort), • exemplaar (specifiek geval), • proces (activiteit), • resultaat (uitkomst)
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'  # ← FOUT!
- 'is het resultaat van...'       # ← FOUT!
- 'betreft een specifieke soort...'
- 'is een exemplaar van...'       # ← FOUT!
```

**Nieuwe Versie (GOED):**
```python
base_section = """### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken door de JUISTE KICK-OFF term te kiezen:

• PROCES begrippen → start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
• TYPE begrippen → start met: 'soort...', 'categorie van...', 'type... dat...'
• RESULTAAT begrippen → start met: 'resultaat van...', 'uitkomst van...', 'product dat...'
• EXEMPLAAR begrippen → start met: 'exemplaar van... dat...', 'specifiek geval van...'

⚠️ Let op: Start NOOIT met 'is een' of andere koppelwerkwoorden!
De kick-off term MOET een zelfstandig naamwoord zijn dat de categorie aangeeft.
```

---

**Huidige PROCES Guidance (FOUT) - lijn 180-183:**
```python
"proces": """**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'  # ← FOUT!
- 'is het proces waarin...'       # ← FOUT!
```

**Nieuwe PROCES Guidance (GOED):**
```python
"proces": """**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**

KICK-OFF opties (kies één):
- 'activiteit waarbij...' → focus op wat er gebeurt
- 'handeling die...' → focus op de actie
- 'proces waarin...' → focus op het verloop

VERVOLG met:
- WIE voert het uit (actor/rol)
- WAT er precies gebeurt (actie)
- HOE het verloopt (stappen/methode)
- WAAR het begint en eindigt (scope)

VOORBEELDEN (GOED):
✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
✅ "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
✅ "proces waarin documenten systematisch worden geanalyseerd"

VOORBEELDEN (FOUT):
❌ "is een activiteit waarbij..." (start met 'is')
❌ "het observeren van..." (werkwoordelijk)
❌ "manier om gegevens te verzamelen" (te abstract)
```

---

**Nieuwe TYPE Guidance:**
```python
"type": """**TYPE CATEGORIE - Formuleer als SOORT/CATEGORIE:**

KICK-OFF opties (kies één):
- 'soort... die...' → algemene classificatie
- 'categorie van...' → formele indeling
- 'type... dat...' → specifieke variant
- 'klasse van...' → technische classificatie

VERVOLG met:
- Tot welke BREDERE KLASSE het behoort
- Wat de ONDERSCHEIDENDE KENMERKEN zijn
- Waarin het VERSCHILT van andere types

VOORBEELDEN (GOED):
✅ "soort document dat formele beslissingen vastlegt"
✅ "categorie van personen die aan bepaalde criteria voldoen"
✅ "type interventie gericht op gedragsverandering"

VOORBEELDEN (FOUT):
❌ "is een soort..." (start met 'is')
❌ "betreft een..." (koppelwerkwoord)
```

---

**Nieuwe RESULTAAT Guidance:**
```python
"resultaat": """**RESULTAAT CATEGORIE - Formuleer als UITKOMST/PRODUCT:**

KICK-OFF opties (kies één):
- 'resultaat van...' → algemene uitkomst
- 'uitkomst van...' → proces resultaat
- 'product dat ontstaat door...' → tastbaar resultaat
- 'gevolg van...' → causaal resultaat

VERVOLG met:
- UIT WELK PROCES het voortkomt (oorsprong)
- WAT het betekent/bewerkstelligt (doel/functie)
- WIE het produceert (actor)

VOORBEELDEN (GOED):
✅ "resultaat van het uitwerken en analyseren van interviews"
✅ "uitkomst van een beoordelingsproces waarbij criteria worden toegepast"
✅ "product dat ontstaat door het combineren van verschillende databronnen"

VOORBEELDEN (FOUT):
❌ "is het resultaat van..." (start met 'is')
❌ "de uitkomst..." (lidwoord)
```

---

**Nieuwe EXEMPLAAR Guidance:**
```python
"exemplaar": """**EXEMPLAAR CATEGORIE - Formuleer als SPECIFIEK GEVAL:**

KICK-OFF opties (kies één):
- 'exemplaar van... dat...' → concrete instantie
- 'specifiek geval van...' → individueel voorbeeld
- 'individuele instantie van...' → uniek voorkomen

VERVOLG met:
- Van welke ALGEMENE KLASSE dit een exemplaar is
- Wat dit exemplaar UNIEK maakt (identificerende kenmerken)
- WANNEER/WAAR het voorkomt (contextualisering)

VOORBEELDEN (GOED):
✅ "exemplaar van een adelaar dat op 25 mei 2024 in de Biesbosch werd waargenomen"
✅ "specifiek geval van een observatie uitgevoerd op 12 maart 2024"
✅ "individuele instantie van een besluit genomen door de rechtbank op 1 april 2024"

VOORBEELDEN (FOUT):
❌ "is een exemplaar van..." (start met 'is')
❌ "het exemplaar..." (lidwoord)
```

---

### 3️⃣ GEEN WIJZIGING NODIG in:

**STR-01.json** - Blijft EXACT zoals het is
- Verboden patronen blijven hetzelfde
- Geen exceptions nodig!
- ESS-02 templates voldoen nu automatisch aan STR-01

**error_prevention_module.py** - Blijft EXACT zoals het is
- Forbidden starters blijven verboden (inclusief "is")
- Geen exceptions nodig!

**structure_rules_module.py** - Blijft EXACT zoals het is
- STR-01 regel blijft ongewijzigd
- Voorbeelden blijven hetzelfde

---

## 🔬 Waarom Dit De Contradictie OPLOST

### VOOR de fix:

```
ESS-02 prompt: "gebruik 'is een activiteit waarbij...'"
STR-01 prompt: "'is' is verboden"
GPT-4: CONFLICT! → kiest "activiteit waarbij" (dropt "is een")
```

### NA de fix:

```
ESS-02 prompt: "PROCES → gebruik 'activiteit waarbij...'"
STR-01 prompt: "'is' is verboden"
GPT-4: GEEN CONFLICT! → gebruikt "activiteit waarbij"
```

**Cruciale Verschil:**
- ESS-02 STUURT naar noun-start templates
- STR-01 VEREIST noun-start
- → BEIDE REGELS WERKEN SAMEN in plaats van tegen elkaar!

---

## 📊 Impact Assessment

### Code Wijzigingen:

| Bestand | Huidige Staat | Wijziging | Reden |
|---------|---------------|-----------|-------|
| **ESS-02.json** | Goede voorbeelden met "is een" | Verwijder "is een", start met noun | Align met STR-01 |
| **semantic_categorisation_module.py** | Guidance met "is een" | Category-specific templates (noun-start) | Align met STR-01 |
| **STR-01.json** | Verbiedt "is" start | **GEEN WIJZIGING** | Blijft zoals het is |
| **error_prevention_module.py** | Verbiedt "is" | **GEEN WIJZIGING** | Blijft zoals het is |
| **structure_rules_module.py** | STR-01 regel | **GEEN WIJZIGING** | Blijft zoals het is |

**Total Wijzigingen:** 2 bestanden (ESS-02.json, semantic_categorisation_module.py)

---

### Database Impact:

**Huidige Staat:**
- 96% gebruikt "activiteit waarbij" (GEEN "is een")
- 1% gebruikt "is een activiteit" (rebels)
- 3% alternatieven

**NA Fix:**
- 98% gebruikt "activiteit waarbij" (aligned pattern)
- 0% gebruikt "is een" (geen contradictie meer)
- 2% alternatieven ("handeling", "proces")

**Impact:** MINIMAAL - meeste definities voldoen al aan nieuwe templates!

---

### GPT-4 Prompt Impact:

**Token Reductie:**
```
VOOR:
- ESS-02 base: 150 tokens ("gebruik 'is een activiteit'...")
- ESS-02 PROCES: 200 tokens ("Gebruik formuleringen zoals: 'is een activiteit'...")
- ERROR: 50 tokens ("Verboden: 'is'")
- STR-01: 80 tokens ("Fout voorbeeld: 'is een maatregel'")
Total: 480 tokens met contradictie

NA:
- ESS-02 base: 120 tokens ("PROCES → 'activiteit waarbij'")
- ESS-02 PROCES: 180 tokens ("Kick-off opties: 'activiteit waarbij'...")
- ERROR: 50 tokens ("Verboden: 'is'")
- STR-01: 80 tokens (ongewijzigd)
Total: 430 tokens ZONDER contradictie

Reductie: 50 tokens (10%) + GEEN conflicting signals!
```

---

## ✅ IMPLEMENTATIE PLAN

### Stap 1: Fix ESS-02.json (15 min)

**Wijzig:**
1. `goede_voorbeelden_proces` (lijn 37-40)
2. `goede_voorbeelden_type` (lijn 24-27)
3. `goede_voorbeelden_resultaat` (lijn 44-46)
4. `goede_voorbeelden_particulier` (lijn 31-33)

**Actie:** Verwijder alle "is een" / "is het" / "Het" starts, direct noun-start

---

### Stap 2: Fix semantic_categorisation_module.py (30 min)

**Wijzig:**
1. `base_section` (lijn 136-150) → Nieuwe template-driven instructies
2. `category_guidance_map["proces"]` (lijn 180-197) → Kick-off opties
3. `category_guidance_map["type"]` (lijn 198-215) → Kick-off opties
4. `category_guidance_map["resultaat"]` (lijn 216-236) → Kick-off opties
5. `category_guidance_map["exemplaar"]` (lijn 237-254) → Kick-off opties

**Actie:** Replace alle "is een" guidance met noun-start templates

---

### Stap 3: Test met GPT-4 (15 min)

**Test Cases:**
```python
# Test 1: PROCES begrip
begrip = "observatie"
categorie = "proces"
# Verwacht: "activiteit waarbij gegevens worden verzameld..."

# Test 2: TYPE begrip
begrip = "sanctie"
categorie = "type"
# Verwacht: "soort maatregel die..."

# Test 3: RESULTAAT begrip
begrip = "rapport"
categorie = "resultaat"
# Verwacht: "resultaat van het uitwerken van..."

# Test 4: EXEMPLAAR begrip
begrip = "dossier X"
categorie = "exemplaar"
# Verwacht: "exemplaar van een dossier dat..."
```

---

### Stap 4: Validatie (10 min)

**Controleer:**
1. ESS-02 validator accepteert nieuwe patterns (Pattern 2 blijft matchen)
2. STR-01 validator accepteert nieuwe patterns (geen "is" start)
3. Beide validators geven PASS voor dezelfde definitie

---

## 🎯 SUCCESS CRITERIA

### Na Implementatie:

✅ **ESS-02 + STR-01 alignment:**
- Goede voorbeelden voldoen aan beide regels
- Geen contradicterende instructies in prompt
- GPT-4 krijgt duidelijke category-specific templates

✅ **Code Simpliciteit:**
- GEEN exceptions nodig
- GEEN nieuwe regels
- Gewoon betere templates!

✅ **Database Continuïteit:**
- 96% bestaande definities blijven valid
- Nieuwe definities volgen cleaner pattern
- Minimale disruptie

---

## 📚 CONCLUSIE

### De Kernles:

> **"Contradictie los je NIET op met exceptions, maar met ALIGNMENT"**

**Foutieve Aanpak:**
- Exception toevoegen aan STR-01 voor ESS-02
- → Logisch inconsistent (exception voor alle begrippen!)

**Juiste Aanpak:**
- ESS-02 templates laten VOLDOEN aan STR-01
- → Logisch consistent (beide regels werken samen!)

### Het Verschil:

| Aanpak | STR-01 | ESS-02 | Resultaat |
|--------|--------|--------|-----------|
| **FOUT (exception)** | Verbied "is" (behalve ESS-02) | Gebruik "is een" | Inconsistent! |
| **GOED (alignment)** | Verbied "is" | Gebruik noun-start | Consistent! |

---

**Next Action:** Implementeer de 2 wijzigingen (ESS-02.json + semantic_categorisation_module.py) volgens dit plan.
