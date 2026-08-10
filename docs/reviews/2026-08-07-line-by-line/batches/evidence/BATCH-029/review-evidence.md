# BATCH-029 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 1.550/1.550 fysieke regels en 57/57 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen;
applicatiebestanden zijn niet gewijzigd.

## Verificatie

- Onderdeel van 206 primaire gerichte tests; Ruff en Black waren schoon.
- JSON/Python-contracten en cache-identiteit zijn met lokale calls gereproduceerd.

## Bevindingen

### B029-001 — P3 — VER Pythonimplementaties wijken af van hun JSON-contract

VER-01 JSON gaat over enkelvoud, maar Python over versie-specifieke formulering;
VER-02 JSON over enkelvoud, maar Python over tijd; VER-03 JSON over infinitief,
maar Python over datum/tijd. Directe validators en de publieke loader produceren
daardoor semantisch verkeerde meldingen. Er is geen productiecaller gevonden en
het Pythonpad is niet de primaire V2-evaluator.
Aanbevolen: één gegenereerd contract en semantische good/bad-goldentests.

### B029-002 — P3 — STR-08 en STR-09 markeren gewone voegwoorden als ambigu

`STR-08.py:52-70` laat ieder `X en Y` falen en `STR-09.py:52-69` ieder `X of Y`,
ook voor duidelijke cumulatieve/alternatieve zinnen en JSON-goedvoorbeelden.
Aanbevolen: echte ambiguïteitscriteria of reviewwaarschuwing, gedreven door de
geconfigureerde voorbeelden.

### B029-003 — P3 — regelcache lekt gedeelde mutabele state

`rule_cache.py:165-228` bewaart en retourneert hetzelfde dictobject. Een caller
die `STR-08` verwijdert, verandert de volgende caller tot clear/TTL. Huidige
callers lijken read-only. Aanbevolen: immutable mapping of defensive deep copy.

## Niet getest

- Actieve productiecaller van de legacy VER-/STR-Pythonlaag niet gevonden.
- Geen browser, externe dienst of credentialflow.
