# DEF-768 — ESS-05: voorstel zes skillvervangingen (WP8-voorbereiding, v2)

24 september 2026 · uitvoerder Claude Code CLI (sessie `6d273f41-0afb-480a-9034-1c87b1ecba58`) · branch `feature/DEF-768-ess05-ai-beoordeling`, basis `26f2374d3`.

**Status: voorstel, niet toegepast.** Vervangt v1 (`2026-09-23-DEF-768-ess05-skillvervangingen-voorstel-v1.md`, bevroren en ongewijzigd) na de gerichte review van 24 september (Cowork `review-v1.md`, Codex-punten 1, 3, 4 en 5). De centrale gedeelde skillbestanden zijn niet gewijzigd. Er zijn geen modelcalls gedaan en er wordt geen kwaliteitswinst geclaimd: een skillwijziging bewijst geen betere generatie of menselijke beoordeling.

## 0. Wat verandert ten opzichte van v1

| # | Wijziging | Grond | Plaats |
|---|---|---|---|
| 1 | 'Uniek', 'specifiek', 'bijzonder' zijn **op zichzelf** geen kenmerk en vervangen geen concreet kenmerk; als deel van een door de bron gedragen naam, vaste term of noodzakelijke inhoud blijven ze staan. Geen trefwoordverbod in G of T. | Codex-punt 3 | §1.3 punt 10; §3.1 (a)(c)(e)(i); §3.2 (a)(e) |
| 2 | Eén beslisvolgorde, gelijk aan de app: fail vóór open; onbevestigde bron-/model-/ontologieburen en modelvoorstellen houden open; een onbevestigde repositorybuur alleen als hij niet onderscheiden is. Dit is een **bestaande implementatiekeuze**, geen nieuw gebruikersbesluit. | Codex-punt 1, RE5-03/RE5-06 | §1.3 punt 7; §3.1 (i) Uitkomsten |
| 3 | Juridische skill: homoniemen buiten de vastgelegde context zijn geen verplichte vergelijkingsbegrippen; de onbewezen zusterindeling (dwangsom, last onder bestuursdwang) vervalt. | Codex-punt 4 | §3.6 |
| 4 | Voorbeeldenskill: één tegenvoorbeeld is illustratieve hulp waar het te onderbouwen is, geen extra slaageis; synthetische voorbeelden herkenbaar; geen onafhankelijk bewijs. | Codex-punt 5 | §3.1 (g); §3.4 (a)(b) |
| 5 | Afgrenzing: een ander woord of kenmerk alleen is nog geen afgrenzing; het kenmerk grenst gevallen van het verwante begrip af die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen mogen; onvoldoende grond blijft onduidelijk. Binnen K-3b/K-5, zonder nieuw schema of verplichte invoer. | RE5-01 | §1.3 punt 2; §3.1 (a)(c)(i); G/T |
| 6 | Een citaat dat ook in de buurdefinitie staat, is een signaal en geen automatisch 'onderscheidt niets'. | review correctie 5 | §3.1 (i) Voorbeelden en T |
| 7 | G- en T-citaten gelijk aan de gecorrigeerde app (`ess05-assess/2`). | — | §3.1 (i) |

## 1. Herkomst en voorrang

### 1.1 Bronnen (alleen gelezen, onveranderd)

Als in v1 §1.1 (zes bronnen, hashes in `logs/def768/wp8-bronhashes.log`), plus de gerichte review [review-v1.md](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260923/onderzoek-cowork-20260924/review-v1.md). Uitspraken uit die review over code zijn geverifieerd tegen de worktree, niet overgenomen als besluit.

De normtekst in dit voorstel volgt de gecorrigeerde app-implementatie in deze worktree:
- regelrecord `src/toetsregels/regels/ESS-05.json`;
- G-tekst `src/services/prompts/modules/json_based_rules_module.py`, sleutel `"ESS-05"`;
- T-instructie `_TOETSINSTRUCTIE` in `src/services/validation/ess05_assessment_service.py`;
- uitkomstteksten `src/domain/ess05/contract.py`;
- [uitvoercontract v2](2026-09-24-DEF-768-ess05-contract-en-runplan-v2.md).

### 1.2 Voorrang

Ongewijzigd t.o.v. v1 §1.2, met twee aanvullingen:

| Historische tekst | Waarom vervallen | Vervangen door |
|---|---|---|
| "één tegenvoorbeeld per verwant begrip" als imperatief (v1 §1.2, §3.1 (g), §3.4 (a)) | kan als extra slaageis worden gelezen of verzonnen voorbeelden uitlokken (Codex-punt 5) | een tegenvoorbeeld kan helpen waar het te onderbouwen is; geen slaageis, geen bewijs |
| "zusterbegrippen (dwangsom, last onder bestuursdwang)" en "dezelfde term in straf- en bestuursrecht … moeten worden onderscheiden" (v1 §3.6) | rechtsinhoudelijke indeling zonder bron; strijdig met K-3b (homoniemen in een andere context zijn geen verwant begrip) | contextgebonden formulering zonder nieuwe juridische inhoud |

