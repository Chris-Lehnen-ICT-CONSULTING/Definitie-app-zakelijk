# INT-03 — herzien advies onderzoeker B — v2

25 september 2026. **Volledig herzien advies na fase-2-review; voorstel, geen normbesluit of implementatie.**

INT-03 beschermt begrijpelijke verwijzingen, niet de afwezigheid van voornaamwoorden. De huidige toetsing bewaart onzekerheid als `review_required`, maar beoordeelt geen antecedenten. De generatie-instructie bevat lokale beperkingen en bereikt in de onderzochte adaptervarianten alleen de prompt met juridische context. Mijn voorkeur is verduidelijking van norm en generatie-instructie, gevolgd door betere menselijke beoordelingshulp. Een AI-oordeel is een afzonderlijke, toetsbare productkeuze.

## Wijzigingen sinds v1 en resterende verschillen

Deze volledige v2 verwerkt alle zestien punten uit A’s review; de verantwoording staat in [verwerking-b-v1.md](verwerking-b-v1.md). De oorspronkelijke zes v1-bestanden, casus-IDs, vooraf vastgelegde verwachtingen en metingen blijven ongewijzigd.

- RB-05: E03/E04 bevatten het lemma al vóór enig herstel. Hun CON-CIRC-fails zijn geen bewijs van door INT-03-herstel veroorzaakte schade; de verplichte fixture blijft geldig voor de INT-03-nulmeting.
- RB-07: G-B1 is verkort voor instruction_map; het volledige G/T/H-contract staat als publiceerbare skilltekst. Ontbrekende bedoeling mag niet worden ingevuld. Vragen behoren buiten de definitiekern en vereisen een aantoonbare uitvoerroute; zij zijn niet exclusief voor AI-toetsing.
- RB-11/12/14/16: de onderzochte UI-route toont geen INT-03-reden. Zichtbare passagehulp en versiegebonden vastlegging zijn expliciete leveringsvoorwaarden; volledige opslagafwezigheid is niet bewezen.
- RB-15: de menselijke-hulpproef omvat ook goede en ruisgevoelige gevallen. De korte G-tekst is een nieuwe voorgestelde variant, nog niet op effect getest.

A heeft zijn T-b (groen zonder hit) en concrete het-regex ingetrokken in de review op B; B’s oordeel verandert daardoor niet. De reviews [op A](review-b-op-a-v1.md) en [op C](review-b-op-c-v1.md) bewaren andere verschillen. C’s hele-INT-keuze, lemma-scope en afhankelijkheid van fail van bekende herstelbedoeling worden niet overgenomen. Het gemeten juridische/contextloze promptlengteverschil is geen geïsoleerde INT-kostprijs. Geen specifieke ESS-03-poortvrijstelling overhevelen. Deze verschillen gaan als keuzes en correcties naar de synthese, niet als bereikte consensus.

## Status, onafhankelijkheid en bronnen

Onderzoeker B: Codex CLI, sessie `01a0d782-026f-7a70-b451-84c5f82137dd`. De eigen `turn_context`-metadata in `/Users/chrislehnen/.codex/sessions/2026/09/25/rollout-2026-09-25T09-40-16-01a0d782-026f-7a70-b451-84c5f82137dd.jsonl` bevestigt `model=gpt-6-astra`, `effort=high`. Geen bewijs uitsluitend uit config. A coördineert in Cowork; C onderzoekt zelfstandig in Claude Code. Geen nieuwe sessies gestart; vóór opslag van de onafhankelijke v1 zijn geen nieuwe conclusies van A/C of bestaande runlogs in onderzoek-b gelezen. Alleen bestandsnamen zijn toen gecontroleerd om overschrijven te voorkomen. In fase 2 zijn de expliciet overgedragen eerste onderzoeken, proefbestanden en A’s review op B gelezen. Dit doet geen afbreuk aan de eerdere onafhankelijke totstandkoming; v2 is uitdrukkelijk na kruisreview geschreven.

Leesbasis: branch `onderzoek/DEF-772-INT-03-20260925`, commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. De proef controleert de commit opnieuw. De gedeelde feitenbasis heeft SHA-256 `c160479ace16663bc89ebf902e69c1ab7c4f19ad87a0114473eddd82d158662d`, conform opdracht. Repositorygebonden documentatie staat op het expliciet opgegeven DEF-pad. Het centrale projectenregister bevat alleen ALG en biedt geen alternatieve DEF-route.

Methodiek: `~/.agents/skills/toetsregel-onderzoek/SKILL.md`, de drie opgegeven references, `analysis-mode` en `verification-before-completion`. De skill-toolaanroepen voor research-dispatch/analysis-mode kregen “MCP tool call requires approval, but approval policy is never”; lokale instructies zijn rechtstreeks gelezen. Geen algemene dispatchworkflow gestart: B is al toegewezen en andere sessies/uitvoerlocaties zijn verboden. Dit is onderzoek met een hulpproef, geen softwareontwikkeling. Een eerste rapport-schrijfopdracht werd vóór uitvoering wegens onleesbare quote-syntaxis geweigerd; de invoervorm is gecorrigeerd, zonder een bestaand bestand te overschrijven.

### Bronregister

Alle bronnen zijn werkelijk gelezen binnen het genoemde bereik; de eerste bronhashes staan in [bewijsmanifest-b-v1.json](bewijsmanifest-b-v1.json), de fase-2-binding en alle eigen bestandsversies in [bewijsmanifest-b-v2.json](bewijsmanifest-b-v2.json). Repositorypaden hieronder zijn relatief aan de projectroot; `../`-paden relatief aan deze map.

