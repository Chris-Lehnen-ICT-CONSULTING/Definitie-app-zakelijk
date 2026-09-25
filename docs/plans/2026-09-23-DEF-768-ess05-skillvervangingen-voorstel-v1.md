# DEF-768 — ESS-05: voorstel zes skillvervangingen (WP8-voorbereiding, v1)

23 september 2026 · uitvoerder Claude Code CLI (sessie `6d273f41-0afb-480a-9034-1c87b1ecba58`) · branch `feature/DEF-768-ess05-ai-beoordeling`, basis `26f2374d3`, softwarediff met totaalhash `4dd4d61a…b1d12abe` (door Codex akkoord bevonden; hier niet gewijzigd).

**Status: voorstel, niet toegepast.** De centrale gedeelde skillbestanden zijn niet gewijzigd. Dit document geeft per doelbestand het bestaande fragment met vindplaats en de volledige vervangende of toe te voegen tekst. Publicatie is een afzonderlijke, af te stemmen stap op de centrale setup-repo (§4). Er zijn geen modelcalls gedaan en er wordt geen kwaliteitswinst geclaimd: een skillwijziging bewijst geen betere generatie of menselijke beoordeling (synthese v3, stap 4–5).

## 1. Herkomst en voorrang

### 1.1 Bronnen (alleen gelezen, onveranderd)

Alle zes staan in de hoofdcheckout onder `docs/analyses/def606-regeldossiers/ESS-05-verdieping/`. De sha256 is vastgelegd in `logs/def768/wp8-bronhashes.log`, dat git negeert.

| Bron | Rol | sha256 |
|---|---|---|
| [onderzoek-b-v1.md §6.8](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260921/b-claude-cli/onderzoek-b-v1.md) (r. 261–288) | de zes oorspronkelijke vervangingen | `78c7f75b…995` |
| [verwerking-a-v1.md §2.5](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260921/a-cowork/verwerking-a-v1.md) (r. 85–92) | A's verwerking van G/T/H en skills | `0e14f86c…b30` |
| [besluiten-v1.md](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md) | productbesluiten K-1…K-10 | `6696dab5…01e` |
| [synthese-v3.md](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260923/gedeeld/synthese-v3.md) | **leidend**, actualisatie van 23 september | `6d3cc62d…41e` |
| [aanvulling-a-v1.md](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260923/onderzoek-a/aanvulling-a-v1.md) | Q3/Q5 (overlap, T-aanvulling) | `5aa5576b…c05` |
| [aanvulling-b-v1.md](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260923/onderzoek-b/aanvulling-b-v1.md) | Q1/Q2/Q5 (G/T/H, "zes skills … zelfde norm") | `feeb73b9…f28` |

De normtekst in dit voorstel volgt de gecorrigeerde app-implementatie in deze worktree:
- regelrecord `src/toetsregels/regels/ESS-05.json`;
- G-tekst `src/services/prompts/modules/json_based_rules_module.py:369–395`;
- T-instructie `src/services/validation/ess05_assessment_service.py:83–103`;
- uitkomstteksten `src/domain/ess05/contract.py`;
- [uitvoercontract](2026-09-23-DEF-768-ess05-contract-en-runplan-v1.md).

### 1.2 Voorrang: welke delen van §6.8 en §2.5 vervallen

Synthese v3 en de aanvullingen bepalen: "bij verschil gelden besluiten en deze synthese boven de historische O2-adviezen" en "vervang verouderde verwijzingen naar een toekomstige O3 of prioriteit hoog". Daarom wijkt dit voorstel op de volgende punten af van de historische teksten:

| Historische tekst (B §6.8 / A §2.5) | Waarom vervallen | Vervangen door |
|---|---|---|
| `**hoog**⁵` plus de voetnoot "Prioriteit volgens de lokale regelkaart; ASTRA hanteert midden (besluit onder DEF-768)" (B 1; A §2.5 "prioriteitswaarde laten staan met voetnoot") | K-4: prioriteit `midden` is besloten; het record zegt `midden` | `midden` zonder voorbehoud |
| "de mens (of een later goedgekeurde AI-substitutietoets) beoordeelt" (B 1) | K-1: direct O3, geen O2-tussenfase | "de app beoordeelt zelf met een AI-beoordeling per verwant begrip" |
| "zodat geen aangeleverd verwant begrip … aan alle kenmerken voldoet" (B 1) en "Voldoet een verwant begrip wél aan alle kenmerken … ESS-05-gebrek" (B 4) | Extensietoets; schendt K-3b (synthese v3 "Concreet resterend afstemmingspunt"; ESS05-E05) | Kenmerkvraag: per verwant begrip een onderbouwd verschil in kenmerken; overlap van gevallen is geen gebrek |
| "Zelftest: vul de definitie in voor elk verwant begrip — voldoet dat begrip eraan, dan is de definitie te breed" (B 2) | Kan als extensietoets worden gelezen | Zelftest op kenmerkniveau, met de expliciete rol-overlap-uitzondering |
| "de differentia moet elk daarvan uitsluiten" (B 3) | "uitsluiten" suggereert disjuncte gevallen | "moet elk daarvan in kenmerken onderscheiden" |
| "Dit voorstel geldt pas na het ESS-05-besluit." (B 1) | Het besluit is genomen (K-1…K-10) | Vervallen |
| "ESS-05 niet te beoordelen zonder toespitsing, STR-04 eigenaar" (A §3 K-8-voorkeur) | K-8: elke regel meldt zelf | Eigen ESS-05-reden naast STR-04 |
| "`context_lists` … ondersteunend" (A §2.4) | K-9: context verplicht | Zonder context: niet uitgevoerd |
| Het nieuwe referentiebestand als "N1 (§2.4), G (§6.5), T (§6.6), H (§6.7)" (B 1) | §6.5–6.7 zijn historische O2-teksten | Het referentiebestand in §3.1, afgestemd op de gebouwde app |

