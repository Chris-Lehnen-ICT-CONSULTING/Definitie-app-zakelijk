# Werkstaat RAG-kwaliteit — bijgewerkt 10 oktober 2026

**Doel:** de bronbibliotheek (RAG) levert voor een begrip de juiste passages uit de gekozen context, in een betrouwbare volgorde, en we laten zien dat die passages de definitie beter maken. Chris: eerst de RAG goed laten werken.

**Stukken:** werkplan `docs/plans/2026-10-09-RAG-kwaliteit-werkplan-v2.md` · meting `docs/analyses/2026-10-09-rag-meting/` (`meet-v1.py`, `resultaat-v1.json`) · matrix `matrix-concept-v2.md` (vastgesteld) · epic Linear **DEF-847**.

## Besluiten (Chris)

**9 oktober 2026**
- **B1** Bronselectie volgt de gekozen context (nieuw WvSv gekozen → alleen nieuw WvSv; beide → beide). Geen apart peildatumfilter.
- **B2** Eén lijst (matrix) wet- en regelgeving × rechtsgebied; regeling zonder bibliotheekcollectie blijft kiesbaar.
- **B3** Goldset (DEF-368) overslaan; indicatieve regressiemeetset (DEF-848).
- **B4** Een Linear-issue dat de prompt builder raakt, geldt als overleg (DEF-632).
- Geen wettelijke basis → zoeken via rechtsgebied; foute combinatie → waarschuwen; collectiekiezer bij generatie vervalt; nieuwe epic DEF-847.

**10 oktober 2026 (DEF-846)**
- Matrix in `config/bronnenlijst.yaml`; buiten de matrix = waarschuwing; BW per boek (Boek 1, 2); lijst van 15 rechtsgebieden blijft, opschonen in DEF-854.
- Na Codex-review van concept v1: **B-1** sanctierecht = strafrechtelijk sanctierecht (label hernoemen in DEF-854) · **B-2** nieuw WvSv alleen bij expliciete keuze, met melding bij de bronnen (AC in DEF-631) · **B-3** Wet RO breed (7 rechtsgebieden) · **B-4** "Uitvoeringswet EU-richtlijnen" vervalt; EU-richtlijnen als eigen regelingen → DEF-855 · **B-5** EVRM: alle rechtsgebieden · **B-6** geen jeugdrecht bij losse bepalingen over minderjarigen; Bjj, Rjj, Bvt, Rvt en Penitentiaire maatregel toegevoegd.
- Matrix-v2 in zijn geheel vastgesteld (30 regelingen).
- Uitvoering (Cowork, na onafhankelijke review): de bestaande labels van Wpg, Vw 2000, WID en EVRM blijven het label (officiële naam in `naam`), omdat hernoemen opgeslagen definities raakt (contextsleutel, duplicaatcontrole, wijzigingsdetectie). Hernoemen met datamigratie → DEF-854.

## Af

- RAG-onderzoek en meting (19 zoekvragen); werkplan v1 → v2.
- Linear: epic DEF-847 met DEF-846, 848–855; besluiten als comments op DEF-631, 632, 368, 614, 849, 854.
- Matrix: concept v1 → Codex-review → v2 → vastgesteld.
- DEF-846 gebouwd op `feature/DEF-846-regelingenregister`: register in `bronnenlijst.yaml`, `domain.sources.regelingen` met laadcontrole, keuzelijst "wettelijke basis" uit het register (contextkiezer, bewerk-tab), oude lijsten weg (`WET_OPTIONS`, `common_laws`), importscript leest `rechtsgebieden` (eerste = hoofdrechtsgebied, ongewijzigd voor bestaande collecties) en heeft een stap `vergelijk --db`; register wordt bij het opstarten gelezen. Onafhankelijke review (subagent) verwerkt.

## Open

- PR van DEF-846: review en merge door Chris.
- Vóór DEF-631/DEF-632: DEF-768-ess05-ai-beoordeling afronden en mergen (overlapt in orchestrator en promptservice). DEF-835-o2 bevat afgeronde code die niet in `main` zit.
- Citeertitels en BWB-id's van Bjj, Rjj, Bvt, Rvt en Penitentiaire maatregel bevestigen bij een eventuele import; Rv-rechtsgebieden nog te verifiëren.
- Dode code met eigen wettenlijsten (nu op het register omgezet, niet verwijderd — verwijderen alleen op opdracht van Chris): `services/validation/context_validator.py`, `ui/components/context_state_cleaner.py`, `ui/components.py` (overschaduwd door het pakket `ui/components/`); `src/config/context_wet_mapping.json` en `context_mapping_file` in de config worden nergens gelezen.
- Weblookup deelt contexttokens in op woorden als "recht"; nieuwe regelingen zonder dat woord (bv. Penitentiaire maatregel, Reglement …) worden daar als organisatie ingedeeld. Raakt de RAG niet; aparte opvolging.
- `vergelijk --db` nog niet tegen de echte `data/bronnen.db` gedraaid (staat alleen op de Mac).

## Volgende actie

1. Chris merget de PR van DEF-846.
2. Daarna DEF-848 (regressiemeetset) en, na DEF-768, DEF-631 (bronselectie volgt context).
