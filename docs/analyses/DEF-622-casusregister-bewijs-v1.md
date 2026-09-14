# DEF-622 — bewijsmapping van de 26 casus-ID's (G/T/H-register)

Bron: `casusregister-generatie-v2.md` (sha256 `3198498b…`), synthese
`gezamenlijk-besluitvoorstel-generatie-v2.md` (sha256 `3e5e7535…`); kopieën en
hashes in `reports/def622/vervolg/onderzoeksbron/manifest.json`. Alle proeven
hieronder draaien op de implementatiecommit (branch
`feature/DEF-622-contextcontract`), met echte productiegrenzen: echte regelset
(`ModularValidationService`), echte `DefinitionOrchestratorV2` met bevroren
modeluitvoer, echte cleaner, echte `PromptServiceV2`, synthetische SQLite.
Onderzoeksproeven op `92b870d8`/`d68a98a9` gelden niet als uitvoeringsbewijs.

Testbestand voor de register-ID's: `tests/unit/services/test_def622_casusregister.py`
(één test per ID of ID-paar, met eigen invoer en uitkomst). Waar het register
op eerder DEF-622-bewijs aansluit, staat dat erbij.

| ID('s) | Casusgrond (eigen invoer) | Bewezen uitkomst op huidige code | Test(s) | Scope-opmerking |
|---|---|---|---|---|
| CON-GT-001, CW-GEN-05 | Alle contextlijsten leeg | Eerst context vragen; geen modelaanroep; geen concept | `test_CON_GT_001_CW_GEN_05_…`; batch 1 `test_def622_generatiegrens.py` (3 varianten) en UI-handler `test_def622_context_voor_generatie.py` | Besloten vervolgcriterium; geldt voor alle ingangen via `create_definition` |
| CON-GT-002 | Neutrale kern, Team Koper in context | D1 positief; D2 geen vermelding binnen bereik; CON-01 Voldoet | `test_CON_GT_002_…` | Geen automatische vaststelling (zie GT-013) |
| CON-GT-003 | Gegenereerd "controle die binnen Team Koper wordt uitgevoerd" | Eerst signaal (open) op de echte generatieroute; met registratiebeoordeling Voldoet niet | `test_CON_GT_003_…` | Zelfde norm als GT-008 |
| CON-GT-008 | Aangeleverd, zelfde zin | Signaal → na registratiebeoordeling afkeur met reden; origineel niet gewijzigd | `test_CON_GT_008_…` | — |
| CW-GEN-02, CW-GEN-07 | "Controle, in de context van DJI, …" (gegenereerd / aangeleverd) | Eerst open, na registratiebeoordeling afkeur; géén automatische meta-frase-exceptie | `test_CW_GEN_02_CW_GEN_07_…[gegenereerd/aangeleverd]` | — |
| CON-GT-004, CW-GEN-01 | Zilverkeurmerk, Stichting Zilver enige uitgever en contextwaarde | Naam behouden door generatie/opschoning/readback; eerst signaal; na geldige beoordeling toegestaan | `test_CON_GT_004_CW_GEN_01_…`; expert/UI-keten `test_def622_apptest_expert.py` | Onderbouwing in bestaande CON-01-beoordeling (reden), geen nieuw veld |
| CON-GT-005 | Zelfde naamtreffer zonder grond | Nog te beoordelen; vaststelgate geblokkeerd; niets verzonnen | `test_CON_GT_005_…`; `test_def622_vaststelconflict.py` | — |
| CON-GT-006, CW-GEN-12 | Gewoon woord "om", OM in context | Geen inhoudelijke naamafkeur (nooit Voldoet niet, geen violation); signaal blijft open (B-04: geen acroniemuitzondering); cleaner vervormt niets | `test_CON_GT_006_CW_GEN_12_…` | Bewijsgrens: open signaal vraagt een expertoordeel, geen afkeur |
| CW-GEN-03 | "Handeling die … om naleving vast te stellen", Team Zilver | Bovenbegrip/grammatica blijven na nabewerking | `test_CW_GEN_03_…`; batch 1 `test_def622_bovenbegrip_beschermd.py` | Cleanerbescherming, geen hergeneratie |
| CW-GEN-04 | Promptopbouw DJI/strafrecht/Sv (en org-only) | Alle actieve bronnen dragen de naamuitzondering; geen absoluut verbod; CON-regelmodule ook bij alleen-organisatorische context; providergrens ontvangt dezelfde prompt | `test_CW_GEN_04_…`; `test_def622_eindprompt.py` (4 varianten + ketenbewijs) | Gevonden en hersteld: `con_rules` was alleen actief bij juridische/wettelijke context |
| CON-GT-007, CW-GEN-11 | Naam alleen in toelichting | Kern/toelichting gescheiden bij domeinreader én legacy recordreader; CON-01 toetst alleen de kern | `test_CON_GT_007_CW_GEN_11_…`; `test_def622_expert_reader_kern_toelichting.py` | Expert-bewerking bewaart de toelichting |
| CON-GT-009, CW-GEN-08 | Ingevulde context, evaluator | Context bereikt de evaluator via de echte transportroute; D1 pass, D2 ziet de naam | `test_CON_GT_009_CW_GEN_08_…`; transporttests batch 1 | — |
| CON-GT-010, CW-GEN-09 | Uitgever verwijderd ("kwaliteitskeurmerk", "de organisatie") | (1) De cleaner verwijdert de noodzakelijke naam niet; (2) een naamloze kandidaat erft de eerdere 'noodzakelijk'-beoordeling niet (vingerafdruk); geen treffer = D2-deeloordeel met beperkt bereik, geen behoudbewijs | `test_CON_GT_010_CW_GEN_09_…` | **Bewijsgrens:** verlies van onderscheid is een oordeel van ESS-05/INT-03/04 en de expert, geen CON-01-blokkade; het afwijzen van zo'n kandidaat is herstelscope (DEF-638). Geen buurregelnormbesluit |
| CON-GT-011, CW-GEN-06 | Zelfde begrip/volledige context met leidende definitie | Checker vindt het record (D3); nieuw concept ernaast archiveert niets; drie keuzes | `test_CON_GT_011_CW_GEN_06_…`; keuzes-AppTest `test_def622_apptest_keuzes.py`; vervanging bij vaststelling `test_def622_vaststelconflict.py` | B-09/B-10 |
| CON-GT-012, CW-GEN-10 | Herhaalde fout/limiet; evaluatorstoring | **Uitgestelde herstelscope (DEF-638):** nul herstelcalls, ook met enhancement aan; open naamfunctie en technische fout apart herkenbaar; handmatige opvolging | `test_CON_GT_012_CW_GEN_10_…` (open signaal en storing elk in een eigen tijdelijke repository, zodat de duplicaatguard van productie ongewijzigd blijft); batch 1 `test_def622_generatiegrens.py` | Geen herstelstrategie beslist |
| CON-GT-013 | Alle automatische controles groen | (1) Echte CON-01-evaluator: elke actieve regel pass, geen violations, gate uitsluitend dicht door niet-beschikbare scores (`overall_score_unavailable` plus categorie-`_unavailable`, geen andere gate); concept blijft concept. (2) Gecontroleerd volledig positief validatieantwoord aan de orchestratorgrens (`is_acceptable=True`, gate open): opgeslagen status `draft`, `approved_by` leeg; vaststellen alleen handmatig na expertbeoordeling | `test_CON_GT_013_alle_automatische_controles_groen_blijft_concept`; `test_CON_GT_013_volledig_positieve_automatische_toetsing_maakt_niet_vastgesteld`; expert-AppTest (handmatige vaststelling) | **Bewijsgrens:** proef (1) = CON-subset, geen claim dat alle 53 regels groen zijn (met de volle regelset is geen kandidaat volledig groen door de generieke heuristieken); proef (2) vervangt de validatieservice door een all-green antwoord en bewijst alleen de orchestrator-/opslaggrens. Geen automatische vaststelling |
| CON-GT-014 | Kern/context gewijzigd na naambeoordeling | Oud oordeel geen actuele toestemming (vingerafdruk + versiebinding) | `test_CON_GT_014_…`; `test_def622_context_contract.py`, `test_def622_vaststelconflict.py` | Versiebinding V2a–V2c gesloten |

## Besluiten die het register aanvullen (14 september 2026)

- Context vóór generatie verplicht voor elke definitiegeneratie-ingang; geen modelaanroep zonder context.
- Tekstvergelijking: melding uitsluitend bij een echte wijziging na generatie; echte kern vóór nabewerking versus eindtekst (`test_def622_tekstwijziging*.py`, beide AppTests); historisch/stale: geen melding.
- Getoetst = getoond = opgeslagen; wijziging na toetsing vereist hertoetsing; blijvende mutatie fail-closed.
- Automatisch tekstherstel uitgesteld (DEF-638); totaalscore blijft niet beschikbaar; DEF-630 houdt de algemene gate; geen globale skillpatch toegepast.
