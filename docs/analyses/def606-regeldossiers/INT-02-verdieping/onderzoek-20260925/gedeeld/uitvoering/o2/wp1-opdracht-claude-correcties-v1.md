# DEF-835 WP1 — reviewcorrecties v1

Jij bent dezelfde Claude Code CLI-uitvoerder, sessie 177f1484-4e5c-482e-b431-450befdab835. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies.

Werkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, branch feature/DEF-835-int02-o2, te corrigeren head314b817aabcaaa9f5a00d74a7633155ec74b799c. Alleen de vijf geaccordeerde WP1-bestanden; nieuwe bewijs-/rapportbestanden in U=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2 toegestaan. Geen andere bronbestanden, geen Actions, geen modelcalls/appactivering, geen dependencies, geen verwijderingen. Omvangverruiming blijft gelden. Geen commit/push; coördinator doet dat.

Lees U/wp1-codex-review-v1.md volledig. De drie P2-bevindingen zijn concreet gereproduceerd en door de coördinator op code/plan beoordeeld: alle drie fix nu. De reviewerprobes staan als exact bewijs in U/bewijs/wp1-codex-probes-v1.py (oorspronkelijke reviewwerkboomreferentie behouden; geen productcode).

1. _grondbron accepteert leeg/alleen witruimte begrip en lege bron als grond zonder citaat. C112→pass en C105→fail: allebei onterecht met lege grond. Vereis gevulde opgeloste grondtekst ook zonder grondcitaat; error/invalid_citation. Test beide verdicts, beide grondvelden, leeg en whitespace.
2. Opeenvolgende replace verandert ingevoegde citaten/grond/reden wanneer ze placeholders bevatten, bijvoorbeeld De medewerker vult {grond} in. en reason met {één vraag}. Render uitsluitend de placeholders in het oorspronkelijke sjabloon in één stap, zonder opnieuw ingevoegde waarden te interpreteren. Behoud alle letterlijke synthesesjablonen. Test de daadwerkelijke verwachte eindstrings zelfstandig (niet dezelfde renderlogica in de test), bij pass/fail/O en relevante placeholdervarianten.
3. toets_actualiteit op replace(doc, oordeel_json="1"*5000) lekt ValueError uit JSON-decoder. Vang relevante decoderfouten bij replay, geef error/MELDING_E; geen catch-all dat fouten stil als oordeel behandelt. Test de genoemde gewone stringinhoud (runtime integerdigitlimiet) en andere concreet relevante decoderfouten zoals overdiepe JSON als die ook kunnen lekken. Geen algemene hypothetische hardening.

Werkwijze:
- Voeg regressietests toe vóór correcties. Draai ze op de ongewijzigde314b817aa-contractimplementatie: moeten op het beschreven gedrag falen. Bewaar volledige rode output + exitcode als U/bewijs/wp1-correcties-rood-v1.log.
- Corrigeer daarna de drie punten, zonder bestaande cases te verwijderen of af te zwakken.
- Draai hele WP1-testmodule, Ruff en Black voor eigen files, bewaar output+exitcodes U/bewijs/wp1-correcties-groen-v1.log en wp1-correcties-lint-v1.log.
- Actualiseer je eigen contractdocument waar nodig voor grond/renderer/decoder; geen nieuwe norm/contractversie als nog niet geactiveerde v1-correctie.
- Documenteer per reviewpunt oorzaak, verandering, nieuwe test, rood→groen, exacte finale bestanden/hashes in U/wp1-claude-correcties-v1.md.
- Geef regressietests/semantische wijzigingen van bestaand testbestand exact aan. Niets anders polijsten.
- Stop met volledig bewijs. Dezelfde Codex-reviewer controleert daarna alleen deze correcties en hun doorwerking.

Je mag je eigen bestanden binnen dit geaccordeerde correctiewerk bewerken. Bewaar een unieke herstelkopie buiten git of vertrouw op de gecommitteerde314b817aa-basis waar regels dat toestaan; bestaande bewijsrapporten blijven ongewijzigd, kies nieuwe versies.
