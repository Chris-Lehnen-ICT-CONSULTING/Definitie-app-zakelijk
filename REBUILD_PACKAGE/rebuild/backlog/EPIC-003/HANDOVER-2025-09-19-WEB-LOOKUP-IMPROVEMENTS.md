---
titel: Handover – Web Lookup (EPIC-003) – Context Backoff, Providers en Volgende Stappen
status: active
owner: development
canonical: false
last_verified: 2025-09-19
applies_to: definitie-app@current
---

# Handover – Web Lookup (EPIC-003)

Deze handover vat de huidige stand van zaken en de volgende concrete stappen samen om de Web Lookup te laten werken zoals bedoeld: context‑gestuurde SRU/Wetgeving/Rechtspraak/Wikipedia zoekopdrachten met zinvolle juridische resultaten (artikelen, leden).

## Scope
- EPIC‑003 (Content Verrijking / Web Lookup)
- Providers: Wetgeving.nl (SRU), Overheid.nl (SRU), Overheid.nl Zoekservice (SRU), Rechtspraak.nl (SRU), Wikipedia (MediaWiki)
- UI: debug/attempts + health check

## Wat is al gedaan
- Nieuwe provider: Wetgeving.nl (SRU) toegevoegd en geprioriteerd bij juridische context
  - Endpoints met fallbacks toegevoegd
- Context‑backoff cascade per provider (SRU en Wikipedia):
  1) term + organisatorisch + juridisch + wettelijk
  2) term + juridisch + wettelijk
  3) term + wettelijk
  4) term (geen context)
- Context tokens geclassificeerd (org/jur/wet) incl. mapping (Sv/Sr/Awb/Rv)
- SRU attempts‑tracing: per poging status/records/url/strategie/stage zichtbaar in UI
- UI health check: management‑tab test per provider
- Artikelmetadata uit SRU:
  - Extract `article_number`, `law_code` (Sv/Sr/Awb/Rv), `law_title`, `law_clause` (lid)
  - Snippet voor juridische bronnen wordt geprefixt met “Artikel <nr> [lid <x>] <code>: …”

## Belangrijkste commits
- c445c76: Voeg Wetgeving.nl SRU provider toe
- 2cb8e1a: UI attempts‑tabel + SRU attempts‑tracing
- 96273e9: SRU fallback queries (serverChoice any + prefix wildcard)
- 57d0c58: Context‑aware SRU zoekopdrachten + UI health check
- ecc00e1: Context‑backoff cascade (org+jur+wet → jur+wet → wet → term)
- 6bdd470: Artikelmetadata (artikel + wetcode) en snippet‑verrijking
- ce568b0: ‘lid’ extractie (numeriek/ordinaal/woord) en in snippet

## Observaties (laatste test – “voorlopige hechtenis”)
- Wikipedia: success
- Overheid.nl / Zoekservice: HTTP 200 maar 0 records
- Wetgeving.nl: HTTP 503 op alle varianten (dienst onbeschikbaar / rate limit / schema mismatch)
- Rechtspraak.nl: ‘fail’ in attempts (geen status ⇒ parse/endpoint/scheme bevestigen)

### Waarschijnlijke oorzaken
- SRU queries gebruiken nu vaak één “gequote” frase met alle contexttokens samen (lage recall):
  - Voorbeeld: `cql.serverChoice all "voorlopige hechtenis OM Strafrecht Wetboek van Strafvordering Sv"`
  - Server zoekt dan naar exacte of té brede frase ⇒ 200/0 records.
- Wetgeving.nl levert 503 bij alle pogingen ⇒ mogelijk rate limiting/onderhoud of schema/index mismatch.

## Aanbevolen volgende stappen (klein, gericht)
1) SRU CQL‑builder corrigeren (grootste impact)
   - Gebruik AND/OR met losse tokens i.p.v. één gequote frase.
   - Voorbeeld (Wetgeving‑gericht voor Sv):
     - `(cql.serverChoice any "voorlopige hechtenis") AND (cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")`
   - Niet alle contexttokens combineren: laat ‘org’ (OM/ZM) weg in SRU queries; deze verlagen eerder de matchkans.