| ID | Bron en claimbereik |
|---|---|
| S1 | `../gedeeld/feitenbasis-v1.md` en `../gedeeld/astra-INT-03-raw-20260925.txt`: gedeelde feiten en letterlijk aangeleverde normtekst. Raw-bron vermeldt ophalen 25-09, HTTP 200 door A; B heeft dat HTTP-verzoek niet uitgevoerd. |
| S2 | `../../../INT-03-v1.md` en `../../../INT-03-bewijs-v1/{gevallen,uitkomsten,claude-review}.json`: historische zes gevallen/twaalf resultaten, commit d68a98a9. Historische review is advies, geen normbesluit. |
| S3 | `docs/analyses/2026-09-07-definitiekwaliteit-dossiers-int-sam.md`, §INT-03; gericht INT-03-materiaal uit `2026-09-11-def606-productonderzoek-bewijs/`; centraal regelregister 17-09. |
| S4 | `src/toetsregels/regels/INT-03.json`; `src/services/validation/evaluators/judgment_review.py`; `src/validation/additional_patterns.py`; `modular_validation_service.py`, `interfaces.py`, managers en runtimefixture: implementatie, geen normbewijs. |
| S5 | `src/services/prompts/modules/json_based_rules_module.py`, `modular_prompt_adapter.py`, `modules/prompt_orchestrator.py`, `modules/integrity_rules_module.py` en bijbehorende context/configtypen: promptselectie en instructies. |
| S6 | Beide skills definitie-toetsregels en definitie-nederlandse-definities: SKILL.md en relevante reference.md-passages in `~/.agents/skills`. Hashvergelijking bevestigt identieke SKILL.md/reference.md-kopieën in `~/.claude/skills` en `~/Projecten/_claude-global-setup/skills`. Geen actuele Cowork-installatie gecontroleerd. |
| S7 | `src/ui/components/validation_view.py`, `expert_review_tab.py`, `src/export/export_txt.py`: gerichte statische inspectie, geen UI-/opslagdoorloop. |
| S8 | `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md` en actuele Linear-issues hieronder: beleid/eigenaarschap. |
| S9 | [Onze Taal: voornaamwoord](https://onzetaal.nl/taalloket/voornaamwoord), §§Soorten en Verwijzing binnen of buiten de tekst; [betrekkelijk voornaamwoord](https://onzetaal.nl/taalloket/betrekkelijk-voornaamwoord), inleiding en §§Die/Dat/Wat/Wie-wat; [Taaladvies: onderwerp](https://taaladvies.net/termen-onderwerp/), §Omschrijving. Rechtstreeks gelezen 25-09: taalkundige onderbouwing, geen appbesluit. |

**S10 — fase 2:** overgedragen A/C-v1-rapporten, A/C-proefverwachtingen, scripts, resultaten, manifesten en genoemde proeflogs; A’s review op B; processtatus-v2. Alle zes manifestgebonden bestanden per onderzoek A/C passen bij hun opgegeven hashes; de zeven C-codehashes passen bij de huidige bron. Gerichte broncontrole herbevestigt service-errorgrens, passage-deduplicatie, UI-presentatie en generieke prefixselectie. Geen nieuwe appproef, modelcall of UI-/opslagdoorloop uitgevoerd. Geen nieuw onleesbaar vereist fase-2-bestand.

**Exacte toegangshiaten:** ASTRA `https://www.astraonline.nl/index.php/Voornaamwoord-verwijzing_duidelijk` en Ross-PDF `https://www.brsolutions.com/wp-content/uploads/2016/10/How-to-Define-Business-Terms-Primer.pdf` geven via de webtool `Internal Error / not accessible`. ASTRA is beschikbaar via S1; Ross DBT §4.3 is niet rechtstreeks gelezen. Het historische Ross-brononderzoek van 7 september beschrijft eveneens onvolledige PDF-dekking; dit vervangt de primaire sectie niet. Geen specifiek opgegeven lokaal onderzoeksbestand bleek onleesbaar. Het aanvankelijk gezochte `src/ui/components/export_txt.py` bestaat niet; het juiste bestand `src/export/export_txt.py` is gelezen. De algemene handover verwijst naar `.claude/handovers/2026-09-23_1914-backup-01a0ce93.md`, dat ontbreekt; dit raakt deze zelfstandige opdracht niet.

Rechtstreeks geraadpleegd op 25-09: [DEF-772](https://linear.app/definitie-app/issue/DEF-772), [DEF-606](https://linear.app/definitie-app/issue/DEF-606), [DEF-624](https://linear.app/definitie-app/issue/DEF-624), [DEF-625](https://linear.app/definitie-app/issue/DEF-625), [DEF-626](https://linear.app/definitie-app/issue/DEF-626), [DEF-630](https://linear.app/definitie-app/issue/DEF-630), [DEF-638](https://linear.app/definitie-app/issue/DEF-638), ter vergelijking [DEF-766](https://linear.app/definitie-app/issue/DEF-766)/[DEF-743](https://linear.app/definitie-app/issue/DEF-743). DEF-772 is Backlog en een placeholder, geen normgoedkeuring. Regelspecifieke besluiten van ESS-03/CON-02 gelden niet automatisch voor INT-03.

## Q1 — norm, lokale toevoegingen en toepasselijkheid

**Bronfeit S1:** ASTRA formuleert: “Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn ''waarnaar'' verwezen wordt.” De toelichting noemt ook `hij`, `het`, `zij` en `dat`; het voorbeeldpaar stelt `die gebeurtenis` tegenover `het`. Voornaamwoorden zijn toegestaan. JUIST(ER) betekent niet dat het voorbeeld aan iedere andere regel voldoet.

| Onderdeel | ASTRA | Lokaal | Duiding B |
|---|---|---|---|
| Doel | Duidelijk waarnaar ieder voornaamwoord verwijst | Uitleg behoudt dit doel | Inhoudelijke overeenkomst. |
| Afstand | Geen eis dezelfde zin/zinsdeel in aangeleverde passage | JSON-toelichting eist dezelfde zin of zinsdeel; prompt dezelfde zin | Lokale aanscherping. Dezelfde zin bewijst geen duidelijkheid; hetzelfde zinsdeel is bij relatieve bijzinnen onnodig beperkend. |
| Verwijzingsdoel | Dingen, waaronder concepten | Expliciet zelfstandig naamwoord | Te smal: een naamwoordgroep, hele uitspraak of ingesloten antecedent kan relevant zijn (S9). |
| Patronen | Geen regexlijst | Tien JSON-patronen plus extra patroon | Zoekheuristiek, geen norm of woordenverbod. |
| Herkomst | DBT 4.3 | Alleen ASTRA | Bewaar beide herkomstlagen met leesstatus; niet doen alsof DBT gecontroleerd is. |
| Type/geldigheid | `term` / `alle` | `interne structuur` / `gehele definitie` | Lokale metadatawijziging. “Alle” bewijst geen toetsing van ieder recordveld. |
| Prioriteit/aanbeveling | Hoog/verplicht | Hoog/verplicht | Bronmetadata bewijst geen cijfer of specifieke softwareblokkade. |

**Interpretatie/voorstel N-B1:** binnen de aangeboden definitiekern moet de bedoelde verwijzing eenduidig vast te stellen zijn. Losse metadata mogen een ontbrekend antecedent niet repareren. Een normale betrekkelijke bijzin mag het genus specificeren. Geen vaste eis dat het antecedent direct voorafgaat, in hetzelfde zinsdeel staat of een los zelfstandig naamwoord is. Dit is een voorgestelde projectinterpretatie van het ASTRA-doel, geen bestaand Chris-besluit.

- **Die/dat:** `persoon die …` en `teken dat …` zijn toegestane constructies. Volledige zin en grammaticale functie bepalen de lezing. Twee naamwoorden betekenen niet automatisch twee even plausibele kandidaten (S9; E06/E16).
- **Vooruitverwijzing:** niet categorisch verbieden; beoordeel de constructie. E08 blijft bewust een beoordelingsgeval met mogelijke concurrentie tussen handeling en aanvraag. ASTRA eist niet expliciet voorafgaande plaatsing. Een specifieke primaire passage over catafora is hier niet gelezen; geen bewezen algemene vrijstelling claimen.
- **Bezittelijk:** ook `zijn`, `haar`, `hun`, `diens` vragen een duidelijke bezitter. Nabijheid of woordgeslacht alleen beslist niet. E07 toont ontbrekende signaaldekking; E17 beschermt bezit en rollen.
- **Het:** lidwoord en loos onderwerp vragen geen fictief antecedent. Taaladvies beschrijft het loos onderwerp (S9). E10 behoudt zijn vooraf vastgelegde verwachting; de nadien gelezen bron onderbouwt die, zonder aanpassing aan uitkomsten.
- **Onbepaald/ingesloten:** `iedereen` duidt een bereik aan; `wie/wat` kan een ingesloten antecedent hebben (S9). Geen verplicht eerder naamwoord verzinnen. Andere regels mogen de inhoud nog afkeuren (E11).
- **Begrip zelf:** `persoon die …` verwijst naar het genus, niet naar een cirkeldefinitie. Alleen `deze` gebruiken omdat het lemma zichtbaar staat, is onder N-B1 onvoldoende. Wie lemma plus kern als één leesobject kiest, kiest een andere scope en een ander transport-/exportcontract (E09).

Dezelfde norm geldt bij genereren, uitsluitend toetsen, import en bewerken. Toetsing bewaart originele invoer. Review, conceptopslag, vaststelling en export zetten een open oordeel niet om in pass. Bij gewijzigde tekst of relevante bewijsgrond hoort herbeoordeling; context-/bronwissel kan herstelbedoeling ongeldig maken.

## Q2 — noodzakelijke informatie en veldmatrix

Noodzakelijk voor de leestoets: exacte definitietekst, versie en vastgestelde scope. Voor betekenisbehoud bij herstel: bedoelde referent en relevante onderbouwing. Context, bronnen en ontologie zijn ondersteunend en soms noodzakelijk voor herstel, niet voor ieder eenvoudig INT-03-oordeel. Huidige signalering gebruikt alleen tekst. De matrix is een voorstel, geen claim van huidige velddekking.

| Veld | Zelf toetsobject | Bewijs voor ander oordeel | Generatie-invoer | Mag AI opleveren/wijzigen? | Ontbrekend/conflict en herkomst |
|---|---|---|---|---|---|
| Definitiezin | Primaire INT-03-kern | Passages/kandidaten | Bij toets/herstel verplicht; bij generatie te produceren | Nieuwe kandidaat, origineel behouden | Leeg: niet beoordeeld. Tekstversie/hash binden. |
| Context | Niet aan kern plakken; eigen proza apart bekijken | Doelgroep/bedoeling, geen reparatie antecedent | Alleen bevestigde selectie | Geen context verzinnen/stil wijzigen | Alleen noodzakelijke betekenisgrond uitvragen; geen generieke fail. |
| Definitiebronnen | Citaat niet automatisch herschrijven | Actor/bezit/bereik/beperkingen | Werkelijk aangeleverde passende passages | Parafrase als voorstel, geen bron verzinnen | Bron niet universeel verplicht; conflict apart onder CON-02. |
| Ontologie/relaties | Los label geen INT-03-object | Rollen/plausibiliteit, geen grammaticaal bewijs | Ondersteunend, bevestigd | Voorstel, geen waarheid fabriceren | Conflict naar domeindeskundige. |
| Voorbeelden | Eigen tekst afzonderlijk | Illustreren bedoelde lezing | Ondersteunend | Synthetisch met label | Geen onafhankelijke bevestiging door eigen modelvoorbeeld. |
| Praktijkvoorbeelden | Eigen verhaal/context | Betrouwbare herkomst kan rollen staven | Alleen geautoriseerde feiten; hier synthetisch | Geen praktijkfeiten verzinnen | Herkomst/fictie gescheiden. |
| Tegenvoorbeelden | Afzonderlijk; opzettelijke fout benoemen | Alternatieve lezing tonen | Ondersteunend | Ja, synthetisch gelabeld | Fout niet overnemen als bedoelde betekenis. |
| Grensgevallen | Afzonderlijk; twijfel zichtbaar | Plausibiliteit versus eenduidigheid | Ondersteunend | Gelabeld voorstel | Onbeslist niet naar pass dwingen. |
| Synoniemen | Termlabel doorgaans geen zinsverwijzingstoets | Ander label, geen automatisch antecedent | Onderbouwde synoniemen | Voorstel met herkomst | Synoniem bewijst niet dezelfde referent in elke context. |
| Homoniemen | Los label geen INT-03-oordeel | Mogelijke betekenisconcurrentie | Ondersteunend | Onderscheid voorstellen, niet gokken | Conflict eerst verduidelijken. |
| Toelichting | Eigen samenhang; mag over zinnen verwijzen | Bevestigde bedoeling/herstelgrond | Apart van kern | Voorstel; geen menselijke bevestiging simuleren | Repareert geen ambigue kern; actor/datum/bron vastleggen. |

Bij E13 kunnen twee dingen tegelijk waar zijn: de kern is aantoonbaar dubbelzinnig en de bedoelde actor ontbreekt als herstelgrond. Dat is een overtreding plus een informatievraag. Is juist de taalkundige beoordeling onvoldoende zeker, dan blijft het oordeel open. Bij E15 kan de verwijzing duidelijk zijn terwijl het bronconflict elders ligt.

## Q3 — relaties en eigenaarschap

| Relatie | Grond | Gevolg |
|---|---|---|
| INT-01 | Record heeft onder meer die/waarbij; actuele proef keurt E01/E02 beide onder INT-01 af | Correcte INT-03-verwijzing kan elders worden afgestraft. Concrete implementatiewrijving, geen noodzakelijk normconflict. DEF-770/regelcoördinatie beoordeelt dit. |
| ARAI-05 / INT-10 | Zelfstandige begrijpelijkheid overlapt; huidige ARAI-05 keurt E03/E04/E07 niet af | Buurregel is geen bewezen vangnet. Een bronnaam toevoegen kan nieuwe impliciete kennis eisen. |
| INT-04 | In deze afspraak is het zelfstandig naamwoord aanwezig, maar de identificatie kan ontbreken | Overlap expliciet maken, geen dubbele inhoudelijke straf. |
| CON-CIRC-001 | Record verbiedt letterlijk lemma in kern; E03/E04 bevatten het lemma al en falen daarom | Dit is geen door INT-03 veroorzaakte fail en geen gemeten herstelregressie. Risico van nieuwe lemmaherhaling apart beoordelen; herformuleer of leg conflict voor. |
| CON-02 | Bron kan referent staven terwijl de kern ambigue blijft | Brongezag geeft geen INT-03-pass; bronconflict bij herstel apart benoemen. |
| ESS-05 / SAM-05 | Actor/bezit/bereik veranderen kan begripsgrens of cirkelrelatie raken | Herstel is niet louter stijl; geraakte regels hertoetsen. Geen buurregelbesluiten overnemen. |

Chris beslist normscope, automatisering en productbeleid. A bewaakt DEF-772 en verwerkt verschillen. DEF-625 draagt normherkomst; DEF-624 resultaatcontract; DEF-626 snapshots; DEF-630 vaststellen/export; DEF-638 herstel. Het expliciete appbesluit van 15 september is **geen totaalscore als kwaliteitscijfer of herstelsturing**. Oudere formuleringen “voorlopig” in DEF-624/skills draaien dat besluit niet terug (S8).

DEF-630 vereist in zijn geplande acceptatiecontract versioned menselijke beoordeling van verplichte reviewuitkomsten. Dat is geen bewezen actuele INT-03-poort. Dit voorstel introduceert geen losse INT-03-poort en neemt de specifieke poortvrijstelling van ESS-03 niet over. DEF-638 heeft maximaal één herstelcall als gepland vervolg; dat is geen actieve INT-03-herstelroute.

## Q4 — appgedrag, proeven en ketengrenzen

### Actuele serviceproef

[Script](proef-b-v1.py), [vooraf opgeslagen verwachtingen](proefverwachtingen-b-v1.json), [uitkomsten met commando/runtime/exitstatus](proefuitkomsten-b-v1.json). Mac `.venv/bin/python -B`, bootstrap vóór applicatie-imports; netwerk, echte sleutels, impliciete dotenv en gebruikersdatabases afgeschermd. Bootstrap rapporteert nul reeds geïmporteerde applicatiemodules. Tijdelijke runtime onder `/private/tmp`; blijvende uitvoer in deze map. Geen modelresponsstubs, live calls, productiegegevens of brede testsuite. Cleaning-service en repository zijn `None`.

**Waarneming B-W1:** acht gevallen × manager/cache = zestien uitkomsten, exitstatus 0, alle runtimeverwachtingen uitgekomen. Alle INT-03-statussen zijn review_required, zonder INT-03-violation/pass. Dit bewijst contractgedrag, geen inhoudelijke kwaliteit. Twee macOS/Xcode cache-/filesystemwaarschuwingen staan volledig in stderr; uitvoering voltooide succesvol.

Alle zestien redenen zijn letterlijk:

> Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?

| Casus | Variant | Signalen |
|---|---|---|
| INT03-B-E01 | ASTRA JUIST(ER) | `\bdie\b` en P-extra |
| INT03-B-E02 | ASTRA ONJUIST | `\bdie\b` en P-extra |
| INT03-B-E03 | regeling waarbij deze afspraak geldt | `\bdeze\b`, `\bwaarbij\b`, P-extra |
| INT03-B-E04 | instrument voor een besluit nadat het is vastgesteld | Leeg |
| INT03-B-E05 | veelhoek met drie zijden | Leeg |
| INT03-B-E06 | teken dat een richting aangeeft | Leeg |
| INT03-B-E07 | bericht … over zijn besluit | Leeg |
| INT03-B-E14 | Lege tekst | Leeg |

P-extra is exact `\b(deze|dit|die|daarvan)\b(?!\s+(begrip|definitie|regel))`. Het zijn patroonstrings, geen passages, posities of kandidaatreferenten. Het ASTRA-paar geeft gelijke signalen doordat beide die bevatten; het onderscheidende het ontbreekt in de lijst. De extra negatieve lookahead geeft geen algemene uitzondering voor deze/die + begrip/definitie/regel: afzonderlijke JSON-patronen blijven bestaan.

**Afbakening buurregelbewijs (RB-05):** E03 is de letterlijk gevraagde runtimefixture en E04 is een synthetische het-zin. De lemmawoorden regeling/instrument staan al in de invoer. De gemeten CON-CIRC-fails bewijzen de reactie op die invoer, niet dat een INT-03-fout of herstel die buurregel heeft veroorzaakt. Beide blijven ongewijzigd geldig voor INT-03-status/reden/signalen. Voor een toekomstige geïsoleerde herstelvergelijking zijn afzonderlijke gevallen zonder vooraf bestaande lemma-fail nodig, met nieuwe IDs en vooraf vastgelegde verwachtingen; zulke nieuwe proeven zijn nu niet uitgevoerd. A/DEF-624 kan de fixturefunctie expliciet documenteren zonder de historische fixture te vervangen.

**Statisch S4:** JudgmentReviewEvaluator heeft geen INT-03-tak; alleen ESS-01/02/04 hebben passagehulp. De normaal afgeronde INT-03-evaluator geeft altijd review. De service vangt evaluator-/contractfouten afzonderlijk als error af (modular_validation_service.py:1430–1483); de gemeten normale rijen zijn geen technische-foutproef. Signalen worden over cleaned_text verzameld. De service verklaart definition_text beschikbaar zonder niet-leegtest: E14 blijft INT-03-review, terwijl VAL-EMP-001 faalt. Dit bewijst geen toegestane vaststelling van lege invoer.

### Promptproef

**Waarneming B-W2:** de echte door de adapter geregistreerde JSONBasedRulesModule rendert in drie contexten hetzelfde blok. De volledige ModularPromptAdapter bevat het met juridische context, niet zonder context of bij alleen organisatorische context. Exacte module-/adapterblokken en volledige-prompt-hashes zijn bewaard. include_examples=True, compact_mode=False; andere instellingen niet uitgevoerd. Statisch activeert `prompt_orchestrator.py:467–469` ook bij wettelijke context. De historische 7-septemberclaim blijft voor deze actuele varianten bevestigd.

Exact moduleblok:

```text
🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**
- Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt.
- **Instructie:** Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin
  ✅ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd.
  ❌ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd.
```

**Statisch S5:** _format_rule rendert uitleg, instruction_map en voorbeelden, geen toelichting/toetsvraag. Alleen JSON-toelichting wijzigen verandert de live generatie-instructie niet. IntegrityRulesModule._build_int03_rule bevat een hardcoded variant en aanvullende voorbeelden, maar de adapter registreert die klasse niet. Gerichte src-zoekactie vindt klassedefinitie/export, geen instantiërende productiecaller. Beide legacy INT03Validator-bestanden zijn identiek; een dynamische loader bestaat, maar heeft buiten zichzelf geen gevonden src-consument. Zijn regex-fail/letterlijk-goed-voorbeeld-uitzondering en hints zijn geen actuele servicebeoordeling. Dit sluit externe/dynamische consumenten buiten src niet uit.

| Ingang/grens | Bewijs | Ontbreekt |
|---|---|---|
| Genereren | Module- en volledige adapterprompt, drie contexten | Modeluitvoer, naleving, nabewerking, volledige opslagroute. |
| Uitsluitend toetsen | Service manager/cache, synthetische tekst zonder cleaning | Schermroute en transport/cleaning vóór service. |
| Import/bewerken | Zelfde norm vereist; geen ingangproef | Exact transport en invalidatie oud oordeel. |
| Review/UI | Statisch validation_view.py:237–263,803–808,859–864: INT-03 als open regelcode; geen INT-03-reden en geen uitleg-expander in deze route | Geen live UI-test of INT-03-antecedentkeuze. Niet bewezen dat iedere mogelijke opslag of andere weergaveroute afwezig is. |
| Conceptopslag/herladen | Open snapshotcontract DEF-626 | Geen save→reload van INT-03-besluit/signalen; generiek reviewveld bewijst dat niet. |
| Vaststellen/export | DEF-630 bepaalt gedeeld contract; exportcode heeft labels voor bestaande specifieke uitvoer | Geen actuele INT-03-poort/exportclaim; een statuslabel bewijst geen INT-03-exportonderbouwing. |
| Hertoetsen | Verse service-uitkomsten | Geen duurzame historie, invalidatie of herstelketen getest. |

## Q5 — exacte vervangteksten en opties

Alles hieronder is voorstel, nergens toegepast. Vindplaatsen gelden op de leesbasis. Pakket samen beoordelen: meer signaalwoorden alleen lossen antecedentbeoordeling niet op.

### N/G — JSON en live generatie-instructie

**src/toetsregels/regels/INT-03.json — uitleg:**

> Maak in de definitiekern eenduidig duidelijk waarnaar ieder verwijzend voornaamwoord verwijst. Duidelijke voornaamwoorden en betrekkelijke bijzinnen zijn toegestaan.

**Zelfde JSON — toelichting**, ter vervanging van dezelfde zin/zinsdeel en verplicht zelfstandig naamwoord:

> Beoordeel de verwijzende functie in de volledige definitiekern. De bedoelde persoon, zaak, gebeurtenis of andere betekenis moet daarin eenduidig herkenbaar zijn. Een antecedent kan een naamwoordgroep of een grotere tekstinhoud zijn; een duidelijke vooruitverwijzing of ingesloten antecedent is niet op zichzelf fout. Een lidwoord, niet-verwijzend gebruik van 'het' of onbepaalde aanduiding vraagt geen verzonnen antecedent. Externe context, een los lemma of een toelichting mag een ontbrekende verwijzing in de kern niet vervangen. Meerdere naamwoorden bewijzen nog geen ambiguïteit: motiveer welke lezingen werkelijk plausibel zijn. De signaalpatronen zijn onvolledige zoekhulp, geen afkeurgronden.

**Zelfde JSON — toetsvraag:**

> Is voor ieder verwijzend voornaamwoord in de definitiekern eenduidig vast te stellen wat bedoeld wordt? Benoem de passage, de plausibele kandidaat-antecedenten en de grond voor het oordeel; onderscheid onduidelijkheid van een ontbrekende beoordeling of ontbrekende herstelgrond.

**JSON-voorbeelden:** behoud het volledige ASTRA-paar letterlijk met herkomst. Voeg als exacte goede teksten toe `teken dat een richting aangeeft` en `periode waarin het regent`; als foute teksten `instrument voor een besluit nadat het is vastgesteld` en `bericht van een medewerker aan een leidinggevende over zijn besluit`. Bijbehorende uitleghulp noemt instrument/besluit respectievelijk medewerker/leidinggevende als kandidaten. De huidige voorbeeldenvelden dragen die uitleg niet. E08 blijft grensgeval in reviewerhulp, geen onvoorwaardelijk goed/fout voorbeeld. Toevoegingen zijn synthetische projectvoorbeelden, geen ASTRA-citaten.

**G-B1: exacte vervanging instruction_map INT-03 in src/services/prompts/modules/json_based_rules_module.py:378:**

> Maak iedere verwijzing in de definitiekern eenduidig, ook bij 'het' en bezit. Duidelijke die/dat-bijzinnen en vooruitverwijzingen zijn toegestaan; niet-verwijzend gebruik vraagt geen antecedent. Herhaal bij dubbelzinnigheid de bevestigde referent of herformuleer, met behoud van actor, rol, bezit en bereik. Vul ontbrekende bedoeling niet zelf in. Losse context, lemma of toelichting vervangt geen ontbrekende verwijzing in de kern.

Huidige passage: zie exact blok Q4; zij eist dezelfde zin en noemt slechts drie vormen. G-B1 is in v2 verkort en verbreedt functies en herstelgrenzen. De langere uitleg staat hieronder in het skillcontract. Te toetsen met E01/E06/E07/E08/E10/E12/E17; de korte tekst heeft nog geen gemeten generatie-effect.

**G-B2 — uitvoerroute bij onbekende betekenis (RB-07):** de instruction_map-instructie is een definitie-instructie, geen nieuw interactieprotocol. Een vraag mag niet in het definitieveld belanden. Bij ontbrekende bedoeling moet een afzonderlijk ondersteunde route de informatievraag/open grond tonen en bevestiging verkrijgen vóór gericht herstel. Dit kan menselijk of later via T-AI; het is niet uitsluitend een T2-vraag. Zonder aantoonbare route geen claim dat een promptzin veilig een interactieve vraag implementeert en geen referent verzinnen om toch een afgeronde definitie te produceren. Het ontwerp moet bepalen hoe onvolledige generatie zichtbaar terugkeert; een generieke appvraagroute is hier niet volledig onderzocht.

**Ook promptselectie aanpassen is nodig:** voorkeur INT-03 afzonderlijk contextvrij meenemen; de gehele INT-module activeren raakt andere regels. A kiest eveneens smal; C kiest breed. C’s circa 10.000 tekens verschil verandert tevens context/SAM en bewijst niet de geïsoleerde meerlengte. JSONBasedRulesModule filtert generiek op prefix; een smalle route is niet bewezen strijdig met de modulestructuur. Technisch ontwerp, exacte meerlengte en doorwerking volgen bij afzonderlijke uitvoering. Geen dependency gekozen.

### G — skillvervangingen

Huidige `~/.agents/skills/definitie-toetsregels/reference.md:64` zegt: Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent. Exacte vervangende rij:

```text
| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Maak iedere verwijzing in de definitiekern eenduidig. Behoud duidelijke die/dat-bijzinnen; controleer ook bezit en andere verwijsvormen. Herhaal de bedoelde referent of herformuleer alleen met behoud van betekenis; vraag ontbrekende bedoeling uit. Aanwezigheid of afwezigheid van een signaalwoord is geen inhoudelijk oordeel. |
```

Huidige `~/.agents/skills/definitie-nederlandse-definities/reference.md:185`: Impliciete verwijzingen: deze, dit, die, dat zonder duidelijk antecedent. Exacte vervangende bullet:

> - Onduidelijke verwijzingen: maak in de definitiekern helder wat ieder verwijzend voornaamwoord bedoelt, ook bij bezit en vooruitverwijzing. Duidelijke 'die/dat'-bijzinnen zijn toegestaan; niet-verwijzend 'het' vraagt geen antecedent. Herhaal alleen de bevestigde referent of herformuleer met behoud van betekenis. Verzin geen bedoeling en gebruik losse context of toelichting niet als vervanging van een ontbrekende verwijzing.

De bestaande positieve passage over betrekkelijke bijzinnen behouden. Beide SKILL.md-bestanden hebben geen INT-03-contractsectie. **Volledig te publiceren skillblok (RB-12)**, als nieuwe sectie in beide SKILL.md-bestanden; onderstaande tekst bevat G/T/H zelf en vereist geen verwijzing naar dit onderzoek:

```text
INT-03 — duidelijke verwijzingen

Genereren: Maak bij ieder verwijzend voornaamwoord in de definitiekern eenduidig wat bedoeld wordt. Gebruik gerust duidelijke betrekkelijke bijzinnen met 'die' of 'dat'; ook bezittelijke verwijzingen en verwijzingen met 'het', 'dit' of 'deze' moeten helder zijn. Beoordeel de hele kern: een duidelijke vooruitverwijzing is toegestaan en niet-verwijzend gebruik vraagt geen antecedent. Bij mogelijke dubbelzinnigheid benoem je de bedoelde referent opnieuw of herformuleer je de zin, zonder actor, rol, bezit, bereik of andere betekeniskenmerken te veranderen. Gebruik alleen aangeleverde betekenisgrond; vraag bij ontbrekende of strijdige bedoeling om verduidelijking in plaats van zelf een referent te kiezen. Houd context, bronadministratie en toelichting buiten de definitiekern; zij repareren geen ontbrekende verwijzing.

Toetsen: Toets de exacte aangeboden definitiekern en leg de tekst- en normversie vast. Bepaal eerst welke woorden werkelijk een verwijzende functie hebben; behandel lidwoorden en loos 'het' niet als ontbrekend antecedent. Benoem per relevante verwijzing de letterlijke passage, de plausibele kandidaten in de kern en de grond voor de gekozen lezing of twijfel. Nabijheid, woordgeslacht, ontologische plausibiliteit of een patroonhit alleen is geen bewijs. Gebruik bevestigde context en bronpassages om de bedoeling te begrijpen, maar laat die een onduidelijke kern niet stil repareren. Geef 'voldoet' als de verwijzingen duidelijk zijn, of na inhoudelijke controle geen verwijzende voornaamwoorden aanwezig zijn. Geef 'voldoet niet' bij aantoonbare ontbrekende of dubbelzinnige verwijzing. Geef 'beoordeling nodig' als de semantische beoordeling niet verantwoord kan worden afgerond en benoem precies welke vraag openstaat. Geef bij ontbrekende definitietekst 'niet beoordeeld'; een technische mislukking krijgt een afzonderlijke fout zonder inhoudelijk oordeel. Verander bij uitsluitend toetsen niets. Een herstelvoorstel staat apart en mag alleen de bevestigde bedoeling volgen.

Terugkoppeling/herstel: Stel eerst vast of het probleem in de kandidaat, de instructie, het invoertransport, de beoordelaar, de bewijsgrond of de techniek zit. Een open beoordeling of patroontreffer is geen herstelopdracht. Herstel uitsluitend een bevestigde onduidelijke verwijzing waarvan de bedoelde referent uit aangeleverde of expliciet bevestigde informatie blijkt. Geef maximaal één gerichte nieuwe kandidaat per generatie als de herstelroute afzonderlijk is geautoriseerd. Herhaal de referent of herformuleer de zin; behoud actor, rol, bezit, reikwijdte, bronbeperkingen en recordidentiteit. Bewaar origineel, voorstel en verschil. Stop bij ontbrekende bedoeling, bronconflict, herhaling van dezelfde fout, betekenisverlies, technische fout of conflict met andere regels. Toets de werkelijk bewaarde nieuwe kandidaat opnieuw op INT-03 en geraakte regels; hergebruik geen oud oordeel als actuele goedkeuring. Toon bij stoppen de oorspronkelijke kandidaat, open grond en benodigde vervolgstap.

Status en uitvoer: een signaal is geen afkeuring en geen signaal is geen goedkeuring. Een vraag staat buiten de definitiekern en vereist een ondersteunde interactieroute. Geef alleen advies over de exacte aangeleverde versie; dit is geen opgeslagen menselijke beoordeling, vaststelling of exportgoedkeuring. Ontbrekende informatie, open oordeel en technische fout blijven onderscheiden. Kies geen totaalscore en neem geen regelspecifieke vaststelvrijstelling over van een andere regel.
```

Dit is publicatietekst als voorstel, geen toegepaste skillwijziging. Beheerde bron in ~/Projecten/_claude-global-setup/skills en werkelijk gebruikte kopieën gecontroleerd publiceren na het besluit. De generieke score-/blokkadeclaims in de toetsregelskill onder DEF-624 synchroniseren, zonder nieuwe score aan INT-03 toe te voegen.

### T-B1 — toetsinstructie en meldingen

Voorgestelde vindplaats: gedeelde INT-03-contractsectie in toetsregelskill; bij AI-optie dezelfde norm in afzonderlijk geversioneerd evaluatorpromptcontract. Bij menselijke optie blijft judgment_review signaalhulp, geen semantische beoordelaar.

> Toets de exacte aangeboden definitiekern en leg de tekst- en normversie vast. Bepaal eerst welke woorden werkelijk een verwijzende functie hebben; behandel lidwoorden en loos 'het' niet als ontbrekend antecedent. Benoem per relevante verwijzing de letterlijke passage, de plausibele kandidaten in de kern en de grond voor de gekozen lezing of twijfel. Nabijheid, woordgeslacht, ontologische plausibiliteit of een patroonhit alleen is geen bewijs. Gebruik bevestigde context en bronpassages om de bedoeling te begrijpen, maar laat die een onduidelijke kern niet stil repareren. Geef 'voldoet' als de verwijzingen duidelijk zijn, of na inhoudelijke controle geen verwijzende voornaamwoorden aanwezig zijn. Geef 'voldoet niet' bij aantoonbare ontbrekende of dubbelzinnige verwijzing. Geef 'beoordeling nodig' als de semantische beoordeling niet verantwoord kan worden afgerond en benoem precies welke vraag openstaat. Geef bij ontbrekende definitietekst 'niet beoordeeld'; een technische mislukking krijgt een afzonderlijke fout zonder inhoudelijk oordeel. Verander bij uitsluitend toetsen niets. Een herstelvoorstel staat apart en mag alleen de bevestigde bedoeling volgen.

| Uitkomst | Exact voorstel melding | Contract |
|---|---|---|
| Voldoet | INT-03 — Voldoet. 'dat' verwijst hier naar 'teken'; er is geen andere plausibele lezing. | pass na inhoudelijk oordeel; voorstel geen INT-03-cijfer. |
| Overtreding | INT-03 — Voldoet niet. In 'nadat het is vastgesteld' kan 'het' verwijzen naar 'instrument' of 'besluit'. Maak de bedoelde referent expliciet. | fail; kandidaten inhoudelijk beoordeeld, niet door regex bewezen. |
| Overtreding + ontbrekende herstelgrond | INT-03 — Voldoet niet. 'zijn besluit' laat de medewerker en de leidinggevende als bezitter toe. Van wie is het besluit? Zonder die keuze volgt geen herstelvoorstel. | Fout én informatievraag behouden. |
| Beoordeling nodig | INT-03 — Nog te beoordelen. Beoordeel of 'deze' in deze zin eenduidig vooruitwijst naar 'aanvraag'; 'handeling' is ook een te onderzoeken kandidaat. | review_required; herkenbaar open oordeel. |
| Toetsobject ontbreekt | INT-03 — Niet beoordeeld: definitietekst ontbreekt. | not_evaluated; geen inhoudelijk fail. |
| Betekenisgrond ontbreekt | INT-03 — Beoordeling nodig: de bedoelde betekenis is onvoldoende onderbouwd. [gerichte vraag] | review_required met subreden; niet elke bron is verplicht. |
| Technische fout | INT-03 — Beoordeling technisch mislukt. Er is geen inhoudelijk oordeel; probeer de beoordeling later opnieuw. | error; interne details alleen diagnostiek. |
| Alleen signaalhulp | INT-03 — Nog te beoordelen. Gevonden passage: 'die'. Bepaal de verwijzing in de volledige zin. Dit signaal bewijst geen onduidelijkheid. | Zonder hit: Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig. |

Voorgesteld bewijscontract: regel/normversie, exacte teksthash, gebruikte context/bronbinding, passage met offsets, taalfunctie, kandidaten met argumenten, gekozen referent of onbekendheid, uitkomst/reden/subtype, beoordelaar of model/promptversie/tijdstip, afzonderlijke menselijke correctie. Bestaand ReviewRequirement heeft alleen rule_id/category/reason/signals. Uitbreiding afstemmen met DEF-624/626/627; geen schemawijziging uitgevoerd.

**Zichtbare reviewroute (RB-11/14/16):** de verbeterde reden moet in de onderzochte UI-route voor INT-03 daadwerkelijk zichtbaar worden, inclusief open status, letterlijke passage, vraag en beperking. Alleen de evaluatorreden vullen is onvoldoende. De huidige passagehelper dedupliceert identieke fragmenten; per-voorkomenanalyse met offsets is dus extra ontwerpwerk, geen vanzelfsprekend ESS-04-hergebruik. Kandidaat-antecedenten komen pas uit menselijke analyse of herkenbaar te beoordelen modelvoorstel. Leg het uiteindelijke oordeel en de onderbouwing op de beoordeelde versie vast via het gedeelde reviewcontract; wijziging van tekst of relevante betekenisgrond maakt dat oordeel niet stil actueel. Verifieer save/reload, edit/hertoets en weergave. Een generiek expertbesluit of snapshot bewijst deze binding niet. Geen wereldwijde afwezigheid van opslag geclaimd: deze doorloop ontbreekt als bewijs.

Drie opties:

1. **Menselijk oordeel zoals nu:** kleinste ingreep; alle gevallen review, weinig hulp. Tussenstand zonder effectclaim.
2. **Verbeterde signaalhulp met menselijk oordeel — voorkeur B als eerste stap:** passages/posities, taalfuncties in instructie, gerichte vragen, opgeslagen oordeel. Het/dat/bezit toevoegen als zoekhulp vergroot mogelijk dekking én ruis. Inzienelijk maken en in het kader hebben zonder onderbouwing geen INT-03-signaalgrond. Kandidaat-antecedenten komen van reviewer of expliciet modelvoorstel, niet van een als betrouwbaar gepresenteerde regexresolver. Gebruikersproef nodig.
3. **AI-beoordeling zoals afzonderlijk besloten voor ESS-03/CON-02:** kan inhoudelijk onderscheid voorstellen, ook zonder patroonhit. Vereist Chris-besluit over versiegebonden invoer/prompt/model, referentiegevallen, twijfel/fouten, kosten/privacy en correctiepad. Geen live beoordeling uitgevoerd; hun interface of kwaliteit bewijst geen INT-03-effect. Beoordeel de hele kern. Integrale expertbeoordeling en handmatige vaststelling blijven apart.

### H-B1 — begrensde terugkoppeling

Exact voorgestelde tekst voor gedeeld contract en latere gerichte herstelinput:

> Stel eerst vast of het probleem in de kandidaat, de instructie, het invoertransport, de beoordelaar, de bewijsgrond of de techniek zit. Een open beoordeling of patroontreffer is geen herstelopdracht. Herstel uitsluitend een bevestigde onduidelijke verwijzing waarvan de bedoelde referent uit aangeleverde of expliciet bevestigde informatie blijkt. Geef maximaal één gerichte nieuwe kandidaat per generatie als de herstelroute afzonderlijk is geautoriseerd. Herhaal de referent of herformuleer de zin; behoud actor, rol, bezit, reikwijdte, bronbeperkingen en recordidentiteit. Bewaar origineel, voorstel en verschil. Stop bij ontbrekende bedoeling, bronconflict, herhaling van dezelfde fout, betekenisverlies, technische fout of conflict met andere regels. Toets de werkelijk bewaarde nieuwe kandidaat opnieuw op INT-03 en geraakte regels; hergebruik geen oud oordeel als actuele goedkeuring. Toon bij stoppen de oorspronkelijke kandidaat, open grond en benodigde vervolgstap.

E02: het → die gebeurtenis is onderbouwd door het ASTRA-paar. E04: het → het besluit kan bij bevestigde bedoeling. E07/E13: geen actor gokken. E09: waar mogelijk genus-herformulering, geen mechanische lemmaherhaling. E17: bezit blijft bij aanvrager. E16: foutieve evaluator corrigeren, goede tekst behouden. INT-01/ARAI-05/CON-CIRC-001-conflicten zichtbaar houden en bij eigenaren beoordelen. Dit sluit aan op gepland DEF-638 en activeert geen herstelcall. Bij onbekende doorwerking alle toepasselijke controles opnieuw uitvoeren; bij succes blijft het een nieuwe kandidaat tot de vereiste beoordeling/vaststelling is doorlopen.

## Q6 — effectevaluatie, besluiten en overdracht

### Vooraf vastgelegde vergelijking

Het [casusregister](casusregister-b-v1.md) en de verwachtingen zijn vóór uitvoering opgeslagen: achttien stabiele INT03-B-E-IDs, historische labels/P/N/G niet hernummerd. De proef is een nulmeting van huidige routes. Geen nieuwe appvariant en geen echte generatie-/herstel-/gebruikersmeting.

| Aanbeveling | Gewenste winst | Vergelijking/behoud | Stand |
|---|---|---|---|
| Norm + G-B1 + contextvrij bereik | Minder ambigue/ontbrekende referenten | Zelfde betekenis/bronnen, oud/nieuw promptpakket, gelijk model/instellingen; E01/E06/E10/E11 behouden; actor/bezit/bereik gelijk | Oude prompt gemeten; aanwezigheid is geen naleving. |
| T-B1 en signaalhulp | Betere onderbouwde menselijke oordelen | Zelfde gevallen, oude/nieuwe hulp, gebalanceerde volgorde; juiste passages/kandidaten; minder gemiste fouten zonder meer foutieve afkeur | Alleen servicebaseline; gebruikersproef ontbreekt. |
| AI-optie | Inhoudelijk oordeel waar nu alleen review staat | Bevroren referentieoordelen; juiste/onjuiste/open/fout apart; volledige kern beoordelen | Nieuwe variant/autorisatie ontbreekt; minder review is geen kwaliteitsbewijs. |
| H-B1 | Verduidelijking zonder betekenisverlies | Origineel/voorstel gepaard, onafhankelijke controle rol/bezit/bereik/bronbeperkingen; één poging en stop | Ontwerp; betekenisverlies is afkeurgrond. |
| Resultaatbinding | Geen oud oordeel voor nieuwe kandidaat | Save/reload, edit/hertoets, review/vaststellen/export; E14/E18 nooit pass | Naar DEF-624/626/630; geen ketenbewijs. |

Klein vervolgontwerp: achttien ontwerpgevallen plus minimaal zes nieuwe, door onafhankelijke deskundige vóór evaluatie vastgelegde en voor ontwerp afgeschermde gevallen. Reeds in A/B/C besproken gevallen zijn na deze review geen ongeziene controlegroep. De oorspronkelijke B-verwachtingen blijven bevroren; voor nieuwe varianten/gevallen komen vooraf aparte verwachtingen. De korte G-B1-v2, lange skilltekst en transportkeuze zijn afzonderlijk te identificeren onderdelen; zet geen ongedefinieerd mengpakket tegenover de nulmeting. Leg voor alle 24 betekenis/toegestane varianten vast. Voor G: per bruikbare generatiebrief drie herhaalde runs per oude/nieuwe variant, hetzelfde model/instellingen. Technische foutgevallen zijn contractproeven, geen gewone generatieopdrachten. A moet de precieze generatiebrief vooraf bevriezen; de huidige kernteksten zijn nog geen volledige brief. T beoordeelt vaste kernen én motivering, H de herstelbare én stopgevallen. De zes aanvullende gevallen worden niet achteraf gebruikt om verwachtingen passend te maken.

Voor menselijke passagehulp blijven de ruwe service-uitkomsten review zolang geen mens oordeelt: winst is betere menselijke beoordeling/onderbouwing, niet automatisch minder review. Neem zowel fouten als duidelijke die/dat, loos het, geen voornaamwoorden en irrelevante signalen op. Meet ook onterechte afkeur, onnodig herstel en beoordelingstijd. Voor herstel en buurregelbehoud scheid vooraf bestaande fails (E03/E04) van nieuw veroorzaakte fails; nieuwe geïsoleerde gevallen vereisen eigen IDs en bevroren bedoeling.

Blind beoordelen waar mogelijk, door taalkundig/domeindeskundige; tweede oordeel bij betwiste betekenis. Gewijzigde evaluator nooit als enige maatstaf. Rapporteer per geval verbeterd/gelijk/verslechterd/onbeslist. Geen algemeen kwaliteitspercentage. Minimale voorgestelde acceptatie: ASTRA-paar juist onderscheiden bij inhoudelijk oordeel; geen afkeur alleen door die/dat of loos het; geen pass bij lege invoer/technische fout; E04/E07 niet overslaan wegens lege signalen; geen betekenisverlies in geaccepteerd herstel. Winst vereist daadwerkelijk betere juiste uitkomsten én behoud van goede gevallen. Kleine synthetische selectie is geen gevalideerde juridische goldset of statistisch bewijs voor alle definities.

### Concrete besluiten voor Chris

| Besluit | Voorkeur B | Alternatief/gevolg | Gevallen |
|---|---|---|---|
| D1 Normscope | Eenduidigheid in kern; lokale zin/zinsdeel-/los-naamwoordeis vervangen; lemma geen verborgen antecedent | Strikte formulering: meer uitzonderingen nodig. Lemma/context meetellen: ander leesobject/transportcontract | E06/E08/E09/E10/E11 |
| D2 Generatiebereik | INT-03 contextvrij, niet automatisch alle INT-regels toevoegen | Huidige selectie laat de instructie weg in twee gemeten varianten | Drie promptvarianten |
| D3 Oordeel | Eerst menselijke passagehulp/vastlegging, AI na specifiek besluit en effectproef | Niets wijzigen: weinig hulp. Direct AI-traject: meer automatisering, nog onbewezen kwaliteit en extra fout-/kosten-/correctiekeuzes | E01/E02/E04/E07/E16 |
| D4 Geen verwijzende woorden | Na inhoudelijke controle voldoet; lege regexlijst blijft review | Niet van toepassing kan ook na controle, maar vraagt expliciete dekkingssemantiek | E05 versus E04/E07 |
| D5 Herstel | Bevestigde referent, diff, maximaal één poging binnen latere DEF-638-route | Alleen handmatig blijft mogelijk; dichtstbijzijnde naamwoord automatisch kiezen afwijzen | E02/E07/E09/E13/E17 |
| D6 Velden/poorten | Kern centraal, aanvullingen apart; gedeelde vaststel-/snapshotbesluiten volgen | Velden samenvoegen of eigen poort toevoegen wijzigt beleid/bewijslast | E12/E14/E15/E18 |

Dit zijn besluitvoorstellen, geen uitvoeringsakkoord. Bronherkomst en geen schijnpass volgen bestaand beleid; normprecisering, AI-keuze, nul-voornaamwoordstatus en herstelactivatie vragen expliciete keuzes.

### Ontbrekend bewijs en volgende actie

| Ontbreekt | Eigenaar en actie | Afhankelijkheid/moment |
|---|---|---|
| Kruisreview/synthese | B heeft A en C gereviewd en A’s review verwerkt; A verwerkt eigen correcties, ontvangt C-verwerking en stelt synthese op | Dit fase-2-pakket gaat naar A. Synthesecontrole volgt op overdracht; niet reeds uitgevoerd. |
| DBT §4.3 | A/DEF-625 organiseert leesbare PDF/sectie en gerichte normcontrole | Vóór claim over volledige Ross-norm; ASTRA-analyse blijft afzonderlijk bruikbaar. |
| Norm-/productkeuze | Chris kiest D1–D6 na synthese | Vóór implementatiebrief; geen nieuwe issues nodig. |
| Referentieoordelen/holdout | A wijst deskundige aan; bevries verwachtingen en zes nieuwe gevallen | Vóór effectmeting; persoon nog niet toegewezen. |
| Echte G/H oud/nieuw | Toekomstige DEF-772-uitvoerder, door A aan te wijzen, bevriest briefs/model/prompt/bronnen en voert gepaarde runs uit | Na afzonderlijke uitvoering- en live-callautorisatie; nu verboden. |
| Menselijke hulp verbetert oordeel | A wijst proefleider/reviewers aan; gebalanceerde oude/nieuwe hulp | Na beschikbare UI-variant en onderzoeksautorisatie. |
| Transport/opslag/stale/poorten | DEF-624/626/627/630 testen zichtbare synthetische keten met versiegebonden INT-03-oordeel | Bij daadwerkelijke levering, vóór volledige appclaim; huidige statische inspectie volstaat niet. |
| Herstel/buurregelconflicten | DEF-638 en regelcoördinatie testen betekenisbehoud/stops en lossen relevante foutieve buurregelreacties op | Na regel-/bewijscontract; geen activering door dit onderzoek. |

Dossierdekking: Q1 doel/norm/toepasselijkheid; Q2 context/bronnen/ontologie/aanvullingen; Q3 samenhang/besluiten; Q4 app/status/proeven/keten; Q5 skills/prompts/verbeteringen; Q6 acceptatie/effect/overdracht. De veertien onderdelen zijn behandeld met expliciete bewijsgrenzen.

**Opleverstatus:** volledig herzien advies B na review van A/C en verwerking van A’s feedback. De onafhankelijke v1 en haar offline nulmeting zijn intact; geen nieuwe appvariant, technische oplevering of aangetoonde kwaliteitswinst. Volgende overdracht: fase-2-pakket aan A voor eigen verwerking, C-verwerking en synthese. Synthesecontrole is nog niet uitgevoerd. Manifest-v2 bindt alle eigen v1-bestanden en fase-2-bestanden; de eigen manifesthash staat afzonderlijk in de oplevering om circulaire zelfhashing te vermijden. Geen gezamenlijke afronding.
