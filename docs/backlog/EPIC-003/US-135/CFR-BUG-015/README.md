---
id: CFR-BUG-015
epic: EPIC-010
titel: Compat web lookup gebruikt niet‑bestaand attribuut 'title'
prioriteit: HOOG
status: OPEN
aangemaakt: 2025-09-10
bijgewerkt: 2025-09-10
component: services.definition_generator_context (compat web lookup)
severity: Medium-High
impact: Exceptions in contextverrijking; potentieel blokkeren van generatieflow
---

# CFR-BUG-015: Compat web lookup gebruikt niet‑bestaand attribuut 'title'

## 🐛 Beschrijving
De compatibele web‑context wrapper in `DefinitionGeneratorContext` gebruikt `r.title` voor weergave van SRU/Wikipedia resultaten. Het `LookupResult`-contract bevat echter geen `title` attribuut; titel/meta-informatie staat in `result.metadata` (bij SRU onder `dc_title`) of ontbreekt. Dit veroorzaakt een `AttributeError` en kan de flow onderbreken tijdens contextverrijking.

**Locatie**
- Bestandslocatie: `src/services/definition_generator_context.py`
- Functie: `_init_web_lookup()` → `web_lookup_wrapper()` (list-comprehensie met `f"{r.title} ({r.source.name})"`)
- Contractreferentie: `src/services/interfaces.py::LookupResult`

## 🔎 Reproduceren
1. Web lookup is automatisch actief wanneer de service beschikbaar is (geen feature flag meer nodig).
2. Activeer een pad dat `HybridContextManager._init_web_lookup()` gebruikt (bv. contextverrijking in V2‑flow met hybrid/web lookup).
3. Trigger generatie met een begrip dat web lookup start.
4. Observeer exception: `AttributeError: 'LookupResult' object has no attribute 'title'`.

## 🎯 Verwacht gedrag
- Compat wrapper gebruikt een robuuste titelbron:
  - SRU: `result.metadata['dc_title']` indien aanwezig
  - Fallback: `result.source.name`
- Geen exceptions in de compatlaag; contextverrijking loopt door (of levert lege string).

## 🧩 Root Cause
- `LookupResult` dataclass heeft geen `title`-attribuut. Titelinformatie zit in `metadata` of valt terug op de bronnaam. De compat wrapper refereert aan een niet‑bestaand attribuut.

## 🛠️ Oplossing (Proposed Fix)
- Pas de compat wrapper aan in `src/services/definition_generator_context.py`:
  - Vervang `r.title` door `(r.metadata.get('dc_title') if isinstance(r.metadata, dict) else None) or r.source.name`.
  - Beperk output tot max 3 resultaten; graceful fallback naar lege string wanneer geen resultaten.
- (Optioneel) Markeer de compat wrapper als deprecated in V2‑only modus om misbruik te voorkomen.

## ✅ Acceptatiecriteria
- Geen `AttributeError` in compat web‑context.
- Bij SRU‑resultaten wordt de titel uit `metadata['dc_title']` gebruikt; anders fallback naar bronnaam.
- Generatieflow loopt door (ook als web lookup geen resultaten geeft of SRU niet beschikbaar is).

## 📎 Referenties
- `src/services/definition_generator_context.py`
- `src/services/interfaces.py` (klassen: `LookupResult`, `WebSource`)
- `src/services/modern_web_lookup_service.py` (mapping SRU → metadata `dc_title`)
- `docs/backlog/EPIC-010/EPIC-010.md`

## 🧪 Testvoorstel
- Unit: mock `LookupResult` met `metadata={'dc_title':'...'}; source.name='...'` → wrapper string bevat `dc_title`.
- Unit: mock zonder `dc_title` → wrapper string bevat `source.name`.
- Integratie: web lookup ingeschakeld in dev; geen exceptions in contextverrijking.

## 🔬 Technische Analyse (aanvulling)

### Symptoom
- Exception tijdens contextverrijking met web lookup ingeschakeld: `AttributeError: 'LookupResult' object has no attribute 'title'`.

### Directe oorzaak
- In `HybridContextManager._init_web_lookup()` wordt een compat‑wrapper gedefinieerd:
  - Locatie: `src/services/definition_generator_context.py`
  - Wrapper formatteert resultaten met `f"{r.title} ({r.source.name})"`, maar `LookupResult` kent geen attribuut `title`.

### Contract‑mismatch onderbouwing
- `LookupResult` (zie `src/services/interfaces.py`) bevat o.a. `term`, `source`, `definition`, `context`, `examples`, `references`, `success`, `error_message`, `metadata` — geen `title` attribuut.
- Bronspecifieke titelvelden worden in `metadata` geplaatst:
  - SRU: `metadata['dc_title']` (aangemaakt in `src/services/web_lookup/sru_service.py` tijdens XML‑parsing)
  - Wikipedia: `metadata['wikipedia_title']` (aangemaakt in `src/services/web_lookup/wikipedia_service.py` bij result‑bouw)

### Waarom nu zichtbaar
- In EPIC‑010 is de moderne web lookup service en compat‑wrapper geïntroduceerd/geüpdatet. De wrapper behield legacy formatting (`r.title`) terwijl het V2‑contract titles naar `metadata` heeft verplaatst. Door dynamische typing werd dit pas runtime zichtbaar.

### Scope en impact (blast radius)
- Treft alleen de compat‑tekstoutput in `HybridContextManager` wanneer web lookup resultaten teruggeeft.
- Verbreekt contextverrijking met een exception; downstream generatie kan stoppen.
- Repo‑scan bevestigt dat `.title` alleen hier op `r` (LookupResult) wordt gebruikt; geen andere call sites geraakt.

### Concretisering fix
- Display‑titel robuust afleiden uit metadata met fallbacks:
  - Eerst `dc_title`
  - Dan `wikipedia_title`
  - Dan `r.source.name` (altijd aanwezig)
- Indicatieve vervanging (alleen ter illustratie, geen code in deze bug):
  ```python
  titles = []
  for r in results[:3]:
      md = r.metadata or {}
      display_title = md.get('dc_title') or md.get('wikipedia_title') or r.source.name
      titles.append(f"{display_title} ({r.source.name})")
  return f"Web informatie voor {term}: " + "; ".join(titles)
  ```

### Niet doen (bewuste keuzes)
- Geen `title` veld toevoegen aan `LookupResult` (zouden dubbele bronnen van waarheid creëren en afwijken van bestaand V2‑contract).

### Validatie en observability
- Na fix: geen `AttributeError`; wrapper levert lege string bij geen resultaten en behoudt max 3 items voor beknopte context.
- Logging: huidige warning in `_get_web_context` blijft volstaan; extra logging niet noodzakelijk.

### Test‑aanvulling (detail)
- Unit:
  - Case A (SRU): `metadata={'dc_title': 'Wet open overheid'}` → string bevat 'Wet open overheid'.
  - Case B (Wikipedia): `metadata={'wikipedia_title': 'Openbaarheid'}` → string bevat 'Openbaarheid'.
  - Case C (Geen titel): `metadata={}` → string gebruikt `r.source.name`.
  - Case D (Lege resultaten): wrapper retourneert `""` zonder exception.
- Integratie (optioneel): simulateer 2 resultaten (1 SRU, 1 Wikipedia) en verifieer concatenatie en volgorde.

### Traceability
- Epic: EPIC‑010 (Context Flow Refactoring)
- Bug: CFR‑BUG‑015 (dit document)
- User story: geen aparte US gekoppeld; kan desgewenst als kleine bug‑fix onder EPIC‑010 worden doorgevoerd zonder nieuwe US.

---
