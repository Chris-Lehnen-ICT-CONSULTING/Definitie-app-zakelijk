# UFO-Ontologie — Volledige Referentie

> On-demand referentie bij `definitie-ufo-ontologie`. Bevat het academisch UFO-overzicht, OntoUML 2.0 en de mapping naar de DefinitieAgent-categorieen.

## UFO Academisch Overzicht

UFO bestaat uit drie complementaire lagen die samen de volledige werkelijkheid beschrijven:

### UFO-A — Endurants (objecten in de tijd)

Endurants zijn entiteiten die op elk moment volledig aanwezig zijn (al hun essentiële delen bestaan tegelijk). UFO-A onderscheidt:

**Substantiële Endurants** — onafhankelijk bestaande entiteiten:

| UFO Type | Betekenis | Identiteit | Voorbeeld |
|----------|-----------|------------|-----------|
| **Kind** | Onafhankelijk type met eigen identiteitscriterium | Levert identiteitscriterium | Persoon, Voertuig, Document |
| **Subkind** | Rigide specialisatie van een Kind (altijd lid) | Erft identiteit van Kind | Vrachtauto (subkind van Voertuig) |
| **Role** | Anti-rigide, relationeel afhankelijke classificatie | Erft identiteit; vereist relatie | Verdachte, Toezichthouder, Schuldeiser |
| **Phase** | Anti-rigide, intrinsieke toestandsverandering | Erft identiteit; intrinsieke conditie | Minderjarige → Meerderjarige, Actief → Inactief |
| **RoleMixin** | Abstracte rol over meerdere Kinds | Geen eigen identiteit | Bewoonbaar (geldt voor gebouw én schip) |
| **Category** | Abstracte rigide eigenschap over Kinds | Geen eigen identiteit | Levend wezen (geldt voor mens én dier) |
| **Mixin** | Abstracte semi-rigide eigenschap | Geen eigen identiteit | Geregistreerd object |
| **Collective** | Verzameling entiteiten als eenheid | Eigen identiteit via lidmaatschap | Commissie, Raad, Gezin |
| **Quantity** | Hoeveelheid van materie | Identiteit via hoeveelheid | Geldbedrag, Partij goederen |

**Moment-endurants** — afhankelijke, inherente eigenschappen:

| UFO Type | Betekenis | Afhankelijkheid | Voorbeeld |
|----------|-----------|-----------------|-----------|
| **Mode** | Intrinsieke eigenschap die NIET direct meetbaar is (disposities, vaardigheden) | Inhereert in één entiteit | Bevoegdheid, Vaardigheid, Intentie |
| **Quality** | Intrinsieke eigenschap die WEL direct meetbaar is in een waardeschaal | Inhereert in één entiteit; heeft waarde in Quality Space | Leeftijd (in jaren), Gewicht (in kg), Lengte |
| **Relator** | Waarheidsmaker van materiële relaties tussen entiteiten | Mediëert tussen 2+ entiteiten | Huwelijk, Arbeidsovereenkomst, Eigendomsrecht |

**Belangrijk onderscheid Mode vs Quality:**
- **Quality**: heeft een geassocieerde *kwaliteitsruimte* (meetschaal). Leeftijd = getal op tijdschaal. Kleur = punt in kleurruimte.
- **Mode**: heeft GEEN meetschaal maar is wel intrinsiek. Bevoegdheid = dispositie die een persoon bezit. Een intentie = mentale toestand.
- Vuistregel: "Kun je het uitdrukken als een getal of punt op een schaal?" → Quality. "Is het een vermogen, dispositie of mentale toestand?" → Mode.

### UFO-B — Perdurants (gebeurtenissen in de tijd)

Perdurants ontvouwen zich in de tijd — ze hebben temporale delen (begin, midden, einde). UFO-B onderscheidt:

| UFO Type | Betekenis | Kenmerken | Voorbeeld |
|----------|-----------|-----------|-----------|
| **Event** | Atomaire, tijdsgebonden gebeurtenis | Heeft begin- en eindpunt; is ondeelbaar op relevant abstractieniveau | Aanhouding, Uitspraak, Ondertekening |
| **Process** | Samengestelde, voortdurende activiteit | Bestaat uit sub-events; heeft duur | Strafrechtelijk onderzoek, Toezichthouden |
| **Situation** | Momentopname van de werkelijkheid op een tijdstip | Beschrijft een configuratie van entiteiten en hun eigenschappen | "Verdachte is voorlopig gehecht", "Vergunning is verlopen" |

**Situation** is cruciaal voor juridisch modelleren: veel juridische concepten beschrijven een *toestand* (bijv. "voorlopige hechtenis", "onherroepelijk vonnis") die geen activiteit is maar een snapshot van de werkelijkheid.