Wat vanuit §6.8 inhoudelijk blijft, met aangepaste woorden:
- het nieuwe referentiebestand;
- de SKILL.md-sectie;
- de verbreding van 'zusterbegrippen' naar 'verwante begrippen';
- het ontologiemodel als vergelijkingsruimte die het onderscheid niet zelf bewijst;
- één tegenvoorbeeld per verwant begrip;
- de UFO-passage over rollen met overlappende extensie;
- de contextgebondenheid van juridische buren (A §2.5: items 5–6 overgenomen).

### 1.3 Normkern: moet in alle zes skills gelijk zijn

Elke vervanging hieronder draagt, waar het in dat bestand relevant is, dezelfde tien punten:

1. **Direct O3.** De app beoordeelt ESS-05 zelf met een AI-beoordeling per verwant begrip, op alleen het aangeleverde materiaal (K-1).
2. **Kenmerkvraag en toegestane overlap (K-3b).** Per verwant begrip moet de kern een onderbouwd verschil in kenmerken uitdrukken. Een persoon of object dat beide rollen vervult, bewijst op zichzelf geen gebrek (E05 lener/werknemer voldoet; E06 "geregistreerd persoon" tweemaal voldoet niet).
3. **Prioriteit `midden`** (ASTRA; K-4).
4. **Geen cijfer en geen zelfstandige blokkade.** Een negatieve of open uitkomst blokkeert vaststellen of export niet (K-4).
5. **Contextplicht.** Zonder context: "niet uitgevoerd" met reden (K-9).
6. **Burenprovenance.** Herkomst gebruiker, bron, repository, model of ontologie (de laatste gereserveerd, DEF-300), plus bevestigingsstatus. Modelvoorstellen blijven `model` en onbevestigd, ook met een broncitaat. Het citaat is een aparte bronverwijzing (K-1, K-6).
7. **Open of leeg bevestigd.** Zonder bevestigd verwant begrip: "nog te beoordelen" met precies één vraag. Een deskundige kan de lege vergelijkingsruimte met grond bevestigen: "voldoet — leeg bevestigd", gebonden aan de versie en vervallend bij wijziging (K-2).
8. **Eigen reden naast STR-04.** Ontbreekt de toespitsing, dan meldt ESS-05 zelf "kan zonder toespitsing geen enkel verwant begrip uitsluiten" (K-8).
9. **Geen automatisch herstel.** Toetsen wijzigt geen tekst. Hoogstens één begrensde poging op verzoek, onder DEF-638 (K-7).
10. **Vorm.** Een vergelijkingszin is een vormoptie en geen bewijs. 'Uniek', 'specifiek', 'bijzonder' en 'kenmerk' zijn geen kenmerk. Een contrast dat de definitie van het andere begrip nodig heeft, hoort in de toelichting (K-3a).

## 2. Doelbestanden en hun vastgelegde stand

- **Beheerde bron:** `~/Projecten/_claude-global-setup/skills/`, HEAD `dc7dc644438a05d602f05bc115ae16ac85b83169` op `main`, zonder ongecommitte wijzigingen in `skills/`.
- **Live kopie:** `~/.claude/skills/` is bij alle negen geraakte bestanden byte-gelijk aan de repo (`logs/def768/wp8-skillbronnen.log`).
- **Regelnummers** hieronder verwijzen naar die HEAD.

| # | Skill | Geraakte bestanden (sha256 bij HEAD, eerste 12) |
|---|---|---|
| 1 | `definitie-toetsregels` | `reference.md` (`f32521057593`), `SKILL.md` (`21b4157cff82`), **nieuw** `references/ess05-onderscheid.md` (canoniek) |
| 2 | `definitie-nederlandse-definities` | `reference.md` (`1be4bfce2563`), `SKILL.md` (`f8239b09a1ba`), **nieuw** `references/ess05-onderscheid.md` (byte-identieke kopie) |
| 3 | `definitie-ontologisch-modelleren` | `reference.md` (`3833f358a454`) |
| 4 | `definitie-voorbeelden-generatie` | `reference.md` (`0e656b52cb2b`), `SKILL.md` (`cf639d791edc`) |
| 5 | `definitie-ufo-ontologie` | `reference.md` (`d078ad7e394d`) |
| 6 | `definitie-juridisch-nederland` | `reference.md` (`acb3182221ef`) |

**Nieuwe referentietekst voor `definitie-toetsregels`:**
- canonieke bron: `definitie-toetsregels/references/ess05-onderscheid.md` (volledige tekst in §3.1);
- byte-identieke kopie: `definitie-nederlandse-definities/references/ess05-onderscheid.md`, volgens de bestaande ESS-03/ESS-04-conventie ("wijzig alleen de canonieke bron en kopieer die opnieuw", `ess04-toetsbaarheid.md:3`);
- de andere vier skills verwijzen er met skillnaam en pad naar.

## 3. De zes vervangingen

### 3.1 `definitie-toetsregels`

**(a) `reference.md:48`**, bestaand:

```
| ESS-05 | Onderscheid van verwante begrippen | **hoog** | Maak expliciet duidelijk waarin het begrip zich onderscheidt van andere verwante begrippen |
```

Vervangen door:

```
| ESS-05 | Voldoende onderscheidend (van verwante begrippen) | **midden** ⁵ | Kies bovenbegrip en toespitsende kenmerken zodat de kern per verwant begrip in deze context een onderbouwd verschil in kenmerken uitdrukt; overlap van gevallen (één persoon in twee rollen) is geen gebrek; een vergelijkingszin is niet vereist en ‘uniek’/‘specifiek’/‘kenmerk’ zijn geen kenmerk — volledige N/G/T/H-instructie in [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md) |
```

**(b) `reference.md` na regel 52** (na voetnoot ⁴), toevoegen:

```
⁵ ESS-05 heeft prioriteit *midden* (ASTRA; besluit 21 september 2026, DEF-768) en levert geen cijfer en geen 0/1: de app beoordeelt zelf met een AI-beoordeling per verwant begrip (voldoet / voldoet niet / nog te beoordelen met precies één vraag / voldoet — leeg bevestigd / niet uitgevoerd zonder context / technische fout). Een negatief of open oordeel blokkeert vaststellen of export niet en start geen herschrijving. Zie [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md).
```

**(c) `reference.md` na regel 54** (na het ESS-03-blok), toevoegen:

```
> **ESS-05 — voldoende onderscheidend.** Met de definitie is het begrip te onderscheiden van de andere begrippen die in dezelfde context relevant zijn: de kern drukt ten opzichte van elk verwant begrip een onderbouwd verschil in kenmerken uit. Verwante begrippen zijn zusterbegrippen onder hetzelfde bovenbegrip, begrippen die in deze context verward kunnen worden of deels dezelfde gevallen dekken, en door bron of gebruiker aangewezen begrippen; niet het bovenbegrip, onderbegrippen, synoniemen of homoniemen in een andere context. Overlap van gevallen is geen gebrek zolang het onderscheidende kenmerk kenbaar is: dezelfde persoon kan lener en werknemer zijn. De app beoordeelt dit zelf met een AI-beoordeling per verwant begrip, op alleen het aangeleverde materiaal; elk verwant begrip draagt herkomst (gebruiker / bron / repository / model / ontologie) en bevestigingsstatus, en door het model voorgestelde begrippen blijven onbevestigd tot een deskundige ze bevestigt of afwijst. Zonder context wordt ESS-05 niet uitgevoerd; zonder bevestigd verwant begrip blijft het oordeel open met precies één vraag, tenzij een deskundige gemotiveerd bevestigt dat de vergelijkingsruimte in deze context leeg is. Ontbreekt de toespitsing, dan meldt ESS-05 dat zelf, naast STR-04. Prioriteit *midden*; geen cijfer, geen zelfstandige blokkade van vaststellen of export, geen automatische herschrijving. Contract: [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md). Besloten 21 september 2026 (DEF-768, K-1…K-10), aangevuld 23 september 2026 (synthese v3).
```

**(d) `SKILL.md:39`**. Vervang in de zin "…ESS-03 (AI-beoordeling van eenheid en identiteit in de app, vier uitkomsten zonder cijfer, […](references/ess03-eenheid-identiteit.md)), CON-01 …" het fragment `, CON-01 (uitkomst per treffer)` door:

```
, ESS-05 (AI-beoordeling van onderscheid per verwant begrip in de app, zonder cijfer, [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md)), CON-01 (uitkomst per treffer)
```

**(e) `SKILL.md` na regel 74** (na het ESS-04-blok), toevoegen:

```
## ESS-05 — voldoende onderscheidend

Lees bij genereren of toetsen het [gedeelde ESS-05-contract](references/ess05-onderscheid.md). De kern moet per verwant begrip in de vastgelegde context een onderbouwd verschil in kenmerken uitdrukken; overlap van gevallen (één persoon of object in twee rollen) is geen gebrek zolang het onderscheidende kenmerk kenbaar is. Een vergelijkingszin is een vormoptie, geen bewijs; ‘uniek’, ‘specifiek’ en ‘kenmerk’ zijn geen kenmerk. De app beoordeelt ESS-05 zelf met een AI-beoordeling per verwant begrip (herkomst en bevestigingsstatus per begrip; modelvoorstellen blijven onbevestigd). Zonder context: niet uitgevoerd. Zonder bevestigd verwant begrip: nog te beoordelen met precies één vraag, of 'voldoet — leeg bevestigd' na gemotiveerde deskundige bevestiging. Ontbrekende toespitsing: eigen ESS-05-reden naast STR-04. Prioriteit *midden*; geen ESS-05-cijfer, geen zelfstandige vaststel-/exportblokkade, geen automatische herschrijving. Skilladvies is geen opgeslagen beoordeling of expertbesluit.
```

**(f) `SKILL.md:78`**. Vervang de openingszin `> **Geen cijfer voor ESS-01, ESS-02, ESS-03 of CON-02; voorlopig geen totaalcijfer.**` door:

```
> **Geen cijfer voor ESS-01, ESS-02, ESS-03, ESS-05 of CON-02; voorlopig geen totaalcijfer.**
```

Voeg in dezelfde alinea direct na de ESS-03-zin (eindigend op "…[`references/ess03-eenheid-identiteit.md`](references/ess03-eenheid-identiteit.md).") in:

```
 ESS-05 krijgt evenmin een cijfer of 0/1 en kent geen zelfstandige blokkade: de app beoordeelt onderscheid per verwant begrip met een AI-beoordeling, prioriteit *midden* ordent de aandacht, een negatieve of open uitkomst blokkeert vaststellen/export niet en start geen herschrijving, en een technische fout is een afzonderlijke fout zonder oordeel — contract: [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md).
```

**(g) `SKILL.md:108`**, bestaand:

