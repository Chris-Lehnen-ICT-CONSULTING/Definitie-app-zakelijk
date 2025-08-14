# Ontologische Categorisering - 6 Stappen Protocol

## 🎯 Doel
Bepaal de exacte ontologische categorie van een begrip voor het opstellen van juridisch correcte definities.

## 📋 De 6 Stappen

### STAP 1: Lexicale en Conceptuele Verkenning
**Doel**: Verzamel alle betekenisaspecten van het begrip.

**Acties**:
```python
# 1. Verzamel definities uit:
- Van Dale / juridische woordenboeken
- Wetteksten waarin begrip voorkomt  
- Vaklliteratuur/standaarden (NEN, ISO)
- Bestaande systemen/registraties

# 2. Identificeer sleutelkenmerken:
- Is het telbaar? (substantie indicator)
- Gebeurt het in tijd? (proces indicator)
- Is het meetbaar? (eigenschap indicator)
- Beschrijft het een verband? (relatie indicator)

# 3. Noteer synoniemen en gerelateerde begrippen
```

**Output**: Semantisch profiel met kenmerken en context.

---

### STAP 2: Context- en Domeinanalyse
**Doel**: Bepaal rol en afhankelijkheden in juridische context.

**Acties**:
```python
# 1. Analyseer gebruik in processen:
- In welke wetten/regelingen komt het voor?
- Welke handelingen zijn ermee verbonden?
- Wie zijn de actoren?

# 2. Test onafhankelijkheid:
- Kan dit begrip op zichzelf bestaan?
- Of heeft het altijd een drager nodig?
- Is het een rol of inherente eigenschap?
```

**Output**: Contextmap met afhankelijkheden.

---

### STAP 3: Formele Categorietoets

**Doel**: Classificeer volgens standaard ontologie (BFO/DOLCE gebaseerd).

**Categorieën en testvragen**:

| Categorie | Testvraag | Voorbeeld | Definitietemplate |
|-----------|-----------|-----------|-------------------|
| **SUBSTANTIE** | Kan dit onafhankelijk bestaan? | Persoon, Gebouw | "Een [genus] dat [kenmerken]" |
| **EIGENSCHAP** | Is dit een meetbare kwaliteit? | Hoogte, Geldigheid | "De [kwaliteit] van [drager]" |
| **TOESTAND** | Is dit een tijdelijke situatie? | Openstand, Werkloosheid | "De situatie waarin [subject] [conditie]" |
| **GEBEURTENIS** | Heeft dit begin- en eindpunt? | Aanvraag, Overdracht | "Het [proces] waarbij [actor] [handeling]" |
| **ROL** | Is dit een functie/positie? | Eigenaar, Aanvrager | "Een [entiteit] die [functie] vervult" |
| **DOCUMENT** | Is dit vastgelegde informatie? | Vergunning, Beschikking | "Een [documenttype] waarin [inhoud]" |

**Output**: Primaire categorie + evt. secundaire aspecten.

---

### STAP 4: Identiteits- en Persistentiecriteria

**Doel**: Bepaal wat instanties uniek maakt en wanneer ze ophouden te bestaan.

**Acties**:
```python
# Identiteitscriteria - "Wanneer zijn twee X hetzelfde?"
- Unieke kenmerken (BSN, documentnummer)
- Combinatie van eigenschappen
- Temporele aspecten (geldig vanaf/tot)

# Persistentiecriteria - "Wanneer houdt X op te bestaan?"
- Expliciet beëindigd (opzegging, intrekking)
- Tijdsverloop (verlopen geldigheid)
- Statusverandering (van concept naar definitief)
```

**Output**: Lijst met identiteits- en bestaansvoorwaarden.

---

### STAP 5: Rol versus Intrinsieke Eigenschappen

**Doel**: Scheid contextuele rollen van inherente categorieën.

**Analyse**:
```python
# Test: Is het begrip altijd waar of alleen in context?
- "Burger" = rol van Persoon (in context van staat)
- "Mens" = intrinsieke substantie
- "Eigenaar" = rol (in context van eigendom)
- "Gebouw" = intrinsieke substantie

# Bij rollen: identificeer de basisentiteit
Aanvrager → Persoon/Organisatie
Vergunninghouder → Persoon/Organisatie  
Bevoegd gezag → Bestuursorgaan
```

**Output**: Basis-entiteit + rol-specificatie indien van toepassing.

---

