# Coverage en verificatie

## Inventarisdekking

| Object | Verified | Totaal | Dekking |
|---|---:|---:|---:|
| Git-bestanden | 1,884 | 1,884 | 100% |
| Line-ownerbereiken | 1,904 | 1,904 | 100% |
| Fysieke regels | 683,954 | 683,954 | 100% |
| Symbolen | 10,581 | 10,581 | 100% |
| Batchmemberships | 12,485 | 12,485 | 100% |
| Bevroren untracked bestanden | 2 | 2 | 100% |

Classificaties: code 935, configuratie 134,
data 37, documentatie 761, generated
17, lege bestanden 13 en binaire-equivalente
review 7.

De canonieke inventoryvalidator slaagt zowel normaal als met `--require-final`.

## Productie-naar-testtraceability

| Status | Symbolen | Betekenis |
|---|---:|---|
| direct | 79 | expliciete test-ID of directe testmapping |
| indirect | 2,293 | afgeleid via geteste module/caller |
| none | 1,473 | geen aantoonbare mapping; geen bewijs van geen uitvoering |

## Verse testgates op immutable base

| Gate | Resultaat | Dispositie |
|---|---|---|
| Unit + coverage, 4 workers | 2.982 collected; 2.894 pass; 88 skip; 0 fail/error | PASS |
| Unitcoverage | 50,56% (34.447 statements; 17.031 missed) | PASS tegen projectratchet 45%; onder algemene 80% |
| Smoke, credentialvrij | 14 pass; 3 fail; 10 skip | FAIL: drie Anthropic-key-afhankelijke tests |
| Acceptance, credentialvrij | 2 pass; 5 fail; 9 skip | FAIL: stale `HybridContextManager(config)`-contract |
| Integratie, ieder bestand apart | 45 pass; 20 fail; 9 skip; 2 blocked; 0 timeout | FAIL/mixed |

## Statische kwaliteit

- Ruff en Black: PASS op 371 Pythonbestanden.
- Complexiteitsratchet: PASS, 200 overtredingen tegenover baseline 201
  (`C901=90`, `PLR0911=18`, `PLR0912=54`, `PLR0915=38`).
- mypy-ratchet: PASS, 0 nieuwe baselinefouten; overrides-baseline 2.
- toolpins, testmarkers (317/317) en `pip check`: PASS.
- Bandit: exit 1 door bekende en beoordeelde signalen, waaronder externe XML,
  lokale pickle en niet-securitykritische MD5-toepassingen; geen groene gate.
- Een zelfstandige duplicatiescanner was niet beschikbaar: duplicatie is daarom
  alleen line-by-line en via gerichte zoekacties beoordeeld, niet kwantitatief
  projectbreed gemeten.

## Dependency- en licentiebewijs

De offline audit dekt alle 92 runtime-lockdependencies exact en meldt 10
advisories: drie op `aiohttp 3.14.1` en zeven op `GitPython 3.1.55`.
`B005-006` en `B005-007` leggen bereikbaarheid en fixes vast. `B005-008` is
suspected: de actieve PyMuPDF-PDF/RAG-flow vereist aantoonbaar een keuze tussen
AGPL-compliance en een commerciële licentie; een eventuele externe overeenkomst
is niet onderzocht.

## Niet getest

Geen echte providers, credentials, netwerkservices of productiedata; geen live
GitHub branch protection; geen volledige VoiceOver/NVDA-, forced-colors- of
touch-device-run; geen schone lockinstallatie, nieuwe online advisoryfeed of
juridisch licentieoordeel.