```
| **definitie-voorbeelden-generatie** | Illustratie — ESS-05 onderscheid aantonen via voorbeelden |
```

Vervangen door:

```
| **definitie-voorbeelden-generatie** | Illustratie — ESS-05: één tegenvoorbeeld per verwant begrip, met het kenmerk dat het verschil draagt; overlap van gevallen is geen tegenvoorbeeld |
```

**(h) `SKILL.md:113`**. Zet vóór `*Versie: 0.8 — DEF-767 …` het nieuwe versienummer:

```
*Versie: 0.9 — DEF-768 (ESS-05 voldoende onderscheidend: AI-beoordeling per verwant begrip, kenmerkvraag met toegestane overlap, prioriteit midden, geen cijfer, geen poort); 0.8 — DEF-767 …
```

De rest van de regel blijft ongewijzigd.

**(i) Nieuw bestand `references/ess05-onderscheid.md`**, volledige tekst:

````markdown
# ESS-05 — voldoende onderscheidend

Vastgesteld door Chris op 21 september 2026 (DEF-768, besluiten K-1…K-10), aangevuld op 23 september 2026 (synthese v3, overlap volgens K-3b). Canonieke bron: `definitie-toetsregels/references/ess05-onderscheid.md`; `definitie-nederlandse-definities` draagt een byte-identieke, versiegebonden kopie in zijn eigen `references/` zodat dat pakket zelfstandig leesbaar is — wijzig alleen de canonieke bron en kopieer die opnieuw. De app voert ESS-05 zelf uit als AI-beoordeling per verwant begrip. Bestaande CON-01/02- en ESS-01/02/03/04-afspraken blijven gelden. Dit advies is geen opgeslagen beoordeling, expertbesluit of vaststelling.

## N — norm en toetsvraag

**Naam:** Voldoende onderscheidend. **Prioriteit:** midden. **Aanbeveling:** verplicht.

> Met de definitie is het begrip te onderscheiden van de andere begrippen die in dezelfde context relevant zijn: de kern drukt ten opzichte van elk verwant begrip een onderbouwd verschil in kenmerken uit. Het onderscheid ligt in de gekozen kenmerken (bovenbegrip en toespitsing), niet in een vergelijkingsfrase of in de woorden 'uniek', 'specifiek' of 'kenmerk'.

**Verwante begrippen.** Zusterbegrippen onder hetzelfde bovenbegrip, begrippen die in deze context met het begrip verward kunnen worden of deels dezelfde gevallen dekken, en door bron of gebruiker aangewezen begrippen. Geen verwante begrippen zijn: het bovenbegrip, onderbegrippen, synoniemen en homoniemen in een andere context.

**Overlap.** Overlap van gevallen is geen gebrek zolang het onderscheidende kenmerk kenbaar is. Een persoon of object dat beide rollen vervult, bewijst op zichzelf geen gebrek. Dat geldt ook voor een onderscheid dat berust op een onderbouwd doelkenmerk (ESS-01 beoordeelt het kenmerk zelf).

**Vorm.** Een vergelijkende formulering is toegestaan als schrijfhulp, maar bewijst niets en vervangt geen kenmerk. Een contrast dat de definitie van het andere begrip nodig heeft, hoort in de toelichting.

**Toetsvraag:** Drukt de definitiekern in deze context ten opzichte van elk relevant verwant begrip een onderbouwd verschil in kenmerken uit, en is per verwant begrip aan te wijzen welk kenmerk in de kern dat verschil draagt?

### Voorbeelden

- Goed (ASTRA): `Incident waarbij een jeugdige zonder toestemming één van de volgende justitiële voorzieningen verlaat: de open justitiële jeugdinrichting of het terrein dat tot de gesloten justitiële jeugdinrichting behoort.` — de limitatieve voorzieningen sluiten ontvluchting uit.
- Fout (ASTRA): `Incident waarbij een jeugdige zonder toestemming de justitiële jeugdinrichting verlaat.` — ontvluchting voldoet aan alle kenmerken; niet te onderscheiden.
- Synthetisch, voldoet (E05): lener = `persoon met een actuele lening bij de instelling`, verwant begrip werknemer = `persoon met een arbeidsovereenkomst met de instelling`. Eén persoon kan beide zijn; de rolkenmerken verschillen.
- Synthetisch, voldoet niet (E06): twee begrippen die beide `persoon die in het systeem is geregistreerd` luiden. Er is geen onderbouwd verschil; een gedeelde passage onderscheidt niets.

## G — bij formuleren

> Kies een bovenbegrip en toespitsende kenmerken die het begrip binnen de gegeven context onderscheiden van de aangeleverde verwante begrippen: de kern drukt per verwant begrip een onderbouwd verschil in kenmerken uit ten opzichte van de beschrijving van dat begrip. Overlap van gevallen is geen gebrek: een persoon of object dat beide rollen vervult, maakt de definitie niet onvoldoende onderscheidend, zolang het onderscheidende kenmerk kenbaar is. Ontleen de kenmerken aan de aangeleverde bronnen en de bedoelde betekenis; verzin geen verwant begrip, kenmerk of bron, en vernauw de betekenis niet verder dan de bron draagt om een verschil te maken. Een onderscheidend kenmerk mag geen niet-begripsbepalend doel of gebruik zijn (ESS-01). Een korte vergelijkende formulering zonder de definitie van het andere begrip is toegestaan wanneer de kern anders onduidelijk blijft; een contrast dat de definitie van het andere begrip nodig heeft, hoort niet in de kern — de app kan het als toelichtingsvoorstel apart aanbieden. De woorden ‘uniek’, ‘specifiek’, ‘bijzonder’ en ‘onderscheidend kenmerk’ zijn geen kenmerk en horen niet in de kern. Zijn geen verwante begrippen aangeleverd, lever dan één kandidaat op grond van de bron; de vergelijking blijft bij de ESS-05-beoordeling open. Spreken bronnen of context elkaar tegen over de afgrenzing of over wat een verwant begrip is, maak dan geen stille keuze. Laat registratiecontext en bronadministratie buiten de kern, met behoud van inhoudelijk noodzakelijke namen (CON-01).

