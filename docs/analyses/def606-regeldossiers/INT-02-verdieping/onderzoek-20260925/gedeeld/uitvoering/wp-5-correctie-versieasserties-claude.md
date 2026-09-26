# WP5 — drie achtergebleven contractversieasserties

Jij bent dezelfde Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Coördinator verifieert; afzonderlijke Codex CLI-review blijft verplicht en wacht momenteel op herstel van CLI-authenticatie. Nederlands.

Werkboom /Users/chrislehnen/Projecten/Definitie-app; feature/DEF-771-int02-contract-o1, reviewcheckpoint d5bf3a0e674febd09be94659b8b772e48a231b18. Behoud bestaande wijzigingen. Alleen jij schrijft de drie hieronder genoemde bestanden. Dit is een kleine noodzakelijke testcorrectie op de al expliciet goedgekeurde algemene contractversie 2.2.0; geen nieuw contractbesluit.

De volledige make test-run is afgerond en bewaard in gedeeld/uitvoering/wp5-make-test.log: 4 failed, 7615 passed, 75 skipped, 722 deselected, 1 xfailed, 21 subtests passed; make exit 2. Drie failures zijn exact assert '2.2.0' == '2.1.0'. Gebruik die aanwezige RED-uitvoer; geen nieuwe brede nulmeting nodig.

## Eigendom en minimale correctie

- tests/unit/services/orchestrators/test_def766_ess03_wrappers.py: de assertion op de algemene result.version is nog CONTRACT_VERSION == '2.1.0'. Herijk die naar '2.2.0'; verander het onafhankelijke ESS-03-assessmentcontract niet.
- tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py: dezelfde algemene result.version-assertion naar '2.2.0'; het CON-02-assessmentcontract blijft intact.
- tests/unit/validation/test_validation_readiness.py: test_contractversie_is_verhoogd_naar_2_1_0, naam en verwachte algemene contractversie herijken naar 2.2.0. Behoud de test en alle overige controles.

Verwacht minder dan twintig gewijzigde regels, drie bestaande bestanden. Maak herstelkopieën. Geen productiecode, overige tests, dependency, schema, score, gate of norm wijzigen. Geen bestanden of testgevallen verwijderen. De vierde failure (test_config_system.py::TestConfigManager::test_environment_detection, offlinegate blokkeert .env) wordt door de coördinator op de basis onderzocht; raak die niet aan.

## Verificatie

Draai de drie volledige genoemde testbestanden offline via bestaande .venv/pytest-bootstrap; Ruff en Black op die bestanden. Bewaar volledige commando's, logs en exitcodes onder docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/ met vrije namen. Geen volledige suite starten: de coördinator draait daarna de volledige pytest-suite. Geen live modelcalls/productiedata, commit/push/PR/Linear-mutatie. Max drie pogingen per actie. Meld iets dat inhoudelijk buiten deze correctie valt vóór uitbreiden.

Lever de exacte diffstat, hashes en GREEN-/lintbewijs. Stop daarna. De coördinator actualiseert de reviewhead zodra de correctie is geverifieerd.
