# DEF-624 — resultaatcontract en consumermigratie

De eerste, door Chris goedgekeurde deellevering is geïmplementeerd en onafhankelijk gereviewd. De volledige story blijft In Progress. Er is nog geen commit, push of merge van deze deellevering.

## Geleverde wijziging

Ontbrekende, null of ongeldige validation_status wordt validation_unknown met een concrete reden. Een hoge score of is_acceptable=True maakt ontbrekend runbewijs niet geldig. Dit geldt voor de gedeelde normalisatie, factories, adapters, UI en de betrokken opslag-, hertoetsings-, bronacceptatie- en optionele exportgrenzen.

Het resultaatcontract is geconsolideerd op schema 2.0.0; schema 1.4.0 blijft historisch beschikbaar. None blijft None. Status, readiness en regel-/bronmetadata blijven bij conversie behouden, zonder bronmutatie of verzonnen beoordelingen. validated betekent dat de run is uitgevoerd, niet dat alle beoordelingen positief of voltooid zijn. De UI toont ontbrekend bewijs met een passende reden. Geen nieuw totaal- of deelscorecijfer, normwijziging, prompt- of skillwijziging.

## Verplichte CLI-rolverdeling

- Implementatie en alle correcties: echte `/Users/chrislehnen/.local/bin/claude`, versie 2.1.270, sessie `0d8400d6-d6f4-437c-a1f3-50b36267161b`.
- Onafhankelijke review: echte `/Users/chrislehnen/.local/bin/codex`, versie 0.154.0, afzonderlijke sessie `01a0ab13-a771-7403-8618-98d1b1f62542`, alleen-lezen.
- Beide CLI's vooraf functioneel beproefd. Alleen de coördinator startte sessies; geen delegatie door uitvoerder/reviewer, geen interne subagents als vervanging. Coördinator heeft geen productiecode, tests, prompts of skills geschreven of gecorrigeerd.

Uitvoeringslogs: `/tmp/def624-claude-implement.stream.jsonl`, `/tmp/def624-claude-fix.stream.jsonl`, `/tmp/def624-claude-factory.stream.jsonl`.
Reviewlogs: `/tmp/def624-codex-review.jsonl`, `/tmp/def624-codex-deltareview.jsonl`, `/tmp/def624-codex-finalreview.jsonl`, `/tmp/def624-codex-gatebewijs.jsonl`.

## Exact beoordeelde versie

Werkboom: `/private/tmp/def624-resultaatcontract`
Branch: `feature/DEF-624-resultaatcontract`
Basiscommit/HEAD: `bceb6ab80a930a2403b51de9a0312880de527f97`.

Volledige diff: `/tmp/def624-review-v3.diff`.
SHA256: `23fc978c74c9bff78b905b1309320d49d82cbf51b43e4dbc35cb45e28bc64f75`.
Manifest met alle 41 bestandsversies: `/tmp/def624-review-source-manifest-v3.json`.

Reviewer controleerde het manifest bij begin/einde. Coördinator controleerde na alle gates opnieuw: 41 bestanden, nul hashafwijkingen, geen extra of ontbrekende gewijzigde bestanden. `git diff --check` slaagt; geen print()-aanroepen in de gewijzigde productiecode.

## Tests en beoordeling

| Controle op eindcode | Bewijs | Uitkomst |
|---|---|---|
| Factory/schema TDD | `/tmp/def624-claude-factory-red.log`, `...-green-1.log` | 29 falende tests vóór correctie; daarna 53 geslaagd |
| Gerichte bestaande regressies | `/tmp/def624-claude-factory-bestaand-1.log` | 845 geslaagd, 7 overgeslagen |
| Volledige unitgate | `/tmp/def624-claude-factory-make-test-2.log` | 6.014 geslaagd, 75 overgeslagen, 1 verwachte failure, 21 geslaagde subtests; exit 0 |
| Coverage-gate | `/tmp/def624-claude-factory-make-test-cov-ci.log` | 61,47%, boven projectvloer 45%; exit 0 |
| Contractgate | `/tmp/def624-claude-factory-make-test-contract.log` | 36 geslaagd, 6 overgeslagen; exit 0 |
| Lint | `/tmp/def624-claude-factory-make-lint.log` | Ruff/Black schoon; exit 0 |
| Types | `/tmp/def624-claude-factory-make-mypy-check.log` | 0 mypy-fouten; exit 0 |

Alle reviewbevindingen zijn door Claude gecorrigeerd en door Codex gecontroleerd. De eindreview keurt de code goed en bevestigt onder meer 1.920 eigen status-/unknown-/readinessproeven tegen het echte schema. Rapport: `/tmp/def624-codex-finalreview-result.md`. Dat historische rapport zag de eindgates nog niet compleet; het afzonderlijke eindbewijsaddendum staat in `/tmp/def624-codex-gatebewijs-result.md`.

De eerste volledige unitrun op de eindcode faalde op de bestaande geheugentest `test_memory_reasonable`: circa 170,4 MiB gemeten tegenover een grens van 100 MiB. Log blijft bewaard: `/tmp/def624-claude-factory-make-test.log`. Zonder bronwijziging slaagden de tweede unitrun en de coverage-run. Geen oorzaak of verband met deze diff vastgesteld; geen test of grens versoepeld. Dit is geen claim dat een geheugenprobleem is opgelost.

Overgeslagen contracttests vereisen onder meer echte API-generatie of de ontbrekende golden_definitions-fixture. De resultaten bewijzen geen volledige live integratie-/UI-acceptatie of semantische dekking van alle 53 regels.

## Resterend werk

De inhoudelijke classificatie van 53 regels, de 44 goed/fout-paren en repositorybewijs blijven open binnen DEF-624; semantische VER/SAM-correcties blijven bij DEF-623. Snapshotopslag/readback, actualiteit en algemeen vaststel/exportbeleid blijven respectievelijk bij DEF-626, DEF-627 en DEF-630. Deze deellevering maakt de volledige story niet Done.

Goedgekeurd plan: `docs/plans/2026-09-16-def624-resultaatcontract.md` in de werkboom; in Linear: https://linear.app/definitie-app/document/def-624-resultaatcontract-en-consumermigratie-goedgekeurd-31b1600cd55d.
