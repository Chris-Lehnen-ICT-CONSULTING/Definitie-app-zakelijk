# DEF-743 pakket F — kwaliteitsronde (P2-eindreview + complexiteit/mypy) — rapport

Status: **2026-09-15 19:40 CEST — Claude Code CLI, pakket F. Bevroren na dit rapport.**
Poorten vooraf gecontroleerd: `/tmp/DEF-743-final-make-test.exit` (aanwezig, inhoud `2`; root:
alleen een D-fixturefout) en `/tmp/DEF-743-codex-F-final-result.md` (aanwezig, één P2). Alle
claims hieronder zijn gebonden aan `/tmp/DEF-743-quality-F-hashes.log` (8 product-, 5 testbestanden).

## 1. Functionele sluiting — Codex-eindreview P2 (tegenstrijdige claims)

**Trigger (reviewer):** gebonden AI-beoordeling, `semantic_support=fail`, geverifieerd bewijs,
twee claims met identieke `text`/`aspect`/`source_id` maar `supported: true` én `false`;
`_negatieve_claims` selecteerde alleen de negatieve en F reserveerde de ene poging.

**Fix (`src/services/source_proposal_service.py`):** `_claimsleutel` (genormaliseerde tekst,
aspect, bron-id) + `_tegenstrijdige_claims(claims)`; in de AI-steundiagnose ná het bewijs- en
afgewezen-pad en vóór `_negatieve_claims`: conflict ⇒ `Diagnose(OORZAAK_AI_ONZEKER, False, …)`
met bevinding "tegenstrijdig beoordeeld: <tekst>" ⇒ `blocked` **vóór** `reserve_source_proposal`
(geen voorstelrecord, geen modelaanroep, poging blijft beschikbaar). Het afzonderlijke pad van
een deskundige negatieve correctie (`steun.field == "source_review"`, eigen gebonden bewijs) gaat
hieraan vooraf en is ongewijzigd.

**Regressies (`tests/unit/services/test_def743_voorstelworkflow.py`, +4 ⇒ 54):**
- `test_tegenstrijdige_claims_verbruiken_de_poging_niet` — conflict ⇒ `blocked`,
  `cause == ai_uncertainty`, `proposal_id None`, 0 modelaanroepen, `get_source_proposals() == []`,
  versie ongewijzigd.
- `test_tegenstrijdigheid_telt_ongeacht_volgorde_en_witruimte` — volgorde/hoofdletters/witruimte.
- `test_consistente_negatieve_claim_naast_andere_positieve_claim_is_uitvoerbaar` — legitieme
  controle: positieve claim over een ándere tekst + (dubbele) negatieve claim ⇒ `proposed`,
  1 aanroep.
- `test_deskundige_negatieve_correctie_blijft_los_van_claimconflict` — expertcorrectie naar fail
  met eigen bewijs ⇒ `proposed` ondanks tegenstrijdige AI-claims.

**RED-bewijs:** `/tmp/DEF-743-quality-F-red-p2.log` — tests toegevoegd, product ongewijzigd:
2 FAILED (`proposed` i.p.v. `blocked`), 2 controles passed. Daarna fix ⇒ 54/54.

## 2. Complexiteit — nieuwe bevindingen in F-scope: 20 ⇒ 0

Methode: pinned Ruff 0.16.5, `--select C901,PLR0911,PLR0912,PLR0915`, HEAD-kopieën van de
8 F-bestanden (`git show HEAD:…`, projectconfig) vs. werkboom, per functie vergeleken
(`/tmp/DEF-743-quality-F-complexity-head.txt` / `-now.txt`). HEAD: 42 bevindingen; werkboom
vóór deze ronde: 62 (+20 nieuw); **werkboom nu: 42 — per bestand+code identiek aan HEAD, alle
nieuwe DEF-743-functies onder de drempels.** `source_proposal_service.py` bestaat niet op HEAD
(6 nieuwe bevindingen ⇒ 0).

