# DEF-766 — onafhankelijke review van fase 1

**Advies: eerst corrigeren; deze diff is nog niet klaar voor de onafhankelijke eindtest.** De technische basis is aangesloten en de gerapporteerde regressietests zijn groen, maar er zijn bevestigde tekortkomingen in actuele binding, invoertransport, uitvoercontrole, verduidelijkingen en uitvoeringsbegrenzing.

De vooraf opgestelde eindset is niet gewijzigd of vrijgegeven. Dit rapport bevat geen specifieke eindgevallen of antwoorden daaruit.

## Beoordeelde identiteit en werkwijze

| Onderdeel | Gecontroleerde stand |
|---|---|
| Werkboom | `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app` |
| Branch | `feature/DEF-766-ess03-ai-beoordeling` |
| Base en HEAD | `2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644` |
| Implementatie | Ongecommitteerde wijzigingen, inclusief nieuwe bestanden |
| Seal | `phase1-coordinator-seal-v2.json` |
| SHA256 seal | `cb489c30092f5cc7444d6045e22a54688197c2837223af324aa297430559ec8d` |
| Hashcontrole | Alle **47 sealbestanden** komen overeen, ook bij de afsluitende controle |
| Uitvoerdersmanifest | 44 bestanden; manifesthash komt overeen met het seal |
| Ontwikkelrun | Hash `e0a9603bc6199006887eab59f5e08d96e87585b2f48b7c81c0afbe193d5de3f4` bevestigd |

Het oude menselijke ADR is buiten de implementatiereview gehouden. Leidende specificatie is het opgegeven implementatieplan.

Ik heb de review zelfstandig uitgevoerd, met de skill `requesting-code-review`, zonder agents, extra AI-CLI-sessies, modelcalls of repositorywijzigingen. Naast code-inspectie en logcontrole heb ik deterministische controles in het geheugen uitgevoerd met vervangen netwerkgrenzen. Die bewijzen technisch gedrag, geen semantische modelbetrouwbaarheid.

## Bevestigde bevindingen

**Dispositie voor R1–R9: fix nu.** Deze bevindingen zijn nog open; er zijn in deze review geen fixes, waivers of nieuwe issues aangemaakt.

### R1 — P1: oude norm-, prompt- en modelbinding blijft actueel

**Locatie:** [contract.py:551](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/domain/ess03/contract.py:551), `valideer_beoordeling` vanaf regel 585; [definition_edit_service.py:192](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/definition_edit_service.py:192).

**Trigger:** Een opgeslagen beoordeling wordt heropend nadat norm, prompt of model is veranderd, terwijl kandidaat en context gelijk blijven.

De replay controleert contractversie, invoervingerafdruk en aanwezigheid van een modelnaam. `prompt_version` en `norm_sha256` worden slechts overgenomen in de samenvatting; een vergelijking met de actuele beoordelingsconfiguratie ontbreekt. Ook de opgeslagen materiaal- en prompthashes worden niet gevalideerd.

**Bewijs:** Een document met een correcte kandidaatvingerafdruk, `obsolete-prompt`, `obsolete-norm`, `retired-model` en een onjuiste materiaalhash leverde bij de echte replay op:

```text
status=pass
applied=True
```

**Impact:** Een historische beoordeling verschijnt als actuele AI-beoordeling. De opslagvelden bieden daardoor minder bescherming dan het verslag claimt.

**Gewenste correctie:** Laat opslag/readback en replay de volledige actuele beoordelingsbinding controleren. Een afwijking moet zichtbaar historisch of niet-actueel worden; louter aanwezigheid van herkomstvelden volstaat niet.

### R2 — P1: de parser en antwoordstructuur zijn niet gesloten

**Locatie:** [ess03_assessment_service.py:244](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/validation/ess03_assessment_service.py:244), [contract.py:397](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/domain/ess03/contract.py:397).

**Trigger:** Het model retourneert omliggende tekst, onbekende velden of meerdere vragen in één string.