### 1.3 Normkern: moet in alle zes skills gelijk zijn

1. **Direct O3.** De app beoordeelt ESS-05 zelf met een AI-beoordeling per verwant begrip, op alleen het aangeleverde materiaal (K-1).
2. **Kenmerkvraag met afgrenzing, overlap toegestaan (K-3b).** Per verwant begrip moet de kern een onderbouwd kenmerk hebben dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen. Gedeelde gevallen mogen: een persoon of object dat beide rollen vervult, bewijst op zichzelf geen gebrek (E05 lener/werknemer voldoet; E06 "geregistreerd persoon" tweemaal voldoet niet). Een ander woord of kenmerk alleen is nog geen afgrenzing (ASTRA-FOUT: 'jeugdige' draagt ook ontvluchting). Onvoldoende grond blijft onduidelijk; niets verzinnen.
3. **Prioriteit `midden`** (ASTRA; K-4).
4. **Geen cijfer en geen zelfstandige blokkade** (K-4).
5. **Contextplicht.** Zonder context: "niet uitgevoerd" met reden (K-9).
6. **Burenprovenance** (K-1, K-6), als v1.
7. **Beslisvolgorde.** Voldoet niet gaat vóór nog te beoordelen. Open met precies één vraag: geen bevestigd verwant begrip; een bevestigd begrip is onduidelijk; een onbevestigd begrip uit bron, model of ontologie, of een modelvoorstel; een onbevestigd repositorybegrip dat niet onderscheiden of onduidelijk is. Een onbevestigd repositorybegrip dat wél onderscheiden is, blokkeert 'voldoet' niet zolang minstens één bevestigd begrip onderscheiden is (bestaande implementatiekeuze binnen K-1/K-2). Leeg bevestigd: zie K-2.
8. **Eigen reden naast STR-04** (K-8); ESS-05 en STR-04 blijven onafhankelijke beoordelingen.
9. **Geen automatisch herstel** (K-7).
10. **Vorm.** Een vergelijkingszin is een vormoptie en geen bewijs. 'Uniek', 'specifiek', 'bijzonder' en 'kenmerk' zijn op zichzelf geen kenmerk en vervangen geen concreet kenmerk; als deel van een door de bron gedragen naam, vaste term of noodzakelijke inhoud blijven ze staan (CON-01). Een contrast dat de definitie van het andere begrip nodig heeft, hoort in de toelichting (K-3a).

## 2. Doelbestanden en hun vastgelegde stand

Ongewijzigd t.o.v. v1 §2 (beheerde bron `~/Projecten/_claude-global-setup/skills/`, HEAD `dc7dc644438a05d602f05bc115ae16ac85b83169`; regelnummers bij die HEAD; zes skills, negen bestaande bestanden plus twee nieuwe referentiebestanden).

## 3. De zes vervangingen

Alleen de voorgestelde teksten zijn gewijzigd; de bestaande fragmenten en vindplaatsen zijn die van v1.

### 3.1 `definitie-toetsregels`

**(a) `reference.md:48`**, bestaand:

```
| ESS-05 | Onderscheid van verwante begrippen | **hoog** | Maak expliciet duidelijk waarin het begrip zich onderscheidt van andere verwante begrippen |
```

Vervangen door:

```
| ESS-05 | Voldoende onderscheidend (van verwante begrippen) | **midden** ⁵ | Kies bovenbegrip en toespitsende kenmerken zodat de kern per verwant begrip in deze context een onderbouwd kenmerk heeft dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen (één persoon in twee rollen) mogen; een ander woord alleen is geen afgrenzing; een vergelijkingszin is niet vereist en ‘uniek’/‘specifiek’/‘kenmerk’ vervangen geen concreet kenmerk (als deel van een naam of vaste term blijven ze staan) — volledige N/G/T/H-instructie in [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md) |
```

**(b) `reference.md` na regel 52** — ongewijzigd t.o.v. v1 §3.1 (b).

**(c) `reference.md` na regel 54** (na het ESS-03-blok), toevoegen:

```
> **ESS-05 — voldoende onderscheidend.** Met de definitie is het begrip te onderscheiden van de andere begrippen die in dezelfde context relevant zijn: de kern heeft ten opzichte van elk verwant begrip een onderbouwd kenmerk dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen. Gedeelde gevallen mogen: dezelfde persoon kan lener en werknemer zijn. Een ander woord of kenmerk alleen is nog geen afgrenzing; is de grond onvoldoende, dan blijft het oordeel open. Verwante begrippen zijn zusterbegrippen onder hetzelfde bovenbegrip, begrippen die in deze context verward kunnen worden of deels dezelfde gevallen dekken, en door bron of gebruiker aangewezen begrippen; niet het bovenbegrip, onderbegrippen, synoniemen of homoniemen in een andere context. De app beoordeelt dit zelf met een AI-beoordeling per verwant begrip, op alleen het aangeleverde materiaal; elk verwant begrip draagt herkomst (gebruiker / bron / repository / model / ontologie) en bevestigingsstatus, en door het model voorgestelde begrippen blijven onbevestigd tot een deskundige ze bevestigt of afwijst. Zonder context wordt ESS-05 niet uitgevoerd; zonder bevestigd verwant begrip blijft het oordeel open met precies één vraag, tenzij een deskundige gemotiveerd bevestigt dat de vergelijkingsruimte in deze context leeg is. Ontbreekt de toespitsing, dan meldt ESS-05 dat zelf, naast STR-04. Prioriteit *midden*; geen cijfer, geen zelfstandige blokkade van vaststellen of export, geen automatische herschrijving. Contract: [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md). Besloten 21 september 2026 (DEF-768, K-1…K-10), aangevuld 23 en 24 september 2026 (synthese v3; gerichte review).
```

**(d) `SKILL.md:39`** — ongewijzigd t.o.v. v1 §3.1 (d).

**(e) `SKILL.md` na regel 74** (na het ESS-04-blok), toevoegen:

```
## ESS-05 — voldoende onderscheidend

Lees bij genereren of toetsen het [gedeelde ESS-05-contract](references/ess05-onderscheid.md). De kern moet per verwant begrip in de vastgelegde context een onderbouwd kenmerk hebben dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen (één persoon of object in twee rollen) mogen, en een ander woord alleen is nog geen afgrenzing. Een vergelijkingszin is een vormoptie, geen bewijs; ‘uniek’, ‘specifiek’ en ‘kenmerk’ vervangen geen concreet kenmerk, maar blijven staan als deel van een door de bron gedragen naam of vaste term. De app beoordeelt ESS-05 zelf met een AI-beoordeling per verwant begrip (herkomst en bevestigingsstatus per begrip; modelvoorstellen blijven onbevestigd). Zonder context: niet uitgevoerd. Zonder bevestigd verwant begrip: nog te beoordelen met precies één vraag, of 'voldoet — leeg bevestigd' na gemotiveerde deskundige bevestiging. Ontbrekende toespitsing: eigen ESS-05-reden naast STR-04. Prioriteit *midden*; geen ESS-05-cijfer, geen zelfstandige vaststel-/exportblokkade, geen automatische herschrijving. Skilladvies is geen opgeslagen beoordeling of expertbesluit.
```

**(f) `SKILL.md:78`** — ongewijzigd t.o.v. v1 §3.1 (f).

**(g) `SKILL.md:108`**, bestaand:

```
| **definitie-voorbeelden-generatie** | Illustratie — ESS-05 onderscheid aantonen via voorbeelden |
```

Vervangen door:

```
| **definitie-voorbeelden-generatie** | Illustratie — ESS-05: waar onderbouwd, een tegenvoorbeeld dat zichtbaar maakt welk kenmerk een verwant begrip afgrenst; hulp, geen slaageis en geen bewijs; gedeelde gevallen zijn geen tegenvoorbeeld |
```

**(h) `SKILL.md:113`** — ongewijzigd t.o.v. v1 §3.1 (h), met als versieregel:

```
*Versie: 0.9 — DEF-768 (ESS-05 voldoende onderscheidend: AI-beoordeling per verwant begrip, kenmerkvraag met afgrenzing en toegestane overlap, prioriteit midden, geen cijfer, geen poort); 0.8 — DEF-767 …
```

**(i) Nieuw bestand `references/ess05-onderscheid.md`**, volledige tekst:

````markdown
# ESS-05 — voldoende onderscheidend

Vastgesteld door Chris op 21 september 2026 (DEF-768, besluiten K-1…K-10), aangevuld op 23 september 2026 (synthese v3, overlap volgens K-3b) en 24 september 2026 (gerichte review: afgrenzing binnen K-3b/K-5, trefwoorden, beslisvolgorde). Canonieke bron: `definitie-toetsregels/references/ess05-onderscheid.md`; `definitie-nederlandse-definities` draagt een byte-identieke, versiegebonden kopie in zijn eigen `references/` zodat dat pakket zelfstandig leesbaar is — wijzig alleen de canonieke bron en kopieer die opnieuw. De app voert ESS-05 zelf uit als AI-beoordeling per verwant begrip. Bestaande CON-01/02- en ESS-01/02/03/04-afspraken blijven gelden. Dit advies is geen opgeslagen beoordeling, expertbesluit of vaststelling.

## N — norm en toetsvraag

**Naam:** Voldoende onderscheidend. **Prioriteit:** midden. **Aanbeveling:** verplicht.

