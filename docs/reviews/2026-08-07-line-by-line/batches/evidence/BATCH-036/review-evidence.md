# BATCH-036 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 14/14 blobs, 3097/3097 fysieke regels en 119/119 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- Onderdeel van 400 relevante unit-tests (1 expliciete skip); offline tiktoken-, SQLite- en URL-reproducties uitgevoerd; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B036-001 — P2 — Offline tokenizer initialization breaks RAG

**Bewijs:** Tokenizer construction requires a tiktoken encoding that may be fetched at runtime.

**Reproductie:** Patch get_encoding to raise OSError in a cold cache; TokenCounter construction fails.

**Aanbevolen oplossing:** Vendor or prewarm the encoding and provide a deterministic offline fallback.

### B036-002 — P2 — Concurrent collection creation races on a unique key

**Bewijs:** Existence check and insert are separate operations without conflict recovery.

**Reproductie:** Run two coordinated _ensure_collection calls against temporary SQLite; one raises UNIQUE IntegrityError.

**Aanbevolen oplossing:** Use an atomic insert-or-ignore/upsert and then load the canonical row.

### B036-003 — P2 — Malformed chunk metadata crashes management queries

**Bewijs:** SQL applies json(metadata) before Python fallback parsing can handle invalid values.

**Reproductie:** Insert malformed metadata in temporary SQLite and execute the management query; SQLite raises OperationalError.

**Aanbevolen oplossing:** Validate metadata on write and make read queries tolerant of legacy malformed rows.

### B036-004 — P2 — Trusted legal domains are accepted by substring

**Bewijs:** Authority scoring searches trusted names in the full URL instead of comparing the hostname.

**Reproductie:** Rank https://rechtspraak.nl.attacker.example and an evil-overheid.nl host; both receive trusted treatment.

**Aanbevolen oplossing:** Parse and normalize the hostname and require exact host or an allowed subdomain.

## Niet getest

- Geen echte externe webdienst, productie-RAG-collectie of netwerkdownload gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
