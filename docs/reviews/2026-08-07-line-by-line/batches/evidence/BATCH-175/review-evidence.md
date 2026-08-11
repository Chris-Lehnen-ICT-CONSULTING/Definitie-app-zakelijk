# BATCH-175 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 13/13 bereiken, 5553/5553 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten en 27 Python-symbolen zijn gelezen; lifecycle-, lexicografische-, launcher-, rollback- en gerichte testgates zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B175-001 — P2 — Ready-for-execution noodrollback herstelt geen gepinde versie en kan de applicatie niet starten

**Bewijs:** Het Emergency Rollback-blok exporteert de featureflag geldig naar childprocessen in dezelfde shell, maar checkt de bewegende branch `main` uit en pullt de nieuwste toestand in plaats van een bewezen known-good commit. Daarna start het `bash scripts/run_app.sh`, terwijl alleen `scripts/deployment/run_app.sh` bestaat. Het Ready for Execution-document belooft minder dan vijf minuten herstel en geen dataverlies zonder SHA/tag, clean-state-, health- of data-postconditions. Er is geen externe caller; de procedure is dormant maar direct kopieerbaar.

**Reproductie:** Controleer met `git cat-file -e b958ddb:scripts/run_app.sh` (exit 128) en `git cat-file -e b958ddb:scripts/deployment/run_app.sh` (exit 0). Inspecteer regels 360-372: er staat geen SHA/tag, clean-worktreecheck, persistent configuratie-update of healthcheck vóór de succesclaim. Voer checkout/pull of een echte productie-rollback niet uit.

**Aanbevolen oplossing:** Gebruik een expliciet geverifieerde known-good tag/SHA of deploymentartifact, preflight branch en clean state, pas de featureflag in de ondersteunde configuratielaag toe, roep de werkende launcher aan en vereis geautomatiseerde health- en dataintegriteitschecks. Oefen de procedure in een disposable checkout en publiceer gemeten rollbackbewijs.

## Deduplicaties en afwijzingen

- Featureflag-export in dezelfde shell is geldig; alleen de ongepinde rollback, ontbrekende launcher en postconditions zijn geregistreerd.

## Niet getest

- Geen netwerk/credentials, live appstart, echte rollback, Linear/GitHub-status, browser/a11y of externe stakeholderbevestiging.