> Met de definitie is het begrip te onderscheiden van de andere begrippen die in dezelfde context relevant zijn: de kern drukt ten opzichte van elk verwant begrip een onderbouwd verschil in kenmerken uit dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen mogen. Het onderscheid ligt in de gekozen kenmerken (bovenbegrip en toespitsing), niet in een vergelijkingsfrase; de woorden 'uniek', 'specifiek' of 'kenmerk' zijn op zichzelf geen kenmerk, maar blijven staan als deel van een door de bron gedragen naam of vaste term.

**Verwante begrippen.** Zusterbegrippen onder hetzelfde bovenbegrip, begrippen die in deze context met het begrip verward kunnen worden of deels dezelfde gevallen dekken, en door bron of gebruiker aangewezen begrippen. Geen verwante begrippen zijn: het bovenbegrip, onderbegrippen, synoniemen en homoniemen in een andere context.

**Afgrenzing en overlap.** Een ander woord of een ander kenmerk alleen is nog geen afgrenzing: het kenmerk moet gevallen van het verwante begrip afgrenzen die volgens bron of bedoelde betekenis niet onder dit begrip vallen. Gedeelde gevallen mogen: een persoon of object dat beide rollen vervult, bewijst op zichzelf geen gebrek. Dat geldt ook voor een onderscheid dat berust op een onderbouwd doelkenmerk (ESS-01 beoordeelt het kenmerk zelf). Draagt het materiaal de afgrenzing niet, dan blijft het oordeel open; er worden geen tegenvoorbeeld of betekenis verzonnen.

**Vorm.** Een vergelijkende formulering is toegestaan als schrijfhulp, maar bewijst niets en vervangt geen kenmerk. Een contrast dat de definitie van het andere begrip nodig heeft, hoort in de toelichting.

**Toetsvraag:** Drukt de definitiekern in deze context ten opzichte van elk relevant verwant begrip een onderbouwd verschil in kenmerken uit dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen (gedeelde gevallen mogen), en is per verwant begrip aan te wijzen welk kenmerk in de kern dat verschil draagt?

### Voorbeelden

- Goed (ASTRA): `Incident waarbij een jeugdige zonder toestemming één van de volgende justitiële voorzieningen verlaat: de open justitiële jeugdinrichting of het terrein dat tot de gesloten justitiële jeugdinrichting behoort.` — de opsomming van voorzieningen is het kenmerk dat volgens ASTRA's voorbeeld het onderscheid met ontvluchting draagt.
- Fout (ASTRA): `Incident waarbij een jeugdige zonder toestemming de justitiële jeugdinrichting verlaat.` — ASTRA: "kan niet worden onderscheiden van ontvluchting". 'Jeugdige' en 'zonder toestemming verlaten' gelden ook voor ontvluchting en grenzen dus niets af.
- Synthetisch voorbeeld, voldoet (E05): lener = `persoon met een actuele lening bij de instelling`, verwant begrip werknemer = `persoon met een arbeidsovereenkomst met de instelling`. Eén persoon kan beide zijn; de rolkenmerken grenzen de rollen af.
- Synthetisch voorbeeld, voldoet niet (E06): twee begrippen die beide `persoon die in het systeem is geregistreerd` luiden. De beschrijvingen zijn gelijk; geen kenmerk grenst af.

De synthetische voorbeelden zijn bedacht ter illustratie en zijn geen bron of onafhankelijk bewijs.

## G — bij formuleren

> Kies een bovenbegrip en toespitsende kenmerken die het begrip binnen de gegeven context onderscheiden van de aangeleverde verwante begrippen: de kern drukt per verwant begrip een onderbouwd verschil in kenmerken uit ten opzichte van de beschrijving van dat begrip. Een ander woord of een ander kenmerk alleen is nog geen afgrenzing: het kenmerk moet gevallen van het verwante begrip afgrenzen die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen mogen. Overlap van gevallen is geen gebrek: een persoon of object dat beide rollen vervult, maakt de definitie niet onvoldoende onderscheidend, zolang het onderscheidende kenmerk kenbaar is. Ontleen de kenmerken aan de aangeleverde bronnen en de bedoelde betekenis; verzin geen verwant begrip, kenmerk of bron, verzin geen tegenvoorbeeld of betekenis om een afgrenzing te maken, en vernauw de betekenis niet verder dan de bron draagt om een verschil te maken. Een onderscheidend kenmerk mag geen niet-begripsbepalend doel of gebruik zijn (ESS-01). Een korte vergelijkende formulering zonder de definitie van het andere begrip is toegestaan wanneer de kern anders onduidelijk blijft; een contrast dat de definitie van het andere begrip nodig heeft, hoort niet in de kern — de app kan het als toelichtingsvoorstel apart aanbieden. De woorden ‘uniek’, ‘specifiek’, ‘bijzonder’ en ‘onderscheidend kenmerk’ zijn op zichzelf geen kenmerk en vervangen geen concreet kenmerk; als deel van een door de bron gedragen naam, vaste term of noodzakelijke inhoud blijven ze staan. Zijn geen verwante begrippen aangeleverd, lever dan één kandidaat op grond van de bron; de vergelijking blijft bij de ESS-05-beoordeling open. Spreken bronnen of context elkaar tegen over de afgrenzing of over wat een verwant begrip is, maak dan geen stille keuze. Laat registratiecontext en bronadministratie buiten de kern, met behoud van inhoudelijk noodzakelijke namen (CON-01).

