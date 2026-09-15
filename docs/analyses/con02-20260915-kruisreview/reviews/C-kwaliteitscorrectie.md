# DEF-743 — kwaliteitsfix pakket C (complexiteit + mypy), gedragsbehoudend — 15-09-2026

**Scope (toegewezen):** `src/domain/sources/contract.py`, `src/domain/sources/normalisatie.py`,
`src/services/orchestrators/validation_orchestrator_v2.py`,
`src/services/validation/source_assessment_service.py` en (smalle E-autorisatie)
`src/services/prompts/prompt_service_v2.py`. Geen testbestand gewijzigd; geen schema-, config-,
hook-, baseline- of dependencywijziging. Geen `noqa`, `type: ignore`, cast-naar-Any, skips of
hernoemingen om checks te omzeilen.

Tooling: gepind `/tmp/DEF-743-quality-venv` (ruff 0.16.5, mypy 2.3.1) voor ruff/mypy/ratchets;
projectvenv (`/Users/chrislehnen/Projecten/Definitie-app/.venv`) voor pytest en Black.
Vóór-kopieën van alle vijf bestanden staan in `/tmp/DEF-743-quality-{contract,normalisatie,vov2,sas,psv2}-before.py`
(de reviewer kan de refactoringdelta daar 1-op-1 tegen diffen).

## 1. Meetresultaat

| Gate | Vooraf (root) | Nu | Eigen scope nu |
|---|---|---|---|
| Complexiteitsratchet (`scripts/complexity_ratchet.py`, gepinde ruff) | 249 vs baseline 201 (+48) | **206** vs 201 (+5) — `/tmp/DEF-743-quality-C-complexity.log`, exit 1 | **0 bevindingen** in alle vijf bestanden (`/tmp/DEF-743-quality-C-complexity-owned.log`) |
| mypy (`src/ --check-untyped-defs`, gepind) | 66 fouten in 7 bestanden | **24** fouten in 3 bestanden — `/tmp/DEF-743-quality-C-mypy.log`, exit 1 | **0** (contract.py 3→0, prompt_service_v2.py 22→0) |

Alle 13 bevindingen die nu nog nieuw zijn t.o.v. de baseline liggen **buiten mijn scope** (pakket F):
`definition_edit_service.py` (C901 `pas_voorstel_toe`, PLR0911 ×2), `definition_workflow_service.py`
(C901 `_con02_blokkades`), `expert_review_tab.py` (C901/PLR0912/PLR0915 `_render_bronbasiscontract`),
`sources_renderer.py` (C901 `_render_beoordeling_samenvatting`, C901/PLR0912/PLR0915 `_render_bron_bewijs`),
`validation_view.py` (C901 `_review_regels`), `definition_generation_handler.py` (PLR0915). De 24 resterende
mypy-fouten zitten in `definition_edit_tab.py` (13), `sources_renderer.py` (9), `validation_view.py` (2) — F.
Die heb ik niet aangeraakt (eigendom van F).

Netto-effect op de ratchet vanuit mijn scope: alle nieuwe C-bevindingen weg **plus** drie pre-existente
bevindingen in `prompt_service_v2.py` op de basis-commit (`_collect_web_brons`: C901 14, PLR0912 13,
PLR0915 51 — zie het `@ basis`-blok in het owned-log) zijn mee opgelost doordat de webselectie nu in
helpers zit. Geen enkele oude bevinding is gegroeid.

## 2. Wat is gerefactord (per bestand) en waarom het gedrag gelijk is

Principe overal: dezelfde controlevolgorde, dezelfde eerste-tekortkoming-wint-semantiek, exact dezelfde
meldingsteksten, dezelfde fail-closed uitgangen; alleen de vorm (helpers) is anders. Alle geëxtraheerde
condities zijn puur en zonder bijwerkingen.

### `src/domain/sources/contract.py`
- Nieuw `_eerste_reden(controles)`: geeft de reden van de eerste falende `(faalt, reden)` in volgorde.
  Gebruikt waar alle condities puur en exceptievrij zijn (eager evaluatie verandert dan niets):
  `_bindingsafwijzing`, `_verzonden_bron`, `_valideer_verwijzing`, `_valideer_correctiebewijs`,
  `_algemene_reviewafwijzing`, en de twee bronlijst-helpers hieronder.
  Waar een conditie op ongehashbare invoer zou kúnnen raisen (`status not in _DEELSTATUSSEN` in
  `_valideer_correctie`) zijn bewust **sequentiële** helpers gebruikt (`_correctievorm`,
  `_correctiebewijseis`), zodat het korte-sluitgedrag van het origineel exact behouden blijft.
