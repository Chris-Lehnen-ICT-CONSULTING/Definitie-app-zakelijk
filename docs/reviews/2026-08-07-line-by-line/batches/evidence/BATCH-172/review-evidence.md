# BATCH-172 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 11/11 bereiken, 5932/5932 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable bronnen en symbolen zijn gelezen; import-, config-, CI-context-, Git-policy-, fuzzy-duplicate- en gerichte pytestreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B172-001 — P2 — Canonieke multi-agentgids schrijft onherstelbare reset- en force-cleanupstappen voor

**Bewijs:** De active/current/canonical gids gebruikt tweemaal git reset --hard om patches sequentieel te testen zonder controle op uncommitted of untracked werk. Het inline scoreboard checkt branches uit zonder dirty-stateguard of hersteltrap. De finale workflow schakelt naar main, merge't daar direct, force-verwijdert de worktree en gebruikt branch -D. Deze paden kunnen agentwerk vernietigen of een niet-gevalideerde branch buiten de PR-flow integreren; de ontbrekende helper uit B171-004 maakt het advies niet veiliger.

**Reproductie:** Inspecteer statisch regels 66-83, 105-119 en 188-204. Een tracked wijziging die niet in de patch zit wordt door reset --hard verwijderd; een niet-gepushte commit op agent-a kan na worktree remove --force en branch -D alleen via reflog worden teruggevonden. Voer deze destructieve commando's niet uit.

**Aanbevolen oplossing:** Vervang sequentiële destructieve patchtests door geïsoleerde tijdelijke worktrees, weiger dirty of untracked state, pin en verifieer iedere commit/patchhash en gebruik finally/traps voor herstel. Merge uitsluitend via de featurebranch-PR-flow en maak cleanup expliciet bevestigd en recoverable.

### B172-002 — P2 — Implemented duplicate-query fix still performs exact-only matching while active callers require fuzzy results

**Bewijs:** The document says Status Implemented and describes bounded fuzzy LIKE, similarity scoring and a top-50 result. The active user guide promises detection of identical or very similar definitions, and DefinitieChecker explicitly handles fuzzy scores above 0.9 and 0.7. Production definition_duplicates.py:20-104 and DefinitionRepository:369-380 perform only exact term and synonym equality; no bounded fuzzy candidate or similarity stage exists.

**Reproductie:** In an in-memory SQLite repository insert `voorlopige hechtenis`. Exact lookup returns one record with score 1.0, while `voorlopige hechtenissen` and `voorlopige hechteni` each return zero. The active generation checker therefore receives no fuzzy candidate and can continue despite the documented similar-duplicate contract.

**Aanbevolen oplossing:** Decide explicitly whether fuzzy detection remains a supported contract. If yes, restore a bounded normalized candidate query plus similarity/top-N scoring with active unit and integration tests; if no, remove unreachable fuzzy score branches and exact the user and implementation documentation to exact-only semantics.

## Deduplicaties en afwijzingen

- Destructieve Gitpatronen relateren aan B135-004; B172-002 is een nieuw actief exact-versus-fuzzy productcontract.

## Niet getest

- Geen live AI/netwerk/credentials, externe GitHub-protection, destructive Gitflows, productiedata of Streamlit/browser/a11y-runtime.
