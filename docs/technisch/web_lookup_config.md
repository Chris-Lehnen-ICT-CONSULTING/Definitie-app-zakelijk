# Web Lookup Configuratie

Dit document beschrijft de standaardconfiguratie en aanbevolen gewichten voor de Web Lookup providers in DefinitieAgent.

## Standaardconfiguratie

Bestand: `config/web_lookup_defaults.yaml`

```yaml
web_lookup:
  enabled: true

  cache:
    strategy: "stale-while-revalidate"
    grace_period: 300
    default_ttl: 3600
    max_entries: 1000

  sanitization:
    strip_tags: [script, style, iframe, object, embed, form]
    block_protocols: [javascript, data, vbscript]
    max_snippet_length: 500

  providers:
    wikipedia:
      enabled: true
      weight: 0.7
      timeout: 5
      cache_ttl: 7200
      min_score: 0.3

    sru_overheid:
      enabled: true
      weight: 1.0
      timeout: 5
      cache_ttl: 3600
      min_score: 0.4

    wetgeving_nl:
      enabled: true
      weight: 0.9
      timeout: 5
      cache_ttl: 3600
      min_score: 0.4

    rechtspraak_ecli:
      enabled: true
      weight: 0.9
      timeout: 5
      cache_ttl: 3600
      min_score: 0.4

    eur_lex:
      enabled: true
      weight: 0.6
      timeout: 5
      cache_ttl: 3600
      min_score: 0.3

    wikidata:
      enabled: true
      weight: 0.3
      timeout: 5
      cache_ttl: 3600
      min_score: 0.2

    dbpedia:
      enabled: true
      weight: 0.2
      timeout: 5
      cache_ttl: 3600
      min_score: 0.2
```

## Orchestrator‑timeout (globaal)

Naast per‑provider timeouts hanteert de orchestrator een globale wachtduur voor web lookup. Deze is instelbaar via een environment‑variabele:

- `WEB_LOOKUP_TIMEOUT_SECONDS` (float, default: `6.0`)

De orchestrator wacht maximaal deze tijd op de verzamelde resultaten en gaat daarna verder zonder externe context (graceful degrade). Gebruik een hogere waarde wanneer betrouwbaarheid belangrijker is dan snelheid.

## Aanbevolen gewichten

- Juridisch (SRU/Wetgeving.nl/Rechtspraak): 0.8–1.0
- Wikipedia: 0.6–0.8
- EUR‑Lex: 0.5–0.7
- Wikidata/DBpedia (verrijking): 0.2–0.4

## NFR‑richtlijnen (veilige scraping)

- Respecteer robots.txt en Terms of Service
- Timeout ≤ 5s per provider; rate limiting + exponential backoff
- Sanitization van HTML/markup (XSS‑preventie) vóór parsing
- Geen PII verzamelen/loggen; AVG/BIR‑conform
- Eenduidige User‑Agent; volledige provenance; beknopte audit logging
