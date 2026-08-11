# BATCH-107 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 6/6 bereiken, 854/854 fysieke regels en 19/19 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte selectie gaf 73 groene en acht verwachte rode gevallen; de rode gevallen bewijzen de geregistreerde contract- en omgevingsproblemen. Ruff, Black en bash -n waren schoon.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B107-001 — P2 — DEF-110-verifier slaagt zonder een vereist app-event te observeren

**Bewijs:** Alleen maxima worden gecontroleerd, dus nul RuleCache-loads en nul context-cleanups gelden als succes. Een mocked Popen met alleen de Streamlit-readyregel gaf exit 0 en Fix is working correctly; readline kan bovendien voorbij de deadline blokkeren.

**Reproductie:** Mock Popen met een stdout die alleen 'You can now view your Streamlit app' retourneert en roep verify_fix aan.

**Aanbevolen oplossing:** Eis exact of minimaal bewijs, gebruik communicate met timeout of nonblocking reads en terminate/kill/wait altijd in finally.

### B107-002 — P3 — Ontbrekend performance-log wordt gerapporteerd als vijf van vijf zonder regressie

**Bewijs:** Een run tegen een niet-bestaand logpad gaf vijf passes, nul failures en exit 0. Ontbrekende renderdata is SKIP maar wordt door de A && B || C-samenvatting als pass geteld.

**Reproductie:** Run bash scripts/verify_performance_regression.sh /private/tmp/nonexistent.log.

**Aanbevolen oplossing:** Behandel onleesbare of ontbrekende logs als aparte nonzero status, eis een minimum aantal samples en gebruik expliciete if-blokken.

### B107-003 — P2 — RuleCache-verifier eindigt succesvol na expliciete cachefouten en een FAIL-resultaat

**Bewijs:** Future-exceptions en verschillende dictreferenties worden alleen gelogd; main retourneert niets en print altijd succes. De offline run logde cache-writefouten en FAIL: Modules got different dict references, daarna US-202 fix is working correctly en exit 0.

**Reproductie:** Draai met een read-only tijdelijke cache of mock vier verschillende resultaten en inspecteer de succesvolle exitcode.

**Aanbevolen oplossing:** Retourneer een gestructureerde status, eis vier succesvolle futures en de loadinvariant, en gebruik een tijdelijke cache zonder applicatiecache te muteren.

### B107-004 — P2 — Workflow-guard strict blokkeert de beloofde TDD review en coverage-overtredingen niet

**Bewijs:** Ontbrekende tests en reviewdocs zijn uitsluitend warnings; de coveragecheck draait alleen collection en telt de tekst test session starts. Een mockdiff met src/new_feature.py zonder test gaf een warning, nul violations en strict_allows=True.

**Reproductie:** Mock git diff met een nieuw src-bestand, maak geen corresponderende test en voer WorkflowGuard(strict=True) uit.

**Aanbevolen oplossing:** Registreer deze checks in strict mode als violations, controleer echte commitvolgorde en gebruik het project-coveragegatecommando.

### B107-005 — P3 — WIP-teller kan op nieuwere Bash-versies bij de eerste match stoppen

**Bewijs:** De postincrements leveren bij beginwaarde nul status 1; met set -e kan moderne Bash daardoor stoppen. Op de gereviewde macOS Bash 3.2 reproduceerde de abort niet, zodat platformimpact niet bewezen is.

**Reproductie:** Run make wip op Bash 4 of 5 met precies een in_progress story en observeer of de eerste postincrement het script beëindigt.

**Aanbevolen oplossing:** Gebruik preincrement of expliciete assignments en voeg een Linux-Bash-regressietest toe.

### B107-006 — P3 — Render-metric-verifier test een lokale kopie in plaats van productiecode

**Bewijs:** Het script definieert zelf _is_heavy_operation en importeert src/main.py niet. Productiewijziging of verwijdering beïnvloedt de verifier niet; de echte productie-unitfile bestaat wel en gaf 14 van 14 pass.

**Reproductie:** Vergelijk imports en symbolen en voer het standalone script uit zonder main._is_heavy_operation aan te raken.

**Aanbevolen oplossing:** Importeer het productiesymbool of verwijder de redundante verifier en gebruik de echte unitfile als bron van waarheid.

## Niet getest

- Geen echte provider, credential, netwerk, productiedatabase of browser; muterende scripts zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
