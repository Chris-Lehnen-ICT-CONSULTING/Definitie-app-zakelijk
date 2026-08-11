# BATCH-176 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 12/12 bereiken, 5863/5863 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; repository-, Streamlit-fixture-, async-API- en Git-datalosscontracten zijn veilig offline gereproduceerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B176-001 — P2 — GitHub-setupguide stuurt beheerders naar de verkeerde repository

**Bewijs:** Regels 12 en 31 verwijzen naar github.com/ChrisLehnen/Definitie-app, terwijl de immutable origin voor deze repository github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk is. De tevens genoemde required-checkcontexts zijn grotendeels workflowstappen of onvolledige joblabels; dat deel is al gedekt door B171-003 en wordt hier niet opnieuw geteld. De verkeerde repository-URL blijft een zelfstandig bewezen beheerpaddefect.

**Reproductie:** Vergelijk regels 12 en 31 rechtstreeks met `git remote get-url origin` op de beoordeelde checkout. De eigenaar en repositoryslug verschillen beide. De externe GitHub-instellingen en branch-protection zijn zonder netwerk niet getest.

**Aanbevolen oplossing:** Genereer repositorylinks uit één canonieke repository-identiteit en test alle beheerlinks case-sensitive tegen de ingestelde remote. Beheer required checks via één stabiele aggregatiejob zoals aanbevolen in B171-003.

### B176-002 — P3 — Test-herstelplan lekt Streamlit-globals en bevat een niet-uitvoerbare afhankelijke pytest-fixture

**Bewijs:** De voorgeschreven contextmanager overschrijft op regels 52-61 `st.session_state` en zes modulefuncties, maar `__exit__` op regels 65-66 herstelt niets; iedere volgende test ziet daardoor de mocks en lege state. Het fixturefragment importeert `st` niet (regels 76-81) en roept op regel 99 de met `@pytest.fixture` gedecoreerde `clean_session_state` direct aan in plaats van dependency injection te gebruiken. Pytest weigert zo'n directe fixture-aanroep. De genoemde utility/fixturebestanden bestaan niet in base en het document heeft geen productiereachability, zodat dit een dormant planfinding is.

**Reproductie:** Voer de contextmanager met een fake `st` uit en vergelijk `st.markdown` en `st.session_state` vóór en na `with`: de originele waarden zijn niet hersteld. Definieer daarnaast een minimale `@pytest.fixture clean_session_state` en roep die aan zoals regel 99; pytest 8 geeft `Failed: Fixture clean_session_state called directly`. Zonder vooraf geïnjecteerd `st` geeft het documentfragment bovendien `NameError`.

**Aanbevolen oplossing:** Gebruik pytest `monkeypatch` of Streamlit AppTest zodat globals automatisch worden hersteld, importeer Streamlit expliciet en maak `session_state_with_context(clean_session_state)` afhankelijk van de fixture in plaats van haar aan te roepen. Voeg een uitvoerbare doctest/zelftest toe voordat dit plan opnieuw als implementatiehandleiding wordt gebruikt.

## Deduplicaties en afwijzingen

- Required-checkcontextdrift dedupliceert naar B171-003; alleen de verkeerde repository-URL blijft zelfstandig.

## Niet getest

- Geen externe GitHub-protection, netwerk/credentials, destructive Gitflow buiten een temp-repository of browser/UI-runtime.
