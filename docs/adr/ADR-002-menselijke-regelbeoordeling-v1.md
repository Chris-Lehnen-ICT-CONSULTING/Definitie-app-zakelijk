# ADR-002: Gedeeld contract voor menselijke regelbeoordeling

**Status:** Voorgesteld — geen implementatiebesluit
**Datum:** 18 september 2026 · **Beslisser:** Chris

## Context

De ESS-03-fix vervangt semantische trefwoordoordelen door scoreloze menselijke beoordeling. De generieke `JudgmentReviewEvaluator` heeft nog geen terugleespad voor een afgerond menselijk oordeel. Daardoor kan een gebruiker ESS-03 nog niet duurzaam afsluiten als voldoet, voldoet niet of bevestigd niet van toepassing.

CON-01 en CON-02 hebben al regelspecifieke beoordeling, opslag en actualiteitscontrole. Hun bewezen gedrag blijft behouden. Het op 16 september goedgekeurde [DEF-624-resultaatcontract](https://linear.app/definitie-app/document/def-624-resultaatcontract-en-consumermigratie-goedgekeurd-31b1600cd55d) regelt betrouwbare runstatus en consumertransport, maar geeft geen toestemming voor een nieuwe reviewdatabase of nieuwe normpolicy. Dit voorstel bouwt op dat onderscheid voort.

Eigenaarschap: DEF-624 beoordeelde uitkomsten en transport; DEF-626 append-only opslag/readback; DEF-627 actualiteit; DEF-625 normversies; DEF-630 vaststellen/export. ESS-03 blijft eigenaar van zijn inhoudelijke telbaarheidsnorm. Geen AI-jury, nieuwe dependencies of authsysteem nodig. De bestaande Python/SQLite/Streamlit-stack en bestaande expertomgeving zijn uitgangspunt.

Gelezen op appbasis `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`, met de gereviewde ESS-03-werkdiff. Vindplaatsen: `src/services/validation/evaluators/judgment_review.py`, `src/services/validation/interfaces.py`, `src/toetsregels/runtime_contract.py`, `src/database/models.py`, `src/database/definitie_crud.py`, `src/database/definitie_repository.py`, `src/ui/components/expert_review_tab.py` en `src/ui/components/validation_view.py`. Het uitvoeringsdossier bevat de gedetailleerde codeverwijzingen; deze bronlezing is geen bewijs van een al gebouwde reviewketen.

## Eerste beslissing — reikwijdte van de voorziening

**Voorstel:** één gedeeld contract en één bediening in de bestaande expertomgeving voor menselijke regelbeoordelingen ontwerpen; ESS-03 als eerste regel aansluiten. Andere oordeelregels migreren later afzonderlijk. CON-01/02 niet direct ombouwen.

| Optie | Voordelen | Nadelen | Complexiteit, kosten en onderhoud |
|---|---|---|---|
| A. Gedeeld contract, eerst ESS-03 | Herbruikbare versiebinding, historie en bediening; voorkomt per regel afwijkende uitkomsten | Vereist vooraf precieze afspraken over statussen en transport | Middelgrote eerste wijziging; bestaande stack en opslagpatronen vertrouwd; geen nieuwe operationele dienst of modelkosten; lagere onderhoudslast bij meer regels |
| B. Eigen ESS-03-opslag en bediening | Kleine, regelspecifieke eerste levering | Dupliceert de oplossingen voor CON-01/02; volgende oordeelregel vraagt opnieuw opslag en UI; latere migratie nodig | Kleinere eerste codeomvang, maar hogere onderhoudslast en meer kans op verschillende betekenis van afgerond/verouderd |
| C. Reviewafronding uitstellen | Geen nieuwe contractwijziging nu; huidige bugfix kan worden gepubliceerd | ESS-03 blijft na beoordeling opnieuw open; volledige acceptatie blijft onafgedekt | Geen directe bouwkosten; onopgeloste gebruikershandeling blijft bestaan |

De verwachte aantallen regels en lokale SQLite-opslag vragen geen nieuwe infrastructuur. Schaalbaarheid is hier vooral het consistent ondersteunen van meer oordeelregels, niet een verondersteld verkeersprobleem. Er zijn geen prestaties of urenramingen gemeten.

## Vervolgbesluiten — één voor één na de eerste keuze

1. **Afgerond versus open en niet van toepassing.** Voorstel: de gebruiker kan voldoet, voldoet niet en gemotiveerd niet van toepassing herkennen als afgeronde menselijke uitkomsten. Open beoordeling, ontbrekende invoer en technische fouten blijven afzonderlijk. Bevestigde niet-toepasselijkheid is geen `pass`, geen ontbrekende invoer en geen blijvende reviewvraag. De exacte publieke status-/veldrepresentatie en migratie van consumers worden pas na die inhoudelijke keuze uitgewerkt; dit ADR keurt geen nieuwe enum stilzwijgend goed.
2. **Bevoegdheid en bewijs.** Voorstel: bestaande handelende reviewer, tijdstip, motivering, relevante bron/conventie en expliciete bevestiging vastleggen. Geen verzonnen actor of automatisch menselijk oordeel. De minimale verplichte bewijsvelden worden per relevante beoordelingssoort besproken.
3. **Actualiteit.** Voorstel: binding aan regel/normversie, kandidaat/definitieversie, term, exacte tekst, relevante context en bewijsversie; concurrent gewijzigde invoer weigeren; oude oordelen als historie bewaren en niet als actueel tonen. Ontbrekende historische bindingsgegevens niet als bewijs van actualiteit invullen.
4. **Vervolgbeleid.** Voorstel: geen nieuwe zelfstandige ESS-03-vaststel-/exportblokkade. Een eventueel blokkerend, door een mens vastgesteld ernstig gebrek vergt een apart productbesluit en implementatie onder DEF-630. Hoog betekent niet automatisch blokkeren. Er blijft geen cijfer of hersteldriver uit ESS-03 voortkomen.
5. **Verduidelijking tijdens generatie.** Vastleggen hoe de gebruiker een ontbrekende of tegenstrijdige teleenheid verduidelijkt zonder dat de generator een conventie verzint. De huidige ESS-02-conflictuitvoer uit DEF-751 niet stilzwijgend verbreden. Een apart herstelvoorstel verandert de oorspronkelijke tekst niet automatisch.

Deze punten zijn voorstellen en geen verleende toestemming. Ze worden niet gezamenlijk ter goedkeuring voorgelegd: eerst de keuze tussen A/B/C, daarna het eerstvolgende noodzakelijke punt.

## Consequenties bij keuze A

Eén contract kan reviewbediening, versiecontrole en historie herbruikbaar maken. De eerste wijziging wordt groter dan een ESS-03-veld toevoegen, omdat opslag, evaluator, resultaatconsumers en UI dezelfde betekenis moeten dragen. Zij zal de grens van vijf bestanden/honderd regels waarschijnlijk overschrijden. De concrete impact, migratie en acceptatietests worden na de inhoudelijke besluiten uitgewerkt en vóór uitvoering ter beoordeling aangeboden.

Hergebruik van bestaande `validation_issues`-patronen is een te onderzoeken implementatieoptie, geen besloten opslagmodel. Een nieuwe tabel of andere schemaverandering wordt niet zonder expliciet besluit toegevoegd. Bestaande CON-01/02-reviews blijven leesbaar; algemene vaststelling of categoriekeuze wordt geen impliciete ESS-03-goedkeuring.

## Voorbereide acceptatiegevallen

| Geval | Te bewijzen gedrag na toekomstige implementatie |
|---|---|
| Natuurlijke afbakening zonder code | Mens kan gemotiveerd voldoet vastleggen; heropenen toont hetzelfde actuele oordeel, zonder cijfer |
| ISBN voor fysieke exemplaren | Mens kan gemotiveerd voldoet niet vastleggen; geen automatische toevoeging van een code |
| Water versus afgebakend watermonster | Menselijk bevestigde niet-toepasselijkheid voor de bedoelde stoflezing kan worden afgerond; dit maakt de monsterlezing niet automatisch vrijgesteld |
| Ontbrekende term/tekst versus technische storing | Respectievelijk ontbrekende invoer en fout; geen inhoudelijke afkeuring of verzonnen beoordeling |
| Gewijzigde term, tekst, context, bewijs of norm | Vorig oordeel blijft in historie maar wordt niet actueel gebruikt; beoordeling opnieuw nodig |
| Tegelijk gewijzigde definitie | Opslaan tegen verkeerde kandidaatversie wordt geweigerd; geen verlies van historie |
| Alleen algemene vaststelling / categoriekeuze | Wordt niet als inhoudelijk ESS-03-oordeel teruggelezen |
| Opslag → adapter → UI → vervolgactie | Dezelfde uitkomst, motivering en binding blijven behouden; geen cijfer of nieuwe gate via conversie |

Dit zijn vooraf ontworpen verwachtingen, geen al uitgevoerde tests en geen expertgoldset. Bij uitvoering horen echte tijdelijke repositories, UI/adaptercontroles, TDD, relevante lint/gates en onafhankelijke CLI-review. Claude Code CLI implementeert; Codex CLI reviewt; de coördinator controleert het bewijs.

## Acties vóór uitvoering

- De bestaande ESS-03-bugfix en skillbronnen afzonderlijk publiceren met hun bewezen scope.
- Chris eerst alleen A/B/C laten kiezen.
- Daarna de uitkomsten en niet-toepasselijkheid bespreken, gevolgd door de overige noodzakelijke beslissingen.
- Na besluitvorming de afgebakende gedeelde levering onder bestaande issues specificeren; geen dubbel nieuw issue of stilzwijgende sluiting van DEF-624/DEF-766.
