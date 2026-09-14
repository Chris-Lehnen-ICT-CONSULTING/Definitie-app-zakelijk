# DEF-622 — vervolgcriteria en versiebinding geverifieerd

15 september 2026. Dit verslag vervangt de open uitvoeringspunten uit oplevering-v1 voor de hier beschreven codewijzigingen. Productie- en testbron: **`c5344b1e0be35930084f2c94b56960d6b4e21f7f`**, branch `feature/DEF-622-contextcontract`. Latere documentatiecommits wijzigen deze bron niet. Bestaande [draft-PR451](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/451); geen merge of deployment.

De [DEF-622-specificatie](https://linear.app/definitie-app/issue/DEF-622) is vóór overdracht opnieuw opgehaald: `updatedAt=2026-09-14T19:28:50.875Z`, ongewijzigd ten opzichte van de verwerkte besluiten. De oorspronkelijke 14 CON-GT- en 12 CW-GEN-casussen zijn behouden en aan actueel bewijs gekoppeld. Bronkopieën en hashes staan lokaal in `reports/def622/vervolg/onderzoeksbron/`; het onderzoek op oudere commits geldt niet als implementatiebewijs.

## Wat is hersteld

- **Versiebinding:** payload, opgeslagen beoordeling, gate en overname bij vaststelling gebruiken dezelfde strikte integerconventie. Ontbrekende/null/string/bool/float-versies kunnen geen versiegebonden oordeel geldig maken. De verwachte versie voor concurrency blijft een afzonderlijke controle. V2b is gesloten; er staat geen waiver open.
- **Context vóór generatie:** minstens één inhoudelijke waarde in de drie canonieke contextlijsten is verplicht. Zonder die invoer start de definitiegeneratie geen modelaanroep. De UI geeft een begrijpelijke melding. Generieke AI-functies krijgen hierdoor geen onbedoelde contextplicht.
- **Prompt en noodzakelijke naam:** ContextAwareness, CON-01-regelmodule en eindchecklist volgen de afgesproken naamuitzondering. Ook uitsluitend organisatorische context activeert de CON-regelmodule. Het bewijs controleert de werkelijk door de provider ontvangen prompt voor organisatorische, juridische, wettelijke en gecombineerde context.
- **Tekststadia en vergelijking:** de echte geëxtraheerde kern vóór nabewerking en de uiteindelijke tekst worden per record bewaard. Bij wijziging verschijnt exact: ‘De tekst is na generatie aangepast. Bekijk wijzigingen.’ De uitklapbare vergelijking markeert toegevoegde/verwijderde woorden. Generator, editor en expertreader gebruiken hetzelfde bewijs; historische of verouderde gegevens leveren geen verzonnen vergelijking op. De editor vergelijkt met de actuele widgetwaarde.
- **Betekenisdragende woorden en eindkandidaat:** beschadigende prefixverwijdering bij ‘Handeling die’, ‘Proces waarbij’, woorddelen, samenstellingen en samentrekkingen is hersteld. Losse labels blijven normaliseren. Een wijziging tijdens validatie wordt opnieuw getoetst; blijvend instabiele tekst wordt niet met een verkeerd gekoppeld oordeel opgeslagen.
- **Expertbewerking:** definitiekern en bestaande inhoudelijke toelichting worden apart getoond en bewerkt, met behoud bij opslag. Wijzigen, legen en terugzetten zijn getest. Na zekere veldopslag wordt het geselecteerde record uit readback ververst, ook wanneer de vervolgworkflow een exception geeft. Twee opeenvolgende opslagacties A→B→A behouden tekst, ID en versie correct. Dit voegt geen afzonderlijk veld voor een CON-01-naamgrond toe.
- **Regressie-invoer:** vier classificatieproeven en twaalf integratiegevallen krijgen de inmiddels verplichte canonieke context. Hun oorspronkelijke doelassertions en de contextpoort zijn behouden.

De eerdere contexttransport-, duplicaat-, drie-keuzes-, vaststelconflict-, opslag- en exportaansluitingen blijven onderdeel van de gewijzigde code. Automatische beoordeling stelt een concept niet zelfstandig vast.

## Finale verificatie

Alle onderstaande controles zijn door de coördinator uitgevoerd. Tijdens de definitieve unitrun bleef de productie- en testbron ongewijzigd op `c5344b1e0`.

| Controle | Werkelijk resultaat | Bewijs onder `reports/def622/vervolg/` |
|---|---|---|
| Canonieke unitgate met coverage | **5.203 geslaagd + 21 subtests**, 0 fouten; 75 bestaande skips, 1 xfail. **57,09%**, vloer45%; exit0,343,12s | `coordinator-final-unit-v4.log`, `final-gates-v4/unit-cov-junit.xml`, `unit-coverage.xml` in dezelfde map |
| Canonieke integrationgate | **571 geslaagd**, 0 fouten; 28 bestaande skips,15 xfails,2 non-strict xpasses; exit0 | `coordinator-final-integration-acceptance-contract.log`, `final-gates-v3/integration-junit.xml` |
| Acceptance-smoke | **21 geslaagd**,5 bestaande collectie-skips; exit0 | hetzelfde log, `final-gates-v3/acceptance-smoke-junit.xml` |
| Contractgate | **36 geslaagd**,6 bestaande skips; exit0 | hetzelfde log, `final-gates-v3/contract-junit.xml` |
| Laatste gerichte expert-/UI-delta | **38 geslaagd**,0 fouten/skips, inclusief echte AppTests en foutinjectie | `coordinator-expert-exception-green.xml` en `.log` |
| Lint, complexiteit en typen | Ruff/Black schoon; complexiteit**199≤201**,mypy**0**; exit0 | `coordinator-expert-exception-quality.log` |
| Overige kwaliteitsguards | Overrides,pins,orphan,silent-except,grep en markers groen;398 testbestanden met markers;0 blokkerende grepbevindingen | `coordinator-final-guards-c534.log` |
| Timinginventaris |116 locaties,0 te beoordelen wijzigingen; exit0 | `coordinator-final-timing-c534.log` |

Exacte kwaliteitstoolversies: Ruff0.16.5,mypy2.3.1,Black26.5.1. Testselecties, budgetten, coveragevloer en uitzonderingen zijn niet versoepeld. De grep-baseline kreeg uitsluitend een verschoven bestaand regelnummer. Tests draaien via de offline-bootstrap met synthetische tijdelijke SQLite en bevroren externe grenzen; geen gebruikersdatabase of live modeloproep. Bestaande skips/xfails zijn geen uitgevoerde positieve proeven.

## Onafhankelijke review en bewijs per casus

Claude CLI implementeerde; een afzonderlijke Codex CLI reviewde. Dezelfde reviewer herbeoordeelde concrete correctiedelta’s, zonder verdere agents of CLI-delegatie. Alle bevestigde bevindingen hebben dispositie **gefixt en geverifieerd**.

- [Versiebinding V2b gesloten](DEF-622-versiebinding-hervat-review-v1.md): 120 gerichte coördinatortests plus onafhankelijke versie-/SQLite-proeven.
- [26 casus-ID’s en bewijsgrenzen](DEF-622-casusregister-bewijs-v1.md): geen ontbrekende of extra ID’s in de eindcontrole. Geen CON-naamhit is geen bewijs dat alle betekenis behouden is; de gecontroleerde all-green opslagproef is afzonderlijk onderscheiden van echte regeltoetsing.
- [Eerste pakketreview](DEF-622-vervolgpakket-review-v1.md), [gerichte correctiereview](DEF-622-vervolgpakket-review-v2.md), [opslagreferentie](DEF-622-vervolgpakket-review-v3.md) en [definitieve afsluiting](DEF-622-vervolgpakket-review-v4.md). De normale A→B→A-reeks én het exceptionpad zijn met eigen readback gecontroleerd. Geen open reviewbevinding binnen dit pakket.
- [Besloten vervolgplan](../plans/2026-09-14-DEF-622-vervolgcriteria.md).

## Afgesproken grenzen

De totaalscore blijft tijdelijk niet beschikbaar; regeluitkomsten blijven zichtbaar. **DEF-624** bepaalt de latere score-uitwerking. Automatisch CON-01-tekstherstel blijft uit en is vervolgwerk in **DEF-638**; dat uitstel blokkeert deze codelevering niet.

**DEF-630** houdt de algemene approval-, identity- en exportgate. Positieve CON-aansluitproeven zetten overige voorwaarden expliciet synthetisch positief en bewijzen niet de volledige algemene productgate. De bestaande scoreafhankelijke gate blijft fail-closed. Deze levering is daarom geen algemene productvrijgave; PR blijft draft en DEF-622 blijft In Progress.

Geen databaseschemamigratie of nieuwe dependency. Consumenten moeten het bestaande gewijzigde resultaatcontract1.3.0 met nullable totaalscore ondersteunen. De voorbereide skillbronpatch is niet globaal toegepast; extra G/T/H-skilltekst over schadelijke nabewerking blijft een voorstel. Actieve appprompts zijn in deze levering wel aangepast en functioneel gecontroleerd.
