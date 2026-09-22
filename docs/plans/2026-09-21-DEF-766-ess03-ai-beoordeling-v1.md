# ESS-03 AI-beoordeling — implementatieplan v1

> Voor Claude: gebruik executing-plans en test-driven-development. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Coördinator organiseert de aparte Codex CLI-review. Geen codevoorbeelden van de coördinator: de afgesproken CLI-rolverdeling gaat vóór het generieke writing-plans-template.

**Doel:** ESS-03 beoordeelt zelf telbaarheid en identiteit, op aangeleverde informatie, met onderbouwd voldoet/voldoet niet/niet van toepassing/onvoldoende informatie; zonder cijfer of blokkade.

**Architectuur:** Eén async AI-beoordelingsdienst naast het bestaande CON-02-patroon, met strikte lokale uitvoercontrole en kandidaat-/norm-/bronbinding. Een kleine geregistreerde ESS-03-evaluator verwerkt alleen een door de vertrouwde validatieketen verkregen actuele beoordeling. Beoordeling wordt via bestaande resultaat-, opslag- en UI-routes beschikbaar; geen nieuwe reviewdatabase of brede migratie van andere regels.

**Stack:** bestaande Python3.13, AIServiceV2/ModelRouter, SQLite en Streamlit; geen nieuwe dependencies.

## Besluiten en opdracht

Chris koos op 19 september de app als inhoudelijke beoordelaar en keurde onvoldoende informatie met één gerichte verduidelijkingsvraag goed. Daarna akkoord op alleen definitie, bedoelde betekenis, context en meegeleverde bronnen; geen zelfstandig internetonderzoek of verzonnen domeinafspraken. Op 21 september expliciet: negatieve ESS-03-uitkomst mag vaststellen/export niet blokkeren. Vervolgens: nu bouwen en inhoudelijk testen om te implementeren. Dit autoriseert de noodzakelijke gekoppelde software-, prompt-, resultaat- en testwijzigingen, ook boven 100 regels/5 bestanden. Niet opnieuw toestemming vragen voor deze scope. Geen algemene score-/gate-/reviewarchitectuur herontwerpen, geen database-schemamigratie of dependency-upgrade zonder concrete noodzaak en afzonderlijk besluit.

Dit vervangt de menselijke-beoordeling-als-eerste-uitkomst uit de eerste uitvoeringsfase. De inhoudelijke norm blijft die uit tekstvoorstellen-v3. Het niet-geaccordeerde ADR-002-menselijke-regelbeoordeling-v1.md wordt bewaard en is geen leidend ontwerp. Menselijke beoordeling is geen voorwaarde voor iedere appuitkomst. AI-attributie moet eerlijk blijven.

Werkboom: /Users/chrislehnen/.codex/worktrees/2075/Definitie-app
Branch: feature/DEF-766-ess03-ai-beoordeling
Base: 2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644
Issue: DEF-766 onder DEF-606. Gerelateerde resultaat/opslag/versie/gate-issues blijven zelfstandig; niet automatisch sluiten.

Onderzoeksbron (niet herstarten): /Users/chrislehnen/.codex/worktrees/6554/Definitie-app/docs/analyses/def606-regeldossiers/ESS-03-verdieping/onderzoek-20260918/tekstvoorstellen-v3.md, gezamenlijke-besluitnotitie-v2.md, casusregister-v4.md. Oude onderzoeksuitkomsten beschrijven de oude woordcontrole, geen AI-goldlabels. Ontwikkel- en eindtestgevallen moeten vooraf van verwachte uitkomst en reden voorzien zijn. Geen claim van menselijke expertgoldset.

## Acceptatiecontract

