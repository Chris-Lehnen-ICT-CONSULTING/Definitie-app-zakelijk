# DEF-835 — akkoord vervolg uitvoering v1

28 september 2026. Chris antwoordde letterlijk **"akkoord! go"** op de twee voorgelegde concrete besluiten.

Geaccordeerd:
- kwalificatieprotocol-v1.md, SHA-256 53a199fdff49c7ec40c10e84c79356fd72dcba6190cb75c715ce077c1054f18f: Q1, goldsetprotocol/kwaliteitsgrenzen, maximaal43appcalls/43tokenmetingen enUS$12 nieuw cumulatief proefbudget. Calls pas na geaccepteerde labels/freeze; geen automatische retries.
- vervolgplan-opslag-ui-v1.md, SHA-256 12cc0d306d5ac631d43efa4a7f8f627450df76c4f2f5d7048cc10b7fe96e5687: S1/S2/U1/E1, schema-/document-/exportcontracten en vervanging van uitsluitend log_definitie_changes en update_definities_timestamp in migratiecode. Alleen tijdelijke testdatabases; gegevens behouden.

De eerdere goldsetvraag bood twee verschillende beoordelaaropties; een algemeen akkoord kiest daar niet eenduidig tussen. Die benoeming blijft nodig vóór labelproductie, maar blokkeert de offline codepakketten niet.

Uitvoering start met Q1, daarna S1/S2/U1/E1 één tegelijk. Claude CLI implementeert; aparte Codex CLI reviewt. Geen nieuwe toestemming voor routineuitvoering binnen dit bereik. Geen Actions, push, merge of productieactivering.

Preflight: echte werkboom staat op feature/DEF-835-int02-o2, HEADf9bb9e697. CLI's: Claude2.1.283 enCodex0.158.0. Claude authstatus binnen sandbox gaf false, controle via bestaande sleutelhanger buiten sandbox bevestigde ingelogd; geen nieuwe login nodig.

