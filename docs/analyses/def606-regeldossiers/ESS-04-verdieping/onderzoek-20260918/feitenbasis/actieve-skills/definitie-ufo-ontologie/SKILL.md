---
name: ufo-ontologie
description: "Classificeer begrippen volgens Guizzardi's UFO: TYPE, PROCES, RESULTAAT, EXEMPLAAR; endurant/perdurant; OntoUML-stereotypen. Triggers: \"UFO\", \"classificeer begrip\", \"Guizzardi\", \"TYPE of PROCES\". NOT for domeinmodellering (use definitie-ontologisch-modelleren)."
triggerExamples:
  positive:
    - "Classificeer dit begrip volgens de UFO ontologie"
    - "Is dit een TYPE, PROCES, RESULTAAT of EXEMPLAAR?"
    - "Pas OntoUML stereotypen toe op deze begripsclassificatie"
    - "Welke UFO-categorie past bij dit concept?"
  negative:
    - "Modelleer de relaties in een begrippenkader" # → definitie-ontologisch-modelleren
    - "Schrijf een definitie in genus-differentia formaat" # → definitie-nederlandse-definities
    - "Valideer deze definitie" # → definitie-toetsregels
lastReviewed: null
evalScore: null
status: active
---

# UFO Ontologie — Academisch + Praktisch

Expertise over de Unified Foundational Ontology (UFO) en de mapping naar de vier praktische richtingen (TYPE/PROCES/RESULTAAT/EXEMPLAAR) van de DefinitieAgent, inclusief OntoUML-stereotypen en Nederlandse standaarden. De vier richtingen zijn een projectmatige vereenvoudiging die kunnen overlappen, geen vier disjuncte UFO-hoofdcategorieën.

## Wanneer gebruiken

- Een ontologische categorie moet worden bepaald of uitgelegd (TYPE/PROCES/RESULTAAT/EXEMPLAAR)
- Classificatie van een begrip vereist kennis van UFO-stereotypen (Kind, Role, Phase, Mode, etc.)
- De relatie tussen UFO-theorie en definitie-generatie relevant is
- OntoUML-modellering of stereotypen moeten worden toegepast of gevalideerd
- De relatie met Nederlandse standaarden (MIM, NORA, NL-SBB) moet worden uitgelegd
- Iemand vraagt over UFO, OntoUML, Guizzardi, of ontologische categorieën

**Niet gebruiken voor:** het daadwerkelijk opzetten van een ontologisch model (gebruik **definitie-ontologisch-modelleren**), taalkundige formulering (gebruik **definitie-nederlandse-definities**), of juridische context (gebruik **definitie-juridisch-nederland**).

## Kernprincipe

UFO (Unified Foundational Ontology) is een formele, axiomatisch gefundeerde ontologie ontwikkeld door Giancarlo Guizzardi en collega's. UFO biedt een filosofisch verantwoorde basis voor conceptueel modelleren en is de theoretische grondslag van OntoUML. De DefinitieAgent gebruikt een vereenvoudigd 4-categorieënmodel afgeleid van UFO; die vereenvoudiging is een hulpmiddel, geen exclusieve indeling (zie ESS-02 hieronder).

## ESS-02 — betekenisniveau en aard

