# Werklijst: Security & Stability Sprint
**Aangemaakt:** 26 maart 2026
**Bron:** Multi-agent code review (15 agents) + Linear opschoning

> **Gebruik in VS Code:** Open een terminal, type `claude`, en zeg:
> "Lees .prompt-forge/werklijst-security-sprint.md en pak de eerste taak op"

---

## Volgorde & Afhankelijkheden

```
Week 1: Security (P0)
  ┌─ DEF-395 (XSS fix)          ← Geen dependencies, snelste win
  ├─ DEF-388 (Middleware wiren)  ← Geen dependencies
  ├─ DEF-387 (Pickle→JSON)      ← cache.py + resilience.py
  └─ DEF-236 (Streamlit race)   ← UI-only, onafhankelijk

Week 2: Stability (P1)
  ┌─ DEF-389 (Repository split) ← Grootste refactor, doe eerst
  ├─ DEF-312 (Container split)  ← Na DEF-389 (minder complex)
  ├─ DEF-189 (Dead code)        ← Na splits (vermijd merge conflicts)
  └─ DEF-197 (Resilience)       ← Na DEF-189 (overlap)

Week 3: Quality (P2)
  ┌─ DEF-390 (Data model)       ← Na DEF-389 (repository is dan gesplit)
  ├─ DEF-391 (DB transacties)   ← Na DEF-389
  ├─ DEF-393 (Exception cleanup)
  └─ DEF-392 (UI business logic)
```

---

## Taak 1: DEF-395 — XSS Filter Regex Bypass
**Prioriteit:** P0 Urgent | **Effort:** ~6 uur | **Branch:** `feature/DEF-395-xss-regex-fix`

### Wat is het probleem?
De sanitizer in `src/validation/sanitizer.py` (regel 189) gebruikt een regex die een spatie vereist vóór gevaarlijke attributen als `onclick=`. Zonder die spatie werkt de filter niet.

### Stappen
1. `git checkout -b feature/DEF-395-xss-regex-fix`
2. `pip install bleach --break-system-packages`
3. Voeg `bleach` toe aan `requirements.txt`
4. Open `src/validation/sanitizer.py`
5. Vervang de custom XSS regex (regel ~189) door `bleach.clean()`
6. Update alle aanroepen van de sanitize functie
7. Schrijf tests in `tests/test_sanitizer.py`:
   - Test: `<div onclick="alert(1)">` wordt gesanitized (ZONDER leading space)
   - Test: `<script>alert(1)</script>` wordt verwijderd
   - Test: Normale tekst blijft ongewijzigd
8. `make test` — alle tests moeten slagen
9. `make lint` — geen linting errors
10. Commit + push

### Verificatie
```bash
make test && make lint
grep -r "pickle\|bleach" src/validation/sanitizer.py  # bleach moet voorkomen
```

---

## Taak 2: DEF-388 — Security Middleware Aansluiten op FastAPI
**Prioriteit:** P0 Urgent | **Effort:** ~4 uur | **Branch:** `feature/DEF-388-wire-security-middleware`

### Wat is het probleem?
Er is een complete security middleware geschreven (731 LOC in `src/security/security_middleware.py`) maar die is nergens aangesloten op de FastAPI app.

### Stappen
1. `git checkout -b feature/DEF-388-wire-security-middleware`
2. Zoek het FastAPI entry point (waarschijnlijk `src/api/` directory)
3. Importeer de SecurityMiddleware
4. Registreer met `app.add_middleware(SecurityMiddleware)`
5. Test dat de middleware daadwerkelijk requests verwerkt
6. Schrijf integration test: request naar API → middleware headers aanwezig
7. `make test && make lint`
8. Commit + push

### Verificatie
```bash
grep -r "SecurityMiddleware" src/api/  # Moet nu imports tonen
make test
```

---

## Taak 3: DEF-387 — Pickle Vervangen door JSON + HMAC
**Prioriteit:** P0 Urgent | **Effort:** ~8 uur | **Branch:** `feature/DEF-387-replace-pickle`

### Wat is het probleem?
`pickle.load()` wordt op 3 plekken gebruikt zonder integriteitscheck. Dit is een Remote Code Execution (RCE) risico.

### Locaties
- `src/utils/cache.py` regel 114 (FileCache.get)
- `src/utils/cache.py` regel 619
- `src/utils/resilience.py` regel 374

### Stappen
1. `git checkout -b feature/DEF-387-replace-pickle`
2. Maak een `src/utils/safe_serializer.py` met:
   - `safe_save(data, filepath)` → JSON serialisatie + HMAC-SHA256 signature
   - `safe_load(filepath)` → HMAC verificatie + JSON deserialisatie
   - Secret key uit `.env` of `os.urandom()` bij eerste gebruik
