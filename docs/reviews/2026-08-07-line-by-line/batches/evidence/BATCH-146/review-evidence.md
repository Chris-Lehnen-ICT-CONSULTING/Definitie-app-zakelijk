# BATCH-146 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 11/11 bereiken, 5890/5890 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; historische tellingen, ontbrekende suites, shell-/AST-reproducties, linkscans en veilige gate-simulaties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B146-001 — P3 — String-duplication report overstates its Python-file scope by more than twelvefold

**Bewijs:** The report labels itself a complete and very thorough analysis of 9,620 Python files. At its introducing commit a4bea5198f87fb83634d4e0258ca8dac1059a0fd, git ls-tree contains 745 tracked .py files and 3,074 tracked paths in total, so 9,620 cannot be a Python-file count for the stated codebase.

**Reproductie:** Resolve the file's introducing commit with git log --follow, then count git ls-tree -r --name-only a4bea5198f87fb83634d4e0258ca8dac1059a0fd entries ending in .py; observe 745 rather than 9,620.

**Aanbevolen oplossing:** Regenerate the analysis from a pinned tree with a published counting query and label occurrence counts separately from file counts; otherwise archive it with a warning that its quantitative scope is invalid.

### B146-002 — P3 — Final prompt analysis gives contradictory module counts in its opening claims

**Bewijs:** Line 6 defines the scope as a 19-module prompt system, while line 14 says the complete exploration covered all 17 modules. The later category table also sums to 17 modules, so the decision document has no single reproducible scope.

**Reproductie:** Read lines 6 and 14 from blob 6779a8fc79430ab478b9374e70c0d4da3f43fa56 and compare the stated module counts; sum the later category counts 7+1+6+2+1 to obtain 17.

**Aanbevolen oplossing:** Pin the analyzed commit and generated module inventory, derive all headline counts from that inventory, and remove or correct every conflicting metric before using the roadmap for prioritization.

### B146-003 — P3 — Validation report changes its own weighted score from 66.75 to 72

**Bewijs:** The displayed formula is 0.4*75 + 0.3*60 + 0.15*40 + 0.15*85. It correctly expands to 66.75 on line 333 but then labels that value approximately 72/100; ordinary rounding yields 67, not 72.

**Reproductie:** Evaluate 0.4*75 + 0.3*60 + 0.15*40 + 0.15*85 in Python; the result is 66.75 and round(...) is 67.

**Aanbevolen oplossing:** Generate the score from the component values and weights, assert weights sum to one, and display 66.75 or the documented rounding result 67.

## Deduplicaties en afwijzingen

- Historische telafwijkingen zijn alleen geregistreerd waar het document een concrete actuele conclusie trekt.

## Niet getest

- Geen externe URLs/netwerk, destructive commands, echte credentials/productiedata, historische benchmarks of browser/UI-runtime.