Lees bij classificeren voor een definitie het [gedeelde ESS-02-contract](references/ess02-betekenisniveau.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Type/particulier geeft het betekenisniveau aan (algemeen begrip, of één bepaald ding — ook abstract — of voorval); activiteit en uitkomst geven een andere, inhoudelijke dimensie aan. Een activiteit of uitkomst kan dus algemeen of één bepaald voorval zijn: TYPE en PROCES sluiten elkaar niet uit. "Er is nu precies één" bepaalt het niveau niet; suffixen, prioriteitscascade en tie-break zijn classificatiehulp, geen betekenisbewijs. Leg de bedoelde betekenis en de grond vast; forceer onbekende of overlappende gevallen niet via een suffix of prioriteitsvolgorde. Een bewuste handmatige keuze (actor, tijd, versie) bevestigt alleen de daarin uitgedrukte bedoeling; een modelvoorstel of default niet; bij werkelijke tegenspraak met bron of context eerst verduidelijken. Een classificatie uit deze skill is een gemotiveerd advies — geen opgeslagen menselijke ESS-02-beoordeling, geen cijfer en geen vaststelblokkade; de inhoudelijke beoordeling blijft "nog te beoordelen" tot de mens haar geeft.

## Volledige UFO-referentie

> Het academisch UFO-overzicht, OntoUML 2.0, de mapping naar de 4 DefinitieAgent-categorieen (TYPE/PROCES/RESULTAAT/EXEMPLAAR) en de relatie met Nederlandse standaarden: zie **[`reference.md`](reference.md)**.

## Referenties

### Gerelateerde skills

| Skill | Relatie |
|-------|---------|
| **definitie-ontologisch-modelleren** | Structuur — UFO-stereotypen toepassen in een concreet model |
| **definitie-nederlandse-definities** | Taalregels — kick-off patronen per categorie (TYPE/PROCES/RESULTAAT) |
| **definitie-toetsregels** | Validatie — ESS-02 betekenisniveau en aard (menselijke beoordeling, geen cijfer); eigenaar van het gedeelde ESS-02-contract |
| **definitie-juridisch-nederland** | Context — UFO-C en UFO-L voor juridische begrippen |

### Primaire academische bronnen
- Guizzardi, G. (2005). *Ontological Foundations for Structural Conceptual Models*. PhD thesis, University of Twente. — Het fundament van UFO
- Guizzardi, G., Fonseca, C.M., Benevides, A.B., et al. (2022). "UFO: Unified Foundational Ontology." *Applied Ontology*, 17(1):167-210. — De meest recente, geconsolideerde beschrijving van UFO
- Guizzardi, G., et al. (2021). "OntoUML 2.0 — Language Reference." — De formele specificatie van OntoUML 2.0

### UFO-L (Legal ontology)
- Griffo, C., Almeida, J.P.A., Guizzardi, G. (2021). "Conceptual Modeling of Legal Relations." *Conceptual Modeling -- ER 2021*. — UFO-L voor juridische modellering
- Griffo, C., et al. (2023). "Legal powers, subjections, disabilities, and immunities: ontological analysis and modeling patterns." *Data & Knowledge Engineering*, 148, 102219.
- Lindeberg, J., et al. (2025). "Modelling Legal Enforcement with UFO-L: A Case from Swedish Healthcare." *ER 2024*.

### ISO-standaardisatie
- UFO is in ontwikkeling als **ISO/IEC 21838-5** (Information technology -- Top level ontologies -- Part 5: UFO). Committee Draft geregistreerd op 17 oktober 2024; CD goedgekeurd voor registratie als DIS (Draft International Standard) per december 2025.

### Nederlandse standaarden
- MIM 1.2 (2024): Metamodel Informatiemodellering — https://docs.geostandaarden.nl/mim/mim/ (MIM 2.0 gepland voor 2026)
- NORA: Nederlandse Overheid Referentie Architectuur — https://www.noraonline.nl/
- NL-SBB: Standaard voor het Beschrijven van Begrippen — https://docs.geostandaarden.nl/nl-sbb/ (status: "Pas toe of leg uit" per OBDO september 2025)

### Technische referenties (DefinitieAgent)
- UFO-regelconfiguratie: `config/ufo_rules.yaml`
- Suffix-gewichten en domain overrides: `config/classification/term_patterns.yaml`
- Classifier implementatie: `src/ontologie/improved_classifier.py`

*Versie: 0.3 — DEF-754 (ESS-02: vier overlappende richtingen, niveau en aard apart, geen "precies één → exemplaar"); 0.2 — ALG-131, ALG-129 — ALG-329 progressive disclosure*