De parser selecteert de tekst tussen de eerste `{` en laatste `}`. Daardoor wordt een onjuist omhuld antwoord stil teruggebracht tot een geldig object. De structuurcontrole heeft geen gesloten veldenset en controleert bij onvoldoende informatie alleen of `question` een niet-lege string is.

**Bewijs:**

```text
geldig object + trailing tekst → geaccepteerd
onbekend extra veld           → pass
"Welke bron? Welk tijdvak?"    → beide vragen doorgegeven
```

**Impact:** Niet-contractuele uitvoer kan als geldige beoordeling worden verwerkt. De eis van precies één gerichte vraag is niet geborgd.

**Gewenste correctie:** Controleer het volledige antwoord en de toegestane velden/typen. Wijs technisch ongeldige uitvoer af als technische fout; herstel haar niet door tekst of velden weg te laten. Borg daarnaast de afgesproken vraagvorm.

### R3 — P1: afgewezen bewijs en foutieve antwoorden worden toch toegepast of gecachet

**Locatie:** [contract.py:483](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/domain/ess03/contract.py:483), [ess03_assessment_service.py:507](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/validation/ess03_assessment_service.py:507), [ai_service_v2.py:246](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/ai_service_v2.py:246).

**Trigger:** Een antwoord bevat zowel geldig als ongeldig bewijs, uitsluitend verzonnen bewijs, of ongeldige JSON.

Een geldig citaat naast een verzonnen citaat kan voldoende blijven voor `pass`; het ongeldige bewijs wordt verwijderd terwijl de oorspronkelijke reden blijft staan. Zonder enig geldig bewijs ontstaat `review_required`, maar het document blijft `assessed` en wordt onthouden. Daarnaast cachet de gedeelde `AIServiceV2` ruwe antwoorden voordat ESS-03 ze valideert.

**Bewijs:**

- Eén bestaand citaat plus `source:missing` resulteerde in **`pass`**, met het tweede bewijsitem onder `rejected`.
- De bestaande servicetest verwacht bij uitsluitend verzonnen bewijs expliciet `assessed`/`review_required`.
- Twee beoordelingen via de echte service- en AIServiceV2-code, met ongeldige JSON aan de vervangen netwerkgrens, leverden tweemaal `error`, maar slechts **één** onderliggende aanroep: het tweede foutantwoord kwam uit de ruwe cache.

**Impact:** Een oordeel kan blijven steunen op een reden waarvan bewijs is afgewezen. “Opnieuw toetsen” kan bovendien hetzelfde technisch ongeldige antwoord teruggeven.

**Gewenste correctie:** Behandel ongeldige bewijsstructuur en niet-verifieerbare aangehaalde grond volgens het afgesproken technische foutbeleid. Cache voor deze route uitsluitend volledig gevalideerde beoordelingen, inclusief controle van de onderliggende cachelaag.

### R4 — P1: aangeleverde betekenisverduidelijking bereikt ESS-03 niet consequent

**Locatie:** [definition_orchestrator_v2.py:1226](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/orchestrators/definition_orchestrator_v2.py:1226), `_toets_kandidaat` vanaf regel 1837; [definition_edit_service.py:37](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/definition_edit_service.py:37).

**Trigger:** Generatie of editor-hertoetsing met een aanwezige `betekenisverduidelijking`.

De generatie bewaart deze gebruikersbedoeling later wel in metadata, maar geeft haar niet mee aan de validatiekandidaat of validatiecontext. De editorcontext neemt de betekenisverduidelijking uit de generatieregistratie evenmin over. De replay gebruikt dat veld vervolgens wél.

**Bewijs:**

```text
GenerationRequest.betekenisverduidelijking: aanwezig
intentie ontvangen via _toets_kandidaat:   None

betekenisverduidelijking bij replay:       aanwezig
betekenisverduidelijking bij editor-toets: None
```

**Impact:** ESS-03 kan een andere betekenis beoordelen dan de gebruiker heeft opgegeven. Een nieuw oordeel kan vervolgens bij opslag/readback niet aansluiten op de rijkere invoerbinding.

**Gewenste correctie:** Gebruik dezelfde volledige, actuele betekenisgegevens voor generatievalidatie, losse toetsing, editor-hertoetsing, opslag en replay.