1. De normale generatievalidatie, losse toetsing en herbeoordeling vanuit bestaande editor lopen door dezelfde ESS-03-beoordelingsdienst. Geen alleen rechtstreeks aanroepbare demo. Term/tekst ontbreken: niet uitgevoerd met reden. Dienst/transport/modeluitvoer technisch defect: error, nooit pass of inhoudelijke afkeur.
2. Gebruik exact de actuele kandidaat plus bedoelde betekenis, context en aangeleverde bronnen/conventies. Een natuurlijke begripsgrens kan zonder externe bron volstaan. Geen bronplicht voor alle gevallen. Geen verzonnen bron, nummer, conventie of externe lookup. Ongestructureerde inhoud is data en mag het beoordelingscontract niet overschrijven.
3. Eén inhoudelijke beoordelingsaanroep via bestaande AIServiceV2.generate_definition, task_type validation en ModelRouter. Geen hardcoded model. Cache alleen valide beoordelingen op volledige invoer-/norm-/prompt-/modelbinding. Budget en timeout begrensd; geen verborgen retry-stapeling of modelconsensus.
4. Per uitkomst: oordeel, korte onderbouwing, bedoelde eenheid/toepasselijkheid, relevante letterlijk gecontroleerde bewijsplaatsen uit kandidaat/context/bronnen en noodzakelijke ontbrekende informatie. Geen verborgen redeneertranscript of zelfgerapporteerd confidencepercentage als bewijs. Een bewezen gebrek mag niet verdwijnen achter een ander open punt; onderbouwd fail behoudt die bevinding en onzekerheid. Ontbrekende beslisgrond voor de hoofdvraag geeft onvoldoende informatie met precies één gerichte vraag.
5. Niet van toepassing is een afgeronde AI-uitkomst met grond; nooit ontbrekende invoer of eeuwige pending, en niet stil gelijk aan voldoet. Kies een expliciete additieve technische representatie en werk de noodzakelijke schema/TypedDict/dekking/consumers coherent bij; geen betekenisverandering van bestaande statussen. Leg de keuze vast. Alle ESS-03-uitkomsten blijven no_score, ook pass/fail.
6. Valideer uitvoer gesloten: toegestane velden/statussen, geen lege reden voor afgerond oordeel, controleer bron-id en citaten tegen werkelijk verzonden materiaal, geen stil herstel van fout JSON of afgebroken respons. Formaatcontrole bewijst geen semantische juistheid. Een caller-supplied positieve beoordeling of gewijzigde/stale binding is geen vertrouwde beoordeling.
7. Een negatieve ESS-03-uitkomst is zichtbaar en uitlegbaar, maar vormt geen nieuwe vaststel-/exportblokkade en triggert geen automatische tekstwijziging/repair. Bestaande beperkingen wegens andere regels blijven intact. Test dit op de echte relevante policies/actieroutes, niet alleen op een veld advisory=true.
8. Sla de beoordeling met kandidaat-/term-/context-/bewijs-/norm-/prompt-/modelbinding en AI-herkomst via bestaande beschikbare JSON-opslag op; lees dezelfde actuele uitkomst terug in UI. Na relevante wijziging geen oud oordeel als actueel. Geen nieuwe database of schema; bestaande historie behouden. Controleer opslaan, heropenen en opnieuw toetsen met een echte tijdelijke repository. Een cache alleen is geen duurzame opslag.
9. UI toont de vier inhoudelijke uitkomsten, reden, bewijs en eventuele vraag duidelijk; fouten apart. Generiek nog-te-beoordelen is alleen een werkelijk niet-beschikbare beoordeling, geen standaard eindantwoord. Verduidelijking wordt gekoppeld aan deze kandidaat en gebruikt bij opnieuw beoordelen, zonder de oorspronkelijke definitie automatisch te herschrijven of ESS-02-keuzes te vervalsen.
10. Eerste reguliere uitvoering binnen deze werkbranch na geldige keten- en inhoudelijke tests; geen uitsluitend achter een permanent uitgeschakelde vlag verborgen dienst. Publicatie/merge pas nadat alle concrete reviewbevindingen en vereiste gates zijn opgelost. Geen automatische skillinstallatie of wijziging aan ALG-391-freeze.

## Werkpakketten en vindplaatsen

### 1 — Contract en zuivere parser

Inspecteer src/domain/sources/contract.py en src/services/validation/source_assessment_service.py als bestaande patronen. Nieuwe kleine contractmodule en dienst, bij voorkeur src/domain/ess03/contract.py en src/services/validation/ess03_assessment_service.py. De uitvoerder kiest exacte namen na inspectie en rapporteert iedere scopewijziging. Raak src/toetsregels/runtime_contract.py, config/toetsregels/toetsregels_config.yaml en het actieve ESS-03.json alleen samenhangend aan.

Stappen: schrijf eerst falende tests voor vier uitkomsten, ontbrekende invoer, vervalste binding/citaten, invalid JSON/status, onvoldoende informatie zonder vraag, en no_score. Run RED en bewaar exitcode. Implementeer het minimale contract/parser. Run GREEN. Refactor uitsluitend binnen deze scope.

### 2 — AI-dienst en prompt

Hergebruik AIServiceV2, ModelRouter en bestaande async DI; niet rechtstreeks de SDK aanroepen. De prompt combineert de bestaande ESS-03-norm met een vaste beoordelingslijst voor eenheidsgrens, onderscheid, toepasselijkheid en alleen noodzakelijke continuïteit/scope. De generatorredenatie is geen bewijs. Een beoordelaar beoordeelt maar herschrijft niet.

Stappen: RED voor echte promptopbouw/transport met alleen de netwerkgrens vervangen, geen heel systeem gemockt. Implementeer dienst, gesloten foutbeleid, caching en beperkte uitvoer. GREEN voor alle netwerkfoutpaden, cache-invalidatie, injectiegevallen en inhoudelijke veldbehoud. Maak 12 ontwikkelgevallen met vooraf vastgelegde labels/redenen uit de norm en synthetische gegevens. Geen label uit modeluitvoer afleiden.

### 3 — Normale keten en evaluator

