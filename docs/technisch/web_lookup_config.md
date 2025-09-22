# Web Lookup Configuratie (SRU/MediaWiki)

## SRU
- Accept headers: `Accept: application/xml`; bij SRU 2.0 ook `httpAccept=application/xml` en `recordPacking=xml` als query-parameters.
- Schema ladder (v2.0): `oai_dc` → `srw_dc` → `dc` (fallback bij 406).
- Wetgeving.nl: gebruik zoekservice `https://zoekservice.overheid.nl/sru/Search` met `x-connection=BWB`.
- Overheid.nl repository: `https://repository.overheid.nl/sru` (recordSchema=dc, collection=rijksoverheid).
- Zoekservice (GZD): `https://zoekservice.overheid.nl/sru/Search` (recordSchema=gzd).

## MediaWiki (Wikipedia/Wiktionary)
- Queries worden gesanitized: organisatorische tokens strippen; juridische/wet-tokens normaliseren; disambiguation overslaan.
- Taal NL; timeouts via config; UA verplicht.

## Providers (defaults)
- `sru_overheid.enabled: true` (Overheid.nl/Zoekservice actief)
- `wetgeving_nl` actief met SRU 2.0 + BWB
- `rechtspraak_ecli`: afhankelijk van netwerk (DNS/poort 443 `zoeken.rechtspraak.nl`)

