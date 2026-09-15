# DEF-743 — reviewfix P2 `_verzonden_bron` (eager hash vóór prefixguard) — 15-09-2026

**Bron:** `/tmp/DEF-743-codex-quality-C-result.md` (één resterende P2).
**Scope:** uitsluitend `src/domain/sources/contract.py` en de bestaande kwitantiematrix
`tests/unit/validation/test_def743_source_assessment_service.py::test_replay_weigert_gemanipuleerde_beoordelingskwitantie`
(C-eigendom; dáár leeft de receipt-manipulatiematrix, niet in `test_def743_broncontract.py`).
Gestart pas nadat `/tmp/DEF-743-final-v2-coverage.exit` bestond (inhoud `2`). Geen wijziging aan cap,
hashformaat, herkomstvelden, beveiliging, andere kwaliteitsdelta's, config, baselines of dependencies;
geen suppressies.

## Bevinding en fix

In de kwaliteitsrefactor berekende `_verzonden_bron` de UTF-8-hash van `content` binnen de eager
`_eerste_reden`-tuple, dus óók wanneer de prefixcontrole (`inhoud != passage[:grens]`) al faalde. Bij een
los surrogaatteken (`"\ud800"`, geldige Python-tekst, niet UTF-8-codeerbaar) gaf dat een
`UnicodeEncodeError`; `beoordeel_bronbasis` ving die defensief af als `"beoordeling onleesbaar"` en
verloor daarmee de specifieke kwitantiereden én de modelherkomst (status/model/provider → `None`).

Fix (`contract.py`, `_verzonden_bron`): de keten is gesplitst in een eerste, hash-vrije guard
(aanwezig → oorspronkelijke hash → inhoud is tekst → exacte prefix) die bij falen direct de reden
teruggeeft, en pas daarna de tuple met hash → afkapmarkering → bronversie. Dit is exact de oorspronkelijke
(pre-quality) volgorde: elke feilbare operatie (`encode`/`sha256`) komt ná de prefixacceptatie. Meldingen,
uitgangen en het `replace(bron, passage=inhoud)`-resultaat zijn ongewijzigd. Complexiteit: 4 returns,
geen nieuwe bevinding.

Audit van de overige `_eerste_reden`-tuples op feilbare operaties: `_bindingsafwijzing`,
`_valideer_verwijzing`, `_valideer_correctiebewijs` (`vind_citaat` op `""` → `False`, geen exception),
`_algemene_reviewafwijzing` (`_versieconflict` is puur), `_gezag/_verwijzing_onderbouwing_ontbreekt`
(iteratie over lege lijst raakt niets) — alle condities puur en exceptievrij; `_valideer_correctie` was al
sequentieel. Geen andere plek waar eager evaluatie een exception naar voren haalt.

Grens (pre-existent, ongewijzigd, buiten dit fix): een los surrogaat in de **canonieke passage zelf** raakt
`bereken_inhoudshash` al bij canonisatie (`normalisatie.py`), vóór elke kwitantiecontrole — dat was in
de pre-quality code identiek en is geen onderdeel van deze bevinding.

## RED → GREEN

- **RED** (`/tmp/DEF-743-quality-C-receipt-red.log`, exit 1): nieuwe matrixmutatie `inhoud_los_surrogaat`
  (`content = "\ud800"`, hash bewust ongewijzigd, verder geldige kwitantie) faalt op de bestaande
  assertie `"kwitantie" in reason` met `'beoordeling onleesbaar'`; het log toont de
  `UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800'` uit `contract.py`.
  De 7 bestaande mutaties slaagden (1 failed, 7 passed).
- **GREEN** (`/tmp/DEF-743-quality-C-receipt-green.log`, exit 0): 8 passed.
- Toegevoegde asserties (gelden voor álle mutaties): reden ≠ `"beoordeling onleesbaar"`, replay behoudt
  `status == "assessed"`, `model`/`provider` == `attribution` van de beoordeling. Voor de surrogaatmutatie
  bovendien direct `valideer_beoordeling(...)` → `({}, samenvatting)` met `applied is False`, reden exact
  `"beoordelingskwitantie: verzonden inhoud van doc:wet-11 is niet de canonieke passage tot de afkapgrens 300"`
  en behouden `model`. Nooit een exception, nooit positief.

## Overig bewijs

- Gerichte C-tests (11 bestanden): `/tmp/DEF-743-quality-C-receipt-targeted.log` — **729 passed**, exit 0
  (`.exit`). Geen bredere 2170-run: de kwitantiematrix plus de C-set dekken de wijziging (één functie in
  `contract.py`).
- Lint/typen (`/tmp/DEF-743-quality-C-receipt-lint.log`): Black `--check` exit 0; gepinde ruff 0.16.5 normaal
  exit 0 (beide bestanden); gepinde ruff `--select C901,PLR0911,PLR0912,PLR0915` op `contract.py` exit 0;
  gepinde mypy 2.3.1 `--check-untyped-defs` op `contract.py`: "Success", exit 0.
- Complexiteitsratchet (gepind, volledige boom) na deze fix: findings=194 vs baseline 201 (geen groei uit
  deze wijziging; de daling t.o.v. 206 komt van bestanden buiten mijn scope).
- Hashmanifest (2 bestanden): `/tmp/DEF-743-quality-C-receipt-hashes.log`
  - `7846cdb8eebaf57ade7ef251c9a81aaa9146384d03f21cfd2835eaf40845485b  src/domain/sources/contract.py`
  - `e51affe8fc51ec180aebf82c907f3fa612f9e25a8d843d9cf0652d25d79716ce  tests/unit/validation/test_def743_source_assessment_service.py`
- Vóór-kopieën voor de reviewdelta: `/tmp/DEF-743-quality-C-receipt-contract-before.py`,
  `/tmp/DEF-743-quality-C-receipt-test-before.py`. Delta: contract.py +12/−2 (docstring + splitsing),
  test +29 regels.

Let op: `contract.py` heeft hiermee een nieuwe hash t.o.v. `/tmp/DEF-743-quality-C-hashes.log`; de andere
vier bestanden uit dat manifest zijn ongewijzigd. Root doet de finale gate op de actuele hashes.

Bevroren na dit rapport.
