## Uitkomst: één P2-regressie in de kwaliteitsdelta

### P2 — Ongeldig kwitantiekanaal wordt stilzwijgend nulgebruik

**Locatie:** [source_proposal_service.py:264](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:264).

**Trigger:** een opgeslagen, geldig gebonden semantische fail met uitvoerbare negatieve claim, maar een misvormd kanaal in `source_receipt`, bijvoorbeeld:

```json
{"status":"none","channels":{"rag":[{"supplied":1,"used":0}]}}
```

Vóór de extractie stopte dit pad met een fout vóór reservering. Nu verandert `_als_mapping(k)` de niet-lege lijst in `{}`. Beide tellingen worden nul, `_transportverlies` retourneert `False` en de diagnose kan doorgaan als `defective_definition`.

De opslagadapter bewaart deze JSON-vorm; F geeft haar ongewijzigd door aan de diagnose. Vervolgens kan [definition_edit_service.py:943](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:943) de ene duurzame poging reserveren en het model aanroepen.

**Impact:** onleesbare transportinformatie wordt behandeld alsof geen transportprobleem bestaat; een eerder blokkerende fout verbruikt daardoor alsnog de voorstelpoging.

**Gerichte correctie:** laat een aanwezig, misvormd kanaal expliciet blokkeren vóór reservering/modelaanroep. Normaliseer dit niet naar lege tellingen. Voeg een regressie toe die ongewijzigde versie, geen voorstelrecord en nul modelaanroepen controleert.

Statisch vastgesteld; dit grensgeval is niet uitgevoerd. Dit betreft de nieuwe F-conversie, geen heropening van D.

## Gesloten en behouden

- **Eerdere claimconflict-P2 gesloten:** identieke tekst/aspect/bron met tegengestelde steun blokkeert vóór reservering. Vier nieuwe regressies controleren conflict, normalisatie, consistente verschillende claims en de afzonderlijke deskundige negatieve correctie.
- Overige bekeken extracties behouden branchvolgorde, bewijsbinding, passageafkapping, AI-routering, versieoverdracht, transactieverantwoordelijkheid, widgetkeys en geïnjecteerde repositories.
- Geen verdere P1/P2-bevindingen in deze delta. Onopgeslagen Apply en actuele reviewreplay blijven gesloten; geen nieuw kwaliteitstotaal.

## Bewijs en grenzen

Vergeleken met de exacte prequality-kopieën; hun hashes gecontroleerd tegen `/tmp/DEF-743-prequality.json`.

**Zelf geen tests/imports/lint uitgevoerd.** Het nieuwe [testlog](/tmp/DEF-743-quality-F-tests.log) bevat **292 afzonderlijke PASSED-regels**, exit 0, inclusief de huidige AppTest-hash. Het oude 260-log is niet hergebruikt.

[Mypy-log](/tmp/DEF-743-quality-F-mypy.log): 387 bestanden zonder fouten, exit 0. [Lintlog](/tmp/DEF-743-quality-F-lint.log): gewone Ruff/Black-checks exit 0; expliciete complexiteitscheck behoudt 42 bestaande meldingen en exit 1.

**Geen drift:** acht productbestanden, vijf test/fixturebestanden en de gelezen rapport-/logbestanden hadden gelijke begin- en eindhashes. Geen expertacceptatie of story-Done; de gecombineerde rootgate blijft afzonderlijk.

## Eigen SHA-256 — begin = einde

```text
59cf9ed421d7c65c4a9da7a8a69aad96b4abaa95b1062b5c89a05be16c21da7e  src/services/source_proposal_service.py
d13de680beda8d2ab857ac4b497b62c32d5943900721c67fae0b6e771980be59  src/services/definition_edit_service.py
5e17dffc6f458f05449d655f9a4604a503d44f3f542a8749a1a01863955622a2  src/services/definition_workflow_service.py
b0faf6d12e6299eb3fc60f88ef95de13d1d1e7bb8fdee2805f49a48237926963  src/ui/components/definition_edit_tab.py
dd97eba5e7906aafa8caf48dfbcdc44dc12ec143f64a01720018fe9c05d922d2  src/ui/components/expert_review_tab.py
e87db806bf43e16bb64d438be691d4cb35947ee10d9a442cf0c778f133b3208a  src/ui/components/sources_renderer.py
e17d1333e267511227ba2a5340a47b5b8b8557646951144e8fb4520a1fdce360  src/ui/components/validation_view.py
98199b8a6027c56dec4177f511b9f79d1cc03b48bfaadb606886d1a4027141ce  src/ui/handlers/definition_generation_handler.py
ab2f30277d11c483fcd7ecd2223c55de5a251c40cd31f2b8b06935fd68c2dfeb  tests/fixtures/def743_fakes.py
451da52b66091aa37f14be79d0b18da70e2606903ef8cfa78b05827b20ff1e66  tests/unit/services/test_def743_editor_pariteit.py
d1700b106ac74716fe78cecf031f9682f6e9298af4d19ccf3a96a7d0ef9b374d  tests/unit/services/test_def743_voorstelworkflow.py
0ad0b497e2753ac94938a6d4dda0346410401492773ce6748ac035d7d43efafc  tests/unit/ui/test_def743_editor_ui.py
722a3451b9cc0a5d44f72ca92e50f68a9543e48b69e5bfdb03e4f31d92572761  tests/unit/ui/test_def743_editor_apptest.py
```

**Gecontroleerde bewijsbestanden, eveneens begin = einde:**

```text
6292cde5f189e072369b2b1c6f7a880d40cb6d19fa53e6f363079c45dc225c14  /tmp/DEF-743-quality-F-report.md
746296342ba10b3ff44f819c878c4ab10ff9e886e41b599d21a9b74711694d56  /tmp/DEF-743-quality-F-hashes.log
54e3cd3f9cd561210d3329409d2039307e6d14065398c4aab465088853568d5a  /tmp/DEF-743-quality-F-tests.log
03e8d6d717fe8487b7caedf2e6b1a0375d1f7b20d5a25e401979a9044d24c9f3  /tmp/DEF-743-quality-F-mypy.log
bd2724940c6df73b95805a718f58bd7a0bae399e40f78bbeba1920cbece76af6  /tmp/DEF-743-quality-F-lint.log
```