Aanvullend buiten de app-prompt:
- Zonder vastgelegde context wordt niet gegenereerd (K-9). Vraag om de context en verzin haar niet.
- Zelf bedachte verwante begrippen zijn onbevestigde voorstellen. Presenteer ze apart, niet als bronfeit.

## T — toetsinstructie (de app voert deze uit)

De tekst hieronder is de toetsinstructie van de app, met één aanpassing voor lezers. In de app staat aan het slot "meld dat dan als lacks_differentia"; hier staat "meld dat dan als eigen ESS-05-reden".

> Beoordeel de ongewijzigde definitiekern bij de vastgelegde term, bedoelde betekenis, context en kandidaatversie. Beoordeel per aangeleverd verwant begrip of de kern in deze context een onderbouwd verschil in kenmerken uitdrukt ten opzichte van de beschrijving van dat begrip. Zo nee, dan onderscheidt de definitie het begrip daar niet van: benoem het ontbrekende of te ruime kenmerk. Zo ja, citeer het kenmerk in de kern dat het verschil draagt. Een ander woord of een ander kenmerk alleen bewijst nog geen afgrenzing: beoordeel of de kern een onderbouwd kenmerk heeft dat gevallen van het verwante begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen mogen. Een kenmerk dat ook het verwante begrip draagt (zoals alleen 'jeugdige' bij onttrekking en ontvluchting) grenst niets af. Zijn de gronden daarvoor onvoldoende, dan is de uitkomst unclear; verzin geen tegenvoorbeeld of betekenis. Beoordeel of de begripsbeschrijvingen in de vastgelegde context een onderbouwd verschil in kenmerken uitdrukken. Een persoon of object dat beide rollen vervult bewijst op zichzelf geen gebrek. Benoem het verschil, het werkelijk ontbrekende kenmerk of de ontbrekende informatie. Een onbesliste buurrelatie blijft open met één vraag; toetsen wijzigt de kern niet. Een vergelijkingsfrase, het woord 'uniek', 'specifiek' of 'kenmerk' bewijst op zichzelf niets en het ontbreken ervan is geen gebrek; als deel van een door de bron gedragen naam of vaste term is zo'n woord evenmin een gebrek; een genoemd contrast moet inhoudelijk kloppen. Overlap van gevallen tussen rollen of fasen, of een onderscheid dat op een onderbouwd doelkenmerk berust, is geen gebrek zolang het kenmerk kenbaar is (ESS-01 beoordeelt het kenmerk zelf). Ontbreekt de toespitsing geheel, zodat de kern geen enkel verwant begrip kan uitsluiten, meld dat dan als eigen ESS-05-reden (STR-04 beoordeelt de vorm apart). Een automatisch signaal, categorielabel, record-ID of vaststelling is geen ESS-05-goedkeuring.

Wat de app in code bewaakt en wat niet: het geciteerde kenmerk moet letterlijk in de definitiekern staan, en twee volledig gelijke beschrijvingen kunnen niet als onderscheiden gelden. Staat het citaat ook in de beschrijving van het verwante begrip, dan toont de app dat als signaal; of het kenmerk daar werkelijk anders is (bijvoorbeeld door een ontkenning), is een inhoudelijk oordeel. Of een kenmerk werkelijk afgrenst, beoordeelt alleen de inhoudelijke beoordeling.

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

### Uitkomsten, in beslisvolgorde

1. **Niet uitgevoerd:** term, definitietekst of context ontbreekt, bijvoorbeeld "ESS-05 niet beoordeeld: zonder context is niet te bepalen welke verwante begrippen de definitie moet uitsluiten." Dit is geen inhoudelijk oordeel.
2. **Technische fout:** de dienst, het transport, het antwoord of de burenlijst faalt. Dit is geen inhoudelijk oordeel, levert nooit 'voldoet' op en wordt niet gecachet.
3. **Voldoet — leeg bevestigd:** een deskundige legde gemotiveerd vast dat er in deze context geen verwante begrippen zijn. Dit is gebonden aan term, tekst, context, betekenis, bronnen en de lege burenlijst, en vervalt bij elke wijziging daarvan. Er is geen goedkeuring door tijdsverloop.
4. **Voldoet niet:** de toespitsing ontbreekt ("ESS-05 — Voldoet niet: de definitie kan zonder toespitsing geen enkel verwant begrip uitsluiten", naast een eventuele STR-04-bevinding), of een bevestigd verwant begrip wordt niet onderscheiden, met het ontbrekende of te ruime kenmerk. Voldoet niet gaat vóór nog te beoordelen.
5. **Nog te beoordelen, met precies één vraag:**
   - een bevestigd verwant begrip is onduidelijk (onbeslist, of zonder beschrijving);
   - er is een onbevestigd verwant begrip uit bron, model of ontologie, of een modelvoorstel — ongeacht het oordeel erover;
   - er is een onbevestigd repositorybegrip dat niet onderscheiden of onduidelijk is;
   - er is geen bevestigd verwant begrip.