2) Wetgeving.nl pragmatisch behandelen
   - Beperk pogingen tot 1–2 strategieën vóór fallback op andere providers bij aanhoudende 503’s
   - Log status “503 (geparkeerd)” en ga door met Overheid/Zoekservice/Rechtspraak/Wikipedia.

3) Rechtspraak.nl valideren
   - Controleer definitieve endpoint + recordSchema ⇒ we gebruiken nu `…/SRU/Search` + `dc`.
   - Laat attempts status/records voor Rechtspraak zien (zoals bij Overheid); nu staat er ‘fail’ zonder status.

## Implementatieplan (kort)
- Bestanden:
  - SRU querybouw en fallback: `src/services/web_lookup/sru_service.py`
  - Stage orchestration + context tokens: `src/services/modern_web_lookup_service.py`
  - Config/wegings/limits: `config/web_lookup_defaults.yaml`
- SRU CQL‑builder aanpassing:
  - Voeg helper toe die uit (term, jur[], wet[]) CQL maakt met AND/OR blokken.
  - Voorbeeld implementatie:
    - `term_block = 'cql.serverChoice any "<term>"'`
    - `wet_block = 'cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv"'` (zelfde voor Sr/Awb)
    - `final = f'({term_block}) AND ({wet_block})'`
  - Pas dit toe in stages 1–3; stage 4 alleen term.
  - Laat ‘org’ tokens achterwege voor SRU.
- Wetgeving.nl (tijdelijk): max 2 pogingen per stage en direct door naar andere providers bij 503.

## Verificatie (na fix)
1) Management‑tab → “🌐 Web Lookup Health Check”
   - Test ‘wetgeving’ met “Wetboek van Strafvordering” / “Wetboek van Strafrecht”
   - Test ‘rechtspraak’ met “ECLI:NL:HR:2019:1288”
2) Generator‑tab (debugtabel aan):
   - “voorlopige hechtenis” met context OM/ZM + Sv
   - Controleer attempts:
     - SRU stage en strategie tonen 200 en records ≥ 1
     - Snippet begint met “Artikel <nr> [lid <x>] <code>: …”

## Bekende beperkingen (bewust niet opgepakt)
- Rate limiting, circuit breaker, SWR cache: niet nodig voor single‑user en pas oppakken als we stabiele hits hebben.
- Robots.txt check: alleen relevant voor scraping (niet actief); SRU/MediaWiki blijven leidend.

## Snelle referentie – paden
- Modern service orchestratie: `src/services/modern_web_lookup_service.py`
- SRU service + parsing: `src/services/web_lookup/sru_service.py`
- Wikipedia service: `src/services/web_lookup/wikipedia_service.py`
- Ranking/dedup: `src/services/web_lookup/ranking.py`
- UI debugsectie: `src/ui/components/definition_generator_tab.py`
- UI health check: `src/ui/components/management_tab.py`
- Config: `config/web_lookup_defaults.yaml`, docs: `docs/technisch/web_lookup_config.md`

## Checklist “Definition of Done” voor de volgende iteratie
- [ ] SRU CQL‑builder gebruikt AND/OR blokken (geen totale frase) met term + (Sv/Sr/Awb)
- [ ] ‘org’ tokens worden niet in SRU query gebruikt
- [ ] Rechtspraak endpoint geeft status/records in attempts (geen ‘fail’ zonder status)
- [ ] Minstens 1 SRU‑hit bij “voorlopige hechtenis” (Sv) met artikelmetadata in snippet
- [ ] Wetgeving.nl 503’s leiden niet tot wachttijden (pogingen beperkt en gelogd)

## Bijlagen – voorbeeld CQL (indicatief)
- Term + Sv:
  - `(cql.serverChoice any "voorlopige hechtenis") AND (cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")`
- Term + Sr:
  - `(cql.serverChoice any "diefstal") AND (cql.serverChoice any "Wetboek van Strafrecht" OR cql.serverChoice any "Sr")`

---

Vragen of sparren over de implementatie? Start bij de CQL‑builder in `sru_service.py` (kleinste diff, grootste opbrengst) en controleer de attempts‑tabel voor directe feedback op elke query.

