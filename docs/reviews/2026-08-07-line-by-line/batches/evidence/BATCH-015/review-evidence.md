# BATCH-015 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 11/11 blobs, 3.990/3.990 fysieke regels en 133/133 Python-symbolen

Alle toegewezen regels en symbolen zijn uit de immutable object-ID’s gelezen.
Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire wave-selectie: onderdeel van 263 geslaagde tests, plus 1 xfail.
- Onafhankelijke selectie: onderdeel van 111 geslaagde tests.
- Ruff en Black: geslaagd. Alleen dummies/mocks; geen externe calls.

## Bewezen bevindingen

### B015-001 — P1 — promptcap knipt begrip en finale opdracht weg

`src/services/prompts/modular_prompt_adapter.py:297-314` doet blind
`prompt[:max_prompt_length]`; de definitietaak staat als laatste en bevat begrip
en slotopdracht. Repro met cap 1.000: bronprompt 25.102 tekens, output 1.000,
unieke term en finale opdracht afwezig, einde midden in een sectie. Aanbevolen:
token-/sectiebudget vóór assembly, invariant budget voor term/taak/suffix en
fail-loud wanneer het minimum niet past.

### B015-002 — P1 — raw begrip wordt vóór securitysanitization gelogd

`src/services/orchestrators/definition_orchestrator_v2.py:337-359` logt
`request.begrip` op 345-348 en sanitizet pas daarna. Een capturelog met dummy
e-mailadres bevatte de raw waarde, terwijl sanitizer `[REDACTED]` leverde.
Aanbevolen: vóór sanitization alleen generation-ID/categorie loggen en daarna
alleen geredigeerde waarde of niet-omkeerbare hash.

### B015-003 — P2 — globale promptorchestrator lekt configuratie tussen adapters

`modular_prompt_adapter.py:30-183` deelt één mutable orchestrator en initialiseert
diens modules bij iedere adapter opnieuw. Na adapter B wijzigde adapter A van
gedrag en metadata. De builder is actief via `definition_generator_prompts.py`.
Aanbevolen: immutable/per-adapter orchestrator of config als per-build context,
met gelijktijdige isolatietest.

### B015-004 — P2 — zes include-flags hebben geen effect

`modular_prompt_builder.py:17-38` definieert de flags; omzetting op
`modular_prompt_adapter.py:189-267` leest ze niet. Alle zes False en defaults
gaven byte-identieke prompt van 26.133 tekens; rol, final instructions, ARAI en
constructiegids bleven aanwezig. Een bestaande test assert alleen nonempty.
Aanbevolen: flags expliciet naar module-activatie mappen of verwijderen en
onverenigbare configuratie fail-loud maken; test exacte afwezigheid.

### B015-005 — P1 — ongeldige RAG_MIN_SCORE breekt generatie zonder RAG

`definition_orchestrator_v2.py:579-588,1286-1302` doet onvoorwaardelijk
`float()` vóór de `rag_service`-check. Met `RAG_MIN_SCORE=not-a-number` en
`rag_service=None` gaf een minimale generatie `success=False` met ValueError.
Aanbevolen: startupconfig met finite/bounded validatie en veilige default/warning;
lees de waarde alleen wanneer RAG werkelijk actief is.

## Niet getest

- Geen externe AI/RAG/web-response, echte credentials of netwerk.
- Geen multi-thread loadtest; de configlek is sequentieel deterministisch bewezen.
- Geen visuele UI/a11y/responsive flow in deze niet-renderende batch.