6. **Voldoet:** ten minste één bevestigd verwant begrip, en elk bevestigd begrip is onderscheiden, met het citaat van het dragende kenmerk. Een onbevestigd repositorybegrip dat onderscheiden is, blokkeert dit niet en blijft zichtbaar als "repository, onbevestigd".

Punt 5 en 6 volgen de bestaande keuze van de app binnen K-1 en K-2; wie een onbevestigd repositorybegrip altijd wil laten openhouden, vraagt daarvoor een apart besluit.

Geen ESS-05-cijfer en geen 0/1. Prioriteit *midden* ordent de aandacht. Een negatieve of open uitkomst blijft zichtbaar en exporteerbaar, maar blokkeert vaststellen of export niet zelfstandig.

## H — terugkoppeling en begrensd herstel

> Onderscheid inhoudelijk tekort, instructieconflict, transportverlies, evaluatorfout, ontbrekend bewijs, storing en schadelijke nabewerking. Meld oorzaak, buur, kenmerk en bron. Start geen herstel. Alleen een afzonderlijk verzoek binnen DEF-638 mag één brongebonden voorstel opleveren; behoud origineel en verschil, verander geen identiteit/context, toets alle geraakte regels opnieuw en stop bij betekenisverlies, bronconflict of ontbrekende buurgrond.

Een voorstel onder DEF-638 volgt deze grenzen:
- het voegt alleen het kenmerk uit de bron toe dat het genoemde verwante begrip afgrenst;
- geen trefwoord, geen contrastzin als enige wijziging, geen vernauwing buiten de bron, geen tweede definitie in de kern en geen wijziging van term, naam of context;
- ESS-05 en STR-02/STR-04, ESS-01, SAM-03, INT-06 en CON-02 worden opnieuw getoetst.

Uitsluitend toetsen verandert geen tekst. Automatisch herstel is niet actief.

Voorbeeld van terugkoppeling: "'Sanctie die door de rechter wordt opgelegd' geldt ook voor taakstraf. Voeg het kenmerk toe dat geldboete van taakstraf onderscheidt volgens de bron; schrijf niet 'in tegenstelling tot een taakstraf' zonder dat kenmerk."

## Afbakening

- **ESS-03** beslist instantie-identiteit; **ESS-05** beslist begripsonderscheid.
- **STR-04** toetst de vorm van de toespitsing. ESS-05 meldt zijn eigen inhoudelijke reden, zonder onderdrukking over en weer (K-8); een STR-04-vormfout is niet vanzelf een ESS-05-gebrek.
- **ESS-01** beslist of een doelkenmerk begripsbepalend is.
- **CON-01** bewaakt context en noodzakelijke namen; **CON-02** de bronsteun.
- **SAM-03/INT-06** bewaken geneste definities en toelichting; **INT-09** de limitatieve opsomming.
- **CON-CIRC-001** beoordeelt letterlijke termherhaling; **ESS-CONT-001/VAL-LEN-001** een te korte kern.
- De gedeelde vaststel- en exportpoort valt onder DEF-624/DEF-630, herstel onder DEF-638, de ontologieleverancier onder DEF-300, en de appbrede contextplicht onder DEF-622.

Bronregel: ASTRA-pagina 'Voldoende onderscheidend', revisie 8561 (11 februari 2025 07:47:05 UTC). 'Politie' is de door ASTRA genoemde herkomst en is niet zelfstandig gelezen. De afbakening van de vergelijkingsruimte, de overlapregel, de afgrenzingsuitwerking, de informatievoorwaarden en de lege-ruimte-uitkomst zijn lokale uitwerking (K-1…K-10); die worden onder DEF-625 geregistreerd.
````

### 3.2 `definitie-nederlandse-definities`

**(a) `reference.md:81`**, bestaand:

```
1. De differentia moet het begrip **onderscheiden** van zijn zusterbegrippen (ESS-05)
```

Vervangen door:

```
1. De differentia moet het begrip **onderscheiden** van zijn verwante begrippen: zusterbegrippen onder hetzelfde genus én begrippen die in dezelfde context met het begrip verward kunnen worden of deels dezelfde gevallen dekken (ESS-05). Zelftest per verwant begrip: welk kenmerk in de kern grenst gevallen van dat begrip af die volgens bron of bedoelde betekenis niet onder dit begrip vallen? Gedeelde gevallen mogen — dezelfde persoon kan lener én werknemer zijn zolang 'actuele lening' en 'arbeidsovereenkomst' de rollen afgrenzen. Een ander woord alleen is geen afgrenzing; een vergelijkingszin of het woord 'uniek' vervangt geen concreet kenmerk. Zie [`references/ess05-onderscheid.md`](references/ess05-onderscheid.md).
```