| Bestand | Nieuwe bevinding(en) vóór | Mechanische helper-extractie (zelfde volgorde/fail-closed) |
| --- | --- | --- |
| `source_proposal_service.py` | `diagnose_bronbasis` C901 18 / PLR0911 17 / PLR0912 17; `controleer_voorstel` C901 15 / PLR0911 9 / PLR0912 14 | `_als_mapping`, `_bevindingen`, `_storingsdiagnose`, `_transportverlies`, `_diagnose_zonder_bevinding` (storing → geen bronnen/dienst → stale → onderdelen zonder basis → transportverlies), `_diagnose_tekstgebrek` (F1: niet-tekstueel → correctie → AI), `_diagnose_correctie`, `_afgewezen_steunclaims`, `_diagnose_ai_steun` (afgewezen → geen bewijs → **tegenstrijdig (P2)** → geen claim → tekortkoming); `_bronwoordcontrole` + `_contextcontrole` (bronwoord vóór context, zoals voorheen; `or`-keten omdat een reden nooit leeg is) |
| `definition_edit_service.py` | `vraag_verbetervoorstel` PLR0911 8; `_technische_fout_in_validatie` PLR0911 7; `pas_voorstel_toe` C901 12 / PLR0911 12 | `_actievoorbereiding` (actor → record → `_weergavecontrole`; geeft `DefinitieRecord | dict`), `_reserveringsweigering`, `_beoordelingsfout`, `_toepasbare_kandidaat` (bestaat → `proposed` → `stale_original` → kandidaattekst; geeft `str | dict`), `_hertoets_kandidaat` (geeft `Mapping | _Weigering`; `_Weigering` is een frozen dataclass zodat een weigering niet met een validatieresultaat te verwarren is). `apply_source_proposal` + `_clear_cache` blijven in `pas_voorstel_toe`, zelfde volgorde. |
| `definition_workflow_service.py` | `_con02_blokkades` C901 11 | `_gedekt_door_uitzondering(part, uitzondering)` (de twee `continue`-voorwaarden, letterlijk) |
| `expert_review_tab.py` | `_render_bronbasiscontract` C901 25 / PLR0912 24 / PLR0915 86 | `_toon_bronbasis`, `_toon_beoordelingsaanhef`, `_geen_bron_invoer`, `_verwijzing_invoer`, `_bronreview_vastleggen` (True ⇒ de weergave stopt, zoals de oorspronkelijke `return` in de knop-handler), `_verwijderknop_bronreview`. Widgetvolgorde, labels en keys (`con02_{id}_soort/_queries/_consulted/_conclusie/_motivering/_bron/_motivering_ref/_locator_<sid>/_accepted/_vastleggen/_verwijderen`, `_corr_*`) ongewijzigd. |
| `sources_renderer.py` | `_render_beoordeling_samenvatting` C901 12; `_render_bron_bewijs` C901 25 / PLR0912 26 / PLR0915 63 | `_render_beoordeeld_onderdeel`; `_render_canonieke_passage` (rol 2), `_render_beoordelingsinvoer` (rol 3 "Wat de beoordeling zag"), `_render_generatiekwitantie`, `_render_ai_oordeel_per_bron` — zelfde volgorde en teksten |
| `validation_view.py` | `_review_regels` C901 13 | `_correctieregel`, `_beoordelingsstatusregel`, `_beoordelingsregel` |
| `definition_generation_handler.py` | `_build_document_snippets` PLR0915 53 (C901 18 / PLR0912 17 gegroeid t.o.v. HEAD 14/13) | `_document_citation_label(doc, text, idx, matched_term)` (incl. "volledig document") ⇒ 14/13, exact de HEAD-waarden; statements < 50 |
| `definition_edit_tab.py` | geen nieuwe bevindingen (11 = HEAD 11) | `_plaats_klaargezette_tekst` (F2 pending-tekst) haalt `_render_editor` terug op de HEAD-waarden C901 17 / PLR0912 15 |

Bewust niet aangeraakt (pre-existing, niet-F): `revert_to_version`, `_validate_definition`
(al kleiner dan HEAD: 13/8/13 vs 17/8/17), `_format_timestamp`, `approve`, `_evaluate_gate`,
`render`/`_render_search_results`/`_save_definition`/`_track_changes`, de vier expert-tab
god-functies, `_render_sources_list`, `render_validation_detailed_list`,
`handle_definition_generation`. Restdelta binnen al gevlagde functies: `_render_editor` PLR0915
93 vs HEAD 92 (de helper-aanroep) en `render` PLR0915 60 vs 58 (de twee sectie-aanroepen
bronbasis/voorstel) — geen nieuwe bevinding, inherent aan de feature-bedrading.

## 3. mypy — F-scope 41 ⇒ 0; volledige `mypy src/ --check-untyped-defs`: 0

`/tmp/DEF-743-quality-F-mypy.log` — pinned mypy 2.3.1: **Success: no issues found in 387
source files, exit 0** (de C/E-fouten uit `/tmp/DEF-743-mypy-pinned.log` zijn door hun eigenaren
gesloten; F heeft die bestanden niet aangeraakt).

Echte vernauwing, geen onderdrukking (geen `type: ignore`, `cast`, `Any`-casts of zwakkere
runtimecontroles):
- `_als_mapping` / `_als_dict` (module-helpers met `isinstance`) vervangen het patroon
  `x.get(k) if isinstance(x.get(k), Mapping) else {}` dat mypy niet kon vernauwen
  (source_proposal_service, definition_edit_service, definition_edit_tab, sources_renderer,
  validation_view). Runtime identiek; waar de oude code `(x or {}).get(...)` deed op een
  niet-mapping zou die crashen, de helper geeft nu `{}` (strikt fail-safer, zelfde typecontract).