3. Vervang `pickle.dump()`/`pickle.load()` op alle 3 locaties
4. Voeg migratiecode toe: als oud `.pkl` bestand bestaat → converteer naar JSON
5. Update tests
6. Verwijder oude `.pkl` bestanden uit `data/` of `src/log/`
7. `make test && make lint`
8. Commit + push

### Let op
- De resilience state (circuit breaker) moet behouden blijven na migratie
- Cache invalidatie is OK (cache bouwt zichzelf opnieuw op)

### Verificatie
```bash
grep -rn "pickle.load\|pickle.dump" src/  # Moet 0 resultaten geven
make test
```

---

## Taak 4: DEF-236 — Streamlit Race Conditions Fixen
**Prioriteit:** P0 Urgent | **Effort:** ~4 uur | **Branch:** `feature/DEF-236-fix-widget-race-conditions`

### Wat is het probleem?
6 widgets in `definition_edit_tab.py` gebruiken `value=X, key=Y` wat race conditions veroorzaakt bij Streamlit reruns. De verplichte pattern is key-only.

### Locaties (alle in `src/ui/components/definition_edit_tab.py`)
- Regel 476-482: `st.text_input("Begrip", value=definition.begrip, key=...)`
- Regel 488-495: `st.text_area("Definitie tekst", value=definition.definitie, key=...)`
- 4 andere instances: org_custom, jur_custom, wet_custom, toelichting

### Stappen
1. `git checkout -b feature/DEF-236-fix-widget-race-conditions`
2. Open `src/ui/components/definition_edit_tab.py`
3. Voor elke widget:
   a. Verwijder de `value=` parameter
   b. Gebruik `SessionStateManager.set_value(key, initial_value)` voor initialisatie
   c. Houd de `key=` parameter
4. Zorg dat initialisatie alleen bij eerste load gebeurt (not on rerun)
5. `make test && make lint`
6. **Handmatig testen:** `streamlit run src/main.py` → edit tab → wijzig velden → geen data loss
7. Commit + push

### Pattern (zo moet het eruitzien)
```python
# Initialisatie (eenmalig, bij laden definitie):
if not SessionStateManager.get_value(k("begrip")):
    SessionStateManager.set_value(k("begrip"), definition.begrip)

# Widget (key-only):
begrip = st.text_input("Begrip", key=k("begrip"))
```

### Verificatie
```bash
grep -n "value=" src/ui/components/definition_edit_tab.py  # Geen widget value= meer
make test && make lint
```

---

## Taak 5: DEF-389 — definitie_repository.py Opsplitsen (2209 LOC)
**Prioriteit:** P1 High | **Effort:** ~16 uur | **Branch:** `feature/DEF-389-split-repository`

### Wat is het probleem?
`src/database/definitie_repository.py` is de grootste file (2209 LOC) met 6+ verantwoordelijkheden.

### Plan
Split naar:
1. `definitie_repository.py` — Core CRUD (create, read, update, delete)
2. `examples_repository.py` — Voorbeelden beheer
3. `synonym_repository.py` — Synoniemen (als niet al apart)
4. `search_repository.py` — Zoekfuncties (fuzzy match, FTS)
5. `history_repository.py` — Geschiedenis/audit trail

### Stappen
1. Lees eerst het volledige bestand en identificeer methode-groepen
2. Maak de nieuwe bestanden aan
3. Verplaats methoden naar juiste bestanden
4. Update alle imports in de rest van de codebase
5. Zorg dat `ServiceContainer` de nieuwe repositories registreert
6. `make test && make lint`

---

## Taak 6-12: Week 2-3 (zie rapport)

De overige taken (DEF-312, DEF-189, DEF-197, DEF-390, DEF-391, DEF-392, DEF-393) volgen hetzelfde patroon. Begin pas nadat de P0 security sprint is afgerond en gereviewd.

---

## Tips voor VS Code + Claude Code

1. **Start altijd met:** `git branch --show-current` — check dat je NIET op main zit
2. **Story runner skill:** Zeg "bouw DEF-395" en Claude Code pakt het hele proces op
3. **Na elke taak:** `make test && make lint` om te verifiëren
4. **Bij twijfel:** Vraag Claude Code om uitleg, hij kent de codebase
5. **PR maken:** Zeg "maak een PR voor deze branch" en Claude doet de rest

---

*Gegenereerd door Cowork multi-agent analyse op 26 maart 2026*