### R5 — P1: gewijzigde of gewiste ESS-03-verduidelijking wordt verkeerd verwerkt

**Locatie:** [definition_edit_service.py:169](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/definition_edit_service.py:169), [definition_edit_tab.py:2112](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/ui/components/definition_edit_tab.py:2112).

**Triggers:**

- De gebruiker wist een opgeslagen verduidelijking.
- De gebruiker vervangt een bestaande verduidelijking, valideert opnieuw en slaat op.
- De gebruiker wijzigt de verduidelijking na de laatste toetsing.

Een lege actuele waarde valt in `ess03_intentie_van_definition` terug op de oude beoordeling. De opslagactie vervoert de widgetwaarde niet in `updates`; de servicelaag werkt daardoor met oude recordmetadata of leidt de bedoeling af uit de meegegeven beoordeling.

**Bewijs:**

```text
gewiste verduidelijking → oude tekst hersteld; replay blijft pass
nieuwe beoordeling met gewijzigde verduidelijking
                       → bindingsafwijzing tegenover oude recordmetadata
```

**Impact:** Bewust gewiste betekenisgrond blijft gelden, een verse beoordeling kan niet worden opgeslagen, en de opslagcontrole ziet niet noodzakelijk wat momenteel in het verduidelijkingsveld staat.

**Gewenste correctie:** Vervoer de actuele verduidelijking expliciet bij opslaan, onderscheid afwezig van bewust leeg en controleer de beoordeling tegen die actuele waarde. Herstel geen oude verduidelijking over een bewuste wijziging heen.

### R6 — P1: totale tijdgrens en “geen retries” zijn niet geborgd

**Locatie:** [ess03_assessment_service.py:438](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/validation/ess03_assessment_service.py:438), [ai_service_v2.py:233](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/ai_service_v2.py:233), [async_api.py:211](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/utils/async_api.py:211), [run_ess03_gevallen.py:127](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/scripts/ess03/run_ess03_gevallen.py:127).

**Trigger:** Trage nabewerking of een tijdelijke providerfout.

`asyncio.wait_for` omvat uitsluitend de clientaanroep. Tokenraming en monitoring vallen erbuiten; service en runner leggen geen totale deadline op. Het uitschakelen van SDK-retries schakelt bovendien de afzonderlijke retrylus van `AsyncGPTClient` niet uit.

**Bewijs:**

- D01 duurde **163,125 seconden** bij een ingestelde grens van 60 seconden.
- Met een onmiddellijke netwerkvervanger en vertraagde tokenraming retourneerde de echte `generate_definition` succesvol na **0,085 seconde** bij een timeout van **0,01 seconde**.
- Eén aanroep door de bestaande clientroute veroorzaakte bij een synthetische tijdelijke fout **drie provideraanroepen**.
- `retry_count=0` wordt in AIServiceV2 hardcoded ingevuld en bewijst dus geen afwezigheid van onderliggende retries.

**Impact:** De duur- en callbudgetclaims zijn niet betrouwbaar afgedwongen. De precieze oorzaak van de 163 seconden is niet gemeten; tiktoken blijft daarvoor een hypothese.

**Gewenste correctie:** Begrens de gehele beoordelingsoperatie, inclusief mogelijk blokkerende nabewerking. Configureer de proefroute aantoonbaar zonder herhalingen op alle lagen en rapporteer werkelijk gemeten pogingen.

### R7 — P1: afgekapt bronmateriaal kan toch een volledig actueel oordeel opleveren

**Locatie:** [ess03_assessment_service.py:412](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/services/validation/ess03_assessment_service.py:412), `_verzonden` vanaf regel 558; [contract.py:754](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/domain/ess03/contract.py:754).

**Trigger:** Een bronpassage overschrijdt de standaardgrens van 4.000 tekens.

De passage wordt afgeknipt. Een markering reist mee, maar een afgerond oordeel wordt niet tegengehouden. De kandidaatvingerafdruk betreft de volledige bronset; de replay controleert citaten opnieuw tegen volledige passages en gebruikt de verzonden-materiaalbinding niet.

