---
name: ontologisch-modelleren
description: "Domeinmodellen en begrippenkaders opzetten: taxonomieën, relaties, begripsstructuren, OntoUML. Triggers: \"ontologisch model\", \"begrippenkader\", \"taxonomie\", \"domeinmodel\", \"modelleer relaties\". NOT for UFO-classificatie (use definitie-ufo-ontologie)."
triggerExamples:
  positive:
    - "Maak een ontologisch model van het domein belastingrecht"
    - "Bouw een begrippenkader met taxonomie voor deze termen"
    - "Modelleer de relaties tussen deze concepten in OntoUML"
    - "Zet een domeinmodel op voor dit project"
  negative:
    - "Classificeer dit begrip als TYPE of PROCES volgens UFO" # → definitie-ufo-ontologie
    - "Schrijf de definitie van dit begrip" # → definitie-nederlandse-definities
    - "Valideer deze definitie" # → definitie-toetsregels
lastReviewed: null
evalScore: null
status: active
---

# Ontologisch Modelleren

Handleiding voor het opzetten, importeren en onderhouden van ontologische modellen (UFO/OntoUML-gebaseerd) als basis voor samenhangende definitie-generatie in de DefinitieAgent.

## Wanneer gebruiken

- Een nieuw domeinmodel moet worden opgezet voor definitie-generatie
- Bestaande begrippen in samenhang moeten worden gebracht (taxonomie, hiërarchie)
- Relaties tussen begrippen moeten worden gemodelleerd (is-een, deel-geheel, oorzaak-gevolg)
- Grensgevallen tussen categorieën (TYPE/PROCES/RESULTAAT) moeten worden opgelost
- Circulariteit in genus-ketens moet worden gedetecteerd of voorkomen
- Jurisdictie- of scopeafbakening nodig is voor een modelleeropdracht
- Een ontologisch model moet worden geïmporteerd of geëxporteerd (CSV, OntoUML, NL-SBB)

**Niet gebruiken voor:** UFO-theorie en classificatie-uitleg (gebruik **definitie-ufo-ontologie**), taalkundige formulering (gebruik **definitie-nederlandse-definities**), of validatie van losse definities (gebruik **definitie-toetsregels**).

## Waarom eerst modelleren?

Definities in isolatie leiden tot inconsistenties. Een ontologisch model brengt begrippen in samenhang VOORDAT je definities genereert. Dit garandeert:

- **Consistentie**: genus-differentia-relaties kloppen over begrippen heen
- **Volledigheid**: geen begrippen vergeten die in het domein thuishoren
- **Hiërarchie**: bovenliggende begrippen zijn gedefinieerd voordat onderliggende worden uitgewerkt
- **Geen circulariteit**: A verwijst niet naar B die weer naar A verwijst (toetsregel SAM-05)
- **Samenhang**: verwante begrippen worden op dezelfde manier en in dezelfde structuur gedefinieerd
- **Herbruikbaarheid**: het model kan dienen als basis voor meerdere toepassingen (definitie-generatie, informatiemodellering, beleidsdocumenten)

## Volledig modelleringsproces

> Het 8-staps modelleringsproces, modelformaten, kwaliteitscriteria voor het model en de DefinitieAgent-integratie: zie **[`reference.md`](reference.md)**.

## Referenties

### Gerelateerde skills

| Skill | Relatie |
|-------|---------|
| **definitie-ufo-ontologie** | Categorie — UFO-theorie en stereotypen als basis voor classificatie |
| **definitie-nederlandse-definities** | Taalregels — genus-differentia uit het model vertalen naar definitie |
| **definitie-toetsregels** | Validatie — SAM-regels voor samenhangcontrole tegen het model |
| **definitie-juridisch-nederland** | Context — rechtsgebied bepaalt scope en jurisdictie |
| **definitie-voorbeelden-generatie** | Illustratie — zusterbegrippen uit model als tegenvoorbeelden |

### Academische bronnen
- Guizzardi, G. (2005). *Ontological Foundations for Structural Conceptual Models*. Proefschrift, Universiteit Twente.
- Guizzardi, G., et al. (2022). "UFO: Unified Foundational Ontology." *Applied Ontology*, 17(1):167-210.
- Prince Sales, T., et al. (2023). "A FAIR catalog of ontology-driven conceptual models." *Data & Knowledge Engineering*, 147, 102210.

### Nederlandse standaarden
- NL-SBB: Standaard voor het Beschrijven van Begrippen — https://docs.geostandaarden.nl/nl-sbb/
- MIM 1.2 (2024): Metamodel Informatiemodellering — https://docs.geostandaarden.nl/mim/mim/ (MIM 2.0 gepland voor 2026)

### Technische referenties (DefinitieAgent)
- UFO-regelconfiguratie: `config/ufo_rules.yaml`
- Classificatie-instellingen: `config/classification/term_patterns.yaml`
- Classifier-implementatie: `src/ontologie/improved_classifier.py`

*Versie: 0.2 — ALG-131, ALG-129 — ALG-329 progressive disclosure*
