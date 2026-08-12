# BATCH-003 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 2/2 bereiken, 195/195 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Beide immutable blobs zijn gelezen; de Make/Python-pathrepro en gerichte test-, lint-, type- en complexiteitsgates zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B003-001 — P2 — Make-testtargets negeren de gekozen project-Python en gebruiken ambient pytest

**Bewijs:** Het Makefile selecteert op regels 1-3 expliciet PY=.venv/bin/python wanneer die bestaat. De markercheck gebruikt `$(PY)`, maar daarna roepen alle twaalf pytest-recepten op regels 51-105 bare `pytest` aan. Installatie, versie en plugins kunnen daardoor afwijken van de gekozen projectinterpreter.

**Reproductie:** Voer offline uit: PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 /usr/bin/make PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python test. De markercheck slaagt via de opgegeven Python; daarna faalt de target met `pytest: command not found` en make-exitcode 2. `make -n` toont twaalf bare-pytestrecepten.

**Aanbevolen oplossing:** Roep in alle testtargets `$(PY) -m pytest` aan via één gedeelde variabele/helper en voeg een regressietest toe die PATH zonder een globale pytest uitvoert.

## Deduplicaties en afwijzingen

- Dashboard- en feature-statusworkflowdefecten zijn reeds B099-002 en B100-006; alleen het ambient-pytestcontract blijft zelfstandig.

## Niet getest

- Geen live GitHub-workflow/projectmutatie, externe Trunk-run, netwerk/CVE-audit, lockregeneratie of echte providercall; geen UI-scope.