**Relatie Event–Situation:** Gebeurtenissen (Events) veroorzaken overgangen tussen situaties (Situations). Een Aanhouding (Event) brengt de situatie "persoon is aangehouden" tot stand.

### UFO-C — Sociale en Intentionele Entiteiten

UFO-C modelleert de sociale werkelijkheid die essentieel is voor het juridische domein:

| UFO Type | Betekenis | Voorbeeld |
|----------|-----------|-----------|
| **Agent** | Entiteit met intentionaliteit en handelingsvermogen | Persoon, Organisatie |
| **InstitutionalAgent** | Agent gecreëerd door sociale constructie | Rechtspersoon, Bestuursorgaan, NV, BV |
| **SocialObject** | Entiteit die bestaat door sociale conventie | Wet, Norm, Recht, Verplichting |
| **Norm** | Sociale regel die gedrag voorschrijft of verbiedt | Wettelijke bepaling, Gedragsregel |
| **Commitment** | Toezegging/verplichting tussen agenten | Contractuele verplichting, Borgsom |
| **Claim** | Recht/aanspraak van een agent jegens een ander | Recht op bijstand, Vorderingsrecht |
| **SocialMoment** | Sociale eigenschap (niet-fysiek) | Rechtsbevoegdheid, Burgerlijke staat |
| **InstitutionalRole** | Rol geconstitueerd door een institutie | Rechter, Officier van Justitie, Notaris |

**UFO-C is essentieel voor juridische definities** omdat vrijwel alle juridische begrippen sociale constructies zijn: rechten, plichten, rollen, normen en instituties bestaan bij de gratie van sociale/institutionele conventies.

### UFO-L — Juridische Kernontologie (uitbreiding op UFO-C)

UFO-L (Griffo et al., 2021) is een specialisatie van UFO-C voor het juridische domein:

| UFO-L Type | Basis | Betekenis | Voorbeeld |
|------------|-------|-----------|-----------|
| **LegalNorm** | Norm | Juridische norm met rechtskracht | Art. 287 Sr (doodslag) |
| **LegalRole** | Role | Juridische rol ontstaan uit norm | Verdachte (art. 27 Sv) |
| **LegalRelator** | Relator | Juridische relatie tussen partijen | Arbeidsovereenkomst, Huurrecht |
| **LegalRight** | Claim | Subjectief recht | Eigendomsrecht, Vorderingsrecht |
| **LegalDuty** | Commitment | Juridische plicht | Zorgplicht, Meldplicht |
| **LegalEvent** | Event | Rechtshandeling of rechtsfeit | Ontslag, Huwelijksvoltrekking |

UFO-L helpt bij het classificeren van juridische begrippen omdat het de UFO-categorieën toespitst op het recht.

## OntoUML 2.0 — Modelleringstaal gebaseerd op UFO

OntoUML is de formele modelleringstaal gebaseerd op UFO. OntoUML 2.0 (Guizzardi et al., 2022) biedt stereotypen die direct corresponderen met UFO-types:

### Stereotypen voor Klassen

| Stereotype | UFO Type | Rigiditeit | Identiteit | Gebruik |
|-----------|----------|-----------|------------|---------|
| `«kind»` | Kind | Rigide | Levert | Basistypen (Persoon, Document) |
| `«subkind»` | Subkind | Rigide | Erft | Specialisaties (Paspoort, Rijbewijs) |
| `«role»` | Role | Anti-rigide | Erft | Contextuele rollen (Verdachte, Rechter) |
| `«phase»` | Phase | Anti-rigide | Erft | Levensfasen (Minderjarig, Actief) |
| `«relator»` | Relator | Rigide | Levert | Reificatie van relaties (Huwelijk) |
| `«mode»` | Mode | — | — | Disposities (Bevoegdheid) |
| `«quality»` | Quality | — | — | Meetbare eigenschappen (Leeftijd) |
| `«collective»` | Collective | Rigide | Levert | Groepen (Commissie, Raad) |
| `«quantity»` | Quantity | Rigide | Levert | Hoeveelheden (Geldbedrag) |
| `«category»` | Category | Rigide | Geen | Abstracte typen over kinds |
| `«mixin»` | Mixin | Semi-rigide | Geen | Gedeelde eigenschappen |
| `«roleMixin»` | RoleMixin | Anti-rigide | Geen | Abstracte rollen |

### Relatie-stereotypen