### STAP 6: Documentatie en Definitieconstructie

**Doel**: Leg vast en construeer de definitie volgens de categorie.

**Template per categorie**:

```yaml
begrip: [BEGRIP]
ontologische_categorie: [CATEGORIE]
basis_entiteit: [indien rol]
definitie_template: [zie stap 3]

identiteitscriteria:
  - [criterium 1]
  - [criterium 2]

persistentiecriteria:
  - ontstaat_door: [gebeurtenis/handeling]
  - eindigt_door: [gebeurtenis/handeling]
  
context_afhankelijkheden:
  - [afhankelijkheid 1]
  - [afhankelijkheid 2]

definitie: "[Gegenereerde definitie volgens template]"
```

---

## 🚀 Implementatie in Code

```python
def bepaal_ontologische_categorie(begrip: str) -> dict:
    """Doorloop 6-stappen protocol voor ontologische analyse."""
    
    # Stap 1: Lexicale verkenning
    semantisch_profiel = verken_begrip(begrip)
    
    # Stap 2: Context analyse
    context_map = analyseer_context(begrip, semantisch_profiel)
    
    # Stap 3: Formele categorisatie
    categorie = toets_categorieen(semantisch_profiel, context_map)
    
    # Stap 4: Identiteitscriteria
    identiteit = bepaal_identiteit(begrip, categorie)
    
    # Stap 5: Rol-analyse
    rol_info = analyseer_rol_vs_intrinsiek(begrip, categorie)
    
    # Stap 6: Documentatie
    return documenteer_resultaat(
        begrip, categorie, identiteit, rol_info
    )
```

## ⚡ Quick Decision Tree

Voor 80% van de gevallen:
1. **Gebeurt het?** → GEBEURTENIS/PROCES
2. **Is het een ding?** → SUBSTANTIE
3. **Is het een kenmerk?** → EIGENSCHAP
4. **Is het een positie/functie?** → ROL
5. **Is het vastgelegd?** → DOCUMENT
6. **Anders** → Doorloop volledig protocol

## 📝 Belangrijke principes

1. **Één primaire categorie** - kies de meest fundamentele
2. **Rollen altijd scheiden** - definieer basis-entiteit apart
3. **Context documenteren** - leg afhankelijkheden vast
4. **Template volgen** - gebruik de juiste definitiestructuur
5. **Valideren** - test of definitie past bij categorie


markdown## 🔍 Ontologische Categorisering Protocol

Bij het bepalen van definities MOET eerst de ontologische categorie vastgesteld worden via dit 6-stappen protocol:

1. **Lexicaal**: Verzamel definities, identificeer kenmerken (telbaar/tijdelijk/meetbaar)
2. **Context**: Analyseer juridisch gebruik en afhankelijkheden  
3. **Categorie**: Bepaal of het een SUBSTANTIE/PROCES/EIGENSCHAP/ROL/DOCUMENT is
4. **Identiteit**: Wat maakt instanties uniek? Wanneer eindigen ze?
5. **Rol-check**: Is het intrinsiek of contextueel? Bij rollen: wat is de basis?
6. **Documenteer**: Gebruik het juiste definitietemplate per categorie

### Definitietemplates per categorie:
- SUBSTANTIE: "Een [genus] dat [kenmerken]"
- PROCES: "Het [werkwoord] waarbij [actor] [handeling]"  
- EIGENSCHAP: "De [kwaliteit] van [drager]"
- ROL: "Een [basis-entiteit] die [functie] vervult"
- DOCUMENT: "Een [type] waarin [inhoud] is vastgelegd"

### Quick-check (80% gevallen):
Gebeurt het? → PROCES | Is het een ding? → SUBSTANTIE | 
Kenmerk? → EIGENSCHAP | Functie? → ROL | Vastgelegd? → DOCUMENT

ALTIJD: Ontologie bepalen → Dan pas definitie opstellen!
💡 Praktisch gebruik:
bash# In je project met Claude Code:
claude "Bepaal de ontologische categorie van 'aanvrager' volgens het 6-stappen protocol"

# Claude zal dan:
1. Het protocol document raadplegen
2. Stap voor stap doorlopen
3. Conclusie: ROL (basis: Persoon/Organisatie)
4. Juiste definitietemplate gebruiken
Dit protocol zorgt voor consistente, juridisch correcte definities in je DefinitieAgent! 🚀RetryClaude can make mistakes. Please double-check responses.