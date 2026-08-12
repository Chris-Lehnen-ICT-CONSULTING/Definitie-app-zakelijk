# BATCH-046 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 12/12 blobs, 3586/3586 fysieke regels en 90/90 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 148 primaire gerichte tests en 50 onafhankelijke crosstests groen; 7 expliciete skips per relevante selectie; drie veilige Streamlit AppTests renderden zonder echte provider.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: B046-007 is gerelateerd aan de eerder vastgelegde false-successfamilie B043-004, maar betreft andere actieve call-sites.

## Bevindingen

### B046-001 — P1 — Cleaning strips valid term prefixes from definitions

**Bewijs:** The anchored term regex has no word or delimiter boundary and removes a prefix from a longer first word.

**Reproductie:** Clean 'Wettelijke regeling voor toezicht' with term 'wet'; the result starts with 'Telijke'.

**Aanbevolen oplossing:** Require a non-empty term and a real term boundary or delimiter; add compound-word regressions.

### B046-002 — P2 — Empty cleaning term causes a non-progressing loop

**Bewijs:** An empty escaped term creates a zero-width match and the repeated substitution makes no progress.

**Reproductie:** Call opschonen('Geldige definitie', '') under a one-second alarm; it does not return.

**Aanbevolen oplossing:** Reject blank terms and break or fail when an iteration does not change the text.

### B046-003 — P2 — Legal-basis parse failure can accept a malformed existing definition

**Bewijs:** The parse exception is logged but the existing match remains selected and can be returned as acceptable.

**Reproductie:** Use a repository record whose legal-basis parser raises; the exact-match path still returns that record.

**Aanbevolen oplossing:** Clear the candidate on parse failure and return a typed data-quality result instead of failing open.

### B046-004 — P3 — Zero performance baseline disables regression monitoring

**Bewijs:** Regression calculation divides by the baseline median although zero is valid in the schema.

**Reproductie:** Return baseline median 0.0 and run the regression check; ZeroDivisionError is raised and caught by the app-level monitor wrapper.

**Aanbevolen oplossing:** Handle zero and near-zero baselines with an absolute-delta policy until a positive baseline exists.

### B046-005 — P2 — API monitoring history is never persisted

**Bewijs:** The save routine exists but has no caller; recording only mutates the in-memory deque.

**Reproductie:** Record an API call with the saver mocked; the deque grows but the saver call count remains zero.

**Aanbevolen oplossing:** Add debounced atomic persistence and a shutdown flush, then verify restart continuity.

### B046-006 — P3 — API monitoring readers race with deque mutation

**Bewijs:** Synchronous readers iterate the shared deque without the asynchronous writer lock.

**Reproductie:** Mutate the deque during get_realtime_metrics iteration; RuntimeError reports that the deque changed size.

**Aanbevolen oplossing:** Take an immutable snapshot under one thread-safe lock and calculate outside the lock.

### B046-007 — P3 — Synonym admin reports failed mutations as success

**Bewijs:** Mutation booleans are ignored and bulk success counters increment even when repository operations return False.

**Reproductie:** Return False from update_member_status or update_member; the page still shows success and invalidates state.

**Aanbevolen oplossing:** Require structured outcomes, show accurate partial failures and bind confirmation state to entity and revision.

### B046-008 — P3 — Hardcoded secondary text fails dark-theme contrast

**Bewijs:** The fixed #666 text color has a 3.291:1 ratio on Streamlit's #0E1117 dark background, below WCAG AA for normal text.

**Reproductie:** Calculate the contrast for the hardcoded color on the default dark background; it is below 4.5:1.

**Aanbevolen oplossing:** Use theme tokens or a color proven to meet 4.5:1 in both light and dark themes; verify in a browser.

### B046-009 — P3 — Four intended checker methods are unreachable nested definitions

**Bewijs:** Four functions are nested after an unconditional return and are absent from the class API.

**Reproductie:** Check hasattr on the four documented method names; every result is False.

**Aanbevolen oplossing:** Dedent supported methods into the class or remove the unreachable code and add public-surface tests.

### B046-010 — P3 — Definition checker discards supplied legal context

**Bewijs:** The method accepts and checks wettelijke_basis but hardcodes an empty legal list in the AI context.

**Reproductie:** Pass ['Wet A'] and capture the adapter context; wettelijk is an empty list.

**Aanbevolen oplossing:** Propagate normalized legal bases through generation and regeneration and add a context contract test.

### B046-011 — P2 — Performance tracker leaks SQLite connections on a hot path

**Bewijs:** with sqlite3.connect commits or rolls back but does not close the connection; the rerun path opens several per metric.

**Reproductie:** Construct a tracker, record metrics and force garbage collection; ResourceWarning reports an unclosed database.

**Aanbevolen oplossing:** Use contextlib.closing around connections with explicit transactions and run warning-as-error lifecycle tests.

### B046-012 — P3 — Synonym Metrics-footer verwijst naar verwijderde /synonym_review-pagina

**Bewijs:** De actieve multipage-footer bevat href=/synonym_review. De immutable src/pages bevat alleen rag_management.py, synonym_admin.py en synonym_metrics.py; synonym_admin.py:17 documenteert expliciet dat die pagina de verwijderde synonym_review.py vervangt. Er bestaat geen route/page/caller met de slug synonym_review. Browserbewijs bevestigde terugval naar home/not-found.

**Reproductie:** Open Synonym Metrics en activeer Synonym Review; de doelpagina bestaat niet. Vergelijk de href met de door Streamlit geregistreerde pagina src/pages/synonym_admin.py.

**Aanbevolen oplossing:** Vervang raw HTML-navigatie door st.page_link naar pages/synonym_admin.py of de correcte geregistreerde route en voeg een multipage-navigatieregressietest/linkintegriteitsgate toe.

## Niet getest

- Geen echte provider/netwerkcall, malformed productie-DB-record, multi-session loadtest of browsermatige dark-theme/keyboard/screenreadertest; maintenance execute is bewust niet uitgevoerd.