**(b), (c)** — ongewijzigd t.o.v. v1 §3.2 (b), (c), met in (c) als vervangende tekst:

```
| Onderscheidend | Kern heeft per verwant begrip in deze context een onderbouwd kenmerk dat gevallen van dat begrip afgrenst; gedeelde gevallen mogen | ESS-05 |
```

**(d) `reference.md:281`**, bestaand:

```
4. ☐ Differentia onderscheidt van zusterbegrippen
```

Vervangen door:

```
4. ☐ Differentia grenst elk verwant begrip in deze context af (gedeelde gevallen toegestaan); inhoudelijk oordeel doet de app per verwant begrip (ESS-05)
```

**(e) `SKILL.md` na regel 63** (na het ESS-04-blok), toevoegen:

```
## ESS-05 — voldoende onderscheidend

Lees bij formuleren het [gedeelde ESS-05-contract](references/ess05-onderscheid.md) (byte-identieke, versiegebonden kopie van de canonieke bron in skill `definitie-toetsregels`). Kies bovenbegrip en toespitsende kenmerken zodat de kern per verwant begrip in de vastgelegde context een onderbouwd kenmerk heeft dat gevallen van dat begrip afgrenst die volgens bron of bedoelde betekenis niet onder dit begrip vallen; gedeelde gevallen (één persoon in twee rollen) mogen, en een ander woord alleen is geen afgrenzing. Ontleen kenmerken aan bron en bedoelde betekenis; verzin geen verwant begrip, kenmerk, tegenvoorbeeld of bron en vernauw niet verder dan de bron draagt. Een vergelijkingszin is een vormoptie; ‘uniek’, ‘specifiek’ en ‘kenmerk’ vervangen geen concreet kenmerk, maar blijven staan als deel van een door de bron gedragen naam of vaste term; een contrast dat de definitie van het andere begrip nodig heeft hoort in de toelichting. Zonder context wordt niet gegenereerd; zonder bekende verwante begrippen mag één brongebonden kandidaat ontstaan en blijft ESS-05 open. De inhoudelijke beoordeling doet de Definitie-app zelf (AI-beoordeling per verwant begrip, geen cijfer, geen zelfstandige vaststelblokkade, geen automatische herschrijving); dit blok is geen opgeslagen beoordeling.
```

**(f), (g), (h)** — ongewijzigd t.o.v. v1 §3.2 (f), (g), (h).

### 3.3 `definitie-ontologisch-modelleren`

**(a) `reference.md:204`**, bestaand:

```
2. **Differentia uit zusterbegrippen**: de differentia moet het begrip onderscheiden van zijn zusterbegrippen (toetsregel ESS-05)
```

Vervangen door:

```
2. **Differentia uit verwante begrippen**: neem uit het model de zusterbegrippen (zelfde direct genus) én begrippen met overlappende betekenis in dezelfde context; de differentia moet gevallen van elk daarvan afgrenzen die volgens bron of bedoelde betekenis niet onder dit begrip vallen (toetsregel ESS-05). Overlappende klassen of rollen die één individu tegelijk kan vervullen zijn toegestaan zolang het afgrenzende kenmerk kenbaar is. Lever deze verwante begrippen mét hun definitie en herkomst aan bij generatie en toetsing; zonder context of zonder bevestigd verwant begrip blijft de ESS-05-beoordeling respectievelijk niet uitgevoerd of open. Zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

**(b)** — ongewijzigd t.o.v. v1 §3.3 (b).

### 3.4 `definitie-voorbeelden-generatie`

**(a) `reference.md:165`**, bestaand:

```
| **ESS-05** (Onderscheid van verwante) | Tegenvoorbeelden verduidelijken de grenzen met zusterbegrippen |
```

Vervangen door:

```
| **ESS-05** (Voldoende onderscheidend) | Waar het te onderbouwen is, kan een tegenvoorbeeld helpen: een geval van een verwant begrip dat op een benoemd kenmerk van de definitie faalt, zodat zichtbaar wordt welk kenmerk afgrenst. Dit is illustratieve hulp, geen extra slaageis: het ontbreken van een tegenvoorbeeld is geen ESS-05-gebrek, en een tegenvoorbeeld bewijst het onderscheid niet — de beoordeling per verwant begrip doet dat. Een geval dat beide begrippen tegelijk dekt (één persoon als lener én werknemer) is geen tegenvoorbeeld en geen gebrek. Markeer bedachte voorbeelden als synthetisch; verzin geen feit of bron |
```

**(b) `reference.md` na regel 184** (Stap 2, na "…verscherp de differentia"), toevoegen:

```
- Voor ESS-05 is dit hulp bij, geen vervanging van, de toetsing per verwant begrip: leg waar mogelijk vooraf vast of een begrip bedoeld is onderscheiden te zijn en door welk kenmerk. Een geval dat onder twee onderscheidbare rollen valt, bewijst geen te brede definitie. Een synthetisch voorbeeld of een label dat uit dezelfde definitie is gegenereerd, is geen onafhankelijk bewijs.
```

**(c), (d)** — ongewijzigd t.o.v. v1 §3.4 (c), (d).

### 3.5 `definitie-ufo-ontologie`

Ongewijzigd t.o.v. v1 §3.5, met in de toe te voegen tekst "overlap is voor ESS-05 geen gebrek zolang het onderscheidende kenmerk kenbaar is" vervangen door "gedeelde gevallen zijn voor ESS-05 geen gebrek zolang een kenmerk de rollen afgrenst". Volledige tekst:

```
**ESS-05-toepassing.** Verwante begrippen zijn de andere subtypes onder hetzelfde bovenbegrip (subkind/role/phase onder dezelfde kind) en begrippen van een ander type die in dezelfde context met het begrip verward kunnen worden. Een categorie- of stereotypelabel onderscheidt geen begrippen; alleen begripsbepalende kenmerken doen dat. Rollen die één individu tegelijk kan vervullen (verdachte én getuige, lener én werknemer) zijn onderscheidbare begrippen met overlappende extensie: gedeelde gevallen zijn voor ESS-05 geen gebrek zolang een kenmerk de rollen afgrenst. De inhoudelijke ESS-05-beoordeling doet de app per verwant begrip; zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