Aanvullend buiten de app-prompt:
- Zonder vastgelegde context wordt niet gegenereerd (K-9). Vraag om de context en verzin haar niet.
- Zelf bedachte verwante begrippen zijn onbevestigde voorstellen. Presenteer ze apart, niet als bronfeit.

## T — toetsinstructie (de app voert deze uit)

De tekst hieronder is de toetsinstructie van de app, met één aanpassing voor lezers. In de app staat aan het slot "meld dat dan als lacks_differentia"; hier staat "meld dat dan als eigen ESS-05-reden".

> Beoordeel de ongewijzigde definitiekern bij de vastgelegde term, bedoelde betekenis, context en kandidaatversie. Beoordeel per aangeleverd verwant begrip of de kern in deze context een onderbouwd verschil in kenmerken uitdrukt ten opzichte van de beschrijving van dat begrip. Zo nee, dan onderscheidt de definitie het begrip daar niet van: benoem het ontbrekende of te ruime kenmerk. Zo ja, citeer het kenmerk in de kern dat het verschil draagt. Beoordeel of de begripsbeschrijvingen in de vastgelegde context een onderbouwd verschil in kenmerken uitdrukken. Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek. Benoem het verschil, het werkelijk ontbrekende kenmerk of de ontbrekende informatie. Een onbesliste buurrelatie blijft open met één vraag; toetsen wijzigt de kern niet. Een vergelijkingsfrase, het woord 'uniek' of 'kenmerk' bewijst niets en het ontbreken ervan is geen gebrek; een genoemd contrast moet inhoudelijk kloppen. Overlap van gevallen tussen rollen of fasen, of een onderscheid dat op een onderbouwd doelkenmerk berust, is geen gebrek zolang het kenmerk kenbaar is (ESS-01 beoordeelt het kenmerk zelf). Ontbreekt de toespitsing geheel, zodat de kern geen enkel verwant begrip kan uitsluiten, meld dat dan als eigen ESS-05-reden (STR-04 beoordeelt de vorm apart). Een automatisch signaal, categorielabel, record-ID of vaststelling is geen ESS-05-goedkeuring.

### Verwante begrippen: herkomst en bevestiging

Elk verwant begrip draagt een herkomst en een bevestigingsstatus.

| Herkomst | Standaard bevestigd? |
|---|---|
| gebruiker | ja |
| bron | nee |
| repository (actieve definities met dezelfde context) | nee |
| model (voorstel van de AI-beoordeling) | nee |
| ontologie (gereserveerd; aanvoer volgt onder DEF-300) | nee |

- Geeft het model bij een voorstel een bronverwijzing met een letterlijk citaat, dan blijft het voorstel `model` en onbevestigd. Het citaat is aparte provenance.
- Een deskundige bevestigt een verwant begrip of wijst het gemotiveerd af (actor, tijd, grond). Een afgewezen begrip gaat niet meer mee en keert niet terug als voorstel.
- De gebruikte burenlijst wordt met de beoordeling opgeslagen.
- Een oordeel geldt alleen voor exact die kern, term, context, betekenis, bronnen en burenlijst. Na een wijziging is het niet meer actueel.

### Uitkomsten

- **Voldoet:** ten minste één bevestigd verwant begrip, en elk ervan is onderscheiden, met het citaat van het dragende kenmerk.
- **Voldoet niet:** een bevestigd verwant begrip wordt niet onderscheiden, met het ontbrekende of te ruime kenmerk. Of de toespitsing ontbreekt: "ESS-05 — Voldoet niet: de definitie kan zonder toespitsing geen enkel verwant begrip uitsluiten", naast een eventuele STR-04-bevinding.
- **Nog te beoordelen, met precies één vraag:**
  - er is geen bevestigd verwant begrip;
  - er is een onbevestigd verwant begrip of modelvoorstel;
  - een relatie is onbeslist;
  - een bevestigd verwant begrip heeft geen beschrijving.
- **Voldoet — leeg bevestigd:** een deskundige legde gemotiveerd vast dat er in deze context geen verwante begrippen zijn. Dit is gebonden aan term, tekst, context, betekenis, bronnen en de lege burenlijst, en vervalt bij elke wijziging daarvan. Er is geen goedkeuring door tijdsverloop.
- **Niet uitgevoerd:** term, definitietekst of context ontbreekt, bijvoorbeeld "ESS-05 niet beoordeeld: zonder context is niet te bepalen welke verwante begrippen de definitie moet uitsluiten." Dit is geen inhoudelijk oordeel.
- **Technische fout:** de dienst, het transport, het antwoord of de burenlijst faalt. Dit is geen inhoudelijk oordeel, levert nooit 'voldoet' op en wordt niet gecachet.

Geen ESS-05-cijfer en geen 0/1. Prioriteit *midden* ordent de aandacht. Een negatieve of open uitkomst blijft zichtbaar en exporteerbaar, maar blokkeert vaststellen of export niet zelfstandig.

## H — terugkoppeling en begrensd herstel

