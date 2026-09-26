# DEF-771 — schema-/contractcorrectie B1/B2 (v1)

26 september 2026. Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Opdracht: `vervolg-schema-opdracht-claude-v1.md` (akkoord Chris "ja akkoord" op B1/B2 uit `vervolg-integratie-rapport-v1.md`). Geen commit/push; de correctie staat **ongestaged** naast de voorbereide merge (HEAD b56e2878, MERGE_HEAD 076c9166, geen unmerged entries). Skillwerkboom niet aangeraakt.

## Gewijzigde bestanden (vijf, zoals opgedragen)

| Bestand | Diff (`git diff`, t.o.v. index) | Whitespace-ongevoelig | SHA-256 na |
|---|---|---|---|
| `docs/architectuur/contracts/schemas/validation_result.schema.json` | +74/−51 | +26/−3 | 7113caed…528bebe |
| `src/services/validation/interfaces.py` | +8/−1 | idem | baa1b048…5dd55 |
| `docs/architectuur/contracts/validation_result_contract.md` | +1/−1 | idem | 61855954…7e336 |
| `tests/unit/services/orchestrators/test_def772_int03_wrappers.py` | +4/−3 | idem | a0f437ef…3f9b |
| `tests/unit/validation/test_def771_int02_o1.py` | +77/−1 | idem | bc4b03ff…b6040 |

Volledige diff: `vervolg-schema-diff-v1.log`. Herstelkopieën: `herstelkopieen/vervolg-schema-*-20260926-131523.bak`.

## Inhoud

**Schema.** Het bestaande regeluitkomst-object is ongewijzigd verplaatst naar `rule_results.$defs.regeluitkomst` (met `$anchor: "regeluitkomst"`); semantisch gecontroleerd gelijk aan het origineel, op het weggehaalde `additionalProperties: false` na. Gebruik:
- `rule_results.additionalProperties` = `$ref #regeluitkomst` + `unevaluatedProperties: false` — alle regels blijven onbekende velden afwijzen, ook `assessment`/`signals`.
- `rule_results.properties["INT-03"]` = `$ref #regeluitkomst` + optioneel `assessment` (`object|null`) en `signals` (`array` van `string`) + `unevaluatedProperties: false`.
- `$anchor` in plaats van `#/$defs/…` zodat ook validatie van alleen het `rule_results`-deelschema (bestaande test) de verwijzing oplost; vooraf met een losse probe voor deelschema én volledig schema bevestigd. Top-level `additionalProperties: false` en alle overige delen ongewijzigd.
- Topbeschrijving: "geen nieuw veld" geldt nu expliciet voor de INT-02-NE-uitbreiding; daarnaast beschrijft 2.2.0 de bestaande INT-03-runtimevelden, alleen voor INT-03.

**interfaces.py.** `CONTRACT_VERSION` blijft 2.2.0. Commentaar 2.2.0 op dezelfde manier afgebakend. `RuleResult` krijgt `assessment: NotRequired[dict[str, Any] | None]` en `signals: NotRequired[list[str]]`, met commentaar dat ze alleen voor INT-03 gelden.

**Contractdocument.** De 2.2.0-rij behoudt de INT-02-NE-beschrijving; "geen nieuw veld" staat nu bij de NE-uitbreiding; aangevuld met de INT-03-velden (bestaande runtimevelden, geen nieuwe norm, geen gedragswijziging).

**B1.** `test_def772_int03_wrappers.py`: assertie en docstringverwijzing 2.1.0 → 2.2.0; bindingtests ongewijzigd.

**B2 — regressietests** (`test_def771_int02_o1.py`, brede `rule_results`-controle behouden; echte service, orchestrator en `FakeInt03Assessor` uit `tests/fixtures/def772_fakes.py`, geen model/netwerk):
- `test_int03_uitkomst_met_en_zonder_beoordeling_past_in_schema[zonder_dienst|pass|fail]`: `assessment` null resp. `assessed`, `signals` gevuld, schema foutloos; INT-02 blijft RR met exacte passagehulp en zonder deeluitkomst.
- `test_int03_velden_hebben_expliciete_typen` (5 gevallen): `signals` als string, `[1]`, `null`; `assessment` als string of lijst → afgewezen (na eerst foutloos basisresultaat).
- `test_onbekende_velden_en_int03_velden_elders_blijven_afgewezen`: onbekend veld bij INT-03, `signals` of `assessment` bij INT-02 → afgewezen; INT-02-NE-melding exact behouden.

## RED → GREEN

| Stap | Log | Uitkomst |
|---|---|---|
| RED (vóór schemawijziging) | `vervolg-schema-red-v1.log` | 13 failed (B1, 3× B2, 9 nieuwe), 31 passed, exit 1; redenen: 12× schema (`assessment`/`signals` unexpected), 1× `'2.2.0' == '2.1.0'` |
| GREEN, zelfde selectie als `vervolg-integratie-tests-v1.log` | `vervolg-schema-tests-v1.log` | 1179 passed, 1 failed, 5 skipped, exit 1 — enige failure de bekende `test_no_negative_commands_in_guide` (niet gerepareerd) |
| Aanvullend, overige schemaconsumenten | `vervolg-schema-consumenten-v2.log` | 109 passed, exit 0 (`test_def624_factory_schema`, `test_def624_reviewcorrecties`, `tests/integration/contracts/test_validation_{result_schema,interface,degraded_contract}.py`) |

1179 = 1166 (eerdere run, 5 FAILED) + 4 herstelde + 9 nieuwe; aantallen geteld op de `-rA`-regels (`^PASSED`/`^FAILED`/`^SKIPPED`) in de logs. Totaal diff +164/−57 (`-w`: +116/−9). `vervolg-schema-consumenten-v1.log` is een mislukte aanroep (`timeout` bestaat niet op macOS, exit 127, niets gedraaid).

Lint (`vervolg-schema-lint-v1.log`): Ruff exit 0, Black exit 0, JSON-geldigheid exit 0, `make lint` exit 0.

## Pogingen en grenzen

Schemascript poging 1 stopte op een eigen assertie (komma na `properties`) vóór schrijven; poging 2 geslaagd. Ketenproef niet opnieuw gedraaid: runtimecode ongewijzigd (alleen schema, typing-annotaties, documentatie en tests). Volledige pytest-suite niet gedraaid (coördinator). Alias-ZIP's, gates, DEF-626 en skills niet aangeraakt.
