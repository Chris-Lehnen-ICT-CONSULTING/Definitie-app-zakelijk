---
name: nederlandse-definities
description: "Schrijf of formuleer een Nederlandse definitie volgens ISO 704/1087 en genus-differentia — ook bij kale opdrachten als \"Schrijf een definitie\", en ook als het begrip juridisch is. Triggers: \"schrijf een definitie\", \"formuleer\", \"definitie opstellen\", \"genus-differentia\", \"taalregel\", \"kick-off\". NOT for validatie (use definitie-toetsregels), NOT for juridische grondslag (use definitie-juridisch-nederland)."
triggerExamples:
  positive:
    - "Schrijf een definitie"
    - "Schrijf de definitie van dit begrip"
    - "Schrijf een definitie voor het begrip 'toezichthouder' volgens ISO 704"
    - "Pas de genus-differentia methode toe op deze term"
    - "Kick-off: we gaan een nieuwe definitie formuleren"
  negative:
    - "Valideer deze definitie met de toetsregels" # → definitie-toetsregels
    - "Maak een ontologisch model" # → definitie-ontologisch-modelleren
    - "Welke juridische context past bij dit begrip?" # → definitie-juridisch-nederland
lastReviewed: null
evalScore: null
status: active
---

# Nederlandse Definities — Taal, Structuur & Theorie

Taal-, structuur- en formuleringsregels voor het schrijven van juridische en bestuurlijke definities in het Nederlands, gebaseerd op ISO 704:2022 en ISO 1087:2019.

## Wanneer gebruiken

- Een definitie in het Nederlands moet worden geschreven of beoordeeld
- Taalkundige kwaliteit van een definitie moet worden gecontroleerd (grammatica, stijl, woordkeuze)
- De genus-differentia structuur moet worden toegepast of gevalideerd
- Kick-off-voorbeelden per praktische richting (TYPE/PROCES/RESULTAAT/EXEMPLAAR) nodig zijn — als hulp, niet als woordplicht
- Definitiefouten moeten worden herkend en gecorrigeerd (circulariteit, te breed/smal, etc.)
- De intensie of extensie van een begrip moet worden bepaald
- Noodzakelijke en voldoende voorwaarden van een definitie moeten worden gecontroleerd
- Een contextnaam in een definitie moet worden beoordeeld: registratie (buiten de zin) of inhoudelijk noodzakelijk (CON-01)

**Niet gebruiken voor:** juridische context en rechtsgebied-terminologie (gebruik **definitie-juridisch-nederland**), ontologische classificatie (gebruik **definitie-ufo-ontologie**), of voorbeeldgeneratie (gebruik **definitie-voorbeelden-generatie**).

## Volledige taal- en definitieregels

> Het theoretisch fundament (ISO 704/1087), het genus-differentia-principe, kick-off-patronen per categorie, de definitiefout-taxonomie, grammatica-/interpunctie-/opbouwregels, verboden patronen, contextvermelding (CON-01) en de beoordelingschecklist: zie **[`reference.md`](reference.md)**.

## Contextvermelding (CON-01)

Registratiecontext (rechtsgebied, organisatie, wet, project) hoort niet in de definitiezin maar gestructureerd in het contextveld bij het record. Een naam die inhoudelijk nodig is voor afbakening of identificatie mag wél — behoud die en motiveer de grond in de toelichting. Een letterlijke treffer op een contextnaam is een signaal voor menselijke beoordeling, geen automatische overtreding; verwijder niets automatisch. De vier onderscheidingen (registratie, noodzakelijke naam, foutief signaal, onduidelijk) met voorbeelden, uitkomsten en grenzen: zie **[`reference.md`](reference.md)** § Contextvermelding.

## Bij werkelijk aangeleverde bronnen