> Onderscheid inhoudelijk tekort, instructieconflict, transportverlies, evaluatorfout, ontbrekend bewijs, storing en schadelijke nabewerking. Meld oorzaak, buur, kenmerk en bron. Start geen herstel. Alleen een afzonderlijk verzoek binnen DEF-638 mag één brongebonden voorstel opleveren; behoud origineel en verschil, verander geen identiteit/context, toets alle geraakte regels opnieuw en stop bij betekenisverlies, bronconflict of ontbrekende buurgrond.

Een voorstel onder DEF-638 volgt deze grenzen:
- het voegt alleen het kenmerk uit de bron toe dat het genoemde verwante begrip onderscheidt;
- geen trefwoord, geen contrastzin als enige wijziging, geen vernauwing buiten de bron, geen tweede definitie in de kern en geen wijziging van term, naam of context;
- ESS-05 en STR-02/STR-04, ESS-01, SAM-03, INT-06 en CON-02 worden opnieuw getoetst.

Uitsluitend toetsen verandert geen tekst. Automatisch herstel is niet actief.

Voorbeeld van terugkoppeling: "Taakstraf voldoet ook aan 'sanctie die door de rechter wordt opgelegd'. Voeg het kenmerk toe dat geldboete van taakstraf onderscheidt volgens de bron (bijvoorbeeld de betaling van een geldbedrag); schrijf niet 'in tegenstelling tot een taakstraf' zonder dat kenmerk."

## Afbakening

- **ESS-03** beslist instantie-identiteit; **ESS-05** beslist begripsonderscheid.
- **STR-04** toetst de vorm van de toespitsing. ESS-05 meldt zijn eigen inhoudelijke reden, zonder onderdrukking over en weer (K-8).
- **ESS-01** beslist of een doelkenmerk begripsbepalend is.
- **CON-01** bewaakt context en noodzakelijke namen; **CON-02** de bronsteun.
- **SAM-03/INT-06** bewaken geneste definities en toelichting; **INT-09** de limitatieve opsomming.
- **CON-CIRC-001** beoordeelt letterlijke termherhaling; **ESS-CONT-001/VAL-LEN-001** een te korte kern.
- De gedeelde vaststel- en exportpoort valt onder DEF-624/DEF-630, herstel onder DEF-638, en de ontologieleverancier onder DEF-300.

Bronregel: ASTRA-pagina 'Voldoende onderscheidend', revisie 8561 (11 februari 2025 07:47:05 UTC). 'Politie' is de door ASTRA genoemde herkomst en is niet zelfstandig gelezen. De afbakening van de vergelijkingsruimte, de overlapregel, de informatievoorwaarden en de lege-ruimte-uitkomst zijn lokale uitwerking (K-1…K-10); die worden onder DEF-625 geregistreerd.
````

### 3.2 `definitie-nederlandse-definities`

**(a) `reference.md:81`**, bestaand:

```
1. De differentia moet het begrip **onderscheiden** van zijn zusterbegrippen (ESS-05)
```

Vervangen door:

```
1. De differentia moet het begrip **onderscheiden** van zijn verwante begrippen: zusterbegrippen onder hetzelfde genus én begrippen die in dezelfde context met het begrip verward kunnen worden of deels dezelfde gevallen dekken (ESS-05). Zelftest per verwant begrip: welk kenmerk in de kern drukt het verschil uit ten opzichte van de beschrijving van dat begrip? Overlap van gevallen is geen gebrek — dezelfde persoon kan lener én werknemer zijn zolang 'actuele lening' en 'arbeidsovereenkomst' de rollen onderscheiden. Een vergelijkingszin of het woord 'uniek' is geen kenmerk. Zie [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md).
```

**(b) `reference.md:136`**, bestaand:

```
| **Onderscheidingsfalen** | Onderscheidt niet van zusterbegrippen | ❌ "Geldboete: sanctie opgelegd door de rechter" (geldt ook voor taakstraf) |
```

Vervangen door:

```
| **Onderscheidingsfalen** | Onderscheidt niet van verwante begrippen in dezelfde context; herstel met een kenmerk uit de bron, niet met 'in tegenstelling tot …' (ESS-05) | ❌ "Geldboete: sanctie opgelegd door de rechter" (geldt ook voor taakstraf) |
```

**(c) `reference.md:211`**, bestaand:

```
| Onderscheidend | Onderscheid van zusterbegrippen | ESS-05 |
```

Vervangen door:

```
| Onderscheidend | Kern drukt per verwant begrip in deze context een onderbouwd verschil in kenmerken uit; overlap van gevallen is geen gebrek | ESS-05 |
```

**(d) `reference.md:281`**, bestaand:

```
4. ☐ Differentia onderscheidt van zusterbegrippen
```

Vervangen door:

```
4. ☐ Differentia onderscheidt in kenmerken van elk verwant begrip in deze context (overlap van gevallen toegestaan); inhoudelijk oordeel doet de app per verwant begrip (ESS-05)
```

**(e) `SKILL.md` na regel 63** (na het ESS-04-blok), toevoegen:

```
## ESS-05 — voldoende onderscheidend

Lees bij formuleren het [gedeelde ESS-05-contract](references/ess05-onderscheid.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Kies bovenbegrip en toespitsende kenmerken zodat de kern per verwant begrip in de vastgelegde context een onderbouwd verschil in kenmerken uitdrukt; overlap van gevallen (één persoon in twee rollen) is geen gebrek zolang het onderscheidende kenmerk kenbaar is. Ontleen kenmerken aan bron en bedoelde betekenis; verzin geen verwant begrip, kenmerk of bron en vernauw niet verder dan de bron draagt. Een vergelijkingszin is een vormoptie; ‘uniek’, ‘specifiek’ en ‘kenmerk’ zijn geen kenmerk; een contrast dat de definitie van het andere begrip nodig heeft hoort in de toelichting. Zonder context wordt niet gegenereerd; zonder bekende verwante begrippen mag één brongebonden kandidaat ontstaan en blijft ESS-05 open. De inhoudelijke beoordeling doet de Definitie-app zelf (AI-beoordeling per verwant begrip, geen cijfer, geen zelfstandige vaststelblokkade, geen automatische herschrijving); dit blok is geen opgeslagen beoordeling.
```

**(f) `SKILL.md:79`**, bestaand:

```
| **definitie-voorbeelden-generatie** | Illustratie — voorbeelden en tegenvoorbeelden bij definities |
```

Geen wijziging nodig. Deze regel is gecontroleerd en noemt geen ESS-05-norm.

**(g) `SKILL.md:87`**. Zet vóór `*Versie: 0.7 — DEF-767 …`:

```
*Versie: 0.8 — DEF-768 (ESS-05 voldoende onderscheidend; verwijzing naar gedeeld ESS-05-contract); 0.7 — DEF-767 …
```

**(h) Nieuw bestand `references/ess05-onderscheid.md`**: een byte-identieke kopie van §3.1 (i).

### 3.3 `definitie-ontologisch-modelleren`

**(a) `reference.md:204`**. Dit is regel 200 in B §6.8; bij HEAD verschoven naar 204. Bestaand:

```
2. **Differentia uit zusterbegrippen**: de differentia moet het begrip onderscheiden van zijn zusterbegrippen (toetsregel ESS-05)
```

Vervangen door:

```
2. **Differentia uit verwante begrippen**: neem uit het model de zusterbegrippen (zelfde direct genus) én begrippen met overlappende betekenis in dezelfde context; de differentia moet elk daarvan in kenmerken onderscheiden (toetsregel ESS-05). Overlappende klassen of rollen die één individu tegelijk kan vervullen zijn toegestaan zolang het onderscheidende kenmerk kenbaar is. Lever deze verwante begrippen mét hun definitie en herkomst aan bij generatie en toetsing; zonder context of zonder bevestigd verwant begrip blijft de ESS-05-beoordeling respectievelijk niet uitgevoerd of open. Zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

**(b) `reference.md:272`**. Dit is regel 268 in B §6.8. Bestaand:

```
- **Differentia-suggestie**: zusterbegrippen in het model helpen bij het formuleren van onderscheidende kenmerken (ESS-05)
```

Vervangen door:

```
- **Vergelijkingsruimte voor ESS-05**: het model levert verwante begrippen (is-een-zusters en overlappende klassen) waartegen de definitie wordt getoetst, met herkomst `ontologie` en onbevestigd tot een deskundige ze bevestigt; het model bewijst het onderscheid niet zelf. De aanvoer uit een ontologiemodel volgt onder DEF-300; tot dan levert de app repository-, bron-, gebruikers- en modelburen.
```

### 3.4 `definitie-voorbeelden-generatie`

**(a) `reference.md:165`**. Dit is regel 163 in B §6.8. Bestaand:

```
| **ESS-05** (Onderscheid van verwante) | Tegenvoorbeelden verduidelijken de grenzen met zusterbegrippen |
```

Vervangen door:

```
| **ESS-05** (Voldoende onderscheidend) | Eén tegenvoorbeeld per verwant begrip: een geval van dat begrip dat op een benoemd kenmerk van de definitie faalt, zodat zichtbaar is welk kenmerk het verschil draagt. Een geval dat beide begrippen tegelijk dekt (één persoon als lener én werknemer) is geen tegenvoorbeeld en geen gebrek zolang de kenmerken verschillen; valt de beschrijving van een verwant begrip samen met de kern, dan is dat een ESS-05-bevinding (te breed) |
```

**(b) `reference.md` na regel 184** (Stap 2, na "…verscherp de differentia"), toevoegen:

```
- Voor ESS-05 is dit een hulp bij de toetsing per verwant begrip: leg per verwant begrip vooraf vast of het bedoeld is onderscheiden te zijn en door welk kenmerk. Een geval dat onder twee onderscheidbare rollen valt, bewijst geen te brede definitie. Een label dat uit dezelfde definitie is gegenereerd, is geen onafhankelijk bewijs.
```

**(c) `reference.md:101`**, bestaand:

```
- Kies naburige begrippen (zusterbegrippen in het ontologisch model)
```

Vervangen door:

```
- Kies naburige begrippen: zusterbegrippen in het ontologisch model én begrippen die in dezelfde context verwarbaar zijn (ESS-05)
```

**(d) `SKILL.md:55`**, bestaand:

```
| **definitie-toetsregels** | Validatie — ESS-03, ESS-05, STR-02 ondersteunen met voorbeelden |
```

Blijft ongewijzigd; B §6.8 zegt "`SKILL.md:55` blijft", en dat is gecontroleerd. Verhoog het versienummer van de skill bij publicatie volgens de bestaande conventie.

### 3.5 `definitie-ufo-ontologie`

**`reference.md` na regel 138** (na de mappingtabel, vóór `### Kanttekening bij RESULTAAT`). B §6.8 noemde regel 133–136; bij HEAD loopt de tabel over regel 133–138. Toevoegen:

```
**ESS-05-toepassing.** Verwante begrippen zijn de andere subtypes onder hetzelfde bovenbegrip (subkind/role/phase onder dezelfde kind) en begrippen van een ander type die in dezelfde context met het begrip verward kunnen worden. Een categorie- of stereotypelabel onderscheidt geen begrippen; alleen begripsbepalende kenmerken doen dat. Rollen die één individu tegelijk kan vervullen (verdachte én getuige, lener én werknemer) zijn onderscheidbare begrippen met overlappende extensie: overlap is voor ESS-05 geen gebrek zolang het onderscheidende kenmerk kenbaar is. De inhoudelijke ESS-05-beoordeling doet de app per verwant begrip; zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

### 3.6 `definitie-juridisch-nederland`

**`reference.md` direct na regel 138** (`- ❌ \`boete\` → ✅ \`bestuurlijke boete\` (onderscheid met strafrechtelijke boete)`), toevoegen:

```
- Voor ESS-05 zijn de verwante begrippen contextgebonden: dezelfde term in straf- en bestuursrecht zijn twee begrippen die binnen de vastgelegde context (CON-01) van elkaar en van hun zusterbegrippen (dwangsom, last onder bestuursdwang) moeten worden onderscheiden; onderscheid in één rechtsgebied is geen universeel onderscheid. Zonder vastgelegde context wordt ESS-05 niet uitgevoerd. Zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

## 4. Publicatie op de centrale setup-repo (later, gescheiden en af te stemmen)

Dit voorstel verandert niets aan `~/Projecten/_claude-global-setup` of `~/.claude/skills`. Publicatie vraagt een eigen opdracht met de volgende grenzen:

1. **Deployment-freeze ALG-391 is actief.** De marker `~/.claude/.global-setup-deployment-freeze-ALG-391` bestaat; gecontroleerd op 23 september 2026. Tijdens de freeze is alleen repo → live geldig, via ALG-391 Task 10 (`rules/global-setup-sync.md`). Wijzig dus niets live in `~/.claude/skills/`, en draai geen `sync-rules.sh --sync`: die weigert terecht met exit 2 en zou gemergd werk terugdraaien.
2. **Eigen branch en issue in de setup-repo.** Gebruik een aparte branch met een ALG-issue, want dit is de centrale setup en niet `DEF`. Dat issue verwijst naar DEF-768 en naar dit document (pad plus commit van deze branch na merge). De repo staat nu op `main` (HEAD `dc7dc644`): eerst een branch maken, niet op `main` werken.
3. **Eerst de canonieke bron, dan de kopie.** Maak `definitie-toetsregels/references/ess05-onderscheid.md` eerst. Kopieer daarna byte-identiek naar `definitie-nederlandse-definities/references/`. Controleer de gelijkheid met sha256.
4. **Regelnummers opnieuw vaststellen.** Controleer bij uitvoering elke vindplaats tegen de dan actuele HEAD. Als een bestand sinds `dc7dc644` is gewijzigd, zoek het bestaande fragment letterlijk op; bij afwijking eerst terugkoppelen.
5. **Setup-tellingen (ALG-423).** Er komen twee referentiebestanden bij, maar geen nieuwe skill, rule, hook, agent, command of template. Controleer of `setup-counts.json` references meetelt. Doet het dat, dan noemt de PR per categorie de telling voor → na, met de twee bestanden en de reden.
6. **Review.** Na de PR draait `/review-pr` in de setup-repo. Dit is een tekstwijziging aan skills, dus geen programmeerwerk volgens de CLI-rolverdeling. Een onafhankelijke review van de consistentie met §1.3 blijft wel nodig.
7. **Pas na merge van DEF-768.** De skillteksten beschrijven de app-uitkomsten van DEF-768. Publiceer ze pas als de DEF-768-code in de Definitie-app op `main` staat, anders beschrijven de skills gedrag dat de app nog niet heeft. Werk dan ook de ESS-05-vermelding in `ess04-toetsbaarheid.md` bij als dat nodig is: die noemt ESS-05 alleen als afbakening en blijft juist.
8. **Buiten de scope van ESS-05.** De prioriteitsverdeling in `definitie-toetsregels/reference.md:135–139` (28 hoog / 22 midden) klopt niet met de regeltabellen zelf. Een telling op HEAD vond 25 regels `**hoog**` en 25 `midden` zonder vet, plus ESS-04 als vetgedrukte `**midden**`. Dat is een bestaande afwijking. Registreer het apart en werk het niet stil mee bij met ESS-05.

## 5. Controle van dit voorstel

- **Inhoud.** Elke vervanging is gecontroleerd op de tien punten van §1.3, voor zover relevant in dat bestand. Er staat geen extensietoets ("geen geval … mag aan alle kenmerken voldoen"), geen prioriteit `hoog` en geen O2- of "later goedgekeurde AI"-formulering in de voorgestelde teksten.
- **Bestaande fragmenten.** Alle geciteerde fragmenten zijn letterlijk overgenomen uit de beheerde bron bij HEAD `dc7dc644`, met Read op de genoemde regels. De verschuivingen ten opzichte van B §6.8 (ontologisch-modelleren 200→204 en 268→272, voorbeelden-generatie 163→165, UFO-tabel 133–136→133–138) zijn vermeld.
- **Linkpaden.** De bronnen staan als absolute paden naar de hoofdcheckout, omdat de analysemappen niet in deze worktree staan. De links in de voorgestelde skillteksten zijn relatief binnen de skill (`references/ess05-onderscheid.md`) of noemen de skillnaam met pad, net als de bestaande ESS-03/ESS-04-verwijzingen.
- **Geen codewijziging.** Het enige nieuwe bestand is dit Markdown-document. Code, tests en uitvoercontracten zijn niet gewijzigd; daarom is er geen programmeertestronde gedraaid.