| Stereotype | Betekenis | Voorbeeld |
|-----------|-----------|-----------|
| `«material»` | Materiële relatie (via Relator) | "werkt voor" (via Arbeidsovereenkomst) |
| `«formal»` | Formele relatie (vergelijking) | "is zwaarder dan" |
| `«mediation»` | Relator verbindt partijen | Huwelijk mediëert echtgenoten |
| `«characterization»` | Mode/Quality inhereert in entiteit | Bevoegdheid karakteriseert Persoon |
| `«componentOf»` | Deel-geheel | Strafmaat componentOf Vonnis |
| `«memberOf»` | Lid-collectief | Rechter memberOf Rechtbank |
| `«subCollectionOf»` | Deelverzameling | Kamer subCollectionOf Rechtbank |

### OntoUML-restricties (formele beperkingen)

OntoUML bevat formele restricties die modelleerfouten voorkomen:
- Een `«kind»` mag NIET specialisatie zijn van een ander `«kind»` (identiteitsconflict)
- Een `«role»` MOET via een `«mediation»`-relatie verbonden zijn met een `«relator»`
- Een `«phase»` MOET onderdeel zijn van een fasepartitie (uitputtend en exclusief)
- `«quality»` MOET een geassocieerde kwaliteitsruimte (waardeschaal) hebben

## Mapping naar DefinitieAgent (4 categorieën)

De DefinitieAgent vereenvoudigt UFO tot 4 werkbare categorieën. Deze mapping is een bewuste reductie om de app bruikbaar te houden. De vier appkeuzes zijn een projectmatige vereenvoudiging, geen vier disjuncte hoofdcategorieën van UFO: type/particulier geeft het betekenisniveau aan; activiteit en resultaat geven een andere, inhoudelijke dimensie aan. Een activiteit of resultaat kan een algemeen begrip of één bepaald ding (ook abstract) of voorval zijn. "Er is nu precies één" bepaalt niet zelfstandig het niveau. Leg bedoelde betekenis en grond vast; forceer onbekende of overlappende gevallen niet via een suffix of prioriteitsvolgorde (ESS-02, [`references/ess02-betekenisniveau.md`](references/ess02-betekenisniveau.md) — kopie van de canonieke bron in `definitie-toetsregels`):

| App Categorie | Code | UFO Mapping | Wat gaat verloren |
|---------------|------|-------------|-------------------|
| **TYPE** | `type` | Kind, Subkind, Role, Phase, Category, Mixin, RoleMixin, Collective, Quantity, Mode, Quality, InstitutionalAgent, SocialObject | Onderscheid rigide/anti-rigide; onderscheid substantieel/moment |
| **PROCES** | `proces` | Event, Process (UFO-B) | Onderscheid atomair/samengesteld; Situation wordt apart behandeld |
| **RESULTAAT** | `resultaat` | Producten/uitkomsten van Events/Processes | Geen direct UFO-equivalent; is een pragmatische categorie |
| **EXEMPLAAR** | `exemplaar` | Particulieren (individuele instanties van elk type) | Onderscheid welk type het een instantie VAN is |

### Kanttekening bij RESULTAAT

RESULTAAT heeft geen direct equivalent in UFO. Het is een pragmatische categorie die in de DefinitieAgent verwijst naar artefacten die ontstaan als uitkomst van een proces. In UFO zou een "vonnis" een **SocialObject** zijn (UFO-C), geproduceerd door een **Event** (uitspreken vonnis). De app kiest ervoor dit als RESULTAAT te classificeren vanwege het belang van de relatie met het bronproces.

### Wanneer welke richting?

De richtingen overlappen: een algemeen activiteitbegrip is TYPE (niveau) én PROCES (aard); één bepaald voorval is EXEMPLAAR (niveau) én bijvoorbeeld PROCES (aard). Suffix-indicatoren zijn classificatiehulp voor een voorstel, geen betekenisbewijs.

**TYPE** — Wanneer je een algemeen begrip (klasse/soort) definieert:
- "Wat IS een verdachte?" → TYPE (Role in UFO: anti-rigide, relationeel afhankelijk)
- "Wat IS een beschikking?" → TYPE (Kind in UFO: zelfstandig type)
- Suffix-indicatoren (hulp): `-heid`, `-schap`, `-isme`, `-systeem`, `-model`, `-recht`, `-plicht`

**PROCES** — Wanneer de kern een activiteit/handeling is:
- "Wat IS een aanhouding?" → PROCES (Event in UFO: atomaire gebeurtenis)
- "Wat IS een opsporingsonderzoek?" → PROCES (Process in UFO: samengestelde activiteit)
- Suffix-indicatoren (hulp): `-ing`, `-atie`, `-tie`, `-eren`, `-isatie`, `-onderzoek`
- Onderscheid waar nodig het algemene begrip van één bepaald voorval; een activiteit mag haar uitkomst noemen zonder van aard te veranderen

