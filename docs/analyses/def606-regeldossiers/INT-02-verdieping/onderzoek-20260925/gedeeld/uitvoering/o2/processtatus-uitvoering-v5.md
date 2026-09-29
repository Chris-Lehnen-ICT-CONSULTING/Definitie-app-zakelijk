# DEF-835 — processtatus uitvoering v5

28 september 2026. Vervolg op v4, oude versies behouden. Actuele takenlijst: takenlijst-v12.md.

| Stap | Status en bewijs |
| --- | --- |
| WP1/WP2 | Eerder afgerond; inhoud ongewijzigd |
| WP3 scope | Chris gaf akkoord op negen bestanden |
| WP3 RED | 92 failed / 19 passed, exit 1; geldige run na één gemelde shellquotingfout |
| WP3 GREEN | 111 passed met bytegelijke tests |
| Testomissie plan | Vijf bestaande bestanden pinnen oud contract; concrete uitbreiding voorgesteld, akkoord nog open |
| Coördinator | 539 passed / 8 bekende failures; log bewaard |
| Eerste review | Verse Codex CLI, één Important/P2-bevinding WP3-R1 |
| Correctie | Dezelfde Claude CLI: 8 RED-failures → 119 groen |
| Herreview | Dezelfde Codex CLI: 119 groen, R1 gesloten; code 9769730d6 |
| Oplevering | Tussenoplevering negen bestanden; WP3 geheel niet afgetekend |

Geen afhankelijk werk uitgevoerd zonder de vereiste toestemming voor vijf extra testbestanden. Geen bestaande testgevallen verwijderd. Prompts/logs in het dossier; ruwe CLI-streams lokaal. Rollen en sessies staan in wp3-tussenoplevering-v1.md. Geen actieve processen, geen Actions/push/merge of appmodelcalls.
