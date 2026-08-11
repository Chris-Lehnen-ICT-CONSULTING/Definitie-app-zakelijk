# BATCH-072 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 13/13 blobs, 2430/2430 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Crossselectie 36 groen en 7 skips; de volledige B072-B074-primary gaf 226 groen, 33 skips en 5 xfails.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Contextbridge is onder B068-002 vastgelegd; session_state/sys.path-delen relateren aan bestaande B052-testisolatie.

## Bevindingen

### B072-001 — P2 — Dutch plural nouns receive verb-specific prompt instructions

**Bewijs:** The test explicitly treats behandelingen as a verb; active expertise classification labels nearly every word longer than four characters ending in en as a verb and downstream modules add action instructions.

**Reproductie:** Build prompts for behandelingen, documenten, wetten and zaken; each is classified as a verb and receives action or process guidance.

**Aanbevolen oplossing:** Use explicit morphology or category-aware classification and add plural-noun negative regressions before verb rules are selected.

### B072-002 — P2 — E2E simulation file collects no tests and mutates Streamlit state

**Bewijs:** The file defines simulate_generation_flow and main but no test_* function; import assigns a plain dict to st.session_state and the copied flow calls no production integration seam.

**Reproductie:** Run pytest collect-only: zero tests are collected; standalone import changes SessionStateProxy to dict.

**Aanbevolen oplossing:** Replace it with real pytest or AppTest cases through production handlers and use scoped monkeypatch fixtures that restore Streamlit state.

## Niet getest

- Geen echte AI-provider of browser; woordsoort- en testcollectiegedrag zijn offline bewezen.
