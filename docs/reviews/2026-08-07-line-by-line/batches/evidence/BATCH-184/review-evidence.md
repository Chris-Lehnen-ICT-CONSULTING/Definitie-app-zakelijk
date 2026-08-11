# BATCH-184 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 7/7 bereiken, 0/0 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten en binaire objecten zijn equivalent beoordeeld; stale pytest-, SQLite-, HTML/a11y-, PDF-, tar- en screenshotgates zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B184-001 — P2 — Gearchiveerde screenshots bewaren persoonlijke browsermetadata in Git

**Bewijs:** Visuele inspectie van de immutable PNG toont in de browserbalk een gedeeltelijk persoonlijk Gmail-adres met inboxaantal, een tab over het aanvragen van een medicijnverklaring, YouTube-titels/aantallen en de persoonlijke GitHub-gebruikersnaam naast een private-repository-indicator. De companion screenshot met OID 232853365071b30d11881945be409e300bcdaaeb bewaart dezelfde inbox- en browsertabmetadata boven een localhost-app. Er zijn geen API-sleutels of volledige credentials gezien, maar de niet-functionele persoonsgegevens en mogelijk gevoelige browsecontext blijven permanent in de Git-historie; het pad is gearchiveerd en heeft geen runtimecaller.

**Reproductie:** Render blob ec71afd346782df093dca59e7cb54efb29d99bff rechtstreeks uit Git en bekijk de bovenste circa 200 pixels; herhaal voor blob 232853365071b30d11881945be409e300bcdaaeb. De genoemde browsermetadata staat buiten de eigenlijke applicatie-inhoud en is leesbaar zonder credentials.

**Aanbevolen oplossing:** Vervang bewaarde UI-beelden door strak uitgesneden en geredigeerde screenshots zonder browserchrome, accountnamen of andere tabs; voeg een privacycheck aan het screenshotproces toe en beoordeel onder expliciete toestemming of historische Git-objecten met gevoelige context moeten worden herschreven.

## Deduplicaties en afwijzingen

- Binaire PDF- en tarinhoud is volledig equivalent beoordeeld; alleen de concrete screenshotprivacyblootstelling is een nieuwe finding.

## Niet getest

- Geen netwerk/credentials, echte provider- of productiedataflow, browser/screenreader/zoomruntime, externe links of uitvoering van binaire artefacten.