Baseer je de definitie op aangeleverde bronpassages (upload, RAG, wet-, beleids- of normtekst), volg dan sectie **G** van het gedeelde CON-02-contract: [`references/con02-bronbasis.md`](references/con02-bronbasis.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Kern: gebruik alleen passende, echt aangeleverde passages; behoud bepalende kenmerken, beperkingen en uitzonderingen; verzin geen bron, passage of vindplaats; houd bronadministratie buiten de definitiezin. Zonder aangeleverde bronnen gelden gewoon de taal- en structuurregels hierboven; een juridische werkwijze is niet voor elke definitie vereist.

## ESS-01 — begripsafbakening, functie en doel

Lees bij genereren of toetsen het [gedeelde N/G/T/H-contract](references/ess01-functiegrens.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Behoud uitsluitend onderbouwde begripsbepalende functies; overig doel buiten de kern. Toets ongewijzigde invoer. Een bevestigde overtreding blijft voldoet niet, ongeacht brongezag. Geen automatische wijziging of regeneratie. Toezicht blijft een grensgeval; “in het kader van” blijft een zichtbaar signaal. Geen ESS-01-cijfer, aparte akkoordplicht of nieuwe vaststelblokkade; CON-01/02-afspraken blijven gelden. Skilladvies is geen opgeslagen menselijke review.

## ESS-02 — betekenisniveau en aard

Lees bij formuleren het [gedeelde ESS-02-contract](references/ess02-betekenisniveau.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Laat bovenbegrip en kenmerken duidelijk maken of een algemeen begrip dan wel één bepaald ding of voorval bedoeld is, en waar relevant of de kern een activiteit of haar uitkomst is. De kick-off-voorbeelden per richting zijn hulp en de vier richtingen overlappen (een algemeen activiteitbegrip is TYPE én PROCES): een passend genus buiten de voorbeelden is even goed; "soort", "type", "proces" of "exemplaar" zijn geen verplichte en geen verboden woorden. Een activiteit mag haar uitkomst noemen. Behandel een opgegeven categorie als te controleren betekenisclaim; een bewuste handmatige keuze (actor, tijd, versie) bevestigt de daarin uitgedrukte bedoeling, een default of modelvoorstel niet. Bij werkelijke tegenspraak met bron of context eerst verduidelijken — herschrijf geen broninhoud om een label passend te maken. De inhoudelijke ESS-02-beoordeling is menselijk en cijferloos; tot dan "nog te beoordelen", en een negatief of open oordeel vormt geen zelfstandige vaststelblokkade. Skilladvies is geen opgeslagen menselijke beoordeling; stijl en zinsbouw beoordeel je onder hun eigen regels.

## Referenties

### Standaarden
- ISO 704:2022 — Terminologiewerk: Principes en methoden (vierde editie, actueel)
- ISO 1087:2019 — Terminologie: Vocabulaire (herbevestigd in 2025, actueel)
- ISO 5078:2025 — Management of terminology resources: Terminology extraction (nieuw)
- NL-SBB — Standaard voor het Beschrijven van Begrippen: https://docs.geostandaarden.nl/nl-sbb/

### Gerelateerde skills

| Skill | Relatie |
|-------|---------|
| **definitie-toetsregels** | Validatie — volledige lijst toetsregels (STR, INT, VER) |
| **definitie-ufo-ontologie** | Categorie — UFO-achtergrond bij de vier praktische richtingen; hulp bij de kick-off, geen woordplicht |
| **definitie-voorbeelden-generatie** | Illustratie — voorbeelden en tegenvoorbeelden bij definities |
| **definitie-ontologisch-modelleren** | Structuur — genus-hiërarchie uit het ontologisch model |
| **definitie-juridisch-nederland** | Context — rechtsgebied-specifieke terminologie |

### Technische referenties (DefinitieAgent)
- Prompt-modules: `src/services/prompts/modules/`
- Toetsregels-configuratie: `config/toetsregels/`

*Versie: 0.4 — DEF-754 (ESS-02 betekenisniveau en aard; kick-off-richtingen als hulp); 0.3 — DEF-743 (verwijzing naar gedeeld CON-02 G-contract bij aangeleverde bronnen); 0.2 — ALG-131 — ALG-329 progressive disclosure — DEF-744 contextvermelding (CON-01)*