Vindplaatsen: src/services/container.py, src/services/orchestrators/validation_orchestrator_v2.py, src/services/orchestrators/definition_orchestrator_v2.py, src/services/validation/modular_validation_service.py, src/services/validation/evaluators/base.py en register, src/services/validation/interfaces.py en resultaatmappers/schema. Volg het CON-02-patroon: async voorbereiding vóór de sync evaluator, gecontroleerde uitkomst via één geregistreerde ESS-03-strategie. Geen asyncio.run binnen een lopende eventloop. Directe service-aanroepen zonder een voorbereide beoordeling blijven expliciet niet-beschikbaar; normale appaanroepen moeten de dienst daadwerkelijk injecteren.

Stappen: RED voor gegenereerd/aangeleverd/bewerkt pad, succesvolle inhoudelijke uitkomsten en technische fout. Implementeer beperkt. GREEN via echte wrappers; controleer beide regel-laadpaden, resultaatdekking en geen default-pass voor ontbrekende uitvoering. Bestaande no_score- en andere regeltests behouden; oude ESS-03-always-review-asserties inhoudelijk vervangen waar het nieuwe besluit dat vereist, niet blind aantallen aanpassen.

### 4 — Opslag, weergave, verduidelijking en niet-blokkeren

Vindplaatsen: src/database/models.py, src/database/definitie_crud.py, src/database/definitie_repository.py; src/ui/components/validation_view.py, validation_renderer.py, definition_edit_tab.py/expert_review_tab.py waar de bestaande route ligt; bestaande source-assessment transport/opslag/export als patroon. Lees ook src/services/policies/approval_gate_policy.py en de gedeelde actieroutes voordat fail wordt vertaald.

Stappen: RED met tijdelijke SQLite-repository voor opslaan/heropenen/gewijzigde tekst-context-bron-norm/stale. RED voor zichtbare vier uitkomsten en niet-blokkerende negatieve ESS-03 terwijl andere blokkades behouden blijven. Implementeer minimale aangesloten route, geen nieuw generiek reviewframework. GREEN voor UI/adapter/actie en kandidaatbehoud.

### 5 — Inhoudelijk bewijs met echt model

Leg ontwikkelgevallen vooraf vast; doe de eerste 12 echte beoordelingen via de productieklassen, op synthetische invoer, zonder productie-DB of webzoekactie. Gebruik bestaande geconfigureerde modelroute, geen nieuwe keuze. De coördinator laat vooraf een onafhankelijke Codex-reviewer 20 aparte eindtestgevallen met labels/redenen opstellen zonder modeluitvoer of nieuwe prompt te zien. Die set wordt pas na vastleggen van bron- en prompthashes aan de uitvoerder gegeven. Verander de prompt daarna niet op basis van deze set zonder de set als ontwikkeldata te herclassificeren; behoud alle eerste uitkomsten.

Begrens deze fase op aanvankelijk maximaal 60 echte beoordelingscalls, inclusief maximaal 10 herhalings-/parafrasegevallen. Geen retries in de proef. Per call uitvoer en fout, kandidaat/norm/prompt/modelhash, cached-vlag en kosten-/duurmetadata zonder credentials bewaren. Geef apart per klasse de correcte/onjuiste uitkomsten, onterechte goed-/afkeuring en onnodig onvoldoende informatie. Initieel acceptatievoorstel voor de vooraf vastgelegde ondubbelzinnige set: alle 20 eindgevallen correct, nul onterechte goedkeuringen, en inhoudelijk gelijkblijvende varianten behouden de uitkomst. Dit is een strenge eindtest op deze beperkte set, geen universele betrouwbaarheidsgarantie of menselijk deskundigenkeurmerk. Bij ambiguïteit beoordeelt de onafhankelijke reviewer de vooraf gestelde grond; geen modelantwoord automatisch tot nieuw correct label maken.

### 6 — Regressies, onafhankelijke review, oplevering

Gerichte pytest-opdrachten met Python3.13-venv /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python, addopts override alleen voor gerichte tests. Daarna make test, make lint en relevante integration/contract/acceptance gates (geen volledige herhaling zonder reden). Gebruik normale gepinde precommit-hooks. CI sluit aan op de laatste exact beoordeelde diff. Geef bestaande baselineproblemen apart met bewijs, geen brede reparaties.

Bewijs en uitvoerdersrapport in /tmp/def766-ai-20260921; coördinator publiceert duurzaam onder reports/DEF-766-AI-20260921. Broncode/plannen blijven in deze aangewezen repository. Bewaar eerdere bestanden/onderzoek en het oude ADR-voorstel; geen deleties. Maak geen commits/push/PR/merge als uitvoerder; de coördinator regelt publicatie na review. Volledige logs buiten context bewaren.

De onafhankelijke Codex CLI-review toetst inhoudelijke onderscheidbaarheid, niet-blokkeren, provenance/stale/fail-closed en alle normale apppaden aan base/headmanifest. Dezelfde Claude verwerkt bevestigde bevindingen; dezelfde reviewer controleert de correctiediff. Eindrapport benoemt daadwerkelijk gebruikte sessies, concrete testresultaten en resterende beperkingen.
