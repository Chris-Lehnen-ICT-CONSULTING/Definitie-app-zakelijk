# DEF-835 — WP5a: voorbereide aansluiting op de validatieketen

28 september 2026. Voorstel voor het pakket ná de technische proefrunner. Nog geen implementatiemandaat voor deze uitbreiding. Basis van deze inventarisatie: 558b50c3f161f819cda6c445f7f81b70888918ac. Dit is een afgebakende tussenstap; volledige WP5 vereist daarna de gedeelde opslagvoorziening DEF-626 en presentatie/herladen.

## Doel en wijzigingsbereik ter akkoord

Een expliciet geïnjecteerde O2-dienst moet de bestaande validatieketen kunnen doorlopen en het WP3-document ongewijzigd in `rule_results['INT-02']` afgeven. Gewone O1-validatie mag hierdoor geen INT-02-modelcall starten. De actieve recordconfiguratie blijft O1; uitsluitend een expliciete test-/proefconfiguratie met O2-evaluator maakt het nieuwe pad bereikbaar. Geen impliciet defaultmodel, fallback of auto-activering.

| Bestand | Werkelijke vindplaats / citaat | Voorgestelde wijziging |
| --- | --- | --- |
| `src/services/container.py` | :332 `def int03_assessment_service(self)`; :421 `int03_assessment_service=self.int03_assessment_service()` | O2-factory die alleen met expliciet vastgesteld profiel en budget construeert. Geen automatische productie-instantiatie door het kopiëren van INT-03. |
| `src/services/orchestrators/definition_orchestrator_v2.py` | :147 `int03_assessment_service: Any \| None = None`; :360 doorgeven aan validation orchestrator | Additieve optionele INT-02-injectie, geen lazy default of verborgen livecall. |
| `src/services/orchestrators/validation_orchestrator_v2.py` | :139 dezelfde INT-03-injectie; :568 `context_dict.pop("int03_assessment", None)` | Equivalent veilige voorbereiding voor INT-02 met eigen WP1-invoer/binding; aangeleverde assessments nooit blind vertrouwen. Ontbrekende dienst/config blijft expliciet open. |
| `src/services/validation/modular_validation_service.py` | :102 `_EVALUATORS_MET_DEELUITKOMST`; momenteel alleen SENTENCE_BOUNDARY en PRONOUN_REFERENCE_ASSESSMENT; :1640 `_boek_rule_result` | DECISION_RULE_ASSESSMENT toevoegen en alle O2-statussen zonder score doorboeken. |
| Nieuw `tests/unit/services/orchestrators/test_def835_int02_wrappers.py` | Nog niet aanwezig; te controleren vóór implementatie | Generatie- en recordroute met fake dienst; exacte kern/context; injectie- en foutpaden. |
| Nieuw `tests/unit/validation/test_def835_int02_modular.py` | Nog niet aanwezig; te controleren vóór implementatie | O2-evaluator met echte modular service, alle statuspaden in rule_results; geen gate/cijfer. |
| Nieuw `tests/unit/services/test_def835_int02_container.py` | Nog niet aanwezig; te controleren vóór implementatie | Geen defaultprofiel/calls; expliciete DI consistent; O1 onveranderd. |

Raming: **zeven bestanden**, circa 400–650 regels inclusief tests. Geen nieuwe dependency. De nieuwe optionele constructorparameters en profiel-/budgetinjectie zijn een API-uitbreiding; zowel dit bereik (>5 bestanden) als die uitbreiding vragen akkoord. Geen schema- of publiek resultaatcontractwijziging voorzien: WP3 leverde 2.3.0. Blijkt die toch nodig, dan eerst concreet terugkoppelen.

## Eerst rood en acceptatie

1. O1-record en normale container veroorzaken nul INT-02-calls, ook bij aanwezige losse metadata.
2. Expliciete O2-configuratie met dienst gebruikt exact de oorspronkelijke kern; geen cleaning/overschrijven. Recordkern is gezaghebbend; ongeldige aanwezige recordkern is een fout, geen fallback.
3. Een door de aanroeper meegegeven assessment kan nooit zelfstandig pass/fail opleveren. Verse binding en WP1-controles bepalen actualiteit.
4. Lege kern/ontbrekende context → NE zonder call; ontbrekend profiel/dienst → expliciet open; ongeldige binding/technische fout → error, nooit inhoudelijk oordeel. Alleen foutcategorie/type in logs.
5. Geldige pass, adviserend fail, review_required, not_evaluated, not_applicable en error komen via de echte modular service in rule_results. Excluded_from_score; geen poort, herstel of tweede modelcall.
6. Ontwikkelgevallen C105/C107/C112 met handmatige fake-respons bewijzen de ketenmapping, geen semantische modelkwaliteit. C117 bewijst afwijzing ongeldige citaten. C118 wordt pas bij opslag bewezen.
7. Bestaande INT-03-/ESS-03-/bronbeoordelingsroutes behouden hun gerichte regressiebewijs; herhaal alleen de geraakte wrappers en container/modular-tests. Nieuwe tests eerst rood, daarna groen en lint. Onafhankelijke Codex CLI-review van deze concrete diff.

## Afzonderlijke opslag- en presentatievervolgstap

De bestaande INT-03-opslag heeft specifieke sleutels en herstelpaden in `src/database/models.py:638`, `src/services/definition_repository.py:1106` en `:1345`; dat is geen geleverde algemene DEF-626-snapshotvoorziening. Die route blind kopiëren naar INT-02 zou de afgesproken gedeelde historie niet leveren.

DEF-626 staat bij actuele Linear-controle in Backlog. Voor het volgende pakket moet het gedeelde transactie-/snapshotcontract concreet worden vastgelegd: definitieversie en volledige validatiesnapshot atomair, append-only historie, exacte input en binding, rollback bij fout en expliciete legacy/stale-status. De bestaande transactieroute zit onder meer in `definition_repository.py:1665`; de definitieve migratie- en bestandslijst volgen uit dit gedeelde contract. Dit voorstel autoriseert geen stil DEF-626-implementatiewerk.

Daarna aansluiten: `definition_repository.py`, `definitie_crud.py`, `models.py`, `definition_edit_service.py`, `data_aggregation_service.py`, `export_service.py`, `definition_edit_tab.py` en `validation_view.py` plus gerichte tijdelijke-SQLite-/UI-tests. Pas save→reload met ongewijzigd historisch document, juiste actualiteit na betekeniswijziging, consistente UI/export en nul verborgen herbeoordeling sluit C118. Omvang/schema eerst apart vaststellen. Het O1-redenvak in `validation_view.py:880` bevat INT-02 al; dat bewijst nog geen O2-detailpresentatie.

Activering blijft apart: technische keten, onafhankelijke inhoudelijke modelevaluatie, duurzame historie en finale tests moeten elk hun eigen bewijs hebben. Actions blijven uit.