**Bewijs:** Met een verkleinde passagegrens en een vervangen modelantwoord leverde de echte service op:

```text
input.afgekapt = ["doc:local-probe"]
assessment    = assessed/pass
replay        = pass
```

**Impact:** Een beoordeling over gedeeltelijk materiaal kan als actuele beoordeling van de volledige aangeleverde grondslag verschijnen. Dit bewijst geen specifieke semantische modelfout, maar wel dat de technische volledigheidswaarborg ontbreekt.

**Gewenste correctie:** Zorg dat noodzakelijke informatie niet stil buiten de beoordeling valt en dat replay exact dezelfde verzonden bewijsbasis respecteert. Een technisch onvolledig aangeboden geval mag niet zonder passende beperking als volledig beoordeeld gelden.

### R8 — P1: D04 en D07 verwarren ontbrekende beslisgrond met bewezen afkeur

**Locatie:** [ontwikkelgevallen_v1.json:47](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/tests/fixtures/ess03/ontwikkelgevallen_v1.json:47), D07 vanaf regel 85; [ontwikkelrun-v1.json](/tmp/def766-ai-20260921/ontwikkelrun-v1.json), betreffende `judgment`-blokken.

**Trigger:** Een kandidaat steunt op een registratienummer waarvan de noodzakelijke identificatieconventie niet is aangeleverd.

Bij D04 noemt het model ontbrekende onderbouwing van referentsoort, naamruimte en geldigheid, maar concludeert toch `fail`. Bij D07 speelt daarnaast circulariteit als zelfstandige afkeurgrond mee. Geen van beide antwoorden toont een codebotsing, verkeerde referentsoort of andere bewezen ondeugdelijke identificatie aan.

**Impact:** De gebruiker krijgt een inhoudelijke afkeuring waar eerst noodzakelijke informatie moet worden gevraagd. Circulariteit kan een andere regel raken, maar bewijst op zichzelf deze ESS-03-overtreding niet.

**Gewenste correctie:** Herstel het onderscheid tussen ontbrekende beslisgrond en aantoonbaar ondeugdelijke afgrenzing. Onderbouw dat met ontwikkelbewijs vóór vrijgave van de eindset. Behoud de oorspronkelijke antwoorden en labels.

D06 is afzonderlijk ambigu; zie de inhoudelijke beoordeling hieronder. Het faseverslag mag daarom niet alle drie afwijkingen zonder nadere kwalificatie als bewezen onterechte afkeuringen presenteren.

### R9 — P2: de UI toont onvoldoende informatie als generiek “Nog te beoordelen”

**Locatie:** [validation_view.py:495](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/ui/components/validation_view.py:495), `_UITKOMSTLABEL`; [contract.py:674](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/src/domain/ess03/contract.py:674).

**Trigger:** Een geldige AI-uitkomst `insufficient_information`.

De UI kiest het label op basis van `review_required`, zonder het inhoudelijke verdict voor het label te gebruiken.

**Bewijs:** De echte renderer met gemockte Streamlit-uitvoer toonde de vraag en ontbrekende informatie, maar uitsluitend het label **“Nog te beoordelen”**. Het expliciete label **“Onvoldoende informatie”** ontbrak.

**Impact:** De vier afgesproken inhoudelijke uitkomsten zijn niet expliciet onderscheiden van een niet-uitgevoerde of niet-bruikbare beoordeling.

**Gewenste correctie:** Toon het inhoudelijke label voor een uitgevoerde onvoldoende-informatiebeoordeling; reserveer generieke openheidslabels voor werkelijk niet-beschikbare beoordelingen.

## Onafhankelijke beoordeling van de twaalf ontwikkelgevallen

De oorspronkelijke verwachtingen blijven ongewijzigd. Onderstaande beoordeling is geen herlabeling van het bestand.

