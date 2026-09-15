# DEF-743 — uitgevoerd bronbehoud en bronweergave

15 september 2026. Branch `feature/DEF-743-con02-bronbasis`, basis `dc7a70e80`. Lokale wijzigingen, niet gecommit of gepubliceerd. Chris gaf expliciet akkoord voor de exacte brontransportpatch en het reviewpakket naar de bestaande Cowork-sessie. Claude Code CLI implementeerde; Codex CLI voerde onafhankelijke code-reviews uit. Deze reviews vervangen de inhoudelijke kruisreview met Cowork niet.

## Werkelijk gewijzigd

- Geselecteerde, niet-lege korte documenten blijven beschikbaar zonder letterlijke termtreffer; bestaande caps en termgerichte PDF/DOCX-selectie blijven behouden. Lege zoektermen selecteren geen bronnen.
- Bestandsnaam, citeerlabel, selectiewijze en documentcontext blijven behouden. Beschikbare RAG-identiteit, bron-/passagecoördinaten en geneste metadata worden zonder verzonnen waarden gekopieerd; geneste gegevens blijven onafhankelijk.
- De bronsectie toont neutrale herkomst, zoekscore voor web/RAG en selectiewijze voor documenten. Een echte nulscore wordt niet door confidence overschreven.
- Beschikbare RAG-links worden getoond; naast de 500-tekenspreview is de volledige aangeleverde passage raadpleegbaar.

## Controle

| Bewijs | Uitkomst | Log |
| --- | --- | --- |
| Bronselectie/transport vóór patch | 17 gefaald, 9 geslaagd | `/tmp/DEF-743-claude-red-v4.log` |
| Gerichte A/B/prompt/docx-tests na patch | 37 geslaagd, exit 0 | `/tmp/DEF-743-approved-targeted.log` |
| A-tests met ResourceWarning als error | 26 geslaagd, exit 0 | `/tmp/DEF-743-approved-a-only.log` |
| Volledige unitgate | 5255 geslaagd, 0 gefaald; 75 overgeslagen, 721 buiten selectie, 1 verwachte failure, 21 subtests geslaagd; exit 0 | `/tmp/DEF-743-approved-make-test.log` |
| Projectlint en A-bestandslint | Ruff/Black schoon, exit 0 | `/tmp/DEF-743-approved-lint.log` |
| B-bestandslint | Ruff/Black schoon, exit 0 | `/tmp/DEF-743-ui-lint-v2.log` |
| Codex CLI-review A, toegepaste patch | Geen bevestigde bevindingen; exacte patchmatch en A/B-aansluiting bevestigd | `/tmp/DEF-743-codex-applied-review-result.md` |
| Codex CLI-review B | Geen bevestigde bevindingen | `/tmp/DEF-743-codex-ui-review-result.md` |

## Grenzen

De tests zijn offline unit-/componenttests met synthetische gegevens en een echte Streamlit AppTest voor presentatie. De lokale Streamlit-runtime is 1.58.0, terwijl requirements 1.62.0 noemt. Geen bewijs voor live AI-kwaliteit, volledige bronbinding in validatie, duurzaam opslaan/herladen, export, semantisch herstel of werking van een geïnstalleerde release. De volledige unitgate bevat bestaande waarschuwingen, skips en xfail; dit zijn geen extra geslaagde controles.

Het algemene CON-02-oordeel zonder cijfer, de actieve broninhoudelijke evaluator, bronversies, historische beoordelingen en gedeelde gates blijven afzonderlijke implementatieonderdelen. DEF-606-volgorde blijft DEF-464 → DEF-624/677 → DEF-638; maximaal één herstelpoging staat al vast, CON-02-activatievoorwaarden nog niet.

## Bestandsbinding

Goedgekeurde patch SHA256: `7ac506b13c23c683a9d661986e0c729e020f72d6ad0aee9bbfe3a27aac2fd0ae`.

- `src/ui/handlers/definition_generation_handler.py`: `d10665e34f5d004a3691f92d47c9391ee64208f5d8bbe47d159bf11c9c33609a`
- `src/services/orchestrators/definition_orchestrator_v2.py`: `9831c2efd78f9e840c09bcd83ee643544501d99f9721294c41939471c32ecd8e`
- `src/ui/components/sources_renderer.py`: `db986792f2321f95ece75adad9ddbbea2228fa2636f7298b827f981d46cb935b`
- `tests/unit/ui/test_def743_document_selection.py`: `3ea30b59c0214982b2e4464dd3646fe7f163d7f12da920c6f7177564ee44d65a`
- `tests/unit/services/orchestrators/test_def743_source_transport.py`: `9ac978f7e4c9b317e01a4ffaa31e4ece671c266c42cc608f04a8e20d2174e447`
- `tests/unit/ui/test_def743_sources_presentation.py`: `6f1612a7fa74b84cdefa3baa46ee9cf1c176178b022d4ffd51d2c0b4eafaf38a`
