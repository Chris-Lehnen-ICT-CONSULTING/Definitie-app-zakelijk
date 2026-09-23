# Ontologisch Modelleren — Volledige Referentie

> On-demand referentie bij `definitie-ontologisch-modelleren`. Bevat het volledige 8-staps modelleringsproces, modelformaten en kwaliteitscriteria.

## Het Modelleringsproces (8 stappen)

### Stap 1: Domeinafbakening en Jurisdictie

Bepaal het domein, de scope en de juridische context:

**Domeinvragen:**
- Welke organisatie(s)? (bijv. DJI, OM, Rechtspraak, IND)
- Welk rechtsgebied? (strafrecht, bestuursrecht, civiel recht, of combinatie)
- Welke wettelijke basis? (specifieke wetten, AMvB's, regelingen)
- Welke processen/activiteiten vallen binnen scope?

**Jurisdictievragen:**
- Is het model specifiek voor Nederlands recht, of ook EU-recht?
- Zijn er internationale verdragen (EVRM, IVBPR) die meespelen?
- Geldt het model voor een specifieke uitvoeringsorganisatie of breder?

**Scopeafbakening vastleggen als:**
```
Domein: [naam]
Rechtsgebied: [strafrecht | bestuursrecht | civiel recht | gemengd]
Kernwetten: [opsomming]
Organisatie(s): [opsomming]
Jurisdictie: [NL | EU | internationaal]
Uitsluitingen: [wat valt er expliciet BUITEN scope]
```

### Stap 2: Begrippen Inventariseren

Verzamel alle kandidaat-begrippen uit:

**Primaire bronnen (gezaghebbend):**
- Wetteksten en regelgeving (wetten.overheid.nl)
- Officiële toelichtingen (Memorie van Toelichting, Nota van Toelichting)
- Jurisprudentie met richtinggevende definities

**Secundaire bronnen:**
- Beleidsdocumenten en procesomschrijvingen
- Bestaande begrippenlijsten/glossaria
- Interviews met domeinexperts

**Tertiaire bronnen (verificatie):**
- Vakliteratuur en handboeken
- Parlementaire geschiedenis

**Inventarisatieregels:**
- Neem zowel brede begrippen (maatregel) als smalle begrippen (taakstraf) op
- Noteer bij elk begrip de bron waar je het gevonden hebt
- Markeer synoniemen (bijv. "justitiabele" / "gedetineerde") — deze krijgen later dezelfde definitie (toetsregel SAM-08)
- Noteer ambigue begrippen die in verschillende rechtsgebieden een andere betekenis hebben

### Stap 3: Ontologische Categorisatie (UFO-gebaseerd)

Classificeer elk begrip volgens de 4 categorieën van de DefinitieAgent (zie skill `ufo-ontologie` voor uitgebreide toelichting):

| Categorie | Testvraag | UFO-basis |
|-----------|-----------|-----------|
| TYPE | "Is dit een klasse/soort van dingen?" | Kind, Subkind, Role, Phase, Mode, Quality |
| PROCES | "Is dit een activiteit/handeling die zich in de tijd ontvouwt?" | Event, Process |
| RESULTAAT | "Is dit de uitkomst/het product van een proces?" | SocialObject (pragmatisch) |
| EXEMPLAAR | "Is dit een specifiek, uniek geval?" | Particulier (instantie) |

**Verfijning met UFO-stereotypen:**
Na de basiscategorisatie, verfijn elk TYPE-begrip met het juiste UFO-stereotype:

| Als het begrip... | Dan is het UFO-stereotype... | Voorbeeld |
|-------------------|------------------------------|-----------|
| ...een zelfstandig type is met eigen identiteit | `«kind»` | Persoon, Document |
| ...een rigide specialisatie is | `«subkind»` | Paspoort (subkind van Document) |
| ...alleen bestaat in relatie tot iets anders | `«role»` | Verdachte (rol van Persoon) |
| ...een levensfase beschrijft | `«phase»` | Minderjarige (fase van Persoon) |
| ...een relatie reificeert | `«relator»` | Huwelijk, Arbeidsovereenkomst |
| ...een niet-meetbare eigenschap is | `«mode»` | Bevoegdheid, Intentie |
| ...een meetbare eigenschap is | `«quality»` | Leeftijd, Strafmaat |
| ...een groep als eenheid is | `«collective»` | Commissie, Meervoudige kamer |

### Stap 4: Relaties Modelleren

**Taxonomische relaties (is-een) — de ruggengraat van het model:**
- `Sanctie` is-een `Maatregel` → bepaalt het genus in definities
- `Geldboete` is-een `Sanctie` → bepaalt genus van geldboete
- `Taakstraf` is-een `Sanctie` → zusterbegrip van geldboete

Vuistregel: als begrip B is-een A, dan begint de definitie van B met het genus A.

**Meronymische relaties (deel-geheel):**
- `Vonnis` heeft-deel `Strafmaat`
- `Strafproces` heeft-fase `Onderzoek ter terechtzitting`
- Relevant voor toetsregel STR-05 (beschrijf essentie, niet alleen onderdelen)

**Procesrelaties (oorzaak-gevolg, input-output):**
- `Vervolging` → leidt-tot → `Vonnis` (PROCES → RESULTAAT)
- `Aanhouding` → onderdeel-van → `Opsporingsonderzoek` (Event → Process)
- `Strafbeschikking` → resulteert-in → `Sanctie` (RESULTAAT → TYPE)

**Rolrelaties (wie doet wat):**
- `Verdachte` speelt-rol-in `Strafproces`
- `Officier van Justitie` voert-uit `Vervolging`
- `Rechter` doet-uitspraak `Vonnis`

**Mediërende relaties (via relator):**
- `Werkgever` ←→ `Werknemer` via `Arbeidsovereenkomst` (relator)
- `Schuldeiser` ←→ `Schuldenaar` via `Verbintenis` (relator)
- In OntoUML: beide rollen zijn via `«mediation»` verbonden met de relator

### Stap 5: Circulariteitsdetectie

Circulariteit is een van de meest voorkomende modelleerfouten. Detecteer en verhelp dit systematisch:

**Directe circulariteit (A → B → A):**
```
Fout: "Sanctie" gedefinieerd met genus "Straf"
      "Straf" gedefinieerd met genus "Sanctie"
Oplossing: bepaal welk begrip breder is en maak dat het genus.
      "Sanctie" = maatregel opgelegd bij overtreding
      "Straf" = sanctie bestaande uit...
```

**Indirecte circulariteit (A → B → C → A):**
- Bouw een gerichte graaf van genus-relaties
- Voer een topologische sortering uit
- Als de sortering faalt (cyclus gedetecteerd), breek de cyclus op de zwakste schakel

**Detectieprocedure:**
1. Maak een lijst van alle genus-relaties: `begrip → genus`
2. Teken de graaf (of gebruik een eenvoudige matrixnotatie)
3. Controleer of de graaf een DAG (gerichte acyclische graaf) is
4. Als er een cyclus is: bepaal welk begrip het meest fundamenteel is en kies daarvoor een extern genus (buiten de cyclus)

**Signalen van verborgen circulariteit:**
- Twee begrippen die "elkaar nodig hebben" om gedefinieerd te worden
- Een genus dat zelf niet gedefinieerd is in het model
- Een begrip waarvan het genus op hetzelfde abstractieniveau zit

### Stap 6: Grensgevallen Modelleren

Sommige begrippen passen niet duidelijk in één categorie. Modelleer deze expliciet:

**Type-Proces grensgevallen:**
- "Registratie" — kan het registreren (PROCES) of het geregistreerde (TYPE/RESULTAAT) zijn
- Oplossing: maak twee begrippen als het domein beide betekenissen kent:
  - `registreren` (PROCES): activiteit waarbij gegevens worden vastgelegd
  - `registratie` (RESULTAAT): resultaat van het registreren; het vastgelegde gegeven

**Type-Resultaat grensgevallen:**
- "Beschikking" — is het een documenttype (TYPE) of het resultaat van beschikken (RESULTAAT)?
- Test: heeft het begrip een duidelijk bronproces? → RESULTAAT. Is het een zelfstandige klasse? → TYPE.

**Ambigue begrippen over rechtsgebieden:**
- "Sanctie" in strafrecht = straf. In bestuursrecht = bestuurlijke maatregel. In internationaal recht = handelsmaatregel.
- Oplossing: modelleer als apart begrip per rechtsgebied, of definieer het overkoepelende begrip met de gemeenschappelijke kern

**Beslismatrix voor grensgevallen:**

| Vraag | Ja → | Nee → |
|-------|------|-------|
| Heeft het een duidelijk bronproces? | RESULTAAT | → volgende vraag |
| Ontvouwt het zich in de tijd? | PROCES | → volgende vraag |
| Is het een uniek, specifiek geval? | EXEMPLAAR | TYPE |

### Stap 7: Hiërarchische Ordening

Bouw het model top-down:

```
Niveau 0: Metabegrippen (categorie-aanduidingen zelf)
    ↓
Niveau 1: Kernbegrippen (meest abstracte types in het domein)
    ↓
Niveau 2: Hoofdcategorieën (directe specialisaties van kernbegrippen)
    ↓
Niveau 3: Specifieke begrippen (concrete toepassingen)
    ↓
Niveau 4: Exemplaren (indien nodig, specifieke gevallen)
```

**Voorbeeld hiërarchie strafrecht:**
```
Niveau 1: Maatregel
    ├── Niveau 2: Sanctie
    │       ├── Niveau 3: Geldboete
    │       ├── Niveau 3: Taakstraf
    │       └── Niveau 3: Gevangenisstraf
    └── Niveau 2: Vrijheidsbeperkende maatregel
            ├── Niveau 3: Voorlopige hechtenis
            └── Niveau 3: TBS
```

**Generatie-volgorde**: definieer ALTIJD het genus-begrip VOORDAT je het species-begrip definieert. Dit voorkomt dat je moet terugkomen om eerder gegenereerde definities aan te passen.

### Stap 8: Definitie-generatie in Samenhang

Nu pas genereer je definities, met het model als leidraad:

1. **Genus uit het model**: gebruik het directe bovenliggende begrip als genus (toetsregel STR-02)
2. **Differentia uit zusterbegrippen**: de differentia moet het begrip onderscheiden van zijn zusterbegrippen (toetsregel ESS-05)
3. **Procesrelaties controleren**: als een RESULTAAT een bronproces heeft, verwijs daarnaar in de definitie
4. **Rolconsistentie**: als een Role verwijst naar een proces, moet dat proces ook in het model zitten
5. **Samenhang-validatie**: controleer dat de definitie past bij de definities van verwante begrippen (SAM-regels)

## Modelformaten

### Eenvoudig (CSV/tabel)

```csv
begrip,categorie,ufo_stereotype,genus,differentia,relaties,bron
sanctie,TYPE,kind,maatregel,"opgelegd bij overtreding van een norm","is-een: maatregel; leidt-tot: tenuitvoerlegging","Sr art. 9"
geldboete,TYPE,subkind,sanctie,"bestaande uit betaling van een geldbedrag","is-een: sanctie","Sr art. 23"
toezicht,PROCES,process,activiteit,"waarbij naleving van voorwaarden wordt gecontroleerd","uitgevoerd-door: toezichthouder","Awb hfst. 5"
vonnis,RESULTAAT,,uitspraak,"van de rechter na behandeling ter terechtzitting","resultaat-van: berechting; heeft-deel: strafmaat","Sv art. 345"
```

### Uitgebreid (OntoUML-compatibel)

Voor formele modellering, gebruik OntoUML-stereotypen. Een OntoUML-model biedt:
- Formele verificatie van ontologische correctheid (geen Kind-onder-Kind, rollen altijd met relator)
- Visuele weergave van het domein
- Export naar OWL/RDF voor machineleesbare verwerking

**OntoUML-stereotypen voor klassen:**
- `«kind»` voor onafhankelijke typen (Persoon, Document, Organisatie)
- `«subkind»` voor rigide specialisaties (Paspoort, Rijbewijs)
- `«role»` voor contextafhankelijke typen (Verdachte, Schuldeiser)
- `«phase»` voor levensfasen (Minderjarige, Actieve zaak)
- `«relator»` voor gereificeerde relaties (Huwelijk, Arbeidsovereenkomst)
- `«collective»` voor groepen (Commissie, Meervoudige kamer)

**OntoUML-stereotypen voor relaties:**
- `«material»` voor materiële relaties ("werkt voor", "is eigenaar van")
- `«mediation»` voor relator-koppelingen
- `«characterization»` voor eigenschap-koppelingen
- `«componentOf»` voor deel-geheel

### NL-SBB-compatibel

Voor aansluiting bij Nederlandse overheidsstandaarden, modelleer begrippen conform NL-SBB:
- Elk begrip krijgt een URI (unieke identificatie)
- Elke term is gekoppeld aan precies één begrip
- Elke definitie volgt genus-differentia-structuur
- Bronvermelding is verplicht

## Kwaliteitscriteria voor het Model

1. **Elk begrip heeft exact één categorie** (TYPE/PROCES/RESULTAAT/EXEMPLAAR)
2. **Elk TYPE-begrip heeft een genus** (behalve de top-level begrippen in het domein)
3. **Geen circulaire genus-ketens** (gecontroleerd met de detectieprocedure uit stap 5)
4. **Processen hebben minimaal één relatie** (input, output, actor, of bovenliggend proces)
5. **Rollen zijn gekoppeld aan processen of relators** (wie doet wat, in welke context?)
6. **Volledigheid**: alle begrippen uit de relevante wetteksten zijn opgenomen
7. **Geen zwevende begrippen**: elk begrip is verbonden met minstens één ander begrip
8. **Grensgevallen zijn expliciet opgelost** (geen begrippen met twijfelachtige categorisatie)
9. **Synoniemen zijn gemarkeerd** en gekoppeld aan het voorkeursbegrip
10. **Het model is geordend**: top-down van abstract naar concreet

## Integratie met DefinitieAgent

Het ontologisch model verrijkt de definitie-generatie op meerdere manieren:

- **Genus-suggestie**: het model levert het juiste genus voor toetsregel STR-02
- **Context-verrijking**: gerelateerde begrippen als context voor RAG (ophalen van relevante informatie)
- **Consistentie-controle**: valideer dat nieuwe definities passen in het bestaande model
- **Samenhang-validatie**: SAM-regels (SAM-01 t/m SAM-08) kunnen geautomatiseerd worden tegen het model
- **Generatie-volgorde**: het model bepaalt in welke volgorde begrippen gedefinieerd moeten worden
- **Differentia-suggestie**: zusterbegrippen in het model helpen bij het formuleren van onderscheidende kenmerken (ESS-05)