| Geval | Verwacht → model | Onafhankelijke beoordeling |
|---|---|---|
| D01 | voldoet → voldoet | Verdedigbaar: natuurlijke grens en peilmomentconventie zijn aangeleverd. Een concrete datum is niet nodig om de definitiekern als afbakeningscriterium te beoordelen. |
| D02 | voldoet niet → voldoet niet | Onderbouwd: de fictieve bron maakt expliciet dat verschillende fysieke exemplaren dezelfde code dragen. |
| D03 | niet van toepassing → idem | Onderbouwd door de expliciete stoflezing. Het categorielabel verandert die bedoeling niet. |
| D04 | onvoldoende informatie → voldoet niet | Verwachting verdedigbaar; modelafkeur onvoldoende onderbouwd. Identificerende werking en scope ontbreken, maar ondeugdelijkheid is niet aangetoond. |
| D05 | voldoet niet → voldoet niet | Onderbouwd: de kandidaat ontkent zelf de uniciteit van het enige bedoelde identificatiemiddel. |
| D06 | voldoet → voldoet niet | **Niet ondubbelzinnig als acceptatiegeval.** De bron onderbouwt nummerbinding aan reeds onderscheiden meetobjecten binnen R, maar specificeert niet welke eenheidsvorming van “meetobject” beoordeeld moet worden. |
| D07 | onvoldoende informatie → voldoet niet | Verwachting verdedigbaar. De noodzakelijke registerconventie ontbreekt; circulariteit vormt geen zelfstandig bewijs dat het identificatiemiddel ondeugdelijk is. |
| D08 | voldoet → voldoet | Hoofdoordeel verdedigbaar: gekozen hoeveelheid en continuïteitsconventie zijn aanwezig. De aanvullende modelonzekerheid over meerdere monsters uit dezelfde monsterneming strookt niet met de expliciete één-monsterconventie. |
| D09 | onvoldoende informatie → idem | Onderbouwd: tegenstrijdige continuïteitsconventies zonder toepasselijkheidskeuze. De vraag is gericht. |
| D10 | niet van toepassing → idem | Onderbouwd door de expliciete algemene verschijnsellezing; hiervoor zijn geen externe juridische feiten nodig. |
| D11 | voldoet niet → voldoet niet | Onderbouwd: de bron onderscheidt registratie-identiteit van gebeurtenisidentiteit en noemt meerdere rij-ID’s voor dezelfde gebeurtenis. |
| D12 | voldoet → voldoet | Verdedigbaar op het ingestelde orgaan als geheel en de aangeleverde continuïteit. De extra verwachting “één commissie per instellingsbesluit” staat echter alleen in `grond`, niet in het modelmateriaal, en mag niet als meegeleverd bewijs worden gebruikt. |

**D06 nader:** Voor het onderscheiden van reeds afgebakende meetobjecten binnen R ondersteunt de bron een positieve beoordeling. Voor de afbakening van de referenten vóór registratie ontbreken gegevens. De bedoelde beoordelingsscope is niet expliciet gemaakt: geldt de registeropname als eenheidsconventie, of moet een zelfstandige fysieke/functionele eenheidsgrens worden vastgesteld? Het modelantwoord maakt die keuze evenmin zorgvuldig en beroept zich mede op circulariteit.

Daarom blijft **9/12 labelovereenkomst** een juiste beschrijving van de oorspronkelijke run. Het is geen zelfstandig bewezen inhoudelijk kwaliteitspercentage. “Drie bewezen onterechte afkeuringen” is te stellig; D04 en D07 zijn bevestigd problematisch, D06 vraagt kwalificatie.

## Bewijscontrole en reikwijdte

De behouden logs ondersteunen:

| Controle | Gelezen resultaat |
|---|---|
| Tweede `make test` | Exit 0; **6764 passed, 75 skipped, 722 deselected, 1 xfailed** |
| Laatste gerichte set | **822 passed, 2 skipped**; exit 0 volgens exitcoderegistratie |
| `make lint` | Exit 0; Ruff en Black op `src/` en `config/` |
| RED/GREEN | Logs aanwezig voor contract, service, evaluator, wrappers, generatie, UI en opslag |
| Ontwikkelcalls | Twaalf antwoorden en twaalf HTTP-200-regels; oorspronkelijke afwijkingen behouden |
| Eigen whitespacecontrole | `git diff --check` geslaagd |

