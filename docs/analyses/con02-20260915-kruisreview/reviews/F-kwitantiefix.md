# DEF-743 pakket F — kwitantiekanaal-fix (Codex-kwaliteitsreview P2) — rapport

Status: **2026-09-15 19:50 CEST — Claude Code CLI, pakket F. Bevroren na dit rapport.**
Scope: uitsluitend `src/services/source_proposal_service.py` en
`tests/unit/services/test_def743_voorstelworkflow.py` (manifest §5). Geen C/D/UI-bestand
aangeraakt; andere F-bestanden onveranderd t.o.v. `/tmp/DEF-743-quality-F-hashes.log`.

## 1. Bevinding (`/tmp/DEF-743-codex-quality-F-result.md`)

Trigger: geldig gebonden semantische fail met uitvoerbare negatieve claim, maar een misvormd
kanaal in `source_receipt`, bv. `{"status":"none","channels":{"rag":[{"supplied":1,"used":0}]}}`.
Vóór de kwaliteitsconversie stopte dit pad met een exceptie vóór reservering; na de conversie
normaliseerde `_als_mapping(k)` het kanaal tot `{}` ⇒ 0/0 ⇒ `_transportverlies` False ⇒
`defective_definition` ⇒ reservering + modelaanroep (poging verbruikt).

## 2. Fix (lokaal, fail-closed; geen transportcontract-herschrijving)

- `_kanaaltelling(kanaal, veld) -> int | None`: geldig = `int`, geen `bool`, ≥ 0 (E-kwitantie v1
  schrijft `supplied`/`used` als `int`); bool/negatief/tekst/float/None/ontbrekend ⇒ None.
- `_kwitantiekanalen(receipt) -> (tellingen, misvormd)`: geen kwitantie of `channels` afwezig
  (None) ⇒ geen transportinformatie (ongewijzigd); `channels` aanwezig maar geen dict ⇒ misvormd;
  per kanaal: geen dict of ongeldige telling ⇒ naam in `misvormd`; anders exacte tellingen.
- `_transportverlies(tellingen, status)`: exact de bestaande semantiek op de geldige tellingen
  (`geleverd and not gebruikt and status != pass`).
- `_kwitantiediagnose(receipt, status)`: `misvormd` ⇒ **nieuwe oorzaak
  `OORZAAK_KWITANTIE_ONGELDIG = "invalid_receipt"`** (`Diagnose(..., False, ...)`, bevinding
  "misvormd kwitantiekanaal: <naam>") — vóór `reserve_source_proposal` en vóór elke
  modelaanroep; anders transportverlies zoals voorheen; anders None. Aangeroepen op dezelfde plek
  in `_diagnose_zonder_bevinding` (na storing → geen bronnen/dienst → stale → onderdelen zonder
  basis), dus de branchvolgorde en het max-één-reserveringsgedrag zijn ongewijzigd.
- `_OMSCHRIJVING[OORZAAK_KWITANTIE_ONGELDIG]`: "onleesbare brontransportkwitantie … geen fout in
  de definitiezin en geen bewijs van transport; herstel of hertoets eerst; de ene poging blijft
  beschikbaar." `__all__` uitgebreid met het label.
- Niet gewijzigd: AI-kwitantie/afkapbewijs (`assessment_receipt`, C §5a), deskundige-
  correctiepaden, claimconflict-P2, geldige-lege-kanalen- en geen-kwitantie-semantiek,
  transportverlies bij geldige tellingen (F8).

Bewuste keuze, expliciet gemeld: een *aanwezig* `channels`-veld dat geen dict is, wordt nu óók
als onleesbaar geblokkeerd (voorheen stil tot `{}` genormaliseerd — al vóór de conversie).
Dat is dezelfde lokale regel ("aanwezig maar onleesbaar ⇒ stoppen"), geen bredere herziening.

## 3. TDD-bewijs