- `_steunbewijs` retourneert `list[Mapping[str, Any]]` voor claims (accurate annotatie).
- `vraag_verbetervoorstel`: `proposal_id`/`gereserveerde_versie` uit de reservering worden vóór
  de modelaanroep vernauwd; `reserved` zonder id/versie (onmogelijk onder het D-contract) valt
  in dezelfde weigering (`_reserveringsweigering`) — geen modelaanroep, geen nieuwe status.
- `_render_beoordelingsinvoer`: `and source_id is not None` in de kwitantietak (runtime-
  equivalent: `gezien` is alleen gezet bij een truthy `source_id`).
- `_actievoorbereiding`/`_toepasbare_kandidaat`/`_hertoets_kandidaat`: onderscheidbare
  retourtypen (`DefinitieRecord | dict`, `str | dict`, `Mapping | _Weigering`) i.p.v.
  optionele tuples.

## 4. Behoudsbewijs (contracten en gesloten reviewfixes)

- Alle eerdere regressies blijven groen: F1–F8, bevinding 1 (Apply bij onopgeslagen tekst, knop
  én handler, volledige AppTest incl. `stale_original` na Opslaan), bevinding 2 (replay tegen
  actuele opgeslagen review/versie), bevinding 3 (strikte negatieve claims), P2 (conflict),
  deskundige negatieve correctie, DEF-622-ketens, gate fail-closed.
- Geen wijziging in: bronkwitanties/vingerafdrukken/citaten/metadata, reviews/uitzonderingen/
  historie, geen auto-reparatie, max-één-reservering per generatie, expliciete Apply, widget-
  keys/labels/volgorde, geïnjecteerde repositories/DB.
- `/tmp/DEF-743-quality-F-tests.log` — **292 passed, 0 failed/error, pytest exit 0**
  (2026-09-15 19:39 CEST, op de hashes van §6): pariteit 12, voorstelworkflow 54, editor-UI 32,
  **AppTest 12 (opnieuw gedraaid op de definitieve bestanden — de eerder gemelde testdrift
  `82a029…` → `722a34…` was een docstring-aanvulling; hash nu `722a34…`)**, sources-presentation
  7, overige scoreweergave 8, def622_apptest_expert 11, vaststelconflict 44, koppelingen-export
  8, contextcontract 4, koppelingen-UI 5, guard-failclosed 62, generator-details 13,
  document_selection 16, snippets_docx 1, evicted_docs 3.
- `/tmp/DEF-743-quality-F-lint.log` — pinned Ruff normaal: exit 0; expliciete complexiteitscheck:
  42 bevindingen (= HEAD, per bestand+code identiek; script-exit 1 is de aanwezigheid van die
  pre-existing 42); Black: exit 0.
- Geen brede unit-gate gedraaid (root); geen C/D/E-bestand aangeraakt; geen baseline/config/hook/
  dependency gewijzigd; geen `noqa`/`type: ignore`/skip; geen symbolen hernoemd; niets
  verwijderd, gecommit of gepusht.

## 5. Opmerkingen voor root / reviewer

1. De eerste testrun na de proposal-service-refactor toonde 2 failures in
   `test_toepassen_*` door een tussenstaat van `validation_orchestrator_v2.py` (C,
   `_technische_blokkade` nog niet gedefinieerd); na C-oplevering groen. F-code ving die
   storing correct als `technical_error` met origineel intact.
2. `_render_editor`/`render` (pre-existing gevlagd) hebben +1/+2 statements t.o.v. HEAD door de
   feature-bedrading (§2); geen nieuwe bevinding.
3. Hulpscripts van deze ronde staan in `/tmp/DEF-743-quality-F-*.py` (edit-service, edit-service2
   [ongebruikt, vervangen door 3], edit-service3, workflow, validation-view, validation-view2,
   sources-renderer, expert, edit-tab, edit-tab2, handler) — alleen documentatie van de
   mechanische vervangingen; niet nodig voor de build.
4. Handover-bestanden van de pre-compact-hook (`.claude/handovers/2026-09-15_1913-*.md`,
   `WIP-snapshot.md`, sectie in `.claude/CLAUDE.md`) zijn niet verplaatst/verwijderd
   (coördinator-eigendom; geen deletes).

## 6. Hashes

Zie `/tmp/DEF-743-quality-F-hashes.log` (SHA-256, 2026-09-15 19:39 CEST). Bevroren.