- Nieuw `_citaattekst(waarde)`: `str` of `""` — de mypy-narrowing voor `vind_citaat(...)` (was `Any | None`).
  `_verifieer_bewijs` en `_valideer_correctiebewijs` toetsen nu `citaat.strip()` i.p.v. `_tekst(citaat)`
  (identiek: `_tekst` = `strip()` op str, anders `""`); `str(citaat)` → `citaat` (was al str).
- `_positieve_onderbouwing_ontbreekt` (C901 12 / 12 returns) → dispatcher + `_gezag_onderbouwing_ontbreekt`,
  `_steun_onderbouwing_ontbreekt`, `_verwijzing_onderbouwing_ontbreekt`; teksten en volgorde
  (tegenspraak → geen toepasselijk/terugvindbaar → bewijs niet uit zo'n bron; claims: leeg → niet gesteund → ongebonden) ongewijzigd.
- `valideer_beoordeling` (C901 12 / 11 returns) → `_statusafwijzing` (unavailable/error/no_sources/onbekend)
  gevolgd door `_bindingsafwijzing` (contractversie → vingerafdruk → model) en daarna de `parts`-controle;
  `or`-ketening kortsluit dus dezelfde eerste reden. Samenvattingsvelden worden op dezelfde plek gevuld.
- `verzonden_passages` (C901 17 / 15 returns / 16 branches) → `_kwitantiegrens`, `_kwitantierecords`,
  `_verzonden_bron` (per bron: aanwezig → oorspronkelijke hash → inhoud is tekst → inhoud == passage[:grens]
  → hash van inhoud → afkapmarkering → bronversie). Eerste fout wint, `()` als resultaat; `replace(bron, passage=inhoud)` ongewijzigd.
- `_valideer_verwijzing` (7 returns), `_valideer_correctiebewijs` (8), `_valideer_correctie` (7): zelfde
  ketens via helpers; genormaliseerd bewijsitem ongewijzigd.
- `valideer_bronreview` (C901 12 / 12 returns) → `_algemene_reviewafwijzing` (type → accepted → actor →
  rationale → vingerafdruk → versiebinding) + `_typespecifieke_review` (correctie: `evidence` vervangen door
  gevalideerd bewijs + `applied_correction`; uitzonderingen: `accepted_exception` reference/no_source).
  `_canoniek(bronnen)` wordt, zoals eerst, pas na de algemene controles berekend.
- mypy 1276: `_pas_correctie_toe` maakt `dict(item)` per bewijsitem (was `Mapping`), passend bij
  `_bewijstekst(tuple[dict[str, Any], ...])`; inhoud gelijk.
- Cosmetisch afgedwongen door de gepinde ruff: ISC004 (impliciete concatenatie in tuples) → omhaakte strings;
  de meldingsteksten zijn karakter-voor-karakter gelijk gebleven.

### `src/domain/sources/normalisatie.py`
- `_locator` (C901 12) → `_metadata_locatordelen(metadata)` (pagina → `locator` dict gesorteerd op sleutel / tekst);
  volgorde legal.citation_text → citation_label/artikel_lid (dedup) → metadata → fallback `locator` ongewijzigd.
- `_basis_id` (7 returns) → expliciet → `_provider_id` (documents→`doc:`, rag→`rag:[doc:]chunk`) →
  kandidatenlijst url → doc → rag → `hash:`; identieke prioriteit en formaten.

### `src/services/orchestrators/validation_orchestrator_v2.py`
- `_beoordeel_bronnen` (7 returns) → module-helper `_technische_blokkade(aliasstatus, receipt, correlation_id)`
  die `(soort, melding)` geeft voor `source_alias_invalid` → `source_alias_conflict` → `receipt_error`
  (met dezelfde `logger.error`-regels) of `None`. Daarna ongewijzigd: geen bronnen → `None`; geen dienst →
  `unavailable`; `assessment_max_passage_chars`; assess; exceptie → `unknown`. `receipt` wordt nu vóór de
  aliascontrole uit de context gelezen (pure read), `kwitantiefout` wordt pas ná de aliascontroles aangeroepen.

### `src/services/validation/source_assessment_service.py`
- `structuurfout_modeluitvoer` (7 returns) → `_structuurfout_onderdeel(onderdeel, deel)`; zelfde meldingen.
- `assess` (8 returns) → `_voorcontrole` (receipt_error → receipt_mismatch → no_sources), cachepad
  ongewijzigd in `assess`, dan `_beoordeel_met_model` (prompt → aanroep → `_foutsoort` → parse →
  structuur → validatie → kwitantie → `_onthoud`). Beide `malformed_response`-uitgangen delen `_misvormd`
  (zelfde document + `raw_response_sha256`, niet gecachet). Attributie: `model` valt terug op
  `attributie_basis["model"]` (= dezelfde waarde als de vroegere lokale `model`).

### `src/services/prompts/prompt_service_v2.py` (E, smalle autorisatie)
- mypy (22×): `class _Correlatie(TypedDict)` met `input_index: int`, `supplied: str`; de drie
  `ref`-toewijzingen zijn nu `ref: _Correlatie = {...}` zodat `**ref` typegetrouw op de keyword-only
  parameters van `_omitted_record` landt. Geen wijziging van de signatuur van `_omitted_record`/`_used_record`.
- `_collect_web_records` (C901 15; op de basis al 14/13/51) → module-helpers `_web_sources`, `_web_omitted`,
  `_is_auth_web`, `_select_web_sources`, `_web_limits` en methode `_web_budget_loop`. Behouden:
  `indexed = list(enumerate(sources))` **vóór** selectie en sortering; `channel_disabled` voor alle bronnen
  bij uitgeschakeld kanaal; `not_selected` in aangeleverde volgorde; `include_all_hits`/`used_in_prompt`/
  fallback-alles; stabiele juridische sortering (auth eerst, -score, titel, url); relaxatie van budget bij
  `include_all`; luslogica `max_count` → `budget` → `empty_content` → `budget` (uitgeput); `format_bron`- en
  `_used_record`-argumenten letterlijk gelijk; dezelfde logregels.

## 3. Bewijs

- Tests (projectvenv, `-p no:cacheprovider -o addopts=""`):
  - eigen 11 C-testbestanden: 728 passed (eerdere run in deze sessie, geen skips);
  - brede gerichte run (domain, validation, orchestrators, prompts, `tests/unit/prompt`, alle DEF-743-tests van
    C/D/E/F, DEF-622 export-readback): `/tmp/DEF-743-quality-C-tests.log` — **2170 passed, 5 skipped,
    1 xfailed** (skips/xfail pre-existent, niet in DEF-743-tests), exit 0 (`/tmp/DEF-743-quality-C-tests.exit`);
  - offline kernjourney: `/tmp/DEF-743-quality-C-journey.log` — 3 passed, exit 0.
- Lint/typen op de vijf bestanden: `/tmp/DEF-743-quality-C-lint.log` — Black `--check` exit 0; gepinde ruff
  normaal exit 0; gepinde ruff `--select C901,PLR0911,PLR0912,PLR0915` exit 0; project-ruff (0.15.17) exit 0;
  gepinde mypy `--check-untyped-defs` op de vijf bestanden: "Success: no issues found in 5 source files", exit 0.
- Ratchets (gepind, volledige scope): `/tmp/DEF-743-quality-C-complexity.log` (206 vs 201, exit 1 — restant F),
  `/tmp/DEF-743-quality-C-mypy.log` (24 fouten in 3 F-bestanden, exit 1).
- Hashmanifest (alleen de vijf in deze taak gewijzigde bestanden): `/tmp/DEF-743-quality-C-hashes.log`.
- Diffomvang t.o.v. de vóór-kopieën: contract.py +427/−258, normalisatie.py +43/−28,
  validation_orchestrator_v2.py +42/−33, source_assessment_service.py +108/−32, prompt_service_v2.py +123/−81.

## 4. Niet gedaan / grenzen

- Geen wijziging aan F-bestanden (de resterende +5 complexiteit en 24 mypy-fouten), geen baseline-aanpassing.
- Geen nieuwe tests: het is een gedragsbehoudende refactor; de bestaande RED→GREEN- en mutatietests van C
  blijven de norm en slagen ongewijzigd.
- `make test`/volledige unitgate en de finale ratchetbeslissing blijven bij root.
- Bevroren: na dit rapport geen verdere edits in mijn scope.
