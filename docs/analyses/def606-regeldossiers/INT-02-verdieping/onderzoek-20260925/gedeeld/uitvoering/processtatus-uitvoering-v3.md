# Processtatus uitvoering — WP4 gecontroleerd, WP5 start

26 september 2026. Deze versie actualiseert de volledige taak-ID's uit takenlijst-v4.md en vervangt v2 als actuele voortgangsingang. Eerdere documenten en bewijs blijven bewaard.

- [x] A06 — aanvullende NE-contractwijziging geaccordeerd en uitgevoerd.
- [x] W3.5 — 146 tests groen; Ruff/Black/make lint schoon. wp3-transport-green-v2.log en wp3-transport-lint-v2.log.
- [x] W3.6 — C1 na definitieve formattering: proef-c1-uitvoering-na-o1-run2.json, 36/36 en exit 0; hashes horen bij huidige productiecode.
- [x] W4.1 — Opdracht en RED vastgelegd. wp4-red.log: golden rood; matrix al groen op NE. wp4-red-probestatus.log legt NE expliciet vast.
- [x] W4.2 — Twee bestaande bestanden herijkt; 22 regels, alle gevallen behouden.
- [x] W4.3 — 437 tests en lint groen. wp4-green.log, wp4-green-probestatus.log, wp4-lint.log. Coördinator heeft de concrete diff en logs gecontroleerd.
- [ ] W5.1 — Reviewbasis en identiteit vastleggen.
- [ ] W5.2 — Verse Codex CLI-review in afzonderlijke werkroot.
- [ ] W5.3 — Bevindingen afhandelen via dezelfde uitvoerder/reviewer.
- [ ] W5.4 — make test, volledige offline pytest en eind-lint.
- [ ] W5.5 — Contracten, casussen en actieve skillversies controleren.

De canonieke en tweede INT-02-contractkopie zijn bytegelijk. Actieve skillpublicatie volgt niet automatisch uit een branchwijziging en is nog niet uitgevoerd. De volledige suite en onafhankelijke review zijn nog geen bewijsclaim.

Bekende bestaande beperkingen: DEF-612-voorbeeldconflict; test_no_negative_commands_in_guide faalt ook op de basiscommit; volledige validatieresultaten hebben op de basiscommit onjuiste schema-eisen voor violation-codes (wp3-schema-basiscontrole.log). De WP3-tests bewijzen het nieuwe rule_results-contractdeel, conversie en exacte NE-weergave. Algemene schemaherziening valt buiten de goedgekeurde INT-02-aanvulling.

Alle prompts en ruwe CLI-streams blijven volledig lokaal opgeslagen in de uitvoeringsmap. Voor de Git-review worden opdrachten, scripts, compacte testlogs en resultaten opgenomen; herstelkopieën en omvangrijke ruwe sessiestreams blijven lokaal als herleidbaar procesbewijs. Er wordt niets verwijderd.
