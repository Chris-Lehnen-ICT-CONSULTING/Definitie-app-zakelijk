# DEF-835 — exact begrensde metadata-uitzondering ter akkoord

28 september 2026. De dossiercommit is daadwerkelijk geblokkeerd; diagnose staat in modelproef-dossiercommit-blokkade-v1.md. Het DEF-522-runbook wijst Chris aan als beslissingseigenaar van uitzonderingen. Dit is een concreet voorstel, nog geen wijziging.

## Uitsluitend deze metadata toestaan

Regel: `generic-api-key`; voorwaarde **AND** van exact pad en volledige exacte regelinhoud. Geen globale padallowlist, geen map/prefixwildcard, geen hookskip en geen wijziging van gescande scope.

Twee paden:

- docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/bewijs/modelproef-manifest-v1.json
- docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/bewijs/modelproef-manifest-v2.json

Op beide paden uitsluitend deze volledige JSON-regel (zes spaties inspringing):

```text
      "src/utils/async_api.py": "f014876b16b76f889cf92faff1d89c3753b4ef0734624e8c45bcb6092841ff93",
```

De waarde is rechtstreeks gelijk bevonden aan SHA-256 van het genoemde bronbestand. Geen sleutelwaarde; er is geen credential ingetrokken of vervangen. De regex mag alleen de bekende optionele voorafgaande newline verdragen die de gepinde Gitleaks aan een volledige regel toevoegt, volgens de bestaande DEF-522-uitzonderingsconstructie.

## Uitvoering na akkoord

Twee software/configuratiebestanden: `.gitleaks.toml` en nieuw `scripts/ci/test_secret_scan_def835_metadata.py`. Raming 100–180 regels inclusief tests; INT-02-verruiming geldt. Geen dependency of publieke API/schemawijziging. Eigenaar Chris Lehnen; herbeoordeling 28 december 2026 of eerder als deze bronhash/manifestroute wijzigt.

Claude CLI implementeert, aparte Codex CLI reviewt. Eerst gedragstest rood met de huidige gepinde scanner/config, daarna groen voor uitsluitend de twee exacte metadataregels. Blokkeren moet blijven voor: dezelfde regel op ander pad, gewijzigde hash, extra tekst op dezelfde regel, synthetische credential op hetzelfde pad en extra credential elders in hetzelfde bestand. Bestaande DEF-522-canaries blijven groen. De normale staged-gate wordt daarna opnieuw op de volledige index uitgevoerd; pas bij clean de dossiercommit hervatten.

Dit voorstel verlaagt geen generieke detectieregel en laat geen hele manifesten ongescand. De geaccordeerde modelproef/WP5a-uitvoering geeft hiervoor niet automatisch toestemming.
