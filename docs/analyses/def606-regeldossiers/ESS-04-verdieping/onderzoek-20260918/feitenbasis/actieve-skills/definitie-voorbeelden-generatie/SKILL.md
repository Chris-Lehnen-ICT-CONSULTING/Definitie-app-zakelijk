---
name: voorbeelden-generatie
description: "Genereer voorbeelden, tegenvoorbeelden en grensgevallen bij juridische definities. Triggers: \"voorbeeld\", \"tegenvoorbeeld\", \"grensgeval\", \"casuïstiek\", \"intensie-extensie\". NOT for validatie (use definitie-toetsregels)."
triggerExamples:
  positive:
    - "Genereer voorbeelden en tegenvoorbeelden bij deze definitie"
    - "Geef grensgevallen bij deze juridische definitie"
    - "Maak casuistiek voor de intensie-extensie analyse"
  negative:
    - "Valideer deze definitie" # → definitie-toetsregels
    - "Schrijf een definitie" # → definitie-nederlandse-definities
    - "Classificeer dit begrip volgens UFO" # → definitie-ufo-ontologie
lastReviewed: null
evalScore: null
status: active
---

# Voorbeelden & Tegenvoorbeelden bij Definities

Systematische methode voor het genereren van voorbeelden, tegenvoorbeelden en grensgevallen bij juridische definities, gebaseerd op intensie-extensie-analyse en kenmerkontleding.

## Wanneer gebruiken

- Voorbeelden bij een definitie moeten worden gegenereerd (positief, negatief, grensgeval)
- Tegenvoorbeelden nodig zijn om de grenzen van een begrip te verduidelijken
- De kwaliteit van bestaande voorbeelden moet worden beoordeeld
- Grensgevallen moeten worden geidentificeerd om een definitie te testen op scherpte
- De intensie-extensie-afstemming van een definitie moet worden gecontroleerd
- Systematisch voorbeelden moeten worden geconstrueerd vanuit de definitiekenmerken

**Niet gebruiken voor:** het schrijven van de definitie zelf (gebruik **definitie-nederlandse-definities**), ontologische classificatie (gebruik **definitie-ufo-ontologie**), of kwaliteitsvalidatie tegen toetsregels (gebruik **definitie-toetsregels**).

## Waarom Voorbeelden?

Een definitie beschrijft de *intensie* van een begrip — de essentiële kenmerken. Voorbeelden, tegenvoorbeelden en grensgevallen tonen de *extensie* — wat er concreet wel en niet onder valt. Samen vormen ze het testpakket waarmee een definitie wordt geverifieerd.

**Belangrijk onderscheid:**
- De **definitie** beschrijft de intensie (kenmerken)
- De **voorbeelden** illustreren de extensie (instanties)
- Voorbeelden zijn GEEN vervanging voor een definitie — ze zijn een aanvulling

## Volledige methodiek

> Het theoretisch kader (intensie-extensie), systematische voorbeeldconstructie, het generatieproces per categorie, kwaliteitscriteria, aantallen/verhoudingen, de relatie met toetsregels en het intensie-extensie-toetsprotocol: zie **[`reference.md`](reference.md)**.

## Referenties

### Gerelateerde skills

| Skill | Relatie |
|-------|---------|
| **definitie-nederlandse-definities** | Taalregels — intensie/extensie-theorie en definitiestructuur |
| **definitie-ufo-ontologie** | Categorie — generatieproces verschilt per categorie (TYPE/PROCES/RESULTAAT) |
| **definitie-juridisch-nederland** | Context — juridische voorbeelden per rechtsgebied |
| **definitie-toetsregels** | Validatie — ESS-03, ESS-05, STR-02 ondersteunen met voorbeelden |
| **definitie-ontologisch-modelleren** | Structuur — zusterbegrippen uit model als tegenvoorbeelden |

### Technische referenties (DefinitieAgent)
- Voorbeelden-velden in database: `src/database/models/`
- RAG-integratie: gepland (DEF-267, DEF-275)

*Versie: 0.1 — ALG-131 — ALG-329 progressive disclosure*