**RESULTAAT** — Wanneer de kern een uitkomst/product van een proces is:
- "Wat IS een vergunning?" → RESULTAAT (uitkomst van vergunningverlening)
- "Wat IS een vonnis?" → RESULTAAT (uitkomst van berechting)
- Suffix-indicatoren (hulp): `-besluit`, `-vergunning`, `-rapport`, `-beschikking`, `-akte`
- Let op: beoordeel of het begrip een onderbouwde ontstaansrelatie met een activiteit heeft. Zo niet, dan is een andere richting waarschijnlijk passender — maar bevestig de bedoeling in plaats van terug te vallen op een default.

**EXEMPLAAR** — Wanneer je één bepaald ding (ook abstract) of voorval definieert:
- "Wat IS de zaak-Wilders?" → EXEMPLAAR (specifiek, uniek rechtsgeval)
- Zelden in juridische definities; meestal TYPE of PROCES
- Test: "Bedoelt het begrip één bepaald ding of voorval, of een algemeen begrip, ook als er nu maar één geval bestaat? Een specifiek proces of resultaat houdt daarnaast zijn aard."

### Classificatie-algoritme

Het classificatieproces in de app volgt deze prioriteitscascade. Het levert een modelvoorstel: geen bevestiging van de bedoelde betekenis en geen ESS-02-bewijs. Alleen een bewuste handmatige keuze (actor, tijd, versie) bevestigt de daarin uitgedrukte bedoeling; bij werkelijke tegenspraak met bron of context wordt de betekenis eerst verduidelijkt.

1. **Domain overrides** (hoogste prioriteit): hardcoded mappings voor ambigue termen
2. **Suffix-matching**: gewogen score per suffix-patroon (0.0–1.0)
3. **Context-boosts**: organisatorische/juridische context verhoogt score
4. **Confidence scoring**: `margin = winner - runner_up`, label = HIGH (≥0.70) / MEDIUM (≥0.45) / LOW (<0.45)
5. **Tie-breaking**: prioriteitsvolgorde EXEMPLAAR > TYPE > RESULTAAT > PROCES

### Moeilijke gevallen en vuistregels

Sommige begrippen zijn lastig te classificeren. De vuistregels hieronder zijn hulp bij een voorstel, geen betekenisbewijs; de gekozen richting moet passen bij de onderbouwde bedoeling en de definitiekern, en het inhoudelijke ESS-02-oordeel blijft aan de mens:

| Geval | Analyse | Classificatie |
|-------|---------|---------------|
| "registratie" | Kan proces (het registreren) OF resultaat (het geregistreerde) zijn | Kies op basis van GEBRUIK in het domein. In DJI: meestal RESULTAAT |
| "toezicht" | Is een voortdurende activiteit | PROCES (Process in UFO) |
| "recidive" | Is een toestand/patroon, geen handeling | TYPE (Phase in UFO: intrinsieke toestandsverandering) |
| "sanctie" | Is een klasse van maatregelen | TYPE (Kind in UFO) |
| "voorwaardelijke invrijheidstelling" | Is een juridische toestand | TYPE (Phase in UFO) — NIET PROCES, want het is geen handeling |
| "vergunning" | Is het resultaat van vergunningverlening | RESULTAAT — heeft duidelijk bronproces |
| "bevoegdheid" | Is een vermogen/dispositie | TYPE (Mode in UFO: intrinsieke eigenschap) |

## Relatie met Nederlandse Standaarden

### MIM (Metamodel Informatiemodellering)
MIM is de Nederlandse standaard voor informatiemodellering bij de overheid. UFO en MIM delen concepten:
- MIM "Objecttype" ≈ UFO Kind
- MIM "Relatiesoort" ≈ UFO Relator/materiële relatie
- MIM "Enumeratie" ≈ UFO Phase partition
- De DefinitieAgent kan begrippen modelleren die later in MIM-conforme modellen landen

### NORA (Nederlandse Overheid Referentie Architectuur)
NORA hanteert een begrippenmodel dat aansluit bij UFO:
- NORA "Begrip" ≈ UFO universele (class-level concept)
- NORA "Term" ≈ linguïstische representatie van een begrip
- De DefinitieAgent definieert begrippen conform NORA-principes

### NL-SBB (Standaard voor het Beschrijven van Begrippen)
NL-SBB is de Nederlandse standaard voor begripsbeschrijvingen. De DefinitieAgent volgt NL-SBB door:
- Begrippen te onderscheiden van termen
- Definities te formuleren als genus-differentia
- Bronvermelding op te nemen als metadata