Een deel van RED bestaat uit collectiefouten wegens nog ontbrekende modules. Dat toont vooraf falende tests, maar niet voor ieder afzonderlijk acceptatiepunt een gedragsmatige RED. De tussentijds falende UI- en unitruns zijn behouden; de latere groene eindruns vervangen die historie niet.

Voor alle twaalf ontwikkelgevallen heb ik prompts en bindingen opnieuw berekend. Systeem-/gebruikersprompt, kandidaatvingerafdruk, materiaalhashes en ruwe antwoordhashes kwamen overeen. Er was geen passageafkapping. `verwacht` en `grond` worden niet naar het model gestuurd. Dat voorkomt labellekkage, maar betekent ook dat uitsluitend in `grond` opgenomen domeinafspraken geen modelinvoer zijn.

De technische controles ondersteunen verder:

- De nieuwe evaluator is geregistreerd; normale generatie en wrappers zijn aangesloten op dezelfde serviceklasse.
- De service gebruikt `AIServiceV2` met taak `validation` en ModelRouter, zonder eigen hardcoded model.
- De normale wrapper verwijdert caller-supplied `ess03_assessment`.
- NA is additief opgenomen in enum, schema, dekking en UI, zonder omzetting naar pass.
- ESS-03 blijft scoreloos; de negatieve violation is niet-kritiek en wordt uit automatische herstelkeuze gehouden.
- Er zijn echte tijdelijke SQLite-tests voor opslag, herladen en historie. Dat is meer dan sessiecachebewijs, maar bewijst niet de ontbrekende actuele norm-/prompt-/modelcontrole uit R1.

## Nog ontbrekend acceptatiebewijs

Deze punten zijn **geen zelfstandig bewezen runtimebugs**, maar verhinderen volledige acceptatie:

1. **Onafhankelijke eindset:** twintig gevallen, vier metamorfosen, twee injectievarianten en eventuele herhalingen zijn nog niet uitgevoerd.
2. **Echte browserbediening:** UI-bewijs gebruikt gemockte Streamlit-aanroepen. De volledige gebruikersroute is nog niet bewezen.
3. **Vaststellen/exporteren:** er is bewijs voor acceptatiepariteit, een echte gate-evaluatie en uitsluiting van herstel. De opslagtest voedt die gate met een zelf samengesteld ESS-03-issue. Een volledige gekoppelde actieproef via de echte vaststel- én exportroute ontbreekt; behoud van blokkades door andere regels moet daarin zichtbaar blijven.
4. **Volledige readbackmatrix:** bestaande opslagtests dekken onder meer tekst en toelichting. Zij bewijzen niet alle vereiste wijzigingen van term, context, broninhoud, betekenis, verduidelijking, norm, prompt en model.
5. **Inhoudelijke injectiebestendigheid:** promptinstructies en escaping zijn aanwezig, maar bewijzen niet dat echte modeluitvoer injecties weerstaat.
6. **Definitieve publicatie:** correctiediff, bijbehorende regressies, nieuw seal en duurzame bewijspublicatie ontbreken nog.

## Vervolgadvies

Laat dezelfde Claude-uitvoerder R1–R9 corrigeren en het faseverslag begrenzen tot daadwerkelijk bewezen gedrag. Behoud alle eerste modelantwoorden en verwachtingen. Kwalificeer D06 als ambigu zonder het oorspronkelijke label te vervangen.

Laat vervolgens dezezelfde reviewersessie de correctiediff en het gerichte bewijs controleren. Verzegel daarna de uiteindelijke bron-, prompt-, norm- en modelbinding vóór vrijgave van de ongewijzigde onafhankelijke eindset.

**Geen vrijgave voor eindtest of publicatie op de huidige diff.** Er zijn geen waivers verleend. Deze review geeft geen menselijke expertvalidatie of universele betrouwbaarheidsgarantie.

Een gecombineerde Python-inspectieopdracht werd door de lokale beveiligingshook geblokkeerd als “Gevaarlijke Python one-liner”. De hashcontrole is daarna met standaard `shasum` uitgevoerd; er resteert hierdoor geen bewijsblokkade.