### 3.6 `definitie-juridisch-nederland`

**`reference.md` direct na regel 138** (`- ❌ \`boete\` → ✅ \`bestuurlijke boete\` (onderscheid met strafrechtelijke boete)`), toevoegen:

```
- Voor ESS-05 zijn de verwante begrippen contextgebonden. Binnen de vastgelegde context (CON-01) tellen alleen begrippen die in die context relevant zijn. Dezelfde term met een betekenis buiten die context is een homoniem en geen verplicht vergelijkingsbegrip; vergelijk alleen wanneer beide betekenissen binnen dezelfde vastgelegde context relevant zijn. Verwante begrippen worden per bron of door de gebruiker aangewezen, niet uit een algemene juridische indeling afgeleid; onderscheid in één rechtsgebied is geen universeel onderscheid. Zonder vastgelegde context wordt ESS-05 niet uitgevoerd. Zie skill `definitie-toetsregels`, `references/ess05-onderscheid.md`.
```

Deze tekst voegt geen rechtsinhoudelijke claim toe; de vervallen zusterindeling uit v1 is niet vervangen door een andere indeling.

## 4. Publicatie op de centrale setup-repo (later, gescheiden en af te stemmen)

Ongewijzigd t.o.v. v1 §4 (freeze ALG-391, eigen ALG-branch en -issue, eerst canonieke bron dan kopie, regelnummers opnieuw vaststellen, setup-tellingen ALG-423, review, pas na merge van DEF-768, prioriteitsverdeling buiten scope). Publicatie gebruikt v2, niet v1.

## 5. Controle van dit voorstel

- **Inhoud.** Gecontroleerd met `logs/def768/review24-controle-v2.py`: G- en T-citaat gelijk aan de app (T met het gemelde slotverschil); geen "horen niet in de kern", geen extensieformulering, geen prioriteit `hoog`, geen O2- of "later goedgekeurde AI"-formulering, geen "Eén tegenvoorbeeld per verwant begrip" als imperatief en geen zusterindeling "(dwangsom, last onder bestuursdwang)" in de voorgestelde teksten; bestaande fragmenten letterlijk in de beheerde bron.
- **Codegrens.** Code, tests en uitvoercontracten die dit voorstel beschrijft, staan in de worktree; zie het uitvoercontract v2. Dit document zelf wijzigt geen code.

## 6. Disposities (Codex-punten en gerichte review, voor zover skilltekst)

| Punt | Dispositie |
|---|---|
| Codex 1 / RE5-03 tweede punt / RE5-06 | gecorrigeerd: één beslisvolgorde, gelijk aan de app, als bestaande implementatiekeuze (§1.3 punt 7, §3.1 (i)) |
| Codex 3 | gecorrigeerd: geen trefwoordverbod; namen en vaste termen blijven (§1.3 punt 10) |
| Codex 4 | gecorrigeerd: homoniemen buiten de context geen verplicht vergelijkingsbegrip; zusterindeling vervallen (§3.6) |
| Codex 5 | gecorrigeerd: tegenvoorbeeld als hulp, geen slaageis, synthetisch gemarkeerd, geen bewijs (§3.1 (g), §3.4) |
| RE5-01 | gecorrigeerd binnen K-3b/K-5 (§1.3 punt 2, N/G/T); K-3c en verplichte 'bedoelde betekenis' niet overgenomen |
