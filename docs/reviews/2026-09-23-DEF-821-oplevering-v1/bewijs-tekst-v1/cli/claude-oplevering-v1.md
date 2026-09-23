AC1–AC7 zijn geïmplementeerd en lokaal gecontroleerd. `make test` gaf exit 0 (7046 passed, 75 skipped, 1 xfailed) en `make lint` gaf exit 0. Er zijn geen commits en geen live modelaanroepen gedaan. De Codex-review en de live effectproef (AC8) staan nog open.

## Wat er veranderd is
- **Nieuwe uitkomst** (`src/services/modelantwoord.py`): naast de definitie en het ESS-02-conflict herkent de parser nu een aparte melding: eerste regel `BETEKENISGROND ONTBREEKT:`, gevolgd door precies één JSON-object met alleen `ontbrekende_grond` en `vraag`. Lezingen of bronverwijzingen zijn niet nodig. Beide soorten melding in één antwoord geeft `gemengde_melding`. Een dubbele melding, extra of lege velden, of markup rond de payload faalt veilig met een vaste foutcode zonder modeltekst.
- **Prompt:**
  - De ESS-04-instructie in `json_based_rules_module.py` is nu exact de G2-v5-tekst.
  - `definition_task_module.py` heeft een tweede uitzonderingscontract. Daarin staat uitdrukkelijk dat kwalitatieve criteria, ontbrekend gevalsbewijs, een ontbrekende categorie, ontbrekende bronsteun en een onbesliste ESS-03-eenheidsgrens géén reden voor de melding zijn.
  - "Enige uitzondering" is verdwenen. De categorieregel en de slotopdracht laten de melding nu toe.
  - Het datakopje in `context_awareness_module.py` is neutraal gemaakt ("…bedoelde betekenis door de gebruiker").
- **Keten:** de orchestrator takt de melding af vóór voorbeelden, opschoning, validatie en opslag, als `error_type="betekenisgrond_ontbreekt"` met `success=False`. Adapter en `UIResponseDict` geven de melding compleet door.
- **UI:** de sessiehulp (`betekenisconflict.py`) kent nu twee soorten open verzoek, met hetzelfde antwoordmechanisme (gebonden aan de invoer en eenmalig). De handler toont een eigen melding. De tab toont grond, vraag en het verzonden antwoord alleen met `st.text`, dus HTML of Markdown uit modelvelden wordt niet uitgevoerd.
- **Aangepaste bestaande test:** één assertie in `tests/unit/services/prompts/test_def766_ess03_promptnorm.py` borgde de "enige uitzondering" die AC1 juist opheft. Ze toetst nu dat ESS-03 niet stil wordt verbreed.
- **Diff:** 11 getrackte bestanden (+422/−68, `git diff`-sha256 `5e50f4b6…36be`) plus 8 nieuwe bestanden.

## Tests (RED eerst, daarna GREEN)
Nieuwe tests in `tests/unit/…`:
- `services/test_def821_modelantwoord.py`: parser, inclusief markup en gemengde of misvormde payloads.
- `services/prompts/test_def821_ess04_promptcontract.py`: exacte G2-tekst, uitvoercontract, ESS-02-tellingen, rijkste prompt onder de 60K-kap, ESS-04-regelrecord ongewijzigd.
- `services/orchestrators/test_def821_ontbrekende_grond_keten.py`: aftakking in de orchestrator.
- `ui/test_def821_ontbrekende_grond_ui.py`: adapter, tab, en een keten met handler, echte repository en tijdelijke SQLite. Bewijst nul opslag bij de melding, daarna antwoord, hergeneratie, opslag en readback; gewijzigde invoer maakt het antwoord ongeldig.
- `ui/test_def821_ontbrekende_grond_apptest.py`: een echte Streamlit-AppTest met een injectiepayload.

## Effectproef-harness (`scripts/testing/def821_effectproef.py`)
- **Basis:** de echte commit `b687c1615`, via `git archive` in de uitvoermap; er wordt geen branch geraakt.
- **Nieuw:** een kopie van de werkboom.
- Elke versie draait in een eigen subprocess met alleen haar eigen `src` en een eigen werkmap, zodat caches gescheiden blijven.
- **Route:** `DefinitionOrchestratorV2.create_definition` met de echte PromptServiceV2, SecurityService, CleaningService, validatie en repository (verse SQLite), en `AIServiceV2(use_cache=False)` met `ModelRouter`. SDK-retries staan op 0.
- **Uitgeschakeld, gelijk voor beide versies:** synoniemen, web lookup, RAG, voorbeelden en CON-02-bronbeoordeling. UI-handler en adapter vallen buiten de lus.
- **Standaard offline:** bouwt alleen de volledige prompts en weigert als model of instellingen per versie verschillen of als de verwachting in de prompt staat.
- **`--live`:** maximaal 32 aanroepen; een groter aantal wordt vóór elke aanroep geweigerd. Volgorde is tegengebalanceerd (h1 basis→nieuw, h2 nieuw→basis). Per aanroep worden de volledige prompt, alle berichten, model en instellingen, de ruwe uitvoer, de appuitkomst en opslag/readback vastgelegd, plus een classificatie met de nieuwe parser. Secrets worden uit alles wat naar schijf gaat verwijderd.
- **Casusschema** (JSON-lijst, `{"casussen": [...]}` of JSONL; `--schema` toont het):
  - Verplicht: `id`, `begrip`, `verwachting`.
  - Optioneel: de drie contextlijsten, `ontologische_categorie`, `documenten` (`doc_id` en `snippet`), `betekenisverduidelijking`, `verwachte_uitkomst` (`definitie`, `ontbrekende_grond`, `conflict` of `onbeslist`), `herkomst`.
  - Onbekende sleutels worden geweigerd.
- D1–D6 staan bevroren in `scripts/testing/def821_ontwikkelcasussen.json`, met de fictieve betekenisgrond als expliciete documentpassage.
- De offline run gaf exit 0: prompts van ongeveer 27K (basis) en 29,5–30K tekens (nieuw), model `claude-opus-5` met temperature 0.1 voor beide versies gelijk.

## Openstaande punten
1. **Logs staan in `/tmp/def821-bewijs/`** (met `INDEX.md`), niet in `.claude/def821-bewijs`: schrijven daar werd door de permissielaag geweigerd. Kopieer ze voordat `/tmp` wordt opgeschoond.
2. **Symlink aangemaakt:** `.claude/hooks` in de werkboom wijst naar de hookmap van de hoofdrepo. Zonder die link faalde de Write-hook; het pad is git-ignored.
3. **Injectierisico ESS-02:** de bestaande conflictweergave toont modelvelden nog via `st.markdown`. Ik heb dat bewust niet aangeraakt omdat de DEF-751-AppTest daarop assert. Dit vraagt een eigen besluit.
4. **Kopje en ESS-02-live-effect:** het neutrale verduidelijkingskopje raakt ook het ESS-02-pad. De unittests zijn groen, maar het effect op echte ESS-02-modeluitvoer is niet live gemeten.
5. **Scopegrens tegenspraak:** tegenspraak over een criterium (bijvoorbeeld twee verschillende grenzen) valt onder de nieuwe melding als "ontbrekende keuze". Tegenspraak over de betekenislaag blijft het ESS-02-conflict. Dat volgt uit mijn lezing van G2 en moet bij de review worden bevestigd.
6. **Twee heldout-cases** van de coördinator ontbreken nog. Samen met D1–D6 zijn dat 8 × 2 × 2 = 32 aanroepen, precies het maximum.