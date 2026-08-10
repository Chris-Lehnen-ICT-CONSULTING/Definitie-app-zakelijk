# BATCH-011 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 5/5 blobs, 2.222/2.222 fysieke regels en 80/80 Python-symbolen

De immutable blobs, alle functies en relevante callers zijn volledig gelezen.
Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire wave-selectie: onderdeel van 263 geslaagde tests.
- Onafhankelijke selectie: onderdeel van 111 geslaagde tests; 142 warnings,
  vooral bevestigende unclosed-SQLite-ResourceWarnings.
- Ruff en Black: geslaagd. Repro’s gebruikten tijdelijke DB’s en mocks.

## Bewezen bevindingen

### B011-001 — P1 — save rapporteert succes wanneer legacy-update faalt

`src/services/definition_repository.py:80-91` negeert `False` van
`legacy_repo.update_definitie`, telt de save en retourneert het ID. Mockrepro:
`update_definitie=False` gaf `save(...) == 123` en `total_saves==1`. Dit is de
containerdefault. Aanbevolen: False naar typed repositoryfout/duidelijk contract
vertalen en statistiek pas na een bewezen write bijwerken.

### B011-002 — P1 — hard_delete bevestigt een niet-gecommitte delete

`definition_repository.py:305-322,819-827` voert DELETE uit en retourneert True,
maar sluit zonder commit. Een nieuwe verbinding zag de rij nog. Aanbevolen:
expliciete transactie en commit vóór True, rollback op fout en rowcountcontrole
na commit.

### B011-003 — P2 — bulkupdate retourneert partial count na volledige rollback

`src/services/definition_edit_repository.py:264-307` telt per UPDATE, commit pas
na de lus en retourneert bij een latere fout de teller. Een trigger die update 2
afbrak gaf return `1`, terwijl beide rijen ongewijzigd waren. Aanbevolen: na
rollback `0` of een typed exception, met expliciete atomiciteitstest.

### B011-004 — P2 — synonymrepository sluit SQLiteconnections niet

`src/repositories/synonym_repository.py:105-250` retourneert raw connections;
`with connection` commit/rollbackt maar sluit niet. Na method-exit kon de
connection nog `SELECT 1` uitvoeren en de tests rapporteerden tientallen
ResourceWarnings. Aanbevolen: een echte contextmanager met `finally: close()`
of `contextlib.closing`, en warnings-as-errors regressietests.

### B011-005 — P2 — reasoned history is niet atomair met de definitiewijziging

`definition_edit_repository.py:98-141,443-478` schrijft de definitie eerst en
de handmatige historie via een aparte connection; een historyfout wordt geslikt.
Een trigger die alleen `wijziging_reden='manualreason'` afbrak liet de methode
succes rapporteren met definitie en generieke trigger-history, maar zonder de
reasoned history. Aanbevolen: data en reasoned audit in één transactie/API,
failure propagaten en generic/manual historie bewust modelleren.

## Niet getest

- Geen echte productie-DB, descriptor-uitputtingsduurtest of UI-flow.
- Geen externe services; visuele UI/a11y/responsive aspecten zijn niet van
  toepassing op deze repositorybatch.