- **RED** — `/tmp/DEF-743-quality-F-receipt-red.log`: tests toegevoegd; in het product alleen
  het oorzaaklabel + omschrijving aanwezig (geen gedragswijziging, diagnose ongewijzigd):
  **9 FAILED** — de reviewer-trigger ⇒ `proposed` (reservering + modelaanroep), bool/tekst-
  tellingen ⇒ stil gecoerceerd naar `transport`, negatief/float/None/ontbrekend/geen-dict/
  `channels`-lijst ⇒ `proposed`; de twee geldige-kwitantiecontroles en F8 slaagden.
- **GREEN** — `/tmp/DEF-743-quality-F-receipt-fix.log`: `test_def743_voorstelworkflow.py`
  **65 passed, 0 failed, pytest exit 0** (54 + 11 nieuw).

Nieuwe regressies (end-to-end met echte `DefinitionEditRepository`/SQLite, D-adapter levert de
kwitantie via `get_contractvelden`):
- `test_misvormd_kwitantiekanaal_blokkeert_voor_reservering` — de exacte trigger ⇒ `blocked`,
  `cause == invalid_receipt`, `proposal_possible False`, bevinding noemt `rag`, `proposal_id`
  None, 0 modelaanroepen, `get_source_proposals() == []`, **recordversie ongewijzigd**.
- `test_misvormde_kanaaltelling_wordt_niet_tot_nul_gedwongen` (7 varianten: bool, negatief,
  tekst, float, None, ontbrekende telling, kanaal geen dict; naast een geldig `web`-kanaal) ⇒
  `blocked`/`invalid_receipt`, 0 aanroepen, geen voorstelrecord.
- `test_channels_zelf_misvormd_blokkeert_ook` — `channels` als lijst ⇒ idem.
- `test_geldige_kwitantie_met_lege_kanalen_laat_voorstel_toe` — geldige 0/0-kanalen (zoals E
  schrijft) ⇒ `proposed`, `defective_definition`, precies 1 aanroep, voorstelrecord `proposed`.
- `test_geldige_kwitantie_met_werkelijk_gebruik_laat_voorstel_toe` — 2/2 ⇒ `proposed`, 1 aanroep.
- Bestaand en groen gebleven: `test_f8_kwitantie_zonder_werkelijk_gebruik_is_transportverlies`
  (1/0 ⇒ `transport`, geen reservering), positieve controle zonder kwitantie ⇒ `proposed`.

## 4. Kwaliteitspoorten (`/tmp/DEF-743-quality-F-receipt-fix.log`)

- pinned Ruff 0.16.5 normaal (projectconfig, product + test): **exit 0**.
- pinned Ruff 0.16.5 expliciete complexiteitscheck op `source_proposal_service.py`: **0
  bevindingen, exit 0** (de tussenstap met 7 returns in `_diagnose_zonder_bevinding` is met
  `_kwitantiediagnose` opgelost; geen `noqa`).
- pinned mypy 2.3.1 `src/ --check-untyped-defs`: **Success, 387 bestanden, exit 0**.
- Black (originele venv): exit 0.
- Niet opnieuw gedraaid: de 292-suite (alleen de diagnosehelper en de proposal-workflowtests zijn
  gewijzigd; root draait de volledige unit-/coverage-gate op de stabiele eindstand).

## 5. Hashes — `/tmp/DEF-743-quality-F-receipt-hashes.log`

```text
42f8c2e870ce84cf8ecf0a08719a505a091880f8261ee25c2605d8cba553d672  src/services/source_proposal_service.py
c1598d670d285cd50f222eeeb61e9c6ffdfe2eab957b77e30c4dc1d1aec39585  tests/unit/services/test_def743_voorstelworkflow.py
```

Alle overige F-bestanden: ongewijzigd t.o.v. `/tmp/DEF-743-quality-F-hashes.log`. Geen
config/baseline/deps/hooks/security gewijzigd; geen `noqa`/`type: ignore`/`Any`-casts; geen
deletes/commit/push/WIP; hulpscripts `/tmp/DEF-743-quality-F-receipt{1,2,3}.py` documenteren de
mechanische vervangingen. Bevroren.
