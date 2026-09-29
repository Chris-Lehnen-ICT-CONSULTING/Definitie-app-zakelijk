# DEF-768 — app-aansluiting ESS-05: aanvulling v1 op plan v1 (besluit Chris)

29-09-2026. Dit is een aanvulling op `2026-09-29-DEF-768-ess05-app-aansluiting-plan-v1.md` (commit `38f3abf12`); plan v1 zelf blijft ongewijzigd.

Chris heeft op 29-09 met **"Ja"** ingestemd met alle adviezen in §4 van plan v1. De STOP uit plan v1 is daarmee opgeheven.

| Keuze | Besluit |
|---|---|
| **A** Modelvoorstellen voor buren | Vervallen. Het veld `review.proposals` blijft in het contract maar is voor ess05/3 altijd leeg. De knop "Neem voorstel over" verdwijnt daardoor vanzelf. |
| **B** Bevestigingsbeleid | Het app-beleid blijft, als dunne afbeelding na `pas_regels_toe`:<ul><li>`niet_onderscheiden` bij een bevestigde buur → fail</li><li>`niet_onderscheiden` bij een onbevestigde buur → open, met de vraag die buur te bevestigen of af te wijzen</li><li>`onderscheiden` → voldoet</li><li>`open` → open</li><li>geen bevestigde buur → open</li><li>kern zonder kenmerk → fail</li></ul> |
| **C** Aanroepen per validatie | 1 interpretatie + 2 (kern, doel) + 1 per buur, na elkaar. Nu geaccepteerd. Conceptissue: `logs/def768/app-aansluiting-v1/issue-parallelle-controles-concept-v1.md` (niet in Linear). |
| **D** Bevestigd | <ul><li>Een lege-ruimte-bevestiging geeft een pass zonder AI-aanroep.</li><li>Zonder actieve buren volgt geen AI-aanroep; de uitkomst is open met "voeg verwante begrippen toe".</li><li>Een opgeslagen ess05/2-document wordt "verouderd — toets opnieuw".</li></ul> |

Uitvoering volgt plan v1 §1–§3 met TDD en uitsluitend stubs, zonder netwerk. Daarna volgt de verwijderlijst; er wordt niets verwijderd.
